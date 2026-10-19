"""Rank descriptor blocks by individual inner score, once per condition.

The size sweep, its inner-criterion twin, the rank lottery and the diversity
sampling all start from the same ranking: every block scored alone on the inner
folds of the outer training partition.  Computing it four times per condition
costs 84 fits each time with four inner folds and 21 blocks, and with a
stochastic learner such as ResMLP it can also return four slightly different
rankings.  This module computes it once and stores it; later calls reuse it only
when the condition, the block library and the training rows all match.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

from run_confirmatory_nested import inner_score

REPO = Path(__file__).resolve().parents[1]
DEFAULT_DIR = REPO / "results/exploratory/ranking_cache"


def condition_key(args) -> str:
    """A file-safe name identifying the outer condition and inner grouping."""
    if getattr(args, "official_split", None) is not None:
        tag = f"official{args.official_split}"
        if getattr(args, "invert_official_split", False):
            tag += "_inverted"
    elif getattr(args, "curet_direction", None):
        tag = args.curet_direction
    else:
        tag = f"f{args.fold}"
    group = getattr(args, "inner_group_column", None) or "group"
    return f"{args.dataset}_{args.classifier}_s{args.seed}_{tag}_inner-{group}"


def _fingerprint(train: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(train, dtype=np.int64).tobytes()).hexdigest()


def ranked_singletons(cache, train, y, inner_groups, classifier, seed, key,
                      n_jobs=1, cache_dir: Path = DEFAULT_DIR) -> dict[str, float]:
    """Inner macro-F1 of every block alone, read from disk when it matches."""
    names = sorted(cache)
    fingerprint = _fingerprint(train)
    path = Path(cache_dir) / f"{key}.json"
    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))
        if stored.get("blocks") == names and stored.get("train_sha256") == fingerprint:
            return {n: float(stored["scores"][n]) for n in names}
    jobs = n_jobs if classifier == "svm" else 1
    values = Parallel(n_jobs=jobs, prefer="threads")(
        delayed(inner_score)(cache, [n], train, y, inner_groups, classifier, seed)
        for n in names)
    scores = dict(zip(names, map(float, values)))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"key": key, "classifier": classifier, "seed": seed,
                               "blocks": names, "train_sha256": fingerprint,
                               "n_train": int(len(train)), "scores": scores},
                              indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return scores
