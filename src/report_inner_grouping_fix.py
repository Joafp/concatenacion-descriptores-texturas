#!/usr/bin/env python3
"""Effect of aligning the inner grouping with the outer protocol structure.

KTH-TIPS2-b holds out a whole physical sample in its external partition, but
the manifest ``group`` column is the per-image SHA-256, so the inner folds
split images at random inside the training samples.  The inner criterion then
measures within-sample recognition, saturates near 1.0 and loses the power to
rank candidates, while the external test still measures across-sample
generalisation.

This script contrasts two runs that differ only in the inner grouping
(``--inner-group-column sample``) and reports both the criterion diagnostics
and the external outcome for every strategy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
LABELS = {"best_individual": "Individual", "gfs": "GFS",
          "homogenea": "Homogenea", "full_concat": "Completa"}
ORDER = ["best_individual", "gfs", "homogenea", "full_concat"]


def outcomes(root: Path) -> pd.DataFrame:
    frame = pd.read_csv(root / "nested_fold_results.csv")
    frame = frame[frame["run_mode"].eq("full")].copy()
    frame["method"] = frame["method"].str.replace(
        "best_homogeneous_.*", "homogenea", regex=True)
    return frame


def diagnostics(root: Path) -> pd.DataFrame:
    records = []
    for line in (root / "selected_subsets.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("run_mode") != "full":
            continue
        history = entry["history"]
        steps = [s for s in history if s["improvement"] is not None]
        records.append({
            "classifier": entry["classifier"], "outer_fold": entry["outer_fold"],
            "inner_best_single": history[0]["inner_f1"], "k": len(entry["gfs"]),
            "blind_steps": sum(1 for s in steps if s["improvement"] == 0.0),
            "steps": len(steps),
            "subset": "+".join(entry["gfs"]),
        })
    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path,
                        default=REPO / "results/extensions/kth_tips2b/oracle_matched")
    parser.add_argument("--corrected", type=Path,
                        default=REPO / "results/extensions/kth_tips2b/inner_group_sample")
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/analysis/inner_grouping")
    args = parser.parse_args()

    do, dc = diagnostics(args.original), diagnostics(args.corrected)
    oo, oc = outcomes(args.original), outcomes(args.corrected)
    keys = ["classifier", "outer_fold"]

    print("DIAGNOSTICO DEL CRITERIO INTERNO")
    print(f"{'clasif':<9}{'grupo':<12}{'inner medio':>13}{'k medio':>10}"
          f"{'pasos ciegos':>15}")
    diag_rows = []
    for clf in ("svm", "resmlp"):
        for label, frame in (("imagen", do), ("muestra", dc)):
            sub = frame[frame["classifier"].eq(clf)]
            if sub.empty:
                continue
            blind = sub["blind_steps"].sum(), sub["steps"].sum()
            print(f"{clf:<9}{label:<12}{sub['inner_best_single'].mean():>13.4f}"
                  f"{sub['k'].mean():>10.2f}{blind[0]:>10}/{blind[1]:<4}")
            diag_rows.append({"classifier": clf, "grouping": label,
                              "inner_mean": float(sub["inner_best_single"].mean()),
                              "k_mean": float(sub["k"].mean()),
                              "blind_steps": int(blind[0]), "steps": int(blind[1])})

    print("\nMACRO-F1 EXTERNO MEDIO POR ESTRATEGIA")
    print(f"{'clasif':<9}{'estrategia':<13}{'original':>11}{'corregido':>12}{'delta':>10}")
    effect_rows = []
    for clf in ("svm", "resmlp"):
        for method in ORDER:
            a = oo[oo["classifier"].eq(clf) & oo["method"].eq(method)]["macro_f1"]
            b = oc[oc["classifier"].eq(clf) & oc["method"].eq(method)]["macro_f1"]
            if a.empty or b.empty:
                continue
            print(f"{clf:<9}{LABELS[method]:<13}{a.mean():>11.4f}{b.mean():>12.4f}"
                  f"{b.mean() - a.mean():>+10.4f}")
            effect_rows.append({"classifier": clf, "method": method,
                                "original": float(a.mean()), "corrected": float(b.mean()),
                                "delta": float(b.mean() - a.mean())})
        print()

    print("CONTRASTES CLAVE (media sobre particiones; victorias entre parentesis)")
    contrast_rows = []
    for clf in ("svm", "resmlp"):
        for left, right in (("gfs", "best_individual"), ("gfs", "full_concat"),
                            ("full_concat", "best_individual")):
            line = [f"{clf:<7}{LABELS[left]:>11} vs {LABELS[right]:<12}"]
            entry = {"classifier": clf, "left": left, "right": right}
            for tag, frame in (("original", oo), ("corrected", oc)):
                piv = frame[frame["classifier"].eq(clf)].pivot_table(
                    index="outer_fold", columns="method", values="macro_f1")
                if left not in piv or right not in piv:
                    continue
                delta = piv[left] - piv[right]
                line.append(f"{tag}: {delta.mean():+.4f} ({int((delta > 0).sum())}/{len(delta)})")
                entry[f"{tag}_delta"] = float(delta.mean())
                entry[f"{tag}_wins"] = int((delta > 0).sum())
                entry["n"] = int(len(delta))
            print("   " + "   ".join(line))
            contrast_rows.append(entry)

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "inner_grouping_effect.json").write_text(
        json.dumps({"diagnostics": diag_rows, "effects": effect_rows,
                    "contrasts": contrast_rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    pd.DataFrame(effect_rows).to_csv(args.output / "inner_grouping_effect.csv", index=False)
    print(f"\nescrito en {args.output}")


if __name__ == "__main__":
    main()
