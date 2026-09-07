#!/usr/bin/env python3
"""Auditoría conservadora de datos/embeddings para el protocolo confirmatorio."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


DATASETS = ("DTD", "FMD", "CUReT", "Soil", "VisTex")
RAW_DIRS = {
    "DTD": "data/DTD",
    "FMD": "data/confirmatory_sources/FMD/extracted/image",
    "CUReT": "data/confirmatory_sources/CUReT/curetgrey_extracted/curetgrey",
    "Soil": "data/Soil",
    "VisTex": "data/VisTex_clean",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".ppm", ".tif", ".tiff"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)


def embedding_audit(repo: Path, dataset: str) -> dict:
    confirmatory = repo / "embeddings_confirmatory" / dataset
    base = confirmatory if confirmatory.is_dir() else repo / "embeddings" / dataset
    feature_files = sorted(p for p in base.glob("*.npy") if not p.name.endswith("_labels.npy"))
    details = []
    reference = None
    aligned = True
    finite = True
    classes_metadata_consistent = True
    for feature in feature_files:
        labels_path = base / f"{feature.stem}_labels.npy"
        if not labels_path.exists():
            aligned = False
            details.append(f"{feature.stem}:missing_labels")
            continue
        x = np.load(feature, mmap_mode="r")
        y = np.load(labels_path, allow_pickle=False)
        classes_path = base / f"{feature.stem}_classes.json"
        if not classes_path.exists() or len(json.loads(classes_path.read_text())) != len(np.unique(y)):
            classes_metadata_consistent = False
        ok_shape = x.ndim == 2 and len(x) == len(y)
        # Compara particiones de clase, no representación (algunos extractores
        # guardan enteros y los nuevos guardan nombres de clase).
        remap = {}
        canonical = np.asarray([remap.setdefault(str(v), len(remap)) for v in y], dtype=np.int64)
        if reference is None:
            reference = canonical
        ok_labels = reference is not None and np.array_equal(reference, canonical)
        # El chequeo por bloques evita duplicar matrices grandes en RAM.
        ok_finite = all(np.isfinite(x[i : i + 512]).all() for i in range(0, len(x), 512))
        aligned &= ok_shape and ok_labels
        finite &= ok_finite
        details.append(f"{feature.stem}:{x.shape[1]}d")
    counts = Counter(reference.tolist()) if reference is not None else Counter()
    return {
        "n_extractors": len(feature_files),
        "n_samples": len(reference) if reference is not None else 0,
        "n_classes": len(counts),
        "min_class_n": min(counts.values()) if counts else 0,
        "max_class_n": max(counts.values()) if counts else 0,
        "labels_aligned": aligned and bool(feature_files),
        "finite": finite and bool(feature_files),
        "classes_metadata_consistent": classes_metadata_consistent and bool(feature_files),
        "extractor_dimensions": ";".join(details),
    }


def soil_groups(files: list[Path]) -> tuple[int, int, int]:
    """Agrupa sufijos a/b/c con su stem numérico explícito, dentro de clase."""
    groups = defaultdict(list)
    unmatched = 0
    for path in files:
        match = re.fullmatch(r"(\d+)[A-Za-z]?", path.stem)
        if not match:
            unmatched += 1
            continue
        groups[(path.parent.name, match.group(1))].append(path)
    repeated = sum(len(v) > 1 for v in groups.values())
    return len(groups), repeated, unmatched


def audit_dataset(repo: Path, dataset: str) -> dict:
    emb = embedding_audit(repo, dataset)
    raw_root = repo / RAW_DIRS[dataset]
    images = image_files(raw_root)
    readable_images = [p for p in images if p.stat().st_size > 0 and p.stat().st_mode & 0o444]
    unreadable_or_empty = len(images) - len(readable_images)
    hashes = Counter(sha256(p) for p in readable_images)
    exact_duplicate_sets = sum(v > 1 for v in hashes.values())
    status = "BLOCKED_DATA_LEAKAGE_RISK"
    split_basis = "none"
    notes = []

    if not images:
        notes.append("raw images/source identifiers unavailable")
    elif unreadable_or_empty:
        notes.append(f"{unreadable_or_empty} raw image entries are empty or unreadable placeholders")
    if not emb["labels_aligned"]:
        notes.append("embedding labels/shapes are not exactly aligned")
    if not emb["finite"]:
        notes.append("NaN or infinite values detected")
    if not emb["classes_metadata_consistent"]:
        notes.append("number of observed labels disagrees with extractor classes metadata")

    n_groups = 0
    repeated_groups = 0
    if dataset == "FMD" and images:
        if (len(images) == emb["n_samples"] == 1000 and emb["n_extractors"] == 20
                and unreadable_or_empty == 0 and exact_duplicate_sets == 0
                and emb["labels_aligned"] and emb["finite"] and emb["classes_metadata_consistent"]):
            status = "PASS_REEXTRACTED_GROUP_AWARE"
            split_basis = "manifest-defined order; SHA-256 groups; repeated stratified group CV"
            n_groups = len(hashes)
            notes.append("20 descriptors re-extracted from the official FMD archive in canonical manifest order")
        else:
            notes.append("confirmatory FMD re-extraction is incomplete or inconsistent")
    elif dataset == "CUReT" and images:
        manifest_path = repo / "results/confirmatory/sample_manifests/CUReT.csv"
        manifest_rows = []
        if manifest_path.exists():
            with manifest_path.open(newline="") as handle:
                manifest_rows = list(csv.DictReader(handle))
        required = {"row_id", "path", "label", "group", "sha256", "benchmark_half"}
        manifest_columns_ok = bool(manifest_rows) and required.issubset(manifest_rows[0])
        row_ids_ok = manifest_columns_ok and [int(row["row_id"]) for row in manifest_rows] == list(range(5612))
        group_counts = Counter(row["group"] for row in manifest_rows) if manifest_columns_ok else Counter()
        group_half = {}
        group_half_consistent = True
        for row in manifest_rows if manifest_columns_ok else []:
            previous = group_half.setdefault(row["group"], row["benchmark_half"])
            group_half_consistent &= previous == row["benchmark_half"]
        half_groups = Counter(group_half.values())
        manifest_hashes = Counter(row["sha256"] for row in manifest_rows) if manifest_columns_ok else Counter()
        manifest_ok = (
            len(manifest_rows) == 5612
            and row_ids_ok
            and len(group_counts) == 92
            and set(group_counts.values()) == {61}
            and group_half_consistent
            and half_groups == Counter({"alternating_a": 46, "alternating_b": 46})
            and manifest_hashes == hashes
        )
        if (len(images) == emb["n_samples"] == 5612 and emb["n_extractors"] == 20
                and emb["n_classes"] == 61 and emb["min_class_n"] == emb["max_class_n"] == 92
                and unreadable_or_empty == 0 and exact_duplicate_sets == 0
                and emb["labels_aligned"] and emb["finite"] and emb["classes_metadata_consistent"]
                and manifest_ok):
            status = "PASS_REEXTRACTED_CONDITION_GROUPED"
            split_basis = "Oxford cropped subset; condition-ID groups; deterministic complementary 46/46 halves"
            n_groups = len(group_counts)
            notes.append("20 descriptors re-extracted from Oxford's 61x92 grayscale CUReT subset in canonical manifest order")
            notes.append("alternating halves are a deterministic reproduction, not the unpublished historical assignment")
        else:
            notes.append("confirmatory CUReT re-extraction or condition-group manifest is incomplete or inconsistent")
    elif dataset == "Soil" and images:
        n_groups, repeated_groups, unmatched = soil_groups(images)
        if unmatched:
            notes.append(f"{unmatched} filenames do not match documented numeric+suffix convention")
        if len(images) != emb["n_samples"]:
            notes.append("raw image count differs from embeddings")
        elif unreadable_or_empty == 0 and unmatched == 0 and emb["labels_aligned"] and emb["finite"]:
            status = "PASS_GROUP_AWARE"
            split_basis = "class directory + numeric filename stem; letter suffix denotes related capture"
            notes.append("embedding order can be reconstructed as class-sorted/path-sorted, matching extraction convention")
    elif dataset == "VisTex" and emb["min_class_n"] < 5:
        notes.append("at least one class has fewer than 5 samples; frozen 5-fold outer CV is infeasible")
    else:
        notes.append("no official split/group metadata linked to embedding row order")

    return {
        "dataset": dataset,
        **emb,
        "raw_path": str(raw_root.relative_to(repo)),
        "raw_images": len(images),
        "exact_duplicate_sets": exact_duplicate_sets,
        "source_groups": n_groups,
        "repeated_source_groups": repeated_groups,
        "split_basis": split_basis,
        "status": status,
        "notes": "; ".join(notes),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("results/confirmatory"))
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = (repo / args.output).resolve() if not args.output.is_absolute() else args.output
    output.mkdir(parents=True, exist_ok=True)
    rows = [audit_dataset(repo, d) for d in DATASETS]
    status_path = output / "sample_manifests" / "manifest_status.json"
    if status_path.exists():
        manifest_statuses = {r["dataset"]: r for r in json.loads(status_path.read_text())["datasets"]}
        for row in rows:
            key = row["dataset"]
            manifest = manifest_statuses.get(key)
            if key == "DTD" and manifest and manifest["status"] == "LINKED_ORDER_LABEL_EXACT":
                row["status"] = "PASS_OFFICIAL_SPLITS_PURGED_DUPLICATES"
                row["split_basis"] = "primary DTD release: split_1..split_10 train/val/test"
                row["notes"] += "; restored row manifest exactly matches embedding label order; runner purges test-SHA duplicates from train/val"
            elif key == "FMD" and manifest:
                row["notes"] += f"; manifest identity status: {manifest['status']}"
            elif key == "CUReT" and "CUReT_official_full" in manifest_statuses:
                row["notes"] += "; historical 100-view embeddings remain excluded; confirmatory data use the independently verified Oxford 92-view subset"
            elif key == "VisTex" and "VisTex_official" in manifest_statuses:
                row["notes"] += "; official 19-class manifest exists; current 23-class embeddings require re-extraction"
    fields = list(rows[0])
    with (output / "data_audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Confirmatory data audit",
        "",
        "This audit is a gate, not a repair step. `BLOCKED_DATA_LEAKAGE_RISK` datasets were not evaluated.",
        "",
        "| Dataset | Samples | Extractors | Raw images | Split decision | Status |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['dataset']} | {row['n_samples']} | {row['n_extractors']} | {row['raw_images']} | "
            f"{row['split_basis'] or 'unverified'} | {row['status']} |"
        )
    lines.extend(["", "## Dataset notes", ""])
    for row in rows:
        lines.extend([f"### {row['dataset']}", "", row["notes"], ""])
    (output / "data_audit.md").write_text("\n".join(lines))
    manifest = {"schema_version": 1, "rows": rows}
    (output / "data_audit.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({r["dataset"]: r["status"] for r in rows}, indent=2))


if __name__ == "__main__":
    main()
