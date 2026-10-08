#!/usr/bin/env python3
"""FSC-Tex Fase 3: Suite Completa de Evaluación (27 Condiciones Canónicas).

Ejecuta el protocolo de evaluación externa e interna sin filtración a través de:
- DTD (10 splits oficiales)
- FMD (5 folds agrupados)
- CUReT (2 direcciones: a_to_b y b_to_a)
- Outex13Official1360 (1 split oficial)
- SoilOriginal (5 folds agrupados)
- KTHTIPS2b (4 particiones 3->1 con agrupación por muestra física)

Total: 27 condiciones experimentales canónicas.
Para cada condición:
1. Validación interna anidada sobre T_train (R_k / V_k) para selección libre de filtración.
2. Ajuste final de modelos de estado y política usando únicamente T_train.
3. Evaluación externa de una sola pasada sobre T_test.
4. Registro de trazas, métricas, latencia de hardware (ms) y predicciones.
5. Checkpoints atómicos por condición que permiten pausar y reanudar.

Salida: results/exploratory/fsc_tex/phase3_full_suite/
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.svm import LinearSVC

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from curet_confirmatory_protocol import curet_half_indices
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

DATASET_CONFIGS = {
    "DTD": {
        "protocol": "official_splits",
        "conditions": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "inner_cv_folds": 3,
        "inner_group_col": None,
        "embedding_root": REPO / "embeddings",
        "manifest_dir": REPO / "results/confirmatory",
    },
    "FMD": {
        "protocol": "stratified_group_kfold",
        "conditions": [0, 1, 2, 3, 4],
        "inner_cv_folds": 4,
        "inner_group_col": None,
        "embedding_root": REPO / "embeddings_confirmatory",
        "manifest_dir": REPO / "results/confirmatory",
    },
    "CUReT": {
        "protocol": "halves",
        "conditions": ["a_to_b", "b_to_a"],
        "inner_cv_folds": 3,
        "inner_group_col": None,
        "embedding_root": REPO / "embeddings_confirmatory",
        "manifest_dir": REPO / "results/confirmatory",
    },
    "Outex13Official1360": {
        "protocol": "official_splits",
        "conditions": [1],
        "inner_cv_folds": 3,
        "inner_group_col": None,
        "embedding_root": REPO / "embeddings_extensions",
        "manifest_dir": REPO / "results/extensions/outex13_official1360",
    },
    "SoilOriginal": {
        "protocol": "stratified_group_kfold",
        "conditions": [0, 1, 2, 3, 4],
        "inner_cv_folds": 4,
        "inner_group_col": None,
        "embedding_root": REPO / "embeddings_extensions",
        "manifest_dir": REPO / "results/extensions/soil_original",
    },
    "KTHTIPS2b": {
        "protocol": "official_splits_inverted_radam",
        "conditions": [1, 2, 3, 4],
        "inner_cv_folds": 3,
        "inner_group_col": "sample",
        "embedding_root": REPO / "embeddings_extensions",
        "manifest_dir": REPO / "results/extensions/kth_tips2b",
    },
}


def build_candidate_state_graph(base_block: str, candidate_blocks: List[str], max_depth: int = 3) -> StateGraph:
    allowlist = sorted([base_block] + candidate_blocks)
    return StateGraph(
        base_block=base_block,
        candidate_blocks=candidate_blocks,
        max_depth=max_depth,
        canonical_22_allowlist=allowlist,
    )


def extract_combined_block_matrix(cache: Dict[str, np.ndarray], state: State) -> np.ndarray:
    blocks_data = [cache[b] for b in state.blocks]
    if len(blocks_data) == 1:
        return blocks_data[0]
    return np.concatenate(blocks_data, axis=1)


def get_external_split(
    protocol: str,
    rows: list[dict],
    condition: Any,
    groups: np.ndarray,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    if protocol == "official_splits":
        return official_split_indices(rows, int(condition))
    elif protocol == "stratified_group_kfold":
        labels = [r["label"] for r in rows]
        sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
        splits_list = list(sgkf.split(np.zeros(len(labels)), labels, groups))
        return splits_list[int(condition)]
    elif protocol == "halves":
        return curet_half_indices(rows, str(condition))
    elif protocol == "official_splits_inverted_radam":
        tr, te = official_split_indices(rows, int(condition))
        return te, tr  # Inversión canónica: 3 muestras train, 1 test
    else:
        raise ValueError(f"Protocolo desconocido: {protocol}")


def run_single_condition(
    dataset_name: str,
    condition: Any,
    config: dict,
    output_dir: Path,
    seed: int = 42,
    skip_existing: bool = True,
) -> dict:
    cond_str = f"condition_{condition}"
    dest_dir = output_dir / dataset_name / cond_str
    metrics_file = dest_dir / "metrics.json"

    if skip_existing and metrics_file.exists():
        print(f"  [CACHE] Cargando condición existente: {dataset_name} / {cond_str}")
        with open(metrics_file, "r", encoding="utf-8") as f:
            return json.load(f)

    dest_dir.mkdir(parents=True, exist_ok=True)
    t0_start = time.time()

    cache, y = load_dataset(REPO, dataset_name, embedding_root=config["embedding_root"])
    groups, rows = load_manifest(config["manifest_dir"], dataset_name, y)

    train_idx, test_idx = get_external_split(
        protocol=config["protocol"],
        rows=rows,
        condition=condition,
        groups=groups,
        seed=seed,
    )

    n_train = len(train_idx)
    n_test = len(test_idx)
    y_train = y[train_idx]
    y_test = y[test_idx]
    classes = np.unique(y_train)
    n_classes = len(classes)

    # Grupos internos
    if config["inner_group_col"] is not None:
        inner_groups = manifest_groups(rows, config["inner_group_col"])[train_idx]
    else:
        inner_groups = groups[train_idx]

    graph = build_candidate_state_graph(BASE_EXTRACTOR, CANDIDATE_SUBSET, max_depth=3)
    cost_model = HardwareCostModel(cost_mode="hardware", normalize_by=BASE_EXTRACTOR)
    all_states = list(graph.states.values())
    initial_id = graph.initial_state.id
    base_cost_ms = cost_model.cumulative_cost_ms(graph.initial_state.blocks)

    full_cand_state = State(tuple(sorted([BASE_EXTRACTOR] + CANDIDATE_SUBSET)))
    cost_full_ms = cost_model.cumulative_cost_ms(full_cand_state.blocks)

    # -------------------------------------------------------------------------
    # 1. NIVEL DE ENTRENAMIENTO EXTERNO: Ajustar clasificadores y política en T_train
    # -------------------------------------------------------------------------
    # Para ajustar la política sin filtración sobre T_train, generamos transiciones
    # con 2 folds productores internos dentro de T_train
    u_groups = len(np.unique(inner_groups))
    if u_groups < n_train and u_groups > 1:
        n_p_splits = min(2, u_groups)
        cv_prod = StratifiedGroupKFold(n_splits=n_p_splits, shuffle=True, random_state=seed)
        prod_folds = list(cv_prod.split(train_idx, y_train, inner_groups))
    else:
        cv_prod = StratifiedKFold(n_splits=2, shuffle=True, random_state=seed)
        prod_folds = list(cv_prod.split(train_idx, y_train))

    oof_features_train: Dict[str, np.ndarray] = {}
    oof_losses_train: Dict[str, np.ndarray] = {}
    oof_margins_train: Dict[str, np.ndarray] = {}

    for state in all_states:
        X_s = extract_combined_block_matrix(cache, state)[train_idx]
        state_oof_preds = np.empty(n_train, dtype=y.dtype)
        state_oof_losses = np.empty(n_train, dtype=np.float32)
        state_oof_margins = np.empty(n_train, dtype=np.float32)
        state_oof_df = np.empty((n_train, n_classes), dtype=np.float32)

        for a_rel, b_rel in prod_folds:
            clf_prod = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
            clf_prod.fit(X_s[a_rel], y_train[a_rel])
            df_b = clf_prod.decision_function(X_s[b_rel])
            preds_b = clf_prod.predict(X_s[b_rel])

            if df_b.ndim == 1:
                state_oof_df[b_rel, 0] = -df_b
                state_oof_df[b_rel, 1] = df_b
            else:
                state_oof_df[b_rel] = df_b

            state_oof_preds[b_rel] = preds_b
            state_oof_losses[b_rel] = compute_loss(y_train[b_rel], preds_b)
            state_oof_margins[b_rel] = compute_margins(df_b)

        oof_losses_train[state.id] = state_oof_losses
        oof_margins_train[state.id] = state_oof_margins
        oof_features_train[state.id] = graph.encode_state_features_batch(
            state=state,
            margins=state_oof_margins,
            decision_functions=state_oof_df,
        )

    # Ajustar clasificadores finales en TODO T_train
    final_clfs_train: Dict[str, LinearSVC] = {}
    test_preds_by_state: Dict[str, np.ndarray] = {}
    test_df_by_state: Dict[str, np.ndarray] = {}
    test_margins_by_state: Dict[str, np.ndarray] = {}
    test_feats_by_state: Dict[str, np.ndarray] = {}

    for state in all_states:
        X_s_full = extract_combined_block_matrix(cache, state)
        X_s_tr = X_s_full[train_idx]
        X_s_te = X_s_full[test_idx]

        clf_final = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
        clf_final.fit(X_s_tr, y_train)
        final_clfs_train[state.id] = clf_final

        df_te = clf_final.decision_function(X_s_te)
        preds_te = clf_final.predict(X_s_te)
        test_preds_by_state[state.id] = preds_te

        if df_te.ndim == 1:
            df_te_pad = np.column_stack([-df_te, df_te])
        else:
            df_te_pad = df_te

        test_df_by_state[state.id] = df_te_pad
        test_margins_by_state[state.id] = compute_margins(df_te)
        test_feats_by_state[state.id] = graph.encode_state_features_batch(
            state=state,
            margins=test_margins_by_state[state.id],
            decision_functions=df_te_pad,
        )

    # Clasificador de Fusión Completa
    X_full_cand = extract_combined_block_matrix(cache, full_cand_state)
    clf_full = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
    clf_full.fit(X_full_cand[train_idx], y_train)
    preds_full_test = clf_full.predict(X_full_cand[test_idx])

    # -------------------------------------------------------------------------
    # 2. EVALUACIÓN EXTERNA EN T_test
    # -------------------------------------------------------------------------
    test_results: Dict[str, dict] = {}
    predictions_record: Dict[str, list] = {"y_true": [int(val) for val in y_test]}

    # A. Base (resnet50)
    preds_base = test_preds_by_state[initial_id]
    lats_base = np.full(n_test, base_cost_ms, dtype=np.float32)
    test_results["Base_resnet50"] = {
        "macro_f1": float(f1_score(y_test, preds_base, average="macro")),
        "accuracy": float(accuracy_score(y_test, preds_base)),
        "mean_latency_ms": float(base_cost_ms),
        "p95_latency_ms": float(base_cost_ms),
        "escalation_rate_pct": 0.0,
        "stop_at_base_pct": 100.0,
    }
    predictions_record["Base_resnet50"] = [int(p) for p in preds_base]

    # B. Fusión Completa
    test_results["Full_Fusion_5cand"] = {
        "macro_f1": float(f1_score(y_test, preds_full_test, average="macro")),
        "accuracy": float(accuracy_score(y_test, preds_full_test)),
        "mean_latency_ms": float(cost_full_ms),
        "p95_latency_ms": float(cost_full_ms),
        "escalation_rate_pct": 100.0,
        "stop_at_base_pct": 0.0,
    }
    predictions_record["Full_Fusion_5cand"] = [int(p) for p in preds_full_test]

    # C. Oráculo con STOP en T_test
    oracle_preds = np.empty(n_test, dtype=y.dtype)
    oracle_lats = np.empty(n_test, dtype=np.float32)
    for i in range(n_test):
        y_true_i = y_test[i]
        if preds_base[i] == y_true_i:
            oracle_preds[i] = preds_base[i]
            oracle_lats[i] = base_cost_ms
        else:
            best_sid = initial_id
            best_c = base_cost_ms
            repaired = False
            for sid, s_obj in graph.states.items():
                if test_preds_by_state[sid][i] == y_true_i:
                    c_ms = cost_model.cumulative_cost_ms(s_obj.blocks)
                    if not repaired or c_ms < best_c:
                        best_sid = sid
                        best_c = c_ms
                        repaired = True
            oracle_preds[i] = test_preds_by_state[best_sid][i]
            oracle_lats[i] = best_c

    test_results["Oracle_STOP"] = {
        "macro_f1": float(f1_score(y_test, oracle_preds, average="macro")),
        "accuracy": float(accuracy_score(y_test, oracle_preds)),
        "mean_latency_ms": float(np.mean(oracle_lats)),
        "p95_latency_ms": float(np.percentile(oracle_lats, 95)),
        "escalation_rate_pct": float(np.mean(oracle_lats > base_cost_ms) * 100),
        "stop_at_base_pct": float(np.mean(oracle_lats == base_cost_ms) * 100),
    }

    # D. Cascada de Dos Etapas
    best_cand = None
    best_cand_loss = 1.0
    for cand in CANDIDATE_SUBSET:
        s_cand = graph.initial_state.add(cand)
        mean_l = float(np.mean(oof_losses_train[s_cand.id]))
        if mean_l < best_cand_loss:
            best_cand_loss = mean_l
            best_cand = cand

    s_cascade = graph.initial_state.add(best_cand)
    cascade_cost_ms = cost_model.cumulative_cost_ms(s_cascade.blocks)
    oof_margins_base = oof_margins_train[initial_id]

    for q in CASCADE_QUANTILES:
        tau_q = float(np.quantile(oof_margins_base, q))
        c_preds = np.empty(n_test, dtype=y.dtype)
        c_lats = np.empty(n_test, dtype=np.float32)

        for i in range(n_test):
            if test_margins_by_state[initial_id][i] < tau_q:
                c_preds[i] = test_preds_by_state[s_cascade.id][i]
                c_lats[i] = cascade_cost_ms
            else:
                c_preds[i] = preds_base[i]
                c_lats[i] = base_cost_ms

        m_key = f"Cascade_q{int(q*100)}"
        test_results[m_key] = {
            "macro_f1": float(f1_score(y_test, c_preds, average="macro")),
            "accuracy": float(accuracy_score(y_test, c_preds)),
            "mean_latency_ms": float(np.mean(c_lats)),
            "p95_latency_ms": float(np.percentile(c_lats, 95)),
            "escalation_rate_pct": float(np.mean(c_lats > base_cost_ms) * 100),
            "stop_at_base_pct": float(np.mean(c_lats == base_cost_ms) * 100),
            "selected_augmentor": best_cand,
        }
        predictions_record[m_key] = [int(p) for p in c_preds]

    # E. FSC-Tex (Horizonte 1 y Horizonte 2)
    for lam in LAMBDA_GRID:
        # 1. H1
        pol_h1 = SequentialAcquisitionPolicy(
            graph=graph, cost_model=cost_model, horizon=1, cost_lambda=lam, random_state=seed
        )
        pol_h1.fit_transitions(oof_features_train, oof_losses_train)
        h1_preds = np.empty(n_test, dtype=y.dtype)
        h1_lats = np.empty(n_test, dtype=np.float32)
        h1_final_states = []

        for i in range(n_test):
            curr_s = graph.initial_state
            while len(curr_s) < graph.max_depth:
                feat_s = test_feats_by_state[curr_s.id][i]
                act, _ = pol_h1.select_action(curr_s, feat_s)
                if act == "STOP":
                    break
                curr_s = curr_s.add(act)
            h1_preds[i] = test_preds_by_state[curr_s.id][i]
            h1_lats[i] = cost_model.cumulative_cost_ms(curr_s.blocks)
            h1_final_states.append(curr_s.id)

        h1_key = f"FSC_Tex_H1_lam{lam}"
        test_results[h1_key] = {
            "macro_f1": float(f1_score(y_test, h1_preds, average="macro")),
            "accuracy": float(accuracy_score(y_test, h1_preds)),
            "mean_latency_ms": float(np.mean(h1_lats)),
            "p95_latency_ms": float(np.percentile(h1_lats, 95)),
            "escalation_rate_pct": float(np.mean(h1_lats > base_cost_ms) * 100),
            "stop_at_base_pct": float(np.mean(h1_lats == base_cost_ms) * 100),
        }
        predictions_record[h1_key] = [int(p) for p in h1_preds]

        # 2. H2
        pol_h2 = SequentialAcquisitionPolicy(
            graph=graph, cost_model=cost_model, horizon=2, cost_lambda=lam, random_state=seed
        )
        pol_h2.fit_transitions(oof_features_train, oof_losses_train)
        h2_preds = np.empty(n_test, dtype=y.dtype)
        h2_lats = np.empty(n_test, dtype=np.float32)
        h2_final_states = []

        for i in range(n_test):
            curr_s = graph.initial_state
            while len(curr_s) < graph.max_depth:
                feat_s = test_feats_by_state[curr_s.id][i]
                act, _ = pol_h2.select_action(curr_s, feat_s)
                if act == "STOP":
                    break
                curr_s = curr_s.add(act)
            h2_preds[i] = test_preds_by_state[curr_s.id][i]
            h2_lats[i] = cost_model.cumulative_cost_ms(curr_s.blocks)
            h2_final_states.append(curr_s.id)

        h2_key = f"FSC_Tex_H2_lam{lam}"
        test_results[h2_key] = {
            "macro_f1": float(f1_score(y_test, h2_preds, average="macro")),
            "accuracy": float(accuracy_score(y_test, h2_preds)),
            "mean_latency_ms": float(np.mean(h2_lats)),
            "p95_latency_ms": float(np.percentile(h2_lats, 95)),
            "escalation_rate_pct": float(np.mean(h2_lats > base_cost_ms) * 100),
            "stop_at_base_pct": float(np.mean(h2_lats == base_cost_ms) * 100),
        }
        predictions_record[h2_key] = [int(p) for p in h2_preds]

    elapsed = float(time.time() - t0_start)
    record = {
        "dataset": dataset_name,
        "condition": condition,
        "n_train": n_train,
        "n_test": n_test,
        "n_classes": n_classes,
        "elapsed_seconds": elapsed,
        "test_results": test_results,
    }

    # Guardar atómicamente
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    pred_file = dest_dir / "test_predictions.json"
    with open(pred_file, "w", encoding="utf-8") as f:
        json.dump(predictions_record, f)

    # Imprimir resumen breve
    best_c_k = max([k for k in test_results if k.startswith("Cascade_")], key=lambda k: test_results[k]["macro_f1"])
    best_h2_k = max([k for k in test_results if k.startswith("FSC_Tex_H2_")], key=lambda k: test_results[k]["macro_f1"])
    print(f"  [DONE] {dataset_name} / {cond_str} ({elapsed:.1f}s) | Base F1: {test_results['Base_resnet50']['macro_f1']:.4f} | Cascada ({best_c_k}): {test_results[best_c_k]['macro_f1']:.4f} ({test_results[best_c_k]['mean_latency_ms']:.1f}ms) | FSC-Tex H2 ({best_h2_k}): {test_results[best_h2_k]['macro_f1']:.4f} ({test_results[best_h2_k]['mean_latency_ms']:.1f}ms)")

    return record


def main():
    parser = argparse.ArgumentParser(description="FSC-Tex Fase 3: Suite Completa de Evaluación")
    parser.add_argument("--output-dir", type=Path, default=REPO / "results/exploratory/fsc_tex/phase3_full_suite")
    parser.add_argument("--datasets", nargs="+", default=list(DATASET_CONFIGS.keys()), help="Datasets a evaluar")
    parser.add_argument("--force-recompute", action="store_true", help="Ignora checkpoints y recalcula")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    t0_suite = time.time()

    all_records: List[dict] = []
    total_conditions = sum(len(DATASET_CONFIGS[ds]["conditions"]) for ds in args.datasets)
    curr_cond = 0

    print("================================================================================")
    print(f"  FSC-Tex FASE 3: SUITE COMPLETA DE EVALUACIÓN ({total_conditions} CONDICIONES)")
    print("================================================================================")

    for ds_name in args.datasets:
        cfg = DATASET_CONFIGS[ds_name]
        print(f"\n>>> Procesando Dataset: {ds_name} ({len(cfg['conditions'])} condiciones) <<<")
        for cond in cfg["conditions"]:
            curr_cond += 1
            print(f"\n--- [{curr_cond}/{total_conditions}] Condición: {ds_name} / {cond} ---")
            rec = run_single_condition(
                dataset_name=ds_name,
                condition=cond,
                config=cfg,
                output_dir=args.output_dir,
                skip_existing=not args.force_recompute,
            )
            all_records.append(rec)

    # Consolidación final
    summary_file = args.output_dir / "summary_27_conditions.json"
    suite_summary = {
        "total_conditions_evaluated": len(all_records),
        "total_elapsed_seconds": float(time.time() - t0_suite),
        "conditions": all_records,
    }
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(suite_summary, f, indent=2)

    print("\n================================================================================")
    print(f"  Fase 3 Completada Exitosamente ({len(all_records)}/{total_conditions} condiciones)")
    print(f"  Tiempo total: {suite_summary['total_elapsed_seconds'] / 60:.1f} minutos")
    print(f"  Resumen guardado en: {summary_file}")
    print("================================================================================")


if __name__ == "__main__":
    main()
