#!/usr/bin/env python3
"""Summarise the exact-archive Top-k cascade experiment.

This reporter intentionally keeps the four KTH-TIPS2-b official partitions
separate in the CSV. Their aggregate is descriptive: the partitions overlap,
so it is not an independent-sample estimate or a hypothesis test.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def load(root: Path) -> pd.DataFrame:
    records = []
    for path in sorted(root.glob("*_topk_cascade.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        if entry["expensive_subset_derived_locally"]:
            raise ValueError(f"{path} derives a Top-k subset locally; exact archive required")
        if abs(float(entry["reproduction_delta"])) > 1e-10:
            raise ValueError(f"{path} does not reproduce its archived Top-k score")
        for row in entry["budgets"]:
            records.append({
                "protocol": entry["protocol"],
                "outer_fold": entry["outer_fold"],
                "cheap_blocks": "+".join(entry["cheap_blocks"]),
                "expensive_blocks": "+".join(entry["expensive_blocks"]),
                "cheap_f1": entry["cheap_only"]["macro_f1"],
                "topk_f1": entry["topk_always"]["macro_f1"],
                "archived_topk_f1": entry["archived_topk_macro_f1"],
                "reproduction_delta": entry["reproduction_delta"],
                "target": row["target_budget"],
                "requested": row["observed_request_fraction"],
                "adaptive_f1": row["adaptive"]["macro_f1"],
                "random_f1": row["random_same_count_mean_macro_f1"],
                "random_f1_sd": row["random_same_count_sd_macro_f1"],
                "gap_to_topk": row["gap_to_topk_always"],
                "estimated_extract_ms": (row.get("cost_model") or {}).get("mean_cost_ms"),
            })
    if not records:
        raise FileNotFoundError(f"no exact cascade results under {root}")
    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=REPO / "results/exploratory/topk_cascade/kth_tips2b/exact_archive")
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/exploratory/topk_cascade/kth_tips2b")
    args = parser.parse_args()

    frame = load(args.root)
    protocols = frame.drop_duplicates("protocol").sort_values("outer_fold")
    print("REPRODUCCION EXACTA DE LA ETAPA TOP-K ARCHIVADA")
    print(f"  {'particion':<22}{'bloques Top-k':<34}{'archivado':>11}{'reproducido':>13}{'delta':>12}")
    for _, row in protocols.iterrows():
        print(f"  {row['protocol']:<22}{row['expensive_blocks']:<34}"
              f"{row['archived_topk_f1']:>11.4f}{row['topk_f1']:>13.4f}"
              f"{row['reproduction_delta']:>+12.2e}")

    print("\nRESULTADO DESCRIPTIVO (media de cuatro particiones oficiales)")
    print(f"  {'objetivo':>9}{'pedido':>9}{'adaptativa':>12}{'Top-k siempre':>15}"
          f"{'aleatoria':>11}{'vs Top-k':>11}{'vs aleatoria':>14}{'extrac. est.':>15}")
    effects = []
    for target, block in frame.groupby("target", sort=True):
        entry = {
            "target": float(target),
            "requested": float(block["requested"].mean()),
            "adaptive": float(block["adaptive_f1"].mean()),
            "topk_always": float(block["topk_f1"].mean()),
            "random": float(block["random_f1"].mean()),
            "estimated_extract_ms": float(block["estimated_extract_ms"].mean()),
            "n_partitions": int(len(block)),
        }
        entry["vs_topk"] = entry["adaptive"] - entry["topk_always"]
        entry["vs_random"] = entry["adaptive"] - entry["random"]
        effects.append(entry)
        print(f"  {entry['target']:>9.2f}{entry['requested']:>9.1%}{entry['adaptive']:>12.4f}"
              f"{entry['topk_always']:>15.4f}{entry['random']:>11.4f}"
              f"{entry['vs_topk']:>+11.4f}{entry['vs_random']:>+14.4f}"
              f"{entry['estimated_extract_ms']:>14.1f} ms")
    print(f"  solo etapa barata: {frame['cheap_f1'].mean():.4f}")

    args.output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output / "topk_cascade_rows.csv", index=False)
    summary = {
        "scope": "KTH-TIPS2-b, SVM, four official inverted partitions",
        "exact_archived_topk_required": True,
        "mean_abs_reproduction_delta": float(frame["reproduction_delta"].abs().mean()),
        "cheap_only_mean_macro_f1": float(frame["cheap_f1"].mean()),
        "effects_descriptive": effects,
        "caveats": [
            "The four KTH-TIPS2-b partitions overlap; means are descriptive, not inferential.",
            "This is a cached-embedding prediction simulation, not an end-to-end latency measurement.",
            "All images execute the cheap stage before escalation; timing must measure incremental stage cost.",
            "The adaptive predictor can exceed the always-Top-k stage because it retains cheap predictions for non-escalated images.",
        ],
    }
    (args.output / "topk_cascade_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nescrito en {args.output}")


if __name__ == "__main__":
    main()
