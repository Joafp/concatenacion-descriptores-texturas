#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ANALYZER_PATH = Path(__file__).resolve().parents[1] / "src" / "analyze_confirmatory_results.py"
SPEC = importlib.util.spec_from_file_location("confirmatory_analysis", ANALYZER_PATH)
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(analysis)


def _rows(dataset: str, classifier: str, deltas: list[float]) -> list[dict]:
    rows = []
    for fold, delta in enumerate(deltas):
        baseline = 0.8
        for method, score in (
            ("best_individual", baseline),
            ("full_concat", baseline + 0.005),
            ("gfs", baseline + delta),
        ):
            rows.append({
                "dataset": dataset,
                "classifier": classifier,
                "seed": 42,
                "outer_fold": fold,
                "method": method,
                "macro_f1": score,
            })
    return rows


def test_curet_complementary_directions_are_descriptive_only():
    result = analysis.paired_comparisons(pd.DataFrame(_rows("CUReT", "svm", [0.01, 0.02])))
    assert len(result) == 2
    assert set(result.n_splits) == {2}
    assert result.wilcoxon_p_uncorrected.isna().all()
    assert result.wilcoxon_p_holm.isna().all()
    assert result.ci95_low.isna().all()
    assert result.ci95_high.isna().all()
    assert result.inference_note.str.contains("descriptive only").all()


def test_holm_ignores_curet_undefined_p_values():
    rows = _rows("CUReT", "svm", [0.01, 0.02])
    rows += _rows("DTD", "svm", [0.01] * 9 + [0.02])
    result = analysis.paired_comparisons(pd.DataFrame(rows))
    curet = result[result.dataset.eq("CUReT")]
    dtd = result[result.dataset.eq("DTD")]
    assert curet.wilcoxon_p_holm.isna().all()
    assert np.isfinite(dtd.wilcoxon_p_uncorrected).all()
    assert np.isfinite(dtd.wilcoxon_p_holm).all()


def test_single_official_split_omits_split_level_inference():
    rows = _rows("Outex13Official1360", "svm", [0.01])
    result = analysis.paired_comparisons(pd.DataFrame(rows))
    assert len(result) == 2
    assert set(result.n_splits) == {1}
    assert result.wilcoxon_p_uncorrected.isna().all()
    assert result.wilcoxon_p_holm.isna().all()
    assert result.ci95_low.isna().all()
    assert result.ci95_high.isna().all()
    assert result.inference_note.str.contains("single official split").all()
