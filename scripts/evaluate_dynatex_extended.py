#!/usr/bin/env python3
"""
Evaluate DynaTex-MoD on additional datasets available in the workspace:
1. VisTexReference12 (Auxiliary synthetic/natural benchmark)
2. HVD_glaucoma (Biomedical texture classification - 1,544 samples)
3. ocular_toxoplasmosis (Biomedical texture classification - 412 samples)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import LinearSVC

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dynatex_mod_classifier import DynaTexMoDClassifier
from resmlp_classifier import ResMLPClassifier
from run_confirmatory_nested import FAMILIES, canonical_labels, l2_rows


def load_dataset_direct(emb_dir: Path):
    cache = {}
    reference = None
    for p in sorted(emb_dir.glob("*.npy")):
        if p.name.endswith("_labels.npy"):
            continue
        lp = emb_dir / f"{p.stem}_labels.npy"
        if not lp.exists():
            continue
        y = canonical_labels(np.load(lp, allow_pickle=False))
        x = np.load(p)
        if x.ndim != 2 or len(x) != len(y) or not np.isfinite(x).all():
            continue
        if reference is None:
            reference = y
        cache[p.stem] = l2_rows(x)
    return cache, reference


def run_extended_dataset(name: str, emb_dir: Path, n_splits: int = 5, seed: int = 42, epochs: int = 60):
    print(f"\n==================================================")
    print(f"   EJECUTANDO DATASET EXTENDIDO: {name}")
    print(f"==================================================")
    cache, y = load_dataset_direct(emb_dir)
    print(f"Extractores cargados: {len(cache)} | Muestras: {len(y)} | Clases: {len(np.unique(y))}")

    family_blocks = {"classical": [], "cnn": [], "transformer": [], "self_supervised": []}
    for ext_name in sorted(cache.keys()):
        fam = FAMILIES.get(ext_name, "other")
        if fam in family_blocks:
            family_blocks[fam].append(cache[ext_name])

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
    print(f"Dimensión total: {X_full.shape[1]}")

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    results = {"svm": [], "resmlp": [], "mod": [], "gates": []}

    for fold, (tr, te) in enumerate(skf.split(X_full, y)):
        y_tr, y_te = y[tr], y[te]

        # SVM
        svm = LinearSVC(C=1.0, random_state=seed, max_iter=2500)
        svm.fit(X_full[tr], y_tr)
        pred_svm = svm.predict(X_full[te])
        f1_svm = f1_score(y_te, pred_svm, average="macro")

        # ResMLP
        resmlp = ResMLPClassifier(hidden_dim=256, n_blocks=3, max_epochs=epochs, random_state=seed)
        resmlp.fit(X_full[tr], y_tr)
        pred_resmlp = resmlp.predict(X_full[te])
        f1_resmlp = f1_score(y_te, pred_resmlp, average="macro")

        # DynaTex-MoD
        mod = DynaTexMoDClassifier(
            family_slices=family_slices,
            proj_dim=128,
            hidden_dim=256,
            dropout=0.15,
            max_epochs=epochs,
            patience=14,
            random_state=seed,
        )
        mod.fit(X_full[tr], y_tr)
        pred_mod = mod.predict(X_full[te])
        f1_mod = f1_score(y_te, pred_mod, average="macro")

        gates = mod.get_gating_weights(X_full[te])
        mean_gates = {fam: float(np.mean(w)) for fam, w in gates.items()}

        results["svm"].append(f1_svm)
        results["resmlp"].append(f1_resmlp)
        results["mod"].append(f1_mod)
        results["gates"].append(mean_gates)

        print(f"  Fold {fold}: SVM={f1_svm:.4f} | ResMLP={f1_resmlp:.4f} | DynaTex={f1_mod:.4f}")

    mean_svm = float(np.mean(results["svm"]))
    mean_resmlp = float(np.mean(results["resmlp"]))
    mean_mod = float(np.mean(results["mod"]))
    std_mod = float(np.std(results["mod"]))

    print(f"\nResumen {name}:")
    print(f"  Linear SVM : F1 = {mean_svm:.4f}")
    print(f"  ResMLP     : F1 = {mean_resmlp:.4f}")
    print(f"  DynaTex-MoD: F1 = {mean_mod:.4f} ± {std_mod:.4f}")

    all_fams = sorted(results["gates"][0].keys())
    avg_gates = {fam: float(np.mean([g[fam] for g in results["gates"]])) for fam in all_fams}
    print("  Compuertas promedio:")
    for fam, w in avg_gates.items():
        print(f"    {fam:16s}: {w*100:.1f}%")

    return {
        "svm": mean_svm,
        "resmlp": mean_resmlp,
        "mod": mean_mod,
        "mod_std": std_mod,
        "gates": avg_gates,
    }


def main():
    extended = {
        "VisTexReference12": REPO / "embeddings_extensions" / "VisTexReference12",
        "HVD_glaucoma": REPO / "embeddings" / "HVD_glaucoma",
        "ocular_toxoplasmosis": REPO / "embeddings" / "ocular_toxoplasmosis",
    }

    all_out = {}
    for name, p in extended.items():
        if p.is_dir():
            all_out[name] = run_extended_dataset(name, p)

    out_file = REPO / "results" / "dynatex_extended_datasets.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(all_out, f, indent=2)
    print(f"\nResultados extendidos guardados en {out_file}")


if __name__ == "__main__":
    main()
