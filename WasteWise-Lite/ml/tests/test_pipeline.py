"""ML unit tests. Run from ml/:  python -m pytest tests -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from src.data_validation import validate_frame  # noqa: E402
from src.discount_engine import choose_best, evaluate_scenarios  # noqa: E402
from src.feature_engineering import build_forecast_frame, build_risk_features  # noqa: E402
from src.preprocessing import chronological_split, load_batches, load_sales  # noqa: E402
from src.predict import risk_level  # noqa: E402


def test_raw_data_valid():
    assert validate_frame(load_sales(), "sales")["ok"]
    assert validate_frame(load_batches(), "batches")["ok"]


def test_validation_detects_missing_columns():
    rep = validate_frame(pd.DataFrame({"product_id": [1]}), "sales")
    assert not rep["ok"] and rep["missing_columns"]


def test_no_leakage_in_lags():
    frame = build_forecast_frame(load_sales())
    g = frame[frame.product_id == frame.product_id.iloc[0]].reset_index(drop=True)
    assert (g["lag1"].iloc[1:].values == g["units_sold"].iloc[:-1].values).all()


def test_chronological_split_order():
    s = load_sales()
    tr, va = chronological_split(s["date"], 0.7, 0.15)
    assert tr < va <= s["date"].max()


def test_risk_features_exclude_outcomes():
    f = build_risk_features(load_batches())
    assert "waste_units_actual_simulated" not in f.columns
    assert "expiry_risk_label" not in f.columns


def test_risk_level_rules():
    assert risk_level(0.9, -1, 10) == "EXPIRED"
    assert risk_level(0.9, 3, 10) == "HIGH"
    assert risk_level(0.5, 3, 10) == "MEDIUM"
    assert risk_level(0.1, 3, 10) == "LOW"
    assert risk_level(0.9, 3, 0) == "NONE"


def test_discount_never_below_margin_and_never_for_expired():
    sc = evaluate_scenarios(quantity=100, baseline_demand=50, unit_price=30, unit_cost=29,
                            days_to_expiry=3, category="Dairy")
    assert not any(s["feasible"] for s in sc if s["discount_pct"] >= 5)
    expired = evaluate_scenarios(quantity=100, baseline_demand=50, unit_price=100, unit_cost=10,
                                 days_to_expiry=-1, category="Dairy")
    assert choose_best(expired) is None
