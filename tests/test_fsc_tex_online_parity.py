"""Pruebas unitarias de paridad física online para FSC-Tex (Hito R5).

Comprueba:
1. Carga perezosa, ejecución y warmup del registro de extractores.
2. Ejecución secuencial online bajo demanda con desglose de latencias (extracción, política, clasificador).
3. Paridad estricta (100% route agreement y prediction agreement) entre ejecución online y simulación cacheada.
"""

from PIL import Image
import numpy as np
import pytest

from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.crossfit import ProtectedFeatureStore, fit_final_classifiers, generate_oof_state_data
from fsc_tex.executor import (
    OnlineExtractorRegistry,
    OnlineSequentialPolicyExecutor,
    benchmark_physical_online_parity,
)
from fsc_tex.policy import SequentialAcquisitionPolicy
from fsc_tex.state_graph import StateGraph


def test_online_executor_and_parity_with_cached_simulation():
    """R5 Test: Comprueba la ejecución online bajo demanda y la paridad con la simulación cacheada."""
    rng = np.random.default_rng(42)
    N_tr = 40
    N_te = 20
    N_tot = N_tr + N_te
    d_dim = 16

    y_tot = np.tile([0, 1], N_tot // 2)

    # Bloques sintéticos
    v_base = rng.standard_normal((N_tot, d_dim)).astype(np.float32)
    v_cand1 = rng.standard_normal((N_tot, d_dim)).astype(np.float32)
    v_cand1[y_tot == 1, 0] += 3.0  # Fuerte señal correctiva

    raw_cache = {
        "resnet50": v_base,
        "siglip_base": v_cand1,
    }
    store = ProtectedFeatureStore(raw_cache)
    graph = StateGraph("resnet50", ["siglip_base"], max_depth=2)
    cost_model = HardwareCostModel(cost_mode="hardware")

    train_idx = np.arange(N_tr)
    test_idx = np.arange(N_tr, N_tot)
    inner_groups = np.arange(N_tr)

    # 1. Ajustar clasificadores y política
    oof_feats, oof_losses, _, _, _ = generate_oof_state_data(
        feature_store=store,
        train_idx=train_idx,
        y_train=y_tot[train_idx],
        inner_groups=inner_groups,
        graph=graph,
        seed=42,
    )
    clfs = fit_final_classifiers(store, train_idx, y_tot[train_idx], graph, seed=42)

    policy = SequentialAcquisitionPolicy(
        graph=graph,
        cost_model=cost_model,
        horizon=1,
        cost_lambda=0.01,
        random_state=42,
    )
    policy.fit_transitions(oof_feats, oof_losses)

    # 2. Configurar registro online con funciones controladas que devuelven los vectores exactos
    registry = OnlineExtractorRegistry(device="cpu", seed=42)

    def mock_extract_base(img_in):
        idx = img_in if isinstance(img_in, (int, np.integer)) else 0
        return v_base[idx]

    def mock_extract_cand1(img_in):
        idx = img_in if isinstance(img_in, (int, np.integer)) else 0
        return v_cand1[idx]

    registry.register_custom_extractor("resnet50", mock_extract_base)
    registry.register_custom_extractor("siglip_base", mock_extract_cand1)

    # 3. Probar ejecución online individual
    executor = OnlineSequentialPolicyExecutor(
        policy=policy,
        state_classifiers=clfs,
        graph=graph,
        cost_model=cost_model,
        extractor_registry=registry,
        target_budget_ms=30.0,
    )

    sample_res = executor.execute_image(test_idx[0])
    assert "final_prediction" in sample_res
    assert "route" in sample_res
    assert "total_measured_ms" in sample_res
    assert sample_res["total_measured_ms"] >= 0.0

    breakdown = sample_res["latency_breakdown_ms"]
    assert "extractor_ms" in breakdown
    assert "policy_gate_ms" in breakdown
    assert "classifier_ms" in breakdown

    # 4. Probar benchmark de paridad pareado completo
    parity_report = benchmark_physical_online_parity(
        policy=policy,
        state_classifiers=clfs,
        graph=graph,
        cost_model=cost_model,
        feature_store=store,
        extractor_registry=registry,
        test_idx=test_idx,
        image_inputs=list(test_idx),  # pasamos los índices como entradas simuladas
        target_budget_ms=30.0,
    )

    # Comprobar paridad matemática exacta
    assert parity_report["route_agreement"] == 1.0, "Las rutas online deben coincidir 100% con la simulación cacheada"
    assert parity_report["prediction_agreement"] == 1.0, "Las predicciones online deben coincidir 100% con la simulación cacheada"
    assert parity_report["parity_passed"] is True
    assert parity_report["n_samples"] == N_te
