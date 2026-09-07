#!/usr/bin/env python3
"""Build the frozen, leakage-aware Soil Original manifest from the audited archive."""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[4]
SOURCE = REPO / "results/confirmatory/recovery/soil/staging/original"
OUTPUT = REPO / "results/confirmatory/recovery/soil/Soil_Original_manifest.csv"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".webp", ".png", ".bmp", ".tif", ".tiff"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pixel_sha256(path: Path) -> tuple[str, int, int, str]:
    with Image.open(path) as image:
        image.load()
        rgb = image.convert("RGB")
        digest = hashlib.sha256(rgb.tobytes()).hexdigest()
        return digest, rgb.width, rgb.height, image.format or "UNKNOWN"


def family_key(path: Path) -> str:
    match = re.match(r"^(\d+)", path.stem)
    stem = match.group(1) if match else path.stem.casefold()
    return f"{path.parent.name}:{stem}"


def main() -> None:
    images = sorted(
        (path for path in SOURCE.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS),
        key=lambda path: (path.parent.name, path.name.casefold(), path.name),
    )
    if len(images) != 1189:
        raise RuntimeError(f"expected 1189 decoded source files, found {len(images)}")

    records = []
    for path in images:
        byte_hash = sha256(path)
        pixel_hash, width, height, image_format = pixel_sha256(path)
        records.append({
            "path": path,
            "label": path.parent.name,
            "source_sha256": byte_hash,
            "pixel_sha256": pixel_hash,
            "width": width,
            "height": height,
            "format": image_format,
            "family": family_key(path),
        })

    # Keep one canonical representative of every byte-identical image. The
    # complete inventory remains recoverable from the immutable source ZIP.
    by_hash: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_hash[record["source_sha256"]].append(record)
    selected = [members[0] for _, members in sorted(by_hash.items(), key=lambda item: (
        item[1][0]["label"], item[1][0]["path"].name.casefold(), item[1][0]["path"].name
    ))]
    selected.sort(key=lambda record: (record["label"], record["path"].name.casefold(), record["path"].name))

    cross_label = [members for members in by_hash.values() if len({r["label"] for r in members}) > 1]
    if cross_label:
        raise RuntimeError("byte-identical images have conflicting labels")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "row_id", "label", "group", "source_path", "source_sha256", "pixel_sha256",
        "width", "height", "format", "official_split", "source_version",
    ]
    with OUTPUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row_id, record in enumerate(selected):
            writer.writerow({
                "row_id": row_id,
                "label": record["label"],
                "group": record["family"],
                "source_path": record["path"].relative_to(REPO),
                "source_sha256": record["source_sha256"],
                "pixel_sha256": record["pixel_sha256"],
                "width": record["width"],
                "height": record["height"],
                "format": record["format"],
                "official_split": "NONE_DEFINED_BY_ARCHIVE",
                "source_version": "Kaggle ai4a-lab/comprehensive-soil-classification-datasets v1",
            })

    counts = Counter(record["label"] for record in selected)
    print(f"source_files={len(records)}")
    print(f"selected_after_exact_dedup={len(selected)}")
    print(f"exact_duplicate_files_removed={len(records) - len(selected)}")
    print(f"dependency_groups={len({record['family'] for record in selected})}")
    print(f"class_counts={dict(sorted(counts.items()))}")
    print(f"manifest={OUTPUT}")


if __name__ == "__main__":
    main()
