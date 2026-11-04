import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import subprocess


def fixture(tmp_path, monkeypatch):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("queue_test", scripts / "run_authorized_remediation_queue.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    source = tmp_path / "frozen"
    source.write_text("fixed")
    manifest = {"source_sha256": {str(source): hashlib.sha256(source.read_bytes()).hexdigest()}, "tasks": []}
    def save(tasks):
        manifest["tasks"] = tasks
        mod.write(tmp_path / "manifest.json", manifest)
    return mod, manifest, source, save


def task(name="a", code="pass", **extra):
    return {"id": name, "lane": "cpu", "commands": [
        {"argv": [sys.executable, "-c", code], "timeout_seconds": 5}], **extra}


def test_success_and_idempotence(tmp_path, monkeypatch):
    mod, _, _, save = fixture(tmp_path, monkeypatch)
    save([task()])
    assert mod.run_queue(tmp_path, "cpu")["outcomes"] == {"a": "complete"}
    log = tmp_path / "tasks/a/stage_0.log"
    before = log.stat().st_mtime_ns
    assert mod.run_queue(tmp_path, "cpu")["outcomes"] == {"a": "complete"}
    assert log.stat().st_mtime_ns == before


def test_failed_dependency_never_executes(tmp_path, monkeypatch):
    mod, _, _, save = fixture(tmp_path, monkeypatch)
    save([task(code="raise SystemExit(2)"), task("b", depends_on=["a"])])
    assert mod.run_queue(tmp_path, "cpu")["outcomes"] == {"a": "requires_review", "b": "blocked"}
    assert not (tmp_path / "tasks/b/stage_0.log").exists()


def test_source_drift_no_execution(tmp_path, monkeypatch):
    mod, _, source, save = fixture(tmp_path, monkeypatch)
    save([task()])
    source.write_text("changed")
    assert mod.run_queue(tmp_path, "cpu")["outcomes"]["a"] == "requires_review"
    assert not (tmp_path / "tasks/a/stage_0.log").exists()


def test_output_guard_no_execution(tmp_path, monkeypatch):
    mod, _, source, save = fixture(tmp_path, monkeypatch)
    save([task(exclusive_outputs=[str(source)])])
    assert mod.run_queue(tmp_path, "cpu")["outcomes"]["a"] == "requires_review"
    assert source.read_text() == "fixed"


def test_stale_running_pid_marker_no_retry(tmp_path, monkeypatch):
    mod, _, _, save = fixture(tmp_path, monkeypatch)
    save([task()])
    path = tmp_path / "tasks/a/state.json"
    mod.write(path, {"status": "running", "pid": 123, "start_ticks": 456})
    assert mod.run_queue(tmp_path, "cpu")["outcomes"]["a"] == "requires_review"
    assert mod.read(path)["pid"] == 123
    assert not (tmp_path / "tasks/a/stage_0.log").exists()


def test_success_conditions_must_match(tmp_path, monkeypatch):
    mod, _, _, save = fixture(tmp_path, monkeypatch)
    result = tmp_path / "result.json"
    result.write_text('{"status":"wrong"}')
    t = task()
    t["commands"][0]["success"] = {"path": str(result), "fields": {"status": "complete"}}
    save([t])
    assert mod.run_queue(tmp_path, "cpu")["outcomes"]["a"] == "requires_review"


def test_matching_nested_success_condition(tmp_path, monkeypatch):
    mod, _, _, save = fixture(tmp_path, monkeypatch)
    result = tmp_path / "result.json"
    result.write_text('{"audit":{"status":"complete"}}')
    t = task()
    t["commands"][0]["success"] = {"path": str(result), "fields": {"audit.status": "complete"}}
    save([t])
    assert mod.run_queue(tmp_path, "cpu")["outcomes"]["a"] == "complete"
    state = mod.read(tmp_path / "tasks/a/state.json")
    assert state["success_artifacts"][0]["sha256"] == hashlib.sha256(result.read_bytes()).hexdigest()


def test_completed_artifact_tamper_blocks_dependency(tmp_path, monkeypatch):
    mod, _, _, save = fixture(tmp_path, monkeypatch)
    result = tmp_path / "result.json"
    result.write_text('{"status":"complete"}')
    a = task()
    a["commands"][0]["success"] = {"path": str(result), "fields": {"status": "complete"}}
    b = task("b", depends_on=["a"])
    b["lane"] = "gpu"
    save([a, b])
    assert mod.run_queue(tmp_path, "cpu")["outcomes"]["a"] == "complete"
    result.write_text('{"status":"complete", "tampered":true}')
    assert mod.run_queue(tmp_path, "gpu")["outcomes"] == {"a": "requires_review", "b": "blocked"}
    assert not (tmp_path / "tasks/b/stage_0.log").exists()


def test_completed_manifest_mismatch_not_reused(tmp_path, monkeypatch):
    mod, manifest, _, save = fixture(tmp_path, monkeypatch)
    save([task()])
    assert mod.run_queue(tmp_path, "cpu")["outcomes"]["a"] == "complete"
    manifest["new_authorization"] = "different manifest"
    save([task()])
    assert mod.run_queue(tmp_path, "cpu")["outcomes"]["a"] == "requires_review"


def test_hard_timeout_records_before_signals(tmp_path, monkeypatch):
    mod, manifest, _, _ = fixture(tmp_path, monkeypatch)
    events = []
    class Process:
        pid = 99999
        calls = 0
        def wait(self, timeout):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired("test", timeout)
            return -15
        def poll(self):
            return -15
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: Process())
    monkeypatch.setattr(mod, "start_ticks", lambda pid: 888)
    monkeypatch.setattr(mod.os, "killpg", lambda pid, sig: events.append(("signal", pid, sig)))
    output = tmp_path / "stage"
    output.mkdir()
    state = mod.run_task(task(), output, manifest,
                         lambda s: events.append(("state", s.copy())))
    assert state["status"] == "requires_review"
    before_signal = events[:next(i for i, e in enumerate(events) if e[0] == "signal")]
    assert before_signal[-1][1]["reason"] == "hard_timeout_before_termination"
    assert before_signal[-1][1]["start_ticks"] == 888


def test_gpu_active_blocks_dispatch_until_window(tmp_path, monkeypatch):
    mod, manifest, _, save = fixture(tmp_path, monkeypatch)
    manifest["gpu_lock"] = str(tmp_path / "gpu.lock")
    t = task()
    t["lane"] = "gpu"
    save([t])
    clock = [0.0]
    monkeypatch.setattr(mod.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(mod.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0]+seconds))
    monkeypatch.setattr(mod, "active_benchmarks", lambda: ["active benchmark"])
    worker = mod.run_queue(tmp_path, "gpu", window_hours=0.001)
    assert worker["status"] == "dispatch_window_ended"
    assert not (tmp_path / "tasks/a/state.json").exists()


def test_cpu_environment_hidden_gpu_and_threads(tmp_path, monkeypatch):
    mod, _, _, save = fixture(tmp_path, monkeypatch)
    save([task(code="import os; assert os.environ['CUDA_VISIBLE_DEVICES']==''; assert os.environ['OMP_NUM_THREADS']=='2'")])
    assert mod.run_queue(tmp_path, "cpu")["outcomes"]["a"] == "complete"
