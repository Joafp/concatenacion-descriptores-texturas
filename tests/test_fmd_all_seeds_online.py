import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/summarize_fmd_online_all_seeds.py"
    spec = importlib.util.spec_from_file_location("fmd_three_seeds_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture():
    calls = pd.DataFrame([dict(seed=s, policy=p, repeat=0, row_index=i, ms=float(s))
        for s in (42, 123, 2026) for p in range(5) for i in range(1000)])
    folds = pd.DataFrame([dict(seed=s, policy=p, outer_fold=f, macro_f1_online=.9)
        for s in (42, 123, 2026) for p in range(5) for f in range(5)])
    return calls, folds


def test_all_seeds_and_repeated_images_across_seeds_valid():
    calls, folds = fixture()
    result = module().aggregate(calls, folds)
    assert (result.conditions == 15).all() and (result.timed_calls == 3000).all()


def test_missing_seed_rejected():
    calls, folds = fixture()
    with pytest.raises(ValueError, match="three seeds"):
        module().aggregate(calls[calls.seed != 123], folds)


def test_duplicate_call_rejected():
    calls, folds = fixture()
    with pytest.raises(ValueError, match="duplicate calls"):
        module().aggregate(pd.concat([calls, calls.iloc[:1]]), folds)
