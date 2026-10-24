import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from data_validation import validate  # noqa: E402
from feature_engineering import RISK_FEATURES, build_risk_features, forecast_row, risk_level  # noqa: E402
from preprocessing import load_batches  # noqa: E402


def test_raw_data_is_valid():
    assert validate() == []


def test_forecast_row_uses_only_past_values():
    row = forecast_row([1, 2, 3, 4, 5, 6, 7, 8], "2026-09-01", 30, 0, 1001, "Dairy")
    assert row["lag_1"] == 8 and row["lag_7"] == 2 and row["roll_mean_7"] == sum(range(2, 9)) / 7


def test_risk_features_exclude_outcomes():
    assert "waste_units_actual_simulated" not in RISK_FEATURES and "expiry_risk_label" not in RISK_FEATURES
    X = build_risk_features(load_batches().head(20))
    assert list(X.columns) == RISK_FEATURES and not X.isna().any().any()


def test_risk_level_rules():
    assert risk_level(0.99, -1) == "EXPIRED" and risk_level(0.8, 3) == "HIGH"
    assert risk_level(0.5, 3) == "MEDIUM" and risk_level(0.1, 3) == "LOW"


def test_predictor_falls_back_without_artifacts(tmp_path):
    from predict import Predictor
    p = Predictor(tmp_path)
    out = p.forecast([5.0] * 20, "2026-10-01", 7, 30, 1, "Dairy")
    assert len(out) == 7 and all(v >= 0 for v in out)
