import hashlib
import json
import pytest
from local_deit_reconstruction import verified_state_path


def evidence(tmp_path):
    state = tmp_path / "pooler_state.pt"
    state.write_bytes(b"state used only for hash tests; never deserialized")
    report = {"status": "diagnostic_complete", "seed": 42, "tolerance": 1e-4,
        "all_rows_pass": True, "checks": [{"pass": True, "same_shape": True,
            "finite": True, "max_abs_error": 3e-7}] * 2,
        "pooler_state_sha256": hashlib.sha256(state.read_bytes()).hexdigest()}
    path = tmp_path / "diagnostic.json"
    path.write_text(json.dumps(report))
    return path, report


def test_accepts_only_hashed_passing_evidence(tmp_path):
    path, _ = evidence(tmp_path)
    state, report = verified_state_path(path)
    assert state.name == "pooler_state.pt" and report["seed"] == 42


@pytest.mark.parametrize("field,value", [("all_rows_pass", False), ("seed", 1), ("tolerance", .001)])
def test_rejects_weaker_or_different_evidence(tmp_path, field, value):
    path, report = evidence(tmp_path)
    report[field] = value
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="evidence"):
        verified_state_path(path)


def test_rejects_changed_pooler(tmp_path):
    path, _ = evidence(tmp_path)
    path.with_name("pooler_state.pt").write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash"):
        verified_state_path(path)
