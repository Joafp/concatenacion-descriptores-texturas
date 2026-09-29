#!/usr/bin/env python3
"""Locate the greedy subset inside the exhaustive ranking of equal-size subsets.

Consumes the enumeration written by ``analyze_oracle_gap.py`` together with a
GFS run over the *same* block library and the *same* outer partitions, and
reports how much external macro-F1 a perfect selector would have recovered.

The oracle is an upper bound computed on the external test; it is not an
achievable selection result.  Its only purpose is to size the headroom that a
better training-time criterion could target.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def load_gfs(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = frame[frame["method"].eq("gfs") & frame["run_mode"].eq("full")]
    return frame[["classifier", "outer_fold", "macro_f1", "k", "selected"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exhaustive", type=Path,
                        default=REPO / "results/analysis/oracle_gap/KTHTIPS2b_svm_exhaustive.csv")
    parser.add_argument("--gfs", type=Path,
                        default=REPO / "results/extensions/kth_tips2b/oracle_matched/nested_fold_results.csv")
    parser.add_argument("--output", type=Path, default=REPO / "results/analysis/oracle_gap")
    args = parser.parse_args()

    grid = pd.read_csv(args.exhaustive)
    gfs = load_gfs(args.gfs)
    # split tags look like ``official3_inverted``; outer_fold is split - 1.
    grid["outer_fold"] = grid["split"].str.extract(r"official(\d+)").astype(int) - 1

    rows = []
    for (split, fold), block in grid.groupby(["split", "outer_fold"]):
        match = gfs[gfs["outer_fold"].eq(fold)]
        if match.empty:
            print(f"aviso: sin GFS para {split}, se omite")
            continue
        chosen = match.iloc[0]
        subset = "+".join(sorted(str(chosen["selected"]).split("+")))
        k = int(chosen["k"])
        same_k = block[block["k"].eq(k)].sort_values("macro_f1", ascending=False)
        if same_k.empty:
            print(f"aviso: la enumeracion no cubre k={k} en {split}, se omite")
            continue
        normalized = same_k.assign(
            key=same_k["subset"].map(lambda s: "+".join(sorted(s.split("+")))))
        hit = normalized[normalized["key"].eq(subset)]
        gfs_f1 = float(chosen["macro_f1"])
        best = same_k.iloc[0]
        better = int((same_k["macro_f1"] > gfs_f1).sum())
        rows.append({
            "split": split, "k": k,
            "gfs_subset": subset, "gfs_macro_f1": gfs_f1,
            "gfs_in_enumeration": bool(len(hit)),
            "gfs_rank": better + 1,
            "oracle_subset": best["subset"], "oracle_macro_f1": float(best["macro_f1"]),
            "gap": float(best["macro_f1"]) - gfs_f1,
            "n_subsets_same_k": int(len(same_k)),
            "n_better_than_gfs": better,
            "gfs_percentile": float(100 * (1 - better / len(same_k))),
        })

    report = pd.DataFrame(rows)
    args.output.mkdir(parents=True, exist_ok=True)
    report.to_csv(args.output / "oracle_gap_summary.csv", index=False)

    pd.set_option("display.width", 200)
    print(report[["split", "k", "gfs_macro_f1", "oracle_macro_f1", "gap",
                  "gfs_rank", "n_subsets_same_k", "gfs_percentile"]]
          .to_string(index=False))
    print()
    print(f"brecha media contra el oraculo del mismo k: {report['gap'].mean():+.4f}")
    print(f"percentil medio de GFS en la enumeracion:   {report['gfs_percentile'].mean():.1f}")
    print()
    print("subconjunto elegido por GFS vs. optimo, por particion:")
    for _, row in report.iterrows():
        print(f"  {row['split']:<22} GFS={row['gfs_subset']:<28} "
              f"oraculo={row['oracle_subset']}")

    # Does the oracle subset of one partition transfer to the others?
    best_per_split = {r["split"]: r["oracle_subset"] for _, r in report.iterrows()}
    print("\nestabilidad del optimo entre particiones:")
    print(f"  subconjuntos optimos distintos: {len(set(best_per_split.values()))}"
          f" de {len(best_per_split)} particiones")
    (args.output / "oracle_gap_summary.json").write_text(
        json.dumps({"per_split": rows,
                    "mean_gap": float(report["gap"].mean()),
                    "mean_percentile": float(report["gfs_percentile"].mean()),
                    "distinct_oracle_subsets": len(set(best_per_split.values()))},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
