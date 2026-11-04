"""Documented reimplementation prototype of Neshov et al. (2025), BEiTv2 branch.

DOI 10.3390/electronics14234779, Figure 1 and sections 3.8, 4.2, 4.4, 4.5.
This is not author code or a claim to have reproduced the published scores.
Layer numbers are interpreted as ONE-based, consistent with Table 2's 1..12 sets.
"""
from pathlib import Path

import torch
from torch import nn


MODEL_NAME = "beitv2_base_patch16_224.in1k_ft_in22k_in1k"
PAPER_LAYERS = (2, 5, 8, 11)


class FrozenLayerAggregation(nn.Module):
    """Pool patch tokens at four block outputs during one complete backbone pass.

    No added per-layer LayerNorm or L2 normalization: neither is specified in the
    paper's aggregation recipe. Full backbone execution is deliberately explicit;
    it is not a claimed reproduction of an undocumented early-stop optimization.
    """

    def __init__(self, backbone, layers=PAPER_LAYERS, prefix_tokens=1):
        super().__init__()
        if len(layers) != 4 or len(set(layers)) != 4:
            raise ValueError("four distinct one-based layer numbers required")
        if any(not isinstance(i, int) or i < 1 or i > len(backbone.blocks) for i in layers):
            raise ValueError("layer number outside backbone")
        if prefix_tokens < 0:
            raise ValueError("invalid prefix-token count")
        self.backbone = backbone
        self.layers = tuple(layers)
        self.prefix_tokens = prefix_tokens
        self.backbone.requires_grad_(False)
        self.backbone.eval()

    def train(self, mode=True):
        # Changing the head's mode must never enable dropout in the frozen backbone.
        super().train(False)
        self.backbone.eval()
        return self

    @torch.no_grad()
    def forward(self, images):
        outputs, handles = {}, []

        def capture(number):
            def hook(module, inputs, output):
                if output.ndim != 3 or output.shape[1] <= self.prefix_tokens:
                    raise ValueError("expected batch x tokens x channels with patch tokens")
                outputs[number] = output[:, self.prefix_tokens:, :].mean(dim=1)
            return hook

        try:
            for number in self.layers:
                handles.append(self.backbone.blocks[number - 1].register_forward_hook(capture(number)))
            self.backbone.forward_features(images)
        finally:
            for handle in handles:
                handle.remove()
        if set(outputs) != set(self.layers):
            raise ValueError("not all requested layers executed")
        return torch.cat([outputs[number] for number in self.layers], dim=1)


class ReferenceMLP(nn.Sequential):
    """Figure 1: FC(64), BN, ReLU, Dropout(.2), FC(K), then softmax for inference.

    Forward returns logits so CrossEntropyLoss can apply log-softmax once.
    """

    def __init__(self, input_dim, n_classes):
        if input_dim < 1 or n_classes < 2:
            raise ValueError("positive input dimension and at least two classes required")
        super().__init__(nn.Linear(input_dim, 64), nn.BatchNorm1d(64),
                         nn.ReLU(), nn.Dropout(.2), nn.Linear(64, n_classes))


def preprocessing():
    from torchvision import transforms
    from torchvision.transforms import InterpolationMode
    # The paper fixes 224x224 and ImageNet mean/std, but not interpolation.
    return transforms.Compose([
        transforms.Resize((224, 224), interpolation=InterpolationMode.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize((.485, .456, .406), (.229, .224, .225)),
    ])


def load_strict_compatible_state(backbone, checkpoint):
    """Discard only the pretraining head and equal regenerated position indices.

    Current timm makes relative_position_index nonpersistent. It is not a learned
    weight. Unlike strict=False, this bridge checks exact buffer equality and
    still rejects every other missing/unexpected parameter or shape mismatch.
    """
    state = dict(checkpoint)
    discarded_head = sorted(k for k in state if k.startswith("head."))
    for key in discarded_head:
        del state[key]
    expected = backbone.state_dict()
    buffers = dict(backbone.named_buffers())
    regenerated = []
    for key in list(state):
        if key not in expected and key.rsplit(".", 1)[-1] == "relative_position_index":
            if key not in buffers or not torch.equal(state[key].cpu(), buffers[key].cpu()):
                raise ValueError(f"regenerated position indices disagree: {key}")
            regenerated.append(key)
            del state[key]
    backbone.load_state_dict(state, strict=True)
    return {"discarded_pretraining_head_keys": discarded_head,
            "equal_regenerated_position_buffers": sorted(regenerated),
            "weight_loading": "strict after exact generated-buffer verification"}


def load_offline_backbone():
    """Load only a local weight file; fail rather than download or use random weights."""
    import timm
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file

    path = Path(hf_hub_download("timm/" + MODEL_NAME, "model.safetensors", local_files_only=True))
    backbone = timm.create_model(MODEL_NAME, pretrained=False, num_classes=0)
    state = load_file(str(path), device="cpu")
    compatibility = load_strict_compatible_state(backbone, state)
    backbone.requires_grad_(False)
    backbone.eval()
    return backbone, {"checkpoint": MODEL_NAME, "local_weight_path": str(path),
                      **compatibility,
                      "timm_version": timm.__version__}
