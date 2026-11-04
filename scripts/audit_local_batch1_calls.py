"""Independently reaggregate online F1 and times; no new timing or model fits."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    import joblib
    import numpy as np
    import pandas as pd
    from batch1_call_audit import summarize_calls

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online-run", type=Path, required=True)
    parser.add_argument("--quality-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    status = json.loads((args.online_run / "status.json").read_text())
    if status["status"] != "batch1_online_f1_and_timing_complete":
        raise ValueError("online execution incomplete")
    if digest(args.quality_run / "status.json") != status["quality_status_sha256"]:
        raise ValueError("quality reference drift")
    quality_status = json.loads((args.quality_run / "status.json").read_text())
    if digest(args.quality_run / "fitted_heads.joblib") != quality_status["output_sha256"]["fitted_heads.joblib"]:
        raise ValueError("frozen model drift")
    for name, expected in status["output_sha256"].items():
        if digest(args.online_run / name) != expected:
            raise ValueError(f"online output drift: {name}")
    heads = joblib.load(args.quality_run / "fitted_heads.joblib")
    archived = pd.read_csv(args.quality_run / "predictions.csv")
    ground_truth = archived.drop_duplicates("row_index").set_index("row_index").label.to_dict()
    calls = pd.read_csv(args.online_run / "online_calls.csv")
    recomputed = summarize_calls(calls, heads["recipes"], status["rows"], ground_truth, heads["labels"], status["repeats"])
    recorded = pd.read_csv(args.online_run / "online_summary.csv").set_index("policy")
    for row in recomputed.to_dict("records"):
        for key, value in row.items():
            if key != "policy" and not np.isclose(value, recorded.loc[row["policy"], key], rtol=0, atol=1e-10):
                raise ValueError(f"summary mismatch: {row['policy']}/{key}")
    args.output.mkdir(parents=True, exist_ok=False)
    recomputed.to_csv(args.output / "recomputed_summary.csv", index=False)
    report = {"status": "ONLINE_CALL_RECORDS_REAGGREGATED", "source_status_sha256": digest(args.online_run / "status.json"),
        "call_rows": len(calls), "unique_images": int(calls.row_index.nunique()), "methods": len(recomputed),
        "source_sha256": digest(__file__), "quality_and_time_from_same_calls": True,
        "archive_feature_parity_claimed": False,
        "limitation": "checks recorded calls and arithmetic; not independent hardware timing or an isolated benchmark"}
    (args.output / "audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(recomputed.to_string(index=False))
