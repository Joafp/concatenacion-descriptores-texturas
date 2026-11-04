"""Join completed matched controls without rewriting original timeout records."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FMD = ROOT / "results/analysis/matched_concat_20261026"
OUTEX = ROOT / "results/analysis/matched_concat_outex_retry_20261026/audit"
HYBRID = ROOT / "results/analysis/mesa_replication_20261026"
IDS = ("FMD_s42", "FMD_s123", "FMD_s2026", "Outex_s123", "Outex_s2026")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(path):
    record = json.loads(path.read_text())
    assert record["status"] == "ANALYZED", path
    for name, expected in record["input_sha256"].items():
        assert digest(ROOT / name) == expected, name
    return record


def aggregate(frame):
    """Never summarize only the feasible seeds as a complete policy result."""
    result = []
    expected = frame.groupby("dataset").seed.nunique().to_dict()
    for (dataset, stage, policy), part in frame.groupby(["dataset", "stage", "policy"]):
        valid = part.complete & part.macro_f1.notna() & part.projected_ms.notna()
        complete = bool(valid.all() and part.seed.nunique() == expected[dataset])
        result.append({"dataset": dataset, "stage": stage, "policy": policy,
            "expected_seeds": expected[dataset], "complete_seeds": int(part[valid].seed.nunique()),
            "complete": complete, "macro_f1": part.macro_f1.mean() if complete else None,
            "projected_ms": part.projected_ms.mean() if complete else None,
            "f1_min": part.macro_f1.min() if complete else None,
            "f1_max": part.macro_f1.max() if complete else None})
    return pd.DataFrame(result)


def build(output):
    if output.exists():
        raise FileExistsError(output)
    rows, sources = [], [Path(__file__)]
    for condition in IDS:
        base = FMD if condition.startswith("FMD") else OUTEX
        cp, hp = base / f"{condition}.json", HYBRID / f"{condition}.json"
        concat, hybrid = checked(cp), checked(hp)
        meta_paths = [name for name in concat["input_sha256"] if name.endswith("/controls/metadata.json")]
        assert len(meta_paths) == 1
        concat_meta = json.loads((ROOT / meta_paths[0]).read_text())
        assert concat["condition"]["seed"] == hybrid["condition"]["seed"]
        assert concat["condition"]["dataset"] == hybrid["condition"]["dataset"]
        for name, expected in hybrid["input_sha256"].items():
            if name.endswith(("/paired/fold0.json", "/paired/fold1.json", "/paired/fold2.json")):
                assert concat_meta["input_sha256"][name] == expected, name
        rows += [{**row, "stage": "concat_control"} for row in concat["metrics"]]
        rows += [{**row, "complete": True} for row in hybrid["metrics"]]
        sources += [cp, hp]
    frame = pd.DataFrame(rows)
    assert len(frame) == 220 and not frame.duplicated(["condition", "stage", "policy"]).any()
    means = aggregate(frame)
    assert len(means) == 88
    pilot_path = OUTEX / "Outex_s42.json"
    pilot = checked(pilot_path)
    sources += [pilot_path]
    output.mkdir(parents=True)
    frame.to_csv(output / "all_policies.csv", index=False)
    means.to_csv(output / "dataset_means.csv", index=False)
    pd.DataFrame(pilot["metrics"]).to_csv(output / "outex42_concat_pilot.csv", index=False)
    report = {"status": "ANALYZED", "scope": "Development comparison, FMD three seeds and Outex two new seeds; historical Outex42 concatenation controls separately retained",
        "concat_conditions_audited": 6, "joined_conditions": 5, "datasets": 2,
        "seed_counts": {"FMD": 3, "Outex13Official1360": 2},
        "policy_rows": len(frame), "mean_rows": len(means),
        "incomplete_policy_means": int((~means.complete).sum()),
        "original_timeouts_preserved": True, "external_test_evaluated": False,
        "physical_timing": False, "new_inferential_tests": 0,
        "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sources},
        "output_sha256": {name: digest(output / name) for name in
            ("all_policies.csv", "dataset_means.csv", "outex42_concat_pilot.csv")}}
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if not k.endswith("sha256")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/analysis/matched_concat_panel_20261026")
    build(parser.parse_args().output.resolve())
