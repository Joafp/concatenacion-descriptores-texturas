#!/usr/bin/env python3
"""Count how many candidates tie at the top of the inner selection criterion.

``run_confirmatory_nested.greedy`` resolves ties with
``max(scored, key=lambda item: (item[0], item[1]))``: when several candidates
reach the same inner macro-F1 it keeps the one whose *name* sorts last.  That
is deterministic but semantically arbitrary, so whenever the criterion
saturates the reported selection reflects alphabetical order rather than
evidence.  This script recomputes the first GFS step for a condition and
reports the size of the tied set.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from run_confirmatory_nested import (  # noqa: E402
    inner_score, load_manifest, official_split_indices,
)
from analyze_oracle_gap import load_embedding_dir  # noqa: E402

REPO = SRC.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="KTHTIPS2b")
    parser.add_argument("--classifier", choices=("svm", "resmlp"), default="svm")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--official-splits", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--invert-official-split", action="store_true")
    parser.add_argument("--embedding-dir", type=Path,
                        default=REPO / "embeddings_extensions/KTHTIPS2b")
    parser.add_argument("--results-root", type=Path,
                        default=REPO / "results/extensions/kth_tips2b")
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/analysis/tie_breaking")
    args = parser.parse_args()

    cache, y = load_embedding_dir(args.embedding_dir.resolve())
    groups, manifest_rows = load_manifest(args.results_root.resolve(), args.dataset, y)
    blocks = sorted(cache)

    records = []
    for split in args.official_splits:
        train, test = official_split_indices(manifest_rows, split)
        if args.invert_official_split:
            train, test = test, train
        scores = {b: inner_score(cache, [b], train, y, groups, args.classifier, args.seed)
                  for b in blocks}
        best = max(scores.values())
        tied = sorted(b for b, s in scores.items() if s >= best - 1e-12)
        # Reproduce the runner's tie-break: highest score, then last name.
        picked = max(((s, b) for b, s in scores.items()), key=lambda item: item)[1]
        records.append({
            "split": split, "inner_best": best, "n_tied_at_top": len(tied),
            "tied": tied, "picked_by_runner": picked,
            "picked_is_alphabetically_last_of_tied": picked == tied[-1],
            "all_scores": {b: round(s, 6) for b, s in sorted(scores.items())},
        })
        print(f"particion {split}: mejor inner-F1 = {best:.6f}; "
              f"{len(tied)} de {len(blocks)} bloques empatados en el maximo")
        if len(tied) > 1:
            print(f"   empatados: {', '.join(tied)}")
            print(f"   el runner elige: {picked}  "
                  f"(= ultimo alfabetico: {picked == tied[-1]})")
        else:
            print(f"   unico ganador: {tied[0]}")

    args.output.mkdir(parents=True, exist_ok=True)
    name = f"{args.dataset}_{args.classifier}"
    if args.invert_official_split:
        name += "_inverted"
    (args.output / f"{name}.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ties = [r["n_tied_at_top"] for r in records]
    print(f"\nempate medio en el primer paso: {np.mean(ties):.2f} candidatos")
    print(f"escrito en {args.output / (name + '.json')}")


if __name__ == "__main__":
    main()
