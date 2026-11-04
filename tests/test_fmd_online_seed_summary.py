import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/summarize_fmd_online_seed.py"
    spec = importlib.util.spec_from_file_location("online_seed_summary_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def panel(mod):
    frames, folds = [], []
    for fold in range(5):
        frames.append(pd.DataFrame([dict(repeat=0, policy=p, row_index=i,
            label=i % 10, prediction=i % 10, ms=fold + 1., escalated=False)
            for p in mod.POLICIES for i in range(fold * 200, (fold + 1) * 200)]))
        folds.append(pd.DataFrame([dict(policy=p, macro_f1_online=1.) for p in mod.POLICIES]))
    return frames, folds, {i: i % 10 for i in range(1000)}


def test_complete_seed_keeps_fold_and_pooled_f1_distinct():
    mod = module()
    frames, folds, labels = panel(mod)
    calls, _, result = mod.combine(frames, folds, labels, 1)
    assert len(calls) == 5000
    assert (result.conditions == 5).all()
    assert (result.mean_ms == 3.).all()
    assert (result.pooled_macro_f1_online == 1.).all()
    assert (result.mean_fold_macro_f1_online == 1.).all()


def test_missing_fold_refused():
    mod = module()
    frames, folds, labels = panel(mod)
    with pytest.raises(ValueError, match="five complete"):
        mod.combine(frames[:4], folds[:4], labels, 1)


def test_repeated_external_image_refused():
    mod = module()
    frames, folds, labels = panel(mod)
    frames[1].loc[frames[1].row_index == 200, "row_index"] = 0
    with pytest.raises(ValueError, match="repeat external"):
        mod.combine(frames, folds, labels, 1)
