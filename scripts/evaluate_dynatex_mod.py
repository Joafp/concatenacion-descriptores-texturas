#!/usr/bin/env python3
"""
Evaluate DynaTex-MoD (Mixture of Descriptors) vs Linear SVM and ResMLP on FMD.
Demonstrates the performance and gating weight interpretability of the proposed model.
"""

from __future__ import annotations

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

from dynatex_mod_classifier import DynaTexMoDClassifier
from resmlp_classifier import ResMLPClassifier
from run_confirmatory_nested import FAMILIES, load_dataset, load_manifest


def main():
    dataset = "FMD"
    seed = 42
    print(f"=== Evaluando DynaTex-MoD vs Baselines en {dataset} ===")

    cache, y = load_dataset(REPO, dataset)
    manifest_dir = REPO / "results" / "confirmatory"
    groups, rows = load_manifest(manifest_dir, dataset, y)

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

    # Concatenar dentro de cada familia y armar el vector completo con slices
    X_parts = []
    family_slices = {}
    curr_dim = 0

    for fam in sorted(family_blocks.keys()):
        arr = np.concatenate(family_blocks[fam], axis=1)
        dim = arr.shape[1]
        family_slices[fam] = (curr_dim, curr_dim + dim)
        curr_dim += dim
        X_parts.append(arr)
        print(f"  Familia '{fam}': {len(family_blocks[fam])} extractores, {dim} dimensiones")

    X_full = np.concatenate(X_parts, axis=1)
    print(f"Dimensión total del vector concatenado: {X_full.shape[1]}")

    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)

    results = {
        "LinearSVM": {"f1": [], "acc": [], "fit_time": []},
        "ResMLP": {"f1": [], "acc": [], "fit_time": []},
        "DynaTex_MoD": {"f1": [], "acc": [], "fit_time": [], "gates": []},
    }

    for fold, (train_idx, test_idx) in enumerate(sgkf.split(X_full, y, groups)):
        print(f"\n--- Fold {fold} (Train: {len(train_idx)}, Test: {len(test_idx)}) ---")
        y_tr, y_te = y[train_idx], y[test_idx]

        # 1. Linear SVM
        t0 = time.time()
        svm = LinearSVC(C=1.0, random_state=seed, max_iter=2000)
        svm.fit(X_full[train_idx], y_tr)
        t_svm = time.time() - t0
        pred_svm = svm.predict(X_full[test_idx])
        f1_svm = f1_score(y_te, pred_svm, average="macro")
        acc_svm = accuracy_score(y_te, pred_svm)
        results["LinearSVM"]["f1"].append(f1_svm)
        results["LinearSVM"]["acc"].append(acc_svm)
        results["LinearSVM"]["fit_time"].append(t_svm)
        print(f"  Linear SVM:    Macro-F1={f1_svm:.4f}, Acc={acc_svm:.4f} ({t_svm:.2f}s)")

        # 2. ResMLP
        t0 = time.time()
        resmlp = ResMLPClassifier(hidden_dim=256, n_blocks=3, max_epochs=80, random_state=seed)
        resmlp.fit(X_full[train_idx], y_tr)
        t_resmlp = time.time() - t0
        pred_resmlp = resmlp.predict(X_full[test_idx])
        f1_resmlp = f1_score(y_te, pred_resmlp, average="macro")
        acc_resmlp = accuracy_score(y_te, pred_resmlp)
        results["ResMLP"]["f1"].append(f1_resmlp)
        results["ResMLP"]["acc"].append(acc_resmlp)
        results["ResMLP"]["fit_time"].append(t_resmlp)
        print(f"  ResMLP:        Macro-F1={f1_resmlp:.4f}, Acc={acc_resmlp:.4f} ({t_resmlp:.2f}s)")

        # 3. DynaTex-MoD
        t0 = time.time()
        mod = DynaTexMoDClassifier(
            family_slices=family_slices,
            proj_dim=128,
            hidden_dim=256,
            dropout=0.15,
            max_epochs=80,
            patience=12,
            random_state=seed,
        )
        mod.fit(X_full[train_idx], y_tr)
        t_mod = time.time() - t0
        pred_mod = mod.predict(X_full[test_idx])
        f1_mod = f1_score(y_te, pred_mod, average="macro")
        acc_mod = accuracy_score(y_te, pred_mod)
        results["DynaTex_MoD"]["f1"].append(f1_mod)
        results["DynaTex_MoD"]["acc"].append(acc_mod)
        results["DynaTex_MoD"]["fit_time"].append(t_mod)

        # Extraer pesos medios de las compuertas en el test set
        gates = mod.get_gating_weights(X_full[test_idx])
        mean_gates = {fam: float(np.mean(w)) for fam, w in gates.items()}
        results["DynaTex_MoD"]["gates"].append(mean_gates)
        gates_str = ", ".join(f"{k}: {v:.3f}" for k, v in mean_gates.items())
        print(f"  DynaTex-MoD:   Macro-F1={f1_mod:.4f}, Acc={acc_mod:.4f} ({t_mod:.2f}s)")
        print(f"    -> Pesos de compuerta test: {gates_str}")

    print("\n" + "=" * 60)
    print("RESUMEN PROMEDIO DE 5 FOLDS EN FMD:")
    print("=" * 60)
    for model_name in ["LinearSVM", "ResMLP", "DynaTex_MoD"]:
        mean_f1 = np.mean(results[model_name]["f1"])
        std_f1 = np.std(results[model_name]["f1"])
        mean_acc = np.mean(results[model_name]["acc"])
        std_acc = np.std(results[model_name]["acc"])
        print(f"{model_name:15s}: Macro-F1 = {mean_f1:.4f} ± {std_f1:.4f} | Acc = {mean_acc:.4f} ± {std_acc:.4f}")

    # Promedio de compuertas
    all_fams = sorted(results["DynaTex_MoD"]["gates"][0].keys())
    print("\nPESOS DE COMPUERTA PROMEDIO (DynaTex-MoD):")
    for fam in all_fams:
        avg_w = np.mean([g[fam] for g in results["DynaTex_MoD"]["gates"]])
        print(f"  Familia {fam:16s}: {avg_w*100:.1f}%")


if __name__ == "__main__":
    main()
