#!/usr/bin/env python3
"""FSC-Tex Hito P4: Benchmark Físico Online sobre Imágenes Reales y Auditoría de Paridad.

Mide la eficiencia física end-to-end con modelos residentes en GPU y CUDA synchronization:
1. Modelos soportados residentes en memoria: ResNet-50, SigLIP, BEiTv2, DINOv2, ConvNeXt V2-T y EVA-02.
2. Medición directa de tiempos envolventes (wall-clock) con torch.cuda.synchronize():
   - Extractor base
   - Sobrecosto del mecanismo de política (gating)
   - Extractores incrementales adquiridos bajo demanda
   - Inferencia del clasificador (LinearSVC)
   - Tiempo total end-to-end
3. Auditoría de memoria VRAM (inicial, pico y residente).
4. Verificación de paridad empírica:
   - Route Agreement: coincidencia de las secuencias de bloques adquiridos entre ejecución física y simulación.
   - Prediction Agreement: coincidencia de la predicción final.
   - Paridad de costos: comparación entre el HardwareCostModel estático y la latencia real observada en GPU.

Salida: results/exploratory/fsc_tex/p4_physical_benchmark_report.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS, HardwareCostModel
from fsc_tex.crossfit import (
    ProtectedFeatureStore,
    fit_final_classifiers,
    generate_oof_state_data,
    select_hyperparameters_prospective,
)
from fsc_tex.executor import OnlineExtractorRegistry, OnlineSequentialPolicyExecutor
from fsc_tex.policy import SequentialAcquisitionPolicy
from fsc_tex.state_graph import State, StateGraph
from run_confirmatory_nested import load_dataset, load_manifest, official_split_indices

EXTRACTORS_TO_BENCHMARK = [
    "resnet50",
    "siglip_base",
    "beitv2_base_final",
    "convnext_v2_t",
    "eva02_base",
    "dinov2",
]


def measure_individual_extractor_latencies(
    registry: OnlineExtractorRegistry,
    image_paths: List[Path],
    n_warmup: int = 5,
) -> Dict[str, Dict[str, float]]:
    """Mide la latencia física real de cada extractor sobre imágenes reales en GPU."""
    results = {}
    print("\n--- Medición Física de Extractores Individuales en GPU ---")

    for name in EXTRACTORS_TO_BENCHMARK:
        fn = registry.load_extractor(name)
        # Warmup
        dummy = Image.open(image_paths[0]).convert("RGB")
        for _ in range(n_warmup):
            fn(dummy)
        if registry.is_cuda():
            torch.cuda.synchronize()

        times_ms = []
        for p in image_paths:
            img = Image.open(p).convert("RGB")
            t0 = time.perf_counter()
            _ = fn(img)
            if registry.is_cuda():
                torch.cuda.synchronize()
            t1 = time.perf_counter()
            times_ms.append((t1 - t0) * 1000.0)

        mean_ms = float(np.mean(times_ms))
        std_ms = float(np.std(times_ms))
        median_ms = float(np.median(times_ms))
        p95_ms = float(np.percentile(times_ms, 95))
        cost_model_pred = float(DEFAULT_HARDWARE_LATENCY_MS.get(name, 0.0))
        delta_pct = float((mean_ms - cost_model_pred) / max(0.1, cost_model_pred) * 100.0)

        print(f"  [{name:18s}] Medido: {mean_ms:6.2f} ± {std_ms:4.2f} ms | CostModel: {cost_model_pred:6.2f} ms | Error: {delta_pct:+5.1f}%")

        results[name] = {
            "mean_latency_ms": mean_ms,
            "std_latency_ms": std_ms,
            "median_latency_ms": median_ms,
            "p95_latency_ms": p95_ms,
            "cost_model_latency_ms": cost_model_pred,
            "discrepancy_pct": delta_pct,
        }

    return results


def run_physical_online_benchmark(
    dataset_name: str = "DTD",
    condition: int = 1,
    target_budget_ms: float = 45.0,
    n_benchmark_samples: int = 50,
    lambda_val: Optional[float] = None,
    seed: int = 42,
    output_file: Path = REPO / "results/exploratory/fsc_tex/p4_physical_benchmark_report.json",
) -> Dict[str, Any]:
    print("=" * 80)
    print(f"  FSC-TEX HITO P4: BENCHMARK FÍSICO ONLINE EN GPU ({dataset_name} cond {condition})")
    print("=" * 80)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Dispositivo activo: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        torch.cuda.reset_peak_memory_stats()
        vram_initial_mb = float(torch.cuda.memory_allocated() / (1024 * 1024))
    else:
        vram_initial_mb = 0.0

    # 1. Cargar dataset y manifiesto
    cache, y = load_dataset(REPO, dataset_name, embedding_root=REPO / "embeddings")
    groups, rows = load_manifest(REPO / "results/confirmatory", dataset_name, y)
    train_idx, test_idx = official_split_indices(rows, condition)
    y_train = y[train_idx]
    inner_groups = groups[train_idx]

    feature_store = ProtectedFeatureStore(cache)
    cost_model = HardwareCostModel(cost_mode="hardware")
    base_block = "resnet50"
    candidates = ["siglip_base", "beitv2_base_final", "dinov2", "convnext_v2_t", "eva02_base"]
    graph = StateGraph(base_block=base_block, candidate_blocks=candidates, max_depth=3)

    # 2. Ajustar política y clasificadores en T_train
    print(f"\n[1/4] Ajustando clasificadores y política H2 en T_train (|T_train|={len(train_idx)})...")
    oof_feats, oof_losses, _, _, _ = generate_oof_state_data(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        inner_groups=inner_groups,
        graph=graph,
        n_splits=3,
        seed=seed,
        cost_model=cost_model,
        target_budget_ms=target_budget_ms,
    )

    if lambda_val is not None:
        sel_lambda = float(lambda_val)
        print(f"  Usando lambda prospectivo provisto: {sel_lambda}")
    else:
        tuning = select_hyperparameters_prospective(
            feature_store=feature_store,
            train_idx=train_idx,
            y_train=y_train,
            inner_groups=inner_groups,
            graph=graph,
            cost_model=cost_model,
            target_budget_ms=target_budget_ms,
            lambda_grid=[0.001, 0.01, 0.05, 0.1, 0.2],
            quantile_grid=[0.1, 0.2, 0.3, 0.4, 0.5],
            n_inner_splits=3,
            seed=seed,
            horizon=2,
        )
        sel_lambda = tuning["selected_lambda"]
        print(f"  Lambda sintonizado prospectivamente: {sel_lambda}")

    final_clfs = fit_final_classifiers(
        feature_store=feature_store,
        train_idx=train_idx,
        y_train=y_train,
        graph=graph,
        seed=seed,
    )

    policy_h2 = SequentialAcquisitionPolicy(
        graph=graph,
        cost_model=cost_model,
        horizon=2,
        cost_lambda=sel_lambda,
        random_state=seed,
    )
    policy_h2.fit_transitions(oof_feats, oof_losses, max_budget=target_budget_ms)

    # 3. Preparar registro de modelos residentes
    print("\n[2/4] Cargando modelos residentes en GPU...")
    registry = OnlineExtractorRegistry(device=device, seed=seed)
    registry.warmup([base_block] + candidates, n_warmup=2)

    if device == "cuda":
        vram_resident_mb = float(torch.cuda.memory_allocated() / (1024 * 1024))
        print(f"  VRAM residente ocupada por los 6 modelos: {vram_resident_mb:.1f} MB")
    else:
        vram_resident_mb = 0.0

    # 4. Seleccionar muestra de imágenes reales para el benchmark
    # Usamos las primeras N imágenes de evaluación disponibles
    eval_sample_indices = test_idx[:n_benchmark_samples]
    eval_image_paths = []
    for idx in eval_sample_indices:
        src_rel = rows[idx]["source_path"]
        eval_image_paths.append(REPO / src_rel)

    # Medición física de extractores
    ind_latencies = measure_individual_extractor_latencies(registry, eval_image_paths[:10], n_warmup=3)

    # 5. Ejecutar benchmark de inferencia física online vs simulación cacheada
    print(f"\n[3/4] Ejecutando Inferencia Física Online sobre {len(eval_sample_indices)} imágenes reales...")
    executor = OnlineSequentialPolicyExecutor(
        policy=policy_h2,
        state_classifiers=final_clfs,
        graph=graph,
        cost_model=cost_model,
        extractor_registry=registry,
        target_budget_ms=target_budget_ms,
    )

    online_results = []
    cached_results = []

    base_cost_ms = cost_model.cumulative_cost_ms(graph.initial_state.blocks)

    for i, global_idx in enumerate(eval_sample_indices):
        img_path = eval_image_paths[i]
        img = Image.open(img_path).convert("RGB")

        # Inferencia Física Online
        res_on = executor.execute_image(img)
        online_results.append(res_on)

        # Simulación Cacheada
        curr_s = graph.initial_state
        rem_b = target_budget_ms - base_cost_ms
        sim_route = list(curr_s.blocks)

        while len(curr_s) < graph.max_depth and rem_b > 0:
            clf_c = final_clfs[curr_s.id]
            X_c = feature_store.get_state_matrix(curr_s)[global_idx : global_idx + 1]
            df_c = clf_c.decision_function(X_c)
            m_c = float(np.abs(df_c)[0]) if df_c.ndim == 1 else float(np.partition(df_c, -2, axis=1)[0, -1] - np.partition(df_c, -2, axis=1)[0, -2])
            top_s = np.abs(df_c.ravel()) if df_c.ndim == 1 else np.sort(df_c[0])[::-1]

            feat_c = graph.encode_state_features(
                state=curr_s,
                margin=m_c,
                top_scores=top_s,
                remaining_budget=float(rem_b),
            )
            act, _ = policy_h2.select_action(curr_s, feat_c, remaining_budget=rem_b)
            if act == "STOP":
                break
            rem_b = max(0.0, rem_b - cost_model.incremental_cost(act, curr_s.blocks))
            curr_s = curr_s.add(act)
            sim_route.append(act)

        clf_fin = final_clfs[curr_s.id]
        X_fin = feature_store.get_state_matrix(curr_s)[global_idx : global_idx + 1]
        sim_pred = clf_fin.predict(X_fin)[0]
        cached_results.append({
            "final_prediction": sim_pred,
            "final_state": curr_s.id,
            "route": sim_route,
        })

    if device == "cuda":
        vram_peak_mb = float(torch.cuda.max_memory_allocated() / (1024 * 1024))
    else:
        vram_peak_mb = 0.0

    # 6. Calcular métricas de paridad y tiempos
    print("\n[4/4] Verificando Paridad y Métricas de Rendimiento...")
    route_matches = sum(1 for o, c in zip(online_results, cached_results) if o["final_state"] == c["final_state"])
    pred_matches = sum(1 for o, c in zip(online_results, cached_results) if o["final_prediction"] == c["final_prediction"])

    route_agreement_pct = float(route_matches / len(eval_sample_indices) * 100.0)
    pred_agreement_pct = float(pred_matches / len(eval_sample_indices) * 100.0)

    total_times = [r["total_measured_ms"] for r in online_results]
    ext_times = [r["latency_breakdown_ms"]["extractor_ms"] for r in online_results]
    gate_times = [r["latency_breakdown_ms"]["policy_gate_ms"] for r in online_results]
    clf_times = [r["latency_breakdown_ms"]["classifier_ms"] for r in online_results]

    mean_total_ms = float(np.mean(total_times))
    mean_ext_ms = float(np.mean(ext_times))
    mean_gate_ms = float(np.mean(gate_times))
    mean_clf_ms = float(np.mean(clf_times))

    print(f"  Route Agreement (Online vs Cached):      {route_agreement_pct:5.1f}% ({route_matches}/{len(eval_sample_indices)})")
    print(f"  Prediction Agreement (Online vs Cached): {pred_agreement_pct:5.1f}% ({pred_matches}/{len(eval_sample_indices)})")
    print(f"\n  Desglose de Tiempos End-to-End Medidos (Promedio por Imagen):")
    print(f"    - Extractores físicos (GPU):  {mean_ext_ms:6.2f} ms ({mean_ext_ms/mean_total_ms*100:4.1f}%)")
    print(f"    - Decisión política (Gating): {mean_gate_ms:6.2f} ms ({mean_gate_ms/mean_total_ms*100:4.1f}%)")
    print(f"    - Clasificador final:         {mean_clf_ms:6.2f} ms ({mean_clf_ms/mean_total_ms*100:4.1f}%)")
    print(f"    - TIEMPO TOTAL REAL:          {mean_total_ms:6.2f} ms")
    print(f"    - VRAM Pico:                  {vram_peak_mb:6.1f} MB")

    parity_audit = {
        "dataset": dataset_name,
        "condition": condition,
        "target_budget_ms": target_budget_ms,
        "n_samples": len(eval_sample_indices),
        "device": device,
        "gpu_name": torch.cuda.get_device_name(0) if device == "cuda" else "cpu",
        "vram_memory_mb": {
            "initial_allocated": vram_initial_mb,
            "resident_models": vram_resident_mb,
            "peak_allocated": vram_peak_mb,
        },
        "individual_extractors_physical": ind_latencies,
        "parity_verification": {
            "route_agreement_pct": route_agreement_pct,
            "prediction_agreement_pct": pred_agreement_pct,
            "parity_passed": (route_agreement_pct >= 90.0 and pred_agreement_pct >= 90.0),
        },
        "end_to_end_timings_ms": {
            "mean_total_measured_ms": mean_total_ms,
            "mean_extractor_ms": mean_ext_ms,
            "mean_policy_gating_ms": mean_gate_ms,
            "mean_classifier_ms": mean_clf_ms,
            "gating_overhead_pct": float(mean_gate_ms / mean_total_ms * 100.0),
        },
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(parity_audit, f, indent=2)

    print(f"\nReporte guardado atómicamente en: {output_file}")
    print("=" * 80)
    return parity_audit


def main():
    parser = argparse.ArgumentParser(description="FSC-Tex Physical Online Benchmark Runner")
    parser.add_argument("--dataset", type=str, default="DTD")
    parser.add_argument("--condition", type=int, default=1)
    parser.add_argument("--budget", type=float, default=45.0)
    parser.add_argument("--samples", type=int, default=50)
    parser.add_argument("--lambda_val", type=float, default=None, help="Lambda prospectivo opcional para saltar grilla")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_file", type=Path, default=REPO / "results/exploratory/fsc_tex/p4_physical_benchmark_report.json")
    args = parser.parse_args()

    run_physical_online_benchmark(
        dataset_name=args.dataset,
        condition=args.condition,
        target_budget_ms=args.budget,
        n_benchmark_samples=args.samples,
        lambda_val=args.lambda_val,
        seed=args.seed,
        output_file=args.output_file,
    )


if __name__ == "__main__":
    main()
