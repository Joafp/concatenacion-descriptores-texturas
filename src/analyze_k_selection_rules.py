#!/usr/bin/env python3
"""Can k be chosen from the training side, and does that choice hold up?

The external sweep shows the accuracy curve flattening around four blocks, but
reading k off that curve reads it off the external test.  Here the same prefixes
are scored on the inner folds, and rules that look only at the inner curve pick
a k whose external result is then reported.

Rules compared, all training-side:

``argmax``     the k maximising the inner criterion;
``elbow(tau)`` the first k whose marginal inner gain falls below tau;
``fixed(c)``   a constant k, which needs no curve at all.

Each is scored against the external oracle k of the same condition, an upper
bound computed on the test that no rule can be expected to reach, and against
concatenating the whole library.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[1]


def load(root: Path) -> pd.DataFrame:
    ext = pd.concat([pd.read_csv(p) for p in glob.glob(str(root / "*/k_sweep.csv"))])
    inn = pd.concat([pd.read_csv(p) for p in glob.glob(str(root / "*/k_sweep_inner.csv"))])
    keys = ["dataset", "classifier", "seed", "outer_fold", "k"]
    merged = ext.merge(inn[keys + ["inner_f1"]], on=keys, validate="one_to_one")
    if len(merged) != len(ext):
        raise RuntimeError(f"join lost rows: {len(ext)} -> {len(merged)}")
    return merged


def pick_argmax(block: pd.DataFrame) -> int:
    return int(block.loc[block["inner_f1"].idxmax(), "k"])


def pick_elbow(block: pd.DataFrame, tau: float) -> int:
    block = block.sort_values("k")
    gains = block["inner_f1"].diff()
    for k, g in zip(block["k"].iloc[1:], gains.iloc[1:]):
        if g < tau:
            return int(k - 1)
    return int(block["k"].max())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path,
                        default=REPO / "results/exploratory/k_sweep")
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/analysis/k_selection_rules")
    args = parser.parse_args()
    frame = load(args.root.resolve())
    conditions = list(frame.groupby(["dataset", "outer_fold"]))
    print(f"condiciones: {len(conditions)}   datasets: {frame.dataset.nunique()}\n")

    print("¿COINCIDEN LAS DOS CURVAS? (Spearman entre inner-F1 y macro-F1 externo)")
    rhos = []
    for (ds, fold), blk in conditions:
        rho = spearmanr(blk["inner_f1"], blk["macro_f1"]).statistic
        rhos.append({"dataset": ds, "outer_fold": fold, "spearman": float(rho)})
    rho_frame = pd.DataFrame(rhos)
    for ds, blk in rho_frame.groupby("dataset"):
        print(f"  {ds:<22}{blk['spearman'].mean():>+8.3f}  "
              f"(n={len(blk)}, positivos {int((blk['spearman'] > 0).sum())})")
    print(f"  {'MEDIA':<22}{rho_frame['spearman'].mean():>+8.3f}  "
          f"positivos {int((rho_frame['spearman'] > 0).sum())}/{len(rho_frame)}")

    rules = {"argmax interno": pick_argmax}
    for tau in (0.02, 0.01, 0.005, 0.002, 0.001):
        rules[f"codo tau={tau}"] = (lambda t: lambda b: pick_elbow(b, t))(tau)
    for c in (2, 3, 4, 6, 8):
        rules[f"fijo k={c}"] = (lambda c: lambda b: min(c, int(b["k"].max())))(c)

    print("\nRESULTADO EXTERNO DE CADA REGLA (media sobre condiciones)")
    print(f"{'regla':<18}{'k medio':>9}{'macroF1':>10}{'% dims':>9}"
          f"{'vs completa':>13}{'vs oraculo':>12}")
    summary = []
    for name, rule in rules.items():
        picks, f1s, dims, vs_full, vs_or = [], [], [], [], []
        for (_, _), blk in conditions:
            blk = blk.sort_values("k")
            k = rule(blk)
            row = blk[blk["k"].eq(k)].iloc[0]
            full = blk.iloc[-1]
            oracle = blk.loc[blk["macro_f1"].idxmax()]
            picks.append(k); f1s.append(row["macro_f1"])
            dims.append(row["pct_dimensions"])
            vs_full.append(row["macro_f1"] - full["macro_f1"])
            vs_or.append(row["macro_f1"] - oracle["macro_f1"])
        entry = {"rule": name, "mean_k": float(np.mean(picks)),
                 "macro_f1": float(np.mean(f1s)), "pct_dims": float(np.mean(dims)),
                 "vs_full": float(np.mean(vs_full)), "vs_oracle": float(np.mean(vs_or)),
                 "wins_vs_full": int(sum(1 for v in vs_full if v > 0)),
                 "n": len(vs_full)}
        summary.append(entry)
        print(f"{name:<18}{entry['mean_k']:>9.1f}{entry['macro_f1']:>10.4f}"
              f"{entry['pct_dims']:>8.0f}%{entry['vs_full']:>+13.4f}"
              f"{entry['vs_oracle']:>+12.4f}")

    oracle_f1 = np.mean([blk["macro_f1"].max() for _, blk in conditions])
    full_f1 = np.mean([blk.sort_values("k")["macro_f1"].iloc[-1] for _, blk in conditions])
    print(f"\n  referencia: oraculo externo {oracle_f1:.4f}   "
          f"biblioteca completa {full_f1:.4f}")

    args.output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary).to_csv(args.output / "k_rules.csv", index=False)
    (args.output / "k_rules.json").write_text(json.dumps(
        {"n_conditions": len(conditions), "rules": summary,
         "spearman_inner_vs_external": rho_frame.to_dict("records"),
         "mean_spearman": float(rho_frame["spearman"].mean()),
         "oracle_macro_f1": float(oracle_f1), "full_macro_f1": float(full_f1),
         "caveats": [
             "The oracle k is read off the external test and is an upper bound, "
             "never an achievable selection.",
             "One classifier and one seed; CUReT directions are dependent and "
             "Outex has a single split, so no inferential contrast applies.",
             "The sweep's full library excludes rgb_ngram_svd.",
         ]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nescrito en {args.output}")


if __name__ == "__main__":
    main()
