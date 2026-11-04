import pytest

from static_concat_controls import greedy_selection, inherited_topk, budget_prefix


def test_unrestricted_replays_archived_greedy_rules(monkeypatch):
    import run_confirmatory_nested as archived
    values = {("a",): .7, ("b",): .7, ("c",): .5,
              ("a", "b"): .8, ("b", "c"): .75, ("a", "b", "c"): .79}
    evaluate = lambda subset: values[tuple(sorted(subset))]
    monkeypatch.setattr(archived, "inner_score", lambda cache, subset, *args, **kwargs: evaluate(subset))
    old, quality, history = archived.greedy({}, list("abc"), None, None, None, "svm", 42, 8, n_jobs=1)
    result = greedy_selection(list("abc"), evaluate, dict.fromkeys("abc", 1))
    assert result["selected"]["blocks"] == sorted(old)
    assert result["selected"]["inner_f1"] == quality
    assert [h["added"] for h in result["history"]] == [h["added"] for h in history]
    assert result["history"][0]["added"] == "b"  # archived lexicographically greatest tie


def test_two_low_gains_stop_and_return_best_not_last():
    def evaluate(subset):
        return {1: .8, 2: .8005, 3: .79, 4: .99}[len(subset)]
    result = greedy_selection(list("abcd"), evaluate, dict.fromkeys("abcd", 1))
    assert len(result["history"]) == 3
    assert result["selected"]["k"] == 2


def test_budget_gfs_never_scores_infeasible_candidates():
    visited = []
    def evaluate(subset):
        visited.append(subset)
        return .5 + .01 * len(subset)
    result = greedy_selection(list("abc"), evaluate, {"a": 5, "b": 50, "c": 6}, budget=12)
    assert result["selected"]["blocks"] == ["a", "c"]
    assert all("b" not in subset for subset in visited)


def test_topk_inherits_gfs_size_even_if_its_own_score_is_worse():
    result = inherited_topk(list("abc"), {"feasible": True, "selected": {"k": 2}},
                            lambda _: .1, dict.fromkeys("abc", 1))
    assert result["selected"]["blocks"] == ["a", "b"]
    assert result["selected"]["k"] == 2
    assert result["k_source"] == "unrestricted_gfs"


def test_infeasible_prefix_does_not_skip_expensive_rank_leader():
    result = budget_prefix(list("abc"), lambda _: pytest.fail("infeasible prefix fitted"),
                           {"a": 100, "b": 1, "c": 1}, 15)
    assert not result["feasible"] and result["selected"] is None


def test_budget_prefix_chooses_internal_f1_not_largest_k():
    result = budget_prefix(list("abc"), lambda s: {1: .8, 2: .9, 3: .7}[len(s)],
                           dict.fromkeys("abc", 1), 15)
    assert result["selected"]["k"] == 2
    assert result["k_source"] != "unrestricted_gfs"


@pytest.mark.parametrize("budget", [-1, float("nan")])
def test_invalid_budget_fails(budget):
    with pytest.raises(ValueError):
        greedy_selection(["a"], lambda _: .5, {"a": 1}, budget=budget)
