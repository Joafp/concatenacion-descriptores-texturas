"""Input contracts: no estimator is fitted in these preparation checks."""
import numpy as np
import pytest

from scripts.prepare_top4_fixed_cascade import cost_coverage, disjoint_indices, duplicate_exclusions, fixed_four


def row(**changes):
    result = dict(dataset="DTD", classifier="svm", seed="42", k="4", outer_fold="0",
                  selected="a+b+c+d", macro_f1="0.1")
    result.update(changes)
    return result


def test_saved_ranking_is_not_reselected_by_external_f1():
    assert fixed_four([row(macro_f1="0.01"), row(seed="123", macro_f1="1.0")], "DTD") == {0: ["a", "b", "c", "d"]}


def test_duplicate_condition_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        fixed_four([row(), row(selected="e+f+g+h")], "DTD")


@pytest.mark.parametrize("selected", ["a+b+c", "a+b+c+d+e", "a+a+b+c", "a+b+c+"])
def test_exactly_four_unique_nonempty_blocks(selected):
    with pytest.raises(ValueError, match="four unique"):
        fixed_four([row(selected=selected)], "DTD")


def test_ngram_extension_cannot_be_substituted_for_e1():
    with pytest.raises(ValueError, match="not E5"):
        fixed_four([row(selected="a+b+c+rgb_ngram_svd")], "DTD")


def test_split_must_be_complete_disjoint_and_nonempty():
    disjoint_indices(np.array([0, 2]), np.array([1, 3]), 4)
    for train, test in (([0, 0], [1, 2, 3]), ([0, 1], [1, 2, 3]), ([0], [2, 3]), ([], [0, 1, 2, 3])):
        with pytest.raises(ValueError):
            disjoint_indices(np.array(train), np.array(test), 4)


def test_only_explicit_duplicate_purge_accounts_for_unused_rows():
    rows = [dict(group="same", split_1="train"), dict(group="same", split_1="test"),
            dict(group="other", split_1="val")]
    excluded = duplicate_exclusions(rows, "official1")
    assert excluded == [0]
    assert duplicate_exclusions(rows, "official1_inverted") == [0]
    disjoint_indices(np.array([2]), np.array([1]), 3, excluded)
    with pytest.raises(ValueError, match="exclusions"):
        disjoint_indices(np.array([2]), np.array([1]), 3, [0, 1])


def test_missing_cost_cannot_silently_use_a_proxy_or_zero():
    costs, missing = cost_coverage(["a", "b", "a"], {"a": 10.0})
    assert costs == {"a": 10.0, "b": None}
    assert missing == ["b"]
