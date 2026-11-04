import importlib.util
import json
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/overnight_multidataset_online.py"
    spec = importlib.util.spec_from_file_location("supplement_online_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_wrong_fmd_count_refused():
    with pytest.raises(ValueError, match="thirty"):
        module().fmd_closed({"jobs": []})


def test_missing_fmd_audit_never_releases_gpu(tmp_path):
    jobs = [{"dataset": "FMD", "online_run": str(tmp_path / f"run{i}"),
             "online_audit": str(tmp_path / f"audit{i}")} for i in range(30)]
    assert not module().fmd_closed({"jobs": jobs})


def fmd_panel(tmp_path, stale=False):
    mod, jobs = module(), []
    for i in range(30):
        run, audit = tmp_path / f"run{i}", tmp_path / f"audit{i}"
        run.mkdir(); audit.mkdir()
        mod.write(run / "status.json", {"status": "batch1_online_f1_and_timing_complete"})
        mod.write(audit / "audit.json", {"status": "ONLINE_CALL_RECORDS_REAGGREGATED",
            "source_status_sha256": "bad" if stale and i == 29 else mod.digest(run / "status.json")})
        jobs.append({"dataset": "FMD", "online_run": str(run), "online_audit": str(audit)})
    return mod, {"jobs": jobs}


def test_only_thirty_complete_audited_fmd_conditions_release_gate(tmp_path):
    mod, manifest = fmd_panel(tmp_path)
    assert mod.fmd_closed(manifest)


def test_stale_fmd_audit_does_not_release_gate(tmp_path):
    mod, manifest = fmd_panel(tmp_path, stale=True)
    assert not mod.fmd_closed(manifest)


def test_missing_quality_waits_without_launching(tmp_path):
    assert not module().quality_ready({"quality_run": str(tmp_path / "q"), "quality_audit": str(tmp_path / "a")})


def test_quality_must_have_replay_bound_to_status(tmp_path):
    mod = module()
    q, a = tmp_path / "q", tmp_path / "a"
    q.mkdir(); a.mkdir()
    mod.write(q / "status.json", {"status": "external_quality_complete_timing_pending"})
    mod.write(a / "audit.json", {"status": "CACHED_HEAD_PREDICTIONS_REPLAYED", "source_status_sha256": "bad"})
    job = {"quality_run": str(q), "quality_audit": str(a)}
    assert not mod.quality_ready(job)
    mod.write(a / "audit.json", {"status": "CACHED_HEAD_PREDICTIONS_REPLAYED", "source_status_sha256": mod.digest(q / "status.json")})
    assert mod.quality_ready(job)
