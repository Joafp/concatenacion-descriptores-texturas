#!/usr/bin/env python3
"""Audit provenance and coverage for saved integration-v2 nested frontiers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_confirmatory_nested import load_dataset, load_manifest
from run_topk_individual_control import outer_indices

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "results/exploratory/integration_v2/nested_frontier21"
OUT = REPO / "results/analysis/integration_v2"
CONDITIONS = {
    "DTD": ("DTD", "results/confirmatory", None, None, False, None),
    "FMD_auto": ("FMD", "results/confirmatory", None, None, False, None),
    "CUReT_a_to_b": ("CUReT", "results/confirmatory", None, "a_to_b", False, None),
    "CUReT_b_to_a": ("CUReT", "results/confirmatory", None, "b_to_a", False, None),
    "Outex13Official1360": ("Outex13Official1360", "results/extensions/outex13_official1360", 1, None, False, "embeddings_extensions"),
    "SoilOriginal": ("SoilOriginal", "results/extensions/soil_original", None, None, False, "embeddings_extensions"),
    "KTHTIPS2b": ("KTHTIPS2b", "results/extensions/kth_tips2b", 1, None, True, "embeddings_extensions"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_indices(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values, dtype="<i8").tobytes()).hexdigest()


def main() -> None:
    records = []
    policy_rows = []
    for folder, spec in CONDITIONS.items():
        dataset, manifest_rel, official, direction, invert, embedding_rel = spec
        path = ROOT / folder
        front_path = next(path.glob("*_nested_frontier.csv"))
        cv_path = next(path.glob("*_cv_folds.json"))
        meta_path = next(path.glob("*_metadata.json"))
        pred_path = next(path.glob("*_oof_predictions.csv"))
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        cv_payload = json.loads(cv_path.read_text(encoding="utf-8"))
        # Older runs stored a bare list; provenance-complete runs store the
        # fold summary and detailed artifacts under separate keys.
        cv = cv_payload.get("folds", cv_payload) if isinstance(cv_payload, dict) else cv_payload
        oof = pd.read_csv(pred_path)
        embedding_root = REPO / embedding_rel if embedding_rel else None
        cache, y = load_dataset(REPO, dataset, embedding_root)
        groups, rows = load_manifest(REPO / manifest_rel, dataset, y)
        train, test = outer_indices(dataset, 42, 0, y, groups, rows,
                                    official, direction, invert)
        oof_idx = oof["row_index"].to_numpy(dtype=int)
        if len(oof_idx) != len(train) or not np.array_equal(oof_idx, train):
            raise ValueError(f"OOF rows do not exactly cover outer training rows: {folder}")
        if not np.array_equal(oof["label"].to_numpy(), y[train]):
            raise ValueError(f"OOF labels do not match source label order: {folder}")
        frontier = pd.read_csv(front_path)
        cv_frame = pd.DataFrame(cv)
        common_library = metadata["library"]
        nondominated = frontier.loc[frontier["pareto_nondominated"]]
        for _, row in frontier.iterrows():
            policy_rows.append({"condition": folder, **row.to_dict()})
        records.append({
            "condition": folder, "dataset": dataset, "classifier": "svm", "seed": 42,
            "outer_fold": 0, "official_split": official or "",
            "official_split_inverted": invert, "curet_direction": direction or "",
            "inner_group_column": metadata["inner_group_column"],
            "n_outer_train": len(train), "n_external_test_reserved": len(test),
            "outer_train_indices_sha256": sha256_indices(train),
            "external_test_indices_sha256": sha256_indices(test),
            "manifest_sha256": sha256_file(REPO / manifest_rel / "sample_manifests" / f"{dataset}.csv"),
            "oof_prediction_sha256": sha256_file(pred_path),
            "frontier_sha256": sha256_file(front_path), "cv_log_sha256": sha256_file(cv_path),
            "metadata_sha256": sha256_file(meta_path),
            "oof_exact_train_coverage": True, "external_test_used": False,
            "cv_folds": int(cv_frame["cv_fold"].nunique()), "library_blocks": 21,
            "library_block_names": ";".join(common_library),
            "rgb_ngram_svd_included": "rgb_ngram_svd" in cache,
            "base_blocks_by_cv_fold": json.dumps(metadata.get("base_blocks_by_cv_fold", {}), ensure_ascii=False),
            "nondominated_policy_count": len(nondominated),
            "executed_source_hash_captured_at_launch": False,
            "source_hash_at_registry_creation": sha256_file(REPO / "src/run_rescue_nested_selection.py"),
            "note": "the output is a nested outer-training estimate; no external test metrics were calculated",
        })
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(OUT / "nested_selection_registry.csv", index=False)
    pd.DataFrame(policy_rows).to_csv(OUT / "nested_frontier_summary.csv", index=False)
    print(f"registered {len(records)} nested conditions and {len(policy_rows)} policy rows")
    print("conditions:", ", ".join(r["condition"] for r in records))
    print("all OOF predictions exactly cover their outer training partition; external tests reserved")


if __name__ == "__main__":
    main()
