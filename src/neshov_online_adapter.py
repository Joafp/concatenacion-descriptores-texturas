"""Batch-one file-to-class adapter; not a benchmark or paper-score reproduction.

Backbone runs on the declared device in FP32; the saved MLP runs on CPU.
Model loading and warmup are outside predict_file's timer. No feature caching.
"""
import hashlib
from pathlib import Path
from time import perf_counter_ns

import torch
from PIL import Image

from neshov_beit_reference import (
    FrozenLayerAggregation, ReferenceMLP, load_offline_backbone, preprocessing,
)


def checked_sha256(path, expected):
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"SHA256 mismatch: {path}")
    return actual


class NeshovOnlineAdapter:
    """Explicit dependencies permit synthetic tests without loading real models."""

    def __init__(self, extractor, head, transform, labels, device="cpu"):
        self.labels = tuple(labels)
        if len(self.labels) < 2 or len(set(self.labels)) != len(self.labels):
            raise ValueError("explicit distinct class labels required")
        self.device = torch.device(device)
        if self.device.type not in ("cpu", "cuda"):
            raise ValueError("only CPU or CUDA supported")
        self.extractor = extractor.to(device=self.device, dtype=torch.float32).eval()
        self.head = head.to(device="cpu", dtype=torch.float32).eval()
        self.extractor.requires_grad_(False)
        self.head.requires_grad_(False)
        self.transform = transform

    @classmethod
    def from_saved_head(cls, path, expected_head_sha256, expected_backbone_sha256,
                        labels, device="cpu"):
        # Verify head before deserialization. Backbone loading is offline and strict.
        checked_sha256(path, expected_head_sha256)
        backbone, info = load_offline_backbone()
        checked_sha256(info["local_weight_path"], expected_backbone_sha256)
        head = ReferenceMLP(3072, len(labels))
        head.load_state_dict(torch.load(path, map_location="cpu", weights_only=True), strict=True)
        adapter = cls(FrozenLayerAggregation(backbone), head, preprocessing(), labels, device)
        adapter.provenance = {**info, "head_sha256": expected_head_sha256,
                              "backbone_sha256": expected_backbone_sha256,
                              "head_device": "cpu", "backbone_device": str(adapter.device),
                              "precision": "float32", "feature_cache": False}
        return adapter

    def _synchronize(self):
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)

    @torch.inference_mode()
    def predict_file(self, path):
        """Time decode RGB → preprocess → extractor → CPU head → class.

        Return prediction and logits from this very call, not historical F1.
        The caller must declare warmups and audit coverage before aggregation.
        Failures propagate; this adapter neither retries nor changes inputs.
        """
        self._synchronize()
        started = perf_counter_ns()
        with Image.open(path) as source:
            rgb = source.convert("RGB")
            try:
                batch = self.transform(rgb).unsqueeze(0).to(self.device, dtype=torch.float32)
            finally:
                rgb.close()
        features = self.extractor(batch)
        if features.shape != (1, 3072) or not torch.isfinite(features).all():
            raise ValueError("expected finite 1x3072 features")
        logits = self.head(features.to(device="cpu", dtype=torch.float32))
        if logits.shape != (1, len(self.labels)) or not torch.isfinite(logits).all():
            raise ValueError("invalid head logits or class mapping")
        prediction = self.labels[int(logits.argmax(dim=1).item())]
        self._synchronize()
        elapsed_ns = perf_counter_ns() - started
        # Output serialization is excluded; classification above is included.
        return {"prediction": prediction, "logits": logits[0].tolist(),
                "elapsed_ns": elapsed_ns, "elapsed_ms": elapsed_ns / 1e6}
