"""Pruebas unitarias para el módulo de utilidad de FSC-Tex."""

import numpy as np
import pytest

from fsc_tex.utility import (
    compute_gain,
    compute_loss,
    compute_margins,
    summarize_oracle_and_harm,
)


def test_compute_loss_binary():
    y_true = np.array([0, 1, 2, 0])
    y_pred = np.array([0, 2, 2, 1])
    loss = compute_loss(y_true, y_pred)
    assert np.allclose(loss, [0.0, 1.0, 0.0, 1.0])


def test_compute_gain_bipolar():
    loss_base = np.array([0.0, 1.0, 0.0, 1.0])
    # Bloque A: acierta en muestra 1 (repara), falla en muestra 2 (daña)
    loss_aug = np.array([0.0, 0.0, 1.0, 1.0])
    gains = compute_gain(loss_base, loss_aug)
    # [0-0, 1-0, 0-1, 1-1] = [0.0, +1.0, -1.0, 0.0]
    assert np.allclose(gains, [0.0, 1.0, -1.0, 0.0])


def test_compute_margins_multiclass():
    # 3 muestras, 4 clases
    logits = np.array([
        [2.0, 5.0, 1.0, 3.0],  # top-1: 5.0, top-2: 3.0 -> margen = 2.0
        [1.0, 1.2, 0.0, 0.5],  # top-1: 1.2, top-2: 1.0 -> margen = 0.2
        [-1.0, -2.0, 4.0, 0.0],# top-1: 4.0, top-2: 0.0 -> margen = 4.0
    ])
    margins = compute_margins(logits)
    assert np.allclose(margins, [2.0, 0.2, 4.0])


def test_summarize_oracle_and_harm():
    loss_base = np.array([0.0, 1.0, 1.0, 0.0])  # Base acierta 0 y 3, falla 1 y 2
    gains_by_action = {
        "action_A": np.array([0.0, 1.0, 0.0, -1.0]),  # Repara 1, daña 3
        "action_B": np.array([0.0, 0.0, 1.0, 0.0]),   # Repara 2, neutral 3
    }
    summary = summarize_oracle_and_harm(loss_base, gains_by_action)
    
    assert summary["base_accuracy"] == 0.5
    # Oráculo con parada:
    # muestra 0: max gain = 0 -> STOP -> correcto
    # muestra 1: action_A repara (+1) -> correcto
    # muestra 2: action_B repara (+1) -> correcto
    # muestra 3: action_A daña (-1), action_B neutral (0) -> STOP -> correcto
    # En las 4 muestras el oráculo con parada acierta!
    assert summary["oracle_with_stop_accuracy"] == 1.0
    assert summary["oracle_headroom"] == 0.5  # de 0.5 a 1.0 = +0.5
    assert summary["repairable_fraction_of_errors"] == 1.0
    assert summary["any_candidate_harms_fraction"] == 0.25  # muestra 3
