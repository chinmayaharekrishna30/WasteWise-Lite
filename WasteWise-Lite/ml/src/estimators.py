"""Estimator factory: XGBoost when installed, otherwise scikit-learn gradient boosting."""
from __future__ import annotations

try:  # pragma: no cover - depends on environment
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGB = True
except Exception:  # xgboost missing or failed to load its native lib
    HAS_XGB = False

from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor


def make_regressor(seed: int = 42):
    if HAS_XGB:
        return XGBRegressor(
            n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9,
            colsample_bytree=0.9, objective="reg:squarederror", random_state=seed, n_jobs=1,
        )
    return HistGradientBoostingRegressor(max_depth=4, learning_rate=0.05, max_iter=300, random_state=seed)


def make_classifier(seed: int = 42):
    if HAS_XGB:
        return XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9,
            colsample_bytree=0.9, eval_metric="logloss", random_state=seed, n_jobs=1,
        )
    return HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=300, random_state=seed)


def estimator_name(est) -> str:
    return type(est).__name__
