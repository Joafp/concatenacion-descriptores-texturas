"""Reaggregate reference F1 and write an explicit, unfilled latency coverage ledger."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from local_comparison_audit import audit

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report, conditions, coverage = audit(ROOT)
    args.output.mkdir(parents=True, exist_ok=False)
    conditions.to_csv(args.output / "reference_conditions.csv", index=False)
    coverage.to_csv(args.output / "coverage.csv", index=False)
    (args.output / "audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "reference_condition_rows": len(conditions),
        "coverage_cells": len(coverage), "missing_latency_cells": int(coverage.measured_ms_per_image.isna().sum()),
        "recipe_records": len(report["recipe_library_audit"]), "physical_latency_published": False}, indent=2))
