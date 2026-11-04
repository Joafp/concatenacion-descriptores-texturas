import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_fmd_report_preserves_full_panel_and_timeout_limitations(tmp_path):
    if not (ROOT / "results/analysis/matched_concat_20261026/FMD_s2026.json").is_file():
        pytest.skip("local completed FMD controls unavailable")
    spec = importlib.util.spec_from_file_location("concat_report", ROOT / "scripts/report_matched_concat_fmd.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / "report"
    module.build(output)
    report = json.loads((output / "summary.json").read_text())
    assert report["comparison_datasets"] == 1 and report["comparison_conditions"] == 3
    assert report["policy_rows"] == 132 and report["mean_rows"] == 44
    assert len(report["outstanding_conditions"]) == 3
    assert all(c["status"] == "timeout_no_final_metrics" for c in report["outstanding_conditions"])
    assert not report["physical_latency_measured"] and report["new_inferential_tests"] == 0
    means = pd.read_csv(output / "dataset_means.csv")
    gfs = means[(means.stage == "concat_control") & (means.policy == "gfs")].iloc[0]
    assert gfs.macro_f1 == pytest.approx(.975409895619907, abs=1e-12)
    differences = pd.read_csv(output / "paired_differences.csv")
    loss = differences[(differences.condition == "FMD_s42") & (differences.control == "static/static_B60")].iloc[0]
    assert loss.delta_macro_f1 < 0 and loss.delta_projected_ms > 0
