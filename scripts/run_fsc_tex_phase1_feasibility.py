#!/usr/bin/env python3
"""FSC-Tex Fase 1: Evaluación de Factibilidad Dentro del Entrenamiento.

Evalúa empíricamente sobre las particiones de entrenamiento de DTD, Soil y KTH:
1. Margen del Oráculo: techo diagnóstico de mejora con parada (max_a g_a > 0 vs STOP).
2. Tasa de Daño/Perjuicio: frecuencia en que un bloque adicional corrompe predicciones correctas.
3. Capacidad Predictiva: si un selector simple (Ridge / Logistic) puede anticipar
   utilidad positiva usando solo el estado observable de la base (márgenes + scores).

Salvaguarda estricta: NO se consulta el conjunto de prueba (T_test).
Todo el análisis se realiza Out-of-Fold (OOF) dentro de T_train.

Salida: results/exploratory/fsc_tex/phase1_feasibility_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fsc_tex.utility import compute_gain, compute_loss, compute_margins, summarize_oracle_and_harm
from run_confirmatory_nested import (
    load_dataset,
    load_manifest,
    manifest_groups,
    official_split_indices,
)

CANDIDATE_AUGMENTATIONS = [
    # Clásicos
    "hog", "lbp", "gabor",
    # CNNs
    "convnext_v2_t", "efficientnet_b0", "vgg16",
    # Transformers
    "vit_b16", "eva02_base", "beitv2_base_final",
    # Autosupervisados
    "dinov2", "siglip_base",
]

BASE_EXTRACTOR = "resnet50"


def evaluate_dataset_phase1(
    dataset_name: str,
    embedding_root: Path,
    manifest_dir: Path,
    split_id: int,
    protocol: str = "official_splits",
    inner_group_col: str | None = None,
    invert_split: bool = False,
    n_inner_splits: int = 3,
    seed: int = 42,
) -> dict:
    print(f"\n================================================================================")
    print(f"  FSC-Tex FASE 1: Factibilidad OOF en {dataset_name} (split {split_id})")
    print(f"================================================================================")

    cache, y = load_dataset(REPO, dataset_name, embedding_root=embedding_root)
    groups, rows = load_manifest(manifest_dir, dataset_name, y)

    # 1. Obtener partición externa oficial y aislar T_train
    if protocol == "halves":
        from run_confirmatory_nested import curet_half_indices
        train_idx, test_idx = curet_half_indices(rows, "a_to_b")
    elif protocol == "grouped_kfold":
        labels = [r["label"] for r in rows]
        sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
        splits_list = list(sgkf.split(np.zeros(len(labels)), labels, groups))
        train_idx, test_idx = splits_list[split_id]
    elif protocol == "official_splits":
        train_idx, test_idx = official_split_indices(rows, split_id)
        if invert_split:
            train_idx, test_idx = test_idx, train_idx
    else:
        raise ValueError(f"Protocolo desconocido: {protocol}")

    n_train = len(train_idx)
    y_train = y[train_idx]
    classes = np.unique(y_train)
    n_classes = len(classes)
    
    print(f"  Muestras T_train: {n_train} | Clases: {n_classes} | Base: {BASE_EXTRACTOR}")
    print(f"  Candidatos evaluados: {len(CANDIDATE_AUGMENTATIONS)}")

    # Grupos internos
    if inner_group_col is not None:
        inner_groups = manifest_groups(rows, inner_group_col)[train_idx]
        print(f"  Grupos internos ({inner_group_col}): {len(np.unique(inner_groups))} grupos físicos")
    else:
        inner_groups = groups[train_idx]

    # 2. Configurar validación cruzada interna (OOF) sobre T_train
    unique_inner_groups = len(np.unique(inner_groups))
    if unique_inner_groups < n_train and unique_inner_groups > 1:
        n_splits_actual = min(n_inner_splits, unique_inner_groups)
        cv = StratifiedGroupKFold(n_splits=n_splits_actual, shuffle=True, random_state=seed)
        split_gen = list(cv.split(train_idx, y_train, inner_groups))
    else:
        cv = StratifiedKFold(n_splits=n_inner_splits, shuffle=True, random_state=seed)
        split_gen = list(cv.split(train_idx, y_train))

    print(f"  Folds internos de validación OOF: {len(split_gen)}")

    # 3. Predicciones OOF de la Base
    X_base = cache[BASE_EXTRACTOR][train_idx]
    oof_base_preds = np.empty(n_train, dtype=y.dtype)
    oof_base_margins = np.empty(n_train, dtype=np.float32)
    oof_base_decision = np.empty((n_train, n_classes), dtype=np.float32)

    for in_tr, in_val in split_gen:
        clf_base = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
        clf_base.fit(X_base[in_tr], y_train[in_tr])
        df = clf_base.decision_function(X_base[in_val])
        if df.ndim == 1:
            # Caso binario
            oof_base_decision[in_val, 0] = -df
            oof_base_decision[in_val, 1] = df
        else:
            oof_base_decision[in_val] = df
        oof_base_preds[in_val] = clf_base.predict(X_base[in_val])
        oof_base_margins[in_val] = compute_margins(df)

    base_loss = compute_loss(y_train, oof_base_preds)
    base_acc = float(accuracy_score(y_train, oof_base_preds))
    base_f1 = float(f1_score(y_train, oof_base_preds, average="macro"))

    print(f"  --> Base ({BASE_EXTRACTOR}) OOF: Acc = {base_acc:.4f} | Macro-F1 = {base_f1:.4f}")

    # 4. Predicciones OOF para cada candidato incremental
    gains_by_action = {}
    aug_f1s = {}
    aug_accs = {}

    for cand in CANDIDATE_AUGMENTATIONS:
        X_cand = cache[cand][train_idx]
        X_combined = np.concatenate([X_base, X_cand], axis=1)

        oof_cand_preds = np.empty(n_train, dtype=y.dtype)
        for in_tr, in_val in split_gen:
            clf_aug = LinearSVC(C=1.0, class_weight="balanced", random_state=seed, max_iter=2000, dual="auto")
            clf_aug.fit(X_combined[in_tr], y_train[in_tr])
            oof_cand_preds[in_val] = clf_aug.predict(X_combined[in_val])

        cand_loss = compute_loss(y_train, oof_cand_preds)
        gain = compute_gain(base_loss, cand_loss)
        gains_by_action[cand] = gain
        aug_accs[cand] = float(accuracy_score(y_train, oof_cand_preds))
        aug_f1s[cand] = float(f1_score(y_train, oof_cand_preds, average="macro"))

    # 5. Resumen del Oráculo y Análisis de Perjuicio
    oracle_summary = summarize_oracle_and_harm(base_loss, gains_by_action)

    print(f"\n  --- Diagnóstico de Techo y Daño ---")
    print(f"  Oráculo con STOP OOF Acc: {oracle_summary['oracle_with_stop_accuracy']:.4f} (Margen de mejora: +{oracle_summary['oracle_headroom']*100:.2f}%)")
    print(f"  Fracción de errores corregibles por algún bloque: {oracle_summary['repairable_fraction_of_errors']*100:.1f}%")
    print(f"  Fracción de muestras donde al menos un bloque daña: {oracle_summary['any_candidate_harms_fraction']*100:.1f}%")

    # 6. Evaluación de la Capacidad Predictiva de un Selector Simple
    # ¿Puede un modelo predecir si invocar el mejor bloque incremental vale la pena?
    # Objetivo binario: y_need_help = 1 si la base erró y el oráculo puede corregirla
    y_can_repair = ((base_loss > 0) & (np.max(np.column_stack(list(gains_by_action.values())), axis=1) > 0)).astype(int)

    # Estado observable: margen base + top-k scores de la base
    # Cuanto menor es el margen de la base, más probable es que necesite ayuda
    selector_features = np.column_stack([
        oof_base_margins,
        np.sort(oof_base_decision, axis=1)[:, ::-1][:, :min(5, n_classes)]  # top-5 scores ordenados
    ])

    selector_cv_aucs = []
    for in_tr, in_val in split_gen:
        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(selector_features[in_tr])
        X_val_s = scaler.transform(selector_features[in_val])

        # Predecir necesidad de adquisición usando el margen
        # Si no hay positivos en val, omitir AUC
        if len(np.unique(y_can_repair[in_val])) > 1:
            # Regresión logística para estimar P(necesita_bloque | estado_base)
            meta_clf = LogisticRegression(class_weight="balanced", random_state=seed)
            meta_clf.fit(X_tr_s, y_can_repair[in_tr])
            probs = meta_clf.predict_proba(X_val_s)[:, 1]
            selector_cv_aucs.append(float(roc_auc_score(y_can_repair[in_val], probs)))

    mean_selector_auc = float(np.mean(selector_cv_aucs)) if selector_cv_aucs else 0.5
    print(f"  AUROC del selector simple (predecir necesidad de bloque desde estado base): {mean_selector_auc:.4f}")

    return {
        "dataset": dataset_name,
        "split_id": split_id,
        "n_train_samples": n_train,
        "n_classes": n_classes,
        "base_extractor": BASE_EXTRACTOR,
        "base_oof_accuracy": base_acc,
        "base_oof_macro_f1": base_f1,
        "oracle_summary": oracle_summary,
        "candidate_performances": {
            c: {"accuracy": aug_accs[c], "macro_f1": aug_f1s[c]} for c in CANDIDATE_AUGMENTATIONS
        },
        "selector_predictive_auc": mean_selector_auc,
    }


def main():
    parser = argparse.ArgumentParser(description="FSC-Tex Fase 1: Factibilidad OOF")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO / "results/exploratory/fsc_tex/phase1_feasibility_report.json",
    )
    args = parser.parse_args()

    results = {
        "schema_version": "1.0",
        "phase": "phase_1_inner_feasibility",
        "base_extractor": BASE_EXTRACTOR,
        "datasets": {},
    }

    # 1. DTD (split oficial 1)
    results["datasets"]["DTD"] = evaluate_dataset_phase1(
        dataset_name="DTD",
        embedding_root=REPO / "embeddings",
        manifest_dir=REPO / "results/confirmatory",
        split_id=1,
        n_inner_splits=3,
    )

    # 2. SoilOriginal (fold 0, agrupado)
    results["datasets"]["SoilOriginal"] = evaluate_dataset_phase1(
        dataset_name="SoilOriginal",
        embedding_root=REPO / "embeddings_extensions",
        manifest_dir=REPO / "results/extensions/soil_original",
        split_id=0,
        protocol="grouped_kfold",
        n_inner_splits=4,
    )

    # 3. KTH-TIPS2-b (split 1 invertido, agrupamiento por muestra física)
    results["datasets"]["KTHTIPS2b"] = evaluate_dataset_phase1(
        dataset_name="KTHTIPS2b",
        embedding_root=REPO / "embeddings_extensions",
        manifest_dir=REPO / "results/extensions/kth_tips2b",
        split_id=1,
        inner_group_col="sample",
        invert_split=True,
        n_inner_splits=3,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n================================================================================")
    print(f"Reporte de Factibilidad guardado en: {args.output}")
    print(f"Fase 1 completada exitosamente.")


if __name__ == "__main__":
    main()
