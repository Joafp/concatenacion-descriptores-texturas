"""Comparación de paridad entre LinearSVC de scikit-learn y cuML."""

from pathlib import Path
import sys
import time

import cupy as cp
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.svm import LinearSVC as CpuLinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from run_confirmatory_nested import (
    load_dataset,
    load_manifest,
    official_split_indices,
)
from cuml.svm import LinearSVC as GpuLinearSVC


DATASET = "DTD"
SEED = 42
SPLIT = 1


def main():
    cache, y = load_dataset(ROOT, DATASET)
    _, rows = load_manifest(ROOT / "results/confirmatory", DATASET, y)
    train, test = official_split_indices(rows, SPLIT)
    archived = pd.read_csv(ROOT / "results/confirmatory/diverse_topk_control/nested_fold_results.csv")
    row = archived[(archived.dataset == DATASET) & (archived.classifier == "svm")
                   & (archived.seed == SEED) & (archived.outer_fold == SPLIT - 1)].iloc[0]
    subset = str(row.selected).split("+")
    x = np.concatenate([cache[name] for name in subset], axis=1).astype(np.float32)

    cpu = CpuLinearSVC(C=1.0, class_weight="balanced", random_state=SEED,
                       dual="auto", max_iter=10000)
    started = time.perf_counter()
    cpu.fit(x[train], y[train])
    cpu_fit_seconds = time.perf_counter() - started
    pred_cpu = cpu.predict(x[test])

    gpu = GpuLinearSVC(C=1.0, class_weight="balanced", penalty="l2",
                       loss="squared_hinge", multi_class="ovr", max_iter=1000,
                       tol=1e-4, output_type="numpy")
    started = time.perf_counter()
    gpu.fit(cp.asarray(x[train]), cp.asarray(y[train]))
    cp.cuda.Stream.null.synchronize()
    gpu_fit_seconds = time.perf_counter() - started
    pred_gpu = np.asarray(gpu.predict(cp.asarray(x[test])))

    print({
        "dataset": DATASET, "split": SPLIT, "subset": "+".join(subset),
        "cpu_macro_f1": float(f1_score(y[test], pred_cpu, average="macro")),
        "gpu_macro_f1": float(f1_score(y[test], pred_gpu, average="macro")),
        "cpu_accuracy": float(accuracy_score(y[test], pred_cpu)),
        "gpu_accuracy": float(accuracy_score(y[test], pred_gpu)),
        "prediction_disagreement": float(np.mean(pred_cpu != pred_gpu)),
        "cpu_fit_seconds": cpu_fit_seconds,
        "gpu_fit_seconds": gpu_fit_seconds,
        "speedup_cpu_over_gpu": cpu_fit_seconds / gpu_fit_seconds,
        "n_test": int(len(test)),
    })


if __name__ == "__main__":
    main()
