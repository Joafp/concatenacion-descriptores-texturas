#!/usr/bin/env python3
"""
Optimization of DynaTex-MoD for SoilOriginal:
Identifies why Soil had lower performance and tests architectural improvements:
1. Regularization tuning (lr, weight decay, batch size for 912 train samples)
2. Projection dimension (128 vs 256)
3. Noise filtering (what happens if the noisy classical family [F1=0.11-0.29] is filtered or weighted by sparse gate)
4. Cosine Annealing learning rate schedule
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.svm import LinearSVC

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dynatex_mod_classifier import DynaTexMoDClassifier
from resmlp_classifier import ResMLPClassifier
from run_confirmatory_nested import FAMILIES, load_dataset, load_manifest


def evaluate_config(name: str, family_blocks: dict[str, list[np.ndarray]], y: np.ndarray, groups: np.ndarray,
                    proj_dim: int = 128, lr: float = 1e-3, wd: float = 1e-4, bs: int = 128, epochs: int = 80,
                    dropout: float = 0.15, seed: int = 42):
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

    X_full = np.concatenate(X_parts, axis=1)
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)

    f1s, accs = [], []
    for fold, (tr, te) in enumerate(sgkf.split(X_full, y, groups)):
        mod = DynaTexMoDClassifier(
            family_slices=family_slices,
            proj_dim=proj_dim,
            hidden_dim=256,
            dropout=dropout,
            lr=lr,
            weight_decay=wd,
            batch_size=bs,
            max_epochs=epochs,
            patience=16,
            random_state=seed,
        )
        mod.fit(X_full[tr], y[tr])
        preds = mod.predict(X_full[te])
        f1 = f1_score(y[te], preds, average="macro")
        acc = accuracy_score(y[te], preds)
        f1s.append(f1)
        accs.append(acc)

    mean_f1, std_f1 = np.mean(f1s), np.std(f1s)
    mean_acc, std_acc = np.mean(accs), np.std(accs)
    print(f"{name:45s}: Macro-F1 = {mean_f1:.4f} ± {std_f1:.4f} | Acc = {mean_acc:.4f} ± {std_acc:.4f}")
    return mean_f1, mean_acc


def main():
    print("=== Optimización de DynaTex-MoD en SoilOriginal ===")
    cache, y = load_dataset(REPO, "SoilOriginal", embedding_root=REPO / "embeddings_extensions")
    groups, rows = load_manifest(REPO / "results/extensions/soil_original", "SoilOriginal", y)

    # 1. Baseline Linear SVM de referencia
    all_X = np.concatenate([cache[k] for k in sorted(cache.keys())], axis=1)
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    svm_f1s = []
    for tr, te in sgkf.split(all_X, y, groups):
        clf = LinearSVC(C=1.0, random_state=42, max_iter=2500)
        clf.fit(all_X[tr], y[tr])
        svm_f1s.append(f1_score(y[te], clf.predict(all_X[te]), average="macro"))
    print(f"{'Baseline Linear SVM':45s}: Macro-F1 = {np.mean(svm_f1s):.4f} ± {np.std(svm_f1s):.4f}")

    # Organizar familias completas (4 familias)
    all_fams = {"classical": [], "cnn": [], "transformer": [], "self_supervised": []}
    for name in sorted(cache.keys()):
        fam = FAMILIES.get(name, "other")
        if fam in all_fams:
            all_fams[fam].append(cache[name])

    # Organizar familias sin ruido clásico (3 familias profundas)
    deep_fams = {"cnn": all_fams["cnn"], "transformer": all_fams["transformer"], "self_supervised": all_fams["self_supervised"]}

    print("\n--- Evaluando Configuraciones de Arquitectura e Hiperparámetros ---")
    # Config 0: Default original
    evaluate_config("0. DynaTex Default (original)", all_fams, y, groups, proj_dim=128, lr=1e-3, wd=1e-4, bs=128, epochs=60)

    # Config 1: Menor batch size (64) y mayor regularización wd=1e-3 (óptimo para 900 muestras)
    evaluate_config("1. Regularized (bs=64, wd=1e-3, lr=5e-4)", all_fams, y, groups, proj_dim=128, lr=5e-4, wd=1e-3, bs=64, epochs=80)

    # Config 2: Mayor capacidad de proyección (proj_dim=256) + regularización
    evaluate_config("2. Proj=256 + Regularized (bs=64, wd=1e-3)", all_fams, y, groups, proj_dim=256, lr=5e-4, wd=1e-3, bs=64, epochs=80)

    # Config 3: Exclusión de la familia clásica ruidosa (CNN + Trans + SSL)
    evaluate_config("3. Solo Familias Profundas (CNN+Trans+SSL)", deep_fams, y, groups, proj_dim=128, lr=1e-3, wd=1e-4, bs=128, epochs=60)

    # Config 4: Familias Profundas + Regularized (bs=64, wd=1e-3, lr=5e-4)
    evaluate_config("4. Profundas + Regularized (bs=64, wd=1e-3)", deep_fams, y, groups, proj_dim=128, lr=5e-4, wd=1e-3, bs=64, epochs=80)

    # Config 5: Profundas + Proj=256 + Regularized
    evaluate_config("5. Profundas + Proj=256 (bs=64, wd=1e-3)", deep_fams, y, groups, proj_dim=256, lr=5e-4, wd=1e-3, bs=64, epochs=80)


if __name__ == "__main__":
    main()
