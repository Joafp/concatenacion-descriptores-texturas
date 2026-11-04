"""Complete file-to-class inference path for the DECLARED LOCAL HyTex adaptation."""
from pathlib import Path
from time import perf_counter_ns

import numpy as np
from PIL import Image
import torch

from hytex_reference import hytex_descriptor, fuse_features, HyTexFusionHead
from neshov_online_adapter import checked_sha256

MODEL_NAME = 'densenet121.tv_in1k'


def load_offline_model(expected_sha256):
    import timm
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file
    path = Path(hf_hub_download('timm/' + MODEL_NAME, 'model.safetensors', local_files_only=True))
    checked_sha256(path, expected_sha256)
    model = timm.create_model(MODEL_NAME, pretrained=False, num_classes=0)
    state = dict(load_file(str(path), device='cpu'))
    discarded = []
    for key in ('classifier.weight', 'classifier.bias'):
        if key in state and key not in model.state_dict():
            discarded.append(key)
            del state[key]
    model.load_state_dict(state, strict=True)
    return model, {'checkpoint': str(path), 'checkpoint_sha256': expected_sha256,
                   'discarded_pretraining_head_keys': discarded, 'weight_loading': 'strict',
                   'timm_version': timm.__version__}


class HyTexOnlineAdapter:
    def __init__(self, backbone, head, labels, device='cpu'):
        self.labels = tuple(labels)
        if len(self.labels) < 2 or len(set(self.labels)) != len(self.labels):
            raise ValueError('distinct explicit class mapping required')
        self.device = torch.device(device)
        if self.device.type not in ('cpu', 'cuda'):
            raise ValueError('only CPU and CUDA supported')
        self.backbone = backbone.to(device=self.device, dtype=torch.float32).eval()
        self.backbone.requires_grad_(False)
        self.head = None if head is None else head.to(device='cpu', dtype=torch.float32).eval()
        if self.head is not None:
            self.head.requires_grad_(False)

    @classmethod
    def from_offline(cls, checkpoint_sha256, labels, device='cuda', head_path=None, head_sha256=None):
        if head_path is not None:
            checked_sha256(head_path, head_sha256)
        model, info = load_offline_model(checkpoint_sha256)
        head = None
        if head_path is not None:
            head = HyTexFusionHead(len(labels))
            head.load_state_dict(torch.load(head_path, map_location='cpu', weights_only=True), strict=True)
        adapter = cls(model, head, labels, device)
        adapter.provenance = {**info, 'method': 'HyTexNet adapted; local fixed configuration',
                              'head_sha256': head_sha256, 'head_device': 'cpu',
                              'backbone_device': str(adapter.device), 'precision': 'float32',
                              'feature_cache': False}
        return adapter

    def _synchronize(self):
        if self.device.type == 'cuda':
            torch.cuda.synchronize(self.device)

    @torch.inference_mode()
    def extract_file(self, path):
        with Image.open(path) as source:
            with source.convert('RGB') as rgb:
                with rgb.resize((128, 128), Image.Resampling.BILINEAR) as resized:
                    pixels = np.array(resized, dtype=np.uint8, copy=True)
        gray = np.asarray(pixels, dtype=np.float64) @ np.asarray([.299, .587, .114])
        local = torch.from_numpy(hytex_descriptor(gray)).unsqueeze(0)
        batch = torch.from_numpy(pixels).permute(2, 0, 1).float().div(255.)
        mean = torch.tensor([.485, .456, .406]).view(3, 1, 1)
        std = torch.tensor([.229, .224, .225]).view(3, 1, 1)
        batch = ((batch - mean) / std).unsqueeze(0).to(self.device)
        deep = self.backbone(batch).to('cpu', dtype=torch.float32)
        return fuse_features(deep, local)

    @torch.inference_mode()
    def predict_file(self, path):
        if self.head is None:
            raise ValueError('trained head required before prediction')
        self._synchronize()
        started = perf_counter_ns()
        features = self.extract_file(path)
        logits = self.head(features)
        if logits.shape != (1, len(self.labels)) or not torch.isfinite(logits).all():
            raise ValueError('invalid classifier logits')
        prediction = self.labels[int(logits.argmax(dim=1).item())]
        self._synchronize()
        elapsed = perf_counter_ns() - started
        return {'prediction': prediction, 'logits': logits[0].tolist(),
                'elapsed_ns': elapsed, 'elapsed_ms': elapsed / 1e6}
