#!/usr/bin/env python3
"""Freeze a proposal for author review; never construct models or execute trials."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = Path("results/analysis/kth_preprocessing_forensics_20261115_v1")
RUN = Path("results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1")
PROTOCOL = Path("docs/fsc_tex/PROTOCOLO_VALIDACION_KTH_CORREGIDA_2026-11-15.md")
REPORT = Path("docs/fsc_tex/REVISION_FIDELIDAD_KTH_2026-11-15.md")
BLOCKS = ("eva02_base", "siglip_base")


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read(relative):
    return json.loads((ROOT / relative).read_text())


def build_proposal():
    audit = read(AUDIT / "provenance.json")
    sources = dict(audit["source_sha256"])
    sources.update({str(AUDIT / name): digest for name, digest in audit["outputs_sha256"].items()})
    for name in [PROTOCOL, REPORT, AUDIT / "provenance.json", RUN / "protocol_frozen.json",
                 Path(__file__).relative_to(ROOT), Path("tests/test_kth_preprocessing_forensics.py")]:
        sources[str(name)] = sha(ROOT / name)
    for name, expected in sources.items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"source changed: {name}")
    for name, expected in audit["environment_source_sha256"].items():
        if sha(name) != expected:
            raise ValueError(f"installed library source changed: {name}")

    first = read(Path("results/analysis/kth_top4_component_profile_20261115_v2/protocol_frozen.json"))
    config = read(AUDIT / "pipeline_configuration.json")
    with (ROOT / AUDIT / "pixel_preprocessing_pairs.csv").open(newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["kind"] == "frozen_training_image"]
    samples = []
    for idx in first["indices"]:
        matching = {r["block"]: r for r in rows if int(r["identifier"]) == idx}
        if set(matching) != set(BLOCKS):
            raise ValueError(f"missing frozen input tensor: {idx}")
        samples.append({"row_id": idx, "candidate_input_sha256": {
            block: matching[block]["reference_pixel_sha256"] for block in BLOCKS}})
    if len(samples) != 33 or len({s["row_id"] for s in samples}) != 33:
        raise ValueError("proposal must preserve the same 33 images")

    status = read(RUN / "status.json")
    conditions = read(RUN / "protocol_frozen.json")["conditions"]
    completed = [key for key, value in status["states"].items() if value == "complete"]
    blocked = [key for key, value in status["states"].items() if value == "requires_review"]
    expected_blocked = {"KTHTIPS2b_svm_s42_f0", "KTHTIPS2b_svm_s42_f2"}
    if len(completed) != 25 or set(blocked) != expected_blocked:
        raise ValueError("unexpected E1 coverage; review instead of preparing another run")
    reusable = {}
    for key in completed:
        folder = RUN / "conditions" / key
        record = read(folder / "status.json")
        sources[str(folder / "status.json")] = sha(ROOT / folder / "status.json")
        for name, expected in record["sha256"].items():
            path = folder / name
            if sha(ROOT / path) != expected:
                raise ValueError(f"completed E1 artifact changed: {path}")
        reusable[key] = {"folder": str(folder), "artifacts_sha256": record["sha256"]}

    blocked_conditions = []
    independent = []
    for condition in conditions:
        key = condition["id"]
        needed = set(condition["cheap_candidates"] + condition["top4_blocks"])
        if key in blocked:
            folder = ROOT / RUN / "conditions" / key
            failure = read(RUN / "conditions" / key / "status.json")
            if "unavailable faithful KTH costs:" not in failure.get("error", ""):
                raise ValueError("blocked E1 case has a different failure")
            if any((folder / name).exists() for name in ["selection_pretest.json", "models.joblib", "result.json"]):
                raise ValueError("blocked E1 case has fit/selection artifacts; do not repeat it")
            source = RUN / "conditions" / key / "status.json"
            sources[str(source)] = sha(ROOT / source)
            blocked_conditions.append({"condition": condition, "old_status_sha256": sources[str(source)],
                                       "required_corrected_blocks": sorted(needed & set(BLOCKS)),
                                       "fit_or_selection_artifacts_present": False})
        elif key in completed and condition["dataset"] == "KTHTIPS2b":
            if needed & set(BLOCKS):
                raise ValueError("completed KTH case depends on a changed component")
            independent.append({"id": key, "all_candidate_and_top4_blocks": sorted(needed),
                                "uses_corrected_components": False})

    accepted = {}
    for source in [Path("results/analysis/kth_top4_component_profile_20261115_v2/status.json"),
                   Path("results/analysis/kth_top4_remaining_components_20261115_v1/status.json")]:
        for block, row in read(source)["blocks"].items():
            if row["min_reference_cosine"] >= .999:
                accepted[block] = {"mean_ms": row["mean_ms"], "source": str(source),
                                   "source_sha256": sources[str(source)],
                                   "min_reference_cosine": row["min_reference_cosine"]}
    if len(accepted) != 6 or set(accepted) & set(BLOCKS):
        raise ValueError("unexpected accepted component profile")
    for block in config["cached_weight_and_config_checks"].values():
        for name, record in block["checks"].items():
            if sha(name) != record["expected_sha256"]:
                raise ValueError(f"local weight/config changed: {name}")

    return {
        "status": "proposal_frozen_author_decision_pending_not_executed",
        "execution_authorized": False, "scientific_calls_executed": 0,
        "protocol": str(PROTOCOL), "protocol_sha256": sources[str(PROTOCOL)],
        "blocks_in_fixed_order": list(BLOCKS), "images": samples,
        "seed": 42, "batch_size": 1, "cpu_threads": 2,
        "warmup_calls_per_block": 5, "evaluated_calls_per_block": 33,
        "maximum_evaluated_calls": 66, "maximum_warmup_calls": 10,
        "minimum_cosine_each_image": .999, "failure_action": "requires_review_stop_no_retry",
        "global_lock": "results/analysis/gpu.lock", "one_resident_model": True,
        "concurrent_fits_or_extractions_allowed": False, "download_weights": False,
        "weights_and_configs": config["cached_weight_and_config_checks"],
        "versions_observed_during_cpu_audit": read(AUDIT / "summary.json")["versions_observed_now"],
        "execution_environment_must_be_frozen_before_first_model_call": True,
        "existing_status_sha256": audit["protected_status_sha256"],
        "source_sha256": sources, "environment_source_sha256": audit["environment_source_sha256"],
        "continuation_only_if_both_blocks_pass": {
            "requires_author_decision": True, "reusable_completed_conditions": reusable,
            "never_fitted_blocked_conditions": blocked_conditions,
            "independent_completed_kth_conditions": independent,
            "accepted_component_costs_to_preserve_exactly": accepted,
            "new_output_directory_required": True, "reselect_completed_routes": False,
            "complete_dataset_mean_requires_all_four_kth_conditions": True,
            "scope_of_costs": "projected acquisition across explicitly distinct timing sessions; not online policy latency"
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    proposal = build_proposal()
    args.output.mkdir(parents=True, exist_ok=False)
    target = args.output / "proposal.json"
    target.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n")
    (args.output / "proposal.sha256").write_text(sha(target) + "  proposal.json\n")
    print(f"Prepared proposal only: {target}")


if __name__ == "__main__":
    main()
