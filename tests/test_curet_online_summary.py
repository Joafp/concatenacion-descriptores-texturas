import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/summarize_curet_online.py"
    spec = importlib.util.spec_from_file_location("curet_online_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def panel(mod):
    frames = [pd.DataFrame([dict(policy=p, repeat=0, row_index=i, label=i % 2,
        prediction=i % 2, escalated=False, ms=float(fold + 1))
        for p in mod.POLICIES for i in range(fold * 2, fold * 2 + 2)]) for fold in range(2)]
    metrics = [pd.DataFrame([dict(policy=p, macro_f1_online=1.) for p in mod.POLICIES])] * 2
    return frames, metrics, {i: i % 2 for i in range(4)}


def test_two_directions_combined_from_calls():
    mod = module()
    frames, metrics, truth = panel(mod)
    calls, _, result = mod.combine(frames, metrics, truth, 4)
    assert len(calls) == 20 and (result.conditions == 2).all()
    assert (result.mean_ms == 1.5).all() and (result.mean_direction_macro_f1_online == 1.).all()


def test_missing_direction_refused():
    mod = module()
    frames, metrics, truth = panel(mod)
    with pytest.raises(ValueError, match="two complete"):
        mod.combine(frames[:1], metrics[:1], truth, 4)


def test_overlap_refused():
    mod = module()
    frames, metrics, truth = panel(mod)
    frames[1].loc[frames[1].row_index == 2, "row_index"] = 0
    with pytest.raises(ValueError, match="repeat external"):
        mod.combine(frames, metrics, truth, 4)


def test_continuation_path_only_for_identical_scientific_condition():
    mod = module()
    job = dict(id="case", config="cfg", config_sha256="sha", dataset="CUReT",
               classifier="resmlp", seed=42, outer_fold=1, online_run="old")
    new = dict(job, online_run="new")
    assert mod.merge_jobs([job], {"case": new})[0]["online_run"] == "new"
    new["config_sha256"] = "different"
    with pytest.raises(ValueError, match="scientific condition"):
        mod.merge_jobs([job], {"case": new})
