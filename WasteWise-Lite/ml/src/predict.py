"""Online inference helpers. Models are loaded ONCE; falls back to transparent baselines if no artifact."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from feature_engineering import (FORECAST_FEATURES, RISK_FEATURES, build_risk_features,  # noqa: E402
                                 forecast_row, risk_level)

DEFAULT_ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


class Predictor:
    def __init__(self, artifact_dir: str | Path = DEFAULT_ARTIFACTS):
        self.dir = Path(artifact_dir)
        self.forecast_bundle = self._load("forecast_model.joblib")
        self.risk_bundle = self._load("expiry_risk_model.joblib")
        self.forecast_version = self.forecast_bundle["version"] if self.forecast_bundle else "baseline-last7-v0"
        self.risk_version = self.risk_bundle["version"] if self.risk_bundle else "baseline-rule-v0"

    def _load(self, name: str):
        p = self.dir / name
        try:
            return joblib.load(p) if p.exists() else None
        except Exception as e:  # corrupt / incompatible artifact
            print(f"[predict] could not load {p}: {e}")
            return None

    def metrics(self) -> dict:
        out = {}
        for key, f in (("forecast", "forecast_metrics.json"), ("expiry_risk", "expiry_risk_metrics.json")):
            p = self.dir / f
            out[key] = json.loads(p.read_text()) if p.exists() else None
        return out

    # ---- demand forecast -------------------------------------------------------------
    def forecast(self, history: list[float], start_date, horizon: int, unit_price: float,
                 product_id: int, category: str, discount_pct: float = 0.0) -> list[float]:
        """Recursive day-by-day forecast. `history` = daily units sold up to (not incl.) start_date."""
        hist, out = list(history), []
        for k in range(horizon):
            day = pd.Timestamp(start_date) + pd.Timedelta(days=k)
            if self.forecast_bundle:
                row = forecast_row(hist, day, unit_price, discount_pct, product_id, category)
                x = pd.DataFrame([row])[self.forecast_bundle["features"]]
                yhat = float(self.forecast_bundle["model"].predict(x)[0])
            else:
                yhat = float(np.mean(hist[-7:])) if hist else 0.0
            yhat = max(0.0, yhat)
            out.append(yhat)
            hist.append(yhat)
        return out

    # ---- expiry risk -----------------------------------------------------------------
    def risk_proba(self, batches: pd.DataFrame) -> np.ndarray:
        X = build_risk_features(batches)
        if self.risk_bundle:
            return self.risk_bundle["model"].predict_proba(X[self.risk_bundle["features"]])[:, 1]
        return (batches["quantity_remaining"] > batches["expected_demand_before_expiry"]).astype(float).values

    def score_batches(self, batches: pd.DataFrame) -> list[dict]:
        probs = self.risk_proba(batches)
        res = []
        for (_, b), p in zip(batches.iterrows(), probs):
            surplus = max(0.0, float(b["quantity_remaining"]) - float(b["expected_demand_before_expiry"]))
            res.append({"batch_id": int(b["batch_id"]), "expiry_risk_probability": round(float(p), 4),
                        "expected_surplus_units": round(surplus, 2),
                        "risk_level": risk_level(float(p), int(b["days_to_expiry"])),
                        "model_version": self.risk_version})
        return res
