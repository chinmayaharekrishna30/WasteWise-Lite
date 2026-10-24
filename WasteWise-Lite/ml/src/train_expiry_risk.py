"""Train the expiry-risk classifier. The label is SIMULATED (see docs/model_card.md)."""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import (average_precision_score, f1_score, precision_score, recall_score,
                             roc_auc_score)

sys.path.insert(0, str(Path(__file__).parent))
from feature_engineering import RISK_FEATURES, build_risk_features  # noqa: E402
from preprocessing import load_batches  # noqa: E402

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
VERSION = "expiry-risk-v1"


def make_classifier(pos_weight: float):
    try:
        from xgboost import XGBClassifier
        return "xgboost", XGBClassifier(n_estimators=250, max_depth=4, learning_rate=0.05, subsample=0.9,
                                        colsample_bytree=0.9, scale_pos_weight=pos_weight, eval_metric="logloss",
                                        random_state=42, n_jobs=1)
    except Exception:
        from sklearn.ensemble import HistGradientBoostingClassifier
        return "sklearn_hist_gradient_boosting", HistGradientBoostingClassifier(
            max_iter=250, learning_rate=0.05, max_depth=4, random_state=42)


def cls_metrics(y, proba, thr=0.5) -> dict:
    pred = (proba >= thr).astype(int)
    return {"precision": round(float(precision_score(y, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
            "pr_auc": round(float(average_precision_score(y, proba)), 4),
            "roc_auc": round(float(roc_auc_score(y, proba)), 4)}


def main():
    b = load_batches()                                   # sorted by snapshot_date
    X, y = build_risk_features(b), b["expiry_risk_label"].astype(int).values
    dates = np.sort(b["snapshot_date"].values)            # row-quantile cut-offs (snapshot dates are uneven)
    t_end, v_end = dates[int(len(dates) * 0.70)], dates[int(len(dates) * 0.85)]
    tr, va, te = (b["snapshot_date"] < t_end).values, ((b["snapshot_date"] >= t_end) & (b["snapshot_date"] < v_end)).values, (b["snapshot_date"] >= v_end).values
    print(f"rows train={tr.sum()} val={va.sum()} test={te.sum()}")

    pos_w = float((y[tr] == 0).sum() / max((y[tr] == 1).sum(), 1))
    algo, clf = make_classifier(pos_w)
    clf.fit(X[tr], y[tr])

    rule = (b["quantity_remaining"] > b["expected_demand_before_expiry"]).astype(float).values   # deterministic baseline
    res = {
        "model_version": VERSION, "algorithm": algo, "features": RISK_FEATURES,
        "label_note": "expiry_risk_label is SIMULATED; validate on real store outcomes before trusting.",
        "split": {"train_rows": int(tr.sum()), "val_rows": int(va.sum()), "test_rows": int(te.sum()),
                  "test_start": str(v_end)[:10]},
        "baseline_rule_surplus_gt_0": {"val": cls_metrics(y[va], rule[va]), "test": cls_metrics(y[te], rule[te])},
        "model": {"val": cls_metrics(y[va], clf.predict_proba(X[va])[:, 1]),
                  "test": cls_metrics(y[te], clf.predict_proba(X[te])[:, 1])},
        "test_positive_rate": round(float(y[te].mean()), 4),
    }
    try:
        imp = getattr(clf, "feature_importances_", None)
        if imp is not None:
            res["feature_importance"] = {f: round(float(v), 4) for f, v in sorted(zip(RISK_FEATURES, imp), key=lambda t: -t[1])}
        else:
            from sklearn.inspection import permutation_importance
            pi = permutation_importance(clf, X[te], y[te], n_repeats=5, random_state=0, scoring="average_precision")
            res["feature_importance"] = {f: round(float(v), 4) for f, v in sorted(zip(RISK_FEATURES, pi.importances_mean), key=lambda t: -t[1])}
    except Exception as e:  # importance is nice-to-have
        res["feature_importance"] = {"error": str(e)}

    algo2, final = make_classifier(pos_w)
    tv = tr | va
    final.fit(X[tv], y[tv])
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final, "features": RISK_FEATURES, "version": VERSION}, ARTIFACTS / "expiry_risk_model.joblib")
    (ARTIFACTS / "expiry_risk_metrics.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
