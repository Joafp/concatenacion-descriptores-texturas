#!/usr/bin/env python3
"""Generador de Vectores de Predicción por Imagen para la Cascada Adaptativa (27 Condiciones).

Genera y persiste '{dataset}_{protocol}_predictions.json' para cada una de las 27 condiciones canónicas,
permitiendo el recálculo y auditoría independiente de Macro-F1 y Accuracy a nivel de muestra individual
sin necesidad de reentrenar ni consultar el conjunto de prueba durante la selección.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score

import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from run_adaptive_descriptor_pilot import margin  # noqa: E402
from run_confirmatory_nested import load_dataset, load_manifest, make_model, manifest_groups  # noqa: E402
from run_train_selected_topk_cascade import outer_split, result_root  # noqa: E402
from report_cost_aware_topk import CASCADE, DEFAULT_KTH_COST, DEFAULT_PROXY_COST, SOURCES, component_costs  # noqa: E402


def stack(cache: dict, blocks: list[str]) -> np.ndarray:
    return np.concatenate([cache[b] for b in blocks], axis=1)


def evaluate_with_predictions(
    selection: dict,
    cache: dict,
    train: np.ndarray,
    test: np.ndarray,
    y: np.ndarray,
    topk_test_pred: np.ndarray,
) -> tuple[np.ndarray, list[bool]]:
    chosen = selection["selected"]
    if chosen["route"] == "topk_direct":
        return topk_test_pred, [True] * len(test)

    cheap = chosen["cheap"]
    model = make_model("svm", 42)
    x = stack(cache, [cheap])
    model.fit(x[train], y[train])
    c_pred = model.predict(x[test])
    c_margins = margin(model, x[test])
    req = c_margins <= chosen["threshold"]
    pred = np.where(req, topk_test_pred, c_pred)
    return pred, req.tolist()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=CASCADE / "cheap_stage_selected_primary22")
    args = parser.parse_args()

    kth_costs = component_costs(DEFAULT_KTH_COST)
    proxy_costs = component_costs(DEFAULT_PROXY_COST)

    print("Iniciando generación y persistencia de predicciones a nivel de muestra...")
    total_samples = 0
    start_time = time.perf_counter()

    for dataset, directory in SOURCES.items():
        costs = kth_costs if dataset == "KTHTIPS2b" else proxy_costs
        archive_dir = CASCADE / directory / "exact_archive"
        paths = sorted(archive_dir.glob("*_topk_cascade.json"))
        root = result_root(dataset, directory)
        embedding_root = (REPO / "embeddings_extensions" if dataset in {"Outex13Official1360", "SoilOriginal", "KTHTIPS2b"}
                          else REPO / "embeddings" if dataset == "DTD" else REPO / "embeddings_confirmatory")
        cache, y = load_dataset(REPO, dataset, embedding_root=embedding_root)
        groups, rows = load_manifest(root, dataset, y)
        labels = np.unique(y)

        for path in paths:
            entry = json.loads(path.read_text(encoding="utf-8"))
            protocol = entry["protocol"]
            stem = f"{dataset}_{protocol}".replace(":", "__")
            result_file = args.output / f"{stem}_result.json"
            pretest_file = args.output / f"{stem}_selection_pretest.json"
            pred_file = args.output / f"{stem}_predictions.json"

            if not result_file.exists() or not pretest_file.exists():
                raise FileNotFoundError(f"Faltan artefactos para {dataset} {protocol}")

            result_data = json.loads(result_file.read_text(encoding="utf-8"))
            pretest_data = json.loads(pretest_file.read_text(encoding="utf-8"))

            topk = entry["expensive_blocks"]
            train, test = outer_split(entry, y, groups, rows)

            # 1. Ajuste de Top-k en entrenamiento y predicción en test
            xk = stack(cache, topk)
            topk_model = make_model("svm", 42)
            topk_model.fit(xk[train], y[train])
            topk_test = topk_model.predict(xk[test])

            # 2. Evaluación de Cascada Adaptativa
            pred_new, req_new = evaluate_with_predictions(
                pretest_data["selected_cheap_stage"], cache, train, test, y, topk_test
            )

            # 3. Evaluación de Cascada ResNet-50
            pred_res, req_res = evaluate_with_predictions(
                pretest_data["resnet50_only"], cache, train, test, y, topk_test
            )

            # Verificación de exactitud estricta frente al registro auditado
            f1_new = float(f1_score(y[test], pred_new, labels=labels, average="macro", zero_division=0))
            f1_res = float(f1_score(y[test], pred_res, labels=labels, average="macro", zero_division=0))
            f1_topk = float(f1_score(y[test], topk_test, labels=labels, average="macro", zero_division=0))

            expected_new = result_data["selected_cheap_stage"]["macro_f1"]
            expected_res = result_data["resnet50_only"]["macro_f1"]
            expected_topk = result_data["topk_direct"]["macro_f1"]

            assert np.isclose(f1_new, expected_new, rtol=0, atol=1e-12), f"Discrepancia en {dataset} {protocol} (new)"
            assert np.isclose(f1_res, expected_res, rtol=0, atol=1e-12), f"Discrepancia en {dataset} {protocol} (res)"
            assert np.isclose(f1_topk, expected_topk, rtol=0, atol=1e-12), f"Discrepancia en {dataset} {protocol} (topk)"

            # Guardado del artefacto de predicciones
            pred_record = {
                "dataset": dataset,
                "protocol": protocol,
                "n_test_samples": len(test),
                "test_indices": test.tolist(),
                "y_true": y[test].tolist(),
                "y_pred_adaptive_cascade": pred_new.tolist(),
                "requested_topk_adaptive": req_new,
                "y_pred_resnet50_cascade": pred_res.tolist(),
                "requested_topk_resnet": req_res,
                "y_pred_topk_direct": topk_test.tolist(),
                "metrics_recomputed": {
                    "adaptive_cascade_macro_f1": f1_new,
                    "adaptive_cascade_accuracy": float(accuracy_score(y[test], pred_new)),
                    "resnet50_cascade_macro_f1": f1_res,
                    "resnet50_cascade_accuracy": float(accuracy_score(y[test], pred_res)),
                    "topk_direct_macro_f1": f1_topk,
                    "topk_direct_accuracy": float(accuracy_score(y[test], topk_test)),
                },
            }
            pred_file.write_text(json.dumps(pred_record, indent=2) + "\n", encoding="utf-8")
            total_samples += len(test)
            print(f"  [OK] {dataset:18s} {protocol:30s} N={len(test):4d} | F1={f1_new:.4f} guardado en {pred_file.name}")

    elapsed = time.perf_counter() - start_time
    print(f"\n¡Completado! {total_samples} predicciones guardadas en 27 condiciones en {elapsed:.1f} segundos.")


if __name__ == "__main__":
    main()
