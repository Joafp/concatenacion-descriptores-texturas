import copy
import pytest
from physical_comparison_panel import checked_recipe, concat_recipe, locate, verify_sources, digest


def test_preserves_permanent_vote_multiplicity_without_mutating_recipe():
    recipe = {"members": [["a", "b"], ["a", "b"], ["c"]]}
    snapshot = copy.deepcopy(recipe)
    result = checked_recipe(recipe, ["a", "b", "c"])
    assert result == snapshot and recipe == snapshot
    result["members"][0].append("c")
    assert recipe == snapshot


@pytest.mark.parametrize("recipe", [
    {"members": []}, {"members": [["unknown"]]},
    {"members": [["a", "a"]]}, {"members": [[]]},
    {"base": "a", "members": [["b"]], "threshold": None},
    {"base": "a", "members": [["b"]], "threshold": float("nan")},
])
def test_refuses_malformed_routes(recipe):
    with pytest.raises(ValueError):
        checked_recipe(recipe, ["a", "b"])


def test_base_only_and_strict_gate_parameters_are_retained():
    assert checked_recipe({"base": "a", "members": [], "threshold": None}, ["a"])["members"] == []
    r = checked_recipe({"base": "a", "members": [["b"]], "threshold": .3}, ["a", "b"])
    assert r["threshold"] == .3


def test_concat_keeps_selected_feature_order_and_does_not_apply_a_new_ranking():
    choice = {"feasible": True, "selected": {"blocks": ["z", "a"]}}
    assert concat_recipe(choice, ["a", "z"])["members"] == [["z", "a"]]
    with pytest.raises(ValueError):
        concat_recipe({"feasible": False}, ["a"])


def test_relocates_only_known_linux_repo_paths(tmp_path):
    assert locate(tmp_path, "/home/joaquin/tesis_claude/results/a") == tmp_path / "results/a"
    with pytest.raises(ValueError):
        locate(tmp_path, "/some/other/repository/a")
    with pytest.raises(ValueError):
        locate(tmp_path, "../outside.json")


def test_source_binding_rejects_missing_modified_or_conflicting_hashes(tmp_path):
    source = tmp_path / "recipe.json"
    source.write_text("{}")
    audit = {"input_sha256": {"recipe.json": digest(source)}}
    assert verify_sources(tmp_path, [source], [audit]) == audit["input_sha256"]
    with pytest.raises(ValueError, match="absent"):
        verify_sources(tmp_path, [source], [{"input_sha256": {}}])
    with pytest.raises(ValueError, match="conflicting"):
        verify_sources(tmp_path, [source], [audit, {"input_sha256": {"recipe.json": "wrong"}}])
    source.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="changed"):
        verify_sources(tmp_path, [source], [audit])
