import importlib.util
from pathlib import Path

import pandas as pd

path = Path(__file__).resolve().parents[1] / "scripts/report_matched_concat_panel.py"
spec = importlib.util.spec_from_file_location("matched_panel", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_does_not_average_only_feasible_seeds():
    frame = pd.DataFrame([
        {"dataset": "D", "stage": "c", "policy": "p", "seed": 42, "complete": True, "macro_f1": .9, "projected_ms": 20.},
        {"dataset": "D", "stage": "c", "policy": "p", "seed": 123, "complete": False, "macro_f1": None, "projected_ms": None},
    ])
    row = module.aggregate(frame).iloc[0]
    assert not row.complete and row.expected_seeds == 2 and row.complete_seeds == 1
    assert pd.isna(row.macro_f1) and pd.isna(row.projected_ms)


def test_complete_mean_preserves_dataset_unit():
    frame = pd.DataFrame([
        {"dataset": "D", "stage": "c", "policy": "p", "seed": s, "complete": True, "macro_f1": f, "projected_ms": c}
        for s, f, c in [(42, .8, 10.), (123, 1., 30.)]
    ])
    row = module.aggregate(frame).iloc[0]
    assert row.complete and row.macro_f1 == .9 and row.projected_ms == 20.
