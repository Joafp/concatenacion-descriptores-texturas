"""Pruebas unitarias para el piloto de adquisición residual y ablaciones (Hito R4).

Comprueba la ejecución end-to-end de run_residual_acquisition_pilot:
- Presencia y validez de todos los controles fuertes (Base, Best Individual, Static Pair, Cascade, Full-6).
- Cálculo de variantes FSC-Tex (H1, H2 Bellman, H2 con representación enriquecida).
- Resumen estructurado de las ablaciones mínimas.
- Evaluación diagnóstica de la puerta de avance.
"""

from pathlib import Path
import numpy as np
import pytest

from fsc_tex.pilot import run_residual_acquisition_pilot


def test_residual_acquisition_pilot_synthetic_execution():
    """R4 Test: Comprueba la ejecución completa del piloto de desarrollo con todas sus ablaciones."""
    rng = np.random.default_rng(42)
    N_tr = 60
    N_te = 30
    N_tot = N_tr + N_te
    d_dim = 16

    # Clases binarias balanceadas
    y_tot = np.tile([0, 1], N_tot // 2)

    # 1. Base (ResNet50): señal moderada
    emb_resnet = rng.standard_normal((N_tot, d_dim)).astype(np.float32)
    emb_resnet[y_tot == 1, 0] += 1.0

    # 2. SigLIP: señal complementaria
    emb_siglip = rng.standard_normal((N_tot, d_dim)).astype(np.float32)
    emb_siglip[y_tot == 0, 1] += 1.5

    # 3. BEiTv2: señal adicional
    emb_beit = rng.standard_normal((N_tot, d_dim)).astype(np.float32)
    emb_beit[y_tot == 1, 2] += 2.0

    # 4. DINOv2: señal fuerte pero costosa
    emb_dino = rng.standard_normal((N_tot, d_dim)).astype(np.float32)
    emb_dino[y_tot == 1, 3] += 3.0

    # 5. ConvNeXt y EVA02
    emb_conv = rng.standard_normal((N_tot, d_dim)).astype(np.float32)
    emb_eva = rng.standard_normal((N_tot, d_dim)).astype(np.float32)

    raw_cache = {
        "resnet50": emb_resnet,
        "siglip_base": emb_siglip,
        "beitv2_base_final": emb_beit,
        "dinov2": emb_dino,
        "convnext_v2_t": emb_conv,
        "eva02_base": emb_eva,
    }

    train_idx = np.arange(N_tr)
    test_idx = np.arange(N_tr, N_tot)
    inner_groups = np.arange(N_tr)
    repo = Path(__file__).resolve().parents[1]

    pilot_report = run_residual_acquisition_pilot(
        raw_cache=raw_cache,
        y=y_tot,
        train_idx=train_idx,
        test_idx=test_idx,
        inner_groups=inner_groups,
        dataset_name="DTD",
        condition=1,
        base_extractor="resnet50",
        candidate_subset=["siglip_base", "beitv2_base_final", "dinov2", "convnext_v2_t", "eva02_base"],
        target_budget_ms=35.0,
        repo_root=repo,
        seed=42,
    )

    # 1. Comprobar tabla de resultados completa
    res_table = pilot_report["results_table"]
    expected_methods = [
        "Base_resnet50",
        "Best_Individual_Internal",
        "Static_Pair_ResNet_SigLIP",
        "Cascade_TopK_Prospective",
        "FSC_Tex_H1_Myopic",
        "FSC_Tex_H2_Bellman",
        "FSC_Tex_H2_Enriched_State",
        "Full_Fusion_6",
    ]
    for m in expected_methods:
        assert m in res_table, f"Método {m} debe estar en la tabla del piloto"
        assert "macro_f1" in res_table[m]
        assert "accuracy" in res_table[m]
        assert "mean_latency_ms" in res_table[m]
        assert 0.0 <= res_table[m]["macro_f1"] <= 1.0

    # 2. Comprobar ablaciones mínimas
    ablations = pilot_report["ablations_summary"]
    assert "ablation_1_h1_vs_h2" in ablations
    assert "ablation_2_uncertainty_vs_enriched" in ablations
    assert "ablation_3_adaptive_vs_static_pair" in ablations

    # 3. Comprobar evaluación diagnóstica de la puerta
    gate = pilot_report["gate_assessment"]
    assert "gate_beats_base" in gate
    assert "gate_savings_vs_full_pct" in gate
    assert "status" in gate
    assert gate["status"] in ("PASS", "INCONCLUSIVE")
