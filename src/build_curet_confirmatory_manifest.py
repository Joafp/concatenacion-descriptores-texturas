#!/usr/bin/env python3
"""Build and audit the canonical manifest for Oxford's cropped CUReT release.

The two ``benchmark_half`` values reproduce a deterministic alternating
partition of the lexicographically ordered common condition IDs.  They do not
claim to recover an unpublished historical split assignment.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


CLASS_RE = re.compile(r"sample(\d{2})$")
IMAGE_RE = re.compile(r"(\d{2})-(\d{3})\.png$", re.IGNORECASE)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_class(root: Path, class_dir: Path) -> dict[str, Path]:
    match = CLASS_RE.fullmatch(class_dir.name)
    if match is None:
        raise ValueError(f"unexpected class directory: {class_dir.relative_to(root)}")
    class_number = match.group(1)
    images: dict[str, Path] = {}
    unexpected = []
    for path in sorted(class_dir.iterdir()):
        if not path.is_file():
            unexpected.append(path.name)
            continue
        image_match = IMAGE_RE.fullmatch(path.name)
        if image_match is None or image_match.group(1) != class_number:
            unexpected.append(path.name)
            continue
        condition_id = image_match.group(2)
        if condition_id in images:
            raise ValueError(f"duplicate condition ID {condition_id} in {class_dir.name}")
        images[condition_id] = path.resolve(strict=True)
    if unexpected:
        raise ValueError(f"unexpected entries in {class_dir.name}: {unexpected[:5]}")
    if len(images) != 92:
        raise ValueError(f"expected 92 PNG images in {class_dir.name}, found {len(images)}")
    return images


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()

    root = args.images.resolve(strict=True)
    class_dirs = sorted(
        (path for path in root.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    )
    expected_classes = [f"sample{number:02d}" for number in range(1, 62)]
    observed_classes = [path.name for path in class_dirs]
    if observed_classes != expected_classes:
        raise ValueError("class directories are not exactly sample01 through sample61")

    by_class = {class_dir.name: parse_class(root, class_dir) for class_dir in class_dirs}
    reference_ids = sorted(by_class[expected_classes[0]])
    for class_name, images in by_class.items():
        if sorted(images) != reference_ids:
            missing = sorted(set(reference_ids) - set(images))
            extra = sorted(set(images) - set(reference_ids))
            raise ValueError(
                f"condition IDs differ for {class_name}: missing={missing}, extra={extra}"
            )

    rows = []
    sizes = Counter()
    modes = Counter()
    hashes = Counter()
    for label, class_name in enumerate(expected_classes):
        for condition_position, condition_id in enumerate(reference_ids):
            path = by_class[class_name][condition_id]
            try:
                with Image.open(path) as image:
                    image.load()
                    image_size = tuple(image.size)
                    sizes[image_size] += 1
                    modes[image.mode] += 1
            except Exception as exc:
                raise ValueError(f"unreadable image {path}: {exc}") from exc
            if image_size != (200, 200):
                raise ValueError(f"expected 200x200 image, got {image_size} for {path}")
            digest = file_sha256(path)
            hashes[digest] += 1
            rows.append({
                "row_id": len(rows),
                "path": str(path),
                "label": label,
                "class_name": class_name,
                "condition_id": condition_id,
                "condition_position": condition_position,
                "group": condition_id,
                "sha256": digest,
                "benchmark_half": "alternating_a" if condition_position % 2 == 0 else "alternating_b",
                "split_provenance": "deterministic alternating reproduction",
            })

    duplicate_hashes = {digest: count for digest, count in hashes.items() if count > 1}
    half_counts = Counter(row["benchmark_half"] for row in rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    audit = {
        "dataset": "CUReT",
        "source_root": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_CANONICAL_MANIFEST",
        "classes": len(expected_classes),
        "images_per_class": 92,
        "rows": len(rows),
        "common_condition_ids": len(reference_ids),
        "condition_ids": reference_ids,
        "condition_ids_identical_across_classes": True,
        "group_semantics": "condition_id shared across all 61 material classes",
        "benchmark_half_semantics": "deterministic alternating reproduction; not a claim of the exact historical split",
        "images_per_class_by_half": {"alternating_a": 46, "alternating_b": 46},
        "rows_by_half": dict(sorted(half_counts.items())),
        "readable_images": len(rows),
        "image_sizes": {f"{width}x{height}": count for (width, height), count in sorted(sizes.items())},
        "image_modes": dict(sorted(modes.items())),
        "unique_sha256": len(hashes),
        "duplicate_sha256_groups": len(duplicate_hashes),
        "duplicate_sha256_rows": sum(duplicate_hashes.values()),
    }
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(json.dumps(audit, indent=2) + "\n")
    print(
        f"rows={len(rows)} classes={len(expected_classes)} conditions={len(reference_ids)} "
        f"halves=46/46 duplicate_hash_groups={len(duplicate_hashes)}"
    )


if __name__ == "__main__":
    main()
