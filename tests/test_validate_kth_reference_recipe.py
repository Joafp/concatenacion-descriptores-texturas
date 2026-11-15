"""Acceptance and execution gates, tested without building any neural model."""
from pathlib import Path
import hashlib
import importlib.util
import json

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kth_recipe_validation", ROOT / "scripts/validate_kth_reference_recipe.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_same_vector_positive_scaling_preserves_cosine():
    x = np.array([1., 2., 3.])
    assert module.validate_vector(x, 10 * x) == pytest.approx(1)


@pytest.mark.parametrize("vector,expected", [
    ([1., 0.], [0., 1.]), ([0., 0.], [1., 1.]),
    ([float("nan"), 1.], [1., 1.]), ([1., 1.], [float("inf"), 1.]),
    ([1., 1.], [1., 1., 1.]), ([[1., 1.]], [[1., 1.]])])
def test_bad_fidelity_shape_or_finiteness_is_terminal(vector, expected):
    with pytest.raises(module.FidelityFailure):
        module.validate_vector(vector, expected)


def test_minimum_is_not_relaxed_near_boundary():
    with pytest.raises(module.FidelityFailure):
        module.validate_vector([.9989, np.sqrt(1 - .9989**2)], [1., 0.])
    assert module.validate_vector([.9991, np.sqrt(1 - .9991**2)], [1., 0.]) >= .999


def test_vision_missing_or_mismatched_weights_block_validation():
    module.check_loading_info({"missing_keys": [], "unexpected_keys": ["text_model.any"]})
    for name in ["missing_keys", "mismatched_keys", "error_msgs"]:
        with pytest.raises(module.FidelityFailure):
            module.check_loading_info({name: ["vision parameter"]})


def test_author_decision_is_bound_to_the_exact_proposal(tmp_path):
    proposal = module.PROPOSAL
    decision = tmp_path / "author.json"
    record = {"user_reply": "SI", "proposal_sha256": module.sha(proposal),
              "execute_corrected_validation": True,
              "complete_only_two_never_fitted_kth_if_both_pass": True}
    decision.write_text(json.dumps(record))
    assert module.verify_authorization(proposal, decision)["maximum_evaluated_calls"] == 66
    record["proposal_sha256"] = "0" * 64
    decision.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="author decision"):
        module.verify_authorization(proposal, decision)
