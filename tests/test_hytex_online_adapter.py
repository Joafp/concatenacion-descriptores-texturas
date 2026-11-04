import numpy as np
from PIL import Image
import pytest
import torch
from torch import nn

import hytex_online_adapter as module
from hytex_reference import HyTexFusionHead
from hytex_fixed_training import fit_head


class FakeBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def forward(self, batch):
        assert batch.shape == (1, 3, 128, 128) and batch.dtype == torch.float32
        assert not self.training and not torch.is_grad_enabled()
        self.calls += 1
        return torch.ones(1, 1024)


def test_full_file_path_uses_same_call_features_prediction_and_timer(tmp_path, monkeypatch):
    path = tmp_path / 'gray.png'
    Image.new('L', (5, 7)).save(path)
    head = HyTexFusionHead(2)
    with torch.no_grad():
        for parameter in head.parameters():
            parameter.zero_()
        head[-1].bias.copy_(torch.tensor([0., 1.]))
    adapter = module.HyTexOnlineAdapter(FakeBackbone(), head, (3, 8))
    clock = iter([10, 3000010, 4000010, 7000010])
    monkeypatch.setattr(module, 'perf_counter_ns', lambda: next(clock))
    first = adapter.predict_file(path)
    second = adapter.predict_file(path)
    assert first == second == {'prediction': 8, 'logits': [0., 1.],
                              'elapsed_ns': 3000000, 'elapsed_ms': 3.}
    assert adapter.backbone.calls == 2
    feature = adapter.extract_file(path)
    assert feature.shape == (1, 1538) and feature[:, :1024].eq(1).all()
    assert torch.isfinite(feature).all() and not adapter.head.training


def test_no_head_or_missing_file_fails_without_fallback(tmp_path):
    adapter = module.HyTexOnlineAdapter(FakeBackbone(), None, (0, 1))
    with pytest.raises(ValueError, match='trained head'):
        adapter.predict_file(tmp_path / 'absent')
    with pytest.raises(FileNotFoundError):
        adapter.extract_file(tmp_path / 'absent')
    assert adapter.backbone.calls == 0


def test_bad_head_checksum_rejected_before_offline_loading(tmp_path, monkeypatch):
    path = tmp_path / 'head.pt'
    path.write_bytes(b'invalid')
    monkeypatch.setattr(module, 'load_offline_model', lambda _: pytest.fail('must not load'))
    with pytest.raises(ValueError, match='SHA256'):
        module.HyTexOnlineAdapter.from_offline('0' * 64, (0, 1), head_path=path, head_sha256='0' * 64)


def test_fixed_training_is_seeded_and_final_epoch_only():
    x = np.arange(4 * 1538, dtype=np.float32).reshape(4, 1538) / 10000
    a, ah = fit_head(x, [0, 1, 0, 1], 2, epochs=2)
    b, bh = fit_head(x, [0, 1, 0, 1], 2, epochs=2)
    assert ah == bh and len(ah) == 2
    assert all(torch.equal(v, b.state_dict()[k]) for k, v in a.state_dict().items())
    assert not a.training


def test_training_does_not_accept_missing_classes_or_wrong_dimension():
    with pytest.raises(ValueError):
        fit_head(np.zeros((4, 1538)), [0] * 4, 2, epochs=1)
    with pytest.raises(ValueError):
        fit_head(np.zeros((4, 514)), [0, 1, 0, 1], 2, epochs=1)
