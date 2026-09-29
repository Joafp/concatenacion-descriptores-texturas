#!/usr/bin/env python3
"""
Multi-dataset evaluation of DynaTex-MoD vs Linear SVM and ResMLP.
Generates comprehensive performance metrics and gating weight distributions per class.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.svm import LinearSVC

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from curet_confirmatory_protocol import curet_half_indices
from dynatex_mod_classifier import DynaTexMoDClassifier
from resmlp_classifier import ResMLPClassifier
from run_confirmatory_nested import (
    FAMILIES,
    load_dataset,
    load_manifest,
    official_split_indices,
)

DATASET_CONFIGS = {
    "FMD": {
        "manifest_dir": REPO / "results" / "confirmatory",
        "embedding_root": None,
        "type": "sgkf",
        "n_splits": 5,
        "exclude": (),
    },
    "DTD": {
        "manifest_dir": REPO / "results" / "confirmatory",
        "embedding_root": None,
        "type": "official",
        "splits": [1, 2, 3],  # representative splits for fast thorough testing
        "exclude": (),
    },
    "CUReT": {
        "manifest_dir": REPO / "results" / "confirmatory",
        "embedding_root": None,
        "type": "curet",
        "directions": ["a_to_b", "b_to_a"],
        "exclude": (),
    },
    "SoilOriginal": {
        "manifest_dir": REPO / "results" / "extensions" / "soil_original",
        "embedding_root": REPO / "embeddings_extensions",
        "type": "sgkf",
        "n_splits": 5,
        "exclude": (),
    },
    "KTHTIPS2b": {
        "manifest_dir": REPO / "results" / "extensions" / "kth_tips2b",
        "embedding_root": REPO / "embeddings_extensions",
        "type": "kth",
        "splits": [1, 2, 3, 4],
        "exclude": ("beitv2_base_multilayer",),
    },
    "Outex13Official1360": {
        "manifest_dir": REPO / "results" / "extensions" / "outex13_official1360",
        "embedding_root": REPO / "embeddings_extensions",
        "type": "official",
        "splits": [1],
        "exclude": (),
    },
}


def evaluate_split(
    X_full: np.ndarray,
    y: np.ndarray,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    family_slices: dict[str, tuple[int, int]],
    class_names: list[str] | None,
    seed: int = 42,
    epochs: int = 80,
) -> dict:
    y_tr, y_te = y[train_idx], y[test_idx]

    # 1. Linear SVM
    t0 = time.time()
    svm = LinearSVC(C=1.0, random_state=seed, max_iter=2500)
    svm.fit(X_full[train_idx], y_tr)
    t_svm = time.time() - t0
    pred_svm = svm.predict(X_full[test_idx])
    f1_svm = f1_score(y_te, pred_svm, average="macro")
    acc_svm = accuracy_score(y_te, pred_svm)

    # 2. ResMLP
    t0 = time.time()
    resmlp = ResMLPClassifier(hidden_dim=256, n_blocks=3, max_epochs=epochs, random_state=seed)
    resmlp.fit(X_full[train_idx], y_tr)
    t_resmlp = time.time() - t0
    pred_resmlp = resmlp.predict(X_full[test_idx])
    f1_resmlp = f1_score(y_te, pred_resmlp, average="macro")
    acc_resmlp = accuracy_score(y_te, pred_resmlp)

    # 3. DynaTex-MoD
    t0 = time.time()
    mod = DynaTexMoDClassifier(
        family_slices=family_slices,
        proj_dim=128,
        hidden_dim=256,
        dropout=0.15,
        max_epochs=epochs,
        patience=14,
        random_state=seed,
    )
    mod.fit(X_full[train_idx], y_tr)
    t_mod = time.time() - t0
    pred_mod = mod.predict(X_full[test_idx])
    f1_mod = f1_score(y_te, pred_mod, average="macro")
    acc_mod = accuracy_score(y_te, pred_mod)

    # Compuertas
    gates = mod.get_gating_weights(X_full[test_idx])
    mean_gates = {fam: float(np.mean(w)) for fam, w in gates.items()}

    # Compuertas por clase
    class_gates = {}
    unique_classes = np.unique(y_te)
    for c in unique_classes:
        c_mask = y_te == c
        c_label = class_names[c] if class_names and c < len(class_names) else str(c)
        class_gates[c_label] = {fam: float(np.mean(gates[fam][c_mask])) for fam in gates}

    return {
        "svm": {"f1": float(f1_svm), "acc": float(acc_svm), "time": float(t_svm)},
        "resmlp": {"f1": float(f1_resmlp), "acc": float(acc_resmlp), "time": float(t_resmlp)},
        "mod": {"f1": float(f1_mod), "acc": float(acc_mod), "time": float(t_mod)},
        "mean_gates": mean_gates,
        "class_gates": class_gates,
    }


def run_dataset(dataset_name: str, seed: int = 42, epochs: int = 80) -> dict:
    print(f"\n==================================================")
    print(f"   EJECUTANDO DATASET: {dataset_name}")
    print(f"==================================================")
    cfg = DATASET_CONFIGS[dataset_name]
    cache, y = load_dataset(REPO, dataset_name, embedding_root=cfg["embedding_root"])
    for name in cfg["exclude"]:
        cache.pop(name, None)

    groups, rows = load_manifest(cfg["manifest_dir"], dataset_name, y)

    # Extraer nombres de clase si existen en el manifiesto
    class_names = None
    if rows and ("class_name" in rows[0] or "label_name" in rows[0]):
        col = "class_name" if "class_name" in rows[0] else "label_name"
        mapping = {}
        for r, label_idx in zip(rows, y):
            mapping[int(label_idx)] = r[col]
        class_names = [mapping[i] for i in range(len(mapping))]

    # Organizar extractores por familia representacional
    family_blocks: dict[str, list[np.ndarray]] = {
        "classical": [],
        "cnn": [],
        "transformer": [],
        "self_supervised": [],
    }
    for name in sorted(cache.keys()):
        fam = FAMILIES.get(name, "other")
        if fam in family_blocks:
            family_blocks[fam].append(cache[name])

    X_parts = []
    family_slices = {}
    curr_dim = 0
    for fam in sorted(family_blocks.keys()):
        if not family_blocks[fam]:
            continue
        arr = np.concatenate(family_blocks[fam], axis=1)
        dim = arr.shape[1]
        family_slices[fam] = (curr_dim, curr_dim + dim)
        curr_dim += dim
        X_parts.append(arr)
        print(f"  Familia '{fam}': {len(family_blocks[fam])} extractores, {dim} dims")

    X_full = np.concatenate(X_parts, axis=1)
    print(f"Dimensión total del vector: {X_full.shape[1]} | Clases: {len(np.unique(y))}")

    split_results = []

    if cfg["type"] == "sgkf":
        sgkf = StratifiedGroupKFold(n_splits=cfg["n_splits"], shuffle=True, random_state=seed)
        for fold, (tr, te) in enumerate(sgkf.split(X_full, y, groups)):
            print(f"  Fold {fold}...", end=" ", flush=True)
            res = evaluate_split(X_full, y, tr, te, family_slices, class_names, seed, epochs)
            split_results.append(res)
            print(f"SVM={res['svm']['f1']:.4f} | ResMLP={res['resmlp']['f1']:.4f} | DynaTex={res['mod']['f1']:.4f}")

    elif cfg["type"] == "official":
        for s in cfg["splits"]:
            tr, te = official_split_indices(rows, s)
            print(f"  Split oficial {s}...", end=" ", flush=True)
            res = evaluate_split(X_full, y, tr, te, family_slices, class_names, seed, epochs)
            split_results.append(res)
            print(f"SVM={res['svm']['f1']:.4f} | ResMLP={res['resmlp']['f1']:.4f} | DynaTex={res['mod']['f1']:.4f}")

    elif cfg["type"] == "curet":
        for direction in cfg["directions"]:
            tr, te = curet_half_indices(rows, direction)
            print(f"  Dirección {direction}...", end=" ", flush=True)
            res = evaluate_split(X_full, y, tr, te, family_slices, class_names, seed, epochs)
            split_results.append(res)
            print(f"SVM={res['svm']['f1']:.4f} | ResMLP={res['resmlp']['f1']:.4f} | DynaTex={res['mod']['f1']:.4f}")

    elif cfg["type"] == "kth":
        for s in cfg["splits"]:
            tr, te = official_split_indices(rows, s)
            # RADAM inverts the official split so that 3 samples train and 1 tests
            tr, te = te, tr
            print(f"  Partición RADAM {s}...", end=" ", flush=True)
            res = evaluate_split(X_full, y, tr, te, family_slices, class_names, seed, epochs)
            split_results.append(res)
            print(f"SVM={res['svm']['f1']:.4f} | ResMLP={res['resmlp']['f1']:.4f} | DynaTex={res['mod']['f1']:.4f}")

    # Agregación
    agg = {
        "svm_f1": float(np.mean([r["svm"]["f1"] for r in split_results])),
        "svm_acc": float(np.mean([r["svm"]["acc"] for r in split_results])),
        "resmlp_f1": float(np.mean([r["resmlp"]["f1"] for r in split_results])),
        "resmlp_acc": float(np.mean([r["resmlp"]["acc"] for r in split_results])),
        "mod_f1": float(np.mean([r["mod"]["f1"] for r in split_results])),
        "mod_acc": float(np.mean([r["mod"]["acc"] for r in split_results])),
        "mod_f1_std": float(np.std([r["mod"]["f1"] for r in split_results])),
    }

    print(f"\nResumen {dataset_name}:")
    print(f"  Linear SVM : F1={agg['svm_f1']:.4f}, Acc={agg['svm_acc']:.4f}")
    print(f"  ResMLP     : F1={agg['resmlp_f1']:.4f}, Acc={agg['resmlp_acc']:.4f}")
    print(f"  DynaTex-MoD: F1={agg['mod_f1']:.4f} ± {agg['mod_f1_std']:.4f}, Acc={agg['mod_acc']:.4f}")

    # Promedio compuertas
    all_fams = sorted(split_results[0]["mean_gates"].keys())
    agg["mean_gates"] = {fam: float(np.mean([r["mean_gates"][fam] for r in split_results])) for fam in all_fams}
    print("  Compuertas promedio:")
    for fam, w in agg["mean_gates"].items():
        print(f"    {fam:16s}: {w*100:.1f}%")

    return {
        "dataset": dataset_name,
        "summary": agg,
        "splits": split_results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["FMD", "SoilOriginal", "DTD", "CUReT", "KTHTIPS2b"])
    parser.add_argument("--epochs", type=int, default=70)
    parser.add_argument("--output", type=Path, default=REPO / "results" / "dynatex_multidataset.json")
    args = parser.parse_args()

    all_results = {}
    for ds in args.datasets:
        if ds not in DATASET_CONFIGS:
            print(f"Dataset desconocido: {ds}")
            continue
        res = run_dataset(ds, epochs=args.epochs)
        all_results[ds] = res

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResultados guardados en {args.output}")


if __name__ == "__main__":
    main()
