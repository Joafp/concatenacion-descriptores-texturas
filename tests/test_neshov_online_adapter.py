import pytest
import torch
from PIL import Image
from torch import nn

import neshov_online_adapter as module


class Features(nn.Module):
    def __init__(self, width=3072):
        super().__init__()
        self.width = width
        self.calls = 0

    def forward(self, batch):
        assert batch.shape == (1, 3, 4, 4)
        assert not self.training and not torch.is_grad_enabled()
        self.calls += 1
        return torch.ones(1, self.width)


def make_adapter(width=3072):
    head = nn.Linear(3072, 2)
    with torch.no_grad():
        head.weight.zero_()
        head.bias.copy_(torch.tensor([0., 2.]))

    def transform(image):
        assert image.mode == "RGB"
        return torch.zeros(3, 4, 4)

    return module.NeshovOnlineAdapter(Features(width), head, transform, (4, 9))


def test_single_file_prediction_and_timer_include_decode(tmp_path, monkeypatch):
    path = tmp_path / "gray.png"
    Image.new("L", (4, 4)).save(path)
    adapter = make_adapter()
    events = []
    clock = iter([10, 2000010])
    monkeypatch.setattr(module, "perf_counter_ns", lambda: (events.append("clock"), next(clock))[1])
    monkeypatch.setattr(adapter, "_synchronize", lambda: events.append("sync"))
    original_open = module.Image.open

    def observed_open(path):
        events.append("decode")
        return original_open(path)

    monkeypatch.setattr(module.Image, "open", observed_open)
    result = adapter.predict_file(path)
    assert events == ["sync", "clock", "decode", "sync", "clock"]
    assert result == {"prediction": 9, "logits": [0., 2.],
                      "elapsed_ns": 2000000, "elapsed_ms": 2.}
    assert not adapter.head.training
    assert all(not p.requires_grad for p in adapter.head.parameters())


def test_calls_do_not_share_features(tmp_path):
    path = tmp_path / "input.png"
    Image.new("RGB", (4, 4)).save(path)
    adapter = make_adapter()
    adapter.predict_file(path)
    adapter.predict_file(path)
    assert adapter.extractor.calls == 2


def test_wrong_dimension_fails_without_retry(tmp_path):
    path = tmp_path / "input.png"
    Image.new("RGB", (4, 4)).save(path)
    adapter = make_adapter(768)
    with pytest.raises(ValueError, match="1x3072"):
        adapter.predict_file(path)
    assert adapter.extractor.calls == 1


def test_missing_file_is_not_replaced(tmp_path):
    adapter = make_adapter()
    with pytest.raises(FileNotFoundError):
        adapter.predict_file(tmp_path / "absent.png")
    assert adapter.extractor.calls == 0


def test_digest_fails_before_loading_backbone(tmp_path, monkeypatch):
    path = tmp_path / "head.pt"
    path.write_bytes(b"not a checkpoint")
    monkeypatch.setattr(module, "load_offline_backbone", lambda: pytest.fail("must not load"))
    with pytest.raises(ValueError, match="SHA256"):
        module.NeshovOnlineAdapter.from_saved_head(path, "0" * 64, "0" * 64, (0, 1))


@pytest.mark.parametrize("labels", [(0,), (1, 1)])
def test_class_mapping_must_be_explicit_distinct(labels):
    with pytest.raises(ValueError, match="labels"):
        module.NeshovOnlineAdapter(Features(), nn.Linear(3072, 2), None, labels)
