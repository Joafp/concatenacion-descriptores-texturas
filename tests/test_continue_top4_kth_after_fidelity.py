"""Only the two never-fitted cases may change their previously missing costs."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from continue_top4_kth_after_fidelity import accepted_costs, prepare_conditions, representation_sources, ALLOWED, CODE_DEPENDENCIES


def test_classifier_dependencies_resolve_to_existing_source_files():
    assert all(p.is_file() for p in CODE_DEPENDENCIES)
    assert ROOT / "src/run_confirmatory_nested.py" in CODE_DEPENDENCIES


def test_every_array_read_by_pending_cases_has_a_parent_hash_and_exists():
    parent = json.loads((ROOT / "results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1/protocol_frozen.json").read_text())
    sources = representation_sources(parent, parent["conditions"])
    assert len(sources) == 12
    assert all((ROOT / name).is_file() and len(digest) == 64 for name, digest in sources.items())


def test_partial_or_failed_fidelity_profile_cannot_start_e1():
    with pytest.raises(ValueError):
        accepted_costs({"status": "requires_review", "blocks": {"eva02_base": {}}})
    profile = {"status": "complete", "evaluated_calls": 66, "warmup_calls": 10,
               "blocks": {name: {"mean_ms": 1., "min_reference_cosine": 1., "n_timed_images": 33}
                          for name in ["eva02_base", "siglip_base"]}}
    assert set(accepted_costs(profile)) == {"eva02_base", "siglip_base"}
    profile["blocks"]["siglip_base"]["min_reference_cosine"] = .9989
    with pytest.raises(ValueError):
        accepted_costs(profile)


def test_only_two_cost_mappings_change_all_other_conditions_and_inputs_stay_identical():
    parent = json.loads((ROOT / "results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1/protocol_frozen.json").read_text())
    proposal = json.loads((ROOT / "results/analysis/kth_reference_validation_proposal_20261115_v1/proposal.json").read_text())
    original = copy.deepcopy(parent)
    conditions = prepare_conditions(parent, proposal, {"eva02_base": 12., "siglip_base": 13.})
    assert parent == original
    assert len(conditions) == 27
    for before, after in zip(parent["conditions"], conditions, strict=True):
        if before["id"] not in ALLOWED:
            assert before == after
        else:
            assert not after["missing_component_costs"]
            for key, value in before.items():
                if key not in ["component_costs_ms", "missing_component_costs"]:
                    assert after[key] == value
            constants = proposal["continuation_only_if_both_blocks_pass"]["accepted_component_costs_to_preserve_exactly"]
            for block, value in after["component_costs_ms"].items():
                if block in constants:
                    assert value == constants[block]["mean_ms"]
