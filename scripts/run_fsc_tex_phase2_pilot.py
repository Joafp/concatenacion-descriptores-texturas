#!/usr/bin/env python3
"""FSC-Tex Fase 2: Piloto del Mecanismo de Adquisición Secuencial.

Evalúa empíricamente sobre particiones internas de T_train para DTD y SoilOriginal:
1. Base individual fija: 'resnet50'
2. Cascada de dos etapas (Baseline Two-Stage Cascade): resnet50 -> Top-k según umbral de margen tau
3. FSC-Tex Horizonte 1 (Miope): balancea ganancia inmediata contra costo lambda * Delta t
4. FSC-Tex Horizonte 2 (Bellman no miope): inducción hacia atrás con parada explícita STOP
5. Oráculo de diagnóstico con STOP: cota superior de reparabilidad al mínimo costo
6. Fusión completa de candidatos: cota superior estática con costo completo

Salvaguarda estricta: NO se consulta el conjunto de prueba (T_test).
Todo el ajuste de políticas y selección de hiperparámetros se realiza estrictamente
sobre las particiones internas R_k de T_train y se valida en V_k.

Salida: results/exploratory/fsc_tex/phase2_pilot_report.json
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.svm import LinearSVC

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.policy import BaselineTwoStageCascadePolicy, SequentialAcquisitionPolicy
from fsc_tex.state_graph import State, StateGraph
from fsc_tex.utility import compute_loss, compute_margins
from run_confirmatory_nested import (
    load_dataset,
    load_manifest,
    manifest_groups,
    official_split_indices,
)

BASE_EXTRACTOR = "resnet50"
CANDIDATE_SUBSET = [
    "siglip_base",
    "beitv2_base_final",
    "dinov2",
    "convnext_v2_t",
    "eva02_base",
]

LAMBDA_GRID = [0.0, 0.01, 0.05, 0.1, 0.25]
CASCADE_QUANTILES = [0.1, 0.2, 0.3, 0.4, 0.5]


def build_candidate_state_graph(base_block: str, candidate_blocks: List[str], max_depth: int = 3) -> StateGraph:
    """Construye el StateGraph canónico de profundidad 3 para los candidatos."""
    allowlist = sorted([base_block] + candidate_blocks)
    return StateGraph(
        base_block=base_block,
        candidate_blocks=candidate_blocks,
        max_depth=max_depth,
        canonical_22_allowlist=allowlist,
    )


def extract_combined_block_matrix(cache: Dict[str, np.ndarray], state: State) -> np.ndarray:
    """Concatena horizontalmente las matrices de embeddings de los bloques de un estado."""
    blocks_data = [cache[b] for b in state.blocks]
    if len(blocks_data) == 1:
        return blocks_data[0]
    return np.concatenate(blocks_data, axis=1)


def evaluate_dataset_phase2(
    dataset_name: str,
    embedding_root: Path,
    manifest_dir: Path,
    split_id: int,
    protocol: str = "official_splits",
    inner_group_col: str | None = None,
    n_inner_splits: int = 3,
    n_producer_splits: int = 2,
    seed: int = 42,
) -> dict:
    print(f"\n================================================================================")
    print(f"  FSC-Tex FASE 2: Piloto del Mecanismo en {dataset_name} (split {split_id})")
    print(f"================================================================================")

    t0_dataset = time.time()
    cache, y = load_dataset(REPO, dataset_name, embedding_root=embedding_root)
    groups, rows = load_manifest(manifest_dir, dataset_name, y)

    # 1. Aislar estrictamente T_train desde los manifiestos auditados
    if protocol == "official_splits":
        train_idx, test_idx = official_split_indices(rows, split_id)
    elif protocol == "grouped_kfold":
        labels = [r["label"] for r in rows]
        sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
        splits_list = list(sgkf.split(np.zeros(len(labels)), labels, groups))
        train_idx, test_idx = splits_list[split_id]
    else:
        raise ValueError(f"Protocolo desconocido: {protocol}")

    n_train = len(train_idx)
    y_train = y[train_idx]
    classes = np.unique(y_train)
    n_classes = len(classes)

    print(f"  Muestras T_train: {n_train} | Clases: {n_classes} | Base: {BASE_EXTRACTOR}")
    print(f"  Candidatos evaluados: {CANDIDATE_SUBSET}")

    # Grupos internos para validación cruzada anidada
    if inner_group_col is not None:
        inner_groups = manifest_groups(rows, inner_group_col)[train_idx]
    else:
        inner_groups = groups[train_idx]

    unique_groups = len(np.unique(inner_groups))
    if unique_groups < n_train and unique_groups > 1:
        n_splits_actual = min(n_inner_splits, unique_groups)
        cv_outer = StratifiedGroupKFold(n_splits=n_splits_actual, shuffle=True, random_state=seed)
        outer_folds = list(cv_outer.split(train_idx, y_train, inner_groups))
    else:
        cv_outer = StratifiedKFold(n_splits=n_inner_splits, shuffle=True, random_state=seed)
        outer_folds = list(cv_outer.split(train_idx, y_train))

    print(f"  Folds internos de validación anidada (R_k / V_k): {len(outer_folds)}")

    # 2. Configurar Grafo de Estados y Modelo de Costo Normalizado
    graph = build_candidate_state_graph(BASE_EXTRACTOR, CANDIDATE_SUBSET, max_depth=3)
    cost_model = HardwareCostModel(cost_mode="hardware", normalize_by=BASE_EXTRACTOR)

    all_states = list(graph.states.values())
    print(f"  Grafo acotado: {len(all_states)} estados alcanzables (profundidad máx: {graph.max_depth})")

    # Estructuras para acumular predicciones OOF de validación sobre todo T_train
    # Para cada método y configuración, guardaremos (y_pred, cumulative_latency_ms, final_state_id)
    methods_predictions: Dict[str, np.ndarray] = {}
    methods_latencies: Dict[str, np.ndarray] = {}
    methods_final_states: Dict[str, List[str]] = {}

    method_keys = [
        "Base_resnet50",
        "Full_Fusion_5cand",
        "Oracle_STOP",
    ]
    for q in CASCADE_QUANTILES:
        method_keys.append(f"Cascade_q{int(q*100)}")
    for lam in LAMBDA_GRID:
        method_keys.append(f"FSC_Tex_H1_lam{lam}")
        method_keys.append(f"FSC_Tex_H2_lam{lam}")

    for k in method_keys:
        methods_predictions[k] = np.empty(n_train, dtype=y.dtype)
        methods_latencies[k] = np.empty(n_train, dtype=np.float32)
        methods_final_states[k] = ["" for _ in range(n_train)]

    # 3. Iteración de Folds de Validación Interna (R_k / V_k)
    for fold_idx, (r_idx_rel, v_idx_rel) in enumerate(outer_folds):
        print(f"\n  --- Ejecutando Fold Interno {fold_idx + 1}/{len(outer_folds)} (|R_k|={len(r_idx_rel)}, |V_k|={len(v_idx_rel)}) ---")
        
        y_R = y_train[r_idx_rel]
        y_V = y_train[v_idx_rel]
        groups_R = inner_groups[r_idx_rel]

        # Configurar folds productores (A / B) dentro de R_k para generar transiciones OOF sin filtración
        u_groups_R = len(np.unique(groups_R))
        if u_groups_R < len(r_idx_rel) and u_groups_R > 1:
            n_p_splits = min(n_producer_splits, u_groups_R)
            cv_prod = StratifiedGroupKFold(n_splits=n_p_splits, shuffle=True, random_state=seed + fold_idx)
            prod_folds = list(cv_prod.split(r_idx_rel, y_R, groups_R))
        else:
            cv_prod = StratifiedKFold(n_splits=n_producer_splits, shuffle=True, random_state=seed + fold_idx)
            prod_folds = list(cv_prod.split(r_idx_rel, y_R))

        # A. Predicciones cruzadas dentro de R_k para todos los estados
        oof_features_R: Dict[str, np.ndarray] = {}
        oof_losses_R: Dict[str, np.ndarray] = {}
        oof_margins_R: Dict[str, np.ndarray] = {}
        oof_preds_R: Dict[str, np.ndarray] = {}

        for state in all_states:
            X_s_full = extract_combined_block_matrix(cache, state)[train_idx]
            X_s_R = X_s_full[r_idx_rel]

            state_oof_preds = np.empty(len(r_idx_rel), dtype=y.dtype)
            state_oof_losses = np.empty(len(r_idx_rel), dtype=np.float32)
            state_oof_margins = np.empty(len(r_idx_rel), dtype=np.float32)
            state_oof_df = np.empty((len(r_idx_rel), n_classes), dtype=np.float32)

            for a_rel, b_rel in prod_folds:
                clf_prod = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
                clf_prod.fit(X_s_R[a_rel], y_R[a_rel])
                
                df_b = clf_prod.decision_function(X_s_R[b_rel])
                preds_b = clf_prod.predict(X_s_R[b_rel])
                
                if df_b.ndim == 1:
                    state_oof_df[b_rel, 0] = -df_b
                    state_oof_df[b_rel, 1] = df_b
                else:
                    state_oof_df[b_rel] = df_b
                
                state_oof_preds[b_rel] = preds_b
                state_oof_losses[b_rel] = compute_loss(y_R[b_rel], preds_b)
                state_oof_margins[b_rel] = compute_margins(df_b)

            oof_preds_R[state.id] = state_oof_preds
            oof_losses_R[state.id] = state_oof_losses
            oof_margins_R[state.id] = state_oof_margins
            oof_features_R[state.id] = graph.encode_state_features_batch(
                state=state,
                margins=state_oof_margins,
                decision_functions=state_oof_df,
            )

        # B. Ajustar clasificadores finales de cada estado usando todo R_k
        final_clfs: Dict[str, LinearSVC] = {}
        val_preds_V: Dict[str, np.ndarray] = {}
        val_df_V: Dict[str, np.ndarray] = {}
        val_margins_V: Dict[str, np.ndarray] = {}
        val_feats_V: Dict[str, np.ndarray] = {}

        for state in all_states:
            X_s_full = extract_combined_block_matrix(cache, state)[train_idx]
            clf_final = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
            clf_final.fit(X_s_full[r_idx_rel], y_R)
            final_clfs[state.id] = clf_final

            df_val = clf_final.decision_function(X_s_full[v_idx_rel])
            preds_val = clf_final.predict(X_s_full[v_idx_rel])
            val_preds_V[state.id] = preds_val

            if df_val.ndim == 1:
                df_pad = np.column_stack([-df_val, df_val])
            else:
                df_pad = df_val
            val_df_V[state.id] = df_pad
            val_margins_V[state.id] = compute_margins(df_val)
            val_feats_V[state.id] = graph.encode_state_features_batch(
                state=state,
                margins=val_margins_V[state.id],
                decision_functions=df_pad,
            )

        # Clasificador de Fusión Completa (todos los 5 candidatos + Base)
        full_cand_state = State(tuple(sorted([BASE_EXTRACTOR] + CANDIDATE_SUBSET)))
        X_full_matrix = extract_combined_block_matrix(cache, full_cand_state)[train_idx]
        clf_full = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
        clf_full.fit(X_full_matrix[r_idx_rel], y_R)
        preds_full_V = clf_full.predict(X_full_matrix[v_idx_rel])
        cost_full_ms = cost_model.cumulative_cost_ms(full_cand_state.blocks)

        # C. Evaluar Referencias: Base, Full Fusion y Oráculo
        initial_id = graph.initial_state.id
        base_cost_ms = cost_model.cumulative_cost_ms(graph.initial_state.blocks)

        methods_predictions["Base_resnet50"][v_idx_rel] = val_preds_V[initial_id]
        methods_latencies["Base_resnet50"][v_idx_rel] = base_cost_ms
        for i, vi in enumerate(v_idx_rel):
            methods_final_states["Base_resnet50"][vi] = initial_id

        methods_predictions["Full_Fusion_5cand"][v_idx_rel] = preds_full_V
        methods_latencies["Full_Fusion_5cand"][v_idx_rel] = cost_full_ms
        for i, vi in enumerate(v_idx_rel):
            methods_final_states["Full_Fusion_5cand"][vi] = full_cand_state.id

        # Oráculo con STOP en V_k
        for i, vi in enumerate(v_idx_rel):
            y_true_i = y_V[i]
            # Si la base acierta, STOP
            if val_preds_V[initial_id][i] == y_true_i:
                methods_predictions["Oracle_STOP"][vi] = val_preds_V[initial_id][i]
                methods_latencies["Oracle_STOP"][vi] = base_cost_ms
                methods_final_states["Oracle_STOP"][vi] = initial_id
            else:
                # Buscar el estado con menor costo que clasifique correctamente
                best_state_id = initial_id
                best_cost_ms = base_cost_ms
                repaired = False
                for sid, s_obj in graph.states.items():
                    if val_preds_V[sid][i] == y_true_i:
                        c_ms = cost_model.cumulative_cost_ms(s_obj.blocks)
                        if not repaired or c_ms < best_cost_ms:
                            best_state_id = sid
                            best_cost_ms = c_ms
                            repaired = True
                
                methods_predictions["Oracle_STOP"][vi] = val_preds_V[best_state_id][i]
                methods_latencies["Oracle_STOP"][vi] = best_cost_ms
                methods_final_states["Oracle_STOP"][vi] = best_state_id

        # D. Evaluar Cascada de Dos Etapas (Baseline Two-Stage Cascade)
        # Seleccionar mejor augmentor candidato en R_k usando la pérdida OOF
        best_cand = None
        best_cand_loss = 1.0
        for cand in CANDIDATE_SUBSET:
            s_cand = graph.initial_state.add(cand)
            mean_loss = float(np.mean(oof_losses_R[s_cand.id]))
            if mean_loss < best_cand_loss:
                best_cand_loss = mean_loss
                best_cand = cand

        s_cascade = graph.initial_state.add(best_cand)
        cascade_cost_ms = cost_model.cumulative_cost_ms(s_cascade.blocks)

        oof_base_margins_R = oof_margins_R[initial_id]
        for q in CASCADE_QUANTILES:
            tau_q = float(np.quantile(oof_base_margins_R, q))
            m_key = f"Cascade_q{int(q*100)}"
            for i, vi in enumerate(v_idx_rel):
                margin_i = val_margins_V[initial_id][i]
                if margin_i < tau_q:
                    # Escalar a la segunda etapa
                    methods_predictions[m_key][vi] = val_preds_V[s_cascade.id][i]
                    methods_latencies[m_key][vi] = cascade_cost_ms
                    methods_final_states[m_key][vi] = s_cascade.id
                else:
                    # Detenerse en la base
                    methods_predictions[m_key][vi] = val_preds_V[initial_id][i]
                    methods_latencies[m_key][vi] = base_cost_ms
                    methods_final_states[m_key][vi] = initial_id

        # E. Evaluar Políticas FSC-Tex (Horizonte 1 y Horizonte 2)
        for lam in LAMBDA_GRID:
            # 1. Horizonte 1 (Miope)
            pol_h1 = SequentialAcquisitionPolicy(
                graph=graph,
                cost_model=cost_model,
                horizon=1,
                cost_lambda=lam,
                random_state=seed,
            )
            pol_h1.fit_transitions(oof_features_R, oof_losses_R)

            h1_key = f"FSC_Tex_H1_lam{lam}"
            for i, vi in enumerate(v_idx_rel):
                curr_s = graph.initial_state
                while len(curr_s) < graph.max_depth:
                    feat_s = val_feats_V[curr_s.id][i]
                    action, _ = pol_h1.select_action(curr_s, feat_s)
                    if action == "STOP":
                        break
                    curr_s = curr_s.add(action)
                
                methods_predictions[h1_key][vi] = val_preds_V[curr_s.id][i]
                methods_latencies[h1_key][vi] = cost_model.cumulative_cost_ms(curr_s.blocks)
                methods_final_states[h1_key][vi] = curr_s.id

            # 2. Horizonte 2 (Bellman no miope)
            pol_h2 = SequentialAcquisitionPolicy(
                graph=graph,
                cost_model=cost_model,
                horizon=2,
                cost_lambda=lam,
                random_state=seed,
            )
            pol_h2.fit_transitions(oof_features_R, oof_losses_R)

            h2_key = f"FSC_Tex_H2_lam{lam}"
            for i, vi in enumerate(v_idx_rel):
                curr_s = graph.initial_state
                while len(curr_s) < graph.max_depth:
                    feat_s = val_feats_V[curr_s.id][i]
                    action, _ = pol_h2.select_action(curr_s, feat_s)
                    if action == "STOP":
                        break
                    curr_s = curr_s.add(action)
                
                methods_predictions[h2_key][vi] = val_preds_V[curr_s.id][i]
                methods_latencies[h2_key][vi] = cost_model.cumulative_cost_ms(curr_s.blocks)
                methods_final_states[h2_key][vi] = curr_s.id

    # 4. Resumen Estadístico y Métricas Consolidadas sobre T_train
    print(f"\n  --- Consolidando Métricas de Validación Interna ({dataset_name}) ---")
    dataset_summary = {
        "dataset": dataset_name,
        "split_id": split_id,
        "n_samples": n_train,
        "n_classes": n_classes,
        "methods": {},
    }

    base_f1 = float(f1_score(y_train, methods_predictions["Base_resnet50"], average="macro"))
    base_acc = float(accuracy_score(y_train, methods_predictions["Base_resnet50"]))
    base_latency = float(np.mean(methods_latencies["Base_resnet50"]))

    print(f"  {'Método':<24} | {'Macro-F1':<8} | {'Exactitud':<9} | {'Lat. Media':<10} | {'Lat. P95':<9} | {'Escalación %':<12}")
    print(f"  {'-'*24}-+-{'-'*8}-+-{'-'*9}-+-{'-'*10}-+-{'-'*9}-+-{'-'*12}")

    for k in method_keys:
        preds = methods_predictions[k]
        lats = methods_latencies[k]
        states_taken = methods_final_states[k]

        f1_m = float(f1_score(y_train, preds, average="macro"))
        acc_m = float(accuracy_score(y_train, preds))
        lat_mean = float(np.mean(lats))
        lat_p95 = float(np.percentile(lats, 95))
        escalation_pct = float(np.mean([s != BASE_EXTRACTOR for s in states_taken]) * 100)

        # Frecuencia de estados
        state_counts = {}
        for s in states_taken:
            state_counts[s] = state_counts.get(s, 0) + 1
        state_distribution = {s: count / n_train for s, count in state_counts.items()}

        dataset_summary["methods"][k] = {
            "macro_f1": f1_m,
            "accuracy": acc_m,
            "mean_latency_ms": lat_mean,
            "p95_latency_ms": lat_p95,
            "escalation_rate_pct": escalation_pct,
            "stop_at_base_pct": 100.0 - escalation_pct,
            "f1_gain_vs_base": f1_m - base_f1,
            "state_distribution": state_distribution,
        }

        print(f"  {k:<24} | {f1_m:<8.4f} | {acc_m:<9.4f} | {lat_mean:<10.2f} | {lat_p95:<9.2f} | {escalation_pct:<12.1f}%")

    dataset_summary["elapsed_seconds"] = float(time.time() - t0_dataset)
    return dataset_summary


def evaluate_phase2_continuation_gate(dtd_res: dict, soil_res: dict) -> dict:
    """Evalúa los criterios formales de la compuerta de continuidad para la Fase 3."""
    print(f"\n================================================================================")
    print(f"  EVALUACIÓN DE LA COMPUERTA DE CONTINUIDAD (GATE A FASE 3)")
    print(f"================================================================================")

    gate_findings = {}

    for d_name, d_res in [("DTD", dtd_res), ("SoilOriginal", soil_res)]:
        methods = d_res["methods"]
        
        # 1. Comparar Horizon 2 vs Horizon 1
        h2_wins_h1 = 0
        h2_comparisons = []
        for lam in LAMBDA_GRID:
            h1_m = methods[f"FSC_Tex_H1_lam{lam}"]
            h2_m = methods[f"FSC_Tex_H2_lam{lam}"]
            diff_f1 = h2_m["macro_f1"] - h1_m["macro_f1"]
            diff_lat = h2_m["mean_latency_ms"] - h1_m["mean_latency_ms"]
            h2_comparisons.append({
                "lambda": lam,
                "h2_f1": h2_m["macro_f1"],
                "h1_f1": h1_m["macro_f1"],
                "f1_diff": diff_f1,
                "h2_latency": h2_m["mean_latency_ms"],
                "h1_latency": h1_m["mean_latency_ms"],
            })
            if diff_f1 >= -0.002:  # No inferior
                h2_wins_h1 += 1

        # 2. Comparar FSC-Tex vs Cascada de dos etapas en la frontera de Pareto
        # Encontrar cascada con mayor F1
        best_cascade_key = max(
            [k for k in methods if k.startswith("Cascade_")],
            key=lambda k: methods[k]["macro_f1"],
        )
        best_cascade = methods[best_cascade_key]

        # Encontrar mejor punto operativo de FSC-Tex H2
        best_h2_key = max(
            [k for k in methods if k.startswith("FSC_Tex_H2_")],
            key=lambda k: methods[k]["macro_f1"],
        )
        best_h2 = methods[best_h2_key]

        # Buscar si FSC-Tex H2 reduce latencia frente a cascada equivalente
        # Filtro de continuidad: latencia reducida en >= 5% con F1 dentro de margen de 0.5 p.p.
        f1_margin = best_cascade["macro_f1"] - 0.005
        fsc_candidates_within_f1 = [
            (k, m) for k, m in methods.items()
            if (k.startswith("FSC_Tex_H2_") or k.startswith("FSC_Tex_H1_")) and m["macro_f1"] >= f1_margin
        ]

        latency_savings_pct = 0.0
        matching_fsc_key = None
        if fsc_candidates_within_f1:
            fastest_fsc = min(fsc_candidates_within_f1, key=lambda pair: pair[1]["mean_latency_ms"])
            matching_fsc_key = fastest_fsc[0]
            latency_savings_pct = float(
                (best_cascade["mean_latency_ms"] - fastest_fsc[1]["mean_latency_ms"]) / best_cascade["mean_latency_ms"] * 100
            )

        f1_gain_at_max = best_h2["macro_f1"] - best_cascade["macro_f1"]

        gate_findings[d_name] = {
            "best_cascade_key": best_cascade_key,
            "best_cascade_f1": best_cascade["macro_f1"],
            "best_cascade_latency_ms": best_cascade["mean_latency_ms"],
            "best_h2_key": best_h2_key,
            "best_h2_f1": best_h2["macro_f1"],
            "best_h2_latency_ms": best_h2["mean_latency_ms"],
            "f1_gain_vs_cascade": f1_gain_at_max,
            "matching_fsc_key": matching_fsc_key,
            "latency_savings_pct": latency_savings_pct,
            "h2_comparisons": h2_comparisons,
        }

        print(f"\n  Resultados de Compuerta para {d_name}:")
        print(f"    - Mejor Cascada ({best_cascade_key}): F1 = {best_cascade['macro_f1']:.4f} | Latencia = {best_cascade['mean_latency_ms']:.2f} ms")
        print(f"    - Mejor FSC-Tex H2 ({best_h2_key}): F1 = {best_h2['macro_f1']:.4f} | Latencia = {best_h2['mean_latency_ms']:.2f} ms")
        print(f"    - Diferencia de Macro-F1: {f1_gain_at_max * 100:+.2f} p.p.")
        if matching_fsc_key:
            print(f"    - Variante FSC equivalente ({matching_fsc_key}): Ahorro de latencia = {latency_savings_pct:.1f}%")

    # Decisión formal de compuerta
    gate_passed = all(
        (g["f1_gain_vs_cascade"] >= -0.005 and (g["latency_savings_pct"] >= 5.0 or g["f1_gain_vs_cascade"] >= 0.005))
        for g in gate_findings.values()
    )

    print(f"\n  ------------------------------------------------------------------------------")
    print(f"  Veredicto de Compuerta para Fase 3: {'APROBADO (PASS)' if gate_passed else 'CONDICIONAL / REVISIÓN'}")
    print(f"  ------------------------------------------------------------------------------")

    return {
        "gate_passed": gate_passed,
        "criteria": "Latencia reducida >= 5% a F1 equivalente (margen <= 0.5 p.p.) o mejora de F1 >= 0.5 p.p.",
        "findings": gate_findings,
    }


def main():
    parser = argparse.ArgumentParser(description="FSC-Tex Fase 2: Piloto del Mecanismo")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO / "results/exploratory/fsc_tex/phase2_pilot_report.json",
    )
    args = parser.parse_args()

    results = {
        "schema_version": "1.0",
        "phase": "phase_2_mechanism_pilot",
        "base_extractor": BASE_EXTRACTOR,
        "candidates": CANDIDATE_SUBSET,
        "datasets": {},
    }

    # 1. DTD (split 1 oficial)
    results["datasets"]["DTD"] = evaluate_dataset_phase2(
        dataset_name="DTD",
        embedding_root=REPO / "embeddings",
        manifest_dir=REPO / "results/confirmatory",
        split_id=1,
        protocol="official_splits",
        n_inner_splits=3,
        n_producer_splits=2,
    )

    # 2. SoilOriginal (fold 0, agrupado)
    results["datasets"]["SoilOriginal"] = evaluate_dataset_phase2(
        dataset_name="SoilOriginal",
        embedding_root=REPO / "embeddings_extensions",
        manifest_dir=REPO / "results/extensions/soil_original",
        split_id=0,
        protocol="grouped_kfold",
        n_inner_splits=4,
        n_producer_splits=2,
    )

    # Evaluación de compuerta de continuidad
    gate_eval = evaluate_phase2_continuation_gate(
        results["datasets"]["DTD"],
        results["datasets"]["SoilOriginal"],
    )
    results["continuation_gate"] = gate_eval

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nReporte de Fase 2 guardado en: {args.output}")
    print(f"Fase 2 completada exitosamente.")


if __name__ == "__main__":
    main()
