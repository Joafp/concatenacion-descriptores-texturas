"""Merged coverage requires every original candidate image to pass."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from merge_kth_reference_component_profiles import validate_calls


def inputs():
    samples = json.loads((ROOT / "results/analysis/kth_reference_validation_proposal_20261115_v1/proposal.json").read_text())["images"]
    calls = json.loads((ROOT / "results/analysis/kth_reference_validation_20261115_v1/eva02_base_calls.json").read_text())
    return calls, samples


def test_real_accepted_calls_use_every_frozen_image_in_order():
    calls, samples = inputs()
    validate_calls(calls, "eva02_base", samples)


@pytest.mark.parametrize("change", ["partial", "order", "below_threshold", "input", "timing"])
def test_partial_changed_or_failed_calls_cannot_form_a_complete_profile(change):
    calls, samples = inputs()
    if change == "partial":
        calls.pop()
    elif change == "order":
        calls.reverse()
    elif change == "below_threshold":
        calls[0]["reference_cosine"] = .9989
    elif change == "input":
        calls[0]["input_pixel_sha256"] = "0" * 64
    else:
        calls[0]["ms"] = float("nan")
    with pytest.raises(ValueError):
        validate_calls(calls, "eva02_base", samples)
