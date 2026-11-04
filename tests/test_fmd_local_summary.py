import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import pandas as pd


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/summarize_fmd_local_seed42.py"
    spec = importlib.util.spec_from_file_location("fmd_summary_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_refuses_incomplete_queue_without_creating_output(tmp_path):
    followup = tmp_path / "followup"
    followup.mkdir()
    (followup / "queue_status.json").write_text(json.dumps({"status": "running", "completed": [1, 2]}))
    args = SimpleNamespace(followup=followup, output=tmp_path / "out")
    with pytest.raises(ValueError, match="incomplete"):
        module().summarize(args)
    assert not args.output.exists()


def make_complete_panel(tmp_path, repeat=False):
    mod = module()
    followup = tmp_path / "followup"
    followup.mkdir()
    (followup / "queue_status.json").write_text(json.dumps({"status": "complete_quality_and_replay", "completed": [1, 2, 3, 4]}))
    args = SimpleNamespace(followup=followup, pilot=tmp_path / "pilot",
        pilot_audit=tmp_path / "pilot_audit", classifier="svm", output=tmp_path / "out")
    policies = ["Completa-22", "Top-4", "Ens-diversidad", "Ens-tombola", "Adaptive-selection-margin"]
    for fold in range(5):
        folder = args.pilot if fold == 0 else followup / f"fold{fold}"
        audit = args.pilot_audit if fold == 0 else followup / f"fold{fold}_audit"
        folder.mkdir()
        audit.mkdir()
        records = []
        for policy in policies:
            for idx in range(fold * 200, (fold + 1) * 200):
                row = 0 if repeat and fold == 1 and idx == 200 else idx
                records.append({"policy": policy, "row_index": row, "label": row % 10,
                    "prediction": row % 10, "escalated": False})
        pd.DataFrame(records).to_csv(folder / "predictions.csv", index=False)
        pd.DataFrame([{"policy": p, "macro_f1": 1.} for p in policies]).to_csv(folder / "metrics.csv", index=False)
        status = {"status": "external_quality_complete_timing_pending", "dataset": "FMD",
            "seed": 42, "outer_fold": fold, "classifier": "svm",
            "output_sha256": {p: mod.digest(folder / p) for p in ["predictions.csv", "metrics.csv"]}}
        (folder / "status.json").write_text(json.dumps(status))
        (audit / "audit.json").write_text(json.dumps({"status": "CACHED_HEAD_PREDICTIONS_REPLAYED",
            "source_status_sha256": mod.digest(folder / "status.json")}))
    return mod, args


def test_complete_seed_is_not_promoted_to_all_three_seeds(tmp_path):
    mod, args = make_complete_panel(tmp_path)
    mod.summarize(args)
    result = json.loads((args.output / "summary.json").read_text())
    assert result["all_three_fmd_seeds_complete"] is False
    assert result["physical_latency_published"] is False
    assert all(m["conditions"] == 5 and m["external_rows"] == 1000 for m in result["methods"])
    assert all(m["mean_fold_macro_f1"] == 1 and m["pooled_macro_f1"] == 1 for m in result["methods"])


def test_repeated_test_images_are_rejected(tmp_path):
    mod, args = make_complete_panel(tmp_path, repeat=True)
    with pytest.raises(ValueError, match="repeat images"):
        mod.summarize(args)
    assert not args.output.exists()
