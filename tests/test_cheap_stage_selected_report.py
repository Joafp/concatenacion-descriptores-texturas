#!/usr/bin/env python3
"""Tests unitarios para la generación de reportes estadísticos de la Cascada Adaptativa."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from scripts.report_cheap_stage_selected_cascade import (
    DEFAULT_ROWS_CSV,
    DEFAULT_LEDGER_CSV,
    load_and_merge_data,
    generate_report,
    get_cond_str,
    holm_bonferroni_correction,
    compute_critical_difference,
)


def test_cond_str_mapping():
    assert get_cond_str("official1") == "1"
    assert get_cond_str("official10") == "10"
    assert get_cond_str("official1_inverted") == "1"
    assert get_cond_str("stratified_group_kfold5_fold3") == "3"
    assert get_cond_str("curet_half_indices:a_to_b") == "a_to_b"


def test_holm_bonferroni():
    raw_p = [0.01, 0.04, 0.03]
    adj_p = holm_bonferroni_correction(raw_p)
    assert len(adj_p) == 3
    assert adj_p[0] <= adj_p[1] <= 1.0


def test_critical_difference():
    cd = compute_critical_difference(k=4, N=6, alpha=0.05)
    assert 1.0 < cd < 3.0


def test_load_and_merge_27_conditions():
    assert DEFAULT_ROWS_CSV.exists()
    assert DEFAULT_LEDGER_CSV.exists()
    df = load_and_merge_data(DEFAULT_ROWS_CSV, DEFAULT_LEDGER_CSV)
    assert len(df) == 27
    assert set(df["dataset"].unique()) == {"DTD", "FMD", "CUReT", "Outex13Official1360", "SoilOriginal", "KTHTIPS2b"}
    assert df["new_f1"].notnull().all()
    assert df["topk_f1"].notnull().all()
    assert df["full_22_macro_f1"].notnull().all()
    assert df["new_ms"].notnull().all()


def test_generate_report_contents(tmp_path):
    df = load_and_merge_data(DEFAULT_ROWS_CSV, DEFAULT_LEDGER_CSV)
    out_file = tmp_path / "test_report.md"
    content = generate_report(df, out_file)
    assert out_file.exists()
    assert "# Reporte auditado: cascada con etapa económica seleccionada" in content
    assert "75.5%" in content
    assert "27 condiciones" in content
    assert "N=5 datasets" in content
    assert "No rechazar no demuestra igualdad" in content
    assert "Costo proyectado" in content
    assert "Paridad estadística" not in content
    assert "equivalencia empírica" not in content
    assert "horizonte infinito" not in content


def test_kth_references_are_not_silently_substituted():
    df = load_and_merge_data(DEFAULT_ROWS_CSV, DEFAULT_LEDGER_CSV)
    kth = df[df.dataset == "KTHTIPS2b"]
    assert kth.topk_reference_status.value_counts().to_dict() == {"missing": 3, "different": 1}
    assert not kth.inference_eligible.any()
    assert df.inference_eligible.sum() == 23


def test_duplicate_conditions_are_rejected(tmp_path):
    rows = pd.read_csv(DEFAULT_ROWS_CSV)
    duplicate = pd.concat([rows, rows.iloc[[0]]])
    path = tmp_path / "rows.csv"
    duplicate.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Duplicate condition"):
        load_and_merge_data(path, DEFAULT_LEDGER_CSV)


def test_bad_metrics_are_rejected(tmp_path):
    import json
    rows = pd.read_csv(DEFAULT_ROWS_CSV)
    row = rows.iloc[0]
    source = DEFAULT_ROWS_CSV.parent / f"{row.dataset}_{row.protocol}_result.json".replace(":", "__")
    record = json.loads(source.read_text())
    record["selected_cheap_stage"]["macro_f1"] += 0.1
    (tmp_path / source.name).write_text(json.dumps(record))
    path = tmp_path / "rows.csv"
    rows.to_csv(path, index=False)
    with pytest.raises(ValueError, match="CSV/JSON mismatch"):
        load_and_merge_data(path, DEFAULT_LEDGER_CSV)


def test_plotting_generation(tmp_path):
    from scripts.plot_cheap_stage_selected_cascade import (
        plot_pareto_frontier,
        plot_routing_efficiency,
        plot_speedup_accuracy_bars,
        RESULTS_DIR,
    )
    df = pd.read_csv(DEFAULT_ROWS_CSV)
    plot_pareto_frontier(df, tmp_path)
    plot_routing_efficiency(RESULTS_DIR, tmp_path)
    plot_speedup_accuracy_bars(df, tmp_path)

    assert (tmp_path / "pareto_frontier_adaptive_cascade.pdf").exists()
    assert (tmp_path / "cascade_routing_efficiency.pdf").exists()
    assert (tmp_path / "multidataset_speedup_accuracy.pdf").exists()


def test_all_27_predictions_exist_and_reproduce_metrics():
    import json
    from sklearn.metrics import f1_score
    rows = pd.read_csv(DEFAULT_ROWS_CSV)
    pred_dir = DEFAULT_ROWS_CSV.parent
    assert len(list(pred_dir.glob("*_predictions.json"))) == 27
    for _, row in rows.iterrows():
        pred_file = pred_dir / f"{row.dataset}_{row.protocol}_predictions.json".replace(":", "__")
        assert pred_file.exists(), f"Falta {pred_file}"
        data = json.loads(pred_file.read_text(encoding="utf-8"))
        y_true = np.array(data["y_true"])
        y_pred = np.array(data["y_pred_adaptive_cascade"])
        labels = np.unique(y_true)
        recalculated_f1 = float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0))
        assert np.isclose(recalculated_f1, row["new_f1"], rtol=0, atol=1e-12)
