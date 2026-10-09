#!/usr/bin/env python3
"""FSC-Tex Fase 3 v2: Suite Canónica Congelada de Evaluación (Hito R6).

Ejecuta el protocolo riguroso sin filtración externa y con presupuesto físico decreciente a través de:
- DTD (10 splits oficiales)
- FMD (5 folds agrupados)
- CUReT (2 direcciones: a_to_b y b_to_a)
- Outex13Official1360 (1 split oficial)
- SoilOriginal (5 folds agrupados)
- KTHTIPS2b (4 particiones 3->1 agrupadas por muestra física)

Total: 27 condiciones experimentales canónicas.
Garantías metodológicas estrictas:
1. Zero Test Leakage: hiperparámetros (lambda*, q*, aumentador de cascada) seleccionados prospectivamente en T_train.
2. Presupuesto físico decreciente en milisegundos reales: Delta t_ms descontado en cada decisión.
3. Bellman no miope desplegable: sin optimismo oracular en los valores de continuación.
4. Controles fuertes: Base (ResNet-50), Mejor Individual Interno, Par Estático (ResNet+SigLIP), Cascada Top-K Prospectiva, Fusión Completa-6, y Referencias Auditadas de 22 Bloques.
5. Persistencia atómica de 7 artefactos auditables por condición.

Salida: results/exploratory/fsc_tex/phase3_v2_suite/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from curet_confirmatory_protocol import curet_half_indices
from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS
from fsc_tex.crossfit import save_condition_artifacts
from fsc_tex.pilot import run_residual_acquisition_pilot
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

CANONICAL_22_ALLOWLIST = sorted(DEFAULT_HARDWARE_LATENCY_MS.keys())

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

MANDATORY_ARTIFACTS = [
    "run_manifest.json",
    "splits.json",
    "state_graph.json",
    "traces.jsonl",
    "predictions.json",
    "metrics.json",
    "audit.json",
]


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


def is_condition_complete(dest_dir: Path) -> bool:
    """Verifica si los 7 contratos de artefactos existen y no están vacíos."""
    for art in MANDATORY_ARTIFACTS:
        f = dest_dir / art
        if not f.exists() or f.stat().st_size == 0:
            return False
    return True


def run_condition_v2(
    dataset_name: str,
    condition: Any,
    config: dict,
    output_dir: Path,
    target_budget_ms: float = 35.0,
    seed: int = 42,
    force: bool = False,
) -> dict:
    cond_str = f"condition_{condition}"
    dest_dir = output_dir / dataset_name / cond_str

    if not force and is_condition_complete(dest_dir):
        print(f"  [CACHE HIT] {dataset_name} / {cond_str} completada con los 7 artefactos válidos.")
        with open(dest_dir / "metrics.json", "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"  [EJECUTANDO] {dataset_name} / {cond_str} (Presupuesto objetivo: {target_budget_ms:.1f} ms)...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    cache, y = load_dataset(REPO, dataset_name, embedding_root=config["embedding_root"])
    groups, rows = load_manifest(config["manifest_dir"], dataset_name, y)

    train_idx, test_idx = get_external_split(
        protocol=config["protocol"],
        rows=rows,
        condition=condition,
        groups=groups,
        seed=seed,
    )

    if config["inner_group_col"] is not None:
        inner_groups = manifest_groups(rows, config["inner_group_col"])[train_idx]
    else:
        inner_groups = groups[train_idx]

    pilot_report = run_residual_acquisition_pilot(
        raw_cache=cache,
        y=y,
        train_idx=train_idx,
        test_idx=test_idx,
        inner_groups=inner_groups,
        dataset_name=dataset_name,
        condition=condition,
        base_extractor=BASE_EXTRACTOR,
        candidate_subset=CANDIDATE_SUBSET,
        target_budget_ms=target_budget_ms,
        repo_root=REPO,
        seed=seed,
    )

    save_condition_artifacts(
        dest_dir=dest_dir,
        dataset_name=dataset_name,
        condition=condition,
        protocol=config["protocol"],
        seed=seed,
        train_idx=train_idx,
        test_idx=test_idx,
        inner_groups=inner_groups,
        graph=pilot_report["graph"],
        cost_model=pilot_report["cost_model"],
        tuning_info=pilot_report["prospective_tuning"],
        test_results=pilot_report["results_table"],
        predictions_record=pilot_report["predictions_record"],
        trace_events=pilot_report["trace_events"],
        allowlist_22=CANONICAL_22_ALLOWLIST,
    )

    # Persistir también diagnósticos de ablaciones y puerta de avance
    with open(dest_dir / "ablations_summary.json", "w", encoding="utf-8") as f:
        json.dump(pilot_report["ablations_summary"], f, indent=2)

    with open(dest_dir / "gate_assessment.json", "w", encoding="utf-8") as f:
        json.dump(pilot_report["gate_assessment"], f, indent=2)

    elapsed = time.time() - t0
    f1_h2 = pilot_report["results_table"]["FSC_Tex_H2_Bellman"]["macro_f1"]
    lat_h2 = pilot_report["results_table"]["FSC_Tex_H2_Bellman"]["mean_latency_ms"]
    print(f"  [LISTO] {dataset_name} / {cond_str} en {elapsed:.1f}s -> H2 Macro-F1: {f1_h2:.4f}, Latencia: {lat_h2:.2f} ms")

    return pilot_report["results_table"]


def main():
    parser = argparse.ArgumentParser(description="FSC-Tex Fase 3 v2 Suite Runner")
    parser.add_argument("--dataset", type=str, default=None, choices=list(DATASET_CONFIGS.keys()), help="Dataset específico")
    parser.add_argument("--condition", type=str, default=None, help="Condición específica (e.g. 1 o a_to_b)")
    parser.add_argument("--target_budget_ms", type=float, default=35.0, help="Presupuesto físico objetivo (ms)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")
    parser.add_argument("--force", action="store_true", help="Forzar re-ejecución ignorando artefactos existentes")
    parser.add_argument("--output_dir", type=Path, default=REPO / "results/exploratory/fsc_tex/phase3_v2_suite", help="Directorio de salida")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    datasets_to_run = [args.dataset] if args.dataset else list(DATASET_CONFIGS.keys())

    total_conditions = 0
    completed_conditions = 0
    t0_suite = time.time()

    print(f"==================================================================")
    print(f"FSC-Tex Fase 3 v2: Suite Canónica Congelada de Evaluación (Hito R6)")
    print(f"Directorio de salida: {args.output_dir}")
    print(f"Presupuesto objetivo: {args.target_budget_ms:.1f} ms | Semilla: {args.seed}")
    print(f"==================================================================")

    for ds_name in datasets_to_run:
        config = DATASET_CONFIGS[ds_name]
        conds = [args.condition] if args.condition else config["conditions"]

        print(f"\n--- Dataset: {ds_name} ({len(conds)} condiciones) ---")
        for cond in conds:
            # Parsear tipo si es numérico
            if isinstance(cond, str) and cond.isdigit():
                cond_val: Any = int(cond)
            else:
                cond_val = cond

            total_conditions += 1
            try:
                run_condition_v2(
                    dataset_name=ds_name,
                    condition=cond_val,
                    config=config,
                    output_dir=args.output_dir,
                    target_budget_ms=args.target_budget_ms,
                    seed=args.seed,
                    force=args.force,
                )
                completed_conditions += 1
            except Exception as e:
                print(f"  [ERROR] Falló condición {cond_val} en {ds_name}: {e}")
                import traceback
                traceback.print_exc()

    elapsed_suite = time.time() - t0_suite
    print(f"\n==================================================================")
    print(f"Suite v2 finalizada: {completed_conditions}/{total_conditions} condiciones en {elapsed_suite/60:.2f} min")
    print(f"==================================================================")


if __name__ == "__main__":
    main()
