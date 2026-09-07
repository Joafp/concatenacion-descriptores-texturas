#!/usr/bin/env python3
"""Controlled RGB Pixel N-gram fusion experiment on official Outex_TC_00013."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy import sparse
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import normalize
from sklearn.svm import SVC

PUBLISHED_ACCURACY = {"rgb_ngram_impl1": 0.963, "rgb_ngram_impl2": 0.953}
MAX_ADDED = 3
MIN_IMPROVEMENT = 0.001
IMPLEMENTATIONS = {
    "rgb_ngram_impl1": {"range": 12, "height": 2, "joint_channels": True},
    "rgb_ngram_impl2": {"range": 11, "height": 4, "joint_channels": False},
}


def encoded_ngrams(image: np.ndarray, implementation: str) -> np.ndarray:
    """Return integer-coded vertical RGB Pixel N-grams for one image."""
    if implementation not in IMPLEMENTATIONS:
        raise KeyError(implementation)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("expected HxWx3 RGB image")
    config = IMPLEMENTATIONS[implementation]
    height = int(config["height"])
    if image.shape[0] < height:
        raise ValueError("image is smaller than the requested window")
    value_range = int(config["range"])
    alphabet = int(np.ceil(256 / value_range))
    quantized = image.astype(np.uint16) // value_range
    if bool(config["joint_channels"]):
        code = np.zeros((image.shape[0] - height + 1, image.shape[1]), dtype=np.uint64)
        for channel in range(3):
            for offset in range(height):
                code = code * alphabet + quantized[offset : offset + code.shape[0], :, channel]
        return code.reshape(-1)
    channel_codes = []
    channel_span = alphabet**height
    for channel in range(3):
        code = np.zeros((image.shape[0] - height + 1, image.shape[1]), dtype=np.uint64)
        for offset in range(height):
            code = code * alphabet + quantized[offset : offset + code.shape[0], :, channel]
        channel_codes.append(code.reshape(-1) + channel * channel_span)
    return np.concatenate(channel_codes)


def count_image(image: np.ndarray, implementation: str) -> tuple[np.ndarray, np.ndarray]:
    keys, counts = np.unique(encoded_ngrams(image, implementation), return_counts=True)
    return keys.astype(np.uint64), counts.astype(np.uint32)


def load_count_cache(output: Path, implementation: str) -> dict[str, np.ndarray]:
    root = output / "count_cache" / implementation
    return {
        "keys": np.load(root / "keys.npy", mmap_mode="r"),
        "counts": np.load(root / "counts.npy", mmap_mode="r"),
        "indptr": np.load(root / "indptr.npy", mmap_mode="r"),
    }


def training_vocabulary(cache: dict[str, np.ndarray], train: np.ndarray) -> np.ndarray:
    parts = []
    indptr = cache["indptr"]
    for row in train:
        parts.append(np.asarray(cache["keys"][indptr[row] : indptr[row + 1]]))
    return np.unique(np.concatenate(parts))


def matrix_from_vocabulary(
    cache: dict[str, np.ndarray], vocabulary: np.ndarray
) -> sparse.csr_matrix:
    return normalize(raw_matrix_from_vocabulary(cache, vocabulary), norm="l2", axis=1, copy=False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"row_id", "path", "label", "official_split", "source_sha256"}
    if len(rows) != 1360 or not required.issubset(rows[0]):
        raise ValueError("official Outex manifest is invalid")
    if [int(row["row_id"]) for row in rows] != list(range(1360)):
        raise ValueError("manifest order is not canonical")
    counts = pd.DataFrame(rows).groupby(["label", "official_split"]).size()
    if len(counts) != 136 or not (counts == 10).all():
        raise ValueError("official split must contain 10 train and 10 test images per class")
    for row in rows:
        path_value = Path(row["path"])
        if not path_value.is_file() or sha256(path_value) != row["source_sha256"]:
            raise ValueError(f"manifest integrity failure: {path_value}")
    return rows


def extract_counts(rows: list[dict[str, str]], output: Path) -> None:
    for implementation in IMPLEMENTATIONS:
        destination = output / "count_cache" / implementation
        required = [destination / name for name in ("keys.npy", "counts.npy", "indptr.npy")]
        if all(path.exists() for path in required):
            cache = load_count_cache(output, implementation)
            if len(cache["indptr"]) == len(rows) + 1:
                print(f"RESUME count cache {implementation}")
                continue
        counts = []
        started = time.time()
        for index, row in enumerate(rows):
            with Image.open(row["path"]) as image:
                rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
            counts.append(count_image(rgb, implementation))
            if (index + 1) % 200 == 0 or index + 1 == len(rows):
                print(f"{implementation}: {index + 1}/{len(rows)}")
        destination.mkdir(parents=True, exist_ok=True)
        keys = [row[0] for row in counts]
        values = [row[1] for row in counts]
        indptr = np.concatenate(
            (np.asarray([0], dtype=np.int64), np.cumsum([len(row) for row in keys], dtype=np.int64))
        )
        np.save(destination / "keys.npy", np.concatenate(keys))
        np.save(destination / "counts.npy", np.concatenate(values))
        np.save(destination / "indptr.npy", indptr)
        (destination / "metadata.json").write_text(
            json.dumps(
                {
                    "implementation": implementation,
                    "config": IMPLEMENTATIONS[implementation],
                    "samples": len(rows),
                    "source": "Paiva Pavon et al. (2023), doi:10.1016/j.image.2023.117028",
                },
                indent=2,
            )
            + "\n"
        )
        print(f"saved {implementation} in {time.time() - started:.1f}s")


def raw_matrix_from_vocabulary(
    cache: dict[str, np.ndarray], vocabulary: np.ndarray
) -> sparse.csr_matrix:
    indptr_source = cache["indptr"]
    row_indptr = [0]
    columns: list[np.ndarray] = []
    values: list[np.ndarray] = []
    for row in range(len(indptr_source) - 1):
        start, end = int(indptr_source[row]), int(indptr_source[row + 1])
        keys = np.asarray(cache["keys"][start:end])
        counts = np.asarray(cache["counts"][start:end], dtype=np.float32)
        positions = np.searchsorted(vocabulary, keys)
        in_bounds = positions < len(vocabulary)
        matched = np.zeros(len(keys), dtype=bool)
        matched[in_bounds] = vocabulary[positions[in_bounds]] == keys[in_bounds]
        columns.append(positions[matched].astype(np.int32))
        values.append(counts[matched])
        row_indptr.append(row_indptr[-1] + int(matched.sum()))
    return sparse.csr_matrix(
        (np.concatenate(values), np.concatenate(columns), np.asarray(row_indptr, dtype=np.int64)),
        shape=(len(indptr_source) - 1, len(vocabulary)),
        dtype=np.float32,
    )


def load_blocks(
    output: Path, embeddings: Path, labels: np.ndarray, train: np.ndarray
) -> tuple[dict[str, sparse.csr_matrix], dict[str, sparse.csr_matrix], dict[str, int]]:
    raw: dict[str, sparse.csr_matrix] = {}
    normalized_blocks: dict[str, sparse.csr_matrix] = {}
    vocab_sizes: dict[str, int] = {}
    for implementation in IMPLEMENTATIONS:
        cache = load_count_cache(output, implementation)
        vocabulary = training_vocabulary(cache, train)
        raw[implementation] = raw_matrix_from_vocabulary(cache, vocabulary)
        normalized_blocks[implementation] = normalize(raw[implementation], norm="l2", axis=1, copy=True)
        vocab_sizes[implementation] = len(vocabulary)
    for path in sorted(embeddings.glob("*.npy")):
        if path.name.endswith("_labels.npy"):
            continue
        labels_path = embeddings / f"{path.stem}_labels.npy"
        if not labels_path.exists() or not np.array_equal(np.load(labels_path), labels):
            raise ValueError(f"embedding label mismatch: {path.stem}")
        values = np.asarray(np.load(path, mmap_mode="r"), dtype=np.float32)
        normalized_blocks[path.stem] = sparse.csr_matrix(
            normalize(values, norm="l2", axis=1, copy=False)
        )
    if len(normalized_blocks) != 22:
        raise ValueError(f"expected two n-grams and twenty dense blocks, got {len(normalized_blocks)}")
    return raw, normalized_blocks, vocab_sizes


def concatenate(
    blocks: dict[str, sparse.csr_matrix], subset: tuple[str, ...]
) -> sparse.csr_matrix:
    return sparse.hstack([blocks[name] for name in subset], format="csr", dtype=np.float32)


def make_classifier() -> SVC:
    # This reproduces Table 4 of Paiva Pavon et al. exactly (0.963/0.953 on Outex13).
    # Their parameter-tuning subsection instead names OneVsRestClassifier, which
    # reproduces the distinct 0.954/0.941 values reported in that subsection.
    return SVC(C=1.0, kernel="linear")


def predict(
    blocks: dict[str, sparse.csr_matrix],
    subset: tuple[str, ...],
    train: np.ndarray,
    test: np.ndarray,
    labels: np.ndarray,
) -> tuple[float, float, float, np.ndarray]:
    matrix = concatenate(blocks, subset)
    model = make_classifier()
    started = time.perf_counter()
    model.fit(matrix[train], labels[train])
    prediction = model.predict(matrix[test])
    return (
        float(f1_score(labels[test], prediction, average="macro")),
        float(accuracy_score(labels[test], prediction)),
        time.perf_counter() - started,
        prediction,
    )


def internal_accuracy(
    blocks: dict[str, sparse.csr_matrix],
    subset: tuple[str, ...],
    outer_train: np.ndarray,
    labels: np.ndarray,
) -> float:
    splitter = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)
    scores = []
    for train_position, validation_position in splitter.split(outer_train, labels[outer_train]):
        train = outer_train[train_position]
        validation = outer_train[validation_position]
        _, accuracy, _, _ = predict(blocks, subset, train, validation, labels)
        scores.append(accuracy)
    return float(np.mean(scores))


def select_blocks(
    blocks: dict[str, sparse.csr_matrix], train: np.ndarray, labels: np.ndarray
) -> tuple[tuple[str, ...], float, tuple[str, ...], list[dict[str, object]], dict[str, float]]:
    ngram_scores = {
        name: internal_accuracy(blocks, (name,), train, labels) for name in IMPLEMENTATIONS
    }
    selected = (max(ngram_scores, key=lambda name: (ngram_scores[name], name)),)
    dense_names = sorted(set(blocks) - set(IMPLEMENTATIONS))
    direct_scores = {name: internal_accuracy(blocks, (name,), train, labels) for name in dense_names}
    best_direct = (max(direct_scores, key=lambda name: (direct_scores[name], name)),)
    best_subset = selected
    best_historical = ngram_scores[selected[0]]
    previous = best_historical
    consecutive_small = 0
    history: list[dict[str, object]] = [
        {"step": 0, "selected": list(selected), "inner_accuracy": best_historical}
    ]
    for step in range(1, MAX_ADDED + 1):
        options = []
        for candidate in dense_names:
            if candidate in selected:
                continue
            subset = selected + (candidate,)
            score = internal_accuracy(blocks, subset, train, labels)
            options.append((score, candidate, subset))
        score, candidate, selected = max(options, key=lambda item: (item[0], item[1]))
        history.append(
            {"step": step, "added": candidate, "selected": list(selected), "inner_accuracy": score}
        )
        if score > best_historical:
            best_historical = score
            best_subset = selected
        consecutive_small = consecutive_small + 1 if score - previous < MIN_IMPROVEMENT else 0
        previous = score
        if consecutive_small >= 2:
            break
    scores = {**{f"ngram:{key}": value for key, value in ngram_scores.items()}, **direct_scores}
    return best_subset, best_historical, best_direct, history, scores


def paired_bootstrap(
    truth: np.ndarray, baseline: np.ndarray, proposed: np.ndarray, repetitions: int = 20_000
) -> dict[str, float]:
    rng = np.random.default_rng(42)
    by_class = [np.flatnonzero(truth == label) for label in np.unique(truth)]
    deltas = np.empty(repetitions, dtype=np.float64)
    for repetition in range(repetitions):
        sample = np.concatenate([rng.choice(indices, size=len(indices), replace=True) for indices in by_class])
        deltas[repetition] = np.mean(proposed[sample] == truth[sample]) - np.mean(
            baseline[sample] == truth[sample]
        )
    return {
        "delta_accuracy": float(np.mean(proposed == truth) - np.mean(baseline == truth)),
        "bootstrap_ci95_low": float(np.quantile(deltas, 0.025)),
        "bootstrap_ci95_high": float(np.quantile(deltas, 0.975)),
        "bootstrap_repetitions": repetitions,
    }


def analyze_predictions(output: Path) -> pd.DataFrame:
    archive = np.load(output / "official_predictions.npz", allow_pickle=False)
    truth = archive["truth"]
    pairs = [
        ("rgb_ngram_full_concat", "published_reproduction_impl1_raw"),
        ("rgb_ngram_gfs", "published_reproduction_impl1_raw"),
        ("rgb_ngram_gfs", "rgb_ngram_selected_l2"),
        ("rgb_ngram_full_concat", "best_direct_descriptor"),
        ("rgb_ngram_full_concat", "rgb_ngram_gfs"),
    ]
    rows = []
    for proposed_name, baseline_name in pairs:
        proposed = archive[proposed_name]
        baseline = archive[baseline_name]
        proposed_correct = proposed == truth
        baseline_correct = baseline == truth
        wins = int(np.sum(proposed_correct & ~baseline_correct))
        losses = int(np.sum(~proposed_correct & baseline_correct))
        comparison = paired_bootstrap(truth, baseline, proposed)
        discordant = wins + losses
        comparison.update(
            {
                "proposed": proposed_name,
                "baseline": baseline_name,
                "proposed_correct": int(proposed_correct.sum()),
                "baseline_correct": int(baseline_correct.sum()),
                "paired_wins": wins,
                "paired_losses": losses,
                "mcnemar_exact_two_sided_p": float(
                    binomtest(wins, discordant, 0.5).pvalue if discordant else 1.0
                ),
            }
        )
        rows.append(comparison)
    frame = pd.DataFrame(rows)
    frame.to_csv(output / "paired_comparisons.csv", index=False)
    print(frame.to_string(index=False))
    return frame


def validate_outputs(repo: Path, output: Path) -> dict[str, object]:
    manifest = repo / "results/extensions/outex13_official1360/sample_manifests/Outex13Official1360.csv"
    embeddings = repo / "embeddings_extensions/Outex13Official1360"
    rows = read_manifest(manifest)
    labels = np.asarray([int(row["label"]) for row in rows], dtype=np.int64)
    train = np.flatnonzero(np.asarray([row["official_split"] == "train" for row in rows]))
    test = np.flatnonzero(np.asarray([row["official_split"] == "test" for row in rows]))
    raw, blocks, _ = load_blocks(output, embeddings, labels, train)
    saved = np.load(output / "official_predictions.npz", allow_pickle=False)
    checks = {}
    validation_methods = [
        (
            "published_reproduction_impl1_raw",
            raw,
            ("rgb_ngram_impl1",),
        ),
        (
            "rgb_ngram_full_concat",
            blocks,
            ("rgb_ngram_impl1",) + tuple(sorted(set(blocks) - set(IMPLEMENTATIONS))),
        ),
    ]
    for method, source_blocks, subset in validation_methods:
        _, _, _, repeated = predict(source_blocks, subset, train, test, labels)
        checks[method] = {
            "identical_predictions": bool(np.array_equal(repeated, saved[method])),
            "prediction_sha256": hashlib.sha256(repeated.tobytes()).hexdigest(),
        }
        if not checks[method]["identical_predictions"]:
            raise AssertionError(f"non-deterministic predictions: {method}")
    results = pd.read_csv(output / "official_results.csv")
    if len(results) != 6 or results["method"].duplicated().any():
        raise ValueError("official results must contain six unique methods")
    if not np.isfinite(results[["macro_f1", "accuracy", "fit_seconds"]].to_numpy()).all():
        raise ValueError("official results contain non-finite required metrics")
    if not results[["macro_f1", "accuracy"]].apply(lambda column: column.between(0, 1).all()).all():
        raise ValueError("metric outside [0,1]")
    report = {
        "status": "pass",
        "manifest_sha256": sha256(manifest),
        "result_rows": len(results),
        "unique_methods": int(results["method"].nunique()),
        "determinism_checks": checks,
    }
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report


def run(repo: Path, output: Path, baseline_only: bool = False) -> None:
    manifest = repo / "results/extensions/outex13_official1360/sample_manifests/Outex13Official1360.csv"
    embeddings = repo / "embeddings_extensions/Outex13Official1360"
    rows = read_manifest(manifest)
    labels = np.asarray([int(row["label"]) for row in rows], dtype=np.int64)
    train = np.flatnonzero(np.asarray([row["official_split"] == "train" for row in rows]))
    test = np.flatnonzero(np.asarray([row["official_split"] == "test" for row in rows]))
    extract_counts(rows, output)
    raw, blocks, vocab_sizes = load_blocks(output, embeddings, labels, train)
    if baseline_only:
        baseline_rows = []
        for implementation in IMPLEMENTATIONS:
            macro_f1, accuracy, seconds, _ = predict(
                raw, (implementation,), train, test, labels
            )
            baseline_rows.append(
                {
                    "method": implementation,
                    "published_accuracy": PUBLISHED_ACCURACY[implementation],
                    "reproduced_accuracy": accuracy,
                    "reproduced_macro_f1": macro_f1,
                    "difference": accuracy - PUBLISHED_ACCURACY[implementation],
                    "fit_seconds": seconds,
                    "vocabulary_size": vocab_sizes[implementation],
                }
            )
            print(
                f"{implementation}: reproduced={accuracy:.6f}, "
                f"published={PUBLISHED_ACCURACY[implementation]:.6f}"
            )
        output.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(baseline_rows).to_csv(output / "baseline_reproduction.csv", index=False)
        return
    selected, selected_inner, best_direct, history, inner_scores = select_blocks(blocks, train, labels)
    selected_ngram = (selected[0],)
    dense_names = tuple(sorted(set(blocks) - set(IMPLEMENTATIONS)))
    methods: list[tuple[str, tuple[str, ...], dict[str, sparse.csr_matrix], float]] = [
        (
            "published_reproduction_impl1_raw",
            ("rgb_ngram_impl1",),
            raw,
            float("nan"),
        ),
        (
            "published_reproduction_impl2_raw",
            ("rgb_ngram_impl2",),
            raw,
            float("nan"),
        ),
        ("rgb_ngram_selected_l2", selected_ngram, blocks, inner_scores[f"ngram:{selected_ngram[0]}"]),
        ("best_direct_descriptor", best_direct, blocks, inner_scores[best_direct[0]]),
        ("rgb_ngram_gfs", selected, blocks, selected_inner),
        ("rgb_ngram_full_concat", selected_ngram + dense_names, blocks, float("nan")),
    ]
    result_rows = []
    predictions: dict[str, np.ndarray] = {}
    for method, subset, source_blocks, inner in methods:
        macro_f1, accuracy, seconds, prediction = predict(
            source_blocks, subset, train, test, labels
        )
        predictions[method] = prediction
        result_rows.append(
            {
                "dataset": "Outex_TC_00013_official",
                "train_n": len(train),
                "test_n": len(test),
                "method": method,
                "macro_f1": macro_f1,
                "accuracy": accuracy,
                "inner_accuracy": inner,
                "k": len(subset),
                "selected": "+".join(subset),
                "fit_seconds": seconds,
                "vocab_impl1": vocab_sizes["rgb_ngram_impl1"],
                "vocab_impl2": vocab_sizes["rgb_ngram_impl2"],
            }
        )
        print(f"{method}: accuracy={accuracy:.6f}, macro_f1={macro_f1:.6f}, subset={subset}")
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(result_rows).to_csv(output / "official_results.csv", index=False)
    np.savez_compressed(output / "official_predictions.npz", truth=labels[test], **predictions)
    comparison = paired_bootstrap(
        labels[test], predictions["rgb_ngram_selected_l2"], predictions["rgb_ngram_gfs"]
    )
    comparison.update(
        {
            "baseline": "rgb_ngram_selected_l2",
            "proposed": "rgb_ngram_gfs",
            "published_accuracy_impl1": PUBLISHED_ACCURACY["rgb_ngram_impl1"],
            "published_accuracy_impl2": PUBLISHED_ACCURACY["rgb_ngram_impl2"],
        }
    )
    (output / "selection_history.json").write_text(json.dumps(history, indent=2) + "\n")
    (output / "inner_scores.json").write_text(json.dumps(inner_scores, indent=2, sort_keys=True) + "\n")
    (output / "paired_bootstrap.json").write_text(json.dumps(comparison, indent=2) + "\n")
    provenance = {
        "manifest": str(manifest.resolve()),
        "manifest_sha256": sha256(manifest),
        "classifier": "SVC(C=1.0, kernel=linear)",
        "selection_metric": "inner_accuracy",
        "inner_folds": 4,
        "inner_seed": 42,
        "max_added_blocks": MAX_ADDED,
        "minimum_improvement": MIN_IMPROVEMENT,
    }
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    analyze_predictions(output)
    print(json.dumps(comparison, indent=2))


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument(
        "--output", type=Path, default=repo / "results/extensions/rgb_pixel_ngrams_outex13_official"
    )
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_outputs(args.repo.resolve(), args.output.resolve())
    elif args.analyze_only:
        analyze_predictions(args.output.resolve())
    else:
        run(args.repo.resolve(), args.output.resolve(), args.baseline_only)


if __name__ == "__main__":
    main()
