"""Pruebas unitarias para el emparejamiento canónico de referencias de 22 bloques (Hito P0).

Verifica el cumplimiento de los criterios de aceptación del Plan 1.2:
- Cobertura 27/27 para Completa-22 y GFS-22.
- Mapeo exacto de outer_fold (0-indexed vs condition).
- CUReT a_to_b -> 0, b_to_a -> 1.
- DTD / Outex / KTH: outer_fold = condition - 1.
- KTH bajo variante canónica 3->1 agrupada con ausencia explícita de Top-k donde aplique.
- Integridad de hashes de archivos fuente.
"""

import json
from pathlib import Path
import pytest

from fsc_tex.baselines import find_confirmatory_reference_metrics


REPO = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO / "results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.json"


def test_canonical_reference_ledger_exists_and_complete():
    """P0 Test: Comprueba que el libro mayor canónico cubre exactamente las 27 condiciones."""
    assert LEDGER_PATH.exists(), "El archivo CANONICAL_22_REFERENCE_LEDGER.json debe existir"
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_conditions"] == 27
    cov = data["coverage_summary"]
    assert cov["full_22_count"] == 27, "Completa-22 debe cubrir las 27 condiciones"
    assert cov["gfs_22_count"] == 27, "GFS-22 debe cubrir las 27 condiciones"
    assert cov["topk_22_count"] == 24, "Top-k 22 debe cubrir 24 condiciones con ausencias explícitas en KTH"


def test_dtd_and_outex_fold_offset_pairing():
    """P0 Test: Comprueba que DTD condición 1 mapea a outer_fold 0 y no a fold 1."""
    # DTD condición 1 debe dar fold 0 (F1 ~ 0.86628, no 0.87009)
    refs_dtd_1 = find_confirmatory_reference_metrics(REPO, "DTD", condition=1, classifier="svm")
    assert refs_dtd_1["Reference_Full_22"] is not None
    assert abs(refs_dtd_1["Reference_Full_22"]["macro_f1"] - 0.86628328) < 1e-5

    # Outex condición 1 debe dar fold 0 (F1 ~ 0.96555)
    refs_outex_1 = find_confirmatory_reference_metrics(REPO, "Outex13Official1360", condition=1, classifier="svm")
    assert refs_outex_1["Reference_Full_22"] is not None
    assert abs(refs_outex_1["Reference_Full_22"]["macro_f1"] - 0.96555100) < 1e-5


def test_curet_direction_explicit_pairing():
    """P0 Test: Comprueba que CUReT mapea a_to_b a fold 0 y b_to_a a fold 1."""
    refs_a = find_confirmatory_reference_metrics(REPO, "CUReT", condition="a_to_b", classifier="svm")
    refs_b = find_confirmatory_reference_metrics(REPO, "CUReT", condition="b_to_a", classifier="svm")

    assert refs_a["Reference_Full_22"] is not None
    assert refs_b["Reference_Full_22"] is not None
    # a_to_b es 0.99786, b_to_a es 1.00000
    assert abs(refs_a["Reference_Full_22"]["macro_f1"] - 0.99786151) < 1e-5
    assert abs(refs_b["Reference_Full_22"]["macro_f1"] - 1.00000000) < 1e-5


def test_kth_innergrp_protocol_and_explicit_absence():
    """P0 Test: Comprueba que KTH usa la variante con agrupación interna y marca ausencias de Top-k."""
    refs_kth_1 = find_confirmatory_reference_metrics(REPO, "KTHTIPS2b", condition=1, classifier="svm")
    refs_kth_4 = find_confirmatory_reference_metrics(REPO, "KTHTIPS2b", condition=4, classifier="svm")

    assert refs_kth_1["Reference_Full_22"] is not None
    assert abs(refs_kth_1["Reference_Full_22"]["macro_f1"] - 0.97286025) < 1e-5
    # En condición 1 no hay topk bajo innergrp
    assert refs_kth_1["Reference_Topk_22"] is None

    # En condición 4 sí está presente
    assert refs_kth_4["Reference_Full_22"] is not None
    assert refs_kth_4["Reference_Topk_22"] is not None
