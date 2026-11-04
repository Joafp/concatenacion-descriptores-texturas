import pandas as pd
import pytest
from local_comparison_audit import paired_frames, unique_conditions


def frame():
    return pd.DataFrame({"dataset": ["FMD", "FMD"], "seed": [42, 42],
        "outer_fold": [0, 1], "macro_f1": [.9, .8]})


def test_rejects_duplicate_even_when_scores_match():
    f = frame()
    with pytest.raises(ValueError, match="duplicate"):
        unique_conditions(pd.concat([f, f.iloc[:1]]), "test")


def test_rejects_missing_condition():
    with pytest.raises(ValueError, match="identical"):
        paired_frames({"a": frame(), "b": frame().iloc[:1]})


def test_pairs_by_key_not_row_order():
    result = paired_frames({"a": frame(), "b": frame().iloc[::-1]})
    assert result.a.equals(result.b)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -.1, 1.1])
def test_rejects_invalid_metric(value):
    f = frame()
    f.loc[0, "macro_f1"] = value
    with pytest.raises(ValueError, match="invalid"):
        unique_conditions(f, "test")
