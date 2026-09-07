#!/usr/bin/env python3
"""Build the canonical FMD sample manifest from the official image archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from pathlib import Path


EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.images.resolve()
    classes = sorted(path.name for path in root.iterdir() if path.is_dir())
    if len(classes) != 10:
        raise ValueError(f"expected 10 FMD classes, found {len(classes)}")
    rows = []
    for label, class_name in enumerate(classes):
        paths = sorted(path for path in (root / class_name).iterdir() if path.suffix.lower() in EXTENSIONS)
        if len(paths) != 100:
            raise ValueError(f"expected 100 images for {class_name}, found {len(paths)}")
        for path in paths:
            digest = file_sha256(path)
            rows.append({
                "row_id": len(rows), "path": str(path), "label": label, "class_name": class_name,
                "sha256": digest, "group": digest,
            })
    duplicates = {digest: count for digest, count in Counter(row["sha256"] for row in rows).items() if count > 1}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"rows={len(rows)} classes={len(classes)} duplicate_hash_groups={len(duplicates)}")


if __name__ == "__main__":
    main()
