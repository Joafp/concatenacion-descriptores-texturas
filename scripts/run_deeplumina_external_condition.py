"""Stages for DeepLumina ADAPTED (ResNet101 fc1000 RGB+YIQ-Y + ECOC-SVM); no retries."""
import argparse
import csv
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_neshov_external_condition import audit_calls, digest, read, utc, verify_artifact
from deeplumina_reference import METHOD, SparseRandomECOCClassifier


def json_scalars(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k: json_scalars(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_scalars(v) for v in value]
    return value


def write(path, data):
    Path(path).write_text(json.dumps(json_scalars(data), indent=2, allow_nan=False) + "\n")


def extract(p, rows, manifest, output):
    from deeplumina_online_adapter import DeepLuminaOnlineAdapter

    adapter = DeepLuminaOnlineAdapter.from_offline(manifest["checkpoint_sha256"], p["labels"])
    features = []
    for number, index in enumerate(p["training_indices"]):
        path = ROOT / rows[index]["path"]
        if digest(path) != rows[index]["sha256"]:
            raise ValueError("training image drift")
        vector = adapter.extract_file(path).numpy()
        if vector.shape != (1, 2000) or not np.isfinite(vector).all():
            raise ValueError("invalid fit feature")
        features.append(vector[0])
        if number % 50 == 0:
            print(f'extracted {number + 1}/{len(p["training_indices"])}', flush=True)
    features = np.asarray(features, dtype=np.float32)
    np.savez_compressed(output / "features.npz", rows=p["training_indices"], features=features)
    comparisons, errors = [], []
    for pos in (0, len(features) - 1):
        index = p["training_indices"][pos]
        again = adapter.extract_file(ROOT / rows[index]["path"]).numpy()[0]
        comparisons.append(again)
        errors.append(float(np.max(np.abs(again - features[pos]))))
    np.savez_compressed(
        output / "parity_vectors.npz",
        cached=features[[0, -1]],
        reextracted=np.asarray(comparisons),
    )
    write(
        output / "parity.json",
        {
            "training_rows": [p["training_indices"][0], p["training_indices"][-1]],
            "max_abs_errors": errors,
            "tolerance": 1e-4,
            "regime": "batch1 vs batch1; DeepLumina ResNet101 fc1000 RGB+YIQ-Y",
        },
    )
    if max(errors) > 1e-4:
        raise ValueError("DeepLumina own-route consistency failed; requires review")
    return {
        "fit_images": len(features),
        "parity_max_abs_error": max(errors),
        "adapter": adapter.provenance,
    }


def train(p, rows, job, output):
    import joblib

    verify_artifact(job / "extract", "extract_complete")
    features = np.load(job / "extract/features.npz", allow_pickle=False)
    if not np.array_equal(features["rows"], p["training_indices"]):
        raise ValueError("fit order drift")
    truth = [int(rows[index]["label"]) for index in p["training_indices"]]
    head = SparseRandomECOCClassifier.fit_from_features(
        features["features"], truth, p["labels"], seed=42, n_candidates=10000
    )
    joblib.dump(head, output / "head.joblib")
    np.save(output / "coding_matrix.npy", head.coding_matrix)
    write(output / "labels.json", list(p["labels"]))
    write(output / "ecoc_metadata.json", head.metadata)
    margins, losses = head.decision_margins_and_losses(features["features"])
    np.savez_compressed(
        output / "training_ecoc_outputs.npz",
        rows=features["rows"],
        margins=margins,
        ecoc_losses=losses,
    )
    return {
        "training_seed": 42,
        "ecoc_metadata": head.metadata,
        "extraction_status_sha256": digest(job / "extract/status.json"),
    }


def online(p, rows, manifest, job, output):
    from deeplumina_online_adapter import DeepLuminaOnlineAdapter

    hs = verify_artifact(job / "train", "train_complete")
    labels = read(job / "train/labels.json")
    if labels != p["labels"]:
        raise ValueError("class mapping drift")
    adapter = DeepLuminaOnlineAdapter.from_offline(
        manifest["checkpoint_sha256"],
        labels,
        head_path=job / "train/head.joblib",
        head_sha256=hs["output_sha256"]["head.joblib"],
    )
    write(
        output / "environment.json",
        {
            "utc": utc(),
            "pid": os.getpid(),
            "platform": platform.platform(),
            "python": sys.version,
            "cpu_threads": 2,
            "hardware_isolated": False,
            "adapter": adapter.provenance,
        },
    )
    for _ in range(5):
        adapter.predict_file(ROOT / rows[p["training_indices"][0]]["path"])
    with (output / "calls.jsonl").open("x") as stream:
        for number, index in enumerate(p["external_indices"]):
            row, timestamp = rows[index], utc()
            path = ROOT / row["path"]
            if digest(path) != row["sha256"]:
                raise ValueError("external image drift")
            result = adapter.predict_file(path)
            stream.write(
                json.dumps(
                    {
                        "row_index": index,
                        "truth": int(row["label"]),
                        "repeat": 0,
                        "started_utc": timestamp,
                        **json_scalars(result),
                    },
                    allow_nan=False,
                )
                + "\n"
            )
            stream.flush()
            if number % 25 == 0:
                print(f'online {number + 1}/{len(p["external_indices"])}', flush=True)
    return {
        "calls": len(p["external_indices"]),
        "warmup_calls_excluded": 5,
        "head_status_sha256": digest(job / "train/status.json"),
    }


def run(manifest_path, number, stage, job):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    os.environ["HF_HUB_OFFLINE"] = "1"
    import torch

    torch.set_num_threads(2)
    torch.manual_seed(42)
    torch.use_deterministic_algorithms(True)
    manifest = read(manifest_path)
    for name, sha in manifest["source_sha256"].items():
        if digest(name) != sha:
            raise ValueError("source drift: " + name)
    p = manifest["conditions"][number]
    with Path(p["manifest"]).open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    job = Path(job)
    output = job / stage
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "running",
        "stage": stage,
        "started_utc": utc(),
        "method": METHOD,
        "partition": p,
        "manifest_sha256": digest(manifest_path),
        "runner_sha256": digest(__file__),
    }
    write(output / "status.json", report)
    try:
        if stage == "extract":
            result = extract(p, rows, manifest, output)
        elif stage == "train":
            result = train(p, rows, job, output)
        elif stage == "online":
            result = online(p, rows, manifest, job, output)
        else:
            result = audit_calls(p, rows, job / "online", output)
            result["method"] = report["method"]
            write(output / "summary.json", result)
        report.update(
            result,
            status=stage + "_complete",
            finished_utc=utc(),
            output_sha256={
                f.name: digest(f) for f in output.iterdir() if f.name != "status.json"
            },
        )
        write(output / "status.json", report)
    except Exception as exc:
        report.update(
            status="requires_review",
            error=f"{type(exc).__name__}: {exc}",
            finished_utc=utc(),
        )
        write(output / "status.json", report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--number", required=True, type=int)
    parser.add_argument("--stage", required=True, choices=["extract", "train", "online", "audit"])
    parser.add_argument("--job", required=True, type=Path)
    args = parser.parse_args()
    run(args.manifest, args.number, args.stage, args.job)
