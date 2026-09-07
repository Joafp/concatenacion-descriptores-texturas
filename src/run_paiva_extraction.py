#!/usr/bin/env python3
"""
run_paiva_extraction.py
=======================
Genera embeddings para los 8 descriptores de Paiva faltantes sobre los 4 datasets
confirmatorios (DTD, FMD, CUReT, Outex13Official1360), usando los manifiestos
canónicos para garantizar orden y reproducibilidad.

Salida: embeddings_paiva/{dataset}/{extractor}.npy
        embeddings_paiva/{dataset}/{extractor}_labels.npy
        embeddings_paiva/{dataset}/{extractor}_classes.json
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
import paiva_extractors as pe

# Mapeo dataset -> manifest canónico (mismo usado para los 20 bloques)
MANIFESTS = {
    "DTD": REPO / "results/confirmatory/sample_manifests/DTD.csv",
    "FMD": REPO / "results/confirmatory/sample_manifests/FMD.csv",
    "CUReT": REPO / "results/confirmatory/sample_manifests/CUReT.csv",
    "Outex13Official1360": REPO / "results/extensions/outex13_official1360/sample_manifests/Outex13Official1360.csv",
}

OUTPUT_ROOT = REPO / "embeddings_paiva"


def read_manifest(manifest: Path):
    """Lee manifest y devuelve paths ordenados, labels y classes.

    Maneja dos formatos:
      - DTD: label es string (nombre de clase), path en source_path
      - Outex: label es int, path en path
    """
    with manifest.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    path_col = "source_path" if "source_path" in rows[0] else "path"
    rows_sorted = sorted(rows, key=lambda r: int(r["row_id"]))
    paths = [r[path_col] for r in rows_sorted]

    # labels: puede ser int string o nombre de clase
    first_label = rows_sorted[0]["label"]
    try:
        int(first_label)
        is_int_label = True
    except:
        is_int_label = False

    if is_int_label:
        labels = np.array([int(r["label"]) for r in rows_sorted], dtype=np.int64)
        class_col = "class_name" if "class_name" in rows_sorted[0] else "label"
        uniq = {}
        for r in rows_sorted:
            lbl = int(r["label"])
            cname = r.get("class_name", str(lbl))
            uniq[lbl] = cname
        classes = [uniq[i] for i in sorted(uniq)]
    else:
        # label es string -> mapear a índices
        all_labels = [r["label"] for r in rows_sorted]
        classes = sorted(set(all_labels))
        label_to_idx = {c: i for i, c in enumerate(classes)}
        labels = np.array([label_to_idx[r["label"]] for r in rows_sorted], dtype=np.int64)
    return paths, labels, classes


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=list(MANIFESTS.keys()),
                        choices=list(MANIFESTS.keys()))
    parser.add_argument("--extractors", nargs="+", default=list(pe.PAIVA_EXTRACTORS.keys()),
                        choices=list(pe.PAIVA_EXTRACTORS.keys()))
    parser.add_argument("--force", action="store_true", help="re-extract aunque ya exista")
    args = parser.parse_args()

    print(f"Datasets: {args.datasets}")
    print(f"Extractores: {args.extractors}")
    print(f"Output: {OUTPUT_ROOT}\n")

    for ds in args.datasets:
        manifest = MANIFESTS[ds]
        if not manifest.exists():
            print(f"  {ds}: manifest no existe {manifest} -> skip")
            continue
        print(f"\n=== {ds} (manifest {manifest.name}) ===")
        paths, labels, classes = read_manifest(manifest)
        print(f"  {len(paths)} imágenes, {len(classes)} clases")
        # verificar que al menos los primeros 3 paths existen
        missing = sum(1 for p in paths[:5] if not Path(p).exists())
        if missing:
            # probar con REPO como base si path es relativo
            paths_abs = []
            for p in paths:
                pp = Path(p)
                if not pp.is_absolute():
                    pp = REPO / p
                paths_abs.append(str(pp))
            paths = paths_abs

        for ext_name in args.extractors:
            out_dir = OUTPUT_ROOT / ds
            out_dir.mkdir(parents=True, exist_ok=True)
            out_npy = out_dir / f"{ext_name}.npy"
            out_labels = out_dir / f"{ext_name}_labels.npy"
            out_classes = out_dir / f"{ext_name}_classes.json"
            if out_npy.exists() and not args.force:
                print(f"  {ext_name}: ya existe {out_npy.stat().st_size/1e6:.1f}MB -> skip")
                continue
            cls, cfg = pe.PAIVA_EXTRACTORS[ext_name]
            extractor = cls(cfg)
            print(f"  -> extrayendo {ext_name} ({cfg}) ...")
            feats = extractor.extract(paths)
            print(f"     -> shape {feats.shape}, guardando")
            np.save(out_npy, feats)
            np.save(out_labels, labels)
            with open(out_classes, "w") as f:
                json.dump(classes, f)
            print(f"     ok {out_npy}")

    print("\nDone.")


if __name__ == "__main__":
    main()
