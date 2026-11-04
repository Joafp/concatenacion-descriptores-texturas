"""Reaggregate one COMPLETE non-FMD DeepLumina ADAPTATION dataset; no models/fits."""
import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from consolidate_overnight_online_panel import digest, macro_f1, read
from consolidate_deeplumina_fmd_external import LOCAL_SHA, METHOD, write_csv
from run_authorized_remediation_queue import verify_sources

EXPECTED = {
    "CUReT": (2, 5612),
    "DTD": (10, 18800),
    "Outex13Official1360": (1, 680),
    "SoilOriginal": (15, 3420),
    "KTHTIPS2b": (4, 4752),
}


def call_metrics(calls, partition, rows):
    import numpy as np

    expected = partition["external_indices"]
    if not calls or [c["row_index"] for c in calls] != expected or len(expected) != len(set(expected)):
        raise ValueError("full unique ordered call coverage required")
    labels = partition["labels"]
    for c in calls:
        if (
            c["truth"] != int(rows[c["row_index"]]["label"])
            or c["repeat"] != 0
            or c["prediction"] not in labels
            or len(c["logits"]) != len(labels)
            or len(c["ecoc_losses"]) != len(labels)
            or not all(math.isfinite(v) for v in c["logits"])
            or not all(math.isfinite(v) for v in c["ecoc_losses"])
            or not all(math.isfinite(v) for v in c["binary_margins"])
            or labels[int(np.argmax(c["logits"]))] != c["prediction"]
            or labels[int(np.argmin(c["ecoc_losses"]))] != c["prediction"]
            or not math.isfinite(c["elapsed_ms"])
            or c["elapsed_ns"] <= 0
            or c["elapsed_ms"] != c["elapsed_ns"] / 1e6
        ):
            raise ValueError("same-call truth/logits/ecoc_losses/timing integrity failure")
    times = [c["elapsed_ms"] for c in calls]
    return {
        "calls": len(calls),
        "macro_f1_online": macro_f1([c["truth"] for c in calls], [c["prediction"] for c in calls]),
        "accuracy_online": statistics.mean(c["truth"] == c["prediction"] for c in calls),
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "p95_ms": float(np.percentile(times, 95)),
    }


def validate_coverage(dataset, partitions, calls_count):
    n, expected_calls = EXPECTED[dataset]
    ids = [(p["seed"], p["outer_fold"]) for p in partitions]
    if (
        len(ids) != n
        or len(set(ids)) != n
        or any(p["dataset"] != dataset for p in partitions)
        or calls_count != expected_calls
    ):
        raise ValueError("complete dataset condition/call coverage required")


def consolidate(queue, output, dataset):
    queue, output = Path(queue).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest, worker, frozen = [
        read(queue / f) for f in ("manifest.json", "gpu.json", "preflight.json")
    ]
    if (
        worker["status"] != "all_tasks_terminal"
        or worker["current_task"] is not None
        or worker["manifest_sha256"] != digest(queue / "manifest.json")
    ):
        raise ValueError("terminal queue required; do not audit during benchmarks")
    verify_sources(manifest)
    partitions = frozen["conditions"]
    validate_coverage(dataset, partitions, sum(len(p["external_indices"]) for p in partitions))
    if len(manifest["tasks"]) != len(partitions):
        raise ValueError("task/partition count mismatch")
    sources = {str(queue / f): digest(queue / f) for f in ("manifest.json", "preflight.json", "gpu.json")}
    sources.update(manifest["source_sha256"])
    records, calls_by_identity = [], {}
    for task, p in zip(manifest["tasks"], partitions):
        name = f'DeepLumina_{dataset}_s{p["seed"]}_f{p["outer_fold"]}'
        state_path = queue / "tasks" / name / "state.json"
        state = read(state_path)
        if (
            task["id"] != name
            or worker["outcomes"].get(name) != "complete"
            or state["status"] != "complete"
            or state["manifest_sha256"] != digest(queue / "manifest.json")
        ):
            raise ValueError("task identity/incomplete receipt")
        receipts = state["success_artifacts"]
        if len(receipts) != 4 or [a["condition"] for a in receipts] != [
            c["success"] for c in task["commands"]
        ]:
            raise ValueError("stage receipt coverage mismatch")
        job, stages = queue / "jobs" / name, {}
        for stage, receipt in zip(("extract", "train", "online", "audit"), receipts):
            path = job / stage / "status.json"
            if str(path) != receipt["path"] or digest(path) != receipt["sha256"]:
                raise ValueError("stage receipt/status hash mismatch")
            status = read(path)
            if (
                status["status"] != stage + "_complete"
                or status["partition"] != p
                or status["manifest_sha256"] != digest(queue / "preflight.json")
                or status["method"] != METHOD
            ):
                raise ValueError("stage identity/recipe drift")
            for filename, sha in status["output_sha256"].items():
                artifact = job / stage / filename
                if digest(artifact) != sha:
                    raise ValueError("stage output drift")
                sources[str(artifact)] = sha
            sources[str(path)] = digest(path)
            stages[stage] = status
        for downstream, key, upstream in (
            ("train", "extraction_status_sha256", "extract"),
            ("online", "head_status_sha256", "train"),
            ("audit", "online_status_sha256", "online"),
        ):
            if stages[downstream][key] != digest(job / upstream / "status.json"):
                raise ValueError("cross-stage lineage drift")
        with Path(p["manifest"]).open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        calls = [json.loads(line) for line in (job / "online/calls.jsonl").read_text().splitlines()]
        actual, summary = call_metrics(calls, p, rows), read(job / "audit/summary.json")
        if summary["method"] != METHOD or not summary["same_call_quality_and_timing"]:
            raise ValueError("same-call/method identity missing")
        for key, value in actual.items():
            if abs(summary[key] - value) > 1e-12:
                raise ValueError("raw call reaggregation mismatch")
        records.append(
            {
                "dataset": dataset,
                "seed": p["seed"],
                "outer_fold": p["outer_fold"],
                "method": METHOD,
                **actual,
            }
        )
        calls_by_identity[p["seed"], p["outer_fold"]] = len(calls)
        sources[str(state_path)] = digest(state_path)
    validate_coverage(dataset, partitions, sum(calls_by_identity.values()))
    local_path = (
        ROOT / "results/analysis/blocker_resolution_20261101/full_panel_online_v1/condition_summary.csv"
    )
    if digest(local_path) != LOCAL_SHA:
        raise ValueError("frozen local table drift")
    with local_path.open(newline="") as stream:
        local = [r for r in csv.DictReader(stream) if r["dataset"] == dataset]
    lookup = {(r["seed"], r["outer_fold"]): r for r in records}
    comparisons = []
    for r in local:
        reference = lookup[int(r["seed"]), int(r["outer_fold"])]
        if int(r["calls"]) != reference["calls"]:
            raise ValueError("reference/local image count mismatch")
        comparisons.append(
            {
                "dataset": dataset,
                "seed": r["seed"],
                "outer_fold": r["outer_fold"],
                "local_classifier": r["classifier"],
                "local_method": r["method"],
                "reference_method": METHOD,
                "local_f1": float(r["macro_f1_online"]),
                "reference_f1": reference["macro_f1_online"],
                "reference_accuracy": reference["accuracy_online"],
                "delta_f1_local_minus_reference": float(r["macro_f1_online"])
                - reference["macro_f1_online"],
                "local_mean_ms": float(r["mean_ms"]),
                "reference_mean_ms": reference["mean_ms"],
                "local_calls": int(r["calls"]),
                "reference_calls": reference["calls"],
                "latency_ratio_reference_over_local": reference["mean_ms"] / float(r["mean_ms"]),
                "physical_timing_reserve_local": r["physical_timing_reserve"],
            }
        )
    keys = {(r["seed"], r["outer_fold"], r["local_classifier"], r["local_method"]) for r in comparisons}
    if len(comparisons) != len(records) * 10 or len(keys) != len(comparisons):
        raise ValueError("all local comparison pairs required")
    groups = defaultdict(list)
    for r in comparisons:
        groups[r["local_classifier"], r["local_method"]].append(r)
    dataset_rows = []
    for (classifier, method), group in sorted(groups.items()):
        local_ms = sum(r["local_mean_ms"] * r["local_calls"] for r in group) / sum(
            r["local_calls"] for r in group
        )
        ref_ms = sum(r["reference_mean_ms"] * r["reference_calls"] for r in group) / sum(
            r["reference_calls"] for r in group
        )
        dataset_rows.append(
            {
                "dataset": dataset,
                "local_classifier": classifier,
                "local_method": method,
                "reference_method": METHOD,
                "conditions": len(group),
                "local_mean_split_f1": statistics.mean(r["local_f1"] for r in group),
                "reference_mean_split_f1": statistics.mean(r["reference_f1"] for r in group),
                "reference_mean_split_accuracy": statistics.mean(
                    r["reference_accuracy"] for r in group
                ),
                "mean_delta_f1_local_minus_reference": statistics.mean(
                    r["delta_f1_local_minus_reference"] for r in group
                ),
                "local_mean_ms_all_calls": local_ms,
                "reference_mean_ms_all_calls": ref_ms,
                "latency_ratio_reference_over_local": ref_ms / local_ms,
                "physical_timing_reserve_local": any(
                    r["physical_timing_reserve_local"].lower() == "true" for r in group
                ),
            }
        )
    sources[str(local_path)] = LOCAL_SHA
    sources[str(Path(__file__).resolve())] = digest(Path(__file__))
    summary = {
        "status": "COMPLETE_DATASET_ADAPTATION_REAGGREGATED",
        "dataset": dataset,
        "method": METHOD,
        "datasets": 1,
        "unique_conditions": len(records),
        "calls": sum(r["calls"] for r in records),
        "mean_split_macro_f1": statistics.mean(r["macro_f1_online"] for r in records),
        "mean_split_accuracy": statistics.mean(r["accuracy_online"] for r in records),
        "mean_ms_all_calls": sum(r["mean_ms"] * r["calls"] for r in records)
        / sum(r["calls"] for r in records),
        "same_call_quality_and_timing": True,
        "paper_scores_reproduced": False,
        "global_inference_performed": False,
        "reservations": [
            "local fixed adaptation, not source scores or MATLAB author implementation",
            "shared hardware/separate measurement dates; no isolated contemporaneous comparison",
            "conditions/seeds are not independent datasets; previously observed benchmark",
            "retain DTD physical reserve and KTH historical protocol reserve where applicable",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "condition_metrics.csv", records)
    write_csv(output / "comparison_by_condition.csv", comparisons)
    write_csv(output / "comparison_dataset.csv", dataset_rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "provenance.json").write_text(json.dumps(sources, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset", choices=sorted(EXPECTED), required=True)
    args = parser.parse_args()
    consolidate(args.queue, args.output, args.dataset)
