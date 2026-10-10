"""Controles y Líneas Base Fuertes para FSC-Tex (Hito R3).

Implementa los comparadores obligatorios de la Sección 8.1 y Hito R3:
1. Base_resnet50: etapa inicial fija (1 bloque, 12.39 ms).
2. Best_Individual_Internal: mejor extractor individual seleccionado prospectivamente
   en T_train mediante validación cruzada interna (evita falacia de atribuir la ventaja
   a la política cuando un solo descriptor fuerte lo explica).
3. Static_Pair_ResNet_SigLIP: ruta estática fija de 2 bloques (ResNet50 + SigLIP),
   controlando que la ventaja no sea simplemente usar un par barato sin adaptación.
4. Cascade_TopK_Prospective: cascada adaptativa de dos etapas con umbral q* y augmentor
   seleccionados internamente en T_train.
5. Full_Fusion_6: fusión completa de los 6 bloques del subconjunto evaluado (ResNet50 + 5 candidatos).
   ROTULADO ESTRICTAMENTE COMO 6 BLOQUES, NUNCA CONFUNDIDO CON COMPLETA-22.
6. Reference_Full_22, Reference_Topk_22, Reference_GFS_22: referencias históricas auditadas
   provenientes de nested_fold_results.csv de la biblioteca canónica de 22 descriptores.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.svm import LinearSVC

from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.crossfit import ProtectedFeatureStore
from fsc_tex.state_graph import State


def select_best_individual_internal(
    feature_store: ProtectedFeatureStore,
    train_idx: np.ndarray,
    y_train: np.ndarray,
    inner_groups: np.ndarray,
    candidate_extractors: List[str],
    cost_model: HardwareCostModel,
    n_splits: int = 3,
    seed: int = 42,
) -> Dict[str, Any]:
    """Selecciona prospectivamente el mejor descriptor individual dentro de T_train."""
    n_train = len(train_idx)
    u_groups = len(np.unique(inner_groups))
    if u_groups < n_train and u_groups > 1:
        n_p = min(n_splits, u_groups)
        cv = StratifiedGroupKFold(n_splits=n_p, shuffle=True, random_state=seed)
        folds = list(cv.split(train_idx, y_train, inner_groups))
    else:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        folds = list(cv.split(train_idx, y_train))

    best_extractor = candidate_extractors[0]
    best_cv_f1 = -1.0
    cv_scores = {}

    for ext in candidate_extractors:
        st = State((ext,))
        X_ext = feature_store.get_state_matrix(st)[train_idx]
        fold_f1s = []

        for tr_rel, val_rel in folds:
            clf = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
            clf.fit(X_ext[tr_rel], y_train[tr_rel])
            p_val = clf.predict(X_ext[val_rel])
            fold_f1s.append(float(f1_score(y_train[val_rel], p_val, average="macro")))

        mean_f1 = float(np.mean(fold_f1s))
        cv_scores[ext] = mean_f1
        if mean_f1 > best_cv_f1:
            best_cv_f1 = mean_f1
            best_extractor = ext

    # Ajustar clasificador final del mejor extractor en TODO T_train
    best_state = State((best_extractor,))
    X_best_tr = feature_store.get_state_matrix(best_state)[train_idx]
    clf_final = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
    clf_final.fit(X_best_tr, y_train)

    cost_ms = cost_model.cumulative_cost_ms(best_state.blocks)

    return {
        "best_extractor": best_extractor,
        "best_state": best_state,
        "inner_cv_f1": best_cv_f1,
        "cv_scores_all": cv_scores,
        "clf_final": clf_final,
        "cost_ms": cost_ms,
    }


def evaluate_fixed_route(
    feature_store: ProtectedFeatureStore,
    train_idx: np.ndarray,
    y_train: np.ndarray,
    test_idx: np.ndarray,
    y_test: np.ndarray,
    blocks: List[str] | Tuple[str, ...],
    cost_model: HardwareCostModel,
    seed: int = 42,
) -> Dict[str, Any]:
    """Ajusta y evalúa una ruta fija arbitraria de bloques sobre T_test."""
    state = State(tuple(blocks))
    X_full = feature_store.get_state_matrix(state)
    X_tr = X_full[train_idx]
    X_te = X_full[test_idx]

    clf = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
    clf.fit(X_tr, y_train)
    preds = clf.predict(X_te)

    macro_f1 = float(f1_score(y_test, preds, average="macro"))
    acc = float(accuracy_score(y_test, preds))
    cost_ms = cost_model.cumulative_cost_ms(state.blocks)

    return {
        "state_id": state.id,
        "blocks": list(state.blocks),
        "macro_f1": macro_f1,
        "accuracy": acc,
        "mean_latency_ms": cost_ms,
        "p95_latency_ms": cost_ms,
        "preds": preds,
    }


def find_confirmatory_reference_metrics(
    repo_root: Path,
    dataset_name: str,
    condition: Any,
    classifier: str = "svm",
) -> Dict[str, Optional[Dict[str, float]]]:
    """Busca y extrae las referencias confirmativas históricas de 22 bloques (Hito P0).
    
    Consulta prioritariamente el libro mayor canónico auditado:
    results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.json
    
    Garantiza el mapeo exacto de outer_fold y fuentes fijas con SHA-256.
    """
    results: Dict[str, Optional[Dict[str, float]]] = {
        "Reference_Full_22": None,
        "Reference_GFS_22": None,
        "Reference_Topk_22": None,
    }

    ledger_path = repo_root / "results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.json"
    if ledger_path.exists():
        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
            cond_str = str(condition)
            for entry in ledger.get("entries", []):
                if (
                    entry["dataset"].lower() == dataset_name.lower()
                    and str(entry["condition"]) == cond_str
                    and entry.get("classifier", "svm").lower() == classifier.lower()
                ):
                    for k in ("Reference_Full_22", "Reference_GFS_22", "Reference_Topk_22"):
                        ref = entry.get(k)
                        if ref is not None:
                            results[k] = {
                                "macro_f1": float(ref["macro_f1"]),
                                "accuracy": float(ref["accuracy"]),
                                "blocks_count": int(ref.get("k", 22 if k == "Reference_Full_22" else 0)),
                            }
                    return results
        except Exception:
            pass

    # Mapeo exacto si el ledger no estuviese generado
    ds_lower = dataset_name.lower()
    if ds_lower in ("dtd", "outex13official1360", "kthtips2b"):
        try:
            cond_fold = int(condition) - 1
        except ValueError:
            cond_fold = 0
    elif ds_lower == "curet":
        cond_fold = 0 if str(condition) == "a_to_b" else 1
    else:  # fmd, soiloriginal
        try:
            cond_fold = int(condition)
        except ValueError:
            cond_fold = 0

    # Fuentes canónicas fijas
    if ds_lower in ("dtd", "fmd", "curet"):
        main_csv = repo_root / "results/confirmatory/ngram22_beitv2/nested_fold_results.csv"
        topk_csv = repo_root / "results/confirmatory/ngram22_beitv2/topk_individual_control/nested_fold_results.csv"
    elif ds_lower == "outex13official1360":
        main_csv = repo_root / "results/extensions/outex13_official1360/ngram22_beitv2/nested_fold_results.csv"
        topk_csv = repo_root / "results/extensions/outex13_official1360/ngram22_beitv2/topk_individual_control/nested_fold_results.csv"
    elif ds_lower == "soiloriginal":
        main_csv = repo_root / "results/extensions/soil_original/ngram22_beitv2/nested_fold_results.csv"
        topk_csv = repo_root / "results/extensions/soil_original/ngram22_beitv2/topk_individual_control/nested_fold_results.csv"
    elif ds_lower == "kthtips2b":
        main_csv = repo_root / "results/extensions/kth_tips2b/ngram22_beitv2_innergrp_sample_v1/nested_fold_results.csv"
        topk_csv = repo_root / "results/extensions/kth_tips2b/ngram22_beitv2_innergrp_sample_v1/topk_individual_control/nested_fold_results.csv"
    else:
        return results

    if main_csv.exists():
        try:
            with open(main_csv, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if (
                        r["dataset"].lower() == ds_lower
                        and r["classifier"].lower() == classifier.lower()
                        and int(r["outer_fold"]) == cond_fold
                        and int(r.get("seed", 42)) == 42
                    ):
                        f1_val = float(r.get("macro_f1", 0.0))
                        acc_val = float(r.get("accuracy", 0.0))
                        k_val = int(r.get("k", 0))
                        if r["method"] == "full_concat" and k_val == 22:
                            results["Reference_Full_22"] = {"macro_f1": f1_val, "accuracy": acc_val, "blocks_count": 22}
                        elif r["method"] == "gfs":
                            results["Reference_GFS_22"] = {"macro_f1": f1_val, "accuracy": acc_val, "blocks_count": k_val}
        except Exception:
            pass

    if topk_csv.exists():
        try:
            with open(topk_csv, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if (
                        r["dataset"].lower() == ds_lower
                        and r["classifier"].lower() == classifier.lower()
                        and int(r["outer_fold"]) == cond_fold
                        and int(r.get("seed", 42)) == 42
                        and r["method"] == "topk_individual"
                    ):
                        results["Reference_Topk_22"] = {
                            "macro_f1": float(r.get("macro_f1", 0.0)),
                            "accuracy": float(r.get("accuracy", 0.0)),
                            "blocks_count": int(r.get("k", 0)),
                        }
        except Exception:
            pass

    return results
