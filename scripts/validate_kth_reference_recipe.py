#!/usr/bin/env python3
"""One authorized KTH reference-recipe validation; terminal failures are not retried."""
from __future__ import annotations

import argparse
import csv
import fcntl
import gc
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from PIL import Image
from reference_preprocessing import eva02_reference_transform, siglip_reference_transform

PROPOSAL = ROOT / "results/analysis/kth_reference_validation_proposal_20261115_v1/proposal.json"
BLOCKS = ["eva02_base", "siglip_base"]


class FidelityFailure(ArithmeticError):
    """Scientific failure: preserve evidence and stop, never retry."""


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def validate_vector(vector, expected, minimum=.999):
    vector, expected = np.asarray(vector, dtype=np.float64), np.asarray(expected, dtype=np.float64)
    if vector.shape != expected.shape or vector.ndim != 1:
        raise FidelityFailure(f"shape mismatch: {vector.shape} versus {expected.shape}")
    if not np.isfinite(vector).all() or not np.isfinite(expected).all():
        raise FidelityFailure("nonfinite embedding or reference")
    denominator = np.linalg.norm(vector) * np.linalg.norm(expected)
    if not np.isfinite(denominator) or denominator <= 0:
        raise FidelityFailure("zero/nonfinite vector norm")
    cosine = float(vector @ expected / denominator)
    if not np.isfinite(cosine) or cosine < minimum:
        raise FidelityFailure(f"reference cosine {cosine} below frozen minimum {minimum}")
    return cosine


def verify_authorization(proposal_path, decision_path):
    p = json.loads(Path(proposal_path).read_text())
    d = json.loads(Path(decision_path).read_text())
    if d.get("proposal_sha256") != sha(proposal_path) or d.get("user_reply") != "SI":
        raise ValueError("missing/mismatched author decision for this frozen proposal")
    if not d.get("execute_corrected_validation") or not d.get("complete_only_two_never_fitted_kth_if_both_pass"):
        raise ValueError("author decision does not cover the proposed continuation")
    if p["blocks_in_fixed_order"] != BLOCKS or p["minimum_cosine_each_image"] != .999:
        raise ValueError("unexpected recipe or scientific acceptance threshold")
    if len(p["images"]) != 33 or p["maximum_evaluated_calls"] != 66 or p["maximum_warmup_calls"] != 10:
        raise ValueError("unexpected frozen call budget")
    return p


def verify_inputs(p):
    for relative, expected in p["source_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"frozen source changed: {relative}")
    for name, expected in p["environment_source_sha256"].items():
        if sha(name) != expected:
            raise ValueError(f"frozen library source changed: {name}")
    for block in p["weights_and_configs"].values():
        for path, record in block["checks"].items():
            if sha(path) != record["expected_sha256"]:
                raise ValueError(f"local frozen weight/config changed: {path}")
    for case in p["continuation_only_if_both_blocks_pass"]["reusable_completed_conditions"].values():
        for name, expected in case["artifacts_sha256"].items():
            if sha(ROOT / case["folder"] / name) != expected:
                raise ValueError(f"completed condition artifact changed: {case['folder']}/{name}")


def check_loading_info(info):
    bad = {k: info.get(k, []) for k in ("missing_keys", "mismatched_keys", "error_msgs") if info.get(k)}
    if bad:
        raise FidelityFailure(f"vision checkpoint is not fully loaded: {bad}")


def build_model(block, record, config):
    """Construct exactly the historical architecture, with pinned local weights."""
    weight = next(Path(name) for name in record["checks"] if name.endswith("model.safetensors"))
    if block == "eva02_base":
        import timm
        from timm.models import load_state_dict
        from timm.models.eva import checkpoint_filter_fn
        model = timm.create_model("eva02_base_patch14_224", pretrained=False, num_classes=0)
        state = checkpoint_filter_fn(load_state_dict(weight), model)
        # No trainable visual parameter is permitted to retain random initialization.
        try:
            info = model.load_state_dict(state, strict=True)
        except RuntimeError as exc:
            raise FidelityFailure(f"EVA checkpoint does not strictly load: {exc}") from exc
        loading = {"missing_keys": list(info.missing_keys), "unexpected_keys": list(info.unexpected_keys),
                   "source": str(weight), "strict": True, "filter": "timm.models.eva.checkpoint_filter_fn"}
        transform = eva02_reference_transform(config["eva_resolved_config_now"])
    else:
        from transformers import SiglipVisionModel
        model, loading = SiglipVisionModel.from_pretrained(
            weight.parent, local_files_only=True, output_loading_info=True)
        check_loading_info(loading)
        transform = siglip_reference_transform(config["siglip_processor_config"])
    return model.eval(), transform, loading


def run(output, decision):
    if output.exists():
        raise FileExistsError("Use a new output folder; scientific failures are never resumed")
    p = verify_authorization(PROPOSAL, decision)
    verify_inputs(p)
    import torch
    versions = {name: importlib.metadata.version(name) for name in
                ["torch", "torchvision", "timm", "transformers", "Pillow", "numpy", "safetensors"]}
    if any(versions[name] != expected for name, expected in p["versions_observed_during_cpu_audit"].items()):
        raise ValueError("runtime libraries differ from the prepared proposal")
    torch.set_num_threads(2)
    native_smi = Path("/mnt/c/Windows/System32/nvidia-smi.exe")
    # WSL's process table can omit Windows graphics clients; inspect the host too.
    gpu_snapshot = subprocess.check_output([str(native_smi) if native_smi.exists() else "nvidia-smi"], text=True)
    if "deadlock.exe" in gpu_snapshot.lower():
        raise RuntimeError("Deadlock is using the GPU; no scientific calls started")
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "preparing", "blocks": {}, "evaluated_calls": 0, "warmup_calls": 0,
              "neural_forward_calls_invoked": 0,
              "minimum_cosine": .999, "scope": "training-image component profile, not policy latency",
              "original_failures_preserved": True, "retry_allowed": False}
    dump(output / "status.json", report)
    try:
        with (ROOT / p["global_lock"]).open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA required; no CPU substitution")
            torch.manual_seed(42)
            torch.cuda.manual_seed_all(42)
            config = json.loads((ROOT / "results/analysis/kth_preprocessing_forensics_20261115_v1/pipeline_configuration.json").read_text())
            with (ROOT / "results/extensions/kth_tips2b/sample_manifests/KTHTIPS2b.csv").open(newline="") as handle:
                manifest = list(csv.DictReader(handle))
            frozen = {"proposal_sha256": sha(PROPOSAL), "author_decision_sha256": sha(decision),
                      "source_sha256": {str(Path(__file__).relative_to(ROOT)): sha(__file__),
                                        "tests/test_validate_kth_reference_recipe.py": sha(ROOT / "tests/test_validate_kth_reference_recipe.py")},
                      "versions": versions, "gpu": torch.cuda.get_device_name(0), "nvidia_smi_before": gpu_snapshot,
                      "cpu_threads": 2, "seed": 42, "batch_size": 1,
                      "timing": "same call; image decode, preprocessing, transfer, forward and CPU vector included; model load, cosine and input-SHA verification excluded",
                      "minimum_cosine": .999, "proposal": p,
                      "model_implementation_sha256": {str(path): sha(path) for path in [
                          ROOT / ".venv-confirmatory/lib/python3.12/site-packages/timm/models/eva.py",
                          ROOT / ".venv-confirmatory/lib/python3.12/site-packages/timm/models/_builder.py"]}}
            dump(output / "author_decision.json", json.loads(decision.read_text()))
            dump(output / "protocol_frozen.json", frozen)
            report.update(status="running", protocol_sha256=sha(output / "protocol_frozen.json"))
            dump(output / "status.json", report)
            for block in BLOCKS:
                report.update(phase="model_loading", active_block=block)
                dump(output / "status.json", report)
                model, transform, loading = build_model(block, p["weights_and_configs"][block], config)
                dump(output / f"{block}_loading_info.json", loading)
                model.to("cuda")
                reference = np.load(ROOT / f"embeddings_extensions/KTH-TIPS2-b/{block}.npy", mmap_mode="r")
                records, vectors = [], []

                def extract(sample):
                    index = sample["row_id"]
                    path = ROOT / manifest[index]["source_path"]
                    torch.cuda.synchronize()
                    started = time.perf_counter()
                    with Image.open(path) as image:
                        pixels = transform(image.convert("RGB"))
                    verify_started = time.perf_counter()
                    actual = hashlib.sha256(pixels.numpy().tobytes()).hexdigest()
                    if actual != sample["candidate_input_sha256"][block]:
                        raise ValueError(f"candidate pixel tensor changed before forward: {block}/{index}")
                    verification_ms = 1000 * (time.perf_counter() - verify_started)
                    with torch.no_grad():
                        batch = pixels.unsqueeze(0).to("cuda")
                        report["neural_forward_calls_invoked"] += 1
                        out = model(batch) if block == "eva02_base" else model(pixel_values=batch)
                        features = out if block == "eva02_base" else out.pooler_output
                        if features is None:
                            raise FidelityFailure("historical pooler_output unavailable")
                        vector = features[0].detach().cpu().numpy()
                    torch.cuda.synchronize()
                    wall_ms = 1000 * (time.perf_counter() - started)
                    return vector, {"row_id": index, "ms": wall_ms - verification_ms,
                                    "raw_wall_ms": wall_ms, "excluded_input_sha_verification_ms": verification_ms,
                                    "input_pixel_sha256": actual}

                report["phase"] = "warmup"
                for sample in p["images"][:5]:
                    report["warmup_calls"] += 1
                    dump(output / "status.json", report)
                    extract(sample)
                report["phase"] = "measurement"
                torch.cuda.reset_peak_memory_stats()
                for sample in p["images"]:
                    report["evaluated_calls"] += 1
                    dump(output / "status.json", report)
                    vector, record = extract(sample)
                    # Save the exact output before testing; a failed case retains its evidence.
                    np.save(output / f"{block}_row{sample['row_id']}.npy", vector, allow_pickle=False)
                    expected = reference[sample["row_id"]]
                    try:
                        record["reference_cosine"] = validate_vector(vector, expected, .999)
                    except FidelityFailure as exc:
                        record.update(status="requires_review", error=str(exc))
                        records.append(record)
                        dump(output / f"{block}_calls.json", records)
                        raise
                    record["status"] = "accepted"
                    records.append(record)
                    vectors.append(vector)
                    dump(output / f"{block}_calls.json", records)
                latencies = [r["ms"] for r in records]
                report["blocks"][block] = {
                    "status": "complete", "n_timed_images": len(records),
                    "min_reference_cosine": min(r["reference_cosine"] for r in records),
                    "mean_ms": float(np.mean(latencies)), "median_ms": float(np.median(latencies)),
                    "p95_ms": float(np.percentile(latencies, 95)),
                    "gpu_peak_allocated_mb": torch.cuda.max_memory_allocated() / 2**20,
                    "calls_sha256": sha(output / f"{block}_calls.json")}
                dump(output / "status.json", report)
                print(f"ACCEPTED {block}: min_cos={report['blocks'][block]['min_reference_cosine']:.9f}, mean_ms={np.mean(latencies):.3f}", flush=True)
                del model, reference, vectors, extract
                gc.collect()
                torch.cuda.empty_cache()
            for relative, expected in p["existing_status_sha256"].items():
                if sha(ROOT / relative) != expected:
                    raise ValueError(f"original failure state changed: {relative}")
            report.update(status="complete", phase="finished", active_block=None)
            dump(output / "profile.json", report)
            report["outputs_sha256"] = {f.name: sha(f) for f in output.iterdir() if f.is_file() and f.name != "status.json"}
            dump(output / "status.json", report)
    except Exception as exc:
        report.update(status="requires_review" if isinstance(exc, FidelityFailure) else "infrastructure_error",
                      error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
        report["outputs_sha256"] = {f.name: sha(f) for f in output.iterdir() if f.is_file() and f.name != "status.json"}
        dump(output / "status.json", report)
        raise


if __name__ == "__main__":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--author-decision", type=Path, required=True)
    args = parser.parse_args()
    run(args.output.resolve(), args.author_decision.resolve())
