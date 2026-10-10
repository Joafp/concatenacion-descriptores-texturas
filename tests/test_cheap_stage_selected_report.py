#!/usr/bin/env python3
"""Tests unitarios para la generación de reportes estadísticos de la Cascada Adaptativa."""

from pathlib import Path
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
    assert "# Reporte de Validación Estadística: Cascada Adaptativa Costo-Consciente" in content
    assert "75.5%" in content
    assert "27 condiciones" in content
