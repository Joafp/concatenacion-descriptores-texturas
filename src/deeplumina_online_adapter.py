"""Complete file-to-class inference path for the DECLARED LOCAL DeepLumina adaptation."""
from pathlib import Path
from time import perf_counter_ns

import numpy as np
from PIL import Image
import torch

from deeplumina_reference import (
    CHECKPOINT_SHA,
    METHOD,
    MODEL_NAME,
    SparseRandomECOCClassifier,
    compute_yiq_luminance,
    fuse_rgb_and_luminance_fc1000,
)
from neshov_online_adapter import checked_sha256


def load_offline_model(expected_sha256=CHECKPOINT_SHA):
    if expected_sha256 != CHECKPOINT_SHA:
        raise ValueError("unapproved ResNet101 checkpoint SHA256")
    import timm
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file

    path = Path(hf_hub_download("timm/" + MODEL_NAME, "model.safetensors", local_files_only=True))
    checked_sha256(path, expected_sha256)
    model = timm.create_model(MODEL_NAME, pretrained=False, num_classes=1000)
    state = dict(load_file(str(path), device="cpu"))
    model.load_state_dict(state, strict=True)
    return model, {
        "checkpoint": str(path),
        "checkpoint_sha256": expected_sha256,
        "feature_layer": "fc1000",
        "weight_loading": "strict",
        "timm_version": timm.__version__,
    }


class DeepLuminaOnlineAdapter:
    def __init__(self, backbone, head, labels, device="cpu"):
        self.labels = tuple(int(x) for x in labels)
        if len(self.labels) < 3 or len(set(self.labels)) != len(self.labels):
            raise ValueError("distinct explicit class mapping (>=3 classes) required")
        self.device = torch.device(device)
        if self.device.type not in ("cpu", "cuda"):
            raise ValueError("only CPU and CUDA supported")
        self.backbone = backbone.to(device=self.device, dtype=torch.float32).eval()
        self.backbone.requires_grad_(False)
        self.head = head
        if self.head is not None:
            if not isinstance(self.head, SparseRandomECOCClassifier):
                raise ValueError("SparseRandomECOCClassifier head required")
            if self.head.labels != self.labels:
                raise ValueError("head class mapping mismatch")
            self.head.validate_fitted()

    @classmethod
    def from_offline(
        cls,
        checkpoint_sha256,
        labels,
        device="cuda",
        head_path=None,
        head_sha256=None,
    ):
        head = None
        if head_path is not None:
            import joblib

            checked_sha256(head_path, head_sha256)
            head = joblib.load(head_path)
            if not isinstance(head, SparseRandomECOCClassifier):
                raise ValueError("SparseRandomECOCClassifier head required")
        model, info = load_offline_model(checkpoint_sha256)
        adapter = cls(model, head, labels, device=device)
        adapter.provenance = {
            **info,
            "method": METHOD,
            "head_sha256": head_sha256,
            "head_device": "cpu",
            "backbone_device": str(adapter.device),
            "precision": "float32",
            "feature_cache": False,
        }
        return adapter

    def _synchronize(self):
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)

    @torch.inference_mode()
    def extract_file(self, path):
        with Image.open(path) as source:
            with source.convert("RGB") as rgb:
                with rgb.resize((224, 224), Image.Resampling.BICUBIC) as resized:
                    pixels = np.array(resized, dtype=np.uint8, copy=True)
        rgb_float = pixels.astype(np.float32) / 255.0
        y_float3 = compute_yiq_luminance(rgb_float)
        mean = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(3, 1, 1)

        rgb_tensor = torch.from_numpy(rgb_float).permute(2, 0, 1)
        rgb_batch = ((rgb_tensor - mean) / std).unsqueeze(0).to(self.device)

        y_tensor = torch.from_numpy(y_float3).permute(2, 0, 1)
        y_batch = ((y_tensor - mean) / std).unsqueeze(0).to(self.device)

        # Two independent passes with the same frozen ResNet101 weights
        rgb_fc = self.backbone(rgb_batch).to("cpu", dtype=torch.float32)
        y_fc = self.backbone(y_batch).to("cpu", dtype=torch.float32)
        return fuse_rgb_and_luminance_fc1000(rgb_fc, y_fc)

    @torch.inference_mode()
    def predict_file(self, path):
        if self.head is None:
            raise ValueError("trained ECOC head required before prediction")
        self._synchronize()
        started = perf_counter_ns()
        features = self.extract_file(path).numpy()
        out = self.head.predict_single(features)
        self._synchronize()
        elapsed = perf_counter_ns() - started
        return {
            **out,
            "elapsed_ns": elapsed,
            "elapsed_ms": elapsed / 1e6,
        }
