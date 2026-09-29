#!/usr/bin/env python3
"""How far is greedy selection from the best subset of the same size?

GFS beats random subsets of equal size, but it reaches the maximum of only 100
random draws in a minority of conditions, which suggests it leaves performance
on the table.  This script measures that directly: for small budgets it
evaluates *every* subset of size k on the external test and reports where the
greedy choice lands in that exhaustive ranking.

IMPORTANT -- this is an upper bound, not a selection procedure.  Choosing the
best subset by its external score uses information the protocol forbids during
selection.  The oracle exists only to quantify the headroom a better
*training-time* criterion could hope to recover; it must never be reported as
an achievable result.

Results are appended incrementally so an interrupted run can resume.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from run_confirmatory_nested import (  # noqa: E402
    canonical_labels, fit_score_matrix, l2_rows, load_dataset, load_manifest,
    official_split_indices,
)

REPO = SRC.parent
FIELDS = ["dataset", "classifier", "seed", "split", "inverted", "k", "subset",
          "macro_f1", "accuracy", "dimensions", "fit_seconds"]


def load_embedding_dir(directory: Path) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Load blocks from an explicit directory, bypassing the dataset-name map.

    ``run_confirmatory_nested.load_dataset`` rewrites some dataset names before
    resolving the embedding folder, which prevents pointing it at a directory
    whose name differs from that mapping.  The validation performed here is the
    same one that function applies.
    """
    cache, reference = {}, None
    for path in sorted(directory.glob("*.npy")):
        if path.name.endswith("_labels.npy"):
            continue
        labels_path = directory / f"{path.stem}_labels.npy"
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
        raise ValueError(f"no valid embeddings in {directory}")
    return cache, reference


def done_keys(path: Path) -> set[tuple[str, str]]:
    """Subsets already evaluated, so an interrupted run resumes cheaply."""
    if not path.exists():
        return set()
    with path.open(newline="") as handle:
        return {(row["split"], row["subset"]) for row in csv.DictReader(handle)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), default="svm")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--official-splits", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--invert-official-split", action="store_true",
                        help="match the RADAM direction used by the manuscript")
    parser.add_argument("--k", type=int, nargs="+", default=[1, 2],
                        help="subset sizes to enumerate exhaustively")
    parser.add_argument("--embedding-root", type=Path, default=REPO / "embeddings_extensions")
    parser.add_argument("--embedding-dir", type=Path,
                        help="explicit block directory; overrides --embedding-root "
                             "and the dataset-name mapping")
    parser.add_argument("--results-root", type=Path,
                        default=REPO / "results/extensions/kth_tips2b",
                        help="directory holding data_audit.csv and sample_manifests/")
    parser.add_argument("--output", type=Path, default=REPO / "results/analysis/oracle_gap")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    destination = args.output / f"{args.dataset}_{args.classifier}_exhaustive.csv"
    already = done_keys(destination)

    if args.embedding_dir is not None:
        cache, y = load_embedding_dir(args.embedding_dir.resolve())
    else:
        cache, y = load_dataset(REPO, args.dataset,
                                embedding_root=args.embedding_root.resolve())
    groups, manifest_rows = load_manifest(args.results_root.resolve(), args.dataset, y)
    blocks = sorted(cache)
    print(f"{args.dataset}: {len(blocks)} bloques, {len(y)} muestras", flush=True)

    combos = [c for size in args.k for c in itertools.combinations(blocks, size)]
    print(f"subconjuntos por particion: {len(combos)}  "
          f"(k={args.k}); particiones: {args.official_splits}", flush=True)

    exists = destination.exists()
    with destination.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        for split in args.official_splits:
            train, test = official_split_indices(manifest_rows, split)
            if args.invert_official_split:
                train, test = test, train
            if set(groups[train]).intersection(groups[test]):
                raise AssertionError("source group leakage in outer split")
            tag = f"official{split}{'_inverted' if args.invert_official_split else ''}"
            started, evaluated = time.time(), 0
            for combo in combos:
                name = "+".join(combo)
                if (tag, name) in already:
                    continue
                matrix = np.concatenate([cache[b] for b in combo], axis=1)
                f1, acc, seconds = fit_score_matrix(
                    matrix, train, test, y, args.classifier, args.seed)
                writer.writerow({
                    "dataset": args.dataset, "classifier": args.classifier,
                    "seed": args.seed, "split": tag,
                    "inverted": int(args.invert_official_split),
                    "k": len(combo), "subset": name, "macro_f1": f1,
                    "accuracy": acc, "dimensions": int(matrix.shape[1]),
                    "fit_seconds": seconds,
                })
                evaluated += 1
                if evaluated % 25 == 0:
                    handle.flush()
                    rate = evaluated / max(time.time() - started, 1e-9)
                    remaining = (len(combos) - evaluated) / max(rate, 1e-9)
                    print(f"  {tag}: {evaluated}/{len(combos)} "
                          f"({rate:.1f}/s, faltan ~{remaining/60:.0f} min)", flush=True)
            handle.flush()
            print(f"  {tag}: completo ({time.time() - started:.0f}s)", flush=True)
    print(f"escrito en {destination}")


if __name__ == "__main__":
    main()
