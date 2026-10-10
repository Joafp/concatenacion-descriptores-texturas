"""Pruebas unitarias para el piloto interno P1-P3 de frontera de bases, presupuestos y puerta de continuidad."""

from pathlib import Path
import numpy as np
import pytest

from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.crossfit import ProtectedFeatureStore
from scripts.run_fsc_tex_p1_p3_internal_pilot import (
    run_p1_base_frontier_analysis,
    run_p2_feasible_budget_and_horizon_sweep,
    run_p3_integrity_and_nested_pca_and_permutation_test,
    evaluate_continuity_gate,
)


def test_p1_p3_internal_pilot_synthetic_run():
    rng = np.random.default_rng(42)
    N_tr = 60
    d_dim = 16
    y_tr = np.tile([0, 1, 2], N_tr // 3)
    inner_groups = np.arange(N_tr)

    # Bloques sintéticos
    emb_resnet = rng.standard_normal((N_tr, d_dim)).astype(np.float32)
    emb_resnet[y_tr == 0, 0] += 1.5

    emb_siglip = rng.standard_normal((N_tr, d_dim)).astype(np.float32)
    emb_siglip[y_tr == 1, 1] += 2.0

    emb_beit = rng.standard_normal((N_tr, d_dim)).astype(np.float32)
    emb_beit[y_tr == 2, 2] += 2.5

    emb_dino = rng.standard_normal((N_tr, d_dim)).astype(np.float32)
    emb_conv = rng.standard_normal((N_tr, d_dim)).astype(np.float32)
    emb_eva = rng.standard_normal((N_tr, d_dim)).astype(np.float32)

    raw_cache = {
        "resnet50": emb_resnet,
        "siglip_base": emb_siglip,
        "beitv2_base_final": emb_beit,
        "dinov2": emb_dino,
        "convnext_v2_t": emb_conv,
        "eva02_base": emb_eva,
    }

    feature_store = ProtectedFeatureStore(raw_cache)
    cost_model = HardwareCostModel(cost_mode="hardware")
    train_idx = np.arange(N_tr)
    pool = ["resnet50", "siglip_base", "beitv2_base_final", "dinov2", "convnext_v2_t", "eva02_base"]

    # 1. P1: Análisis de Frontera de Bases
    p1_res = run_p1_base_frontier_analysis(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_tr,
        inner_groups=inner_groups,
        candidate_bases=["resnet50", "siglip_base"],
        pool=pool,
        cost_model=cost_model,
        n_splits=2,
        seed=42,
    )

    assert "individual_performance" in p1_res
    assert "best_individual" in p1_res
    assert "resnet50" in p1_res["base_analysis"]
    assert "siglip_base" in p1_res["base_analysis"]
    assert "best_static_pair" in p1_res["base_analysis"]["resnet50"]

    # 2. P2: Barrido de Presupuestos
    p2_res = run_p2_feasible_budget_and_horizon_sweep(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_tr,
        inner_groups=inner_groups,
        base_extractor="resnet50",
        pool=pool,
        cost_model=cost_model,
        budgets_ms=[35.0, 45.0],
        n_inner_splits=2,
        seed=42,
    )

    assert "budget_35ms" in p2_res
    assert "budget_45ms" in p2_res
    assert "fsc_tex_h1" in p2_res["budget_45ms"]
    assert "fsc_tex_h2" in p2_res["budget_45ms"]
    assert "multistep_acquisitions_pct" in p2_res["budget_45ms"]["fsc_tex_h2"]

    # 3. P3: Integridad y Permutación
    p3_res = run_p3_integrity_and_nested_pca_and_permutation_test(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_tr,
        inner_groups=inner_groups,
        base_extractor="resnet50",
        pool=pool,
        cost_model=cost_model,
        target_budget_ms=45.0,
        seed=42,
    )

    assert p3_res["producer_folds_count"] >= 2
    assert "permutation_test" in p3_res
    assert "permuted_policy_f1" in p3_res["permutation_test"]

    # 4. Puerta de Continuidad
    gate_res = evaluate_continuity_gate(p1_res, p2_res, p3_res, budget_key="budget_45ms")
    assert "overall_status" in gate_res
    assert "gate_1_beats_base" in gate_res
    assert "gate_2_beats_or_dominates_best_ind" in gate_res
    assert "gate_4_multistep_feasible_observed" in gate_res
