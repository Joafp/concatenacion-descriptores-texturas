import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/run_fmd_local_followup.py"
    spec = importlib.util.spec_from_file_location("fmd_queue_test", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def args(tmp_path, dataset="FMD"):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"provenance": {"arguments": {
        "dataset": dataset, "seed": 42, "fold": 0, "manifest_root": "unchanged"}}}))
    protocol = tmp_path / "protocol.md"
    protocol.write_text("fixed protocol")
    return SimpleNamespace(reference_config=config, protocol=protocol,
        classifier="svm", output=tmp_path / "new_results")


def test_four_folds_no_changes_to_other_config(monkeypatch, tmp_path):
    mod = module()
    cfg = args(tmp_path)
    original = cfg.reference_config.read_bytes()
    calls = []

    def fake(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(mod.subprocess, "run", fake)
    mod.run(cfg)
    assert len(calls) == 8
    assert cfg.reference_config.read_bytes() == original
    for fold in (1, 2, 3, 4):
        changed = json.loads((cfg.output / f"fold{fold}_config.json").read_text())["provenance"]["arguments"]
        assert changed == {"dataset": "FMD", "seed": 42, "fold": fold, "manifest_root": "unchanged"}
    assert json.loads((cfg.output / "queue_status.json").read_text())["completed"] == [1, 2, 3, 4]


def test_stops_without_retry_on_first_failure(monkeypatch, tmp_path):
    mod = module()
    cfg = args(tmp_path)
    calls = []
    monkeypatch.setattr(mod.subprocess, "run", lambda command, **kwargs:
        calls.append(command) or SimpleNamespace(returncode=7))
    with pytest.raises(SystemExit) as exc:
        mod.run(cfg)
    assert exc.value.code == 7 and len(calls) == 1
    state = json.loads((cfg.output / "queue_status.json").read_text())
    assert state["status"] == "stopped_on_failure" and state["completed"] == []
    assert not (cfg.output / "fold2_config.json").exists()


def test_rejects_wrong_dataset_before_writing_results(tmp_path):
    mod = module()
    cfg = args(tmp_path, dataset="DTD")
    with pytest.raises(ValueError, match="restricted"):
        mod.run(cfg)
    assert not cfg.output.exists()
