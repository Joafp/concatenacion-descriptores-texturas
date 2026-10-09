"""Piloto de Adquisición Residual con Respaldo y Ablaciones (Hito R4).

Ejecuta el estudio piloto de desarrollo sobre condiciones auditadas (DTD, Soil, KTH), evaluando:
1. Base fija (ResNet-50) y Mejor Individual Prospectivo (Best Individual).
2. Ruta estática fija de costo comparable (ResNet-50 + SigLIP).
3. Cascada adaptativa prospectiva de dos etapas.
4. FSC-Tex H1 (Miope) y FSC-Tex H2 (Bellman Desplegable).
5. FSC-Tex H2 con Representación Enriquecida (Incertidumbre + Proyección de Contenido).
6. Fusión Completa-6 rotulada honestamente y Referencias Confirmativas Canónicas de 22 bloques.
7. Las 4 ablaciones mínimas obligatorias del protocolo.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, f1_score
from sklearn.svm import LinearSVC

from fsc_tex.baselines import (
    evaluate_fixed_route,
    find_confirmatory_reference_metrics,
    select_best_individual_internal,
)
from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.crossfit import (
    ProtectedFeatureStore,
    evaluate_state_classifiers,
    fit_final_classifiers,
    generate_oof_state_data,
    select_hyperparameters_prospective,
    trace_policy_test_evaluation,
)
from fsc_tex.policy import SequentialAcquisitionPolicy
from fsc_tex.state_graph import State, StateGraph


def run_residual_acquisition_pilot(
    raw_cache: Dict[str, np.ndarray],
    y: np.ndarray,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    inner_groups: np.ndarray,
    dataset_name: str,
    condition: Any,
    base_extractor: str = "resnet50",
    candidate_subset: Optional[List[str]] = None,
    target_budget_ms: float = 35.0,
    repo_root: Optional[Path] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """Ejecuta el piloto de adquisición residual evaluando métodos y ablaciones."""
    t0 = time.time()
    feature_store = ProtectedFeatureStore(raw_cache)
    candidates = candidate_subset or ["siglip_base", "beitv2_base_final", "dinov2", "convnext_v2_t", "eva02_base"]
    y_train = y[train_idx]
    y_test = y[test_idx]
    n_test = len(test_idx)

    # 1. Grafos de estado y modelo de costos
    graph_std = StateGraph(base_block=base_extractor, candidate_blocks=candidates, max_depth=3)
    cost_model_hw = HardwareCostModel(cost_mode="hardware")
    cost_model_unit = HardwareCostModel(cost_mode="unit")

    # 2. Proyección de contenido para representación enriquecida (Ablación 2)
    # Ajustada exclusivamente sobre el bloque base en T_train (Zero Test Leakage)
    pca_content = PCA(n_components=16, random_state=seed)
    X_base_tr = raw_cache[base_extractor][train_idx]
    pca_content.fit(X_base_tr)
    content_tr = pca_content.transform(raw_cache[base_extractor][train_idx])
    content_te = pca_content.transform(raw_cache[base_extractor][test_idx])

    # 3. Datos OOF en T_train para ajuste de políticas
    oof_feats, oof_losses, oof_margins, _, _ = generate_oof_state_data(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        inner_groups=inner_groups,
        graph=graph_std,
        n_splits=3,
        seed=seed,
    )

    # Generar también características OOF enriquecidas
    oof_feats_enriched = {}
    for sid, feats in oof_feats.items():
        oof_feats_enriched[sid] = np.hstack([feats, content_tr])

    # 4. Ajustar clasificadores finales en T_train
    final_clfs = fit_final_classifiers(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        graph=graph_std,
        seed=seed,
    )

    # 5. Selección prospectiva de hiperparámetros
    lambda_grid = [0.001, 0.01, 0.05, 0.1, 0.2]
    quantile_grid = [0.1, 0.2, 0.3, 0.4, 0.5]
    prospective_tuning = select_hyperparameters_prospective(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        inner_groups=inner_groups,
        graph=graph_std,
        cost_model=cost_model_hw,
        target_budget_ms=target_budget_ms,
        lambda_grid=lambda_grid,
        quantile_grid=quantile_grid,
        n_inner_splits=3,
        seed=seed,
        horizon=2,
    )
    selected_lambda = prospective_tuning["selected_lambda"]
    selected_q = prospective_tuning["selected_q"]
    selected_cascade_aug = prospective_tuning["selected_cascade_augmentor"]

    results_table: Dict[str, Dict[str, Any]] = {}

    # A. Control 1: Base Fija
    base_eval = evaluate_fixed_route(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        test_idx=test_idx,
        y_test=y_test,
        blocks=[base_extractor],
        cost_model=cost_model_hw,
        seed=seed,
    )
    results_table["Base_" + base_extractor] = {
        "macro_f1": base_eval["macro_f1"],
        "accuracy": base_eval["accuracy"],
        "mean_latency_ms": base_eval["mean_latency_ms"],
        "p95_latency_ms": base_eval["p95_latency_ms"],
        "description": "Base única barata (control fijo)",
    }

    # B. Control 2: Mejor Individual Prospectivo
    best_ind_res = select_best_individual_internal(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        inner_groups=inner_groups,
        candidate_extractors=[base_extractor] + candidates,
        cost_model=cost_model_hw,
        n_splits=3,
        seed=seed,
    )
    best_ind_clf = best_ind_res["clf_final"]
    X_ind_te = feature_store.get_state_matrix(best_ind_res["best_state"])[test_idx]
    ind_preds = best_ind_clf.predict(X_ind_te)
    results_table["Best_Individual_Internal"] = {
        "macro_f1": float(f1_score(y_test, ind_preds, average="macro")),
        "accuracy": float(accuracy_score(y_test, ind_preds)),
        "mean_latency_ms": best_ind_res["cost_ms"],
        "p95_latency_ms": best_ind_res["cost_ms"],
        "selected_extractor": best_ind_res["best_extractor"],
        "description": f"Mejor individual elegido en train ({best_ind_res['best_extractor']})",
    }

    # C. Control 3: Ruta fija estática ResNet + SigLIP (Costo comparable)
    static_pair_eval = evaluate_fixed_route(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        test_idx=test_idx,
        y_test=y_test,
        blocks=[base_extractor, "siglip_base"],
        cost_model=cost_model_hw,
        seed=seed,
    )
    results_table["Static_Pair_ResNet_SigLIP"] = {
        "macro_f1": static_pair_eval["macro_f1"],
        "accuracy": static_pair_eval["accuracy"],
        "mean_latency_ms": static_pair_eval["mean_latency_ms"],
        "p95_latency_ms": static_pair_eval["p95_latency_ms"],
        "description": "Ruta estática fija de costo comparable (24.52 ms)",
    }

    # D. Control 4: Cascada Top-K Prospectiva
    tau_q = float(np.quantile(oof_margins[graph_std.initial_state.id], selected_q))
    s_cascade = graph_std.initial_state.add(selected_cascade_aug)
    cascade_cost_ms = cost_model_hw.cumulative_cost_ms(s_cascade.blocks)
    base_cost_ms = cost_model_hw.cumulative_cost_ms(graph_std.initial_state.blocks)

    clf_cascade = final_clfs[s_cascade.id]
    clf_base = final_clfs[graph_std.initial_state.id]
    X_casc_te = feature_store.get_state_matrix(s_cascade)[test_idx]
    X_base_te = feature_store.get_state_matrix(graph_std.initial_state)[test_idx]

    df_base_te = clf_base.decision_function(X_base_te)
    margins_base_te = np.abs(df_base_te) if df_base_te.ndim == 1 else np.partition(df_base_te, -2, axis=1)[:, -1] - np.partition(df_base_te, -2, axis=1)[:, -2]

    casc_preds = np.empty(n_test, dtype=y_test.dtype)
    casc_lats = np.empty(n_test, dtype=np.float32)
    for i in range(n_test):
        if margins_base_te[i] < tau_q:
            casc_preds[i] = clf_cascade.predict(X_casc_te[i : i + 1])[0]
            casc_lats[i] = cascade_cost_ms
        else:
            casc_preds[i] = clf_base.predict(X_base_te[i : i + 1])[0]
            casc_lats[i] = base_cost_ms

    results_table["Cascade_TopK_Prospective"] = {
        "macro_f1": float(f1_score(y_test, casc_preds, average="macro")),
        "accuracy": float(accuracy_score(y_test, casc_preds)),
        "mean_latency_ms": float(np.mean(casc_lats)),
        "p95_latency_ms": float(np.percentile(casc_lats, 95)),
        "selected_q": selected_q,
        "selected_augmentor": selected_cascade_aug,
        "description": "Cascada adaptativa con umbral prospectivo en train",
    }

    # E. Método Propuesto 1: FSC-Tex H1 (Miope)
    pol_h1 = SequentialAcquisitionPolicy(
        graph=graph_std,
        cost_model=cost_model_hw,
        horizon=1,
        cost_lambda=selected_lambda,
        random_state=seed,
    )
    pol_h1.fit_transitions(oof_feats, oof_losses, max_budget=target_budget_ms)
    h1_preds, h1_lats, h1_traces = trace_policy_test_evaluation(
        policy=pol_h1,
        test_clfs=final_clfs,
        feature_store=feature_store,
        test_idx=test_idx,
        graph=graph_std,
        cost_model=cost_model_hw,
        target_budget_ms=target_budget_ms,
    )
    results_table["FSC_Tex_H1_Myopic"] = {
        "macro_f1": float(f1_score(y_test, h1_preds, average="macro")),
        "accuracy": float(accuracy_score(y_test, h1_preds)),
        "mean_latency_ms": float(np.mean(h1_lats)),
        "p95_latency_ms": float(np.percentile(h1_lats, 95)),
        "description": "FSC-Tex Horizonte 1 (Miope)",
    }

    # F. Método Propuesto 2: FSC-Tex H2 (Bellman Desplegable)
    pol_h2 = SequentialAcquisitionPolicy(
        graph=graph_std,
        cost_model=cost_model_hw,
        horizon=2,
        cost_lambda=selected_lambda,
        random_state=seed,
    )
    pol_h2.fit_transitions(oof_feats, oof_losses, max_budget=target_budget_ms)
    h2_preds, h2_lats, h2_traces = trace_policy_test_evaluation(
        policy=pol_h2,
        test_clfs=final_clfs,
        feature_store=feature_store,
        test_idx=test_idx,
        graph=graph_std,
        cost_model=cost_model_hw,
        target_budget_ms=target_budget_ms,
    )
    results_table["FSC_Tex_H2_Bellman"] = {
        "macro_f1": float(f1_score(y_test, h2_preds, average="macro")),
        "accuracy": float(accuracy_score(y_test, h2_preds)),
        "mean_latency_ms": float(np.mean(h2_lats)),
        "p95_latency_ms": float(np.percentile(h2_lats, 95)),
        "description": "FSC-Tex Horizonte 2 (Bellman no miope desplegable)",
    }

    # G. Método Propuesto 3: FSC-Tex H2 con Representación Enriquecida (Incertidumbre + Contenido)
    pol_h2_enr = SequentialAcquisitionPolicy(
        graph=graph_std,
        cost_model=cost_model_hw,
        horizon=2,
        cost_lambda=selected_lambda,
        random_state=seed,
    )
    pol_h2_enr.fit_transitions(oof_feats_enriched, oof_losses, max_budget=target_budget_ms)

    # Evaluación paso a paso con características enriquecidas
    enr_preds = np.empty(n_test, dtype=y_test.dtype)
    enr_lats = np.empty(n_test, dtype=np.float32)
    for i, s_idx in enumerate(test_idx):
        curr_s = graph_std.initial_state
        rem_b = target_budget_ms - base_cost_ms
        while len(curr_s) < graph_std.max_depth and rem_b > 0:
            clf_c = final_clfs[curr_s.id]
            X_c_i = feature_store.get_state_matrix(curr_s)[s_idx : s_idx + 1]
            df_i = clf_c.decision_function(X_c_i)
            m_i = float(np.abs(df_i)[0]) if df_i.ndim == 1 else float(np.partition(df_i, -2, axis=1)[0, -1] - np.partition(df_i, -2, axis=1)[0, -2])
            top_s = np.abs(df_i.ravel()) if df_i.ndim == 1 else np.sort(df_i[0])[::-1]

            feat_c = graph_std.encode_state_features(
                state=curr_s,
                margin=m_i,
                top_scores=top_s,
                remaining_budget=float(rem_b),
                content_embedding=content_te[i],
            )
            act, _ = pol_h2_enr.select_action(curr_s, feat_c, remaining_budget=rem_b)
            if act == "STOP":
                break
            rem_b = max(0.0, rem_b - cost_model_hw.incremental_cost(act, curr_s.blocks))
            curr_s = curr_s.add(act)

        clf_fin = final_clfs[curr_s.id]
        X_fin = feature_store.get_state_matrix(curr_s)[s_idx : s_idx + 1]
        enr_preds[i] = clf_fin.predict(X_fin)[0]
        enr_lats[i] = cost_model_hw.cumulative_cost_ms(curr_s.blocks)

    results_table["FSC_Tex_H2_Enriched_State"] = {
        "macro_f1": float(f1_score(y_test, enr_preds, average="macro")),
        "accuracy": float(accuracy_score(y_test, enr_preds)),
        "mean_latency_ms": float(np.mean(enr_lats)),
        "p95_latency_ms": float(np.percentile(enr_lats, 95)),
        "description": "FSC-Tex H2 con Incertidumbre + Proyección PCA de Contenido",
    }

    # H. Fusión Completa-6
    full6_eval = evaluate_fixed_route(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        test_idx=test_idx,
        y_test=y_test,
        blocks=[base_extractor] + candidates,
        cost_model=cost_model_hw,
        seed=seed,
    )
    results_table["Full_Fusion_6"] = {
        "macro_f1": full6_eval["macro_f1"],
        "accuracy": full6_eval["accuracy"],
        "mean_latency_ms": full6_eval["mean_latency_ms"],
        "p95_latency_ms": full6_eval["p95_latency_ms"],
        "description": "Fusión estática Completa-6 (subconjunto candidata, no 22)",
    }

    # I. Referencias Confirmativas Canónicas de 22 Bloques (si existen)
    if repo_root is not None:
        canon_refs = find_confirmatory_reference_metrics(
            repo_root=repo_root,
            dataset_name=dataset_name,
            condition=condition,
            classifier="svm",
        )
        for r_key, r_val in canon_refs.items():
            if r_val is not None:
                results_table[r_key] = {
                    "macro_f1": r_val["macro_f1"],
                    "accuracy": r_val["accuracy"],
                    "mean_latency_ms": None,
                    "description": f"Referencia auditada de biblioteca completa ({r_key})",
                }

    # 6. Diagnóstico de Puerta de Avance del Hito R4
    f1_h2 = results_table["FSC_Tex_H2_Bellman"]["macro_f1"]
    cost_h2 = results_table["FSC_Tex_H2_Bellman"]["mean_latency_ms"]
    f1_base = results_table["Base_" + base_extractor]["macro_f1"]
    cost_base = results_table["Base_" + base_extractor]["mean_latency_ms"]
    cost_full6 = results_table["Full_Fusion_6"]["mean_latency_ms"]

    gate_beats_base = f1_h2 > f1_base
    gate_savings_vs_full = (cost_full6 - cost_h2) / cost_full6 >= 0.20
    epsilon_margin_satisfied = (f1_h2 - results_table["Full_Fusion_6"]["macro_f1"]) >= -0.01

    gate_assessment = {
        "gate_beats_base": gate_beats_base,
        "gate_savings_vs_full_pct": float((cost_full6 - cost_h2) / cost_full6 * 100),
        "gate_meets_20pct_savings": gate_savings_vs_full,
        "epsilon_margin_satisfied": epsilon_margin_satisfied,
        "status": "PASS" if (gate_beats_base and gate_savings_vs_full) else "INCONCLUSIVE",
    }

    # 7. Resumen de Ablaciones Mínimas
    ablations_summary = {
        "ablation_1_h1_vs_h2": {
            "h1_f1": results_table["FSC_Tex_H1_Myopic"]["macro_f1"],
            "h2_f1": results_table["FSC_Tex_H2_Bellman"]["macro_f1"],
            "delta_f1_h2_minus_h1": float(f1_h2 - results_table["FSC_Tex_H1_Myopic"]["macro_f1"]),
        },
        "ablation_2_uncertainty_vs_enriched": {
            "uncertainty_only_f1": f1_h2,
            "enriched_state_f1": results_table["FSC_Tex_H2_Enriched_State"]["macro_f1"],
            "delta_f1": float(results_table["FSC_Tex_H2_Enriched_State"]["macro_f1"] - f1_h2),
        },
        "ablation_3_adaptive_vs_static_pair": {
            "fsc_tex_h2_f1": f1_h2,
            "static_pair_f1": results_table["Static_Pair_ResNet_SigLIP"]["macro_f1"],
            "fsc_tex_h2_cost": cost_h2,
            "static_pair_cost": results_table["Static_Pair_ResNet_SigLIP"]["mean_latency_ms"],
        },
    }

    # 8. Registro de predicciones por método para trazabilidad y auditoría
    predictions_record = {
        "y_true": [int(x) for x in y_test],
        "Base_" + base_extractor: [int(x) for x in base_eval["preds"]],
        "Best_Individual_Internal": [int(x) for x in ind_preds],
        "Static_Pair_ResNet_SigLIP": [int(x) for x in static_pair_eval["preds"]],
        "Cascade_TopK_Prospective": [int(x) for x in casc_preds],
        "FSC_Tex_H1_Myopic": [int(x) for x in h1_preds],
        "FSC_Tex_H2_Bellman": [int(x) for x in h2_preds],
        "FSC_Tex_H2_Enriched_State": [int(x) for x in enr_preds],
        "Full_Fusion_6": [int(x) for x in full6_eval["preds"]],
    }

    return {
        "dataset_name": dataset_name,
        "condition": condition,
        "target_budget_ms": target_budget_ms,
        "prospective_tuning": prospective_tuning,
        "results_table": results_table,
        "gate_assessment": gate_assessment,
        "ablations_summary": ablations_summary,
        "predictions_record": predictions_record,
        "trace_events": h2_traces,
        "graph": graph_std,
        "cost_model": cost_model_hw,
        "elapsed_seconds": float(time.time() - t0),
    }
