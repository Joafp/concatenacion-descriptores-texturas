#!/usr/bin/env python3
"""Nested-CV confirmatorio con gate de datos, checkpoints y resume.

Requiere ``results/confirmatory/sample_manifests/<dataset>.csv`` con una fila
por embedding y columnas ``row_id,label,group``. El manifiesto debe provenir de
metadatos de origen verificables; este programa nunca infiere grupos.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.svm import LinearSVC

SRC_DIR = str(Path(__file__).resolve().parent)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
from curet_confirmatory_protocol import curet_half_indices


FAMILIES = {
    "lbp": "classical", "drlbp": "classical", "gabor": "classical",
    "glcm": "classical", "hog": "classical",
    "resnet50": "cnn", "resnet101": "cnn", "vgg16": "cnn",
    "densenet121": "cnn", "efficientnet_b0": "cnn", "convnext_v2_t": "cnn",
    "vit_b16": "transformer", "deit_s": "transformer", "swin_t": "transformer",
    "dinov2": "self_supervised", "dinov2_small": "self_supervised",
    "dinov2_large": "self_supervised", "mae_base": "self_supervised",
    "siglip_base": "self_supervised", "eva02_base": "transformer",
    "rgb_ngram_svd": "ngram",
    "beitv2_base": "transformer", "swinv2_base": "transformer",
}
RESULT_FIELDS = [
    "dataset", "classifier", "seed", "outer_fold", "run_mode", "method", "macro_f1",
    "accuracy", "k", "dimensions", "fit_seconds", "selected", "inner_f1",
]


def canonical_labels(y: np.ndarray) -> np.ndarray:
    mapping: dict[str, int] = {}
    return np.asarray([mapping.setdefault(str(v), len(mapping)) for v in y], dtype=np.int64)


def l2_rows(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(norm, 1e-12)


def load_dataset(repo: Path, dataset: str, embedding_root: Path | None = None) -> tuple[dict[str, np.ndarray], np.ndarray]:
    if embedding_root is not None:
        base = embedding_root / dataset
    else:
        confirmatory = repo / "embeddings_confirmatory" / dataset
        base = confirmatory if confirmatory.is_dir() else repo / "embeddings" / dataset
    cache: dict[str, np.ndarray] = {}
    reference = None
    for path in sorted(base.glob("*.npy")):
        if path.name.endswith("_labels.npy"):
            continue
        labels_path = base / f"{path.stem}_labels.npy"
        if not labels_path.exists():
            continue
        y = canonical_labels(np.load(labels_path, allow_pickle=False))
        x = np.load(path)
        if x.ndim != 2 or len(x) != len(y) or not np.isfinite(x).all():
            raise ValueError(f"invalid embedding: {path}")
        if reference is None:
            reference = y
        if not np.array_equal(reference, y):
            raise ValueError(f"label partition mismatch: {labels_path}")
        cache[path.stem] = l2_rows(x)
    if not cache or reference is None:
        raise ValueError(f"no valid embeddings for {dataset}")
    return cache, reference


def load_manifest(output: Path, dataset: str, y: np.ndarray) -> tuple[np.ndarray, list[dict]]:
    path = output / "sample_manifests" / f"{dataset}.csv"
    if not path.exists():
        raise FileNotFoundError(f"verified sample manifest required: {path}")
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"row_id", "label", "group"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"manifest must contain {sorted(required)}")
    if [int(r["row_id"]) for r in rows] != list(range(len(y))):
        raise ValueError("manifest row_id does not exactly cover embedding row order")
    manifest_y = canonical_labels(np.asarray([r["label"] for r in rows]))
    if not np.array_equal(y, manifest_y):
        raise ValueError("manifest labels do not match embedding class partition")
    groups = np.asarray([r["group"] for r in rows])
    if any(not g for g in groups):
        raise ValueError("empty source group in manifest")
    return groups, rows


def official_split_indices(rows: list[dict], split_number: int) -> tuple[np.ndarray, np.ndarray]:
    """Use a manifest-defined official train[/val]/test partition."""
    numbered_column = f"split_{split_number}"
    if not rows:
        raise ValueError("empty official manifest")
    if numbered_column in rows[0]:
        column = numbered_column
    elif split_number == 1 and "official_split" in rows[0]:
        column = "official_split"
    else:
        raise ValueError(f"manifest has no official {numbered_column}")
    roles = np.asarray([r[column] for r in rows])
    observed = set(roles)
    allowed = ({"train", "val", "test"}, {"train", "test"})
    if observed not in allowed:
        raise ValueError(f"invalid roles in {column}: {sorted(set(roles))}")
    train = np.flatnonzero(np.isin(roles, ["train", "val"]))
    test = np.flatnonzero(roles == "test")
    # Purga conservadora: el release DTD contiene duplicados byte-idénticos que
    # cruzan roles. Se conserva el test oficial y se excluye su copia de train/val.
    test_groups = {rows[i]["group"] for i in test}
    train = np.asarray([i for i in train if rows[i]["group"] not in test_groups], dtype=np.int64)
    if set(train).intersection(test):
        raise AssertionError("official split row overlap")
    if {rows[i]["group"] for i in train}.intersection(test_groups):
        raise AssertionError("official split duplicate-content leakage")
    return train, test


def make_model(name: str, seed: int, svm_backend: str = "cpu"):
    if name == "svm":
        if svm_backend == "cuml":
            from cuml.svm import LinearSVC as CuLinearSVC
            return CuLinearSVC(C=1.0, class_weight="balanced", penalty="l2",
                               loss="squared_hinge", multi_class="ovr", max_iter=1000,
                               tol=1e-4, output_type="numpy")
        return LinearSVC(C=1.0, class_weight="balanced", random_state=seed, dual="auto", max_iter=10000)
    if name == "resmlp":
        src = str(Path(__file__).resolve().parent)
        if src not in sys.path:
            sys.path.insert(0, src)
        from resmlp_classifier import ResMLPClassifier
        return ResMLPClassifier(random_state=seed, max_epochs=100, patience=10)
    raise ValueError(name)


def matrix(cache: dict[str, np.ndarray], subset: list[str], idx: np.ndarray) -> np.ndarray:
    return np.concatenate([cache[name][idx] for name in subset], axis=1)


def fit_score(cache, subset, train, test, y, classifier, seed, svm_backend="cpu"):
    x = np.concatenate([cache[name] for name in subset], axis=1)
    return fit_score_matrix(x, train, test, y, classifier, seed, svm_backend)


def fit_score_foldaware(cache, subset, train, test, y, classifier, seed,
                        svm_backend="cpu", ngram_block=None):
    """Fit a subset, learning any trainable descriptor only from ``train``."""
    if ngram_block is None or ngram_block.name not in subset:
        return fit_score(cache, subset, train, test, y, classifier, seed, svm_backend)
    static = [name for name in subset if name != ngram_block.name]
    ng_train, ng_test, _ = ngram_block.transform(train, test)
    train_parts = [cache[name][train] for name in static] + [ng_train]
    test_parts = [cache[name][test] for name in static] + [ng_test]
    x_train = np.concatenate(train_parts, axis=1)
    x_test = np.concatenate(test_parts, axis=1)
    model = make_model(classifier, seed, svm_backend)
    started = time.perf_counter()
    if classifier == "svm" and svm_backend == "cuml":
        import cupy as cp
        model.fit(cp.asarray(x_train), cp.asarray(y[train]))
        pred = np.asarray(model.predict(cp.asarray(x_test)))
        cp.cuda.Stream.null.synchronize()
    else:
        model.fit(x_train, y[train])
        pred = model.predict(x_test)
    return (float(f1_score(y[test], pred, average="macro")),
            float(accuracy_score(y[test], pred)), time.perf_counter() - started)


def fit_score_matrix(x, train, test, y, classifier, seed, svm_backend="cpu"):
    model = make_model(classifier, seed, svm_backend)
    started = time.perf_counter()
    if classifier == "svm" and svm_backend == "cuml":
        import cupy as cp
        model.fit(cp.asarray(x[train]), cp.asarray(y[train]))
        pred = np.asarray(model.predict(cp.asarray(x[test])))
        cp.cuda.Stream.null.synchronize()
    else:
        model.fit(x[train], y[train])
        pred = model.predict(x[test])
    return (
        float(f1_score(y[test], pred, average="macro")),
        float(accuracy_score(y[test], pred)),
        time.perf_counter() - started,
    )


def inner_score(cache, subset, outer_train, y, groups, classifier, seed, n_splits=4,
                svm_backend="cpu", ngram_block=None):
    x = None
    if ngram_block is None or ngram_block.name not in subset:
        x = np.concatenate([cache[name] for name in subset], axis=1)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    scores = []
    for inner_train_pos, inner_val_pos in splitter.split(outer_train, y[outer_train], groups[outer_train]):
        inner_train = outer_train[inner_train_pos]
        inner_val = outer_train[inner_val_pos]
        if x is None:
            score, _, _ = fit_score_foldaware(
                cache, subset, inner_train, inner_val, y, classifier, seed,
                svm_backend, ngram_block,
            )
        else:
            score, _, _ = fit_score_matrix(x, inner_train, inner_val, y, classifier, seed,
                                           svm_backend)
        scores.append(score)
    return float(np.mean(scores))


def greedy(cache, candidates, outer_train, y, groups, classifier, seed, max_k,
           n_jobs=2, score_cache=None, svm_backend="cpu", ngram_block=None):
    selected: list[str] = []
    remaining = sorted(candidates)
    history = []
    low_improvements = 0
    historical_best = (float("-inf"), [])
    previous = None
    score_cache = {} if score_cache is None else score_cache
    effective_jobs = n_jobs if classifier == "svm" and svm_backend == "cpu" else 1
    for step in range(1, min(max_k, len(remaining)) + 1):
        specs = [(tuple(selected + [candidate]), candidate) for candidate in remaining]
        missing = [(subset, candidate) for subset, candidate in specs if subset not in score_cache]
        values = Parallel(n_jobs=effective_jobs, prefer="threads")(
            delayed(inner_score)(cache, list(subset), outer_train, y, groups, classifier, seed,
                                 svm_backend=svm_backend, ngram_block=ngram_block)
            for subset, _ in missing
        )
        for (subset, _), value in zip(missing, values):
            score_cache[subset] = value
        scored = [(score_cache[subset], candidate) for subset, candidate in specs]
        score, candidate = max(scored, key=lambda item: (item[0], item[1]))
        selected.append(candidate)
        remaining.remove(candidate)
        improvement = None if previous is None else score - previous
        history.append({"step": step, "added": candidate, "inner_f1": score, "improvement": improvement})
        if score > historical_best[0]:
            historical_best = (score, selected.copy())
        if improvement is not None and improvement < 0.001:
            low_improvements += 1
        else:
            low_improvements = 0
        previous = score
        if low_improvements >= 2:
            break
    return historical_best[1], historical_best[0], history


def audit_gate(output: Path, dataset: str) -> None:
    path = output / "data_audit.csv"
    with path.open(newline="") as handle:
        row = next((r for r in csv.DictReader(handle) if r["dataset"] == dataset), None)
    if row is None or not row["status"].startswith("PASS"):
        raise RuntimeError(f"{dataset}: BLOCKED_DATA_LEAKAGE_RISK")


def append_rows(path: Path, rows: list[dict]) -> None:
    exists = path.exists()
    with path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def run_condition(repo, output, dataset, classifier, seed, fold, random_b, max_k, smoke,
                  official_split=None, curet_direction=None, n_jobs=2, embedding_root=None,
                  svm_backend="cpu", include_rgb_ngram=False, ngram_components=256,
                  ngram_hash_bins=8192):
    if official_split is not None and curet_direction is not None:
        raise ValueError("official_split and curet_direction are mutually exclusive")
    if curet_direction is not None and dataset != "CUReT":
        raise ValueError("curet_direction is only valid for dataset CUReT")
    if dataset == "CUReT" and curet_direction is None:
        raise ValueError("dataset CUReT requires curet_direction")
    audit_gate(output, dataset)
    cache, y = load_dataset(repo, dataset, embedding_root=embedding_root)
    groups, manifest_rows = load_manifest(output, dataset, y)
    ngram_block = None
    if include_rgb_ngram:
        from rgb_ngram_descriptor import BLOCK_NAME, RGBNgramSVDBlock, build_count_cache
        count_dir = output / "rgb_ngram_count_cache" / dataset / "rgb_ngram_impl1"
        counts = build_count_cache(manifest_rows, repo, count_dir, "rgb_ngram_impl1")
        ngram_block = RGBNgramSVDBlock(counts, n_components=ngram_components,
                                       random_state=seed, hash_bins=ngram_hash_bins)
    if official_split is not None:
        train, test = official_split_indices(manifest_rows, official_split)
        fold = official_split - 1
    elif curet_direction is not None:
        train, test = curet_half_indices(manifest_rows, curet_direction)
        fold = {"a_to_b": 0, "b_to_a": 1}[curet_direction]
    else:
        splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
        splits = list(splitter.split(np.zeros(len(y)), y, groups))
        train, test = splits[fold]
    if set(groups[train]).intersection(groups[test]):
        raise AssertionError("source group leakage in outer split")
    ngram_output_dim = None
    if ngram_block is not None:
        ngram_output_dim = min(ngram_components, len(train) - 1, ngram_hash_bins - 1)
    # GPU/cuML runs live in an isolated subtree so CPU historical artifacts
    # remain reproducible and cannot be mixed accidentally.
    backend_root = output / "gpu_svm" if svm_backend == "cuml" else output
    if include_rgb_ngram:
        backend_root = backend_root / "ngram21"
    result_root = backend_root / "smoke" if smoke else backend_root
    result_root.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = result_root / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    run_mode = "smoke" if smoke else "full"
    split_tag = (f"official{official_split}" if official_split is not None
                 else curet_direction if curet_direction is not None else f"fold{fold}")
    key = f"{dataset}__{classifier}__{seed}__{split_tag}__{run_mode}"
    checkpoint = checkpoint_dir / f"{key}.json"
    if checkpoint.exists():
        print(f"RESUME skip completed {key}")
        return
    candidates = sorted(cache)
    if ngram_block is not None:
        candidates.append(ngram_block.name)
    if smoke:
        static_smoke = [name for name in candidates if ngram_block is None or name != ngram_block.name]
        candidates = static_smoke[: min(4, len(static_smoke))]
        if ngram_block is not None:
            candidates.append(ngram_block.name)
        max_k = min(2, max_k)
        random_b = min(3, random_b)
    memo = {}
    gfs, gfs_inner, history = greedy(cache, candidates, train, y, groups, classifier, seed,
                                     max_k, n_jobs=n_jobs, score_cache=memo,
                                     svm_backend=svm_backend, ngram_block=ngram_block)
    best_single = [history[0]["added"]]
    best_single_inner = history[0]["inner_f1"]
    family_options = []
    for family in sorted(set(FAMILIES.get(e, "other") for e in candidates)):
        members = [e for e in candidates if FAMILIES.get(e, "other") == family]
        subset, score, hist = greedy(cache, members, train, y, groups, classifier, seed,
                                     min(len(gfs), max_k), n_jobs=n_jobs, score_cache=memo,
                                     svm_backend=svm_backend, ngram_block=ngram_block)
        family_options.append((score, family, subset, hist))
    family_inner, family_name, family_subset, family_history = max(family_options)
    methods = [
        ("best_individual", best_single, best_single_inner),
        ("full_concat", candidates, float("nan")),
        ("gfs", gfs, gfs_inner),
        (f"best_homogeneous_{family_name}", family_subset, family_inner),
    ]
    rows = []
    for method, subset, inner in methods:
        f1, acc, seconds = fit_score_foldaware(cache, subset, train, test, y, classifier, seed,
                                               svm_backend, ngram_block)
        rows.append({
            "dataset": dataset, "classifier": classifier, "seed": seed, "outer_fold": fold,
            "run_mode": run_mode,
            "method": method, "macro_f1": f1, "accuracy": acc, "k": len(subset),
            "dimensions": sum(ngram_output_dim if ngram_block is not None and e == ngram_block.name
                              else cache[e].shape[1] for e in subset), "fit_seconds": seconds,
            "selected": "+".join(subset), "inner_f1": inner,
        })
    rng = np.random.default_rng(seed * 100 + fold)
    random_rows = []
    for iteration in range(random_b):
        subset = sorted(rng.choice(candidates, size=len(gfs), replace=False).tolist())
        f1, acc, seconds = fit_score_foldaware(cache, subset, train, test, y, classifier, seed,
                                               svm_backend, ngram_block)
        random_rows.append({**rows[0], "method": f"random_{iteration:03d}", "macro_f1": f1,
                            "accuracy": acc, "k": len(subset),
                            "dimensions": sum(ngram_output_dim if ngram_block is not None and e == ngram_block.name
                                              else cache[e].shape[1] for e in subset),
                            "fit_seconds": seconds, "selected": "+".join(subset), "inner_f1": ""})
    append_rows(result_root / "nested_fold_results.csv", rows)
    append_rows(result_root / "random_subset_results.csv", random_rows)
    subset_record = {"dataset": dataset, "classifier": classifier, "seed": seed, "outer_fold": fold,
                     "run_mode": run_mode, "curet_direction": curet_direction,
                     "gfs": gfs, "history": history, "best_family": family_name,
                     "family_subset": family_subset, "family_history": family_history}
    with (result_root / "selected_subsets.jsonl").open("a") as handle:
        handle.write(json.dumps(subset_record) + "\n")
    checkpoint.write_text(json.dumps({"status": "complete", "key": key, "smoke": smoke}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--fold", type=int, choices=range(5), required=True)
    split_group = parser.add_mutually_exclusive_group()
    split_group.add_argument("--official-split", type=int, choices=range(1, 11),
                             help="use manifest split_N (DTD); fold is ignored")
    split_group.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"),
                             help="use one deterministic complementary CUReT half direction")
    parser.add_argument("--random-b", type=int, default=100)
    parser.add_argument("--max-k", type=int, default=8)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--n-jobs", type=int, default=2,
                        help="candidate scoring threads for SVM; ResMLP is forced to one")
    parser.add_argument("--svm-backend", choices=("cpu", "cuml"), default="cpu",
                        help="SVM implementation; cuml requires the GPU environment")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("results/confirmatory"))
    parser.add_argument("--embedding-root", type=Path, default=None,
                        help="isolated embedding root containing <dataset>/*.npy")
    parser.add_argument("--include-rgb-ngram", action="store_true",
                        help="add leakage-safe RGB Pixel N-gram + TruncatedSVD as descriptor 21")
    parser.add_argument("--ngram-components", type=int, default=256)
    parser.add_argument("--ngram-hash-bins", type=int, default=8192)
    args = parser.parse_args()
    if args.n_jobs < 1:
        parser.error("--n-jobs must be >= 1")
    if args.ngram_components < 1:
        parser.error("--ngram-components must be >= 1")
    if args.ngram_hash_bins < 2:
        parser.error("--ngram-hash-bins must be >= 2")
    if args.svm_backend == "cuml" and args.classifier != "svm":
        parser.error("--svm-backend cuml requires --classifier svm")
    if args.curet_direction is not None and args.dataset != "CUReT":
        parser.error("--curet-direction is only valid with --dataset CUReT")
    if args.dataset == "CUReT" and args.curet_direction is None:
        parser.error("--dataset CUReT requires --curet-direction")
    repo = args.repo.resolve()
    output = (repo / args.output).resolve() if not args.output.is_absolute() else args.output
    embedding_root = None
    if args.embedding_root is not None:
        embedding_root = ((repo / args.embedding_root).resolve()
                          if not args.embedding_root.is_absolute() else args.embedding_root)
    output.mkdir(parents=True, exist_ok=True)
    started = time.time()
    status, error = "running", None
    try:
        run_condition(repo, output, args.dataset, args.classifier, args.seed, args.fold,
                      args.random_b, args.max_k, args.smoke,
                      official_split=args.official_split,
                      curet_direction=args.curet_direction, n_jobs=args.n_jobs,
                      embedding_root=embedding_root, svm_backend=args.svm_backend,
                      include_rgb_ngram=args.include_rgb_ngram,
                      ngram_components=args.ngram_components,
                      ngram_hash_bins=args.ngram_hash_bins)
        status, error = "complete", None
    except KeyboardInterrupt:
        status, error = "interrupted", "KeyboardInterrupt()"
        raise
    except Exception as exc:
        status, error = "blocked" if "BLOCKED_DATA_LEAKAGE_RISK" in str(exc) else "failed", repr(exc)
        raise
    finally:
        record = {"dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
                  "fold": args.fold, "smoke": args.smoke, "status": status, "error": error,
                  "official_split": args.official_split,
                  "curet_direction": args.curet_direction,
                  "n_jobs": args.n_jobs,
                  "include_rgb_ngram": args.include_rgb_ngram,
                  "ngram_components": args.ngram_components,
                  "ngram_hash_bins": args.ngram_hash_bins,
                  "embedding_root": str(embedding_root) if embedding_root is not None else None,
                  "started_unix": started, "elapsed_seconds": time.time() - started,
                  "command": " ".join(sys.argv), "python": sys.version,
                  "platform": platform.platform(), "script_sha256": file_sha256(Path(__file__))}
        logs = output / ("ngram21/logs" if args.include_rgb_ngram else "logs")
        if args.svm_backend == "cuml":
            logs = output / "gpu_svm" / ("ngram21/logs" if args.include_rgb_ngram else "logs")
        logs.mkdir(parents=True, exist_ok=True)
        log_fold = (f"official{args.official_split}" if args.official_split
                    else args.curet_direction if args.curet_direction else str(args.fold))
        log_mode = "smoke" if args.smoke else "full"
        (logs / f"{args.dataset}__{args.classifier}__{args.seed}__{log_fold}__{log_mode}.json").write_text(
            json.dumps(record, indent=2)
        )


if __name__ == "__main__":
    main()
