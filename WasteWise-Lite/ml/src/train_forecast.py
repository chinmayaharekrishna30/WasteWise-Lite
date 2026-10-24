"""Train demand-forecast models (baselines + XGBoost) with a CHRONOLOGICAL split."""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from feature_engineering import FORECAST_FEATURES, build_forecast_training_frame, forecast_row  # noqa: E402
from preprocessing import load_daily_sales  # noqa: E402

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
VERSION = "demand-forecast-v1"


def make_regressor():
    try:
        from xgboost import XGBRegressor
        return "xgboost", XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9,
                                       colsample_bytree=0.9, random_state=42, n_jobs=1)
    except Exception:  # xgboost not installed -> documented sklearn fallback
        from sklearn.ensemble import HistGradientBoostingRegressor
        return "sklearn_hist_gradient_boosting", HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.05, max_depth=4, random_state=42)


def metrics(y, p) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    mae = float(np.mean(np.abs(y - p)))
    rmse = float(np.sqrt(np.mean((y - p) ** 2)))
    wape = float(np.abs(y - p).sum() / max(y.sum(), 1e-9))
    return {"MAE": round(mae, 3), "RMSE": round(rmse, 3), "WAPE": round(wape, 4)}


def chrono_split(df: pd.DataFrame, train=0.70, val=0.15):
    dates = np.sort(df["date"].unique())
    t_end, v_end = dates[int(len(dates) * train)], dates[int(len(dates) * (train + val))]
    return df[df["date"] < t_end], df[(df["date"] >= t_end) & (df["date"] < v_end)], df[df["date"] >= v_end]


def horizon_eval(model, sales: pd.DataFrame, test_start, horizon=7) -> dict:
    """Recursive 7-day-ahead forecast from weekly origins in the test period (the real use case)."""
    act, mod, base = [], [], []
    for pid, g in sales.sort_values("date").groupby("product_id"):
        g = g.reset_index(drop=True)
        cat, starts = g["category"].iloc[0], g.index[g["date"] >= test_start]
        for s in starts[::horizon]:
            if s + horizon > len(g):
                break
            hist = list(g["units_sold"].iloc[:s].astype(float))
            b = float(np.mean(hist[-7:]))
            h2, pred = list(hist), 0.0
            for k in range(horizon):
                r = g.iloc[s + k]
                row = forecast_row(h2, r["date"], r["unit_price"], r["discount_pct"], pid, cat)
                yhat = max(0.0, float(model.predict(pd.DataFrame([row])[FORECAST_FEATURES])[0]))
                pred += yhat
                h2.append(yhat)
            act.append(float(g["units_sold"].iloc[s:s + horizon].sum()))
            mod.append(pred)
            base.append(b * horizon)
    return {"n_windows": len(act), "model_7day_total": metrics(act, mod), "baseline_7day_total": metrics(act, base)}


def main():
    sales = load_daily_sales()
    frame = build_forecast_training_frame(sales)
    frame = frame[frame["stockout_flag"] == 0]          # stockout sales are censored demand
    train, val, test = chrono_split(frame)
    print(f"rows  train={len(train)}  val={len(val)}  test={len(test)}")

    algo, model = make_regressor()
    model.fit(train[FORECAST_FEATURES], train["target"])

    res = {
        "model_version": VERSION, "algorithm": algo, "features": FORECAST_FEATURES,
        "split": {"train_rows": len(train), "val_rows": len(val), "test_rows": len(test),
                  "test_start": str(test["date"].min().date())},
        "baseline_last7_mean": {"val": metrics(val["target"], val["roll_mean_7"]),
                                "test": metrics(test["target"], test["roll_mean_7"])},
        "baseline_seasonal_naive_lag7": {"val": metrics(val["target"], val["lag_7"]),
                                         "test": metrics(test["target"], test["lag_7"])},
        "model": {"val": metrics(val["target"], np.maximum(0, model.predict(val[FORECAST_FEATURES]))),
                  "test": metrics(test["target"], np.maximum(0, model.predict(test[FORECAST_FEATURES])))},
    }
    # refit on train+val before saving; the reported test numbers come from the train-only fit
    res["horizon_7day_test"] = horizon_eval(model, sales, test["date"].min())
    _, final = make_regressor()
    trainval = pd.concat([train, val])
    final.fit(trainval[FORECAST_FEATURES], trainval["target"])

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final, "features": FORECAST_FEATURES, "version": VERSION}, ARTIFACTS / "forecast_model.joblib")
    (ARTIFACTS / "forecast_metrics.json").write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
