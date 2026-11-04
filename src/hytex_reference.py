"""HyTexNet source-formula descriptor and fusion head; not a trained replica.

DOI 10.1016/j.knosys.2026.115482, equations 1-18. Explicit reconstruction
choices: clockwise neighbors starting top-left; discard one-pixel border;
each histogram L1-normalized; center threshold is the equation's GLOBAL mean.
Equation 4 is the empirical inverse CDF, not interpolated numpy percentile.
Input grayscale conversion/resize and DenseNet weights are not defined here.
"""
import numpy as np
import torch
from torch import nn


def empirical_t75(magnitudes):
    values = np.asarray(magnitudes, dtype=np.float64)
    if values.shape[-1:] != (8,) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('eight finite nonnegative neighbor magnitudes required')
    # ceil(.75*8)-1 = 5: the sixth order statistic, including ties.
    return np.partition(values, 5, axis=-1)[..., 5]


def hytex_descriptor(gray):
    gray = np.asarray(gray, dtype=np.float64)
    if gray.ndim != 2 or min(gray.shape) < 3 or not np.isfinite(gray).all():
        raise ValueError('finite grayscale matrix of at least 3x3 required')
    windows = np.lib.stride_tricks.sliding_window_view(gray, (3, 3))
    center = windows[..., 1, 1]
    offsets = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0))
    neighbors = np.stack([windows[..., y, x] for y, x in offsets], axis=-1)
    weights = 2 ** np.arange(8, dtype=np.int64)
    sign = ((neighbors >= center[..., None]) * weights).sum(axis=-1)
    magnitudes = np.abs(neighbors - center[..., None])
    magnitude = ((magnitudes >= empirical_t75(magnitudes)[..., None]) * weights).sum(axis=-1)
    central = (center >= gray.mean()).astype(np.int64)
    histograms = [np.bincount(code.ravel(), minlength=bins).astype(np.float64) / code.size
                  for code, bins in ((sign, 256), (magnitude, 256), (central, 2))]
    return np.concatenate(histograms).astype(np.float32)


class HyTexFusionHead(nn.Sequential):
    """1538→256/ReLU/Dropout(.5)→K; logits for cross-entropy.

    Softmax/argmax are inference operations. No undocumented BatchNorm added.
    """
    def __init__(self, n_classes):
        if n_classes < 2:
            raise ValueError('at least two classes required')
        super().__init__(nn.Linear(1538, 256), nn.ReLU(), nn.Dropout(.5),
                         nn.Linear(256, n_classes))


def fuse_features(deep, local):
    """Equation 15 order: CNN1024 first, then HyTex514; no added scaling."""
    if (deep.ndim != 2 or local.ndim != 2 or deep.shape[0] != local.shape[0]
            or deep.shape[1] != 1024 or local.shape[1] != 514
            or not torch.isfinite(deep).all() or not torch.isfinite(local).all()):
        raise ValueError('aligned finite CNN1024 and HyTex514 required')
    return torch.cat([deep, local.to(device=deep.device, dtype=deep.dtype)], dim=1)
