"""Schema + sanity checks for the CSV files in ml/data/raw."""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

REQUIRED = {
    "products.csv": ["product_id", "product_name", "category", "shelf_life_days", "selling_price", "unit_cost"],
    "inventory_batches.csv": ["batch_id", "product_id", "category", "received_at", "snapshot_date", "expiry_date",
                              "initial_quantity", "quantity_remaining", "days_to_expiry", "avg_daily_sales_7d",
                              "expected_demand_before_expiry", "unit_price", "unit_cost", "discount_pct",
                              "expiry_risk_label", "waste_units_actual_simulated"],
    "perishable_inventory.csv": ["product_id", "date", "category", "opening_stock", "units_received", "units_sold",
                                 "unit_price", "discount_pct", "days_to_expiry", "temperature_c", "waste_units",
                                 "stockout_flag"],
    "discount_scenarios_simulated.csv": ["batch_id", "product_id", "days_to_expiry", "quantity_remaining",
                                         "discount_pct", "estimated_units_sold_simulated",
                                         "estimated_revenue_simulated", "estimated_gross_margin_simulated"],
}


def validate(raw_dir: Path = RAW) -> list[str]:
    """Return a list of problems (empty list == all good)."""
    problems: list[str] = []
    frames = {}
    for fname, cols in REQUIRED.items():
        path = raw_dir / fname
        if not path.exists():
            problems.append(f"{fname}: file missing")
            continue
        df = pd.read_csv(path)
        frames[fname] = df
        missing = [c for c in cols if c not in df.columns]
        if missing:
            problems.append(f"{fname}: missing columns {missing}")
        nulls = int(df[[c for c in cols if c in df.columns]].isna().sum().sum())
        if nulls:
            problems.append(f"{fname}: {nulls} null values")
    if "inventory_batches.csv" in frames:
        b = frames["inventory_batches.csv"]
        if b["batch_id"].duplicated().any():
            problems.append("inventory_batches.csv: duplicate batch_id")
        if (b["quantity_remaining"] < 0).any():
            problems.append("inventory_batches.csv: negative quantity_remaining")
        if (b["quantity_remaining"] > b["initial_quantity"]).any():
            problems.append("inventory_batches.csv: remaining > initial")
    if "perishable_inventory.csv" in frames:
        p = frames["perishable_inventory.csv"]
        if p.duplicated(["product_id", "date"]).any():
            problems.append("perishable_inventory.csv: duplicate (product_id, date)")
        if (p["units_sold"] < 0).any():
            problems.append("perishable_inventory.csv: negative units_sold")
    if "products.csv" in frames and "inventory_batches.csv" in frames:
        unknown = set(frames["inventory_batches.csv"]["product_id"]) - set(frames["products.csv"]["product_id"])
        if unknown:
            problems.append(f"inventory_batches.csv: unknown product ids {sorted(unknown)}")
    return problems


if __name__ == "__main__":
    issues = validate()
    print("Data validation:", "OK" if not issues else "")
    for i in issues:
        print(" -", i)
    raise SystemExit(1 if issues else 0)
