"""
05_greedy_subset_search.py
==========================
Búsqueda greedy forward de subconjuntos óptimos de extractores.

Algoritmo: Greedy Forward Selection (GFS)
  - Empezar con subset vacío
  - En cada paso, evaluar todos los candidatos (agregar 1 extractor a los ya seleccionados)
  - Quedarse con el candidato que más mejora macro-F1
  - Repetir hasta que no haya mejora o se llegue al máximo

Evalúa con 5-fold stratified CV (igual que baseline y concat).
Para cada (dataset, clf), corre un GFS independiente.

Outputs:
  results/tables/greedy_{dataset}.csv  (path incremental por clf)
  results/tables/greedy_summary.csv
  results/figures/greedy_path_{dataset}.png  (curva F1 vs # extractores)
  results/tables/greedy_vs_prefix.csv  (comparación)
"""

import argparse
import json
import time
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

sys.path.insert(0, str(Path(__file__).parent))
from resmlp_classifier import ResMLPClassifier

warnings.filterwarnings("ignore")


# ---------------- Configuración ----------------

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]
ALL_EXTRACTORS = [
    "vit_b16", "swin_t", "deit_s",
    "dinov2_small", "dinov2", "dinov2_large",
    "vgg16", "resnet50", "resnet101", "densenet121",
    "efficientnet_b0", "convnext_v2_t",
    "lbp", "glcm", "gabor", "hog", "drlbp",
]

# Hiperparámetros fijos (SVM linear es el ganador del Cap. 5.11.6)
CLF_PARAMS = {
    "svm":    {"kernel": "linear", "C": 1.0},
    "knn":    {"n_neighbors": 5, "weights": "distance"},
    "rf":     {"n_estimators": 300, "max_depth": None},
    "mlp":    {"hidden_layer_sizes": (256,), "max_iter": 100, "alpha": 1e-3, "early_stopping": True},
    "resmlp": {"hidden_dim": 256, "n_blocks": 3, "dropout": 0.1, "max_epochs": 100, "patience": 10, "batch_size": 256},
}

CV_SPLITS = 5
CV_SEED = 42


def load_embeddings(dataset: str, extractor: str) -> tuple[np.ndarray, np.ndarray]:
    base = EMBEDDINGS_ROOT / dataset
    emb = np.load(base / f"{extractor}.npy")
    labels = np.load(base / f"{extractor}_labels.npy")
    return emb, labels


def normalize_l2(X: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def make_clf(name: str):
    if name == "svm":
        return SVC(**CLF_PARAMS["svm"])
    if name == "knn":
        return KNeighborsClassifier(**CLF_PARAMS["knn"])
    if name == "rf":
        return RandomForestClassifier(random_state=CV_SEED, n_jobs=-1, **CLF_PARAMS["rf"])
    if name == "mlp":
        return MLPClassifier(random_state=CV_SEED, **CLF_PARAMS["mlp"])
    if name == "resmlp":
        return ResMLPClassifier(random_state=CV_SEED, **CLF_PARAMS["resmlp"])
    raise ValueError(name)


def evaluate_subset(emb_arrays: list[np.ndarray], labels: np.ndarray) -> dict:
    """Evalúa un subset con 5-fold CV. Devuelve mean ± std macro-F1 y accuracy."""
    if not emb_arrays:
        return {"mean_f1": 0.0, "std_f1": 0.0, "mean_acc": 0.0, "std_acc": 0.0}
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    f1s, accs = [], []
    for tr_idx, te_idx in skf.split(emb_arrays[0], y):
        X_tr = np.concatenate([normalize_l2(e[tr_idx]) for e in emb_arrays], axis=1)
        X_te = np.concatenate([normalize_l2(e[te_idx]) for e in emb_arrays], axis=1)
        y_tr, y_te = y[tr_idx], y[te_idx]
        clf = make_clf(ARGS.clf)
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)
        f1s.append(f1_score(y_te, y_pred, average="macro"))
        accs.append(accuracy_score(y_te, y_pred))
    return {
        "mean_f1": float(np.mean(f1s)),
        "std_f1": float(np.std(f1s)),
        "mean_acc": float(np.mean(accs)),
        "std_acc": float(np.std(accs)),
        "per_fold_f1": f1s,
        "per_fold_acc": accs,
    }


def greedy_forward_search(emb_cache: dict, labels, max_steps: int = 12) -> list[dict]:
    """GFS: en cada paso, agrega el extractor que maximiza macro-F1.

    emb_cache: dict {extractor_name: np.ndarray}
    Devuelve: lista de dicts con info de cada paso
    """
    from joblib import Parallel, delayed
    selected = []  # lista de extractores seleccionados en orden
    remaining = list(emb_cache.keys())
    history = []  # log de cada paso

    prev_f1 = 0.0
    for step in range(1, max_steps + 1):
        if not remaining:
            break
        # Evaluar todos los candidatos EN PARALELO
        n_jobs = min(8, len(remaining))
        results = Parallel(n_jobs=n_jobs)(
            delayed(evaluate_subset)(
                [emb_cache[e] for e in selected + [cand]], labels
            )
            for cand in remaining
        )
        # Encontrar el mejor
        best_idx = max(range(len(remaining)), key=lambda i: results[i]["mean_f1"])
        best_ext = remaining[best_idx]
        best_f1 = results[best_idx]["mean_f1"]
        best_r = results[best_idx]
        # Agregar el mejor
        selected.append(best_ext)
        remaining.remove(best_ext)
        dim = sum(emb_cache[e].shape[1] for e in selected)
        delta = best_f1 - prev_f1
        history.append({
            "step": step,
            "added": best_ext,
            "selected": list(selected),
            "f1": best_f1,
            "std_f1": best_r["std_f1"],
            "acc": best_r["mean_acc"],
            "dim": dim,
            "delta": delta,
            "per_fold_f1": best_r.get("per_fold_f1", []),
        })
        prev_f1 = best_f1
        print(f"  step {step:2d}  +{best_ext:20s}  f1={best_f1:.3f}  Δ={delta:+.3f}  dim={dim}", flush=True)
        # Si no hay mejora significativa, parar
        if step > 1 and delta < 1e-4:
            break
    return history


# Variable global para el clf (CLI arg)
ARGS = None


def main():
    global ARGS
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=DATASETS)
    parser.add_argument("--extractors", nargs="+", default=ALL_EXTRACTORS)
    parser.add_argument("--clfs", nargs="+", default=["svm", "knn", "rf", "mlp", "resmlp"])
    parser.add_argument("--max-steps", type=int, default=17)
    args = parser.parse_args()
    ARGS = args  # para que evaluate_subset lo vea

    print(f"GFS: datasets={args.datasets}, extractors={len(args.extractors)} disponibles, clfs={args.clfs}\n")

    all_results = []

    for dataset in args.datasets:
        print(f"=== Dataset: {dataset} ===")
        # Cargar embeddings disponibles
        emb_cache = {}
        for ext in args.extractors:
            try:
                emb, lab = load_embeddings(dataset, ext)
                emb_cache[ext] = emb
            except FileNotFoundError:
                pass
        if not emb_cache:
            print(f"  [SKIP] Sin embeddings, saltando\n")
            continue
        labels = lab  # son los mismos
        print(f"  {len(emb_cache)} extractores disponibles: {list(emb_cache.keys())}")

        ds_results = []
        for clf_name in args.clfs:
            print(f"  --- clf={clf_name} ---")
            ARGS.clf = clf_name  # para evaluate_subset
            t0 = time.time()
            history = greedy_forward_search(emb_cache, labels, max_steps=args.max_steps)
            elapsed = time.time() - t0
            print(f"    GFS completado en {elapsed:.1f}s ({len(history)} pasos)")
            for h in history:
                row = {
                    "dataset": dataset,
                    "clf": clf_name,
                    "step": h["step"],
                    "added": h["added"],
                    "selected": " + ".join(h["selected"]),
                    "n_selected": len(h["selected"]),
                    "f1": h["f1"],
                    "std_f1": h["std_f1"],
                    "acc": h["acc"],
                    "dim": h["dim"],
                    "delta": h["delta"],
                }
                ds_results.append(row)
                all_results.append(row)
                print(f"    step {h['step']:2d}  +{h['added']:20s}  f1={h['f1']:.3f}  Δ={h['delta']:+.3f}  dim={h['dim']}")

            # Figura: F1 vs step
            fig, ax = plt.subplots(figsize=(8, 5))
            steps = [h["step"] for h in history]
            f1s = [h["f1"] for h in history]
            stds = [h["std_f1"] for h in history]
            ax.plot(steps, f1s, marker="o", linewidth=2, color="C0")
            ax.fill_between(steps,
                            [f - s for f, s in zip(f1s, stds)],
                            [f + s for f, s in zip(f1s, stds)],
                            alpha=0.2)
            ax.set_xlabel("Step (extractores seleccionados)")
            ax.set_ylabel("macro-F1 (5-fold CV)")
            ax.set_title(f"GFS path: {dataset} ({clf_name})")
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 1.05)
            plt.tight_layout()
            out_path = FIGURES_DIR / f"greedy_path_{dataset}_{clf_name}.png"
            plt.savefig(out_path, dpi=120)
            plt.close()
            print(f"    -> {out_path}")
            print()

        # CSV per dataset
        if ds_results:
            pd.DataFrame(ds_results).to_csv(TABLES_DIR / f"greedy_{dataset}.csv", index=False)
            # Per-fold para diff sig
            with open(TABLES_DIR / f"perfold_greedy_{dataset}.jsonl", "w") as fp:
                for r in ds_results:
                    fp.write(json.dumps({
                        "dataset": r["dataset"], "clf": r["clf"],
                        "step": r["step"], "selected": r["selected"],
                        "extractors": r["selected"],
                        "per_fold_f1": history[r["step"] - 1].get("per_fold_f1", []) if r["step"] <= len(history) else [],
                    }) + "\n")
            print(f"  -> Saved results/tables/greedy_{dataset}.csv + perfold_greedy_{dataset}.jsonl")

    # Summary
    if all_results:
        pd.DataFrame(all_results).to_csv(TABLES_DIR / "greedy_summary.csv", index=False)
        print(f"=== Summary: results/tables/greedy_summary.csv ===\n")

        # Tabla de mejor (subset, clf) por dataset
        df = pd.DataFrame(all_results)
        best_per = df.loc[df.groupby("dataset")["f1"].idxmax()][
            ["dataset", "step", "n_selected", "selected", "f1", "std_f1", "dim"]
        ].sort_values("f1", ascending=False)
        print("Mejor subset greedy por dataset:")
        print(best_per.to_string(index=False))


if __name__ == "__main__":
    main()
