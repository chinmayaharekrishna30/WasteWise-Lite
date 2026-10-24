"""WasteWise AI - Lite. No database, no login: everything is read from the CSV files in ml/data/raw."""
from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
ML_SRC = ROOT / "ml" / "src"
RAW = ROOT / "ml" / "data" / "raw"
ART = ROOT / "ml" / "artifacts"
sys.path.insert(0, str(ML_SRC))

from predict import Predictor  # noqa: E402

# ------------------------------------------------------------------ load data once
products = pd.read_csv(RAW / "products.csv")
batches = pd.read_csv(RAW / "inventory_batches.csv")
sales = pd.read_csv(RAW / "perishable_inventory.csv")
scenarios_df = pd.read_csv(RAW / "discount_scenarios_simulated.csv").drop_duplicates(["batch_id", "discount_pct"])
for c in ("received_at", "snapshot_date", "expiry_date"):
    batches[c] = pd.to_datetime(batches[c]).dt.strftime("%Y-%m-%d")
sales["date"] = pd.to_datetime(sales["date"])
sales = sales.sort_values(["product_id", "date"]).reset_index(drop=True)
cost_of = dict(zip(products.product_id, products.unit_cost))
name_of = dict(zip(products.product_id, products.product_name))

# ------------------------------------------------------------------ models (train on first start if missing)
if not (ART / "forecast_model.joblib").exists():
    import train_forecast
    train_forecast.main()
if not (ART / "expiry_risk_model.joblib").exists():
    import train_expiry_risk
    train_expiry_risk.main()
predictor = Predictor(ART)

BATCH_COLS = ["batch_id", "product_id", "category", "received_at", "expiry_date", "initial_quantity",
              "quantity_remaining", "days_to_expiry", "avg_daily_sales_7d", "expected_demand_before_expiry",
              "unit_price", "unit_cost", "discount_pct"]


def active_mask(df: pd.DataFrame):
    return (df.days_to_expiry >= 0) & (df.quantity_remaining > 0)


def clean(rec: dict) -> dict:
    return {k: (v.item() if hasattr(v, "item") else v) for k, v in rec.items()}


# ------------------------------------------------------------------ forecast
def run_forecast(product_id: int, horizon: int, discount: float = 0.0) -> dict:
    p = products[products.product_id == product_id]
    if p.empty:
        raise HTTPException(404, "Product not found")
    p = p.iloc[0]
    g = sales[sales.product_id == product_id]
    start = g.date.iloc[-1] + timedelta(days=1)
    price = float(p.selling_price) * (1 - discount / 100)
    preds = predictor.forecast([float(x) for x in g.units_sold], start, horizon, price, product_id, p.category, discount)
    return {
        "product_id": product_id, "product_name": p.product_name, "horizon_days": horizon,
        "total_predicted_units": round(sum(preds), 2),
        "daily": [{"date": (start + timedelta(days=i)).strftime("%Y-%m-%d"), "predicted_units": round(v, 2)}
                  for i, v in enumerate(preds)],
        "history": [{"date": d.strftime("%Y-%m-%d"), "units_sold": int(u)} for d, u in zip(g.date.tail(30), g.units_sold.tail(30))],
        "model_version": predictor.forecast_version,
    }


# ------------------------------------------------------------------ recommendations
DISCOUNTS = (0, 5, 10, 15, 20)
MIN_MARGIN = 0.05
RECS: list[dict] = []


def scenarios_for(b: pd.Series) -> list[dict]:
    rows = scenarios_df[scenarios_df.batch_id == b.batch_id].sort_values("discount_pct")
    if not rows.empty:
        return [{"discount_pct": float(r.discount_pct), "units_sold": float(r.estimated_units_sold_simulated),
                 "revenue": float(r.estimated_revenue_simulated), "margin": float(r.estimated_gross_margin_simulated),
                 "source": "discount_scenarios_simulated"} for r in rows.itertuples()]
    out = []
    for d in DISCOUNTS:
        units = float(min(b.quantity_remaining, round(max(b.expected_demand_before_expiry, 0) * (1 + 0.025 * d))))
        rev = units * float(b.unit_price) * (1 - d / 100)
        out.append({"discount_pct": d, "units_sold": units, "revenue": round(rev, 2),
                    "margin": round(rev - units * float(b.unit_cost), 2), "source": "simulated_rule"})
    return out


def build_rec(b: pd.Series, risk: dict) -> dict | None:
    qty, cost, price = int(b.quantity_remaining), float(b.unit_cost), float(b.unit_price)
    if qty <= 0:
        return None
    if b.days_to_expiry < 0:   # food safety first: never discount expired stock
        return dict(batch_id=int(b.batch_id), action_type="INSPECT_REMOVE", suggested_discount_pct=None,
                    expected_units_sold=None, expected_revenue=None, expected_margin=None, scenarios=[],
                    rationale=f"Batch expired {abs(int(b.days_to_expiry))} day(s) ago. Do NOT sell; inspect and remove "
                              f"{qty} unit(s) per store food-safety policy.")
    surplus = risk["expected_surplus_units"]
    if surplus <= 0 and risk["expiry_risk_probability"] < 0.4:
        return None
    sc = scenarios_for(b)
    for s in sc:
        s["feasible"] = price * (1 - s["discount_pct"] / 100) >= cost * (1 + MIN_MARGIN)
        s["unsold_units"] = round(max(qty - s["units_sold"], 0), 2)
        s["net_value"] = round(s["margin"] - s["unsold_units"] * cost, 2)
    pool = [s for s in sc if s["feasible"]] or [s for s in sc if s["discount_pct"] == 0]
    best = max(pool, key=lambda s: s["net_value"])
    base = next(s for s in sc if s["discount_pct"] == 0)
    why = (f"{qty} units left, {int(b.days_to_expiry)} day(s) to expiry, expected demand "
           f"{b.expected_demand_before_expiry:.0f} -> predicted surplus {surplus:.0f} units "
           f"(risk {risk['expiry_risk_probability']:.0%}).")
    if best["discount_pct"] > 0:
        action, disc = "DISCOUNT", float(best["discount_pct"])
        why += f" A {disc:.0f}% discount maximises expected net value ({best['net_value']:.0f} vs {base['net_value']:.0f} at no discount)."
    else:
        action, disc = "REDUCE_REPLENISHMENT", None
        why += " No feasible discount helps enough - reduce the next replenishment quantity."
    return dict(batch_id=int(b.batch_id), action_type=action, suggested_discount_pct=disc,
                expected_units_sold=best["units_sold"], expected_revenue=best["revenue"],
                expected_margin=best["margin"], rationale=why, scenarios=sc)


class Decision(BaseModel):
    status: str = Field(pattern="^(APPROVED|REJECTED|MODIFIED)$")
    final_discount_pct: float | None = Field(default=None, ge=0, le=50)


# ------------------------------------------------------------------ routes
router = APIRouter(prefix="/api/v1")


@router.get("/dashboard/summary")
def summary():
    act = batches[active_mask(batches)].reset_index(drop=True)
    value = float((act.quantity_remaining * act.unit_cost).sum())
    risk_units = risk_cost = 0.0
    high = 0
    for (_, b), s in zip(act.iterrows(), predictor.score_batches(act)):
        if s["risk_level"] in ("HIGH", "MEDIUM"):
            risk_units += s["expected_surplus_units"]
            risk_cost += s["expected_surplus_units"] * float(b.unit_cost)
            high += s["risk_level"] == "HIGH"
    recent = sales[sales.date > sales.date.max() - timedelta(days=30)]
    trend = recent.groupby("date")[["units_sold", "waste_units"]].sum().reset_index()
    stock = act.groupby("product_id").quantity_remaining.sum().to_dict()
    demand, low = 0.0, []
    for pid in products.product_id:
        f = run_forecast(int(pid), 7)
        demand += f["total_predicted_units"]
        if stock.get(pid, 0) < f["total_predicted_units"]:
            low.append({"product_id": int(pid), "product_name": name_of[pid], "stock": int(stock.get(pid, 0)),
                        "forecast_7d": f["total_predicted_units"]})
    return {
        "inventory_value": round(value, 2), "active_batches": len(act),
        "expiry_risk_units_predicted": round(risk_units), "expiry_risk_cost_predicted": round(risk_cost, 2),
        "high_risk_batches": int(high),
        "expired_units_on_hand": int(batches[batches.days_to_expiry < 0].quantity_remaining.sum()),
        "waste_units_actual_30d": int(recent.waste_units.sum()),
        "waste_cost_actual_30d": round(float((recent.waste_units * recent.product_id.map(cost_of)).sum()), 2),
        "predicted_demand_7d": round(demand), "low_stock_alerts": low,
        "trend": [{"date": d.strftime("%Y-%m-%d"), "units_sold": int(u), "waste_units": int(w)}
                  for d, u, w in zip(trend.date, trend.units_sold, trend.waste_units)],
        "model_versions": {"forecast": predictor.forecast_version, "expiry_risk": predictor.risk_version},
    }


@router.get("/products")
def list_products(q: str | None = None, category: str | None = None):
    df = products.copy()
    if q:
        df = df[df.product_name.str.contains(q, case=False) | df.product_id.astype(str).str.contains(q)]
    if category:
        df = df[df.category == category]
    stock = batches[batches.days_to_expiry >= 0].groupby("product_id").quantity_remaining.sum().to_dict()
    return [{"product_id": int(r.product_id), "sku": f"P{r.product_id}", "product_name": r.product_name,
             "category": r.category, "shelf_life_days": int(r.shelf_life_days), "selling_price": float(r.selling_price),
             "unit_cost": float(r.unit_cost), "stock_on_hand": int(stock.get(r.product_id, 0))} for r in df.itertuples()]


@router.get("/batches")
def list_batches(product_id: int | None = None, status: str | None = Query(None, pattern="^(active|expired|empty)$"),
                 limit: int = Query(100, le=500), offset: int = 0):
    df = batches
    if product_id:
        df = df[df.product_id == product_id]
    if status == "active":
        df = df[active_mask(df)]
    elif status == "expired":
        df = df[(df.days_to_expiry < 0) & (df.quantity_remaining > 0)]
    elif status == "empty":
        df = df[df.quantity_remaining == 0]
    df = df.sort_values(["days_to_expiry", "batch_id"])
    return {"total": len(df), "items": [clean(r) for r in df[BATCH_COLS].iloc[offset:offset + limit].to_dict("records")]}


@router.get("/batches/at-risk")
def at_risk(limit: int = Query(50, le=500)):
    act = batches[active_mask(batches)].reset_index(drop=True)
    out = []
    for (_, b), s in zip(act.iterrows(), predictor.score_batches(act)):
        if s["risk_level"] in ("HIGH", "MEDIUM"):
            out.append({**clean(b[BATCH_COLS].to_dict()), **s,
                        "reason": f"{int(b.quantity_remaining)} units left vs expected demand "
                                  f"{b.expected_demand_before_expiry:.0f} in {int(b.days_to_expiry)} day(s)"})
    out.sort(key=lambda x: (-x["expiry_risk_probability"], x["days_to_expiry"]))
    return out[:limit]


@router.get("/sales")
def sales_history(product_id: int | None = None, limit: int = Query(200, le=2000)):
    df = sales if not product_id else sales[sales.product_id == product_id]
    df = df.sort_values("date", ascending=False).head(limit)
    return [{"product_id": int(r.product_id), "date": r.date.strftime("%Y-%m-%d"), "category": r.category,
             "opening_stock": int(r.opening_stock), "units_received": int(r.units_received),
             "units_sold": int(r.units_sold), "unit_price": float(r.unit_price), "discount_pct": float(r.discount_pct),
             "waste_units": int(r.waste_units), "stockout_flag": int(r.stockout_flag)} for r in df.itertuples()]


class ForecastReq(BaseModel):
    product_id: int
    horizon_days: int = Field(default=7, ge=1, le=30)
    discount_pct: float = Field(default=0, ge=0, le=50)


@router.post("/forecast/run")
def forecast(req: ForecastReq):
    return run_forecast(req.product_id, req.horizon_days, req.discount_pct)


@router.post("/recommendations/generate")
def generate(body: dict | None = None):
    limit = int((body or {}).get("limit", 50))
    cand = batches[(batches.days_to_expiry <= 7) & (batches.quantity_remaining > 0)].copy()
    cand["expired"] = cand.days_to_expiry < 0           # sellable-but-urgent batches first, expired ones after
    urgent = cand.sort_values(["expired", "days_to_expiry"]).head(limit).drop(columns="expired").reset_index(drop=True)
    pending = {r["batch_id"] for r in RECS if r["status"] == "PENDING"}
    created = []
    for (_, b), s in zip(urgent.iterrows(), predictor.score_batches(urgent)):
        if int(b.batch_id) in pending:
            continue
        rec = build_rec(b, s)
        if rec:
            rec.update(recommendation_id=len(RECS) + 1, status="PENDING", final_discount_pct=None,
                       decided_at=None, created_at=pd.Timestamp.now().isoformat())
            RECS.append(rec)
            created.append(rec)
    return {"created": len(created), "items": created}


@router.get("/recommendations")
def list_recs(status: str | None = None, limit: int = 100):
    rows = [r for r in RECS if not status or r["status"] == status]
    return list(reversed(rows))[:limit]


@router.patch("/recommendations/{rec_id}")
def decide(rec_id: int, body: Decision):
    rec = next((r for r in RECS if r["recommendation_id"] == rec_id), None)
    if not rec:
        raise HTTPException(404, "Recommendation not found")
    if rec["status"] != "PENDING":
        raise HTTPException(409, f"Already {rec['status']}")
    if body.status == "MODIFIED" and body.final_discount_pct is None:
        raise HTTPException(422, "final_discount_pct is required when modifying")
    b = batches[batches.batch_id == rec["batch_id"]].iloc[0]
    final = body.final_discount_pct if body.status == "MODIFIED" else rec["suggested_discount_pct"]
    if body.status != "REJECTED" and final is not None:
        if b.days_to_expiry < 0:
            raise HTTPException(422, "Expired stock cannot be discounted or sold")
        if b.unit_price * (1 - final / 100) < b.unit_cost:
            raise HTTPException(422, "Discount would price the product below unit cost")
    rec.update(status=body.status, final_discount_pct=final, decided_at=pd.Timestamp.now().isoformat())
    return rec


@router.get("/waste-logs")
def waste_logs(limit: int = 300):
    w = sales[sales.waste_units > 0].sort_values("date", ascending=False).head(limit)
    return [{"waste_id": i, "product_id": int(r.product_id), "product_name": name_of[r.product_id], "batch_id": None,
             "waste_date": r.date.strftime("%Y-%m-%d"), "units_wasted": int(r.waste_units),
             "waste_cost": float(r.waste_units * cost_of[r.product_id]), "reason": "recorded daily waste"}
            for i, r in enumerate(w.itertuples(), 1)]


@router.get("/waste-logs/summary")
def waste_summary():
    w = sales[sales.waste_units > 0].copy()
    w["cost"] = w.waste_units * w.product_id.map(cost_of)
    g = w.groupby("product_id").agg(units=("waste_units", "sum"), cost=("cost", "sum")).reset_index()
    return [{"product_name": name_of[r.product_id], "units": int(r.units), "cost": float(r.cost)} for r in g.itertuples()]


@router.get("/models/metrics")
def metrics():
    return {"active": {"forecast": predictor.forecast_version, "expiry_risk": predictor.risk_version},
            "metrics": predictor.metrics(), "runs": []}


app = FastAPI(title="WasteWise AI Lite", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
