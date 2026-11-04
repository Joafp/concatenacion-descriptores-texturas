import numpy as np
from PIL import Image
import pytest
import torch
from torch import nn

import deeplumina_online_adapter as adapter_mod
from deeplumina_reference import (
    SparseRandomECOCClassifier,
    compute_yiq_luminance,
    filter_coding_columns,
    fuse_rgb_and_luminance_fc1000,
    generate_sparse_random_coding_matrix,
    min_pairwise_row_distance,
)


class FakeResNet101(nn.Module):
    def __init__(self):
        super().__init__()
        self.calls = []

    def forward(self, batch):
        assert batch.shape == (1, 3, 224, 224) and batch.dtype == torch.float32
        assert not self.training and not torch.is_grad_enabled()
        call_idx = len(self.calls)
        self.calls.append(batch.detach().cpu().clone())
        # Return distinct values for RGB pass vs Y pass to verify concatenation order
        val = 1.0 if call_idx % 2 == 0 else 2.0
        return torch.full((1, 1000), val, dtype=torch.float32)


def test_yiq_luminance_equation_and_channel_replication():
    rgb = np.array([[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]], dtype=np.float32)
    y3 = compute_yiq_luminance(rgb)
    assert y3.shape == (1, 3, 3) and y3.dtype == np.float32
    assert np.allclose(y3[0, 0], 0.299)
    assert np.allclose(y3[0, 1], 0.587)
    assert np.allclose(y3[0, 2], 0.114)


def test_concatenation_order_and_dimension_2000():
    rgb_fc = torch.ones((2, 1000), dtype=torch.float32)
    y_fc = torch.full((2, 1000), 3.5, dtype=torch.float32)
    fused = fuse_rgb_and_luminance_fc1000(rgb_fc, y_fc)
    assert fused.shape == (2, 2000)
    assert torch.all(fused[:, :1000] == 1.0)
    assert torch.all(fused[:, 1000:] == 3.5)
    with pytest.raises(ValueError):
        fuse_rgb_and_luminance_fc1000(torch.ones((2, 2048)), torch.ones((2, 2048)))


def test_filter_coding_columns_and_pairwise_distance():
    # Col 0: valid [1, -1, 0]
    # Col 1: invalid (only +1 and 0)
    # Col 2: duplicate of Col 0
    # Col 3: negated duplicate of Col 0 [-1, 1, 0]
    # Col 4: valid [0, 1, -1]
    raw = np.array(
        [
            [1, 1, 1, -1, 0],
            [-1, 0, -1, 1, 1],
            [0, 1, 0, 0, -1],
        ],
        dtype=np.int8,
    )
    filtered = filter_coding_columns(raw)
    assert filtered.shape == (3, 2)
    assert np.array_equal(filtered[:, 0], [1, -1, 0])
    assert np.array_equal(filtered[:, 1], [0, 1, -1])
    # Pair (0,1) differs in col 0 (+1 vs -1) -> dist 1.0
    # Pair (0,2) has 0 in both cols for one class -> dist 0.0
    assert min_pairwise_row_distance(filtered) == 0.0


def test_reproducible_sparse_random_matrix_k10():
    m1, meta1 = generate_sparse_random_coding_matrix(10, seed=42, n_candidates=100)
    m2, meta2 = generate_sparse_random_coding_matrix(10, seed=42, n_candidates=100)
    assert np.array_equal(m1, m2)
    assert meta1 == meta2
    assert meta1["raw_columns"] == 50
    assert m1.shape[0] == 10 and 0 < m1.shape[1] <= 50
    for l_idx in range(m1.shape[1]):
        col = m1[:, l_idx]
        assert (col == 1).any() and (col == -1).any()


def test_ecoc_zero_row_exclusion_and_tie_breaking():
    # 3 classes, 2 columns:
    # class 10: [+1,  0]
    # class 20: [-1, +1]
    # class 30: [ 0, -1]
    coding = np.array([[1, 0], [-1, 1], [0, -1]], dtype=np.int8)
    rng = np.random.default_rng(7)
    x = rng.normal(size=(12, 2000)).astype(np.float32)
    y = np.array([10] * 4 + [20] * 4 + [30] * 4, dtype=np.int64)
    clf = SparseRandomECOCClassifier.fit_from_features(x, y, (10, 20, 30), seed=42, n_candidates=20)
    assert clf.labels == (10, 20, 30)
    # Test exact tie-breaking to smallest class index when margins are all zero
    for est in clf.estimators:
        est.coef_.fill(0.0)
        est.intercept_.fill(0.0)
    res = clf.predict_single(np.zeros((1, 2000), dtype=np.float32))
    assert np.allclose(res["ecoc_losses"], 0.5)
    assert res["prediction"] == 10


def test_online_adapter_single_call_contract(tmp_path, monkeypatch):
    img_path = tmp_path / "sample.png"
    Image.new("RGB", (16, 12), color=(100, 150, 200)).save(img_path)
    rng = np.random.default_rng(11)
    x = rng.normal(size=(9, 2000)).astype(np.float32)
    y = np.array([0, 1, 2] * 3, dtype=np.int64)
    head = SparseRandomECOCClassifier.fit_from_features(x, y, (0, 1, 2), seed=42, n_candidates=20)
    fake_net = FakeResNet101()
    adapter = adapter_mod.DeepLuminaOnlineAdapter(fake_net, head, (0, 1, 2), device="cpu")
    clock = iter([1000, 5001000])
    monkeypatch.setattr(adapter_mod, "perf_counter_ns", lambda: next(clock))
    out = adapter.predict_file(img_path)
    assert out["elapsed_ns"] == 5000000 and out["elapsed_ms"] == 5.0
    assert len(fake_net.calls) == 2
    assert len(out["ecoc_losses"]) == 3 and len(out["logits"]) == 3
    assert out["prediction"] == int(np.argmax(out["logits"]))
    feat = adapter.extract_file(img_path)
    assert feat.shape == (1, 2000)
    assert torch.all(feat[:, :1000] == 1.0) and torch.all(feat[:, 1000:] == 2.0)
