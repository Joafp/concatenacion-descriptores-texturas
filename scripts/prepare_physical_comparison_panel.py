"""Prepare immutable development timing recipes; no GPU, fitting or timing."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from physical_comparison_panel import build


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    args = p.parse_args()
    report = build(ROOT, args.output, args.protocol)
    print(json.dumps({"status": report["status"], "conditions": len(report["conditions"]),
                      "folds": sum(len(c["folds"]) for c in report["conditions"]),
                      "recipes": sum(len(f["recipes"]) for c in report["conditions"] for f in c["folds"]),
                      "physical_latency_published": False}, indent=2))
