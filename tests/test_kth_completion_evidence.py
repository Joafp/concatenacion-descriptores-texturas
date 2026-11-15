"""Audit the completed six-dataset evidence without fitting or neural extraction."""
from pathlib import Path
import csv
import hashlib
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results/analysis/top4_fixed_kth_completion_audit_20261115_v1"
RUN = ROOT / "results/exploratory/topk_cascade/top4_fixed_kth_completion_20261115_v1"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_closed_coverage_reuses_25_and_preserves_original_failure_records():
    s = json.loads((AUDIT / "summary.json").read_text())
    state = json.loads((RUN / "status.json").read_text())
    assert s["completed_conditions"] == 27 and s["new_conditions"] == 2 and s["reused_conditions"] == 25
    assert s["e2_rows"] == 486 and len(s["complete_datasets"]) == 6
    assert state["status"] == "complete" and set(state["states"].values()) == {"complete"}
    p = json.loads((ROOT / "results/analysis/kth_reference_validation_proposal_20261115_v1/proposal.json").read_text())
    assert all(sha(ROOT / path) == digest for path, digest in p["existing_status_sha256"].items())
    old = json.loads((ROOT / "results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1/status.json").read_text())
    assert old["status"] == "requires_review"


def test_accepted_profile_has_exactly_66_evaluated_calls_without_repeated_eva():
    first = json.loads((ROOT / "results/analysis/kth_reference_validation_20261115_v1/status.json").read_text())
    second = json.loads((ROOT / "results/analysis/kth_reference_siglip_unexecuted_20261115_v1/status.json").read_text())
    assert first["evaluated_calls"] == second["evaluated_calls"] == 33
    assert first["warmup_calls"] == second["warmup_calls"] == 5
    assert first["neural_forward_calls_invoked"] + second["neural_forward_calls_invoked"] == 76
    assert set(first["blocks"]) == {"eva02_base"} and set(second["blocks"]) == {"siglip_base"}
    profile = json.loads((ROOT / "results/analysis/kth_reference_validated_profile_20261115_v1/status.json").read_text())
    assert profile["status"] == "complete" and profile["evaluated_calls"] == 66
    assert all(r["n_timed_images"] == 33 and r["min_reference_cosine"] >= .999 for r in profile["blocks"].values())


def test_all_27_direct_results_exactly_reproduce_saved_top4_accuracy_and_f1():
    with (AUDIT / "direct_reference_comparison.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 27
    assert all(float(r["accuracy_delta"]) == 0 and float(r["macro_f1_delta"]) == 0 for r in rows)


def test_dataset_balanced_means_include_all_four_kth_and_keep_projected_scope():
    with (AUDIT / "e1_conditions.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    kth = [r for r in rows if r["dataset"] == "KTHTIPS2b"]
    assert len(kth) == 4 and {int(r["outer_fold"]) for r in kth} == {0, 1, 2, 3}
    with (AUDIT / "e1_complete_dataset_means.csv").open() as handle:
        means = list(csv.DictReader(handle))
    s = json.loads((AUDIT / "summary.json").read_text())
    assert len(means) == 6 and s["costs_are_projections_not_online_policy_latency"]
    for route in ["direct", "cascade"]:
        assert np.isclose(np.mean([float(r[f"{route}_accuracy"]) for r in means]), s[f"mean_accuracy_{route}"], rtol=0, atol=1e-12)
    assert not s["incomplete_dataset_averages_reported"]


def test_audit_outputs_and_sources_still_match_their_hashes():
    p = json.loads((AUDIT / "provenance.json").read_text())
    for name, expected in p["outputs"].items():
        assert sha(AUDIT / name) == expected
    for name, expected in p["sources"].items():
        assert sha(ROOT / name) == expected
