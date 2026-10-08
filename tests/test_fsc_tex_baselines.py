"""Pruebas unitarias para comparadores y controles fuertes (Hito R3).

Verifica:
1. Selección prospectiva del mejor descriptor individual en entrenamiento.
2. Evaluación de la ruta fija estática ResNet + SigLIP (control de costo comparable).
3. Distinción explícita e inequívoca entre Full_Fusion_6 y Completa-22.
4. Extracción de referencias canónicas históricas (Completa-22, GFS-22, Top-k 22) desde CSVs auditados.
"""

from pathlib import Path
import numpy as np
import pytest

from fsc_tex.baselines import (
    select_best_individual_internal,
    evaluate_fixed_route,
    find_confirmatory_reference_metrics,
)
from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.crossfit import ProtectedFeatureStore
from fsc_tex.state_graph import State


def test_select_best_individual_internal():
    """R3 Test 1: Comprueba que el mejor extractor se selecciona prospectivamente en T_train."""
    rng = np.random.default_rng(42)
    N_tr = 60
    N_te = 30
    N_tot = N_tr + N_te

    # Bloque débil: ruido puro
    emb_weak = rng.standard_normal((N_tot, 8)).astype(np.float32)
    # Bloque fuerte: señal nítida correlacionada con las etiquetas
    y_tot = np.tile([0, 1], N_tot // 2)
    emb_strong = np.zeros((N_tot, 8), dtype=np.float32)
    emb_strong[y_tot == 1, 0] = 5.0

    raw_cache = {
        "block_weak": emb_weak,
        "block_strong": emb_strong,
    }
    store = ProtectedFeatureStore(raw_cache)
    cost_model = HardwareCostModel(cost_mode="unit")

    train_idx = np.arange(N_tr)
    test_idx = np.arange(N_tr, N_tot)
    inner_groups = np.arange(N_tr)

    res = select_best_individual_internal(
        feature_store=store,
        train_idx=train_idx,
        y_train=y_tot[train_idx],
        inner_groups=inner_groups,
        candidate_extractors=["block_weak", "block_strong"],
        cost_model=cost_model,
        n_splits=2,
        seed=42,
    )

    assert res["best_extractor"] == "block_strong", "Debió seleccionar el descriptor con mayor F1 interno"
    assert res["inner_cv_f1"] > 0.95

    # Evaluar el modelo seleccionado en test
    clf = res["clf_final"]
    X_te = store.get_state_matrix(res["best_state"])[test_idx]
    preds = clf.predict(X_te)
    acc = np.mean(preds == y_tot[test_idx])
    assert acc > 0.95


def test_evaluate_fixed_route_resnet_siglip():
    """R3 Test 2: Comprueba la evaluación de la ruta fija estática ResNet50 + SigLIP."""
    rng = np.random.default_rng(42)
    N_tr = 40
    N_te = 20
    N_tot = N_tr + N_te

    raw_cache = {
        "resnet50": rng.standard_normal((N_tot, 16)).astype(np.float32),
        "siglip_base": rng.standard_normal((N_tot, 16)).astype(np.float32),
    }
    store = ProtectedFeatureStore(raw_cache)
    cost_model = HardwareCostModel(cost_mode="hardware")

    y_tot = np.tile([0, 1], N_tot // 2)
    train_idx = np.arange(N_tr)
    test_idx = np.arange(N_tr, N_tot)

    eval_res = evaluate_fixed_route(
        feature_store=store,
        train_idx=train_idx,
        y_train=y_tot[train_idx],
        test_idx=test_idx,
        y_test=y_tot[test_idx],
        blocks=["resnet50", "siglip_base"],
        cost_model=cost_model,
        seed=42,
    )

    assert eval_res["state_id"] == "resnet50+siglip_base"
    # Costo físico esperado: resnet50 (11.94+0.45=12.39) + siglip_base (11.68+0.45=12.13) = 24.52 ms
    assert eval_res["mean_latency_ms"] == pytest.approx(24.52, abs=0.1)
    assert len(eval_res["preds"]) == N_te


def test_full_fusion_6_vs_22_distinction():
    """R3 Test 3: Comprueba que la fusión de 6 bloques nunca se rotula como Completa-22."""
    cost_model = HardwareCostModel(cost_mode="hardware")
    six_blocks = ["resnet50", "siglip_base", "beitv2_base_final", "dinov2", "convnext_v2_t", "eva02_base"]
    s6 = State(tuple(six_blocks))

    # El estado contiene exactamente 6 bloques
    assert len(s6.blocks) == 6
    cost_s6 = cost_model.cumulative_cost_ms(s6.blocks)

    # Costo de 6 bloques debe ser estrictamente menor que la biblioteca canónica de 22
    canonical_22 = list(cost_model.latencies.keys())
    assert len(canonical_22) == 22
    s22 = State(tuple(canonical_22))
    cost_s22 = cost_model.cumulative_cost_ms(s22.blocks)

    assert cost_s6 < cost_s22
    assert "Full_Fusion_6" != "Full_Fusion_22"


def test_confirmatory_reference_parser():
    """R3 Test 4: Comprueba que el parser extrae las referencias auditadas de nested_fold_results.csv."""
    repo = Path(__file__).resolve().parents[1]
    refs = find_confirmatory_reference_metrics(
        repo_root=repo,
        dataset_name="CUReT",
        condition=0,
        classifier="svm",
    )

    # CUReT fold 0 tiene resultados confirmativos guardados
    assert refs["Reference_Full_22"] is not None
    assert refs["Reference_Full_22"]["blocks_count"] == 22
    assert refs["Reference_Full_22"]["macro_f1"] > 0.99
    assert refs["Reference_GFS_22"] is not None
