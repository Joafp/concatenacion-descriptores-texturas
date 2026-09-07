"""Control anidado top-k que prioriza cobertura de familias.

En cada entrenamiento externo se puntúan los 20 bloques individualmente con
los mismos cuatro folds internos que GFS.  La lista candidata toma primero el
mejor bloque de cada familia (en el orden dictado por ese rendimiento interno)
y, después, los bloques restantes por rendimiento individual.  Se valida cada
prefijo de longitud k=1..max_k y se conserva el mejor.  Ninguna decisión usa
el test externo.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from run_confirmatory_nested import (
    FAMILIES,
    append_rows,
    audit_gate,
    curet_half_indices,
    fit_score,
    fit_score_matrix,
    inner_score,
    load_dataset,
    load_manifest,
    official_split_indices,
)


def gpu_fit_score(cache, subset, train, test, y, seed):
    """Ajuste/evaluación cuML manteniendo la interfaz de fit_score."""
    import cupy as cp
    from cuml.svm import LinearSVC

    x = np.concatenate([cache[name] for name in subset], axis=1).astype(np.float32)
    model = LinearSVC(C=1.0, class_weight="balanced", penalty="l2",
                      loss="squared_hinge", multi_class="ovr", max_iter=1000,
                      tol=1e-4, output_type="numpy")
    started = __import__("time").perf_counter()
    model.fit(cp.asarray(x[train]), cp.asarray(y[train]))
    pred = np.asarray(model.predict(cp.asarray(x[test])))
    cp.cuda.Stream.null.synchronize()
    return (float(__import__("sklearn.metrics", fromlist=["f1_score"]).f1_score(
                    y[test], pred, average="macro")),
            float(__import__("sklearn.metrics", fromlist=["accuracy_score"]).accuracy_score(
                    y[test], pred)),
            __import__("time").perf_counter() - started)


def gpu_inner_score(cache, subset, outer_train, y, groups, seed, n_splits=4):
    import cupy as cp
    from cuml.svm import LinearSVC
    from sklearn.metrics import f1_score

    x = np.concatenate([cache[name] for name in subset], axis=1).astype(np.float32)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    scores = []
    for inner_train_pos, inner_val_pos in splitter.split(outer_train, y[outer_train], groups[outer_train]):
        inner_train = outer_train[inner_train_pos]
        inner_val = outer_train[inner_val_pos]
        model = LinearSVC(C=1.0, class_weight="balanced", penalty="l2",
                          loss="squared_hinge", multi_class="ovr", max_iter=1000,
                          tol=1e-4, output_type="numpy")
        model.fit(cp.asarray(x[inner_train]), cp.asarray(y[inner_train]))
        pred = np.asarray(model.predict(cp.asarray(x[inner_val])))
        scores.append(float(f1_score(y[inner_val], pred, average="macro")))
    cp.cuda.Stream.null.synchronize()
    return float(np.mean(scores))


def outer_indices(dataset, seed, fold, y, groups, manifest_rows,
                  official_split=None, curet_direction=None):
    if official_split is not None:
        return official_split_indices(manifest_rows, official_split)
    if curet_direction is not None:
        return curet_half_indices(manifest_rows, curet_direction)
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    return list(splitter.split(np.zeros(len(y)), y, groups))[fold]


def family_diverse_order(ranked: list[tuple[float, str]]) -> list[str]:
    """Put the strongest representative of every family before repetitions."""
    selected: list[str] = []
    used_families: set[str] = set()
    for _, name in ranked:
        family = FAMILIES.get(name, "other")
        if family not in used_families:
            selected.append(name)
            used_families.add(family)
    selected_set = set(selected)
    selected.extend(name for _, name in ranked if name not in selected_set)
    return selected


def already_recorded(path: Path, dataset: str, classifier: str, seed: int, fold: int) -> bool:
    if not path.exists():
        return False
    import pandas as pd

    rows = pd.read_csv(path)
    return bool(((rows["dataset"] == dataset)
                 & (rows["classifier"] == classifier)
                 & (rows["seed"] == seed)
                 & (rows["outer_fold"] == fold)
                 & (rows["method"] == "diverse_topk")
                 & (rows["run_mode"] == "full")).any())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--fold", type=int, choices=range(5), required=True)
    split = parser.add_mutually_exclusive_group()
    split.add_argument("--official-split", type=int, choices=range(1, 11))
    split.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--max-k", type=int, default=8)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--n-jobs", type=int, default=2)
    parser.add_argument("--svm-backend", choices=("cpu", "cuml"), default="cpu",
                        help="backend for --classifier svm; cuml uses the CUDA GPU")
    args = parser.parse_args()
    if args.max_k < 1:
        parser.error("--max-k must be >= 1")
    if args.n_jobs < 1:
        parser.error("--n-jobs must be >= 1")

    repo = args.repo.resolve()
    output = (repo / args.output).resolve() if not args.output.is_absolute() else args.output
    embedding_root = args.embedding_root
    if embedding_root is not None and not embedding_root.is_absolute():
        embedding_root = (repo / embedding_root).resolve()

    audit_gate(output, args.dataset)
    cache, y = load_dataset(repo, args.dataset, embedding_root=embedding_root)
    groups, manifest_rows = load_manifest(output, args.dataset, y)
    train, test = outer_indices(
        args.dataset, args.seed, args.fold, y, groups, manifest_rows,
        args.official_split, args.curet_direction,
    )
    fold = (
        args.official_split - 1 if args.official_split is not None
        else {"a_to_b": 0, "b_to_a": 1}[args.curet_direction]
        if args.curet_direction is not None else args.fold
    )
    if set(groups[train]).intersection(groups[test]):
        raise AssertionError("source group leakage in outer split")

    if args.svm_backend == "cuml" and args.classifier != "svm":
        parser.error("--svm-backend cuml requires --classifier svm")
    control = output / ("diverse_topk_control_gpu" if args.svm_backend == "cuml"
                        else "diverse_topk_control")
    control.mkdir(parents=True, exist_ok=True)
    key = f"{args.dataset}__{args.classifier}__{args.seed}__{fold}"
    checkpoint = control / f"{key}.json"
    result_path = control / "nested_fold_results.csv"
    if checkpoint.exists() or already_recorded(result_path, args.dataset, args.classifier, args.seed, fold):
        print(f"RESUME skip completed {key}")
        return

    def score_subset(subset: list[str]) -> float:
        if args.classifier == "svm" and args.svm_backend == "cuml":
            return gpu_inner_score(cache, subset, train, y, groups, args.seed)
        return inner_score(cache, subset, train, y, groups, args.classifier, args.seed)

    names = sorted(cache)
    if args.classifier == "svm" and args.svm_backend == "cpu" and args.n_jobs > 1:
        with ThreadPoolExecutor(max_workers=args.n_jobs) as pool:
            singleton_scores = list(pool.map(lambda name: (score_subset([name]), name), names))
    else:
        singleton_scores = [(score_subset([name]), name) for name in names]
    ranked = sorted(singleton_scores, key=lambda item: (-item[0], item[1]))
    ordered = family_diverse_order(ranked)
    max_k = min(args.max_k, len(ordered))
    prefixes = [ordered[:k] for k in range(1, max_k + 1)]
    if args.classifier == "svm" and args.svm_backend == "cpu" and args.n_jobs > 1:
        with ThreadPoolExecutor(max_workers=args.n_jobs) as pool:
            prefix_scores = list(pool.map(score_subset, prefixes))
    else:
        prefix_scores = [score_subset(prefix) for prefix in prefixes]
    best_index = max(range(len(prefixes)), key=lambda i: (prefix_scores[i], -(i + 1)))
    selected = prefixes[best_index]
    inner_f1 = prefix_scores[best_index]
    if args.classifier == "svm" and args.svm_backend == "cuml":
        f1, accuracy, seconds = gpu_fit_score(cache, selected, train, test, y, args.seed)
    else:
        f1, accuracy, seconds = fit_score(cache, selected, train, test, y, args.classifier, args.seed)
    row = {
        "dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
        "outer_fold": fold, "run_mode": "full", "method": "diverse_topk",
        "macro_f1": f1, "accuracy": accuracy, "k": len(selected),
        "dimensions": sum(cache[name].shape[1] for name in selected), "fit_seconds": seconds,
        "selected": "+".join(selected), "inner_f1": inner_f1,
    }
    append_rows(result_path, [row])
    checkpoint.write_text(json.dumps({
        "status": "complete", **row,
        "family_diverse_order": ordered,
        "singleton_inner_scores": dict((name, score) for score, name in ranked),
        "prefix_inner_scores": dict((str(k), score) for k, score in enumerate(prefix_scores, start=1)),
    }, indent=2))
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
