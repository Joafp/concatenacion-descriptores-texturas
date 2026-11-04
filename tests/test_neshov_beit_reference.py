import pytest
import torch
from torch import nn
from neshov_beit_reference import FrozenLayerAggregation, ReferenceMLP, load_strict_compatible_state


class AddOne(nn.Module):
    def forward(self, x):
        return x + 1


class FakeBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.blocks = nn.ModuleList([AddOne() for _ in range(12)])
        self.weight = nn.Parameter(torch.ones(1))

    def forward_features(self, x):
        for block in self.blocks:
            x = block(x)
        return x


def test_layer_numbering_excludes_cls_and_preserves_concatenation_order():
    model = FakeBackbone()
    extractor = FrozenLayerAggregation(model)
    x = torch.zeros(2, 3, 2)
    x[:, 0, :] = 999
    result = extractor(x)
    assert result.shape == (2, 8)
    assert torch.equal(result[0], torch.tensor([2., 2., 5., 5., 8., 8., 11., 11.]))
    assert all(not b._forward_hooks for b in model.blocks)


def test_backbone_remains_frozen_and_in_eval_when_training_head():
    backbone = FakeBackbone()
    extractor = FrozenLayerAggregation(backbone).train()
    assert not backbone.training and not any(p.requires_grad for p in backbone.parameters())
    head = ReferenceMLP(8, 3).train()
    features = extractor(torch.zeros(4, 3, 2))
    head(features).sum().backward()
    assert head[0].weight.grad is not None and backbone.weight.grad is None


def test_mlp_matches_paper_order_and_returns_logits():
    head = ReferenceMLP(3072, 10)
    assert [type(m) for m in head] == [nn.Linear, nn.BatchNorm1d, nn.ReLU, nn.Dropout, nn.Linear]
    assert head[0].out_features == 64 and head[3].p == .2
    assert head.eval()(torch.zeros(2, 3072)).shape == (2, 10)


@pytest.mark.parametrize("layers", [(0, 5, 8, 11), (2, 5, 8, 13), (2, 2, 8, 11), (2, 5)])
def test_invalid_layer_requests_fail(layers):
    with pytest.raises(ValueError):
        FrozenLayerAggregation(FakeBackbone(), layers=layers)


def test_generated_index_compatibility_is_exact_and_other_keys_remain_strict():
    model = nn.Linear(2, 2)
    model.register_buffer("relative_position_index", torch.tensor([0, 1]), persistent=False)
    state = {**model.state_dict(), "relative_position_index": torch.tensor([0, 1]),
             "head.weight": torch.ones(3, 2)}
    info = load_strict_compatible_state(model, state)
    assert info["equal_regenerated_position_buffers"] == ["relative_position_index"]
    assert "head.weight" in state  # caller-owned checkpoint remains untouched
    with pytest.raises(ValueError):
        load_strict_compatible_state(model, {**state, "relative_position_index": torch.tensor([1, 0])})
    with pytest.raises(RuntimeError):
        load_strict_compatible_state(model, {**state, "unexplained.weight": torch.ones(1)})
    with pytest.raises(RuntimeError):
        load_strict_compatible_state(model, {k: v for k, v in state.items() if k != "weight"})
