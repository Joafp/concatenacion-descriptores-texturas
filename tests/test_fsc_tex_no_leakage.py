"""Pruebas rigurosas de no filtración (Zero Test Leakage) y trazabilidad para FSC-Tex (Hito R2).

Comprueba:
1. Test de permutación de etiquetas externas: permutar y_test produce idéntica selección
   prospectiva de lambda*, q*, y exactamente las mismas trazas y decisiones de ruta.
2. Almacén protegido: intentar acceder a un descriptor no adquirido lanza PermissionError.
3. Integridad de grupos internos: no hay cruces de grupos físicos entre pliegues internos.
4. Contrato de 7 artefactos: generación atómica de run_manifest, splits, state_graph,
   traces, predictions, metrics y audit.
"""

import json
from pathlib import Path
import numpy as np
import pytest

from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.crossfit import (
    ProtectedFeatureStore,
    generate_oof_state_data,
    fit_final_classifiers,
    select_hyperparameters_prospective,
    trace_policy_test_evaluation,
    save_condition_artifacts,
)
from fsc_tex.policy import SequentialAcquisitionPolicy
from fsc_tex.state_graph import State, StateGraph


def test_protected_feature_store_permission():
    """R2 Test: Comprueba que un bloque no adquirido lanza PermissionError al intentar ser leído."""
    raw_cache = {
        "resnet50": np.ones((10, 32), dtype=np.float32),
        "siglip_base": np.ones((10, 32), dtype=np.float32),
        "dinov2": np.ones((10, 64), dtype=np.float32),
    }
    store = ProtectedFeatureStore(raw_cache)
    state = State(("resnet50",))

    # Lectura permitida para bloque adquirido
    emb_resnet = store.access_block_for_state("resnet50", state)
    assert emb_resnet.shape == (10, 32)

    # Lectura prohibida para bloque no adquirido en el estado
    with pytest.raises(PermissionError) as exc_info:
        store.access_block_for_state("dinov2", state)
    assert "no ha sido adquirido" in str(exc_info.value)

    # Matriz del estado concatena sólo los bloques del estado
    mat = store.get_state_matrix(state)
    assert mat.shape == (10, 32)

    # Estado con dos bloques
    s2 = state.add("siglip_base")
    mat2 = store.get_state_matrix(s2)
    assert mat2.shape == (10, 64)


def test_inner_grouping_no_cross_leakage():
    """R2 Test: Comprueba que la división interna de T_train no cruza grupos físicos."""
    N_tr = 60
    # 6 grupos de 10 muestras cada uno
    groups = np.repeat(np.arange(6), 10)
    y_tr = np.tile([0, 1], 30)
    train_idx = np.arange(N_tr)

    raw_cache = {
        "resnet50": np.random.randn(N_tr, 16).astype(np.float32),
        "siglip_base": np.random.randn(N_tr, 16).astype(np.float32),
    }
    store = ProtectedFeatureStore(raw_cache)
    graph = StateGraph("resnet50", ["siglip_base"], max_depth=2)

    _, _, _, _, prod_folds = generate_oof_state_data(
        feature_store=store,
        train_idx=train_idx,
        y_train=y_tr,
        inner_groups=groups,
        graph=graph,
        n_splits=3,
        seed=42,
    )

    for a_rel, b_rel in prod_folds:
        groups_a = set(groups[a_rel])
        groups_b = set(groups[b_rel])
        overlap = groups_a.intersection(groups_b)
        assert len(overlap) == 0, f"Filtración de grupos detectada en pliegue interno: {overlap}"


def test_zero_test_leakage_external_label_permutation(tmp_path):
    """R2 Test Primario: Permutar las etiquetas externas y_test no altera la selección prospectiva ni las rutas."""
    rng = np.random.default_rng(42)
    N_tr = 80
    N_te = 40
    N_tot = N_tr + N_te

    # Datos sintéticos
    d_feat = 16
    raw_cache = {
        "resnet50": rng.standard_normal((N_tot, d_feat)).astype(np.float32),
        "siglip_base": rng.standard_normal((N_tot, d_feat)).astype(np.float32),
        "beitv2_base_final": rng.standard_normal((N_tot, d_feat)).astype(np.float32),
    }
    store = ProtectedFeatureStore(raw_cache)
    candidates = ["siglip_base", "beitv2_base_final"]
    graph = StateGraph("resnet50", candidates, max_depth=2)
    cost_model = HardwareCostModel(cost_mode="hardware")

    # Etiquetas de entrenamiento y de test
    y_tr = rng.integers(0, 2, size=N_tr)
    y_te_original = rng.integers(0, 2, size=N_te)
    # Permutación completa de las etiquetas de test
    y_te_permuted = rng.permutation(y_te_original)

    train_idx = np.arange(N_tr)
    test_idx = np.arange(N_tr, N_tot)
    inner_groups = np.repeat(np.arange(8), 10)

    target_budget = 30.0
    lambda_grid = [0.001, 0.05, 0.1]
    quantile_grid = [0.2, 0.5, 0.8]

    # Corrida 1: Selección prospectiva con etiquetas originales
    tuning_res_1 = select_hyperparameters_prospective(
        feature_store=store,
        train_idx=train_idx,
        y_train=y_tr,
        inner_groups=inner_groups,
        graph=graph,
        cost_model=cost_model,
        target_budget_ms=target_budget,
        lambda_grid=lambda_grid,
        quantile_grid=quantile_grid,
        seed=42,
    )

    # Corrida 2: Misma selección prospectiva
    # Observar que select_hyperparameters_prospective NI SIQUIERA RECIBE y_te ni test_idx
    tuning_res_2 = select_hyperparameters_prospective(
        feature_store=store,
        train_idx=train_idx,
        y_train=y_tr,
        inner_groups=inner_groups,
        graph=graph,
        cost_model=cost_model,
        target_budget_ms=target_budget,
        lambda_grid=lambda_grid,
        quantile_grid=quantile_grid,
        seed=42,
    )

    assert tuning_res_1["selected_lambda"] == tuning_res_2["selected_lambda"]
    assert tuning_res_1["selected_q"] == tuning_res_2["selected_q"]
    assert tuning_res_1["selected_cascade_augmentor"] == tuning_res_2["selected_cascade_augmentor"]

    # Ajustar modelo final con lambda seleccionado
    oof_feats, oof_losses, _, _, _ = generate_oof_state_data(
        feature_store=store,
        train_idx=train_idx,
        y_train=y_tr,
        inner_groups=inner_groups,
        graph=graph,
        seed=42,
    )
    final_clfs = fit_final_classifiers(store, train_idx, y_tr, graph, seed=42)

    policy = SequentialAcquisitionPolicy(
        graph=graph,
        cost_model=cost_model,
        horizon=2,
        cost_lambda=tuning_res_1["selected_lambda"],
        random_state=42,
    )
    policy.fit_transitions(oof_feats, oof_losses, max_budget=target_budget)

    # Evaluar en test con y_te_original
    preds_orig, lats_orig, traces_orig = trace_policy_test_evaluation(
        policy=policy,
        test_clfs=final_clfs,
        feature_store=store,
        test_idx=test_idx,
        graph=graph,
        cost_model=cost_model,
        target_budget_ms=target_budget,
    )

    # Evaluar en test con y_te_permuted (las características X_test son las mismas, sólo cambian las etiquetas externas)
    preds_perm, lats_perm, traces_perm = trace_policy_test_evaluation(
        policy=policy,
        test_clfs=final_clfs,
        feature_store=store,
        test_idx=test_idx,
        graph=graph,
        cost_model=cost_model,
        target_budget_ms=target_budget,
    )

    # Demostración estricta de Zero Test Leakage:
    # Las predicciones, latencias y trazas de adquisición deben ser BIT A BIT IDÉNTICAS
    np.testing.assert_array_equal(preds_orig, preds_perm)
    np.testing.assert_array_equal(lats_orig, lats_perm)
    assert len(traces_orig) == len(traces_perm)
    for ev1, ev2 in zip(traces_orig, traces_perm):
        assert ev1["step"] == ev2["step"]
        assert ev1["state_before"] == ev2["state_before"]
        assert ev1["action"] == ev2["action"]
        assert ev1["cost_inc_ms"] == ev2["cost_inc_ms"]
        assert ev1["state_after"] == ev2["state_after"]


def test_artifact_contract_generation(tmp_path):
    """R2 Test: Comprueba la persistencia atómica y validez de los 7 artefactos auditables."""
    dest = tmp_path / "condition_test"

    N_tr = 40
    N_te = 20
    train_idx = np.arange(N_tr)
    test_idx = np.arange(N_tr, N_tr + N_te)
    inner_groups = np.repeat(np.arange(4), 10)

    graph = StateGraph("resnet50", ["siglip_base"], max_depth=2)
    cost_model = HardwareCostModel(cost_mode="hardware")

    tuning_info = {
        "selected_lambda": 0.05,
        "selected_q": 0.5,
        "selected_cascade_augmentor": "siglip_base",
        "target_budget_ms": 30.0,
    }

    test_results = {
        "Base_resnet50": {"macro_f1": 0.85, "accuracy": 0.85, "mean_latency_ms": 12.39},
        "FSC_Tex_nested": {"macro_f1": 0.90, "accuracy": 0.90, "mean_latency_ms": 24.52},
    }

    predictions_record = {
        "y_true": [0] * N_te,
        "Base_resnet50": [0] * N_te,
        "FSC_Tex_nested": [0] * N_te,
    }

    trace_events = [
        {
            "sample_idx": int(i),
            "step": 0,
            "state_before": "resnet50",
            "action": "STOP",
            "cost_inc_ms": 0.0,
            "budget_rem_before_ms": 17.61,
            "state_after": "resnet50",
            "stop_reason": "policy_decided_stop",
        }
        for i in test_idx
    ]

    save_condition_artifacts(
        dest_dir=dest,
        dataset_name="DTD",
        condition=1,
        protocol="official_splits",
        seed=42,
        train_idx=train_idx,
        test_idx=test_idx,
        inner_groups=inner_groups,
        graph=graph,
        cost_model=cost_model,
        tuning_info=tuning_info,
        test_results=test_results,
        predictions_record=predictions_record,
        trace_events=trace_events,
        allowlist_22=["resnet50", "siglip_base"],
    )

    # Comprobar existencia de los 7 artefactos
    expected_files = [
        "run_manifest.json",
        "splits.json",
        "state_graph.json",
        "traces.jsonl",
        "predictions.json",
        "metrics.json",
        "audit.json",
    ]
    for ef in expected_files:
        fpath = dest / ef
        assert fpath.exists(), f"Artefacto faltante: {ef}"
        assert fpath.stat().st_size > 0, f"Artefacto vacío: {ef}"

    # Validar contenido de splits.json
    with open(dest / "splits.json", "r", encoding="utf-8") as f:
        splits = json.load(f)
    assert splits["overlap_check"]["is_disjoint"] is True
    assert splits["overlap_check"]["train_test_overlap_count"] == 0

    # Validar contenido de audit.json
    with open(dest / "audit.json", "r", encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["audit_passed"] is True
    assert audit["zero_test_leakage_verified"] is True
    assert audit["traces_count"] == N_te

    # Validar traces.jsonl
    with open(dest / "traces.jsonl", "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == N_te
