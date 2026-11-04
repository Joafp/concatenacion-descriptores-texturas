"""Join all three completed FMD seeds with their audited hybrid references.

Descriptive partial-panel report: explicitly retains the Outex timeouts and all
44 policy variants per FMD seed. No new models or inferential tests are run.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDS = ("FMD_s42", "FMD_s123", "FMD_s2026")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_record(path):
    record = json.loads(path.read_text())
    assert record["status"] == "ANALYZED"
    for file, expected in record["input_sha256"].items():
        assert digest(ROOT / file) == expected, file
    return record


def build(output):
    if output.exists():
        raise FileExistsError(output)
    analysis = ROOT / "results/analysis/matched_concat_20261026"
    reference = ROOT / "results/analysis/mesa_replication_20261026"
    suite = ROOT / "results/exploratory/integration_v12/matched_concat_20261026"
    summary = json.loads((analysis / "summary.json").read_text())
    assert {c["condition"] for c in summary["conditions"] if c["status"] == "audited"} >= set(IDS)
    rows, inputs = [], [analysis / "summary.json", reference / "summary.json", Path(__file__)]
    for condition in IDS:
        newpath, oldpath = analysis / f"{condition}.json", reference / f"{condition}.json"
        new, old = checked_record(newpath), checked_record(oldpath)
        meta_path = suite / condition / "controls/metadata.json"
        meta = json.loads(meta_path.read_text())
        ref = Path(meta["reference_run"])
        assert new["condition"]["seed"] == old["condition"]["seed"]
        assert new["condition"]["dataset"] == old["condition"]["dataset"] == "FMD"
        assert new["condition"]["expected_images"] == old["development_images"] == 800
        for fold in range(3):
            relative = str((ref / f"fold{fold}.json").relative_to(ROOT))
            assert meta["input_sha256"][relative] == old["input_sha256"][relative]
        inputs += [newpath, oldpath, meta_path]
        for row in new["metrics"]:
            rows.append({**row, "stage": "concat_control"})
        for row in old["metrics"]:
            rows.append({**row, "complete": True})
    frame = pd.DataFrame(rows)
    assert len(frame) == 132 and not frame.duplicated(["condition", "stage", "policy"]).any()
    assert frame.complete.all() and (frame.n == 800).all()
    means = frame.groupby(["dataset", "stage", "policy"], sort=True).agg(
        seeds=("seed", "nunique"), macro_f1=("macro_f1", "mean"),
        projected_ms=("projected_ms", "mean"), f1_min=("macro_f1", "min"),
        f1_max=("macro_f1", "max")).reset_index()
    assert len(means) == 44 and (means.seeds == 3).all()
    pairs = []
    for condition in IDS:
        part = frame[frame.condition == condition]
        for budget in (15, 30, 60, 120):
            h = part[(part.stage == "hybrid") & (part.policy == f"pruned_relevance_B{budget}")].iloc[0]
            comparators = [("static", f"static_B{budget}"),
                           ("concat_control", f"gfs_budget_B{budget}"),
                           ("concat_control", f"top_prefix_budget_B{budget}")]
            if budget == 60:
                comparators += [("concat_control", "gfs"), ("concat_control", "topk_gfs_size")]
            for stage, policy in comparators:
                control = part[(part.stage == stage) & (part.policy == policy)].iloc[0]
                pairs.append({"condition": condition, "budget": budget, "control": f"{stage}/{policy}",
                    "hybrid_macro_f1": h.macro_f1, "control_macro_f1": control.macro_f1,
                    "delta_macro_f1": h.macro_f1 - control.macro_f1,
                    "hybrid_projected_ms": h.projected_ms, "control_projected_ms": control.projected_ms,
                    "delta_projected_ms": h.projected_ms - control.projected_ms})
    failures = []
    for state in summary["conditions"]:
        if not state["condition"].startswith("Outex_"):
            continue
        path = suite / state["condition"] / "state.json"
        raw = json.loads(path.read_text())
        assert raw["status"] == "failed" and raw["timeout"] and raw["returncode"] == -15
        failures.append({"condition": state["condition"], "status": "timeout_no_final_metrics",
                         "elapsed_seconds": raw["elapsed_seconds"], "not_a_predictive_defeat": True})
        inputs.append(path)
    assert len(failures) == 3
    output.mkdir(parents=True)
    frame.to_csv(output / "all_policies.csv", index=False)
    means.to_csv(output / "dataset_means.csv", index=False)
    pd.DataFrame(pairs).to_csv(output / "paired_differences.csv", index=False)
    report = {"status": "PARTIAL", "scope": "Three FMD development seeds only; Outex concatenation controls timed out",
        "comparison_datasets": 1, "comparison_conditions": 3, "development_rows_per_condition": 800,
        "rows_are_not_unique_new_images": True, "policy_rows": len(frame), "mean_rows": len(means),
        "paired_differences": len(pairs), "outstanding_conditions": failures,
        "external_test_evaluated": False, "physical_latency_measured": False,
        "new_inferential_tests": 0,
        "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs},
        "output_sha256": {name: digest(output / name) for name in
                          ("all_policies.csv", "dataset_means.csv", "paired_differences.csv")}}
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("input_sha256", "output_sha256")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/analysis/matched_concat_20261026/comparison_fmd")
    args = parser.parse_args()
    build(args.output.resolve())
