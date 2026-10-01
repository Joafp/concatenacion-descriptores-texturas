#!/usr/bin/env python3
"""Aggregate the Top-k cascade runs and contrast the two inner groupings.

The escalation threshold is a quantile of training margins, so the inner folds
have to pose the same task as the external test.  This report shows what that
choice costs: how far the observed request fraction lands from the target
budget, and how much external macro-F1 the rule retains against always paying
for the Top-k route and against a random control that escalates the same number
of images.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def load(root: Path, grouping: str) -> pd.DataFrame:
    records = []
    for path in sorted(root.glob("*_topk_cascade.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        for row in entry["budgets"]:
            records.append({
                "grouping": grouping,
                "protocol": entry["protocol"],
                "cheap_f1": entry["cheap_only"]["macro_f1"],
                "topk_f1": entry["topk_always"]["macro_f1"],
                "archived_topk_f1": entry["archived_topk_macro_f1"],
                "reproduction_delta": entry["reproduction_delta"],
                "derived": entry["expensive_subset_derived_locally"],
                "expensive_blocks": "+".join(entry["expensive_blocks"]),
                "target": row["target_budget"],
                "requested": row["observed_request_fraction"],
                "adaptive_f1": row["adaptive"]["macro_f1"],
                "random_f1": row["random_same_count_mean_macro_f1"],
                "gap_to_topk": row["gap_to_topk_always"],
            })
    if not records:
        raise FileNotFoundError(f"no cascade results under {root}")
    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path,
                        default=REPO / "results/exploratory/topk_cascade/kth_tips2b")
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/exploratory/topk_cascade/kth_tips2b")
    args = parser.parse_args()

    frame = pd.concat([load(args.root / "group_image", "imagen"),
                       load(args.root / "group_sample", "muestra")],
                      ignore_index=True)

    print("REPRODUCCION DE LA ETAPA CARA (Top-k archivado vs. reproducido)")
    seen = frame.drop_duplicates(["grouping", "protocol"])
    seen = seen[seen["grouping"].eq("muestra")]
    print(f"  {'particion':<22}{'bloques elegidos':<30}{'archivado':>11}"
          f"{'reproducido':>13}{'delta':>9}  derivado")
    for _, row in seen.iterrows():
        print(f"  {row['protocol']:<22}{row['expensive_blocks']:<30}"
              f"{row['archived_topk_f1']:>11.4f}{row['topk_f1']:>13.4f}"
              f"{row['reproduction_delta']:>+9.4f}  {row['derived']}")
    print(f"  delta absoluto medio: {frame['reproduction_delta'].abs().mean():.4f}")

    print("\nCONTROL DEL PRESUPUESTO: fraccion pedida frente al objetivo")
    print(f"  {'objetivo':>9}{'imagen':>12}{'muestra':>12}{'error imagen':>15}"
          f"{'error muestra':>15}")
    budget_rows = []
    for target, block in frame.groupby("target"):
        per = block.groupby("grouping")["requested"].mean()
        err = {g: abs(per[g] - target) for g in per.index}
        print(f"  {target:>9.2f}{per['imagen']:>12.1%}{per['muestra']:>12.1%}"
              f"{err['imagen']:>15.1%}{err['muestra']:>15.1%}")
        budget_rows.append({"target": float(target),
                            "requested_image": float(per["imagen"]),
                            "requested_sample": float(per["muestra"]),
                            "abs_error_image": float(err["imagen"]),
                            "abs_error_sample": float(err["muestra"])})
    mean_err = {g: float(np.mean([abs(r[f"requested_{k}"] - r["target"])
                                 for r in budget_rows]))
                for g, k in (("imagen", "image"), ("muestra", "sample"))}
    print(f"  error absoluto medio: imagen {mean_err['imagen']:.1%}, "
          f"muestra {mean_err['muestra']:.1%}")

    print("\nACIERTO Y COSTO (agrupamiento por muestra, media de 4 particiones)")
    print(f"  {'objetivo':>9}{'pedido':>9}{'adaptativa':>12}{'Top-k siempre':>15}"
          f"{'aleatoria':>11}{'vs Top-k':>10}{'vs aleatoria':>14}")
    effect_rows = []
    sample = frame[frame["grouping"].eq("muestra")]
    for target, block in sample.groupby("target"):
        entry = {
            "target": float(target),
            "requested": float(block["requested"].mean()),
            "adaptive": float(block["adaptive_f1"].mean()),
            "topk_always": float(block["topk_f1"].mean()),
            "random": float(block["random_f1"].mean()),
            "n_partitions": int(len(block)),
        }
        entry["vs_topk"] = entry["adaptive"] - entry["topk_always"]
        entry["vs_random"] = entry["adaptive"] - entry["random"]
        print(f"  {target:>9.2f}{entry['requested']:>9.1%}{entry['adaptive']:>12.4f}"
              f"{entry['topk_always']:>15.4f}{entry['random']:>11.4f}"
              f"{entry['vs_topk']:>+10.4f}{entry['vs_random']:>+14.4f}")
        effect_rows.append(entry)
    print(f"  solo etapa barata: {sample['cheap_f1'].mean():.4f}")

    args.output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output / "topk_cascade_rows.csv", index=False)
    (args.output / "topk_cascade_summary.json").write_text(
        json.dumps({"budget_control": budget_rows,
                    "mean_abs_budget_error": mean_err,
                    "effects_sample_grouping": effect_rows,
                    "cheap_only_mean_macro_f1": float(sample["cheap_f1"].mean()),
                    "mean_abs_reproduction_delta":
                        float(frame["reproduction_delta"].abs().mean()),
                    "caveats": [
                        "Four partitions of one dataset; descriptive only.",
                        "The Top-k subset was re-derived from the locally "
                        "available library in three of four partitions because "
                        "beitv2_base_final is absent, so the composition differs "
                        "from the manuscript.",
                        "No route cost is reported: the measured 345.59 ms Top-k "
                        "route belongs to Outex's eight-block subset and does not "
                        "transfer to these one- and two-block subsets.",
                    ]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nescrito en {args.output}")


if __name__ == "__main__":
    main()
