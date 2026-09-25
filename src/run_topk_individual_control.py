"""Control anidado: concatenar los k mejores descriptores individuales.

El ranking y k se determinan sin consultar el test externo. k se toma del GFS
ya archivado para la misma condición; cada singleton se puntúa en los cuatro
folds internos y los k primeros se concatenan para una única evaluación externa.
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from run_confirmatory_nested import (
    append_rows,
    audit_gate,
    curet_half_indices,
    fit_score_foldaware,
    inner_score,
    load_dataset,
    load_manifest,
    official_split_indices,
)


def outer_indices(dataset, seed, fold, y, groups, manifest_rows,
                  official_split=None, curet_direction=None,
                  invert_official_split=False):
    if official_split is not None:
        train, test = official_split_indices(manifest_rows, official_split)
        return (test, train) if invert_official_split else (train, test)
    if curet_direction is not None:
        return curet_half_indices(manifest_rows, curet_direction)
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    return list(splitter.split(np.zeros(len(y)), y, groups))[fold]


def archived_k(output, dataset, classifier, seed, fold, svm_backend="cpu",
               include_rgb_ngram=False, ngram_result_subdir="ngram21"):
    if svm_backend == "cuml":
        source = output / "gpu_svm" / (f"{ngram_result_subdir}/nested_fold_results.csv"
                                        if include_rgb_ngram else "nested_fold_results.csv")
    else:
        source = output / (f"{ngram_result_subdir}/nested_fold_results.csv"
                           if include_rgb_ngram else "nested_fold_results.csv")
    rows = pd.read_csv(source)
    match = rows[
        (rows["dataset"] == dataset)
        & (rows["classifier"] == classifier)
        & (rows["seed"] == seed)
        & (rows["outer_fold"] == fold)
        & (rows["method"] == "gfs")
        & (rows["run_mode"] == "full")
    ]
    if len(match) != 1:
        raise ValueError(f"expected one archived GFS row, found {len(match)}")
    return int(match.iloc[0]["k"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--fold", type=int, choices=range(5), required=True)
    split = parser.add_mutually_exclusive_group()
    split.add_argument("--official-split", type=int, choices=range(1, 11))
    split.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--n-jobs", type=int, default=2)
    parser.add_argument("--svm-backend", choices=("cpu", "cuml"), default="cpu")
    parser.add_argument("--include-rgb-ngram", action="store_true")
    parser.add_argument("--ngram-components", type=int, default=256)
    parser.add_argument("--ngram-hash-bins", type=int, default=8192)
    parser.add_argument("--ngram-result-subdir", default="ngram21")
    parser.add_argument("--invert-official-split", action="store_true")
    parser.add_argument("--exclude-extractors", nargs="*", default=[])
    args = parser.parse_args()
    if args.svm_backend == "cuml" and args.classifier != "svm":
        parser.error("--svm-backend cuml requires --classifier svm")

    repo = args.repo.resolve()
    output = (repo / args.output).resolve() if not args.output.is_absolute() else args.output
    embedding_root = args.embedding_root
    if embedding_root is not None and not embedding_root.is_absolute():
        embedding_root = (repo / embedding_root).resolve()

    audit_gate(output, args.dataset)
    cache, y = load_dataset(repo, args.dataset, embedding_root=embedding_root)
    unknown_exclusions = sorted(set(args.exclude_extractors).difference(cache))
    if unknown_exclusions:
        raise ValueError(f"cannot exclude missing extractors: {unknown_exclusions}")
    for name in args.exclude_extractors:
        cache.pop(name)
    groups, manifest_rows = load_manifest(output, args.dataset, y)
    ngram_block = None
    if args.include_rgb_ngram:
        from rgb_ngram_descriptor import RGBNgramSVDBlock, build_count_cache
        count_dir = output / args.ngram_result_subdir / "rgb_ngram_count_cache" / args.dataset / "rgb_ngram_impl1"
        counts = build_count_cache(manifest_rows, repo, count_dir, "rgb_ngram_impl1")
        ngram_block = RGBNgramSVDBlock(
            counts, n_components=args.ngram_components,
            random_state=args.seed, hash_bins=args.ngram_hash_bins,
        )
    train, test = outer_indices(
        args.dataset, args.seed, args.fold, y, groups, manifest_rows,
        args.official_split, args.curet_direction, args.invert_official_split,
    )
    fold = (
        args.official_split - 1 if args.official_split is not None
        else {"a_to_b": 0, "b_to_a": 1}[args.curet_direction]
        if args.curet_direction is not None else args.fold
    )
    if set(groups[train]).intersection(groups[test]):
        raise AssertionError("source group leakage in outer split")

    if args.svm_backend == "cuml":
        control = output / "gpu_svm" / (f"{args.ngram_result_subdir}/topk_individual_control"
                                         if args.include_rgb_ngram
                                         else "topk_individual_control")
    else:
        control = output / (f"{args.ngram_result_subdir}/topk_individual_control"
                            if args.include_rgb_ngram else "topk_individual_control")
    control.mkdir(parents=True, exist_ok=True)
    key = f"{args.dataset}__{args.classifier}__{args.seed}__{fold}"
    checkpoint = control / f"{key}.json"
    if checkpoint.exists():
        print(f"RESUME skip completed {key}")
        return

    k = archived_k(output, args.dataset, args.classifier, args.seed, fold,
                   args.svm_backend, args.include_rgb_ngram, args.ngram_result_subdir)
    names = sorted(cache)
    if ngram_block is not None:
        names.append(ngram_block.name)
    def score_one(name):
        return (
            inner_score(cache, [name], train, y, groups, args.classifier, args.seed,
                        svm_backend=args.svm_backend, ngram_block=ngram_block),
            name,
        )
    if args.classifier == "svm" and args.svm_backend == "cpu" and args.n_jobs > 1:
        with ThreadPoolExecutor(max_workers=args.n_jobs) as pool:
            ranked = sorted(pool.map(score_one, names))
    else:
        ranked = sorted(score_one(name) for name in names)
    selected = [name for _, name in ranked[-k:]][::-1]
    mean_inner = float(np.mean([score for score, _ in ranked[-k:]]))
    f1, accuracy, seconds = fit_score_foldaware(
        cache, selected, train, test, y, args.classifier, args.seed,
        args.svm_backend, ngram_block
    )
    ngram_output_dim = min(args.ngram_components, len(train) - 1,
                           args.ngram_hash_bins - 1)
    row = {
        "dataset": args.dataset,
        "classifier": args.classifier,
        "seed": args.seed,
        "outer_fold": fold,
        "run_mode": "full",
        "method": "topk_individual",
        "macro_f1": f1,
        "accuracy": accuracy,
        "k": k,
        "dimensions": sum(ngram_output_dim if ngram_block is not None and name == ngram_block.name
                          else cache[name].shape[1] for name in selected),
        "fit_seconds": seconds,
        "selected": "+".join(selected),
        "inner_f1": mean_inner,
    }
    append_rows(control / "nested_fold_results.csv", [row])
    checkpoint.write_text(json.dumps({"status": "complete", **row}, indent=2))
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
