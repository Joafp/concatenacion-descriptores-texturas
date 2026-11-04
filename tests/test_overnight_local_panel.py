import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/overnight_local_panel.py"
    spec = importlib.util.spec_from_file_location("night_panel_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_zero_dispatch_window_runs_nothing(tmp_path, monkeypatch):
    mod = module()
    mod.write(tmp_path / "manifest.json", {"jobs": [], "source_sha256": {}})
    calls = []
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: calls.append(a))
    mod.worker(tmp_path, "quality", 0)
    state = mod.read(tmp_path / "worker_quality.json")
    assert state["status"] == "dispatch_window_ended" and calls == []


def test_lock_prevents_second_worker(tmp_path):
    import fcntl
    mod = module()
    mod.write(tmp_path / "manifest.json", {"jobs": [], "source_sha256": {}})
    with (tmp_path / "quality.lock").open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(SystemExit, match="already exists"):
            mod.worker(tmp_path, "quality", 0)
    assert not (tmp_path / "worker_quality.json").exists()


def test_failure_is_marked_without_retry_or_audit(tmp_path, monkeypatch):
    mod = module()
    config = tmp_path / "config.json"
    config.write_text("{}")
    job_dir = tmp_path / "job"
    job_dir.mkdir()
    job = {"id": "FMD_svm_s123_f0", "quality_external_managed": False, "quality_hold": None,
        "job_dir": str(job_dir), "quality_run": str(job_dir / "quality"), "quality_audit": str(job_dir / "audit"),
        "config": str(config), "config_sha256": mod.digest(config), "classifier": "svm",
        "quality_timeout_seconds": 1, "replay_timeout_seconds": 1}
    mod.write(tmp_path / "manifest.json", {"jobs": [job], "source_sha256": {}})
    times = iter([0, 0, 4000])
    monkeypatch.setattr(mod.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(mod, "alive", lambda pid: False)
    calls = []
    monkeypatch.setattr(mod.subprocess, "run", lambda cmd, **kw:
        calls.append(cmd) or SimpleNamespace(returncode=13))
    mod.worker(tmp_path, "quality", 1)
    assert len(calls) == 1
    state = mod.read(job_dir / "quality_state.json")
    assert state["status"] == "requires_review" and state["exit_code"] == 13
    assert not (job_dir / "quality_audit.log").exists()


def test_atomic_state_writer_preserves_json(tmp_path):
    mod = module()
    path = tmp_path / "state.json"
    mod.write(path, {"status": "running"})
    mod.write(path, {"status": "complete"})
    assert json.loads(path.read_text()) == {"status": "complete"}
    assert not path.with_suffix(".json.tmp").exists()
