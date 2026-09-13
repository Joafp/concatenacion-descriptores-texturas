#!/usr/bin/env python3
"""Build and validate the official KTH-TIPS2-b manifest.

Source: Mallikarjuna, Tavakoli Targhi, Fritz, Hayman, Caputo and Eklundh (2006),
"The KTH-TIPS2 database" (KTH CVAP user guide). Official train/test protocol:
Caputo, Hayman and Mallikarjuna, "Class-specific material categorisation",
ICCV 2005 -- train on the images of ONE physical sample, test on the images of
the OTHER THREE samples, rotating over the four samples (a, b, c, d). This
yields four fixed folds; there is no official validation split, so
``official_split_indices`` in ``src/run_confirmatory_nested.py`` will read the
``split_N`` columns with roles restricted to {"train", "test"}.

Expected raw layout (one directory per material, one subdirectory per physical
sample, downloaded from the KTH CVAP kth-tips page):

    <root>/<material>/sample_<a|b|c|d>/*.png

11 materials x 4 samples x 108 images/sample = 4,752 images total.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED_MATERIALS = 11
EXPECTED_SAMPLES_PER_MATERIAL = 4
EXPECTED_IMAGES_PER_SAMPLE = 108
EXPECTED_TOTAL_IMAGES = (
    EXPECTED_MATERIALS * EXPECTED_SAMPLES_PER_MATERIAL * EXPECTED_IMAGES_PER_SAMPLE
)
SAMPLE_LETTERS = ("a", "b", "c", "d")
SAMPLE_DIR_RE = re.compile(r"^sample[_-]?([a-dA-D])$")
IMAGE_SUFFIXES = {".png", ".ppm", ".bmp"}
OFFICIAL_SPLIT_MARKER = "FOUR_FOLD_ONE_SAMPLE_TRAIN_SEE_split_1_4"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_samples(material_dir: Path) -> dict[str, Path]:
    samples: dict[str, Path] = {}
    for entry in sorted(material_dir.iterdir()):
        if not entry.is_dir():
            continue
        match = SAMPLE_DIR_RE.match(entry.name)
        if match:
            samples[match.group(1).lower()] = entry
    return samples


def build_rows(root: Path, workspace: Path) -> list[dict]:
    material_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    if len(material_dirs) != EXPECTED_MATERIALS:
        raise SystemExit(
            f"expected {EXPECTED_MATERIALS} material directories under {root}, "
            f"found {len(material_dirs)}: {[p.name for p in material_dirs]}"
        )

    rows: list[dict] = []
    row_id = 0
    for material_dir in material_dirs:
        label = material_dir.name
        samples = discover_samples(material_dir)
        missing = set(SAMPLE_LETTERS) - set(samples)
        if missing:
            raise SystemExit(
                f"material '{label}' is missing sample directories: {sorted(missing)}"
            )
        for letter in SAMPLE_LETTERS:
            images = sorted(
                p for p in samples[letter].iterdir()
                if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
            )
            if len(images) != EXPECTED_IMAGES_PER_SAMPLE:
                raise SystemExit(
                    f"material '{label}' sample '{letter}' has {len(images)} images, "
                    f"expected {EXPECTED_IMAGES_PER_SAMPLE} ({samples[letter]})"
                )
            for image in images:
                digest = sha256(image)
                row = {
                    "row_id": row_id,
                    "label": label,
                    "sample": letter,
                    "group": digest,
                    "source_path": image.relative_to(workspace).as_posix(),
                    "source_sha256": digest,
                    "official_split": OFFICIAL_SPLIT_MARKER,
                }
                for split_number, train_letter in enumerate(SAMPLE_LETTERS, start=1):
                    row[f"split_{split_number}"] = "train" if letter == train_letter else "test"
                rows.append(row)
                row_id += 1
    return rows


def validate(rows: list[dict]) -> dict:
    labels = sorted({row["label"] for row in rows})
    hashes = [row["source_sha256"] for row in rows]
    per_label_sample_counts = Counter((row["label"], row["sample"]) for row in rows)
    per_split_roles: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        for split_number in range(1, EXPECTED_SAMPLES_PER_MATERIAL + 1):
            per_split_roles[f"split_{split_number}"][row[f"split_{split_number}"]] += 1

    checks = {
        "rows_4752": len(rows) == EXPECTED_TOTAL_IMAGES,
        "classes_11": len(labels) == EXPECTED_MATERIALS,
        "108_images_per_material_sample": all(
            count == EXPECTED_IMAGES_PER_SAMPLE for count in per_label_sample_counts.values()
        )
        and len(per_label_sample_counts) == EXPECTED_MATERIALS * EXPECTED_SAMPLES_PER_MATERIAL,
        "unique_row_ids": len({row["row_id"] for row in rows}) == len(rows),
        "unique_source_paths": len({row["source_path"] for row in rows}) == len(rows),
        "unique_hashes": len(set(hashes)) == len(hashes),
        "no_cross_label_hashes": all(
            len({row["label"] for row in rows if row["source_sha256"] == digest}) == 1
            for digest in set(hashes)
        ),
    }
    for split_number in range(1, EXPECTED_SAMPLES_PER_MATERIAL + 1):
        column = f"split_{split_number}"
        roles = per_split_roles[column]
        # One sample (108 images/material) trains, the other three (324) test.
        checks[f"{column}_train_test_balance"] = roles == Counter(
            {"train": EXPECTED_MATERIALS * EXPECTED_IMAGES_PER_SAMPLE,
             "test": EXPECTED_MATERIALS * EXPECTED_IMAGES_PER_SAMPLE * 3}
        )
    return checks


def main() -> None:
    here = Path(__file__).resolve().parent
    workspace = here.parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, required=True,
        help="path to the extracted KTH-TIPS2-b archive "
             "(directory containing one subfolder per material)",
    )
    parser.add_argument(
        "--manifest", type=Path, default=here / "KTH-TIPS2-b_manifest.csv",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"--root is not a directory: {root}")

    rows = build_rows(root, workspace)
    checks = validate(rows)
    if not all(checks.values()):
        failed = ", ".join(name for name, passed in checks.items() if not passed)
        raise SystemExit(f"manifest validation failed before write: {failed}")

    fieldnames = [
        "row_id", "label", "sample", "group", "source_path", "source_sha256",
        "official_split", "split_1", "split_2", "split_3", "split_4",
    ]
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    manifest_digest = sha256(args.manifest)
    print(f"Wrote {args.manifest} ({len(rows)} rows, {len(set(r['label'] for r in rows))} classes)")
    print(f"Manifest SHA-256: {manifest_digest}")
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")


if __name__ == "__main__":
    main()
