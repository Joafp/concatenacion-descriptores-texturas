#!/usr/bin/env python3
"""Build the canonical 27-condition registry and link available baseline rows.

This is an accounting step: it loads cached embeddings/manifests to reconstruct
the declared outer partitions, but it does not fit classifiers or recompute
predictive metrics. Historical launch logs are retained as provenance and the
registry explicitly marks that historical row-level split indices were not
persisted by those runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from run_confirmatory_nested import load_dataset, load_manifest  # noqa: E402
from run_topk_individual_control import outer_indices  # noqa: E402

REPO = SRC.parent
PRIMARY_CSV = REPO / "results/confirmatory/ngram22_beitv2/nested_fold_results.csv"
DATASETS = {
    "DTD": ("DTD", "results/confirmatory", None, "official10"),
    "FMD": ("FMD", "results/confirmatory", None, "sgkf_seed42"),
    "CUReT": ("CUReT", "results/confirmatory", None, "two_directions"),
    "Outex13Official1360": (
        "Outex13Official1360", "results/extensions/outex13_official1360",
        "embeddings_extensions", "official1"),
    "SoilOriginal": (
        "SoilOriginal", "results/extensions/soil_original",
        "embeddings_extensions", "sgkf_seed42"),
    "KTHTIPS2b": (
        "KTHTIPS2b", "results/extensions/kth_tips2b",
        "embeddings_extensions", "official4_inverted"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_indices(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values, dtype="<i8").tobytes()).hexdigest()


def counts(values: np.ndarray) -> dict[str, int]:
    labels, frequencies = np.unique(values, return_counts=True)
    return {str(label): int(n) for label, n in zip(labels, frequencies)}


def canonical_specs() -> list[dict]:
    specs = []
    for split in range(1, 11):
        specs.append({"dataset": "DTD", "condition_id": f"DTD_official{split:02d}",
                      "seed": 42, "outer_fold": split - 1, "official_split": split,
                      "curet_direction": None, "invert_official_split": False})
    for fold in range(5):
        specs.append({"dataset": "FMD", "condition_id": f"FMD_s42_f{fold}",
                      "seed": 42, "outer_fold": fold, "official_split": None,
                      "curet_direction": None, "invert_official_split": False})
    for direction, fold in (("a_to_b", 0), ("b_to_a", 1)):
        specs.append({"dataset": "CUReT", "condition_id": f"CUReT_{direction}",
                      "seed": 42, "outer_fold": fold, "official_split": None,
                      "curet_direction": direction, "invert_official_split": False})
    specs.append({"dataset": "Outex13Official1360", "condition_id": "Outex_official01",
                  "seed": 42, "outer_fold": 0, "official_split": 1,
                  "curet_direction": None, "invert_official_split": False})
    for fold in range(5):
        specs.append({"dataset": "SoilOriginal", "condition_id": f"Soil_s42_f{fold}",
                      "seed": 42, "outer_fold": fold, "official_split": None,
                      "curet_direction": None, "invert_official_split": False})
    for split in range(1, 5):
        specs.append({"dataset": "KTHTIPS2b", "condition_id": f"KTH_official{split:02d}_inverted",
                      "seed": 42, "outer_fold": split - 1, "official_split": split,
                      "curet_direction": None, "invert_official_split": True})
    if len(specs) != 27 or len({row["condition_id"] for row in specs}) != 27:
        raise AssertionError("canonical condition definition must have 27 unique rows")
    return specs


def source_row(dataset: str, fold: int, seed: int) -> pd.DataFrame:
    paths = {
        "DTD": PRIMARY_CSV,
        "FMD": PRIMARY_CSV,
        "CUReT": PRIMARY_CSV,
        "Outex13Official1360": REPO / "results/extensions/outex13_official1360/ngram22_beitv2/nested_fold_results.csv",
        "SoilOriginal": REPO / "results/extensions/soil_original/ngram22_beitv2/nested_fold_results.csv",
        "KTHTIPS2b": REPO / "results/extensions/kth_tips2b/ngram22_beitv2/nested_fold_results.csv",
    }
    path = paths[dataset]
    frame = pd.read_csv(path)
    return frame[(frame["dataset"] == dataset)
                 & (frame["seed"] == seed)
                 & (frame["outer_fold"] == fold)].copy()


def run_log_path(dataset: str, classifier: str, seed: int, fold: int,
                 official_split: int | None, direction: str | None) -> Path:
    tag = (f"official{official_split}" if official_split is not None else
           direction if direction is not None else str(fold))
    root = (REPO / "results/confirmatory/ngram22_beitv2/logs"
            if dataset in {"DTD", "FMD", "CUReT"} else
            REPO / "results/extensions" / {
                "Outex13Official1360": "outex13_official1360",
                "SoilOriginal": "soil_original", "KTHTIPS2b": "kth_tips2b",
            }[dataset] / "ngram22_beitv2/logs")
    log_dataset = dataset
    if dataset == "KTHTIPS2b":
        log_dataset = "KTHTIPS2b"
    return root / f"{log_dataset}__{classifier}__{seed}__{tag}__full.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/analysis/integration_v3/canonical_registry_20261021"))
    args = parser.parse_args()
    output = (REPO / args.output).resolve() if not args.output.is_absolute() else args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error(f"output directory is not empty; choose a new --output: {output}")

    primary = pd.read_csv(PRIMARY_CSV)
    dataset_state = {}
    for dataset, (loader_name, manifest_rel, embedding_rel, _) in DATASETS.items():
        embedding_root = REPO / embedding_rel if embedding_rel else None
        cache, y = load_dataset(REPO, loader_name, embedding_root)
        manifest_root = REPO / manifest_rel
        groups, rows = load_manifest(manifest_root, loader_name, y)
        manifest_path = manifest_root / "sample_manifests" / f"{loader_name}.csv"
        dataset_state[dataset] = {
            "y": y, "groups": groups, "rows": rows,
            "manifest_path": manifest_path,
            "manifest_sha256": sha256_file(manifest_path),
            "n_images": int(len(y)), "class_count": int(len(np.unique(y))),
            "block_names": sorted(cache),
            "embedding_root": str((embedding_root or REPO / "embeddings_confirmatory" / loader_name).relative_to(REPO)),
        }

    records = []
    reference_rows = []
    for spec in canonical_specs():
        dataset = spec["dataset"]
        loader_name, manifest_rel, embedding_rel, outer_protocol = DATASETS[dataset]
        state = dataset_state[dataset]
        y, groups, rows = state["y"], state["groups"], state["rows"]
        train, test = outer_indices(
            loader_name, spec["seed"], spec["outer_fold"], y, groups, rows,
            spec["official_split"], spec["curet_direction"], spec["invert_official_split"])
        if set(groups[train]).intersection(groups[test]):
            raise ValueError(f"source groups overlap for {spec['condition_id']}")
        baseline = source_row(loader_name, spec["outer_fold"], spec["seed"])
        expected_classifiers = {"svm", "resmlp"}
        if set(baseline["classifier"]) != expected_classifiers:
            raise ValueError(f"baseline classifier coverage is incomplete: {spec['condition_id']}")
        if not baseline["run_mode"].eq("full").all():
            raise ValueError(f"non-full run found in primary reference: {spec['condition_id']}")
        if baseline.duplicated(["dataset", "classifier", "seed", "outer_fold", "method"]).any():
            raise ValueError(f"duplicate primary result row: {spec['condition_id']}")
        full = baseline[baseline["method"] == "full_concat"]
        if len(full) != 2 or not full["dimensions"].eq(20652).all():
            raise ValueError(f"Complete-22 dimensionality mismatch: {spec['condition_id']}")
        required_methods = {"best_individual", "full_concat", "gfs"}
        missing_methods = required_methods.difference(set(baseline["method"]))
        if missing_methods:
            raise ValueError(f"missing primary22 methods at {spec['condition_id']}: {sorted(missing_methods)}")
        homogeneous = baseline[baseline["method"].astype(str).str.startswith("best_homogeneous_")]
        if set(homogeneous["classifier"]) != expected_classifiers or len(homogeneous) != 2:
            raise ValueError(f"expected one selected homogeneous control per classifier: {spec['condition_id']}")
        baseline_csv = (PRIMARY_CSV if loader_name in {"DTD", "FMD", "CUReT"}
                        else REPO / manifest_rel / "ngram22_beitv2" / "nested_fold_results.csv")
        logs = {}
        for classifier in sorted(expected_classifiers):
            log = run_log_path(loader_name, classifier, spec["seed"], spec["outer_fold"],
                               spec["official_split"], spec["curet_direction"])
            if not log.exists():
                raise FileNotFoundError(f"expected historical run log absent: {log}")
            log_data = json.loads(log.read_text(encoding="utf-8"))
            if log_data.get("status") != "complete":
                raise ValueError(f"historical run not complete: {log}")
            if log_data.get("include_rgb_ngram") is not True:
                raise ValueError(f"primary reference did not use the 22-block library: {log}")
            if (log_data.get("dataset") != loader_name
                    or log_data.get("classifier") != classifier
                    or int(log_data.get("seed", -1)) != spec["seed"]):
                raise ValueError(f"run identity mismatch in historical log: {log}")
            if spec["curet_direction"] is not None:
                if log_data.get("curet_direction") != spec["curet_direction"]:
                    raise ValueError(f"CUReT direction mismatch in historical log: {log}")
            elif spec["official_split"] is None:
                if int(log_data.get("fold", -1)) != spec["outer_fold"]:
                    raise ValueError(f"fold mismatch in historical log: {log}")
            if spec["official_split"] is not None:
                if log_data.get("official_split") != spec["official_split"]:
                    raise ValueError(f"official split mismatch in historical run log: {log}")
                if bool(log_data.get("invert_official_split")) != spec["invert_official_split"]:
                    raise ValueError(f"inversion mismatch in historical run log: {log}")
            logs[classifier] = {"path": str(log.relative_to(REPO)), "sha256": sha256_file(log),
                                "command": log_data.get("command"),
                                "script_sha256": log_data.get("script_sha256")}
        for _, row in baseline.iterrows():
            reference_rows.append({"condition_id": spec["condition_id"], **row.to_dict(),
                                   "source_csv": str(baseline_csv.relative_to(REPO)),
                                   "source_csv_sha256": sha256_file(baseline_csv)})
        records.append({
            **spec,
            "canonical_registry_version": "27-condition-v1",
            "outer_protocol": outer_protocol,
            "inner_protocol_status": "historical launch commands recorded; exact historical inner split indices not saved",
            "historical_row_level_partition_saved": False,
            "n_images_total": state["n_images"], "n_classes": state["class_count"],
            "n_train": int(len(train)), "n_test": int(len(test)),
            "train_class_counts": json.dumps(counts(y[train]), sort_keys=True),
            "test_class_counts": json.dumps(counts(y[test]), sort_keys=True),
            "train_groups": int(len(np.unique(groups[train]))),
            "test_groups": int(len(np.unique(groups[test]))),
            "source_group_overlap": 0,
            "train_indices_sha256": sha256_indices(train),
            "test_indices_sha256": sha256_indices(test),
            "manifest_path": str(state["manifest_path"].relative_to(REPO)),
            "manifest_sha256": state["manifest_sha256"],
            "embedding_root": state["embedding_root"],
            "historical_launch_logs": json.dumps(logs, sort_keys=True),
            "source_baseline_csv": str(baseline_csv.relative_to(REPO)),
            "source_baseline_csv_sha256": sha256_file(baseline_csv),
            "baseline_rows": int(len(baseline)),
            "baseline_classifiers": ";".join(sorted(set(baseline["classifier"]))),
        })

    registry = pd.DataFrame(records)
    if len(registry) != 27 or registry["condition_id"].duplicated().any():
        raise AssertionError("registry does not contain 27 unique canonical conditions")
    if registry["baseline_rows"].sum() != 27 * 2 * 4:
        raise AssertionError("expected 216 historical baseline rows across 27 conditions")
    output.mkdir(parents=True, exist_ok=True)
    registry.to_csv(output / "canonical_conditions.csv", index=False)
    pd.DataFrame(reference_rows).to_csv(output / "primary22_reference_rows.csv", index=False)
    manifest = {
        "registry_version": "27-condition-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ANALYZED",
        "condition_count": len(registry),
        "primary22_reference_row_count": len(reference_rows),
        "datasets": {name: int(n) for name, n in registry.groupby("dataset").size().items()},
        "source_hashes": {
            "primary_results_csv": sha256_file(PRIMARY_CSV),
            "builder_source": sha256_file(Path(__file__)),
            "outer_split_source": sha256_file(SRC / "run_topk_individual_control.py"),
            "manifest_sources": {name: dataset_state[name]["manifest_sha256"] for name in DATASETS},
        },
        "scope_note": "Partition hashes are reconstructed from current manifests and split code. Historical logs lack saved row-index arrays, so they establish command/protocol identity but do not independently prove the exact old row membership.",
    }
    (output / "registry_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"registered {len(registry)} canonical conditions and {len(reference_rows)} reference rows")
    print(registry.groupby("dataset").size().to_string())
    print(f"saved: {output}")


if __name__ == "__main__":
    main()
