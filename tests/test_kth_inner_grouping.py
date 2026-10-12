"""The KTH inner score must hold out physical samples, not image hashes."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import run_confirmatory_nested as nested  # noqa: E402


def test_inner_folds_hold_out_whole_kth_samples(monkeypatch):
    samples = np.repeat(["a", "b", "c"], 4)
    labels = np.tile([0, 0, 1, 1], 3)
    manifest = [
        {"group": f"image-{index}", "sample": sample}
        for index, sample in enumerate(samples)
    ]
    inner_groups = nested.manifest_groups(manifest, "sample")
    held_out = []

    def record_fold(_features, train, valid, _labels, _classifier, _seed, _backend):
        assert not set(samples[train]).intersection(samples[valid])
        held_out.append(tuple(sorted(set(samples[valid]))))
        return 0.5, 0.5, 0.0

    monkeypatch.setattr(nested, "fit_score_matrix", record_fold)
    score = nested.inner_score(
        {"toy": np.arange(len(labels)).reshape(-1, 1)}, ["toy"],
        np.arange(len(labels)), labels, inner_groups, "svm", 42,
    )

    assert score == 0.5
    assert sorted(held_out) == [("a",), ("b",), ("c",)]
