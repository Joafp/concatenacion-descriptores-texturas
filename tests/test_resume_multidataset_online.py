import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/resume_multidataset_online.py"
    spec = importlib.util.spec_from_file_location("resume_online_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def job(tmp_path):
    return dict(id="case", job_dir=str(tmp_path / "job"), online_run=str(tmp_path / "run"),
        online_audit=str(tmp_path / "audit"), config="same", config_sha256="sha", quality_run="old", quality_audit="old_audit")


def test_only_untried_job_eligible(tmp_path):
    assert module().eligible(job(tmp_path))


def test_failed_binding_marker_excludes_all_dependent_jobs(tmp_path):
    item = job(tmp_path)
    Path(item["job_dir"]).mkdir()
    (Path(item["job_dir"]) / "online_state.json").write_text('{"status":"requires_review"}')
    assert not module().eligible(item)


def test_partial_online_output_excluded(tmp_path):
    item = job(tmp_path)
    Path(item["online_run"]).mkdir()
    assert not module().eligible(item)


def test_quality_path_updates_only_for_identical_scientific_config(tmp_path):
    item = job(tmp_path)
    replacement = dict(item, quality_run="new", quality_audit="new_audit")
    assert module().quality_override(item, {"case": replacement})["quality_run"] == "new"
    replacement["config_sha256"] = "different"
    with pytest.raises(ValueError, match="scientific config"):
        module().quality_override(item, {"case": replacement})


def test_failed_evidence_is_not_copied(tmp_path):
    mod = module()
    source = tmp_path / "prior"
    source.mkdir()
    mod.write(source / "diagnostic.json", {"status": "diagnostic_complete", "all_rows_pass": False})
    assert not mod.copy_approved_binding(source, tmp_path / "new")
    assert not (tmp_path / "new").exists()
