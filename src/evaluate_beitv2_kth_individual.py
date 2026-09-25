#!/usr/bin/env python3
"""Controlled KTH-TIPS2-b evaluation of the two frozen BEiTv2 descriptors."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

from run_confirmatory_nested import (
    RESULT_FIELDS, audit_gate, fit_score, fit_score_foldaware, load_dataset, load_manifest,
    official_split_indices,
)
from rgb_ngram_descriptor import RGBNgramSVDBlock, build_count_cache


DESCRIPTORS = ("beitv2_base_final", "beitv2_base_multilayer")


def append_unique(path: Path, rows: list[dict]) -> None:
    existing = set()
    if path.exists():
        with path.open(newline="") as handle:
            existing = {(r["classifier"], r["outer_fold"], r["method"])
                        for r in csv.DictReader(handle)}
    pending = [r for r in rows if (r["classifier"], r["outer_fold"], r["method"]) not in existing]
    if not pending:
        return
    with path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        if not existing:
            writer.writeheader()
        writer.writerows(pending)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--mode", choices=("individual", "full_plus_beitv2"), default="individual")
    parser.add_argument("--invert-official-split", action="store_true",
                        help="RADAM protocol: three physical samples train and one tests")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--embedding-root", type=Path, default=Path("embeddings_extensions"))
    parser.add_argument("--output", type=Path, default=Path("results/extensions/kth_tips2b"))
    parser.add_argument("--image-root", type=Path,
                        default=Path("results/confirmatory/recovery/kth/staging/KTH-TIPS2-b"))
    args = parser.parse_args()
    repo = args.repo.resolve()
    embedding_root = args.embedding_root if args.embedding_root.is_absolute() else repo / args.embedding_root
    output = args.output if args.output.is_absolute() else repo / args.output
    image_root = args.image_root if args.image_root.is_absolute() else repo / args.image_root
    audit_gate(output, "KTHTIPS2b")
    cache, y = load_dataset(repo, "KTH-TIPS2-b", embedding_root)
    missing = set(DESCRIPTORS).difference(cache)
    if missing:
        raise FileNotFoundError(f"missing BEiTv2 embeddings: {sorted(missing)}")
    groups, rows = load_manifest(output, "KTHTIPS2b", y)
    result_dir = "beitv2_individual" if args.mode == "individual" else "beitv2_full_concat"
    if args.invert_official_split:
        result_dir += "_radam_3train"
    destination = output / result_dir / "nested_fold_results.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    completed = []
    base_descriptors = sorted(name for name in cache if name not in DESCRIPTORS)
    if args.mode == "full_plus_beitv2":
        # The audited manifest retains its original release-relative paths;
        # the verified recovery is staged elsewhere. Rebase only the path used
        # for label-free count extraction, and check its recorded content hash.
        ngram_rows = []
        prefix = "data/KTH-TIPS2-b/"
        for row in rows:
            value = row.get("source_path") or row.get("path") or ""
            if not value.startswith(prefix):
                raise ValueError(f"unexpected KTH source path: {value}")
            rebased = image_root / value.removeprefix(prefix)
            if not rebased.is_file():
                raise FileNotFoundError(rebased)
            expected = row.get("source_sha256") or row.get("sha256")
            if expected and hashlib.sha256(rebased.read_bytes()).hexdigest() != expected:
                raise ValueError(f"recovered image hash mismatch: {rebased}")
            ngram_rows.append({**row, "source_path": str(rebased)})
        count_dir = output / result_dir / "rgb_ngram_count_cache" / "KTHTIPS2b" / "rgb_ngram_impl1"
        counts = build_count_cache(ngram_rows, repo, count_dir, "rgb_ngram_impl1")
        ngram_block = RGBNgramSVDBlock(counts, n_components=256, random_state=42, hash_bins=8192)
    else:
        ngram_block = None
    for split in range(1, 5):
        train, test = official_split_indices(rows, split)
        if args.invert_official_split:
            train, test = test, train
        if set(groups[train]).intersection(groups[test]):
            raise AssertionError(f"source-group overlap in official split {split}")
        variants = DESCRIPTORS if args.mode == "individual" else DESCRIPTORS
        for descriptor in variants:
            if args.mode == "individual":
                selected = [descriptor]
                f1, accuracy, seconds = fit_score(cache, selected, train, test, y, args.classifier, 42)
                method = descriptor
            else:
                selected = base_descriptors + [descriptor, ngram_block.name]
                f1, accuracy, seconds = fit_score_foldaware(
                    cache, selected, train, test, y, args.classifier, 42, ngram_block=ngram_block
                )
                method = f"full21_plus_{descriptor}"
            dimensions = (
                cache[descriptor].shape[1] if args.mode == "individual" else
                sum(256 if name == ngram_block.name else cache[name].shape[1] for name in selected)
            )
            completed.append({
                "dataset": "KTHTIPS2b", "classifier": args.classifier, "seed": 42,
                "outer_fold": split - 1, "run_mode": "full", "method": method,
                "macro_f1": f1, "accuracy": accuracy, "k": 1,
                "dimensions": dimensions,
                "selected": "+".join(selected), "inner_f1": "",
            })
            print(f"split={split} {args.classifier} {method} macro_f1={f1:.6f} accuracy={accuracy:.6f}", flush=True)
    append_unique(destination, completed)


if __name__ == "__main__":
    main()
