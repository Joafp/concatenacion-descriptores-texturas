import importlib.util
import json
from pathlib import Path

import pytest


def module():
    spec = importlib.util.spec_from_file_location(
        "observer_test", Path(__file__).resolve().parents[1] / "scripts/observe_benchmark_process.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stat(start=123, state="S"):
    fields = ["0"] * 22
    fields[0], fields[11], fields[12], fields[19], fields[21] = state, "41", "7", str(start), "1024"
    return "99 (name with ) parentheses)) " + " ".join(fields)


def setup(tmp_path, monkeypatch):
    mod = module()
    proc = tmp_path / "proc" / "99"
    proc.mkdir(parents=True)
    path = proc / "stat"
    path.write_text(stat())
    clock = [0.0]
    monkeypatch.setattr(mod.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(mod.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    monkeypatch.setattr(mod, "gpu_snapshot", lambda _: pytest.fail("GPU disabled by default"))
    return mod, path, clock


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_parser_command_spaces_and_closing_parentheses():
    parsed = module().parse_proc_stat(stat())
    assert parsed == dict(pid=99, comm="name with ) parentheses)", state="S",
                          utime_ticks=41, stime_ticks=7, start_ticks=123, rss_pages=1024)


def test_parser_rejects_truncation():
    with pytest.raises(ValueError):
        module().parse_proc_stat("99 (x) S 0")


def test_deadline_stops_observer_not_target(tmp_path, monkeypatch):
    mod, proc, clock = setup(tmp_path, monkeypatch)
    output = tmp_path / "events.jsonl"
    assert mod.observe(99, output, proc_root=tmp_path / "proc", interval_seconds=5,
                       max_seconds=12) == "deadline_reached"
    events = records(output)
    assert clock[0] == 12
    assert proc.exists()
    assert len([e for e in events if e["event"] == "process_snapshot"]) == 3
    assert events[-1]["target_signalled"] is False
    assert all({"utc", "monotonic_seconds", "boottime_seconds"} <= e.keys() for e in events)


def test_pid_reuse_rejected(tmp_path, monkeypatch):
    mod, proc, clock = setup(tmp_path, monkeypatch)
    def sleep(seconds):
        clock[0] += seconds
        proc.write_text(stat(start=456))
    monkeypatch.setattr(mod.time, "sleep", sleep)
    output = tmp_path / "events.jsonl"
    assert mod.observe(99, output, expected_start_ticks=123, interval_seconds=5,
                       proc_root=tmp_path / "proc") == "pid_reused"
    assert len([e for e in records(output) if e["event"] == "process_snapshot"]) == 1


@pytest.mark.parametrize("terminal", ["Z", "X", "x"])
def test_terminal_state(tmp_path, monkeypatch, terminal):
    mod, proc, _ = setup(tmp_path, monkeypatch)
    proc.write_text(stat(state=terminal))
    assert mod.observe(99, tmp_path / "events.jsonl", proc_root=tmp_path / "proc") == "target_terminal_state"


def test_exit_detected(tmp_path, monkeypatch):
    mod, proc, clock = setup(tmp_path, monkeypatch)
    def sleep(seconds):
        clock[0] += seconds
        proc.unlink()
    monkeypatch.setattr(mod.time, "sleep", sleep)
    assert mod.observe(99, tmp_path / "events.jsonl", interval_seconds=5,
                       proc_root=tmp_path / "proc") == "target_exited"


def test_existing_output_preserved(tmp_path, monkeypatch):
    mod, _, _ = setup(tmp_path, monkeypatch)
    output = tmp_path / "events.jsonl"
    output.write_text("keep original\n")
    with pytest.raises(FileExistsError):
        mod.observe(99, output, proc_root=tmp_path / "proc")
    assert output.read_text() == "keep original\n"


def test_short_interval_rejected(tmp_path):
    with pytest.raises(ValueError):
        module().observe(99, tmp_path / "events.jsonl", interval_seconds=4.9)


def test_supplied_identity_mismatch_before_first_snapshot(tmp_path, monkeypatch):
    mod, _, _ = setup(tmp_path, monkeypatch)
    output = tmp_path / "events.jsonl"
    assert mod.observe(99, output, expected_start_ticks=999,
                       proc_root=tmp_path / "proc") == "pid_reused"
    assert not any(e["event"] == "process_snapshot" for e in records(output))


def test_gpu_timeout_is_recorded_not_target_action(monkeypatch):
    mod = module()
    def run(*args, **kwargs):
        assert kwargs["timeout"] == 1.5
        raise mod.subprocess.TimeoutExpired(args[0], 1.5)
    monkeypatch.setattr(mod.subprocess, "run", run)
    assert mod.gpu_snapshot(1.5)["error"] == "TimeoutExpired"


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_invalid_deadline_rejected(tmp_path, bad):
    with pytest.raises(ValueError):
        module().observe(99, tmp_path / "events.jsonl", max_seconds=bad)
