#!/usr/bin/env python3
"""Audit and materialize the complete official Outex_TC_00013 archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from PIL import Image


EXPECTED_IMAGES = 1360
EXPECTED_CLASSES = 68
EXPECTED_PER_CLASS = 20


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_protocol(value: bytes) -> list[tuple[str, int]]:
    lines = [line.strip() for line in value.decode("utf-8").splitlines() if line.strip()]
    expected = int(lines[0])
    rows = [(parts[0], int(parts[1])) for parts in (line.split() for line in lines[1:])]
    if len(rows) != expected:
        raise ValueError(f"protocol declares {expected} rows but contains {len(rows)}")
    return rows


def parse_classes(value: bytes) -> dict[int, str]:
    lines = [line.strip() for line in value.decode("utf-8").splitlines() if line.strip()]
    expected = int(lines[0])
    classes = {int(parts[1]): parts[0] for parts in (line.split() for line in lines[1:])}
    if len(classes) != expected or expected != EXPECTED_CLASSES:
        raise ValueError("unexpected Outex class table")
    return classes


def safe_destination(root: Path, member: str) -> Path:
    relative = PurePosixPath(member)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe ZIP member: {member}")
    destination = root.joinpath(*relative.parts).resolve()
    if root.resolve() not in destination.parents and destination != root.resolve():
        raise ValueError(f"ZIP member escapes output directory: {member}")
    return destination


def prepare(archive: Path, output: Path, manifest: Path) -> dict[str, object]:
    image_prefix = "Outex_TC_00013/images/"
    train_name = "Outex_TC_00013/000/train.txt"
    test_name = "Outex_TC_00013/000/test.txt"
    classes_name = "Outex_TC_00013/000/classes.txt"
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("ZIP CRC validation failed")
        names = bundle.namelist()
        image_members = sorted(
            name for name in names if name.startswith(image_prefix) and name.lower().endswith(".bmp")
        )
        expected_names = [f"{image_prefix}{index:06d}.bmp" for index in range(EXPECTED_IMAGES)]
        if image_members != expected_names:
            raise ValueError("archive does not contain the complete ordered 000000--001359 image set")
        classes = parse_classes(bundle.read(classes_name))
        train = parse_protocol(bundle.read(train_name))
        test = parse_protocol(bundle.read(test_name))
        train_names = {name for name, _ in train}
        test_names = {name for name, _ in test}
        if train_names & test_names or len(train_names | test_names) != EXPECTED_IMAGES:
            raise ValueError("official train/test protocol is incomplete or overlapping")
        protocol = {name: (label, "train") for name, label in train}
        protocol.update({name: (label, "test") for name, label in test})
        counts = Counter(label for label, _ in protocol.values())
        if counts != Counter({label: EXPECTED_PER_CLASS for label in range(EXPECTED_CLASSES)}):
            raise ValueError("class balance differs from 20 images per class")

        manifest_rows: list[dict[str, object]] = []
        hashes: defaultdict[str, list[str]] = defaultdict(list)
        metadata = Counter()
        for row_id, member in enumerate(image_members):
            data = bundle.read(member)
            digest = sha256_bytes(data)
            hashes[digest].append(member)
            with Image.open(io.BytesIO(data)) as image:
                image.load()
                metadata[(image.size, image.mode, image.format)] += 1
            destination = safe_destination(output, member)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and sha256_file(destination) != digest:
                raise ValueError(f"existing extracted image differs: {destination}")
            if not destination.exists():
                temporary = destination.with_suffix(".tmp")
                temporary.write_bytes(data)
                os.replace(temporary, destination)
            basename = Path(member).name
            label, split = protocol[basename]
            manifest_rows.append(
                {
                    "row_id": row_id,
                    "path": str(destination),
                    "label": label,
                    "class_name": classes[label],
                    "official_split": split,
                    "source_member": member,
                    "source_sha256": digest,
                    "group": digest,
                }
            )
    if any(len(group) > 1 for group in hashes.values()):
        raise ValueError("duplicate image payload detected")
    if metadata != Counter({((128, 128), "RGB", "BMP"): EXPECTED_IMAGES}):
        raise ValueError(f"unexpected image metadata: {metadata}")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    fields = list(manifest_rows[0])
    temporary_manifest = manifest.with_suffix(".tmp.csv")
    with temporary_manifest.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest_rows)
    os.replace(temporary_manifest, manifest)
    report = {
        "archive": str(archive.resolve()),
        "archive_sha256": sha256_file(archive),
        "manifest": str(manifest.resolve()),
        "manifest_sha256": sha256_file(manifest),
        "images": EXPECTED_IMAGES,
        "classes": EXPECTED_CLASSES,
        "train": len(train),
        "test": len(test),
        "image_metadata": {"width": 128, "height": 128, "mode": "RGB", "format": "BMP"},
        "duplicate_payloads": 0,
    }
    report_path = manifest.with_suffix(".audit.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive", type=Path, default=repo / "Outex_TC_00013-20260120T014101Z-3-001.zip"
    )
    parser.add_argument(
        "--output", type=Path, default=repo / "results/confirmatory/recovery/outex13/staging/official1360"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=repo / "results/extensions/outex13_official1360/sample_manifests/Outex13Official1360.csv",
    )
    args = parser.parse_args()
    print(json.dumps(prepare(args.archive.resolve(), args.output.resolve(), args.manifest.resolve()), indent=2))


if __name__ == "__main__":
    main()
