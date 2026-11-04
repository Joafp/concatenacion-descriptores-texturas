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
import inspect
import json
import os
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

from run_confirmatory_nested import inner_score, make_model

REPO = Path(__file__).resolve().parents[1]
DEFAULT_DIR = REPO / "results/exploratory/integration_v2/ranking_cache"


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


def _fingerprint(cache, train: np.ndarray, y: np.ndarray,
                 inner_groups: np.ndarray, protocol_signature: dict,
                 ngram_block=None) -> str:
    """Bind ranking scores to training rows, groups, and evaluation protocol."""
    digest = hashlib.sha256()
    digest.update(json.dumps(protocol_signature, sort_keys=True).encode("utf-8"))
    train = np.asarray(train, dtype=np.int64)
    digest.update(train.tobytes())
    digest.update(np.asarray(y[train]).tobytes())
    digest.update(np.asarray(inner_groups[train]).astype(str).tobytes())
    for name in sorted(cache):
        values = np.ascontiguousarray(cache[name][train])
        digest.update(name.encode("utf-8"))
        digest.update(str(values.shape).encode("ascii"))
        digest.update(values.dtype.str.encode("ascii"))
        digest.update(memoryview(values).cast("B"))
    if ngram_block is not None:
        # Label-free counts outside train must not affect a training ranking.
        digest.update(ngram_block.name.encode("utf-8"))
        indptr = ngram_block.counts["indptr"]
        for row in train:
            start, end = int(indptr[row]), int(indptr[row + 1])
            digest.update(np.asarray([end - start], dtype="<i8").tobytes())
            for name in ("keys", "counts"):
                values = np.ascontiguousarray(ngram_block.counts[name][start:end])
                digest.update(values.dtype.str.encode("ascii"))
                digest.update(memoryview(values).cast("B"))
    return digest.hexdigest()


def ranked_singletons(cache, train, y, inner_groups, classifier, seed, key,
                      n_jobs=1, cache_dir: Path = DEFAULT_DIR,
                      n_splits=4, svm_backend="cpu", protocol_signature=None,
                      return_info=False, ngram_block=None):
    """Inner macro-F1 of every block alone, read from disk when it matches."""
    names = sorted(cache)
    if ngram_block is not None:
        if ngram_block.name in cache:
            raise ValueError("trainable N-gram block cannot also be a static matrix")
        names = sorted(names + [ngram_block.name])
    evaluator_source = inspect.getsource(inner_score) + inspect.getsource(make_model)
    signature = {
        "classifier": classifier,
        "seed": int(seed),
        "n_splits": int(n_splits),
        "splitter": "StratifiedGroupKFold(shuffle=True, random_state=seed)",
        "scorer": "macro_f1",
        "svm_backend": svm_backend,
        "evaluator_source_sha256": hashlib.sha256(evaluator_source.encode("utf-8")).hexdigest(),
        "caller_protocol": protocol_signature or {},
    }
    if ngram_block is not None:
        module_path = Path(inspect.getfile(type(ngram_block)))
        signature["ngram"] = {
            "components": ngram_block.n_components,
            "hash_bins": ngram_block.hash_bins,
            "random_state": ngram_block.random_state,
            "implementation_source_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(),
            "foldaware_evaluator_sha256": hashlib.sha256(
                Path(inspect.getfile(inner_score)).read_bytes()).hexdigest(),
        }
    fingerprint = _fingerprint(cache, train, y, inner_groups, signature, ngram_block)
    path = Path(cache_dir) / f"{key}.json"
    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))
        if (stored.get("blocks") == names
                and stored.get("training_inputs_sha256") == fingerprint
                and stored.get("protocol_signature") == signature):
            scores = {n: float(stored["scores"][n]) for n in names}
            info = {"cache_hit": True, "cache_path": str(path),
                    "training_inputs_sha256": fingerprint, "model_fits": 0}
            return (scores, info) if return_info else scores
    jobs = n_jobs if classifier == "svm" else 1
    effective_splits = min(n_splits, len(np.unique(inner_groups[train])))
    values = Parallel(n_jobs=jobs, prefer="threads")(
        delayed(inner_score)(cache, [n], train, y, inner_groups, classifier, seed,
                             n_splits=n_splits, svm_backend=svm_backend,
                             ngram_block=ngram_block)
        for n in names)
    scores = dict(zip(names, map(float, values)))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"key": key, "classifier": classifier, "seed": seed,
                               "blocks": names, "training_inputs_sha256": fingerprint,
                               "protocol_signature": signature,
                               "n_train": int(len(train)), "scores": scores},
                              indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    info = {"cache_hit": False, "cache_path": str(path),
            "training_inputs_sha256": fingerprint,
            "model_fits": len(names) * effective_splits}
    return (scores, info) if return_info else scores
