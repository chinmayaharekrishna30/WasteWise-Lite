"""Print a summary of the saved model metrics (written by the train_* scripts)."""
import json
from pathlib import Path

ART = Path(__file__).resolve().parents[1] / "artifacts"

for name in ("forecast_metrics.json", "expiry_risk_metrics.json"):
    p = ART / name
    if not p.exists():
        print(f"{name}: not found - run the training scripts first")
        continue
    d = json.loads(p.read_text())
    print(f"\n=== {name}  ({d.get('model_version')} / {d.get('algorithm')}) ===")
    for k, v in d.items():
        if k in ("features", "model_version", "algorithm"):
            continue
        print(f"{k}: {json.dumps(v)}")
