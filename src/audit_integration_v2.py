#!/usr/bin/env python3
"""Build provenance and error-transition tables for the integration-v1 pilots.

The script audits saved predictions only. It does not fit models or select a
method. Its output deliberately labels the four pilot conditions as
non-comparable when their feature libraries differ.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_confirmatory_nested import load_dataset, load_manifest
from run_topk_individual_control import outer_indices


REPO = Path(__file__).resolve().parents[1]
PILOT_ROOT = REPO / "results/exploratory/integration_v1/cascade_rescue_pilot"
OUT = REPO / "results/analysis/integration_v2"
PILOTS = {
    "FMD": {
        "base": "siglip_base", "manifest": "results/confirmatory",
        "embedding_root": None, "audit": "results/confirmatory",
        "official_split": None, "curet_direction": None, "invert": False,
        "inner_group_column": "group",
    },
    "Outex13Official1360": {
        "base": "beitv2_base_final", "manifest": "results/extensions/outex13_official1360",
        "embedding_root": "embeddings_extensions", "audit": "results/extensions/outex13_official1360",
        "official_split": 1, "curet_direction": None, "invert": False,
        "inner_group_column": "group",
    },
    "SoilOriginal": {
        "base": "siglip_base", "manifest": "results/extensions/soil_original",
        "embedding_root": "embeddings_extensions", "audit": "results/extensions/soil_original",
        "official_split": None, "curet_direction": None, "invert": False,
        "inner_group_column": "group",
    },
    "KTHTIPS2b": {
        "base": "beitv2_base_final", "manifest": "results/extensions/kth_tips2b",
        "embedding_root": "embeddings_extensions", "audit": "results/extensions/kth_tips2b",
        "official_split": 1, "curet_direction": None, "invert": True,
        "inner_group_column": "sample",
    },
}
DATASET_SOURCES = {
    "DTD": {"manifest": "results/confirmatory", "embedding_root": None,
            "official_split": None, "curet_direction": None, "invert": False},
    "FMD": {"manifest": "results/confirmatory", "embedding_root": None,
            "official_split": None, "curet_direction": None, "invert": False},
    "CUReT": {"manifest": "results/confirmatory", "embedding_root": None,
              "official_split": None, "curet_direction": "a_to_b", "invert": False},
    "Outex13Official1360": {"manifest": "results/extensions/outex13_official1360",
                             "embedding_root": "embeddings_extensions", "official_split": 1,
                             "curet_direction": None, "invert": False},
    "SoilOriginal": {"manifest": "results/extensions/soil_original",
                     "embedding_root": "embeddings_extensions", "official_split": None,
                     "curet_direction": None, "invert": False},
    "KTHTIPS2b": {"manifest": "results/extensions/kth_tips2b",
                  "embedding_root": "embeddings_extensions", "official_split": 1,
                  "curet_direction": None, "invert": True},
}
COMMON_21 = {
    "beitv2_base_final", "convnext_v2_t", "deit_s", "densenet121", "dinov2",
    "dinov2_large", "dinov2_small", "drlbp", "efficientnet_b0", "eva02_base",
    "gabor", "glcm", "hog", "lbp", "mae_base", "resnet101", "resnet50",
    "siglip_base", "swin_t", "vgg16", "vit_b16",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_indices(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values, dtype="<i8").tobytes()).hexdigest()


def embedding_dir(dataset: str, explicit: Path | None) -> Path:
    name = {"KTHTIPS2b": "KTH-TIPS2-b"}.get(dataset, dataset)
    if explicit is not None:
        return explicit / name
    candidate = REPO / "embeddings_confirmatory" / name
    if candidate.is_dir():
        return candidate
    candidate = REPO / "embeddings" / name
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError(f"could not locate embeddings for {dataset}")


def prediction_transitions(dataset: str, pred: pd.DataFrame, labels: np.ndarray,
                           manifest_rows: list[dict], image_rows: list[dict],
                           class_rows: list[dict], group_column: str) -> None:
    if not np.array_equal(pred["label"].to_numpy(), labels[pred["row_index"].to_numpy(dtype=int)]):
        raise ValueError(f"test prediction labels do not align with canonical labels: {dataset}")
    groups = np.asarray([r.get(group_column, "") for r in manifest_rows], dtype=object)
    methods = {
        "adaptive_rescue_ensemble": ("cascade_prediction", "rescue_ensemble_prediction"),
        "adaptive_topk_rescue": ("cascade_top_k_rescue_prediction", "top_k_static_prediction"),
    }
    for method, (column, static_column) in methods.items():
        y = pred["label"].to_numpy()
        base = pred["base_prediction"].to_numpy()
        rescue = pred[column].to_numpy()
        base_ok, rescue_ok = base == y, rescue == y
        static_ok = pred[static_column].to_numpy() == y
        missed_correctable = (~base_ok) & static_ok & (pred["escalate"].to_numpy() == 0)
        transition = np.where(base_ok & rescue_ok, "both_correct",
                     np.where(~base_ok & rescue_ok, "error_corrected",
                     np.where(base_ok & ~rescue_ok, "error_introduced", "both_wrong")))
        rows = pred.assign(_class=y, _transition=transition)
        for class_value, part in rows.groupby("_class", sort=True):
            counts = part["_transition"].value_counts()
            class_rows.append({
                "dataset": dataset, "method": method, "class_label": class_value,
                "n_test": len(part), "base_errors": int((~base_ok[rows.index.isin(part.index)]).sum()),
                "error_corrected": int(counts.get("error_corrected", 0)),
                "error_introduced": int(counts.get("error_introduced", 0)),
                "both_wrong": int(counts.get("both_wrong", 0)),
                "both_correct": int(counts.get("both_correct", 0)),
                "gate_missed_correctable": int(missed_correctable[rows.index.isin(part.index)].sum()),
                "net_error_change": int(counts.get("error_corrected", 0) - counts.get("error_introduced", 0)),
            })
        for _, row in pred.iterrows():
            idx = int(row["row_index"])
            image_rows.append({
                "dataset": dataset, "method": method, "class_label": row["label"],
                "n_test": 1, "base_errors": int(row["base_prediction"] != row["label"]),
                "error_corrected": int(row["base_prediction"] != row["label"] and row[column] == row["label"]),
                "error_introduced": int(row["base_prediction"] == row["label"] and row[column] != row["label"]),
                "both_wrong": int(row["base_prediction"] != row["label"] and row[column] != row["label"]),
                "both_correct": int(row["base_prediction"] == row["label"] and row[column] == row["label"]),
                "static_rescue_prediction": row[static_column],
                "static_rescue_correct": int(row[static_column] == row["label"]),
                "gate_missed_correctable": int(row["base_prediction"] != row["label"]
                                                and row[static_column] == row["label"]
                                                and int(row["escalate"]) == 0),
                "net_error_change": int(bool(row["base_prediction"] != row["label"])) - int(bool(row[column] != row["label"])),
                "row_index": idx, "source_group": groups[idx],
                "base_prediction": row["base_prediction"], "rescue_prediction": row[column],
                "transition": transition[pred.index.get_loc(row.name)],
                "escalated": int(row["escalate"]),
            })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    out_dir = args.output.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    registry: list[dict] = []
    inventory: list[dict] = []
    image_transitions: list[dict] = []
    class_transitions: list[dict] = []
    pilot_summaries: list[dict] = []

    for dataset, cfg in PILOTS.items():
        source_dir = PILOT_ROOT / dataset
        json_path = source_dir / f"{dataset}_svm_s42_fold0_cascade_rescue.json"
        pred_path = source_dir / f"{dataset}_svm_s42_fold0_predictions.csv"
        summary = json.loads(json_path.read_text(encoding="utf-8"))
        pred = pd.read_csv(pred_path)
        emb_root = REPO / cfg["embedding_root"] if cfg["embedding_root"] else None
        cache, y = load_dataset(REPO, dataset, embedding_root=emb_root)
        manifest_root = REPO / cfg["manifest"]
        groups, manifest_rows = load_manifest(manifest_root, dataset, y)
        train, test = outer_indices(
            dataset, 42, 0, y, groups, manifest_rows,
            cfg["official_split"], cfg["curet_direction"], cfg["invert"],
        )
        if not np.array_equal(pred["row_index"].to_numpy(dtype=int), test):
            raise ValueError(f"saved prediction order differs from recomputed split: {dataset}")
        if cfg["inner_group_column"] not in manifest_rows[0]:
            raise ValueError(f"inner grouping column missing for {dataset}")
        embed_path = embedding_dir(dataset, emb_root)
        available = sorted(cache)
        common_csv = ",".join(available)
        split_tag = (f"official{cfg['official_split']}" + ("_inverted" if cfg["invert"] else "")
                     if cfg["official_split"] else f"f{0}")
        ranking_name = (f"{dataset}_svm_s42_{split_tag}_"
                        f"inner-{cfg['inner_group_column']}.json")
        ranking_path = REPO / "results/exploratory/integration_v1/ranking_cache" / ranking_name
        if not ranking_path.is_file():
            raise FileNotFoundError(f"ranking cache not found for audited pilot: {ranking_path}")
        ranking_metadata = json.loads(ranking_path.read_text(encoding="utf-8"))
        for block in available:
            x = cache[block]
            file_path = embed_path / f"{block}.npy"
            registry.append({
                "dataset": dataset, "pilot_version": "integration_v1", "split_key": f"seed42_fold0_split{cfg['official_split'] or cfg['curet_direction'] or 'sgkf'}",
                "n_train": len(train), "n_test": len(test), "train_indices_sha256": sha256_indices(train),
                "test_indices_sha256": sha256_indices(test), "manifest_sha256": sha256_file(manifest_root / "sample_manifests" / f"{dataset}.csv"),
                "embedding_block": block, "dimensions": int(x.shape[1]), "embedding_shape": f"{x.shape[0]}x{x.shape[1]}",
                "embedding_file_sha256": sha256_file(file_path),
                "labels_file_sha256": sha256_file(embed_path / f"{block}_labels.npy"),
                "embedding_root": str(embed_path.relative_to(REPO)), "base_block": cfg["base"],
                "inner_group_column": cfg["inner_group_column"],
                "official_split": cfg["official_split"] or "", "official_split_inverted": cfg["invert"],
                "curet_direction": cfg["curet_direction"] or "", "rgb_ngram_svd_included": "rgb_ngram_svd" in cache,
                "available_blocks": len(available), "available_block_names": common_csv,
                "pilot_json_sha256": sha256_file(json_path), "prediction_csv_sha256": sha256_file(pred_path),
                "ranking_cache_sha256": sha256_file(ranking_path),
                "ranking_training_inputs_sha256": ranking_metadata["training_inputs_sha256"],
                "selection_seed": summary["seed"], "classifier": summary["classifier"],
                "k": summary["k"], "members": summary["members"], "beta": summary["beta"],
                "escalation_quantile": summary["escalation_quantile_fixed_on_training"],
                "cascade_source_sha256": sha256_file(Path(__file__)),
                "test_partition_match": True, "labels_row_order_match": True,
                "common_21_library_eligible": COMMON_21.issubset(cache) and "rgb_ngram_svd" not in cache,
                "common_22_library_eligible": len(available) == 22 and "rgb_ngram_svd" in cache,
            })
        prediction_transitions(dataset, pred, y, manifest_rows, image_transitions,
                               class_transitions, cfg["inner_group_column"])
        pilot_summaries.append({
            "dataset": dataset, "available_blocks": len(available), "includes_rgb_ngram_svd": "rgb_ngram_svd" in cache,
            "available_block_names": ",".join(available),
            "block_set_sha256": hashlib.sha256("\n".join(available).encode()).hexdigest(),
            "test_indices_sha256": sha256_indices(test), "test_rows": len(test),
            "cascade_ensemble_f1": summary["macro_f1"]["cascade_with_rescue"],
            "cascade_topk_f1": summary["macro_f1"]["cascade_with_top_k_rescue"],
            "complete_available_f1": summary["macro_f1"]["complete_available_static"],
            "escalation_fraction": summary["escalation_fraction"],
        })

    six_library_sets: dict[str, set[str]] = {}
    six_dimensions: dict[str, dict[str, int]] = {}
    for dataset, cfg in DATASET_SOURCES.items():
        emb_root = REPO / cfg["embedding_root"] if cfg["embedding_root"] else None
        cache, y = load_dataset(REPO, dataset, embedding_root=emb_root)
        manifest_root = REPO / cfg["manifest"]
        groups, manifest_rows = load_manifest(manifest_root, dataset, y)
        train, test = outer_indices(dataset, 42, 0, y, groups, manifest_rows,
                                    cfg["official_split"], cfg["curet_direction"], cfg["invert"])
        name = {"KTHTIPS2b": "KTH-TIPS2-b"}.get(dataset, dataset)
        source = (emb_root / name if emb_root else
                  (REPO / "embeddings_confirmatory" / name
                   if (REPO / "embeddings_confirmatory" / name).is_dir()
                   else REPO / "embeddings" / name))
        blocks = sorted(cache)
        six_library_sets[dataset] = set(blocks)
        six_dimensions[dataset] = {block: int(cache[block].shape[1]) for block in blocks}
        manifest_path = manifest_root / "sample_manifests" / f"{dataset}.csv"
        for block in blocks:
            embedding_file = source / f"{block}.npy"
            inventory.append({
                "dataset": dataset, "n_images": len(y), "n_classes": int(len(np.unique(y))),
                "embedding_block": block, "dimensions": int(cache[block].shape[1]),
                "embedding_shape": f"{cache[block].shape[0]}x{cache[block].shape[1]}",
                "embedding_file_sha256": sha256_file(embedding_file),
                "labels_file_sha256": sha256_file(source / f"{block}_labels.npy"),
                "manifest_sha256": sha256_file(manifest_path),
                "train_indices_sha256": sha256_indices(train), "test_indices_sha256": sha256_indices(test),
                "n_train": len(train), "n_test": len(test),
                "official_split": cfg["official_split"] or "",
                "official_split_inverted": cfg["invert"],
                "curet_direction": cfg["curet_direction"] or "",
            })

    pd.DataFrame(registry).to_csv(out_dir / "condition_registry.csv", index=False)
    pd.DataFrame(inventory).to_csv(out_dir / "six_dataset_library_inventory.csv", index=False)
    pd.DataFrame(image_transitions).to_csv(out_dir / "rescue_error_transitions.csv", index=False)
    pd.DataFrame(class_transitions).to_csv(out_dir / "rescue_error_transitions_by_class.csv", index=False)
    pd.DataFrame(pilot_summaries).to_csv(out_dir / "pilot_comparability_summary.csv", index=False)
    block_sets = {r["dataset"]: set(r["available_block_names"].split(",")) for r in pilot_summaries}
    common = set.intersection(*block_sets.values())
    six_common = set.intersection(*six_library_sets.values())
    dimension_consistent = all(
        len({six_dimensions[dataset][block] for dataset in DATASET_SOURCES}) == 1
        for block in six_common
    )
    report = {
        "scope": "four existing integration_v1 pilots; no new model fitting",
        "datasets": list(PILOTS), "common_available_blocks_across_four_pilots": sorted(common),
        "common_available_block_count": len(common),
        "all_pilots_include_rgb_ngram_svd": all(r["includes_rgb_ngram_svd"] for r in pilot_summaries),
        "six_dataset_common_available_blocks": sorted(six_common),
        "six_dataset_common_block_count": len(six_common),
        "six_dataset_common_dimensions_consistent": dimension_consistent,
        "rgb_ngram_svd_ready_as_cached_block": any("rgb_ngram_svd" in blocks for blocks in six_library_sets.values()),
        "condition_registry_rows": len(registry), "image_transition_rows": len(image_transitions),
        "class_transition_rows": len(class_transitions),
        "caution": "the pilots do not instantiate the manuscript common-22 library; do not pool their metric differences as a matched comparison",
        "files": ["condition_registry.csv", "six_dataset_library_inventory.csv", "rescue_error_transitions.csv", "rescue_error_transitions_by_class.csv", "pilot_comparability_summary.csv"],
    }
    (out_dir / "audit_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
