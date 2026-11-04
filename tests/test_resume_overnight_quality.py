import importlib.util
from pathlib import Path


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/resume_overnight_quality.py"
    spec = importlib.util.spec_from_file_location("resume_quality_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def job(tmp_path):
    return dict(id="DTD_resmlp_s42_f9", quality_hold=None, quality_external_managed=False,
        job_dir=str(tmp_path / "job"), quality_run=str(tmp_path / "quality"), quality_audit=str(tmp_path / "audit"))


def test_only_never_attempted_job_eligible(tmp_path):
    assert module().eligible(job(tmp_path))


def test_review_or_complete_marker_excludes_retry(tmp_path):
    item = job(tmp_path)
    directory = Path(item["job_dir"])
    directory.mkdir()
    (directory / "quality_state.json").write_text('{"status":"requires_review"}')
    assert not module().eligible(item)


def test_partial_output_excludes_retry(tmp_path):
    item = job(tmp_path)
    Path(item["quality_run"]).mkdir()
    assert not module().eligible(item)


def test_holds_not_released(tmp_path):
    item = job(tmp_path)
    item["quality_hold"] = "kth_protocol_reconciliation"
    assert not module().eligible(item)


def test_new_output_paths_preserve_original(tmp_path):
    mod = module()
    item = job(tmp_path)
    result = mod.build({"jobs": [item], "conditions": 94}, tmp_path / "new")
    assert result["conditions"] == 1
    assert result["jobs"][0]["quality_run"] != item["quality_run"]
    assert item["quality_run"] == str(tmp_path / "quality")
