#!/usr/bin/env python3
"""Build a provenance manifest for KTH-TIPS2-b and its four sample splits."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[4]
SOURCE = REPO / "results/confirmatory/recovery/kth/staging/KTH-TIPS2-b"
OUTPUT = REPO / "results/confirmatory/recovery/kth/KTH-TIPS2-b_manifest.csv"
EXTENSION = REPO / "results/extensions/kth_tips2b"
SAMPLES = ("sample_a", "sample_b", "sample_c", "sample_d")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def image_info(path: Path) -> tuple[str, int, int, str]:
    with Image.open(path) as image:
        image.load()
        rgb = image.convert("RGB")
        return hashlib.sha256(rgb.tobytes()).hexdigest(), rgb.width, rgb.height, image.format or "UNKNOWN"


def main() -> None:
    images = sorted(SOURCE.glob("*/*/*.png"), key=lambda path: path.as_posix())
    if len(images) != 4752:
        raise RuntimeError(f"expected 4752 PNGs, found {len(images)}")
    labels = sorted({path.parent.parent.name for path in images})
    if len(labels) != 11:
        raise RuntimeError(f"expected 11 labels, found {labels}")
    by_sample = {(label, sample): 0 for label in labels for sample in SAMPLES}
    rows = []
    for row_id, path in enumerate(images):
        label, sample = path.parent.parent.name, path.parent.name
        if sample not in SAMPLES:
            raise RuntimeError(f"unexpected sample directory: {path}")
        pixel_hash, width, height, image_format = image_info(path)
        by_sample[(label, sample)] += 1
        row = {
            "row_id": row_id,
            "label": label,
            "group": f"{label}:{sample}",
            "source_path": path.relative_to(REPO).as_posix(),
            "source_sha256": sha256(path),
            "pixel_sha256": pixel_hash,
            "width": width,
            "height": height,
            "format": image_format,
            "source_version": "KTH official KTH-TIPS2-b colour 200x200 archive",
        }
        for index, held_out in enumerate(SAMPLES, start=1):
            row[f"split_{index}"] = "test" if sample == held_out else "train"
        rows.append(row)
    if set(by_sample.values()) != {108}:
        raise RuntimeError(f"expected 108 images per class/sample, observed {sorted(set(by_sample.values()))}")
    fields = list(rows[0])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    EXTENSION.mkdir(parents=True, exist_ok=True)
    (EXTENSION / "sample_manifests").mkdir(exist_ok=True)
    with (EXTENSION / "sample_manifests/KTH-TIPS2-b.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (EXTENSION / "data_audit.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["dataset", "status", "n_samples", "n_classes", "n_groups", "protocol"])
        writer.writeheader()
        writer.writerow({"dataset": "KTH-TIPS2-b", "status": "PASS_OFFICIAL_SAMPLE_SPLITS", "n_samples": 4752, "n_classes": 11, "n_groups": 44, "protocol": "4 official leave-one-physical-sample-out splits"})
    print(f"manifest={OUTPUT}")
    print("samples=4752 classes=11 groups=44 splits=4 images_per_group=108")


if __name__ == "__main__":
    main()
