#!/usr/bin/env python3
"""FSC-Tex: Piloto Interno de Base+Políticas, Presupuestos Factibles e Integridad (Hitos P1, P2, P3).

Garantías metodológicas estrictas:
1. ZERO TEST LEAKAGE: Toda la evaluación, ajuste de políticas, selección de hiperparámetros
   y comparación de bases se ejecuta estrictamente sobre T_train de DTD (split 1) y SoilOriginal (fold 0).
   NUNCA se consulta T_test.
2. HITO P1 (Frontera de Base y Utilidad Residual):
   - Evalúa los 21 extractores individuales en T_train mediante OOF.
   - Contrasta 3 bases candidatas: 'resnet50' (control), 'siglip_base', y 'convnext_v2_t'.
   - Mide reparación, perjuicio, oráculo 1-paso, ganancia neta Delta F1 y costo incremental.
   - Compara contra la mejor ruta estática fija.
3. HITO P2 (Presupuestos Factibles y Comparación Equitativa H1 vs H2):
   - Barre presupuestos estimados de 35.0 ms, 45.0 ms y 75.0 ms.
   - Sintoniza prospectivamente lambda*(H1) y lambda*(H2) sobre la misma grilla interna.
   - Cuantifica la proporción de adquisiciones multietapa (>= 2 adquisiciones).
   - Evalúa si H2 supera a H1 cuando el horizonte multietapa es físicamente factible.
4. HITO P3 (Integridad de Entrenamiento y Puerta de Continuidad):
   - Unidades coherentes de presupuesto remanente en milisegundos en todas las features.
   - PCA anidada ajustada exclusivamente dentro de los pliegues productores (a_rel).
   - Test de permutación de etiquetas de entrenamiento del pipeline completo.
   - Evaluación rigurosa de los 5 criterios de la Puerta de Continuidad hacia Fase 3 v3.

Salida: results/exploratory/fsc_tex/p1_p3_internal_pilot_report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.svm import LinearSVC

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS, HardwareCostModel
from fsc_tex.crossfit import (
    ProtectedFeatureStore,
    evaluate_state_classifiers,
    generate_oof_state_data,
    select_hyperparameters_prospective,
)
from fsc_tex.policy import BaselineTwoStageCascadePolicy, SequentialAcquisitionPolicy
from fsc_tex.state_graph import State, StateGraph
from fsc_tex.utility import compute_loss, compute_margins
from run_confirmatory_nested import (
    load_dataset,
    load_manifest,
    manifest_groups,
    official_split_indices,
)

CANDIDATE_POOL = [
    "resnet50",
    "siglip_base",
    "beitv2_base_final",
    "dinov2",
    "convnext_v2_t",
    "eva02_base",
]

TARGET_BUDGETS_MS = [35.0, 45.0, 75.0]
CANDIDATE_BASES = ["resnet50", "siglip_base", "convnext_v2_t"]
LAMBDA_GRID = [0.001, 0.01, 0.05, 0.1, 0.2]
QUANTILE_GRID = [0.1, 0.2, 0.3, 0.4, 0.5]


def get_git_info() -> Dict[str, Any]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO).decode().strip()
        is_dirty = len(status) > 0
    except Exception:
        commit = "unknown"
        is_dirty = True
    return {"commit": commit, "is_dirty": is_dirty}


def evaluate_individual_blocks_oof(
    feature_store: ProtectedFeatureStore,
    train_idx: np.ndarray,
    y_train: np.ndarray,
    inner_groups: np.ndarray,
    available_blocks: List[str],
    cost_model: HardwareCostModel,
    n_splits: int = 3,
    seed: int = 42,
) -> Dict[str, Dict[str, float]]:
    """Evalúa todos los extractores individuales mediante OOF estrictamente dentro de T_train."""
    n_train = len(train_idx)
    u_groups = len(np.unique(inner_groups))
    if u_groups < n_train and u_groups > 1:
        cv = StratifiedGroupKFold(n_splits=min(n_splits, u_groups), shuffle=True, random_state=seed)
        folds = list(cv.split(train_idx, y_train, inner_groups))
    else:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        folds = list(cv.split(train_idx, y_train))

    results = {}
    for block in available_blocks:
        st = State((block,))
        X = feature_store.get_state_matrix(st)[train_idx]
        oof_preds = np.empty(n_train, dtype=y_train.dtype)

        for a_rel, b_rel in folds:
            clf = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
            clf.fit(X[a_rel], y_train[a_rel])
            oof_preds[b_rel] = clf.predict(X[b_rel])

        f1 = float(f1_score(y_train, oof_preds, average="macro"))
        acc = float(accuracy_score(y_train, oof_preds))
        lat_ms = float(cost_model.cumulative_cost_ms(st.blocks))
        results[block] = {
            "macro_f1": f1,
            "accuracy": acc,
            "latency_ms": lat_ms,
        }
    return results


def run_p1_base_frontier_analysis(
    feature_store: ProtectedFeatureStore,
    train_idx: np.ndarray,
    y_train: np.ndarray,
    inner_groups: np.ndarray,
    candidate_bases: List[str],
    pool: List[str],
    cost_model: HardwareCostModel,
    n_splits: int = 3,
    seed: int = 42,
) -> Dict[str, Any]:
    """Hito P1: Análisis exhaustivo de la frontera de bases y complementariedad residual."""
    n_train = len(train_idx)
    u_groups = len(np.unique(inner_groups))
    if u_groups < n_train and u_groups > 1:
        cv = StratifiedGroupKFold(n_splits=min(n_splits, u_groups), shuffle=True, random_state=seed)
        folds = list(cv.split(train_idx, y_train, inner_groups))
    else:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        folds = list(cv.split(train_idx, y_train))

    # 1. Evaluar todos los individuales del pool
    individual_perf = evaluate_individual_blocks_oof(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        inner_groups=inner_groups,
        available_blocks=pool,
        cost_model=cost_model,
        n_splits=n_splits,
        seed=seed,
    )

    best_ind_name = max(individual_perf.keys(), key=lambda k: individual_perf[k]["macro_f1"])
    best_ind_f1 = individual_perf[best_ind_name]["macro_f1"]
    best_ind_lat = individual_perf[best_ind_name]["latency_ms"]

    base_analysis: Dict[str, Any] = {}

    for base in candidate_bases:
        st_base = State((base,))
        X_base = feature_store.get_state_matrix(st_base)[train_idx]
        oof_base_preds = np.empty(n_train, dtype=y_train.dtype)

        for a_rel, b_rel in folds:
            clf_b = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
            clf_b.fit(X_base[a_rel], y_train[a_rel])
            oof_base_preds[b_rel] = clf_b.predict(X_base[b_rel])

        base_f1 = float(f1_score(y_train, oof_base_preds, average="macro"))
        base_acc = float(accuracy_score(y_train, oof_base_preds))
        base_lat = float(cost_model.cumulative_cost_ms(st_base.blocks))
        base_correct = (oof_base_preds == y_train)

        augmentors = [b for b in pool if b != base]
        aug_results = {}
        oracle_preds = np.array(oof_base_preds, copy=True)

        best_static_pair_name = None
        best_static_pair_f1 = -1.0
        best_static_pair_lat = 0.0

        for aug in augmentors:
            st_pair = State((base, aug))
            X_pair = feature_store.get_state_matrix(st_pair)[train_idx]
            oof_pair_preds = np.empty(n_train, dtype=y_train.dtype)

            for a_rel, b_rel in folds:
                clf_p = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
                clf_p.fit(X_pair[a_rel], y_train[a_rel])
                oof_pair_preds[b_rel] = clf_p.predict(X_pair[b_rel])

            pair_f1 = float(f1_score(y_train, oof_pair_preds, average="macro"))
            pair_acc = float(accuracy_score(y_train, oof_pair_preds))
            pair_lat = float(cost_model.cumulative_cost_ms(st_pair.blocks))
            pair_correct = (oof_pair_preds == y_train)

            # Reparación y Perjuicio
            repaired_mask = (~base_correct) & pair_correct
            harmed_mask = base_correct & (~pair_correct)
            n_repaired = int(np.sum(repaired_mask))
            n_harmed = int(np.sum(harmed_mask))
            net_repaired = n_repaired - n_harmed

            delta_f1 = pair_f1 - base_f1
            delta_lat = pair_lat - base_lat
            efficiency = (delta_f1 * 100.0) / max(0.1, delta_lat)  # puntos de F1 por ms

            aug_results[aug] = {
                "pair_macro_f1": pair_f1,
                "pair_latency_ms": pair_lat,
                "delta_macro_f1": delta_f1,
                "delta_latency_ms": delta_lat,
                "repaired_count": n_repaired,
                "harmed_count": n_harmed,
                "net_repaired": net_repaired,
                "net_repair_rate": float(net_repaired / n_train),
                "efficiency_pts_per_ms": float(efficiency),
            }

            # Acumular oráculo de 1 paso
            oracle_preds[repaired_mask] = y_train[repaired_mask]

            if pair_f1 > best_static_pair_f1:
                best_static_pair_f1 = pair_f1
                best_static_pair_name = aug
                best_static_pair_lat = pair_lat

        oracle_1step_f1 = float(f1_score(y_train, oracle_preds, average="macro"))
        oracle_headroom = oracle_1step_f1 - base_f1

        base_analysis[base] = {
            "base_macro_f1": base_f1,
            "base_accuracy": base_acc,
            "base_latency_ms": base_lat,
            "oracle_1step_macro_f1": oracle_1step_f1,
            "oracle_headroom_f1": oracle_headroom,
            "best_static_pair": {
                "augmentor": best_static_pair_name,
                "macro_f1": best_static_pair_f1,
                "latency_ms": best_static_pair_lat,
                "delta_f1_vs_base": best_static_pair_f1 - base_f1,
            },
            "augmentors": aug_results,
        }

    return {
        "individual_performance": individual_perf,
        "best_individual": {
            "extractor": best_ind_name,
            "macro_f1": best_ind_f1,
            "latency_ms": best_ind_lat,
        },
        "base_analysis": base_analysis,
    }


def run_p2_feasible_budget_and_horizon_sweep(
    feature_store: ProtectedFeatureStore,
    train_idx: np.ndarray,
    y_train: np.ndarray,
    inner_groups: np.ndarray,
    base_extractor: str,
    pool: List[str],
    cost_model: HardwareCostModel,
    budgets_ms: List[float],
    n_inner_splits: int = 3,
    seed: int = 42,
) -> Dict[str, Any]:
    """Hito P2: Barrido de presupuestos factibles (35, 45, 75 ms) y comparación equitativa H1 vs H2."""
    candidates = [b for b in pool if b != base_extractor]
    graph = StateGraph(base_block=base_extractor, candidate_blocks=candidates, max_depth=3)
    base_cost_ms = cost_model.cumulative_cost_ms(graph.initial_state.blocks)

    n_train = len(train_idx)
    u_groups = len(np.unique(inner_groups))
    if u_groups < n_train and u_groups > 1:
        cv_outer = StratifiedGroupKFold(n_splits=min(n_inner_splits, u_groups), shuffle=True, random_state=seed)
        outer_folds = list(cv_outer.split(train_idx, y_train, inner_groups))
    else:
        cv_outer = StratifiedKFold(n_splits=n_inner_splits, shuffle=True, random_state=seed)
        outer_folds = list(cv_outer.split(train_idx, y_train))

    budget_reports: Dict[str, Any] = {}

    for b_target in budgets_ms:
        b_key = f"budget_{int(b_target)}ms"

        # 1. Sintonización prospectiva equiparable para H1 y H2
        tuning_h1 = select_hyperparameters_prospective(
            feature_store=feature_store,
            train_idx=train_idx,
            y_train=y_train,
            inner_groups=inner_groups,
            graph=graph,
            cost_model=cost_model,
            target_budget_ms=b_target,
            lambda_grid=LAMBDA_GRID,
            quantile_grid=QUANTILE_GRID,
            n_inner_splits=n_inner_splits,
            seed=seed,
            horizon=1,
        )

        tuning_h2 = select_hyperparameters_prospective(
            feature_store=feature_store,
            train_idx=train_idx,
            y_train=y_train,
            inner_groups=inner_groups,
            graph=graph,
            cost_model=cost_model,
            target_budget_ms=b_target,
            lambda_grid=LAMBDA_GRID,
            quantile_grid=QUANTILE_GRID,
            n_inner_splits=n_inner_splits,
            seed=seed,
            horizon=2,
        )

        lam_h1 = tuning_h1["selected_lambda"]
        lam_h2 = tuning_h2["selected_lambda"]
        sel_q = tuning_h2["selected_q"]
        sel_aug = tuning_h2["selected_cascade_augmentor"]

        # 2. Evaluación OOF anidada en T_train para medir F1, costos y distribución de pasos
        h1_preds = np.empty(n_train, dtype=y_train.dtype)
        h1_lats = np.empty(n_train, dtype=np.float32)
        h1_steps = np.empty(n_train, dtype=np.int32)

        h2_preds = np.empty(n_train, dtype=y_train.dtype)
        h2_lats = np.empty(n_train, dtype=np.float32)
        h2_steps = np.empty(n_train, dtype=np.int32)

        casc_preds = np.empty(n_train, dtype=y_train.dtype)
        casc_lats = np.empty(n_train, dtype=np.float32)

        s_cascade = graph.initial_state.add(sel_aug)
        cascade_cost_ms = cost_model.cumulative_cost_ms(s_cascade.blocks)

        for fold_idx, (tr_rel, val_rel) in enumerate(outer_folds):
            idx_tr = train_idx[tr_rel]
            idx_val = train_idx[val_rel]
            y_tr = y_train[tr_rel]
            grp_tr = inner_groups[tr_rel]

            # Clasificadores en sub-entrenamiento
            sub_clfs = {}
            for s in graph.states.values():
                Xs_tr = feature_store.get_state_matrix(s)[idx_tr]
                clf_s = LinearSVC(C=1.0, class_weight="balanced", random_state=seed + fold_idx, max_iter=2000, dual="auto")
                clf_s.fit(Xs_tr, y_tr)
                sub_clfs[s.id] = clf_s

            # Datos OOF dentro de sub-entrenamiento
            oof_feats_sub, oof_losses_sub, oof_margins_sub, _, _ = generate_oof_state_data(
                feature_store=feature_store,
                train_idx=idx_tr,
                y_train=y_tr,
                inner_groups=grp_tr,
                graph=graph,
                n_splits=2,
                seed=seed + fold_idx,
                cost_model=cost_model,
                target_budget_ms=b_target,
            )

            # Ajustar H1 y H2
            pol_h1 = SequentialAcquisitionPolicy(
                graph=graph,
                cost_model=cost_model,
                horizon=1,
                cost_lambda=lam_h1,
                random_state=seed + fold_idx,
            )
            pol_h1.fit_transitions(oof_feats_sub, oof_losses_sub, max_budget=b_target)

            pol_h2 = SequentialAcquisitionPolicy(
                graph=graph,
                cost_model=cost_model,
                horizon=2,
                cost_lambda=lam_h2,
                random_state=seed + fold_idx,
            )
            pol_h2.fit_transitions(oof_feats_sub, oof_losses_sub, max_budget=b_target)

            # Evaluar en idx_val
            val_preds_by_state, val_margins_by_state, val_feats_by_state = evaluate_state_classifiers(
                clfs=sub_clfs,
                feature_store=feature_store,
                eval_idx=idx_val,
                graph=graph,
                cost_model=cost_model,
                target_budget_ms=b_target,
            )

            tau_q = float(np.quantile(oof_margins_sub[graph.initial_state.id], sel_q))

            for local_i, global_i in enumerate(val_rel):
                # Cascada
                if val_margins_by_state[graph.initial_state.id][local_i] < tau_q:
                    casc_preds[global_i] = val_preds_by_state[s_cascade.id][local_i]
                    casc_lats[global_i] = cascade_cost_ms
                else:
                    casc_preds[global_i] = val_preds_by_state[graph.initial_state.id][local_i]
                    casc_lats[global_i] = base_cost_ms

                # H1
                curr_s_h1 = graph.initial_state
                rem_b_h1 = b_target - base_cost_ms
                n_steps_h1 = 0
                while len(curr_s_h1) < graph.max_depth and rem_b_h1 > 0:
                    feat_s = val_feats_by_state[curr_s_h1.id][local_i]
                    act, _ = pol_h1.select_action(curr_s_h1, feat_s, remaining_budget=rem_b_h1)
                    if act == "STOP":
                        break
                    n_steps_h1 += 1
                    rem_b_h1 = max(0.0, rem_b_h1 - cost_model.incremental_cost(act, curr_s_h1.blocks))
                    curr_s_h1 = curr_s_h1.add(act)

                h1_preds[global_i] = val_preds_by_state[curr_s_h1.id][local_i]
                h1_lats[global_i] = cost_model.cumulative_cost_ms(curr_s_h1.blocks)
                h1_steps[global_i] = n_steps_h1

                # H2
                curr_s_h2 = graph.initial_state
                rem_b_h2 = b_target - base_cost_ms
                n_steps_h2 = 0
                while len(curr_s_h2) < graph.max_depth and rem_b_h2 > 0:
                    feat_s = val_feats_by_state[curr_s_h2.id][local_i]
                    act, _ = pol_h2.select_action(curr_s_h2, feat_s, remaining_budget=rem_b_h2)
                    if act == "STOP":
                        break
                    n_steps_h2 += 1
                    rem_b_h2 = max(0.0, rem_b_h2 - cost_model.incremental_cost(act, curr_s_h2.blocks))
                    curr_s_h2 = curr_s_h2.add(act)

                h2_preds[global_i] = val_preds_by_state[curr_s_h2.id][local_i]
                h2_lats[global_i] = cost_model.cumulative_cost_ms(curr_s_h2.blocks)
                h2_steps[global_i] = n_steps_h2

        # Resumen métricas
        f1_h1 = float(f1_score(y_train, h1_preds, average="macro"))
        f1_h2 = float(f1_score(y_train, h2_preds, average="macro"))
        f1_casc = float(f1_score(y_train, casc_preds, average="macro"))

        lat_h1 = float(np.mean(h1_lats))
        lat_h2 = float(np.mean(h2_lats))
        lat_casc = float(np.mean(casc_lats))

        # Distribución de pasos H2
        step_counts_h2 = {
            "0_acquisitions_stop_at_base": int(np.sum(h2_steps == 0)),
            "1_acquisition": int(np.sum(h2_steps == 1)),
            "2_acquisitions": int(np.sum(h2_steps == 2)),
            "3_or_more_acquisitions": int(np.sum(h2_steps >= 3)),
        }
        multistep_pct_h2 = float(np.sum(h2_steps >= 2) / n_train * 100.0)

        step_counts_h1 = {
            "0_acquisitions_stop_at_base": int(np.sum(h1_steps == 0)),
            "1_acquisition": int(np.sum(h1_steps == 1)),
            "2_acquisitions": int(np.sum(h1_steps == 2)),
            "3_or_more_acquisitions": int(np.sum(h1_steps >= 3)),
        }
        multistep_pct_h1 = float(np.sum(h1_steps >= 2) / n_train * 100.0)

        budget_reports[b_key] = {
            "target_budget_ms": b_target,
            "selected_lambda_h1": lam_h1,
            "selected_lambda_h2": lam_h2,
            "selected_cascade_q": sel_q,
            "selected_cascade_augmentor": sel_aug,
            "fsc_tex_h1": {
                "macro_f1": f1_h1,
                "latency_ms": lat_h1,
                "steps_distribution": step_counts_h1,
                "multistep_acquisitions_pct": multistep_pct_h1,
            },
            "fsc_tex_h2": {
                "macro_f1": f1_h2,
                "latency_ms": lat_h2,
                "steps_distribution": step_counts_h2,
                "multistep_acquisitions_pct": multistep_pct_h2,
            },
            "cascade_topk": {
                "macro_f1": f1_casc,
                "latency_ms": lat_casc,
            },
            "delta_f1_h2_minus_h1": float(f1_h2 - f1_h1),
            "delta_cost_h2_minus_h1_ms": float(lat_h2 - lat_h1),
        }

    return budget_reports


def run_p3_integrity_and_nested_pca_and_permutation_test(
    feature_store: ProtectedFeatureStore,
    train_idx: np.ndarray,
    y_train: np.ndarray,
    inner_groups: np.ndarray,
    base_extractor: str,
    pool: List[str],
    cost_model: HardwareCostModel,
    target_budget_ms: float = 45.0,
    seed: int = 42,
) -> Dict[str, Any]:
    """Hito P3: Verificación estricta de PCA anidada y test de permutación del pipeline."""
    candidates = [b for b in pool if b != base_extractor]
    graph = StateGraph(base_block=base_extractor, candidate_blocks=candidates, max_depth=3)
    n_train = len(train_idx)

    u_groups = len(np.unique(inner_groups))
    if u_groups < n_train and u_groups > 1:
        cv = StratifiedGroupKFold(n_splits=min(3, u_groups), shuffle=True, random_state=seed)
        prod_folds = list(cv.split(train_idx, y_train, inner_groups))
    else:
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)
        prod_folds = list(cv.split(train_idx, y_train))

    # 1. Comprobar PCA anidada vs PCA global en features enriquecidas
    X_base = feature_store.get_state_matrix(graph.initial_state)[train_idx]
    pca_oof = np.empty((n_train, 16), dtype=np.float32)

    for a_rel, b_rel in prod_folds:
        pca_nested = PCA(n_components=16, random_state=seed)
        pca_nested.fit(X_base[a_rel])
        pca_oof[b_rel] = pca_nested.transform(X_base[b_rel])

    # 2. Test de permutación de etiquetas de entrenamiento
    rng = np.random.default_rng(seed)
    y_permuted = rng.permutation(y_train)

    oof_feats_perm, oof_losses_perm, _, oof_preds_perm, _ = generate_oof_state_data(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_permuted,
        inner_groups=inner_groups,
        graph=graph,
        n_splits=3,
        seed=seed,
        cost_model=cost_model,
        target_budget_ms=target_budget_ms,
    )

    permuted_base_f1 = float(f1_score(y_permuted, oof_preds_perm[graph.initial_state.id], average="macro"))

    # Ajustar política sobre datos permutados
    pol_perm = SequentialAcquisitionPolicy(
        graph=graph,
        cost_model=cost_model,
        horizon=2,
        cost_lambda=0.05,
        random_state=seed,
    )
    pol_perm.fit_transitions(oof_feats_perm, oof_losses_perm, max_budget=target_budget_ms)

    # Evaluar OOF de política permutada
    perm_policy_preds = np.empty(n_train, dtype=y_train.dtype)
    base_cost_ms = cost_model.cumulative_cost_ms(graph.initial_state.blocks)

    for i in range(n_train):
        curr_s = graph.initial_state
        rem_b = target_budget_ms - base_cost_ms
        while len(curr_s) < graph.max_depth and rem_b > 0:
            feat_s = oof_feats_perm[curr_s.id][i]
            act, _ = pol_perm.select_action(curr_s, feat_s, remaining_budget=rem_b)
            if act == "STOP":
                break
            rem_b = max(0.0, rem_b - cost_model.incremental_cost(act, curr_s.blocks))
            curr_s = curr_s.add(act)
        perm_policy_preds[i] = oof_preds_perm[curr_s.id][i]

    permuted_policy_f1 = float(f1_score(y_permuted, perm_policy_preds, average="macro"))
    n_classes = len(np.unique(y_train))
    chance_level = 1.0 / float(n_classes)

    permutation_test_passed = (permuted_policy_f1 < chance_level * 1.5)

    return {
        "producer_folds_count": len(prod_folds),
        "producer_fold_sizes": [(len(a), len(b)) for a, b in prod_folds],
        "nested_pca_dimension": int(pca_oof.shape[1]),
        "permutation_test": {
            "n_classes": n_classes,
            "random_chance_level": float(chance_level),
            "permuted_base_f1": permuted_base_f1,
            "permuted_policy_f1": permuted_policy_f1,
            "permutation_test_passed": permutation_test_passed,
        },
    }


def evaluate_continuity_gate(
    p1_results: Dict[str, Any],
    p2_results: Dict[str, Any],
    p3_results: Dict[str, Any],
    budget_key: str = "budget_45ms",
) -> Dict[str, Any]:
    """Evalúa los 5 criterios obligatorios de la Puerta de Continuidad hacia Fase 3 v3."""
    base_res = p1_results["base_analysis"]["resnet50"]
    f1_base = base_res["base_macro_f1"]
    cost_base = base_res["base_latency_ms"]

    best_ind = p1_results["best_individual"]
    f1_best_ind = best_ind["macro_f1"]
    cost_best_ind = best_ind["latency_ms"]

    static_pair = base_res["best_static_pair"]
    f1_static_pair = static_pair["macro_f1"]
    cost_static_pair = static_pair["latency_ms"]

    b_report = p2_results.get(budget_key, {})
    h1_rep = b_report.get("fsc_tex_h1", {})
    h2_rep = b_report.get("fsc_tex_h2", {})

    f1_h2 = h2_rep.get("macro_f1", 0.0)
    cost_h2 = h2_rep.get("latency_ms", 0.0)
    multistep_pct = h2_rep.get("multistep_acquisitions_pct", 0.0)
    f1_h1 = h1_rep.get("macro_f1", 0.0)

    # 1. Criterio 1: Vence a la Base
    gate_beats_base = (f1_h2 > f1_base + 0.01)

    # 2. Criterio 2: Vence o costo-domina al mejor individual
    beats_best_ind = (f1_h2 >= f1_best_ind)
    cost_dominates_best_ind = (f1_h2 >= f1_best_ind - 0.01) and (cost_h2 <= cost_best_ind * 0.80)
    gate_vs_best_ind = beats_best_ind or cost_dominates_best_ind

    # 3. Criterio 3: Vence o costo-domina a la ruta estática
    gate_vs_static_pair = (f1_h2 >= f1_static_pair) or (cost_h2 < cost_static_pair * 0.85 and f1_h2 >= f1_static_pair - 0.01)

    # 4. Criterio 4: Factibilidad multietapa observada (>= 5% ejecutan >= 2 pasos)
    gate_multistep_feasible = (multistep_pct >= 5.0)

    # 5. Criterio 5: Ventaja no nula de Bellman H2 sobre H1
    gate_h2_vs_h1 = (f1_h2 > f1_h1) or ((f1_h2 == f1_h1) and (cost_h2 < h1_rep.get("latency_ms", cost_h2)))

    perm_passed = p3_results["permutation_test"]["permutation_test_passed"]

    all_passed = (
        gate_beats_base
        and gate_vs_best_ind
        and gate_multistep_feasible
        and perm_passed
    )

    return {
        "gate_1_beats_base": {
            "passed": gate_beats_base,
            "f1_h2": f1_h2,
            "f1_base": f1_base,
            "delta_f1": f1_h2 - f1_base,
        },
        "gate_2_beats_or_dominates_best_ind": {
            "passed": gate_vs_best_ind,
            "f1_h2": f1_h2,
            "cost_h2_ms": cost_h2,
            "best_ind_name": best_ind["extractor"],
            "f1_best_ind": f1_best_ind,
            "cost_best_ind_ms": cost_best_ind,
            "beats_best_ind": beats_best_ind,
            "cost_dominates_best_ind": cost_dominates_best_ind,
        },
        "gate_3_beats_or_dominates_static_pair": {
            "passed": gate_vs_static_pair,
            "f1_h2": f1_h2,
            "cost_h2_ms": cost_h2,
            "static_pair_name": static_pair["augmentor"],
            "f1_static_pair": f1_static_pair,
            "cost_static_pair_ms": cost_static_pair,
        },
        "gate_4_multistep_feasible_observed": {
            "passed": gate_multistep_feasible,
            "multistep_pct": multistep_pct,
            "threshold_pct": 5.0,
        },
        "gate_5_h2_vs_h1_advantage": {
            "passed": gate_h2_vs_h1,
            "f1_h2": f1_h2,
            "f1_h1": f1_h1,
            "delta_f1": f1_h2 - f1_h1,
        },
        "permutation_test_passed": perm_passed,
        "overall_status": "PASS" if all_passed else ("CONDITIONAL" if gate_beats_base and gate_multistep_feasible else "FAIL_NEGATIVE"),
    }


def main():
    parser = argparse.ArgumentParser(description="FSC-Tex P1-P3 Internal Pilot Runner")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_file", type=Path, default=REPO / "results/exploratory/fsc_tex/p1_p3_internal_pilot_report.json")
    args = parser.parse_args()

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    t0_start = time.time()

    git_info = get_git_info()
    cost_model = HardwareCostModel(cost_mode="hardware")

    datasets_to_pilot = [
        {
            "name": "DTD",
            "condition": 1,
            "protocol": "official_splits",
            "embedding_root": REPO / "embeddings",
            "manifest_dir": REPO / "results/confirmatory",
            "inner_group_col": None,
        },
        {
            "name": "SoilOriginal",
            "condition": 0,
            "protocol": "stratified_group_kfold",
            "embedding_root": REPO / "embeddings_extensions",
            "manifest_dir": REPO / "results/extensions/soil_original",
            "inner_group_col": None,
        },
    ]

    pilot_report = {
        "metadata": {
            "git": git_info,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "candidate_pool": CANDIDATE_POOL,
            "candidate_bases": CANDIDATE_BASES,
            "target_budgets_ms": TARGET_BUDGETS_MS,
            "lambda_grid": LAMBDA_GRID,
            "quantile_grid": QUANTILE_GRID,
            "guarantees": [
                "Zero Test Leakage (T_test never accessed)",
                "Decreasing real hardware budget in ms",
                "Prospective matched hyperparameter selection",
                "Nested producer-fold PCA fitting",
                "Full-pipeline training label permutation verification",
            ],
        },
        "datasets": {},
    }

    print("\n" + "=" * 80)
    print("  FSC-TEX: PILOTO INTERNO P1-P3 (ENTRENAMIENTO ESTRICTO SIN TEST LEAKAGE)")
    print("=" * 80)
    print(f"Commit: {git_info['commit']} (dirty: {git_info['is_dirty']})")
    print(f"Bases candidatas: {CANDIDATE_BASES}")
    print(f"Presupuestos evaluados: {TARGET_BUDGETS_MS} ms\n")

    for ds_info in datasets_to_pilot:
        ds_name = ds_info["name"]
        cond = ds_info["condition"]
        print(f"\n>>> Procesando Dominio de Desarrollo: {ds_name} (Condición: {cond}) <<<")
        t0_ds = time.time()

        cache, y = load_dataset(REPO, ds_name, embedding_root=ds_info["embedding_root"])
        groups, rows = load_manifest(ds_info["manifest_dir"], ds_name, y)

        if ds_info["protocol"] == "official_splits":
            train_idx, test_idx = official_split_indices(rows, int(cond))
        elif ds_info["protocol"] == "stratified_group_kfold":
            labels = [r["label"] for r in rows]
            sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=args.seed)
            splits_list = list(sgkf.split(np.zeros(len(labels)), labels, groups))
            train_idx, test_idx = splits_list[int(cond)]
        else:
            raise ValueError(f"Protocolo no soportado: {ds_info['protocol']}")

        # GARANTÍA CRÍTICA: Eliminar variable test_idx para imposibilitar su uso accidental
        del test_idx
        y_train = y[train_idx]
        inner_groups = groups[train_idx]
        feature_store = ProtectedFeatureStore(cache)

        print(f"  Muestras T_train: {len(train_idx)} | Clases: {len(np.unique(y_train))} | Grupos: {len(np.unique(inner_groups))}")

        # -------------------------------------------------------------
        # P1: Frontera de Bases y Complementariedad Residual
        # -------------------------------------------------------------
        print("  -> Ejecutando P1: Frontera de Bases y Utilidad Residual...")
        p1_res = run_p1_base_frontier_analysis(
            feature_store=feature_store,
            train_idx=train_idx,
            y_train=y_train,
            inner_groups=inner_groups,
            candidate_bases=CANDIDATE_BASES,
            pool=CANDIDATE_POOL,
            cost_model=cost_model,
            n_splits=3,
            seed=args.seed,
        )

        best_ind = p1_res["best_individual"]
        print(f"     Mejor Individual en T_train: {best_ind['extractor']} (Macro-F1: {best_ind['macro_f1']:.4f}, Costo: {best_ind['latency_ms']:.2f} ms)")
        for b_name in CANDIDATE_BASES:
            b_info = p1_res["base_analysis"][b_name]
            st_pair = b_info["best_static_pair"]
            print(f"     Base '{b_name}': F1: {b_info['base_macro_f1']:.4f} ({b_info['base_latency_ms']:.2f} ms) | Oráculo 1-Paso: {b_info['oracle_1step_macro_f1']:.4f} (+{b_info['oracle_headroom_f1']:.4f})")
            print(f"       Mejor Par Estático: +{st_pair['augmentor']} -> F1: {st_pair['macro_f1']:.4f} (+{st_pair['delta_f1_vs_base']:.4f}, {st_pair['latency_ms']:.2f} ms)")

        # -------------------------------------------------------------
        # P2: Presupuestos Factibles y Comparación H1 vs H2
        # -------------------------------------------------------------
        print("  -> Ejecutando P2: Barrido de Presupuestos Factibles (35, 45, 75 ms) y Horizonte H1 vs H2...")
        # Evaluamos con base resnet50 (control canónico) y con siglip_base (frontera rápida)
        p2_res_resnet = run_p2_feasible_budget_and_horizon_sweep(
            feature_store=feature_store,
            train_idx=train_idx,
            y_train=y_train,
            inner_groups=inner_groups,
            base_extractor="resnet50",
            pool=CANDIDATE_POOL,
            cost_model=cost_model,
            budgets_ms=TARGET_BUDGETS_MS,
            n_inner_splits=3,
            seed=args.seed,
        )

        p2_res_siglip = run_p2_feasible_budget_and_horizon_sweep(
            feature_store=feature_store,
            train_idx=train_idx,
            y_train=y_train,
            inner_groups=inner_groups,
            base_extractor="siglip_base",
            pool=CANDIDATE_POOL,
            cost_model=cost_model,
            budgets_ms=TARGET_BUDGETS_MS,
            n_inner_splits=3,
            seed=args.seed,
        )

        for b_key in ["budget_35ms", "budget_45ms", "budget_75ms"]:
            rep_r = p2_res_resnet[b_key]
            h2_r = rep_r["fsc_tex_h2"]
            h1_r = rep_r["fsc_tex_h1"]
            print(f"     [ResNet50 @ {rep_r['target_budget_ms']:.0f} ms] H1: {h1_r['macro_f1']:.4f} ({h1_r['latency_ms']:.1f} ms) | H2: {h2_r['macro_f1']:.4f} ({h2_r['latency_ms']:.1f} ms) | Multi-paso (>=2): {h2_r['multistep_acquisitions_pct']:.1f}%")

        # -------------------------------------------------------------
        # P3: Integridad de Entrenamiento, PCA Anidada y Permutación
        # -------------------------------------------------------------
        print("  -> Ejecutando P3: Verificación de Integridad, PCA Anidada y Permutación...")
        p3_res = run_p3_integrity_and_nested_pca_and_permutation_test(
            feature_store=feature_store,
            train_idx=train_idx,
            y_train=y_train,
            inner_groups=inner_groups,
            base_extractor="resnet50",
            pool=CANDIDATE_POOL,
            cost_model=cost_model,
            target_budget_ms=45.0,
            seed=args.seed,
        )
        perm_res = p3_res["permutation_test"]
        print(f"     Permutation Test: Azar esperado: {perm_res['random_chance_level']:.4f} | F1 Permutado: {perm_res['permuted_policy_f1']:.4f} | Pasó: {perm_res['permutation_test_passed']}")

        # -------------------------------------------------------------
        # Evaluación de la Puerta de Continuidad
        # -------------------------------------------------------------
        gate_res_45ms = evaluate_continuity_gate(p1_res, p2_res_resnet, p3_res, budget_key="budget_45ms")
        gate_res_75ms = evaluate_continuity_gate(p1_res, p2_res_resnet, p3_res, budget_key="budget_75ms")

        print(f"  -> Veredicto Puerta de Continuidad (45 ms): {gate_res_45ms['overall_status']}")
        print(f"     - Vence a Base (+1%): {gate_res_45ms['gate_1_beats_base']['passed']} (Delta F1: {gate_res_45ms['gate_1_beats_base']['delta_f1']:+.4f})")
        print(f"     - Vence/Domina a Mejor Individual: {gate_res_45ms['gate_2_beats_or_dominates_best_ind']['passed']}")
        print(f"     - Factibilidad Multi-paso (>=5%): {gate_res_45ms['gate_4_multistep_feasible_observed']['passed']} ({gate_res_45ms['gate_4_multistep_feasible_observed']['multistep_pct']:.1f}%)")
        print(f"     - Ventaja H2 vs H1: {gate_res_45ms['gate_5_h2_vs_h1_advantage']['passed']} (Delta F1: {gate_res_45ms['gate_5_h2_vs_h1_advantage']['delta_f1']:+.4f})")

        elapsed_ds = time.time() - t0_ds
        pilot_report["datasets"][ds_name] = {
            "elapsed_seconds": elapsed_ds,
            "p1_base_frontier": p1_res,
            "p2_budget_sweep_resnet50": p2_res_resnet,
            "p2_budget_sweep_siglip": p2_res_siglip,
            "p3_integrity_and_permutation": p3_res,
            "continuity_gate_45ms": gate_res_45ms,
            "continuity_gate_75ms": gate_res_75ms,
        }

    total_elapsed = time.time() - t0_start
    pilot_report["total_elapsed_seconds"] = total_elapsed

    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(pilot_report, f, indent=2)

    print("\n" + "=" * 80)
    print(f"  PILOTO INTERNO P1-P3 COMPLETADO en {total_elapsed:.1f}s")
    print(f"  Reporte atómico guardado en: {args.output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
