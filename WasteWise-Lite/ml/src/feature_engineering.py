"""Feature builders shared by training AND online inference (so they never drift apart)."""
from __future__ import annotations

import numpy as np
import pandas as pd

CATEGORY_CODES = {"Bakery": 0, "Beverage": 1, "Dairy": 2, "Produce": 3}

FORECAST_FEATURES = [
    "lag_1", "lag_7", "lag_14", "roll_mean_7", "roll_mean_14", "roll_mean_28",
    "dow", "month", "is_weekend", "unit_price", "discount_pct", "product_id", "category_code",
]

RISK_FEATURES = [
    "days_to_expiry", "quantity_remaining", "initial_quantity", "avg_daily_sales_7d",
    "expected_demand_before_expiry", "unit_price", "unit_cost", "discount_pct", "category_code",
    "margin_pct", "sell_through_so_far", "coverage_ratio", "surplus_units",
]


def category_code(category: str) -> int:
    return CATEGORY_CODES.get(category, -1)


# --------------------------------------------------------------------------- forecasting
def forecast_row(history: list[float], day, unit_price: float, discount_pct: float,
                 product_id: int, category: str) -> dict:
    """Features for predicting the units sold on `day`, given the sales history before it."""
    h = list(history)
    mean_all = float(np.mean(h)) if h else 0.0

    def lag(k: int) -> float:
        return float(h[-k]) if len(h) >= k else mean_all

    def roll(k: int) -> float:
        return float(np.mean(h[-k:])) if h else 0.0

    ts = pd.Timestamp(day)
    return {
        "lag_1": lag(1), "lag_7": lag(7), "lag_14": lag(14),
        "roll_mean_7": roll(7), "roll_mean_14": roll(14), "roll_mean_28": roll(28),
        "dow": ts.dayofweek, "month": ts.month, "is_weekend": int(ts.dayofweek >= 5),
        "unit_price": float(unit_price), "discount_pct": float(discount_pct),
        "product_id": int(product_id), "category_code": category_code(category),
    }


def build_forecast_training_frame(sales: pd.DataFrame, min_history: int = 14) -> pd.DataFrame:
    """One row per (product, day) with features from PAST days only (no leakage) + target."""
    rows = []
    for pid, g in sales.sort_values("date").groupby("product_id"):
        g = g.reset_index(drop=True)
        hist: list[float] = []
        for i, r in g.iterrows():
            if i >= min_history:
                feat = forecast_row(hist, r["date"], r["unit_price"], r["discount_pct"], pid, r["category"])
                feat.update(date=r["date"], target=float(r["units_sold"]), stockout_flag=int(r["stockout_flag"]))
                rows.append(feat)
            hist.append(float(r["units_sold"]))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- expiry risk
def build_risk_features(b: pd.DataFrame) -> pd.DataFrame:
    """Batch-level features. NOTE: `waste_units_actual_simulated` and the label are NEVER used."""
    out = pd.DataFrame(index=b.index)
    for c in ["days_to_expiry", "quantity_remaining", "initial_quantity", "avg_daily_sales_7d",
              "expected_demand_before_expiry", "unit_price", "unit_cost", "discount_pct"]:
        out[c] = b[c].astype(float)
    out["category_code"] = b["category"].map(category_code)
    net_price = out["unit_price"] * (1 - out["discount_pct"] / 100.0)
    out["margin_pct"] = (net_price - out["unit_cost"]) / net_price.replace(0, np.nan)
    out["margin_pct"] = out["margin_pct"].fillna(0.0)
    out["sell_through_so_far"] = 1.0 - out["quantity_remaining"] / out["initial_quantity"].clip(lower=1)
    horizon = out["days_to_expiry"].clip(lower=0)
    out["coverage_ratio"] = (out["avg_daily_sales_7d"] * horizon) / out["quantity_remaining"].clip(lower=1)
    out["surplus_units"] = (out["quantity_remaining"] - out["expected_demand_before_expiry"]).clip(lower=0)
    return out[RISK_FEATURES]


def risk_level(prob: float, days_to_expiry: int) -> str:
    if days_to_expiry < 0:
        return "EXPIRED"
    if prob >= 0.70:
        return "HIGH"
    if prob >= 0.40:
        return "MEDIUM"
    return "LOW"
