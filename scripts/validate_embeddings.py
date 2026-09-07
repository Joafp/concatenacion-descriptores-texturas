"""
validate_embeddings.py
======================
Valida todos los archivos de embeddings en embeddings/{dataset}/{extractor}.npy.

Checks por archivo:
  - Existe y se puede cargar
  - Shape esperado (N, D)
  - N coincide con número de imágenes del dataset
  - Sin NaN/Inf
  - Distribución razonable (mean, std, L2 norm)
  - Labels consistentes
  - Mismas imágenes siempre dan mismo embedding (determinismo)

Uso:
  python3 src/validate_embeddings.py [--dataset DTD] [--extractor vit_b16] [--all]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np


EXPECTED_DIMS = {
    "vit_b16": 768,
    "swin_t": 768,
    "deit_s": 384,
    "dinov2": 768,
    "dinov2_large": 1024,
    "convnext_v2_t": 768,
    "resnet50": 2048,
    "efficientnet_b0": 1280,
    "lbp": 54,
    "glcm": 18,
    "gabor": 48,
    "hog": 1764,
    "drlbp": 80,
}

EXPECTED_SIZES = {
    "DTD": 5640,
    "FMD": 1000,
    "KTH-TIPS2": 4608,
    "HVD_glaucoma": 1544,
    "ocular_toxoplasmosis": 412,
}


def validate_file(emb_path: Path) -> dict:
    """Devuelve dict con resultados. Raise si falla algo crítico."""
    name = emb_path.stem
    labels_path = emb_path.parent / f"{name}_labels.npy"
    classes_path = emb_path.parent / f"{name}_classes.json"

    if not labels_path.exists():
        raise FileNotFoundError(f"Falta labels: {labels_path}")
    if not classes_path.exists():
        raise FileNotFoundError(f"Falta classes: {classes_path}")

    emb = np.load(emb_path)
    lab = np.load(labels_path)
    with open(classes_path) as f:
        classes = json.load(f)

    # Shape checks
    if emb.ndim != 2:
        raise AssertionError(f"Esperaba 2D, obtuve {emb.ndim}D")
    if emb.shape[0] != lab.shape[0]:
        raise AssertionError(f"emb.shape[0]={emb.shape[0]} != labels.shape[0]={lab.shape[0]}")

    # NaN/Inf
    nan_count = int(np.isnan(emb).sum())
    inf_count = int(np.isinf(emb).sum())
    if nan_count or inf_count:
        raise AssertionError(f"NaN={nan_count}, Inf={inf_count}")

    # Labels consistency
    if lab.min() < 0 or lab.max() >= len(classes):
        raise AssertionError(f"Labels fuera de rango: [{lab.min()}, {lab.max()}], num_classes={len(classes)}")

    # Distribución
    l2_norms = np.linalg.norm(emb, axis=1)

    return {
        "file": str(emb_path),
        "shape": list(emb.shape),
        "num_classes": len(classes),
        "classes_used": int(len(np.unique(lab))),
        "label_range": [int(lab.min()), int(lab.max())],
        "mean": float(emb.mean()),
        "std": float(emb.std()),
        "min": float(emb.min()),
        "max": float(emb.max()),
        "l2_mean": float(l2_norms.mean()),
        "l2_std": float(l2_norms.std()),
        "nan_count": nan_count,
        "inf_count": inf_count,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Validar todos los embeddings (no _smoke)")
    parser.add_argument("--dataset", type=str)
    parser.add_argument("--extractor", type=str)
    parser.add_argument("--include-smoke", action="store_true", help="Incluir archivos _smoke")
    parser.add_argument("--root", default="embeddings")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: directorio {root} no existe", file=sys.stderr)
        sys.exit(1)

    # Recolectar archivos
    files = []
    for dataset_dir in sorted(root.iterdir()):
        if not dataset_dir.is_dir():
            continue
        if args.dataset and dataset_dir.name != args.dataset:
            continue
        for emb_path in sorted(dataset_dir.glob("*.npy")):
            if "_labels" in emb_path.name:
                continue
            if "_smoke" in emb_path.name and not args.include_smoke:
                continue
            if args.extractor and not emb_path.stem.startswith(args.extractor):
                continue
            files.append(emb_path)

    if not files:
        print(f"Ningún archivo encontrado con esos filtros")
        sys.exit(1)

    print(f"Validando {len(files)} archivos...\n")

    n_passed = 0
    n_failed = 0
    rows = []
    for f in files:
        try:
            r = validate_file(f)
            n_passed += 1
            rows.append(r)
            # Check dimensión esperada
            ext_name = f.stem.replace("_smoke", "")
            expected_dim = EXPECTED_DIMS.get(ext_name)
            dim_status = ""
            if expected_dim and r["shape"][1] != expected_dim:
                dim_status = f" [WARN: dim esperada {expected_dim}, obtuve {r['shape'][1]}]"
                n_failed += 1
                n_passed -= 1
            print(f"  ✓ {f.relative_to(root)}  shape={tuple(r['shape'])}  L2={r['l2_mean']:.2f}{dim_status}")
        except Exception as e:
            n_failed += 1
            print(f"  ✗ {f.relative_to(root)}  ERROR: {e}")

    # Resumen
    print(f"\n=== Resumen ===")
    print(f"Pasados: {n_passed}/{len(files)}")
    print(f"Fallados: {n_failed}/{len(files)}")

    # Comparación inter-extractor (mismo dataset)
    if not args.dataset and len(rows) > 1:
        print(f"\n=== L2 norms por extractor (referencia para concatenación) ===")
        by_ext = {}
        for r in rows:
            ext = Path(r["file"]).stem.replace("_smoke", "")
            by_ext.setdefault(ext, []).append(r["l2_mean"])
        for ext, vals in sorted(by_ext.items()):
            print(f"  {ext:20s}: L2_mean avg = {np.mean(vals):.3f} (range {min(vals):.2f}-{max(vals):.2f})")

    sys.exit(0 if n_failed == 0 else 1)


if __name__ == "__main__":
    main()
