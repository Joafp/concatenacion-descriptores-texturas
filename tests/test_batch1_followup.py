import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def setup(tmp_path, status):
    path = Path(__file__).resolve().parents[1] / "scripts/run_local_batch1_followup.py"
    spec = importlib.util.spec_from_file_location("batch1_followup_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    online = tmp_path / "svm_online"
    online.mkdir()
    (online / "status.json").write_text(json.dumps({"status": status, "pid": 123, "error": "test failure"}))
    args = SimpleNamespace(svm_online=online, svm_quality=tmp_path / "svm_quality",
        resmlp_quality=tmp_path / "resmlp_quality", deit_reconstruction=tmp_path / "deit.json",
        protocol=tmp_path / "protocol.md", output=tmp_path / "sequence")
    return mod, args


def test_never_runs_next_pilot_after_svm_failure(monkeypatch, tmp_path):
    mod, args = setup(tmp_path, "blocked_online_execution")
    calls = []
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: calls.append(a))
    with pytest.raises(SystemExit):
        mod.run(args)
    assert calls == []
    assert json.loads((args.output / "sequence_status.json").read_text())["status"] == "stopped_on_svm_failure"


def test_audit_precedes_resmlp_and_stops_on_error(monkeypatch, tmp_path):
    mod, args = setup(tmp_path, "batch1_online_f1_and_timing_complete")

    def gone(*a):
        raise ProcessLookupError

    monkeypatch.setattr(mod.os, "kill", gone)
    calls = []
    monkeypatch.setattr(mod.subprocess, "run", lambda command, **kwargs:
        calls.append(command) or SimpleNamespace(returncode=1))
    with pytest.raises(SystemExit):
        mod.run(args)
    assert len(calls) == 1 and "audit_local_batch1_calls.py" in calls[0][3]


def test_success_runs_three_stages_in_order(monkeypatch, tmp_path):
    mod, args = setup(tmp_path, "batch1_online_f1_and_timing_complete")

    def gone(*a):
        raise ProcessLookupError

    monkeypatch.setattr(mod.os, "kill", gone)
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
    mod.run(args)
    report = json.loads((args.output / "sequence_status.json").read_text())
    assert report["completed_stages"] == ["audit_svm", "measure_resmlp", "audit_resmlp"]
    assert report["status"] == "both_pilots_and_call_audits_complete"
