#!/usr/bin/env python3
"""Build and validate the study-defined VisTex Reference-12 manifest."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[3]
REFERENCE = HERE / "staging/VisionTexture/VisTex/Images/Reference"
MANIFEST = HERE / "VisTex_Reference12_manifest.csv"
REPORT = HERE / "VALIDATION.md"
MIN_SOURCES = 7
OFFICIAL_SPLIT = "NONE_DEFINED_BY_ARCHIVE"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if not REFERENCE.is_dir():
        raise SystemExit(f"Reference directory not found: {REFERENCE}")

    all_images = sorted(REFERENCE.glob("*/*.ppm"), key=lambda p: (p.parent.name, p.name))
    all_counts = Counter(path.parent.name for path in all_images)
    eligible = sorted(label for label, count in all_counts.items() if count >= MIN_SOURCES)
    selected = [path for path in all_images if path.parent.name in eligible]

    rows = []
    hashes: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row_id, path in enumerate(selected):
        digest = sha256(path)
        relpath = path.relative_to(WORKSPACE).as_posix()
        label = path.parent.name
        hashes[digest].append((label, relpath))
        rows.append(
            {
                "row_id": row_id,
                "label": label,
                "group": digest,
                "source_path": relpath,
                "source_sha256": digest,
                "official_split": OFFICIAL_SPLIT,
            }
        )

    selected_counts = Counter(row["label"] for row in rows)
    duplicate_hashes = {digest: values for digest, values in hashes.items() if len(values) > 1}
    cross_label_duplicates = {
        digest: values
        for digest, values in duplicate_hashes.items()
        if len({label for label, _ in values}) > 1
    }

    checks = {
        "archive_reference_images": len(all_images) == 167,
        "selected_images": len(rows) == 140,
        "selected_classes": len(selected_counts) == 12,
        "minimum_class_count": min(selected_counts.values()) >= MIN_SOURCES,
        "unique_row_ids": len({row["row_id"] for row in rows}) == len(rows),
        "unique_source_paths": len({row["source_path"] for row in rows}) == len(rows),
        "unique_groups": len({row["group"] for row in rows}) == len(rows),
        "group_equals_source_sha256": all(
            row["group"] == row["source_sha256"] for row in rows
        ),
        "no_exact_duplicates": not duplicate_hashes,
        "no_cross_label_duplicates": not cross_label_duplicates,
        "paintings_not_split": "Paintings" in selected_counts
        and not any(label.startswith("Paintings.") for label in selected_counts),
        "split_marker": all(row["official_split"] == OFFICIAL_SPLIT for row in rows),
    }

    if not all(checks.values()):
        failed = ", ".join(name for name, passed in checks.items() if not passed)
        raise SystemExit(f"Manifest validation failed before write: {failed}")

    fieldnames = [
        "row_id",
        "label",
        "group",
        "source_path",
        "source_sha256",
        "official_split",
    ]
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    manifest_digest = sha256(MANIFEST)
    class_lines = "\n".join(
        f"| {label} | {selected_counts[label]} |" for label in sorted(selected_counts)
    )
    check_lines = "\n".join(
        f"| `{name}` | {'PASS' if passed else 'FAIL'} |" for name, passed in checks.items()
    )
    report = f"""# VisTex Reference-12 manifest validation

Date: 2026-07-21

Status: **PASS**

This report validates the study-defined VisTex Reference-12 manifest generated
from the independently extracted staging copy. No descriptor or classifier was
executed.

## Frozen selection rule

- Input: `staging/VisionTexture/VisTex/Images/Reference/<category>/*.ppm`
- Label: immediate parent directory (so all `Paintings.*.ppm` remain
  `Paintings`)
- Eligibility: categories with at least {MIN_SOURCES} independent source images
- Ordering: `(label, filename)`, ascending
- Group: full source-image SHA-256
- Split marker: `{OFFICIAL_SPLIT}`

## Output

- Manifest: `{MANIFEST.name}`
- Rows: {len(rows)}
- Classes: {len(selected_counts)}
- Unique source groups: {len({row['group'] for row in rows})}
- Manifest SHA-256: `{manifest_digest}`

## Class counts

| Label | Sources |
|---|---:|
{class_lines}

Minimum: {min(selected_counts.values())}; maximum: {max(selected_counts.values())}.

## Integrity checks

| Check | Result |
|---|---|
{check_lines}

Exact duplicate hashes in selected set: {len(duplicate_hashes)}. Cross-label
duplicate hashes: {len(cross_label_duplicates)}.

## Interpretation

The manifest is internally suitable for preregistering grouped nested
validation at the source-image level. Fold construction still has to verify
class support in every realized outer and inner partition. This validation
does not authorize using historical VisTex embeddings, which retain the old
23-label error.
"""
    REPORT.write_text(report, encoding="utf-8")

    print(f"Wrote {MANIFEST} ({len(rows)} rows, {len(selected_counts)} classes)")
    print(f"Wrote {REPORT}")
    print(f"Manifest SHA-256: {manifest_digest}")


if __name__ == "__main__":
    main()
