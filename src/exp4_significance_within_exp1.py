"""
exp4_significance_within_exp1.py
================================
A partir de los resultados de Exp 1 (perfold_*.jsonl), para cada (dataset, clf):
  1. Identifica el mejor extractor (mayor mean F1)
  2. Hace paired t-test entre el mejor y cada uno de los otros 16
  3. Aplica corrección Holm-Bonferroni por familia (dataset, clf)
  4. Genera:
     - results/tables/exp4_best_per_dataset_clf.csv
     - results/tables/exp4_significance_matrix.csv
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

TABLES = Path("results/tables")
DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]


def holm_bonferroni(p_values: list[float]) -> list[float]:
    n = len(p_values)
    if n == 0:
        return []
    order = np.argsort(p_values)
    sorted_p = np.array(p_values)[order]
    adjusted = np.zeros(n)
    running_max = 0.0
    for i in range(n):
        val = sorted_p[i] * (n - i)
        running_max = max(running_max, val)
        adjusted[i] = min(running_max, 1.0)
    result = np.zeros(n)
    for i, oi in enumerate(order):
        result[oi] = adjusted[i]
    return result.tolist()


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    diff = np.array(a) - np.array(b)
    return diff.mean() / (diff.std(ddof=1) + 1e-12)


def main():
    rows = []
    for ds in DATASETS:
        p = TABLES / f"perfold_{ds}.jsonl"
        if not p.exists():
            continue
        ds_rows = [json.loads(l) for l in open(p) if l.strip()]

        # Agrupar por clf
        clfs = sorted(set(r["clf"] for r in ds_rows))
        for clf in clfs:
            sub = [r for r in ds_rows if r["clf"] == clf]
            if not sub:
                continue
            # Best por mean F1
            sub_sorted = sorted(sub, key=lambda r: -np.mean(r["per_fold_f1"]))
            best = sub_sorted[0]
            best_name = best["extractor"]
            best_f1 = np.array(best["per_fold_f1"])
            best_mean = float(best_f1.mean())
            best_std = float(best_f1.std(ddof=1))

            # Pairwise vs todos los otros
            pvals = []
            rows_ds = []
            for other in sub:
                if other["extractor"] == best_name:
                    continue
                other_f1 = np.array(other["per_fold_f1"])
                if len(other_f1) != len(best_f1):
                    continue
                t_stat, p_val = stats.ttest_rel(best_f1, other_f1)
                d = cohens_d(best_f1, other_f1)
                rows_ds.append({
                    "dataset": ds,
                    "clf": clf,
                    "best_extractor": best_name,
                    "best_mean_f1": best_mean,
                    "best_std_f1": best_std,
                    "comparison_extractor": other["extractor"],
                    "comparison_mean_f1": float(other_f1.mean()),
                    "comparison_std_f1": float(other_f1.std(ddof=1)),
                    "delta": float(best_mean - other_f1.mean()),
                    "t_stat": float(t_stat),
                    "p_value": float(p_val),
                    "cohens_d": float(d),
                })
                pvals.append(float(p_val))
            # Holm-Bonferroni
            adj = holm_bonferroni(pvals)
            for i, r in enumerate(rows_ds):
                r["p_value_holm"] = adj[i]
                r["significant_05"] = bool(adj[i] < 0.05)
                r["significant_01"] = bool(adj[i] < 0.01)
                r["significant_001"] = bool(adj[i] < 0.001)
                r["rank"] = i + 1
            rows.extend(rows_ds)

    if not rows:
        print("Sin resultados.")
        return

    df = pd.DataFrame(rows)
    cols = [
        "dataset", "clf", "best_extractor", "best_mean_f1", "best_std_f1",
        "comparison_extractor", "comparison_mean_f1", "comparison_std_f1",
        "delta", "t_stat", "p_value", "p_value_holm", "cohens_d", "rank",
        "significant_05", "significant_01", "significant_001",
    ]
    df[cols].to_csv(TABLES / "exp4_significance_matrix.csv", index=False)
    print(f"[OK] exp4_significance_matrix.csv: {len(df)} filas")

    # Best per (dataset, clf) — summary
    best_summary = (
        df.groupby(["dataset", "clf"])
        .agg(
            best_extractor=("best_extractor", "first"),
            best_mean_f1=("best_mean_f1", "first"),
            n_sig_05=("significant_05", "sum"),
            n_sig_01=("significant_01", "sum"),
            n_sig_001=("significant_001", "sum"),
        )
        .reset_index()
    )
    best_summary["n_total_comparisons"] = (
        df.groupby(["dataset", "clf"]).size().values
    )
    best_summary.to_csv(TABLES / "exp4_best_per_dataset_clf.csv", index=False)
    print(f"[OK] exp4_best_per_dataset_clf.csv: {len(best_summary)} filas")

    # Print resumen
    print("\nMejor extractor por (dataset, clf) — Exp 1:")
    for _, r in best_summary.iterrows():
        print(
            f"  {r['dataset']:10s} {r['clf']:5s}  "
            f"best={r['best_extractor']:18s} f1={r['best_mean_f1']:.3f}  "
            f"sig_vs_others(05)={r['n_sig_05']}/{r['n_total_comparisons']}"
        )


if __name__ == "__main__":
    main()
