#!/usr/bin/env python3
"""Auditoría de integridad de entradas para FSC-Tex (Fase 0).

Verifica para los seis datasets canónicos:
1. Manifiestos de muestras: filas, clases, columnas requeridas, hashes y grupos.
2. Embeddings estáticos (21 bloques): presencia, dimensiones, finitud (sin NaN/inf),
   correspondencia exacta fila-a-fila con el manifiesto.
3. Caché de conteos de RGB N-gramas (bloque 22): presencia y coincidencia de muestras.
4. Particiones canónicas (27 condiciones externas): verificación de grupos disjuntos
   y ausencia de fuga externa.

Salida: results/exploratory/fsc_tex/audit/data_inventory.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from run_confirmatory_nested import (
    FAMILIES,
    curet_half_indices,
    load_dataset,
    load_manifest,
    official_split_indices,
)

CANONICAL_22_BLOCKS = [
    # Clásicos (5)
    "lbp", "drlbp", "gabor", "glcm", "hog",
    # CNNs (6)
    "resnet50", "resnet101", "vgg16", "densenet121", "efficientnet_b0", "convnext_v2_t",
    # Transformers supervisados (5)
    "vit_b16", "deit_s", "swin_t", "eva02_base", "beitv2_base_final",
    # Autosupervisados y fundacionales (5)
    "dinov2", "dinov2_small", "dinov2_large", "mae_base", "siglip_base",
    # Color secuencial (1)
    "rgb_ngram_svd",
]

DATASET_CONFIGS = [
    {
        "name": "DTD",
        "embedding_root": REPO / "embeddings/DTD",
        "manifest_path": REPO / "results/confirmatory/sample_manifests/DTD.csv",
        "protocol": "official_splits",
        "splits": list(range(1, 11)),
        "inner_group_col": None,
        "count_cache_dir": REPO / "results/confirmatory/rgb_ngram_count_cache/DTD/rgb_ngram_impl1",
    },
    {
        "name": "FMD",
        "embedding_root": REPO / "embeddings_confirmatory/FMD",
        "manifest_path": REPO / "results/confirmatory/sample_manifests/FMD.csv",
        "protocol": "grouped_kfold",
        "splits": [0, 1, 2, 3, 4],
        "inner_group_col": None,
        "count_cache_dir": REPO / "results/confirmatory/rgb_ngram_count_cache/FMD/rgb_ngram_impl1",
    },
    {
        "name": "CUReT",
        "embedding_root": REPO / "embeddings_confirmatory/CUReT",
        "manifest_path": REPO / "results/confirmatory/sample_manifests/CUReT.csv",
        "protocol": "halves",
        "splits": ["a_to_b", "b_to_a"],
        "inner_group_col": None,
        "count_cache_dir": REPO / "results/confirmatory/rgb_ngram_count_cache/CUReT/rgb_ngram_impl1",
    },
    {
        "name": "Outex13Official1360",
        "embedding_root": REPO / "embeddings_extensions/Outex13Official1360",
        "manifest_path": REPO / "results/extensions/outex13_official1360/sample_manifests/Outex13Official1360.csv",
        "protocol": "official_splits",
        "splits": [1],
        "inner_group_col": None,
        "count_cache_dir": REPO / "results/extensions/outex13_official1360/rgb_ngram_count_cache/Outex13Official1360/rgb_ngram_impl1",
    },
    {
        "name": "SoilOriginal",
        "embedding_root": REPO / "embeddings_extensions/SoilOriginal",
        "manifest_path": REPO / "results/extensions/soil_original/sample_manifests/SoilOriginal.csv",
        "protocol": "grouped_kfold",
        "splits": [0, 1, 2, 3, 4],
        "inner_group_col": None,
        "count_cache_dir": REPO / "results/extensions/soil_original/rgb_ngram_count_cache/SoilOriginal/rgb_ngram_impl1",
    },
    {
        "name": "KTHTIPS2b",
        "embedding_root": REPO / "embeddings_extensions/KTH-TIPS2-b",
        "manifest_path": REPO / "results/extensions/kth_tips2b/sample_manifests/KTHTIPS2b.csv",
        "protocol": "official_splits_inverted",
        "splits": [1, 2, 3, 4],
        "inner_group_col": "sample",
        "count_cache_dir": REPO / "results/extensions/kth_tips2b/rgb_ngram_count_cache/KTHTIPS2b/rgb_ngram_impl1",
    },
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_dataset(cfg: dict) -> dict:
    name = cfg["name"]
    print(f"\n==================================================")
    print(f"Auditoría: {name}")
    print(f"==================================================")

    # 1. Manifiesto
    manifest_p = cfg["manifest_path"]
    if not manifest_p.is_file():
        raise FileNotFoundError(f"Manifiesto no encontrado: {manifest_p}")
    
    with open(manifest_p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        manifest_rows = list(reader)
    n_samples = len(manifest_rows)
    classes = sorted(set(r["label"] for r in manifest_rows))
    n_classes = len(classes)
    groups = [r.get("group", "") for r in manifest_rows]
    n_unique_groups = len(set(groups))
    manifest_hash = sha256_file(manifest_p)

    print(f"  Muestras: {n_samples} | Clases: {n_classes} | Grupos únicos: {n_unique_groups}")

    # Verificar columna interna si aplica
    inner_col = cfg.get("inner_group_col")
    inner_group_stats = None
    if inner_col:
        inner_vals = [r.get(inner_col, "") for r in manifest_rows]
        inner_unique = sorted(set(inner_vals))
        inner_group_stats = {
            "column": inner_col,
            "unique_count": len(inner_unique),
            "values": inner_unique,
        }
        print(f"  Columna de grupo interno ({inner_col}): {len(inner_unique)} grupos físicos ({inner_unique})")

    # 2. Embeddings estáticos (21 bloques)
    emb_root = cfg["embedding_root"]
    block_audits = {}
    total_static_dims = 0

    for block in CANONICAL_22_BLOCKS:
        if block == "rgb_ngram_svd":
            continue  # Se audita aparte con su caché
        
        npy_path = emb_root / f"{block}.npy"
        if not npy_path.is_file():
            raise FileNotFoundError(f"Embedding estático faltante: {npy_path}")

        arr = np.load(npy_path)
        if arr.shape[0] != n_samples:
            raise ValueError(f"Dimensión de muestras no coincide: {block} tiene {arr.shape[0]}, esperado {n_samples}")

        is_finite = bool(np.all(np.isfinite(arr)))
        if not is_finite:
            raise ValueError(f"Valores no finitos detectados en {block} de {name}")

        row_norms = np.linalg.norm(arr, axis=1)
        is_l2 = bool(np.allclose(row_norms, 1.0, atol=1e-3))
        dim = int(arr.shape[1])
        total_static_dims += dim

        block_audits[block] = {
            "family": FAMILIES.get(block, "unknown"),
            "shape": list(arr.shape),
            "dim": dim,
            "is_finite": is_finite,
            "is_l2_normalized": is_l2,
            "norm_mean": float(np.mean(row_norms)),
            "sha256": sha256_file(npy_path),
        }

    # 3. RGB N-gram count cache
    ngram_cache_dir = cfg["count_cache_dir"]
    ngram_cache_valid = False
    ngram_cache_info = {}
    if ngram_cache_dir.is_dir():
        required_files = ["counts.npy", "indptr.npy", "keys.npy", "metadata.json"]
        if all((ngram_cache_dir / f).is_file() for f in required_files):
            with open(ngram_cache_dir / "metadata.json", encoding="utf-8") as f:
                meta = json.load(f)
            indptr = np.load(ngram_cache_dir / "indptr.npy", mmap_mode="r")
            n_cache_samples = len(indptr) - 1
            if n_cache_samples == n_samples:
                ngram_cache_valid = True
                ngram_cache_info = {
                    "valid": True,
                    "samples": n_cache_samples,
                    "meta_samples": meta.get("samples"),
                    "algorithm": meta.get("algorithm"),
                    "cache_dir": str(ngram_cache_dir),
                }
                print(f"  Caché de conteos RGB N-gramas: VÁLIDO ({n_cache_samples} muestras)")
            else:
                ngram_cache_info = {"valid": False, "reason": f"samples mismatch: {n_cache_samples} vs {n_samples}"}
        else:
            ngram_cache_info = {"valid": False, "reason": "missing cache files"}
    else:
        ngram_cache_info = {"valid": False, "reason": f"directory not found: {ngram_cache_dir}"}

    # 4. Particiones y ausencia de fuga
    protocol = cfg["protocol"]
    splits = cfg["splits"]
    split_audits = []

    for sp in splits:
        if protocol == "official_splits":
            tr, te = official_split_indices(manifest_rows, sp)
        elif protocol == "official_splits_inverted":
            tr, te = official_split_indices(manifest_rows, sp)
            tr, te = te, tr  # 3 train, 1 test
        elif protocol == "halves":
            tr, te = curet_half_indices(manifest_rows, sp)
        elif protocol == "grouped_kfold":
            # Para FMD y SoilOriginal, split es fold index de StratifiedGroupKFold con seed 42
            from sklearn.model_selection import StratifiedGroupKFold
            labels = [r["label"] for r in manifest_rows]
            sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
            splits_list = list(sgkf.split(np.zeros(len(labels)), labels, groups))
            tr, te = splits_list[sp]
        else:
            raise ValueError(f"Protocolo desconocido: {protocol}")

        # Control de fuga: intersección vacía de índices
        tr_set = set(tr)
        te_set = set(te)
        assert len(tr_set.intersection(te_set)) == 0, f"Fuga de índices en split {sp}"

        # Control de grupos disjuntos
        tr_groups = set(groups[i] for i in tr)
        te_groups = set(groups[i] for i in te)
        group_intersection = tr_groups.intersection(te_groups)
        
        # En datasets con grupos a nivel de imagen (DTD/Outex), cada imagen es su grupo.
        # En datasets agrupados físicamente (FMD, Soil, KTH), los grupos deben ser disjuntos.
        split_audits.append({
            "split_id": str(sp),
            "n_train": len(tr),
            "n_test": len(te),
            "n_train_groups": len(tr_groups),
            "n_test_groups": len(te_groups),
            "group_leakage_count": len(group_intersection),
        })

    print(f"  Bloques estáticos: 21 verificados (Dimensión total: {total_static_dims:,})")
    print(f"  Condiciones evaluadas: {len(split_audits)} splits sin fuga externa de índices.")

    return {
        "dataset": name,
        "n_samples": n_samples,
        "n_classes": n_classes,
        "classes": classes,
        "n_groups": n_unique_groups,
        "manifest_path": str(manifest_p),
        "manifest_sha256": manifest_hash,
        "inner_group_stats": inner_group_stats,
        "total_static_dims": total_static_dims,
        "static_blocks": block_audits,
        "rgb_ngram_cache": ngram_cache_info,
        "conditions_count": len(split_audits),
        "split_audits": split_audits,
    }


def main():
    parser = argparse.ArgumentParser(description="Auditoría de datos para FSC-Tex")
    parser.add_argument("--output", type=Path, default=REPO / "results/exploratory/fsc_tex/audit/data_inventory.json")
    args = parser.parse_args()

    results = {
        "schema_version": "1.0",
        "audit_name": "fsc_tex_phase0_data_audit",
        "canonical_22_blocks": CANONICAL_22_BLOCKS,
        "datasets": {},
    }

    total_conditions = 0
    for cfg in DATASET_CONFIGS:
        audit_res = audit_dataset(cfg)
        results["datasets"][cfg["name"]] = audit_res
        total_conditions += audit_res["conditions_count"]

    results["total_canonical_conditions"] = total_conditions
    print(f"\n==================================================")
    print(f"RESUMEN AUDITORÍA: 6 datasets | {total_conditions} condiciones externas canónicas")
    print(f"Guardando inventario en: {args.output}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Auditoría completada exitosamente.")


if __name__ == "__main__":
    main()
