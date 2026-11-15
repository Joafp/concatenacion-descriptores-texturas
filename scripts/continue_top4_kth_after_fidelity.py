#!/usr/bin/env python3
"""Complete only the two never-fitted KTH E1 cases after authorized fidelity passes."""
from __future__ import annotations
import argparse
import copy
import fcntl
import importlib.metadata
import json
from pathlib import Path
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from run_top4_fixed_e1_e2 import run_condition, dump
from validate_kth_reference_recipe import sha, verify_authorization, verify_inputs, PROPOSAL

PARENT = Path("results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1")
ALLOWED = {"KTHTIPS2b_svm_s42_f0", "KTHTIPS2b_svm_s42_f2"}
CODE_DEPENDENCIES = [ROOT / "scripts/run_cheap_stage_selected_cascade.py", ROOT / "src/run_confirmatory_nested.py"]


def accepted_costs(profile):
    if profile["status"] != "complete" or set(profile["blocks"]) != {"eva02_base", "siglip_base"}:
        raise ValueError("both corrected blocks must be completely validated")
    if profile["evaluated_calls"] != 66 or profile["warmup_calls"] != 10:
        raise ValueError("corrected validation has incomplete or unexpected call coverage")
    for row in profile["blocks"].values():
        if row["n_timed_images"] != 33 or row["min_reference_cosine"] < .999:
            raise ValueError("a corrected block failed the frozen fidelity criterion")
    return {block: row["mean_ms"] for block, row in profile["blocks"].items()}


def prepare_conditions(parent, proposal, new_costs):
    conditions = copy.deepcopy(parent["conditions"])
    constants = proposal["continuation_only_if_both_blocks_pass"]["accepted_component_costs_to_preserve_exactly"]
    costs = {block: row["mean_ms"] for block, row in constants.items()}
    costs.update(new_costs)
    for condition in conditions:
        key = condition["id"]
        if key in ALLOWED:
            needed = sorted(set(condition["cheap_candidates"] + condition["top4_blocks"]))
            condition["component_costs_ms"] = {block: costs[block] for block in needed}
            condition["missing_component_costs"] = []
        elif condition != next(c for c in parent["conditions"] if c["id"] == key):
            raise ValueError("completed condition was modified")
    if {c["id"] for c in conditions if c["id"] in ALLOWED} != ALLOWED:
        raise ValueError("missing authorized KTH conditions")
    return conditions


def representation_sources(parent, conditions):
    bound = {}
    for c in conditions:
        if c["id"] not in ALLOWED:
            continue
        for block in sorted(set(c["cheap_candidates"] + c["top4_blocks"])):
            # These are exactly the arrays read by the unchanged E1 runner.
            for suffix in [".npy", "_labels.npy"]:
                name = str(Path(c["embedding_directory"]) / (block + suffix))
                bound[name] = parent["original_preparation"]["sources"][name]["sha256"]
    return bound


def run(output, profile_folder, decision):
    if output.exists():
        raise FileExistsError("Use a new continuation folder; no completed or failed cases may be resumed")
    p = verify_authorization(PROPOSAL, decision)
    verify_inputs(p)
    profile = json.loads((profile_folder / "status.json").read_text())
    new_costs = accepted_costs(profile)
    for name, expected in profile["outputs_sha256"].items():
        if sha(profile_folder / name) != expected:
            raise ValueError(f"corrected profile output changed: {name}")
    parent = json.loads((ROOT / PARENT / "protocol_frozen.json").read_text())
    for name, expected in parent["sources"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"parent E1 source changed: {name}")
    versions = {name: importlib.metadata.version(name) for name in parent["recipe"]["versions"]}
    if versions != parent["recipe"]["versions"]:
        raise ValueError("classifier library versions differ from original E1")
    conditions = prepare_conditions(parent, p, new_costs)
    source_hashes = dict(parent["sources"])
    source_hashes.update({str(path.relative_to(ROOT)): sha(path) for path in
                         [Path(__file__), ROOT / "tests/test_continue_top4_kth_after_fidelity.py",
                          ROOT / PARENT / "protocol_frozen.json", ROOT / PARENT / "status.json",
                          PROPOSAL, decision, profile_folder / "status.json",
                          profile_folder / "protocol_frozen.json", *CODE_DEPENDENCIES]})
    # Bind the unchanged representation and labels read by the two new fits.
    for c in conditions:
        if c["id"] not in ALLOWED:
            continue
        original_folder = ROOT / PARENT / "conditions" / c["id"]
        original = json.loads((original_folder / "status.json").read_text())
        if "unavailable faithful KTH costs:" not in original.get("error", ""):
            raise ValueError("original case no longer matches a pre-fit cost failure")
        if any((original_folder / name).exists() for name in ["selection_pretest.json", "models.joblib", "result.json"]):
            raise ValueError("the original case has fit artifacts; do not repeat it")
    for name, expected in representation_sources(parent, conditions).items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"frozen E1 representation changed: {name}")
        source_hashes[name] = expected

    sources = {c["id"]: str((output / "conditions" / c["id"]).relative_to(ROOT)) if c["id"] in ALLOWED
               else str(PARENT / "conditions" / c["id"]) for c in conditions}
    output.mkdir(parents=True, exist_ok=False)
    frozen = {"recipe": parent["recipe"], "conditions": conditions, "sources": source_hashes,
              "condition_sources": sources, "original_parent": str(PARENT),
              "authorized_new_condition_ids": sorted(ALLOWED),
              "maximum_classifier_fits": sum((len(c["inner_folds"]) + 1) * (len(c["cheap_candidates"]) + 1)
                                             for c in conditions if c["id"] in ALLOWED),
              "cost_scope": "projected acquisition; six unchanged accepted constants and two corrected-session constants; not online policy latency",
              "accepted_profile_constants": p["continuation_only_if_both_blocks_pass"]["accepted_component_costs_to_preserve_exactly"],
              "new_profile_constants": new_costs, "author_decision": json.loads(decision.read_text())}
    dump(output / "protocol_frozen.json", frozen)
    state = {"status": "prepared", "expected": 27, "primary_metric": "accuracy",
             "protocol_sha256": sha(output / "protocol_frozen.json"), "states": {
                 key: "not_executed" if key in ALLOWED else "complete" for key in sources},
             "new_conditions": sorted(ALLOWED), "completed_parent_conditions_repeated": 0}
    dump(output / "status.json", state)
    with (ROOT / p["global_lock"]).open("a") as lock, threadpool_limits(limits=2):
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            state["status"] = "running"
            for c in conditions:
                if c["id"] not in ALLOWED:
                    continue
                state["states"][c["id"]] = "running"
                dump(output / "status.json", state)
                state["states"][c["id"]] = run_condition(c, output / "conditions" / c["id"])
                dump(output / "status.json", state)
                if state["states"][c["id"]] != "complete":
                    break
    state["status"] = "complete" if all(v == "complete" for v in state["states"].values()) else "requires_review"
    state["original_statuses_unchanged"] = {name: sha(ROOT / name) == expected
                                           for name, expected in p["existing_status_sha256"].items()}
    if not all(state["original_statuses_unchanged"].values()):
        state["status"] = "requires_review"
        state["error"] = "an original status changed during continuation"
    dump(output / "status.json", state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--author-decision", type=Path, required=True)
    args = parser.parse_args()
    run(args.output.resolve(), args.profile.resolve(), args.author_decision.resolve())
