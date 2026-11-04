import importlib.util
from pathlib import Path
import tempfile
import json

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("replication_audit", ROOT / "scripts/audit_mesa_replication.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_recovery_requires_failed_static_and_matching_decisions(tmp_path):
    path = tmp_path / "FMD_s42"
    path.mkdir()
    state = {"status": "complete_pending_audit", "stages": []}
    (path / "state.json").write_text(json.dumps(state))
    with pytest.raises(AssertionError):
        audit.recovery_inputs(path)


def test_recovery_cannot_silently_accept_an_unapproved_attempt(tmp_path):
    path = tmp_path / "FMD_s42"
    path.mkdir()
    state = {"status": "failed", "failed_stage": "static", "stages": [
        {"stage": "paired", "status": "complete"}, {"stage": "static", "status": "failed"}]}
    (path / "state.json").write_text(json.dumps(state))
    with pytest.raises(FileNotFoundError):
        audit.recovery_inputs(path)


@pytest.mark.parametrize("same_decisions", [True, False])
def test_recovery_is_bound_to_original_frozen_decisions(tmp_path, monkeypatch, same_decisions):
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    path = tmp_path / "FMD_s42"
    (path / "static").mkdir(parents=True)
    (path / "static_recovery").mkdir()
    (path / "static/decisions.json").write_text("[]\n")
    (path / "static_recovery/decisions.json").write_text("[]\n" if same_decisions else "[1]\n")
    (path / "static.log").write_text("coverage failure")
    (path / "state.json").write_text(json.dumps({"status": "failed", "failed_stage": "static",
        "stages": [{"stage": "paired", "status": "complete"}, {"stage": "static", "status": "failed"}]}))
    command = ["python", "--hybrid-run", str(path / "hybrid"), "--output", str(path / "static_recovery")]
    receipt_path = tmp_path / "static_recovery_authorization.json"
    receipt_path.write_text(json.dumps({"input_sha256": {"FMD_s42/state.json": audit.digest(path / "state.json")},
                                       "commands": [command]}))
    (path / "static_recovery_state.json").write_text(json.dumps({"status": "complete_pending_audit",
        "returncode": 0, "command": command, "authorization_sha256": audit.digest(receipt_path)}))
    if same_decisions:
        assert len(audit.recovery_inputs(path)) == 5
    else:
        with pytest.raises(AssertionError):
            audit.recovery_inputs(path)


def test_auditor_replays_preexisting_outcome_without_changing_it():
    folders = {
        "paired": "results/exploratory/integration_v7/outex_paired22_20261021",
        "carlos": "results/exploratory/integration_v6/carlos_outex22_20261021",
        "hybrid": "results/exploratory/integration_v8/carlos_hybrid_outex22_20261021",
        "static": "results/exploratory/integration_v10/static_budget_outex22_20261025",
    }
    if not all((ROOT / p / "metadata.json").is_file() for p in folders.values()):
        pytest.skip("archived local scores unavailable")
    before = {name: audit.digest(ROOT / p / "predictions.csv") for name, p in folders.items()}
    with tempfile.TemporaryDirectory(prefix="audit_replay_", dir=ROOT / "tmp") as name:
        path = Path(name)
        for stage, target in folders.items():
            (path / stage).symlink_to(ROOT / target, target_is_directory=True)
        result = audit.audit_condition(path, {
            "id": "Outex_s42", "dataset": "Outex13Official1360", "seed": 42,
            "expected_development_images": 680, "manifest_root": "results/extensions/outex13_official1360"
        }, {"config": {"budgets_ms": [15, 30, 60, 120]}})
    assert result["static_choices_replayed"] == 12
    assert result["hybrid_routes_replayed"] == 36
    assert result["development_images"] == 680
    assert len(result["p0"]) == 12
    after = {name: audit.digest(ROOT / p / "predictions.csv") for name, p in folders.items()}
    assert before == after
