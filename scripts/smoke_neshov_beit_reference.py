"""CPU-only functional check on two development-fit images; not a quality/timing run."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "STARTED", "device": "cpu", "head_trained": False,
              "quality_evaluated": False, "external_test_evaluated": False,
              "physical_latency_published": False, "functional_check_only": True}

    def save():
        (output / "status.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    save()
    try:
        import torch
        from PIL import Image
        from neshov_beit_reference import (FrozenLayerAggregation, ReferenceMLP,
                                           preprocessing, load_offline_backbone, PAPER_LAYERS)
        torch.set_num_threads(2)
        torch.manual_seed(42)
        torch.use_deterministic_algorithms(True)
        fold_path = ROOT / "results/exploratory/integration_v11/replication_20261026/FMD_s42/paired/fold0.json"
        manifest = ROOT / "results/confirmatory/sample_manifests/FMD.csv"
        fold = json.loads(fold_path.read_text())
        indices = fold["fit_indices"][:2]
        assert not set(indices) & set(fold["validation_indices"])
        with manifest.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        transform, images, sources = preprocessing(), [], {}
        for idx in indices:
            row = rows[idx]
            path = Path(row.get("source_path") or row["path"])
            if not path.is_absolute():
                path = ROOT / path
            expected = row.get("source_sha256") or row.get("sha256")
            assert expected and digest(path) == expected, str(path)
            sources[str(path)] = expected
            with Image.open(path) as image:
                images.append(transform(image.convert("RGB")))
        print("Loading local BEiTv2 weights, no GPU and no downloads", flush=True)
        backbone, weights = load_offline_backbone()
        report.update(weights=weights, layers_one_based=list(PAPER_LAYERS),
                      torch_version=torch.__version__, selected_fit_rows=indices)
        save()
        print("Extracting four intermediate representations from two fit images", flush=True)
        extractor = FrozenLayerAggregation(backbone).eval()
        x = torch.stack(images)
        features = extractor(x)
        head = ReferenceMLP(3072, 10).eval()
        with torch.inference_mode():
            logits = head(features)
            probabilities = logits.softmax(dim=1)
        assert tuple(features.shape) == (2, 3072)
        assert tuple(logits.shape) == (2, 10)
        assert torch.isfinite(features).all() and torch.isfinite(logits).all()
        assert torch.allclose(probabilities.sum(dim=1), torch.ones(2))
        assert not any(p.requires_grad for p in backbone.parameters())
        report.update(status="FUNCTIONAL_SMOKE_PASSED_NOT_A_REPLICATION_RESULT",
                      feature_shape=list(features.shape), logit_shape=list(logits.shape),
                      backbone_parameters=sum(p.numel() for p in backbone.parameters()),
                      head_parameters=sum(p.numel() for p in head.parameters()),
                      checkpoint_sha256=digest(weights["local_weight_path"]),
                      source_sha256={str(manifest): digest(manifest), str(fold_path): digest(fold_path),
                                     str(ROOT / "src/neshov_beit_reference.py"): digest(ROOT / "src/neshov_beit_reference.py"),
                                     str(Path(__file__)): digest(__file__), **sources},
                      limitations=["Untrained head; no F1 or accuracy claim",
                                   "One-based layer interpretation and pooling choices documented",
                                   "No original-author implementation/output available for parity",
                                   "Software versions and development split differ from paper"])
        save()
        print(json.dumps({k: report[k] for k in ("status", "feature_shape", "logit_shape", "head_trained", "physical_latency_published")}), flush=True)
    except Exception as exc:
        report.update(status="FAILED_NO_AUTOMATIC_RETRY", error=f"{type(exc).__name__}: {exc}")
        save()
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run(args.output)
