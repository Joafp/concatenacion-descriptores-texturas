"""
14_diff_sig_vs_individual.py
=============================
Para cada combinación (prefix concat k=N, GFS step=N) corre paired t-test
contra CADA UNO de los 17 extractores solitarios, sobre los mismos 5 folds,
para cada (dataset, classifier). Aplica corrección de Holm-Bonferroni.

Lee:
  - results/tables/perfold_<dataset>.jsonl       (solitarios)
  - results/tables/perfold_concat_<dataset>.jsonl (prefix concat)
  - results/tables/perfold_greedy_<dataset>.jsonl (GFS - futuro)

Genera:
  - results/tables/diff_sig_vs_individual.csv
    Columnas: dataset, clf, strategy, combination_subset, comparison_extractor,
              mean_a, mean_b, delta, t_stat, p_value, cohens_d, p_value_holm,
              rank, significant_05, significant_01, significant_001
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy import stats


TABLES = Path("results/tables")


def load_perfold(path: Path) -> list[dict]:
    """Carga archivo JSONL de per-fold."""
    if not path.exists():
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def holm_bonferroni(p_values: list[float]) -> list[float]:
    """Ajusta p-values con Holm-Bonferroni (FWER control)."""
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
    # Reordenar al orden original
    result = np.zeros(n)
    for i, oi in enumerate(order):
        result[oi] = adjusted[i]
    return result.tolist()


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's d para muestras pareadas (a - b)."""
    diff = np.array(a) - np.array(b)
    return diff.mean() / (diff.std(ddof=1) + 1e-12)


def diff_sig_one_strategy(strategy_rows: list[dict], individual_index: dict, dataset: str, clf: str) -> list[dict]:
    """Para cada combinación en strategy_rows, corre paired t-test vs cada individual."""
    results = []
    for comb in strategy_rows:
        comb_name = comb.get("extractors") or " + ".join(comb.get("selected", []))
        comb_f1 = np.array(comb["per_fold_f1"])
        for indiv_ext, indiv_f1 in individual_index.items():
            if len(indiv_f1) != len(comb_f1):
                continue
            indiv_f1_arr = np.array(indiv_f1)
            t_stat, p_val = stats.ttest_rel(comb_f1, indiv_f1_arr)
            d = cohens_d(comb_f1, indiv_f1_arr)
            results.append({
                "dataset": dataset,
                "clf": clf,
                "strategy": comb.get("strategy", "concat"),
                "combination_subset": comb_name,
                "comparison_extractor": indiv_ext,
                "mean_combination": float(comb_f1.mean()),
                "mean_individual": float(indiv_f1_arr.mean()),
                "delta": float(comb_f1.mean() - indiv_f1_arr.mean()),
                "t_stat": float(t_stat),
                "p_value": float(p_val),
                "cohens_d": float(d),
            })
    return results


def diff_sig_for_dataset(dataset: str, clfs: list[str], results_dir: Path) -> list[dict]:
    """Corre todos los tests para un dataset y todos los clfs."""
    # Cargar individuales
    indiv_rows = load_perfold(results_dir / f"perfold_{dataset}.jsonl")
    indiv_index = {}  # {(clf, extractor): per_fold_f1}
    for r in indiv_rows:
        indiv_index[(r["clf"], r["extractor"])] = r["per_fold_f1"]

    all_results = []
    # Cargar prefix concat
    concat_rows = load_perfold(results_dir / f"perfold_concat_{dataset}.jsonl")
    for clf in clfs:
        sub = [r for r in concat_rows if r["clf"] == clf]
        sub_indiv = {ext: f1 for (c, ext), f1 in indiv_index.items() if c == clf}
        # Marcar strategy
        for r in sub:
            r["strategy"] = "prefix_concat"
        all_results.extend(diff_sig_one_strategy(sub, sub_indiv, dataset, clf))

    # Cargar GFS si existe
    greedy_rows = load_perfold(results_dir / f"perfold_greedy_{dataset}.jsonl")
    if greedy_rows:
        for clf in clfs:
            sub = [r for r in greedy_rows if r["clf"] == clf]
            sub_indiv = {ext: f1 for (c, ext), f1 in indiv_index.items() if c == clf}
            for r in sub:
                r["strategy"] = "gfs"
            all_results.extend(diff_sig_one_strategy(sub, sub_indiv, dataset, clf))

    return all_results


def main():
    results_dir = TABLES
    datasets = ["DTD", "FMD", "KTH-TIPS2-b", "GTOS-Mobile", "VisTex", "CUReT", "Soil"]
    clfs = ["svm", "knn", "rf", "mlp", "resmlp"]

    all_results = []
    for ds in datasets:
        if not (results_dir / f"perfold_{ds}.jsonl").exists():
            print(f"  [SKIP] {ds}: sin perfold_{ds}.jsonl")
            continue
        print(f"Procesando {ds}...")
        rs = diff_sig_for_dataset(ds, clfs, results_dir)
        print(f"  → {len(rs)} comparaciones")
        all_results.extend(rs)

    if not all_results:
        print("Sin resultados.")
        return

    df = pd.DataFrame(all_results)

    # Holm-Bonferroni por (dataset, clf, strategy, combination_subset)
    # Para cada combinación, ajustamos las p-values vs los 17 individuales
    df["p_value_holm"] = np.nan
    df["significant_05"] = False
    df["significant_01"] = False
    df["significant_001"] = False
    df["rank"] = 0

    for (ds, clf, strat, comb), grp in df.groupby(["dataset", "clf", "strategy", "combination_subset"]):
        idx = grp.index
        adjusted = holm_bonferroni(grp["p_value"].tolist())
        df.loc[idx, "p_value_holm"] = adjusted
        df.loc[idx, "significant_05"] = (np.array(adjusted) < 0.05)
        df.loc[idx, "significant_01"] = (np.array(adjusted) < 0.01)
        df.loc[idx, "significant_001"] = (np.array(adjusted) < 0.001)
        # rank por p_value (1 = más significativo)
        order = np.argsort(grp["p_value"].values)
        ranks = np.empty(len(order), dtype=int)
        ranks[order] = np.arange(1, len(order) + 1)
        df.loc[idx, "rank"] = ranks

    cols = [
        "dataset", "clf", "strategy", "combination_subset", "comparison_extractor",
        "mean_combination", "mean_individual", "delta", "t_stat", "p_value",
        "p_value_holm", "cohens_d", "rank",
        "significant_05", "significant_01", "significant_001",
    ]
    df[cols].to_csv(results_dir / "diff_sig_vs_individual.csv", index=False)
    print(f"\n=== Guardado: results/tables/diff_sig_vs_individual.csv ({len(df)} filas) ===")

    # Resumen por dataset
    print("\nResumen por dataset:")
    summary = df.groupby("dataset").agg(
        n_total=("p_value", "count"),
        n_sig_05=("significant_05", "sum"),
        n_sig_01=("significant_01", "sum"),
        n_sig_001=("significant_001", "sum"),
    )
    print(summary.to_string())

    # Top 10 comparaciones más significativas
    print("\nTop 10 comparaciones más significativas (p_value_holm < 0.001):")
    top = df[df["significant_001"]].nsmallest(10, "p_value_holm")
    print(top[["dataset", "clf", "strategy", "combination_subset", "comparison_extractor",
               "delta", "p_value_holm", "cohens_d"]].to_string(index=False))


if __name__ == "__main__":
    main()
