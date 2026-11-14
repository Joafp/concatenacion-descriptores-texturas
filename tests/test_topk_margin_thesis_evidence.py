"""Check the evidence used by the rewritten thesis without fitting models."""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json

import numpy as np
import pytest
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results/analysis/topk_margin_rewrite_20261113_v1"
GENERATED = ROOT / "paper/generated_topk_margin"


def test_all_audited_sources_and_rendered_artifacts_are_bound_to_hashes():
    summary = json.loads((AUDIT / "summary.json").read_text())
    assert summary["new_fits"] == summary["new_predictions"] == summary["new_timings"] == 0
    assert len(summary["source_sha256"]) == 124
    for relative, expected in summary["source_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
    provenance = json.loads((GENERATED / "provenance.json").read_text())
    assert hashlib.sha256((AUDIT / "summary.json").read_bytes()).hexdigest() == provenance["audit_summary_sha256"]
    for name, expected in provenance["generated_sha256"].items():
        assert hashlib.sha256((GENERATED / name).read_bytes()).hexdigest() == expected, name


def test_both_classifiers_have_the_same_complete_k_grid():
    with (AUDIT / "curves.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 42
    for classifier in ("svm", "resmlp"):
        selected = [r for r in rows if r["classifier"] == classifier]
        assert sorted(int(r["k"]) for r in selected) == list(range(1, 22))
        assert all(int(r["conditions"]) == 47 for r in selected)


def test_all_27_conditional_records_use_the_same_direct_rescue():
    folder = ROOT / "results/exploratory/topk_cascade/cheap_stage_selected_primary22"
    with (AUDIT / "paired_cascade_audit.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 27
    for row in rows:
        stem = f"{row['dataset']}_{row['protocol']}".replace(":", "__")
        pred = json.loads((folder / f"{stem}_predictions.json").read_text())
        y = np.asarray(pred["y_true"])
        direct = np.asarray(pred["y_pred_topk_direct"])
        conditional = np.asarray(pred["y_pred_adaptive_cascade"])
        requested = np.asarray(pred["requested_topk_adaptive"], dtype=bool)
        assert np.array_equal(direct[requested], conditional[requested])
        for name, prediction in (("direct", direct), ("conditional", conditional)):
            assert f1_score(y, prediction, average="macro", zero_division=0) == pytest.approx(float(row[name + "_f1"]), abs=1e-12)


def test_incomplete_deeplumina_is_not_turned_into_a_complete_dtd_mean():
    with (AUDIT / "external_top4.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 23
    assert not any(r["dataset"] == "DTD" and r["reference_method"] == "DeepLumina" for r in rows)
    assert all(r["scientific_status_reference"] == "requires_review_solver_nonconvergence"
               for r in rows if r["reference_method"] == "DeepLumina")
    assert "incompleto" in (GENERATED / "externos_f1.tex").read_text()


def test_builder_refuses_to_overwrite_an_existing_audit(tmp_path):
    spec = importlib.util.spec_from_file_location("topk_thesis_builder", ROOT / "scripts/build_topk_margin_thesis_20261113.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    audit = tmp_path / "existing"
    audit.mkdir()
    marker = audit / "marker"
    marker.write_text("sealed")
    generated = tmp_path / "generated"
    with pytest.raises(FileExistsError):
        module.build(audit, generated)
    assert marker.read_text() == "sealed"
    assert not generated.exists()


def test_fixed_top4_subset_keeps_gains_losses_and_ties():
    rows = json.loads((AUDIT / "top4_margin_subset.json").read_text())
    assert len(rows) == 5
    assert all(r["same_selected_blocks_as_fixed4_sweep"] for r in rows)
    differences = [r["margin_f1"] - r["direct_f1"] for r in rows]
    assert any(d > 0 for d in differences)
    assert any(d < 0 for d in differences)
    assert any(d == 0 for d in differences)
    provenance = json.loads((AUDIT / "top4_margin_subset_provenance.json").read_text())
    for relative, expected in provenance["output_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected


def test_progression_keeps_every_dataset_and_classifier_and_its_sources():
    folder = ROOT / 'results/analysis/topk_marginal_gains_20261113_v1'
    provenance = json.loads((folder / 'provenance.json').read_text())
    for section in ['source_sha256', 'output_sha256']:
        for relative, expected in provenance[section].items():
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    with (folder / 'per_dataset_curves.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    keys = {(r['classifier'], r['dataset'], int(r['k'])) for r in rows}
    assert len(rows) == len(keys) == 252
    assert len({r['dataset'] for r in rows}) == 6
    for clf in ['svm', 'resmlp']:
        for dataset in {r['dataset'] for r in rows}:
            assert {k for c, d, k in keys if c == clf and d == dataset} == set(range(1, 22))


def test_marginal_gains_show_later_improvements_and_telescope_in_percentage_points():
    folder = ROOT / 'results/analysis/topk_marginal_gains_20261113_v1'
    summary = json.loads((folder / 'summary.json').read_text())
    assert summary['new_fits'] == summary['new_predictions'] == summary['new_timings'] == 0
    with (AUDIT / 'curves.csv').open() as stream:
        curves = list(csv.DictReader(stream))
    with (folder / 'marginal_gains.csv').open() as stream:
        gains = list(csv.DictReader(stream))
    assert len(gains) == 40
    for clf in ['svm', 'resmlp']:
        curve = sorted([r for r in curves if r['classifier'] == clf], key=lambda r: int(r['k']))
        local = [r for r in gains if r['classifier'] == clf]
        assert sum(float(r['gain_pp_vs_previous_k']) for r in local) == pytest.approx(
            100 * (float(curve[-1]['macro_f1']) - float(curve[0]['macro_f1'])), abs=1e-10)
        assert any(float(r['gain_pp_vs_previous_k']) > 0 for r in local if int(r['k']) > 4)
        assert any(float(r['gain_pp_vs_previous_k']) < 0 for r in local if int(r['k']) > 4)
    svm, mlp = summary['statistics']
    assert svm['peak_k'] == 10 and mlp['peak_k'] == 5
    assert svm['gain_1_to_4_pp'] == pytest.approx(1.910633, abs=1e-6)
    assert svm['gap_4_to_peak_pp'] == pytest.approx(.0209922, abs=1e-6)


def test_concatenation_example_matches_a_real_condition_not_a_universal_subset():
    summary = json.loads((ROOT / 'results/analysis/topk_marginal_gains_20261113_v1/summary.json').read_text())
    example = summary['example']
    assert (example['dataset'], example['seed'], example['outer_fold'], example['k']) == ('FMD', 42, 0, 4)
    assert example['selected'].split('+') == ['siglip_base', 'dinov2_large', 'eva02_base', 'dinov2']
    assert example['dimensions'] == 768 + 1024 + 768 + 768 == 3328
