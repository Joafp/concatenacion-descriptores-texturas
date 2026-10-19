#!/usr/bin/env python3
"""Does the saturation decision rule survive the inner-grouping correction?

The rule reads how much headroom the inner criterion still has
(``1 - inner_f1`` of the best single block, training-side only) and falls back
to full concatenation when that headroom is below tau, on the grounds that a
saturated criterion cannot rank candidates.  KTH-TIPS2-b is the partition where
the rule earns its keep in the leave-one-dataset-out validation.

But the correction (``--inner-group-column sample``) exists precisely to stop
the inner criterion from saturating there, so it moves the rule's own input.
This script contrasts the two matched runs and reports what the rule decides,
and what that decision yields externally, before and after the correction.

Both runs share one block library, which is the locally available one rather
than the manuscript's; the comparison is therefore about the rule's behaviour
under the correction, not about reproducing published values.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
HOMOGENEOUS = "best_homogeneous_"


def headroom(root: Path) -> pd.DataFrame:
    """Training-side headroom of each condition, from the GFS history."""
    records = []
    for line in (root / "selected_subsets.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("run_mode") != "full":
            continue
        records.append({
            "classifier": entry["classifier"],
            "outer_fold": entry["outer_fold"],
            "inner_best_single": entry["history"][0]["inner_f1"],
            "k_gfs": len(entry["gfs"]),
        })
    frame = pd.DataFrame(records)
    frame["headroom"] = 1.0 - frame["inner_best_single"]
    return frame


def outcomes(root: Path) -> pd.DataFrame:
    frame = pd.read_csv(root / "nested_fold_results.csv")
    frame = frame[frame["run_mode"].eq("full")]
    wide = frame.pivot_table(index=["classifier", "outer_fold"],
                             columns="method", values="macro_f1").reset_index()
    return wide


def combine(root: Path) -> pd.DataFrame:
    joined = headroom(root).merge(outcomes(root), on=["classifier", "outer_fold"],
                                  validate="one_to_one")
    missing = [c for c in ("gfs", "full_concat") if c not in joined]
    if missing:
        raise ValueError(f"{root} lacks methods {missing}")
    return joined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--original", type=Path,
                        default=REPO / "results/extensions/kth_tips2b/oracle_matched")
    parser.add_argument("--corrected", type=Path,
                        default=REPO / "results/extensions/kth_tips2b/inner_group_sample")
    parser.add_argument("--tau", type=float, default=0.01,
                        help="threshold the leave-one-dataset-out validation "
                             "selected for KTH-TIPS2-b from the other datasets")
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/analysis/policy_under_fix")
    args = parser.parse_args()

    runs = {"sin correccion": combine(args.original),
            "con correccion": combine(args.corrected)}

    print(f"REGLA DE SATURACION BAJO LA CORRECCION   (tau = {args.tau})\n")
    print(f"{'corrida':<16}{'clasif':<9}{'fold':>5}{'headroom':>11}"
          f"{'satura?':>10}{'elige':>12}{'GFS':>9}{'Completa':>10}{'logra':>9}")
    summary = []
    for label, frame in runs.items():
        for _, row in frame.sort_values(["classifier", "outer_fold"]).iterrows():
            blind = row["headroom"] < args.tau
            choice = "Completa" if blind else "GFS"
            got = row["full_concat"] if blind else row["gfs"]
            print(f"{label:<16}{row['classifier']:<9}{int(row['outer_fold']):>5}"
                  f"{row['headroom']:>11.4f}{('si' if blind else 'no'):>10}"
                  f"{choice:>12}{row['gfs']:>9.4f}{row['full_concat']:>10.4f}"
                  f"{got:>9.4f}")
        print()

    print(f"{'corrida':<16}{'clasif':<9}{'regla':>9}{'siempre GFS':>14}"
          f"{'siempre Compl.':>16}{'veces satura':>14}")
    for label, frame in runs.items():
        for clf, block in frame.groupby("classifier"):
            blind = block["headroom"] < args.tau
            policy = np.where(blind, block["full_concat"], block["gfs"])
            entry = {
                "run": label, "classifier": clf,
                "tau": args.tau,
                "policy": float(policy.mean()),
                "always_gfs": float(block["gfs"].mean()),
                "always_full_concat": float(block["full_concat"].mean()),
                "n_saturated": int(blind.sum()), "n": int(len(block)),
                "mean_headroom": float(block["headroom"].mean()),
            }
            entry["policy_minus_gfs"] = entry["policy"] - entry["always_gfs"]
            entry["policy_minus_full"] = entry["policy"] - entry["always_full_concat"]
            summary.append(entry)
            print(f"{label:<16}{clf:<9}{entry['policy']:>9.4f}"
                  f"{entry['always_gfs']:>14.4f}{entry['always_full_concat']:>16.4f}"
                  f"{entry['n_saturated']:>9}/{entry['n']:<4}")

    print("\nLECTURA")
    for clf in sorted({e["classifier"] for e in summary}):
        before = next(e for e in summary if e["run"] == "sin correccion" and e["classifier"] == clf)
        after = next(e for e in summary if e["run"] == "con correccion" and e["classifier"] == clf)
        print(f"  {clf}: headroom medio {before['mean_headroom']:.4f} -> "
              f"{after['mean_headroom']:.4f}; satura {before['n_saturated']}/{before['n']}"
              f" -> {after['n_saturated']}/{after['n']}")
        print(f"      la regla logra {before['policy']:.4f} -> {after['policy']:.4f}  "
              f"(vs mejor fija {max(after['always_gfs'], after['always_full_concat']):.4f})")

    args.output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary).to_csv(args.output / "policy_under_fix.csv", index=False)
    (args.output / "policy_under_fix.json").write_text(
        json.dumps({"tau": args.tau, "summary": summary,
                    "caveats": [
                        "Both runs use the locally available block library, not "
                        "the manuscript's; values are not published numbers.",
                        "Four outer partitions of one dataset; descriptive only.",
                        "tau is the value the leave-one-dataset-out validation "
                        "chose for KTH-TIPS2-b from the other five datasets.",
                    ]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nescrito en {args.output}")


if __name__ == "__main__":
    main()
