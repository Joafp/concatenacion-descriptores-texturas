import pandas as pd
import pytest
from batch1_call_audit import summarize_calls


def frame():
    return pd.DataFrame([{"repeat": rep, "row_index": row, "label": row, "policy": p,
        "prediction": row, "escalated": False, "ms": 10. + row}
        for rep in (0, 1) for row in (0, 1) for p in ("static", "adaptive")])


def check(f):
    return summarize_calls(f, ["static", "adaptive"], [0, 1], {0: 0, 1: 1}, [0, 1], 2)


def test_repeats_do_not_inflate_quality_population():
    result = check(frame())
    assert (result.external_images == 2).all() and (result.timed_calls == 4).all()
    assert (result.macro_f1_online == 1).all() and (result.mean_ms == 10.5).all()


def test_rejects_missing_calls():
    with pytest.raises(ValueError, match="coverage"):
        check(frame().iloc[1:])


def test_rejects_duplicate_calls():
    f = frame()
    with pytest.raises(ValueError, match="duplicate"):
        check(pd.concat([f, f.iloc[:1]]))


def test_rejects_unstable_predictions():
    f = frame()
    f.loc[0, "prediction"] = 1
    with pytest.raises(ValueError, match="unstable"):
        check(f)


def test_rejects_nonfinite_time():
    f = frame()
    f.loc[0, "ms"] = float("nan")
    with pytest.raises(ValueError, match="latency"):
        check(f)
