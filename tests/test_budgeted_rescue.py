import numpy as np
import pytest

from budgeted_rescue import acquisition_cost, select_policy, singleton_frontier


def scores(pred):
    return np.eye(2)[pred] * 2 - 1


def selection(criterion="marginal_cost", budget=20, reverse=False):
    y = np.asarray([0, 0, 1, 1, 0, 1])
    members = {("cheap",): scores([0, 0, 0, 1, 0, 1]),
               ("expensive",): scores(y)}
    if reverse:
        members = dict(reversed(list(members.items())))
    return select_policy(
        {"base": scores([1, 1, 0, 1, 0, 1])}, members, y, np.arange(2),
        {"base": np.arange(6)}, {"base": 1, "cheap": 1, "expensive": 10},
        budget, quantiles=[.5], max_members=1, overhead=0, criterion=criterion)


def test_cost_ratio_and_relevance_use_same_pool_but_choose_different_members():
    cost, quality = selection(), selection("relevance")
    assert cost["selected"]["members"] == [["cheap"]]
    assert quality["selected"]["members"] == [["expensive"]]
    assert quality["selected"]["training_macro_f1"] > cost["selected"]["training_macro_f1"]
    assert cost == selection(reverse=True)


def test_budget_infeasible_and_base_only_are_distinct():
    assert selection(budget=.5)["feasible"] is False
    point = selection(budget=1.4)["selected"]
    assert point["members"] == [] and point["training_projected_ms"] == 1
    assert point["threshold"] is None


def test_shared_extractors_and_base_are_charged_once():
    latencies = {"base": 1, "shared": 2, "other": 3}
    first = acquisition_cost("base", [["base", "shared"]], .25, latencies, .5)
    duplicate = acquisition_cost("base", [["base", "shared"], ["shared"]], .25, latencies, .5)
    assert first == duplicate == 2
    assert acquisition_cost("base", [["shared"], ["shared", "other"]], .25, latencies, .5) == 2.75
    assert acquisition_cost("base", [], .25, latencies, .5) == 1


def test_no_positive_gain_stops_without_adding_free_classifiers():
    y = np.asarray([0, 1, 0, 1])
    same = scores(y)
    result = select_policy({"base": same}, {("base",): same}, y, np.arange(2),
                            {"base": np.arange(4)}, {"base": 1}, 10)
    assert result["selected"]["members"] == []
    assert all(path["steps"] == [] for path in result["paths"])


def test_base_frontier_retains_cheaper_lower_quality_option():
    y = np.asarray([0, 1, 0, 1])
    pool = {"cheap": scores([1, 1, 0, 1]), "strong": scores(y), "dominated": scores(y)}
    assert singleton_frontier(pool, y, np.arange(2), {"cheap": 1, "strong": 2, "dominated": 3}) == ["cheap", "strong"]


def test_unknown_cost_is_not_silently_assigned_zero():
    with pytest.raises(KeyError):
        acquisition_cost("base", [["missing"]], .2, {"base": 1}, 0)


def test_positive_gain_from_reusing_the_same_union_is_handled_without_infinite_json():
    y = np.asarray([0, 0, 1, 1, 0, 1])
    ab = np.asarray([[3, 0], [3, 0], [1, 0], [0, 3], [3, 0], [0, 3.]])
    a = np.asarray([[0, 1], [0, 1], [0, 3], [0, 3], [3, 0], [0, 3.]])
    result = select_policy({"base": scores([1, 1, 0, 1, 0, 1])},
                           {("a", "b"): ab, ("a",): a}, y, np.arange(2),
                           {"base": np.arange(6)}, {"base": 1, "a": 1, "b": .01},
                           10, quantiles=[.5], max_members=2, overhead=0)
    assert len(result["selected"]["members"]) == 2
    assert result["paths"][0]["steps"][-1]["merit"] == "positive_gain_zero_cost"
    assert result["selected"]["training_macro_f1"] == 1
