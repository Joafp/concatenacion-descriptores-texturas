"""CPU-only candidate input adapters matching the historical SOTA recipe.

These functions load no neural model or weights. Their unit tests establish
input-transform contracts, not embedding fidelity or authorization to retry a
scientific failure. The existing online executor is deliberately unchanged.
"""
from __future__ import annotations
from collections.abc import Mapping

import numpy as np
from torchvision import transforms
from torchvision.transforms import InterpolationMode


def _check_rgb_normalization(mean, std):
    if len(mean) != 3 or len(std) != 3:
        raise ValueError("RGB normalization requires three channels")
    if not np.isfinite(mean).all() or not np.isfinite(std).all() or min(std) <= 0:
        raise ValueError("normalization must be finite with positive standard deviations")


def eva02_reference_transform(config: Mapping | None = None):
    """Use timm's evaluation transform, preserving crop_pct and interpolation."""
    from timm.data import create_transform, resolve_model_data_config
    if config is None:
        from timm import get_pretrained_cfg
        config = resolve_model_data_config(
            None, pretrained_cfg=get_pretrained_cfg("eva02_base_patch14_224").to_dict())
    config = dict(config)
    if tuple(config["input_size"]) != (3, 224, 224):
        raise ValueError("this adapter is frozen to the historical EVA-02 224 RGB recipe")
    _check_rgb_normalization(config["mean"], config["std"])
    return create_transform(**config, is_training=False)


def siglip_reference_transform(processor_config: Mapping):
    """Reproduce the explicit historical Resize/ToTensor/Normalize sequence.

    The historical source uses processor mean/std only. Its Resize default
    is bilinear in the audited torchvision runtime; processor resample is
    intentionally not used. No assumption of original-runtime identity is made.
    """
    mean, std = processor_config["image_mean"], processor_config["image_std"]
    _check_rgb_normalization(mean, std)
    return transforms.Compose([
        transforms.Resize((224, 224), interpolation=InterpolationMode.BILINEAR, antialias=True),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ])
