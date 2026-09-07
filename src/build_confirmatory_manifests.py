#!/usr/bin/env python3
"""Construye manifests deterministas desde fuentes primarias restauradas."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / "data" / "confirmatory_sources"
OUT = REPO / "results" / "confirmatory" / "sample_manifests"
BASE_FIELDS = ["row_id", "label", "group", "source_path", "source_sha256", "official_split"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(y) -> np.ndarray:
    mapping = {}
    return np.asarray([mapping.setdefault(str(v), len(mapping)) for v in y], dtype=np.int64)


def embedding_partition(dataset: str) -> tuple[np.ndarray, list[str]]:
    base = REPO / "embeddings" / dataset
    labels = np.load(base / "dinov2_labels.npy", allow_pickle=False)
    classes = json.loads((base / "dinov2_classes.json").read_text())
    return canonical(labels), classes


def write_manifest(name: str, rows: list[dict], extra_fields: list[str] | None = None) -> Path:
    path = OUT / f"{name}.csv"
    fields = BASE_FIELDS + (extra_fields or [])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    return path


def build_dtd() -> dict:
    root = SOURCES / "DTD" / "extracted" / "dtd"
    images = root / "images"
    paths = [p for cls in sorted(images.iterdir()) if cls.is_dir()
             for p in sorted(cls.iterdir()) if p.suffix.lower() == ".jpg"]
    split_maps = []
    for i in range(1, 11):
        mapping = {}
        for role in ("train", "val", "test"):
            for line in (root / "labels" / f"{role}{i}.txt").read_text().splitlines():
                mapping[line.strip()] = role
        if len(mapping) != 5640:
            raise ValueError(f"DTD split {i} covers {len(mapping)} rows")
        split_maps.append(mapping)
    rows = []
    for row_id, path in enumerate(paths):
        rel_image = path.relative_to(images).as_posix()
        splits = [m[rel_image] for m in split_maps]
        digest = sha256(path)
        row = {
            "row_id": row_id, "label": path.parent.name,
            "group": digest, "source_path": path.relative_to(REPO).as_posix(),
            "source_sha256": digest,
            "official_split": "|".join(f"{i + 1}:{role}" for i, role in enumerate(splits)),
        }
        row.update({f"split_{i + 1}": role for i, role in enumerate(splits)})
        rows.append(row)
    y, classes = embedding_partition("DTD")
    manifest_y = canonical([r["label"] for r in rows])
    linked = len(rows) == len(y) and np.array_equal(manifest_y, y) and sorted(set(r["label"] for r in rows)) == sorted(classes)
    write_manifest("DTD", rows, [f"split_{i}" for i in range(1, 11)])
    return {"dataset": "DTD", "rows": len(rows), "classes": len(set(r["label"] for r in rows)),
            "status": "LINKED_ORDER_LABEL_EXACT" if linked else "REEXTRACT_REQUIRED",
            "evidence": "original extractor: sorted class directories then sorted filenames; counts/classes/label partition match; 10 official splits retained"}


def build_fmd() -> dict:
    root = SOURCES / "FMD" / "extracted" / "image"
    paths = [p for cls in sorted(root.iterdir()) if cls.is_dir()
             for p in sorted(cls.iterdir()) if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    rows = []
    for row_id, path in enumerate(paths):
        digest = sha256(path)
        rows.append({"row_id": row_id, "label": path.parent.name, "group": digest,
                     "source_path": path.relative_to(REPO).as_posix(), "source_sha256": digest,
                     "official_split": "UNSPECIFIED_BY_PRIMARY_ARCHIVE"})
    y, classes = embedding_partition("FMD")
    linked = len(rows) == len(y) and np.array_equal(canonical([r["label"] for r in rows]), y) and sorted(set(r["label"] for r in rows)) == sorted(classes)
    write_manifest("FMD", rows)
    return {"dataset": "FMD", "rows": len(rows), "classes": len(set(r["label"] for r in rows)),
            "status": "LINKED_ORDER_LABEL_EXACT_NO_OFFICIAL_SPLIT" if linked else "REEXTRACT_REQUIRED",
            "evidence": ("original recursive extractor resolves sorted leaf directories then sorted filenames; "
                         + ("row label sequence matches" if linked else "counts/classes match but row label sequence does not match the flat official archive")
                         + "; archive supplies no splits")}


def build_vistex() -> dict:
    root = SOURCES / "VisTex" / "extracted" / "VisionTexture" / "VisTex" / "Images" / "Reference"
    paths = [p for cls in sorted(root.iterdir()) if cls.is_dir()
             for p in sorted(cls.iterdir()) if p.suffix.lower() == ".ppm"]
    rows = []
    for row_id, path in enumerate(paths):
        target = path.resolve(strict=True)
        digest = sha256(target)
        rows.append({"row_id": row_id, "label": path.parent.name, "group": digest,
                     "source_path": path.relative_to(REPO).as_posix(), "source_sha256": digest,
                     "official_split": "REEXTRACT_REQUIRED_NO_OFFICIAL_SPLIT"})
    write_manifest("VisTex_official", rows)
    y, classes = embedding_partition("VisTex")
    exact = len(rows) == len(y) and np.array_equal(canonical([r["label"] for r in rows]), y) and sorted(set(r["label"] for r in rows)) == sorted(classes)
    return {"dataset": "VisTex_official", "rows": len(rows), "classes": len(set(r["label"] for r in rows)),
            "status": "LINKED_ORDER_LABEL_EXACT" if exact else "REEXTRACT_REQUIRED",
            "evidence": f"official Reference hierarchy is 19 classes/167 rows; existing embedding metadata is {len(classes)} classes/{len(y)} rows and splits Paintings"}


def build_curet() -> dict:
    root = SOURCES / "CUReT" / "extracted" / "data"
    paths = []
    for sample in sorted(root.glob("sample*"), key=lambda p: int(p.name[6:])):
        number = int(sample.name[6:])
        pattern = re.compile(fr"{number:02d}-\d{{2}}-\d{{2}}\.bmp\.Z$")
        selected = sorted(p for p in sample.glob("*.bmp.Z") if pattern.fullmatch(p.name))
        if len(selected) != 205:
            raise ValueError(f"{sample.name}: expected 205 standard views, got {len(selected)}")
        paths.extend(selected)
    rows = []
    for row_id, path in enumerate(paths):
        digest = sha256(path)
        rows.append({"row_id": row_id, "label": path.parent.name, "group": digest,
                     "source_path": path.relative_to(REPO).as_posix(), "source_sha256": digest,
                     "official_split": "REEXTRACT_REQUIRED_SELECT_CROPPED_92_PROTOCOL"})
    write_manifest("CUReT_official_full", rows)
    y, classes = embedding_partition("CUReT")
    return {"dataset": "CUReT_official_full", "rows": len(rows), "classes": 61,
            "status": "REEXTRACT_REQUIRED",
            "evidence": f"primary distribution has 205 standard views/class; existing embeddings have {len(y) // len(classes)} rows/class; no local selection list or log proves those 100 views"}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    statuses = [build_dtd(), build_fmd(), build_vistex(), build_curet()]
    (OUT / "manifest_status.json").write_text(json.dumps({"schema_version": 1, "datasets": statuses}, indent=2))
    print(json.dumps(statuses, indent=2))


if __name__ == "__main__":
    main()
