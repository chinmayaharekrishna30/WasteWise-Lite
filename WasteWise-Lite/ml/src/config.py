"""Shared paths and constants for the ML pipeline."""
from __future__ import annotations

from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ML_ROOT / "data" / "raw"
INTERIM_DIR = ML_ROOT / "data" / "interim"
PROCESSED_DIR = ML_ROOT / "data" / "processed"
ARTIFACT_DIR = ML_ROOT / "artifacts"

FILES = {
    "products": RAW_DIR / "products.csv",
    "batches": RAW_DIR / "inventory_batches.csv",
    "sales": RAW_DIR / "perishable_inventory.csv",
    "discounts": RAW_DIR / "discount_scenarios_simulated.csv",
}

FORECAST_MODEL_PATH = ARTIFACT_DIR / "forecast_model.joblib"
RISK_MODEL_PATH = ARTIFACT_DIR / "expiry_risk_model.joblib"
DISCOUNT_MODEL_PATH = ARTIFACT_DIR / "discount_response.json"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"

FORECAST_VERSION = "demand-forecast-v1"
RISK_VERSION = "expiry-risk-v1"
DISCOUNT_VERSION = "discount-response-sim-v1"

# Chronological split fractions (by date, never random).
TRAIN_FRAC = 0.70
VAL_FRAC = 0.15  # remaining 0.15 is the test period

# Risk thresholds on the predicted probability.
RISK_HIGH = 0.70
RISK_MEDIUM = 0.40

DISCOUNT_GRID = [0, 5, 10, 15, 20]

CATEGORIES = ["Bakery", "Beverage", "Dairy", "Produce"]
