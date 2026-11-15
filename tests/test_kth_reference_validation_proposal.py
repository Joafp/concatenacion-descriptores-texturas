"""Validate the frozen proposal without making any neural calls."""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "results/analysis/kth_reference_validation_proposal_20261115_v1"


def load():
    return json.loads((FOLDER / "proposal.json").read_text())


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def test_proposal_is_unexecuted_and_preserves_images_threshold_and_budget():
    p = load()
    assert not p["execution_authorized"] and p["scientific_calls_executed"] == 0
    assert "not_executed" in p["status"]
    assert p["maximum_evaluated_calls"] == 66 and p["maximum_warmup_calls"] == 10
    assert p["minimum_cosine_each_image"] == .999
    assert p["failure_action"] == "requires_review_stop_no_retry"
    assert len(p["images"]) == len({r["row_id"] for r in p["images"]}) == 33
    with (ROOT / "results/analysis/kth_preprocessing_forensics_20261115_v1/pixel_preprocessing_pairs.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    expected = {(int(r["identifier"]), r["block"]): r["reference_pixel_sha256"]
                for r in rows if r["kind"] == "frozen_training_image"}
    for sample in p["images"]:
        for block, digest in sample["candidate_input_sha256"].items():
            assert digest == expected[sample["row_id"], block]


def test_proposal_separates_never_fitted_cases_from_25_reusable_results():
    c = load()["continuation_only_if_both_blocks_pass"]
    assert len(c["reusable_completed_conditions"]) == 25
    assert len(c["never_fitted_blocked_conditions"]) == 2
    needed = {r["condition"]["id"]: r["required_corrected_blocks"]
              for r in c["never_fitted_blocked_conditions"]}
    assert needed == {"KTHTIPS2b_svm_s42_f0": ["siglip_base"],
                      "KTHTIPS2b_svm_s42_f2": ["eva02_base"]}
    assert all(not r["fit_or_selection_artifacts_present"] for r in c["never_fitted_blocked_conditions"])
    assert len(c["independent_completed_kth_conditions"]) == 2
    assert all(not r["uses_corrected_components"] for r in c["independent_completed_kth_conditions"])
    assert len(c["accepted_component_costs_to_preserve_exactly"]) == 6
    assert not c["reselect_completed_routes"]


def test_proposal_and_reusable_results_match_recorded_hashes():
    p = load()
    assert (FOLDER / "proposal.sha256").read_text().split()[0] == sha(FOLDER / "proposal.json")
    assert sha(ROOT / p["protocol"]) == p["protocol_sha256"]
    for relative, expected in p["source_sha256"].items():
        assert sha(ROOT / relative) == expected
    for relative, expected in p["existing_status_sha256"].items():
        assert sha(ROOT / relative) == expected
    for record in p["continuation_only_if_both_blocks_pass"]["reusable_completed_conditions"].values():
        for name, expected in record["artifacts_sha256"].items():
            assert sha(ROOT / record["folder"] / name) == expected
