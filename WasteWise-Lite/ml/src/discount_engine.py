"""Discount recommendation engine.

The demand response to a discount is LEARNED FROM THE SIMULATED SCENARIO FILE
(discount_scenarios_simulated.csv). It is therefore a simulation-based estimate, not a real
price elasticity - the API and UI label it as such.

Training:   python -m src.discount_engine
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from .config import ARTIFACT_DIR, DISCOUNT_GRID, DISCOUNT_MODEL_PATH, DISCOUNT_VERSION
from .preprocessing import load_batches, load_discounts

MIN_MARGIN_PCT = 0.05  # never recommend a price below cost * (1 + 5%)


def fit_uplift_table() -> dict:
    """Mean demand multiplier per (category, discount) from rows not capped by remaining stock."""
    d = load_discounts().merge(
        load_batches()[["batch_id", "category", "expected_demand_before_expiry"]], on="batch_id")
    d = d[(d["days_to_expiry"] > 0) & (d["expected_demand_before_expiry"] > 0)
          & (d["estimated_units_sold_simulated"] < d["quantity_remaining"])]
    d["mult"] = d["estimated_units_sold_simulated"] / d["expected_demand_before_expiry"]
    table = d.groupby(["category", "discount_pct"])["mult"].mean().unstack("discount_pct")
    base = table[0]
    table = table.div(base, axis=0)  # normalise so 0% discount == 1.0
    return {cat: {str(int(c)): float(v) for c, v in row.items()} for cat, row in table.iterrows()}


def train() -> dict:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": DISCOUNT_VERSION,
        "source": "discount_scenarios_simulated.csv (SIMULATED)",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "uplift": fit_uplift_table(),
    }
    DISCOUNT_MODEL_PATH.write_text(json.dumps(payload, indent=2))
    return payload


def load_uplift() -> dict:
    if not DISCOUNT_MODEL_PATH.exists():
        return train()
    return json.loads(DISCOUNT_MODEL_PATH.read_text())


def evaluate_scenarios(*, quantity: float, baseline_demand: float, unit_price: float, unit_cost: float,
                       days_to_expiry: int, category: str, uplift: dict | None = None,
                       grid: list[int] | None = None, min_margin_pct: float = MIN_MARGIN_PCT) -> list[dict]:
    """Expected units / revenue / margin for each discount in the grid.

    expected_units = min(quantity, baseline_demand * uplift(category, discount)).
    Margin = revenue - cost of ALL units (unsold units are written off at cost).
    """
    uplift = uplift or load_uplift()
    table = uplift["uplift"].get(category) or {}
    out = []
    for d in grid or DISCOUNT_GRID:
        mult = table.get(str(d), 1.0)
        units = float(min(quantity, max(0.0, baseline_demand) * mult))
        price = unit_price * (1 - d / 100.0)
        revenue = units * price
        waste_units = max(0.0, quantity - units)
        waste_cost = waste_units * unit_cost
        out.append({
            "discount_pct": d,
            "expected_units_sold": round(units, 1),
            "expected_revenue": round(revenue, 2),
            "expected_margin": round(revenue - quantity * unit_cost, 2),
            "expected_waste_units": round(waste_units, 1),
            "expected_waste_cost": round(waste_cost, 2),
            "sell_through": round(units / quantity, 3) if quantity else 0.0,
            "feasible": bool(price >= unit_cost * (1 + min_margin_pct)) and days_to_expiry > 0,
        })
    return out


def choose_best(scenarios: list[dict]) -> dict | None:
    feasible = [s for s in scenarios if s["feasible"]]
    if not feasible:
        return None
    best = max(feasible, key=lambda s: (s["expected_margin"], -s["discount_pct"]))
    return best


if __name__ == "__main__":
    p = train()
    print(json.dumps(p, indent=2))
