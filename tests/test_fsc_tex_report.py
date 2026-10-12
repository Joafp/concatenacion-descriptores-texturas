"""Regression tests for reporting scope; no dataset training or online timing."""

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/report_fsc_tex_phase3_v2.py"
SPEC = importlib.util.spec_from_file_location("fsc_v2_report", SCRIPT)
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def write_condition(root, dataset="DTD"):
    path = root / dataset / "condition_1"
    path.mkdir(parents=True)
    predictions = {"y_true": [0, 1, 0, 1]}
    predictions.update({m: [0, 1, 0, 1] for m in report.CORE_METHODS})
    metrics = {
        m: {"macro_f1": 1.0, "accuracy": 1.0,
            "mean_latency_ms": 25.0, "p95_latency_ms": 25.0}
        for m in report.CORE_METHODS
    }
    manifest = {"prospective_tuning": {"target_budget_ms": 35.0}}
    for name, data in {
        "metrics.json": metrics, "predictions.json": predictions,
        "run_manifest.json": manifest, "splits.json": {},
        "state_graph.json": {}, "audit.json": {}, "traces.jsonl": {},
    }.items():
        (path / name).write_text(json.dumps(data), encoding="utf-8")
    return path


def test_loader_recomputes_predictive_metrics(tmp_path):
    write_condition(tmp_path)
    assert len(report.load_all_suite_results(tmp_path)) == 1


def test_loader_rejects_incorrect_metric(tmp_path):
    path = write_condition(tmp_path)
    metrics_path = path / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics["FSC_Tex_H2_Bellman"]["macro_f1"] = 0.99
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")
    with pytest.raises(ValueError, match="Métrica no reproducible"):
        report.load_all_suite_results(tmp_path)


def test_loader_rejects_missing_artifact(tmp_path):
    path = write_condition(tmp_path)
    # Only a test-owned temporary fixture is removed.
    (path / "audit.json").unlink()
    with pytest.raises(ValueError, match="Falta artefacto"):
        report.load_all_suite_results(tmp_path)


def test_report_does_not_turn_point_estimate_into_certification(tmp_path):
    for dataset in ("DTD", "FMD", "CUReT"):
        write_condition(tmp_path, dataset)
    content = report.compute_statistics_and_report(
        report.load_all_suite_results(tmp_path), tmp_path / "report.md"
    )
    assert "(3 condiciones)" in content
    assert "No se ha ejecutado una prueba formal de no inferioridad" in content
    assert "costos estimados, no cronometraje físico" in content
    assert "evidencia insuficiente" in content
    assert "Referencias históricas de v2 en cuarentena" in content
    assert "P0 corrigió después" in content
    assert "Mejora Calidad-Costo Comprobada" not in content
    assert "Ganancia neta por planificación a 2 pasos" not in content
