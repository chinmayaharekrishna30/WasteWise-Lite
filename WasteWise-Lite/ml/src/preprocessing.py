"""Load + clean the raw CSVs and write interim/processed copies."""
from pathlib import Path

import pandas as pd

ML_DIR = Path(__file__).resolve().parents[1]
RAW, INTERIM, PROCESSED = (ML_DIR / "data" / d for d in ("raw", "interim", "processed"))


def load_daily_sales(raw_dir: Path = RAW) -> pd.DataFrame:
    df = pd.read_csv(raw_dir / "perishable_inventory.csv", parse_dates=["date"])
    df = df.drop_duplicates(["product_id", "date"]).sort_values(["product_id", "date"]).reset_index(drop=True)
    return df


def load_batches(raw_dir: Path = RAW) -> pd.DataFrame:
    df = pd.read_csv(raw_dir / "inventory_batches.csv", parse_dates=["received_at", "snapshot_date", "expiry_date"])
    return df.sort_values(["snapshot_date", "batch_id"]).reset_index(drop=True)


def load_products(raw_dir: Path = RAW) -> pd.DataFrame:
    return pd.read_csv(raw_dir / "products.csv")


def build_processed() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    sales, batches = load_daily_sales(), load_batches()
    sales.to_csv(INTERIM / "daily_sales_clean.csv", index=False)
    batches.to_csv(INTERIM / "batches_clean.csv", index=False)
    from feature_engineering import build_forecast_training_frame, build_risk_features
    build_forecast_training_frame(sales).to_csv(PROCESSED / "forecast_features.csv", index=False)
    rf = build_risk_features(batches)
    rf["expiry_risk_label"] = batches["expiry_risk_label"].values
    rf["snapshot_date"] = batches["snapshot_date"].values
    rf.to_csv(PROCESSED / "risk_features.csv", index=False)
    print("processed files written to", PROCESSED)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    build_processed()
