#!/usr/bin/env python3
"""Valida y resume únicamente resultados outer-test confirmatorios."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon


PRIMARY_BASELINES = ("best_individual", "full_concat")
BOOTSTRAP_ITERATIONS = 20_000
BOOTSTRAP_SEED = 20260719


def paired_comparisons(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize paired outer-split differences without treating them as IID samples."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows = []
    keys = ["dataset", "classifier", "seed", "outer_fold"]
    for (dataset, classifier), group in df.groupby(["dataset", "classifier"]):
        pivot = group.pivot(index=keys[2:], columns="method", values="macro_f1")
        if "gfs" not in pivot:
            continue
        for baseline in PRIMARY_BASELINES:
            if baseline not in pivot:
                continue
            paired = pivot[["gfs", baseline]].dropna()
            delta = (paired["gfs"] - paired[baseline]).to_numpy()
            if len(delta) < 2:
                # Una partición oficial permite calcular el efecto observado,
                # pero no una distribución entre particiones independientes.
                ci_low = ci_high = p_value = np.nan
                inference_note = (
                    "single official split; effect size is descriptive only; "
                    "split-level CI and Wilcoxon intentionally omitted"
                )
            elif dataset == "CUReT":
                # Las dos direcciones reutilizan las mismas 92 condiciones,
                # intercambiando train y test. No son réplicas independientes y
                # n=2 no sustenta inferencia entre splits.
                ci_low = ci_high = p_value = np.nan
                inference_note = (
                    "two complementary dependent directions; descriptive only; "
                    "split-level CI and Wilcoxon intentionally omitted"
                )
            else:
                boot = rng.choice(delta, size=(BOOTSTRAP_ITERATIONS, len(delta)), replace=True).mean(axis=1)
                ci_low, ci_high = np.quantile(boot, [0.025, 0.975])
                try:
                    p_value = float(wilcoxon(delta, zero_method="pratt", alternative="two-sided").pvalue)
                except ValueError:
                    p_value = 1.0
                inference_note = "outer splits overlap across repetitions; treat split-level inference as descriptive"
            rows.append({
                "dataset": dataset, "classifier": classifier, "comparison": f"gfs_vs_{baseline}",
                "n_splits": len(delta), "delta_mean": delta.mean(),
                "ci95_low": ci_low, "ci95_high": ci_high,
                "wins": int((delta > 0).sum()), "ties": int((delta == 0).sum()),
                "losses": int((delta < 0).sum()), "practical_equivalence_rate": float((abs(delta) < 0.01).mean()),
                "wilcoxon_p_uncorrected": p_value,
                "inference_note": inference_note,
            })
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    valid = result.wilcoxon_p_uncorrected.dropna()
    order = valid.sort_values().index
    m = len(valid)
    adjusted = pd.Series(np.nan, index=result.index, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, result.loc[idx, "wilcoxon_p_uncorrected"] * (m - rank)))
        adjusted.loc[idx] = running
    result["wilcoxon_p_holm"] = adjusted
    return result


def random_subset_summary(df: pd.DataFrame, random_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if random_df.empty:
        return pd.DataFrame(rows)
    gfs = df[df.method.eq("gfs")].set_index(["dataset", "classifier", "seed", "outer_fold"])
    for key, group in random_df.groupby(["dataset", "classifier", "seed", "outer_fold"]):
        if key not in gfs.index:
            continue
        score = float(gfs.loc[key, "macro_f1"])
        ge = int((group.macro_f1 >= score).sum())
        rows.append({
            "dataset": key[0], "classifier": key[1], "seed": key[2], "outer_fold": key[3],
            "gfs_macro_f1": score, "random_b": len(group), "random_mean": group.macro_f1.mean(),
            "random_std": group.macro_f1.std(), "random_max": group.macro_f1.max(),
            "gfs_percentile": float((group.macro_f1 < score).mean()),
            "empirical_p": (1 + ge) / (len(group) + 1),
        })
    return pd.DataFrame(rows)


def empty_outputs(out: Path) -> None:
    schemas = {
        "nested_summary.csv": ["dataset", "classifier", "method", "n", "macro_f1_mean", "macro_f1_std"],
        "selection_frequency.csv": ["dataset", "classifier", "extractor", "family", "count", "frequency"],
        "stability_summary.csv": ["dataset", "classifier", "n_pairs", "jaccard_mean", "jaccard_std"],
        "family_ablation.csv": ["dataset", "classifier", "method", "macro_f1_mean", "k_mean"],
        "cost_summary.csv": ["dataset", "classifier", "method", "dimensions_mean", "fit_seconds_mean"],
        "paired_comparisons.csv": ["dataset", "classifier", "comparison", "n_splits", "delta_mean"],
        "random_subset_summary.csv": ["dataset", "classifier", "seed", "outer_fold", "empirical_p"],
    }
    for name, columns in schemas.items():
        if not (out / name).exists():
            pd.DataFrame(columns=columns).to_csv(out / name, index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/confirmatory"))
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    path = out / "nested_fold_results.csv"
    if not path.exists() or path.stat().st_size == 0:
        empty_outputs(out)
        print("No eligible outer-test results; wrote schema-only outputs.")
        return
    df = pd.read_csv(path)
    required = {"dataset", "classifier", "seed", "outer_fold", "method", "macro_f1", "selected"}
    if not required.issubset(df.columns):
        raise ValueError(f"missing columns: {sorted(required - set(df.columns))}")
    if df.duplicated(["dataset", "classifier", "seed", "outer_fold", "method"]).any():
        raise ValueError("duplicate outer-test condition/method rows")
    numeric = ["macro_f1", "accuracy", "k", "dimensions", "fit_seconds"]
    if df[numeric].isna().any().any() or not np.isfinite(df[numeric]).all().all():
        raise ValueError("missing/NaN/non-finite confirmatory result")
    summary = (df.groupby(["dataset", "classifier", "method"])["macro_f1"]
               .agg(n="size", macro_f1_mean="mean", macro_f1_std="std").reset_index())
    summary.to_csv(out / "nested_summary.csv", index=False)
    selected = df[df.method.eq("gfs")].copy()
    freq_rows = []
    for (dataset, clf), group in selected.groupby(["dataset", "classifier"]):
        subsets = [set(str(v).split("+")) for v in group.selected]
        for extractor in sorted(set().union(*subsets)):
            count = sum(extractor in s for s in subsets)
            freq_rows.append({"dataset": dataset, "classifier": clf, "extractor": extractor,
                              "family": "see runner family map", "count": count,
                              "frequency": count / len(subsets)})
    pd.DataFrame(freq_rows).to_csv(out / "selection_frequency.csv", index=False)
    stability = []
    for (dataset, clf), group in selected.groupby(["dataset", "classifier"]):
        subsets = [set(str(v).split("+")) for v in group.selected]
        values = [len(a & b) / len(a | b) for a, b in itertools.combinations(subsets, 2)]
        stability.append({"dataset": dataset, "classifier": clf, "n_pairs": len(values),
                          "jaccard_mean": np.mean(values) if values else np.nan,
                          "jaccard_std": np.std(values) if values else np.nan})
    pd.DataFrame(stability).to_csv(out / "stability_summary.csv", index=False)
    family = df[df.method.str.startswith("best_homogeneous_") | df.method.eq("gfs")]
    family.groupby(["dataset", "classifier", "method"]).agg(
        macro_f1_mean=("macro_f1", "mean"), k_mean=("k", "mean")
    ).reset_index().to_csv(out / "family_ablation.csv", index=False)
    df.groupby(["dataset", "classifier", "method"]).agg(
        dimensions_mean=("dimensions", "mean"), fit_seconds_mean=("fit_seconds", "mean")
    ).reset_index().to_csv(out / "cost_summary.csv", index=False)
    paired_comparisons(df).to_csv(out / "paired_comparisons.csv", index=False)
    random_path = out / "random_subset_results.csv"
    random_df = pd.read_csv(random_path) if random_path.exists() and random_path.stat().st_size else pd.DataFrame()
    random_subset_summary(df, random_df).to_csv(out / "random_subset_summary.csv", index=False)
    print(json.dumps({"rows": len(df), "conditions": len(selected)}, indent=2))


if __name__ == "__main__":
    main()
