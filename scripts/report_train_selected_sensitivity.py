#!/usr/bin/env python3
"""Post-hoc sensitivity of training-only tolerance, without refitting models.

All tolerances are compared after inspecting outer-test outcomes. This output
must not be presented as independent validation or used to pick a winning
tolerance for the current test partitions.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
DEFAULT = REPO / "results/exploratory/topk_cascade/train_selected_primary22"
TOLERANCES = (0.0, 0.0025, 0.005, 0.01)


def evaluate_tolerance(record: dict, archive: dict, tolerance: float) -> dict:
    selection = record["selection"]
    baseline = selection["oof_topk_macro_f1"]
    eligible = [row for row in selection["candidates"]
                if row["oof_macro_f1"] >= baseline - tolerance - 1e-12]
    chosen = min(eligible, key=lambda row: (row["projected_component_ms"],
                                           row["route"] != "topk_direct"))
    if chosen["route"] == "topk_direct":
        test_f1 = float(archive["topk_always"]["macro_f1"])
        cost = selection["topk_direct_component_ms"]
    else:
        budget_row = next(row for row in archive["budgets"]
                          if row["target_budget"] == chosen["budget"])
        test_f1 = float(budget_row["adaptive"]["macro_f1"])
        cost = (selection["base_component_ms"]
                + float(budget_row["observed_request_fraction"])
                * selection["incremental_component_ms"])
    return {"dataset": record["dataset"], "protocol": record["protocol"],
            "tolerance": tolerance, "route": chosen["route"],
            "budget": chosen["budget"], "oof_gap": chosen["oof_macro_f1"] - baseline,
            "test_f1": test_f1,
            "test_topk_f1": float(archive["topk_always"]["macro_f1"]),
            "component_ms": cost,
            "topk_component_ms": selection["topk_direct_component_ms"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path, default=DEFAULT / "sensitivity")
    args = parser.parse_args()
    paths = sorted(args.input.glob("*_selection.json"))
    if len(paths) != 27:
        raise ValueError(f"expected 27 selected conditions, found {len(paths)}")
    rows = []
    for path in paths:
        record = json.loads(path.read_text(encoding="utf-8"))
        archive = json.loads(Path(record["source_archive"]["path"]).read_text(encoding="utf-8"))
        for tolerance in TOLERANCES:
            rows.append(evaluate_tolerance(record, archive, tolerance))
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "tolerance_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summaries = []
    for dataset in sorted({row["dataset"] for row in rows}):
        for tolerance in TOLERANCES:
            subset = [row for row in rows if row["dataset"] == dataset
                      and row["tolerance"] == tolerance]
            mean_cost = float(np.mean([row["component_ms"] for row in subset]))
            mean_topk_cost = float(np.mean([row["topk_component_ms"] for row in subset]))
            gaps = [row["test_f1"] - row["test_topk_f1"] for row in subset]
            summaries.append({"dataset": dataset, "tolerance": tolerance,
                              "conditions": len(subset),
                              "cascade_selections": sum(row["route"] == "cascade" for row in subset),
                              "mean_test_f1_gap": float(np.mean(gaps)),
                              "worst_test_f1_gap": float(min(gaps)),
                              "mean_component_saving_fraction": 1 - mean_cost / mean_topk_cost})
    (args.output / "tolerance_summary.json").write_text(json.dumps({
        "status": "EXPLORATORY_POSTHOC_SENSITIVITY_NOT_INDEPENDENT_VALIDATION",
        "tolerances": TOLERANCES, "summaries": summaries,
        "warning": "Tolerance comparison uses already-inspected outer-test results; do not select a final tolerance on these same partitions."
    }, indent=2) + "\n", encoding="utf-8")
    for row in summaries:
        print(f"{row['dataset']:<22} tol={row['tolerance']:.4f} "
              f"cascade={row['cascade_selections']}/{row['conditions']} "
              f"mean ΔF1={row['mean_test_f1_gap']:+.4f} "
              f"worst={row['worst_test_f1_gap']:+.4f} "
              f"cost saving={row['mean_component_saving_fraction']:.1%}")


if __name__ == "__main__":
    main()
