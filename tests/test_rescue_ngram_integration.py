"""Train-only SVD and cache-identity checks for the rescue integration."""

import json

import numpy as np
import pytest

from rgb_ngram_descriptor import RGBNgramSVDBlock, _manifest_digest
from run_rescue_nested_selection import (
    REPO, base_oof_margins, fit_scores, load_existing_ngram,
)
from run_rgb_ngram_outex13_official import IMPLEMENTATIONS
from singleton_ranking import _fingerprint, ranked_singletons


def sample_inputs():
    n = 48
    y = np.arange(n) % 2
    keys = np.concatenate([np.asarray([1, 3, 5], dtype=np.uint64) + 8 * label
                           for label in y])
    counts = {"keys": keys,
              "counts": np.tile(np.asarray([2, 3, 5], dtype=np.uint32), n),
              "indptr": np.arange(0, 3 * n + 1, 3, dtype=np.int64)}
    rng = np.random.default_rng(42)
    static = {"static": rng.normal(size=(n, 3)).astype(np.float32)}
    return counts, static, y, np.arange(n)


def test_eval_counts_do_not_change_fitted_training_projection():
    counts, _, _, _ = sample_inputs()
    train, evaluate = np.arange(32), np.arange(32, 40)
    block = RGBNgramSVDBlock(counts, n_components=4, hash_bins=32)
    x_train, x_eval, _ = block.transform(train, evaluate)
    changed = {name: values.copy() for name, values in counts.items()}
    changed["keys"][3 * 32:3 * 40] = 24
    other = RGBNgramSVDBlock(changed, n_components=4, hash_bins=32)
    other_train, other_eval, _ = other.transform(train, evaluate)
    np.testing.assert_array_equal(x_train, other_train)
    assert not np.allclose(x_eval, other_eval)
    audit = block.transformation_audits()[0]
    assert audit["train_indices"] == train.tolist()
    assert audit["evaluation_indices"] == evaluate.tolist()
    assert audit["components"] == 4


def test_ranking_identity_uses_only_training_counts():
    counts, static, y, groups = sample_inputs()
    train = np.arange(40)
    block = RGBNgramSVDBlock(counts, n_components=4, hash_bins=32)
    before = _fingerprint(static, train, y, groups, {}, block)
    counts["keys"][3 * 45] += 1
    assert _fingerprint(static, train, y, groups, {}, block) == before
    counts["keys"][3 * 2] += 1
    assert _fingerprint(static, train, y, groups, {}, block) != before


def test_dynamic_ranking_fit_and_calibration_restrict_projection_to_training(tmp_path):
    counts, static, y, groups = sample_inputs()
    train, evaluate = np.arange(40), np.arange(40, 48)
    block = RGBNgramSVDBlock(counts, n_components=4, hash_bins=32)
    rank, info = ranked_singletons(
        static, train, y, groups, "svm", 42, "synthetic",
        n_splits=2, cache_dir=tmp_path, ngram_block=block, return_info=True)
    assert set(rank) == {"static", "rgb_ngram_svd"}
    assert info["model_fits"] == 4 and not info["cache_hit"]
    margins = base_oof_margins(static, block.name, train, y, groups, 42, 2, block)
    assert margins.shape == (40,) and np.isfinite(margins).all()
    for audit in block.transformation_audits():
        fit, val = set(audit["train_indices"]), set(audit["evaluation_indices"])
        assert not fit.intersection(val)
        assert fit | val == set(train)
    _, second = ranked_singletons(
        static, train, y, groups, "svm", 42, "synthetic",
        n_splits=2, cache_dir=tmp_path, ngram_block=block, return_info=True)
    assert second["cache_hit"] and second["model_fits"] == 0
    for subset in ([block.name], ["static", block.name]):
        scores, predictions, scale = fit_scores(
            static, subset, train, evaluate, y, np.unique(y), 42, block)
        assert scores.shape == (8, 2) and predictions.shape == (8,)
        assert np.isfinite(scores).all() and scale > 0


def test_existing_cache_is_rejected_when_manifest_changes(tmp_path):
    counts, _, y, _ = sample_inputs()
    rows = [{"row_id": str(i), "path": str(tmp_path / f"{i}.jpg"),
             "source_sha256": str(i)} for i in range(len(y))]
    for name, values in counts.items():
        np.save(tmp_path / f"{name}.npy", values)
    (tmp_path / "metadata.json").write_text(json.dumps({
        "implementation": "rgb_ngram_impl1", "config": IMPLEMENTATIONS["rgb_ngram_impl1"],
        "samples": len(rows), "manifest_sha256": _manifest_digest(rows, REPO),
    }))
    block, provenance = load_existing_ngram(rows, tmp_path, 4, 32, 42)
    assert block.name == "rgb_ngram_svd" and len(provenance["file_sha256"]) == 4
    rows[0]["source_sha256"] = "changed"
    with pytest.raises(ValueError, match="does not match"):
        load_existing_ngram(rows, tmp_path, 4, 32, 42)
