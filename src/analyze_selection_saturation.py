#!/usr/bin/env python3
"""When does block selection stop paying off? A training-time decision rule.

Greedy Forward Selection stops adding blocks when the internal criterion stops
improving.  That criterion is macro-F1 over the inner folds, so when the single
best block already saturates it, GFS has no signal left to discriminate between
candidates and stops almost immediately.  This script quantifies that effect
and turns it into a decision rule that uses *only* training-time information.

Inputs (all already produced by the confirmatory protocol):
  * the canonical 22-block result matrix used by the manuscript;
  * the per-condition GFS histories, whose first step records the inner
    macro-F1 of the best individual block.

Definitions
-----------
headroom
    ``1 - inner_f1`` of the best single block, measured on the inner folds of
    the outer training partition.  It never touches the external test, so a
    practitioner can compute it before choosing a representation.

Outputs
-------
``selection_saturation.csv``    one row per external condition
``selection_saturation.json``   correlations, regime table, policy comparison
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, pearsonr, spearmanr, wilcoxon

REPO = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = REPO / "paper/articulo/borrador_profesor/generated/primary22_beitv2_source_rows.csv"
DEFAULT_HISTORIES = (
    REPO / "results/confirmatory/ngram22_beitv2/selected_subsets.jsonl",
    REPO / "results/extensions/kth_tips2b/ngram22_beitv2/selected_subsets.jsonl",
    REPO / "results/extensions/outex13_official1360/ngram22_beitv2/selected_subsets.jsonl",
    REPO / "results/extensions/soil_original/ngram22_beitv2/selected_subsets.jsonl",
)
KEYS = ["dataset", "classifier", "seed", "outer_fold"]
REGIMES = ((0.0, 0.01, "<1% (saturado)"), (0.01, 0.05, "1-5%"),
           (0.05, 0.12, "5-12%"), (0.12, 1.0, ">12%"))


def load_conditions(matrix_path: Path, history_paths) -> pd.DataFrame:
    """Join external results with the training-time headroom of each condition."""
    matrix = pd.read_csv(matrix_path)
    matrix = matrix[matrix["run_mode"].eq("full")]
    wide = matrix.pivot_table(index=KEYS, columns="method",
                              values=["macro_f1", "dimensions"])
    wide.columns = [f"{metric}__{method}" for metric, method in wide.columns]
    wide = wide.reset_index()

    records = []
    for path in history_paths:
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("run_mode") != "full":
                continue
            records.append({
                "dataset": entry["dataset"], "classifier": entry["classifier"],
                "seed": entry["seed"], "outer_fold": entry["outer_fold"],
                "inner_best_single": entry["history"][0]["inner_f1"],
                "k_gfs": len(entry["gfs"]),
                "gfs_steps": len(entry["history"]),
            })
    histories = pd.DataFrame(records)
    if histories.duplicated(KEYS).any():
        raise RuntimeError("duplicate GFS history for a single external condition")

    joined = wide.merge(histories, on=KEYS, how="inner", validate="one_to_one")
    if len(joined) != len(histories):
        raise RuntimeError(f"join lost conditions: {len(histories)} -> {len(joined)}")
    joined["headroom"] = 1.0 - joined["inner_best_single"]
    joined["completa_menos_gfs"] = joined["macro_f1__full_concat"] - joined["macro_f1__gfs"]
    return joined


def regime_table(frame: pd.DataFrame) -> list[dict]:
    rows = []
    for low, high, label in REGIMES:
        mask = (frame["headroom"] >= low) & (frame["headroom"] < high)
        subset = frame[mask]
        if subset.empty:
            continue
        wins = int((subset["completa_menos_gfs"] > 0).sum())
        rows.append({
            "regime": label, "n": int(len(subset)),
            "k_gfs_mean": float(subset["k_gfs"].mean()),
            "completa_minus_gfs_mean": float(subset["completa_menos_gfs"].mean()),
            "full_concat_wins": wins,
            "full_concat_win_rate": float(wins / len(subset)),
            "binomial_p_two_sided": float(binomtest(wins, len(subset), 0.5).pvalue),
        })
    return rows


def apply_policy(frame: pd.DataFrame, tau: float) -> pd.Series:
    """Adaptive policy: fall back to full concatenation when selection is blind."""
    blind = frame["headroom"] < tau
    return frame["macro_f1__full_concat"].where(blind, frame["macro_f1__gfs"])


def policy_dimensions(frame: pd.DataFrame, tau: float) -> pd.Series:
    blind = frame["headroom"] < tau
    return frame["dimensions__full_concat"].where(blind, frame["dimensions__gfs"])


def dataset_balanced_mean(frame: pd.DataFrame, values: pd.Series) -> float:
    """Average per dataset first so large datasets do not dominate."""
    return float(values.groupby(frame["dataset"]).mean().mean())


def leave_one_dataset_out(frame: pd.DataFrame, grid: np.ndarray) -> dict:
    """Choose tau on the remaining datasets, then apply it to the held-out one."""
    per_dataset, chosen = {}, {}
    for held_out in sorted(frame["dataset"].unique()):
        train = frame[frame["dataset"].ne(held_out)]
        test = frame[frame["dataset"].eq(held_out)]
        scores = [dataset_balanced_mean(train, apply_policy(train, tau)) for tau in grid]
        tau = float(grid[int(np.argmax(scores))])
        chosen[held_out] = tau
        per_dataset[held_out] = {
            "tau_from_other_datasets": tau,
            "adaptive": float(apply_policy(test, tau).mean()),
            "always_gfs": float(test["macro_f1__gfs"].mean()),
            "always_full_concat": float(test["macro_f1__full_concat"].mean()),
            "dims_adaptive": float(policy_dimensions(test, tau).mean()),
            "dims_always_gfs": float(test["dimensions__gfs"].mean()),
            "dims_always_full_concat": float(test["dimensions__full_concat"].mean()),
            "n_conditions": int(len(test)),
            "switched_to_full_concat": int((test["headroom"] < tau).sum()),
        }
    summary = {
        "tau_per_fold": chosen,
        "per_dataset": per_dataset,
        "mean_over_datasets": {
            name: float(np.mean([v[name] for v in per_dataset.values()]))
            for name in ("adaptive", "always_gfs", "always_full_concat",
                         "dims_adaptive", "dims_always_gfs", "dims_always_full_concat")
        },
    }
    # Six paired dataset means is a small sample; report the exact test rather
    # than leaning on the mean difference alone.
    adaptive = np.array([v["adaptive"] for v in per_dataset.values()])
    summary["paired_tests"] = {}
    for name in ("always_gfs", "always_full_concat"):
        other = np.array([v[name] for v in per_dataset.values()])
        delta = adaptive - other
        entry = {
            "mean_delta": float(delta.mean()),
            "wins": int((delta > 0).sum()),
            "ties": int((delta == 0).sum()),
            "losses": int((delta < 0).sum()),
        }
        if np.any(delta != 0):
            test = wilcoxon(delta, alternative="two-sided", method="exact",
                            zero_method="wilcox")
            entry["wilcoxon_statistic"] = float(test.statistic)
            entry["wilcoxon_p_two_sided"] = float(test.pvalue)
        summary["paired_tests"][f"adaptive_vs_{name}"] = entry
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/analysis/selection_saturation")
    args = parser.parse_args()

    frame = load_conditions(args.matrix, DEFAULT_HISTORIES)
    args.output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output / "selection_saturation.csv", index=False)

    pear_r, pear_p = pearsonr(frame["headroom"], frame["k_gfs"])
    spear_r, spear_p = spearmanr(frame["headroom"], frame["k_gfs"])
    grid = np.round(np.arange(0.0, 0.2001, 0.0025), 4)
    report = {
        "n_conditions": int(len(frame)),
        "datasets": sorted(frame["dataset"].unique().tolist()),
        "headroom_vs_k_gfs": {
            "pearson_r": float(pear_r), "pearson_p": float(pear_p),
            "spearman_r": float(spear_r), "spearman_p": float(spear_p),
        },
        "regimes": regime_table(frame),
        "leave_one_dataset_out": leave_one_dataset_out(frame, grid),
    }
    (args.output / "selection_saturation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"condiciones externas: {report['n_conditions']}")
    print(f"headroom vs k_gfs: Pearson r={pear_r:+.3f} (p={pear_p:.2e}), "
          f"Spearman r={spear_r:+.3f} (p={spear_p:.2e})\n")
    print(f"{'regimen':<18}{'n':>5}{'k medio':>10}{'Completa-GFS':>15}{'gana Completa':>16}{'p binom':>12}")
    for row in report["regimes"]:
        print(f"{row['regime']:<18}{row['n']:>5}{row['k_gfs_mean']:>10.2f}"
              f"{row['completa_minus_gfs_mean']:>+15.4f}"
              f"{row['full_concat_wins']:>8}/{row['n']:<7}"
              f"{row['binomial_p_two_sided']:>12.2e}")
    lodo = report["leave_one_dataset_out"]
    print("\nvalidacion leave-one-dataset-out (macro-F1 externo medio):")
    print(f"{'dataset':<22}{'tau':>8}{'adaptativa':>13}{'siempre GFS':>14}{'siempre Completa':>19}")
    for name, values in lodo["per_dataset"].items():
        print(f"{name:<22}{values['tau_from_other_datasets']:>8.4f}"
              f"{values['adaptive']:>13.4f}{values['always_gfs']:>14.4f}"
              f"{values['always_full_concat']:>19.4f}")
    means = lodo["mean_over_datasets"]
    print(f"{'PROMEDIO':<22}{'':>8}{means['adaptive']:>13.4f}"
          f"{means['always_gfs']:>14.4f}{means['always_full_concat']:>19.4f}")

    print("\ncontrastes pareados sobre las seis medias por dataset:")
    for name, entry in lodo["paired_tests"].items():
        line = (f"  {name:<32} delta={entry['mean_delta']:+.4f}  "
                f"V/E/D={entry['wins']}/{entry['ties']}/{entry['losses']}")
        if "wilcoxon_p_two_sided" in entry:
            line += f"  Wilcoxon p={entry['wilcoxon_p_two_sided']:.4f}"
        print(line)

    print("\ndimension media de la representacion:")
    print(f"  adaptativa       {means['dims_adaptive']:>10.0f}")
    print(f"  siempre GFS      {means['dims_always_gfs']:>10.0f}")
    print(f"  siempre Completa {means['dims_always_full_concat']:>10.0f}")
    print(f"\nescrito en {args.output}")


if __name__ == "__main__":
    main()
