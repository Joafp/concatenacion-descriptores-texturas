"""Replay the validated historical DeiT pooler, never silently replace it by CLS."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def verified_state_path(diagnostic_path):
    path = Path(diagnostic_path).resolve()
    evidence = json.loads(path.read_text())
    checks = evidence.get("checks", [])
    if (evidence.get("status") != "diagnostic_complete"
            or evidence.get("seed") != 42 or evidence.get("tolerance") != 1e-4
            or evidence.get("all_rows_pass") is not True or len(checks) != 2
            or any(c.get("pass") is not True or not c.get("same_shape") or not c.get("finite")
                   or c.get("max_abs_error", float("inf")) > 1e-4 for c in checks)):
        raise ValueError("DeiT reconstruction lacks passing original-tolerance evidence")
    state_path = path.with_name("pooler_state.pt")
    if hashlib.sha256(state_path.read_bytes()).hexdigest() != evidence.get("pooler_state_sha256"):
        raise ValueError("reconstructed pooler state hash mismatch")
    return state_path, evidence


def load_reconstructed_deit(diagnostic_path, device):
    import torch

    state_path, evidence = verified_state_path(diagnostic_path)
    legacy_path = ROOT / "src/01_extract_features.py"
    if hashlib.sha256(legacy_path.read_bytes()).hexdigest() != evidence["legacy_source_sha256"]:
        raise ValueError("legacy extractor source drift")
    spec = importlib.util.spec_from_file_location("reconstructed_deit_legacy", legacy_path)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    # Preserve caller RNG; reconstruct the recovered parameters explicitly,
    # rather than depend on unrelated model initialization order.
    with torch.random.fork_rng(devices=[]):
        ext = legacy.get_extractor("deit_s", device=device)
    state = torch.load(state_path, map_location="cpu", weights_only=True)
    if set(state) != {"pooler.dense.weight", "pooler.dense.bias"}:
        raise ValueError("unexpected recovered state; only the validated pooler may be restored")
    ext.model.pooler.load_state_dict({k.removeprefix("pooler."): v for k, v in state.items()}, strict=True)
    ext.model.eval()

    def extract(image):
        inputs = ext.processor(images=[image], return_tensors="pt").to(device)
        with torch.inference_mode():
            vector = ext.model(**inputs).pooler_output.cpu().numpy().ravel().astype(np.float32)
        return vector / max(float(np.linalg.norm(vector)), 1e-12)

    return extract
