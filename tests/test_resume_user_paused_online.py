import importlib.util
from pathlib import Path


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/resume_user_paused_online.py"
    spec = importlib.util.spec_from_file_location("paused_resume_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(tmp_path):
    mod = module()
    mod.write(tmp_path / "worker.json", {"status": "running", "current_job": "partial", "completed": []})
    mod.write(tmp_path / "manifest.json", {"jobs": []})
    receipt = tmp_path / "user_pause.json"
    data = dict(status="user_requested_stop", resume_scope="never_dispatched_only",
                worker_sha256=mod.digest(tmp_path / "worker.json"),
                manifest_sha256=mod.digest(tmp_path / "manifest.json"),
                interrupted_job="partial", retry_interrupted=False)
    mod.write(receipt, data)
    return mod, receipt, data


def test_valid_pause_receipt_allows_only_untried_scope(tmp_path):
    mod, receipt, _ = fixture(tmp_path)
    assert mod.previous_terminal_or_user_paused(tmp_path, receipt)
    assert not mod.previous_terminal_or_user_paused(tmp_path)


def test_receipt_rejects_drift_and_retry_authority(tmp_path):
    mod, receipt, data = fixture(tmp_path)
    data["retry_interrupted"] = True
    mod.write(receipt, data)
    assert not mod.previous_terminal_or_user_paused(tmp_path, receipt)
    data["retry_interrupted"] = False
    data["manifest_sha256"] = "wrong"
    mod.write(receipt, data)
    assert not mod.previous_terminal_or_user_paused(tmp_path, receipt)


def test_partial_and_failed_marker_never_eligible(tmp_path):
    mod = module()
    job = dict(job_dir=str(tmp_path / "job"), online_run=str(tmp_path / "online"),
               online_audit=str(tmp_path / "audit"))
    assert mod.eligible(job)
    Path(job["online_run"]).mkdir()
    assert not mod.eligible(job)


def test_normal_finished_worker_remains_supported(tmp_path):
    mod = module()
    mod.write(tmp_path / "worker.json", {"status": "dispatch_window_ended"})
    assert mod.previous_terminal_or_user_paused(tmp_path)
