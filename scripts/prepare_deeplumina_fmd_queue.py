"""New independent FMD adaptation queue for DeepLumina; reuse verified FMD partitions."""
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from consolidate_overnight_online_panel import digest, read
from prepare_neshov_fmd_external import validate_partition
from deeplumina_reference import CHECKPOINT_SHA, METHOD, MODEL_NAME


def prepare(output):
    from huggingface_hub import hf_hub_download

    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    path = ROOT / "results/analysis/neshov_fmd_external_preflight_20261102_v1/manifest.json"
    partitions = read(path)
    for source, expected in partitions["source_sha256"].items():
        if digest(source) != expected:
            raise ValueError("partition preflight source drift: " + source)
    conditions = partitions["conditions"]
    if len(conditions) != 15:
        raise ValueError("15 conditions required")
    manifest_path = Path(conditions[0]["manifest"])
    with manifest_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    for p in conditions:
        if (
            Path(p["manifest"]) != manifest_path
            or validate_partition(p["training_indices"], p["external_indices"], rows) != p["labels"]
        ):
            raise ValueError("partition or label mapping disagreement")
    for row in rows:
        if digest(ROOT / row["path"]) != row["sha256"]:
            raise ValueError("image drift")
    checkpoint = Path(
        hf_hub_download("timm/" + MODEL_NAME, "model.safetensors", local_files_only=True)
    )
    if digest(checkpoint) != CHECKPOINT_SHA:
        raise ValueError("backbone drift")
    names = [
        "src/deeplumina_reference.py",
        "src/deeplumina_online_adapter.py",
        "src/neshov_online_adapter.py",
        "scripts/run_deeplumina_external_condition.py",
        "scripts/run_neshov_external_condition.py",
        "scripts/consolidate_overnight_online_panel.py",
        "scripts/prepare_deeplumina_fmd_queue.py",
        "scripts/prepare_neshov_fmd_external.py",
        "scripts/run_authorized_remediation_queue.py",
        "docs/fsc_tex/PROTOCOLO_DEEPLUMINA_ADAPTACION_FMD_2026-11-03.md",
    ]
    sources = {str(ROOT / n): digest(ROOT / n) for n in names}
    sources.update(
        {
            str(path): digest(path),
            str(manifest_path): digest(manifest_path),
            str(checkpoint): CHECKPOINT_SHA,
        }
    )
    preflight = {
        "status": "DEEPLUMINA_FMD_ADAPTATION_FROZEN_NOT_EXECUTED",
        "conditions": conditions,
        "source_sha256": sources,
        "unique_conditions": 15,
        "planned_online_calls": 3000,
        "unique_images_hashed": len(rows),
        "checkpoint_sha256": CHECKPOINT_SHA,
        "checkpoint": str(checkpoint),
        "method": METHOD,
    }
    output.mkdir(parents=True, exist_ok=False)
    frozen = output / "preflight.json"
    frozen.write_text(json.dumps(preflight, indent=2) + "\n")
    tasks = []
    for number, p in enumerate(conditions):
        name = f'DeepLumina_FMD_s{p["seed"]}_f{p["outer_fold"]}'
        job = output / "jobs" / name
        commands = []
        for stage, timeout in [("extract", 7200), ("train", 1800), ("online", 14400), ("audit", 300)]:
            commands.append(
                {
                    "argv": [
                        sys.executable,
                        str(ROOT / "scripts/run_deeplumina_external_condition.py"),
                        "--manifest",
                        str(frozen),
                        "--number",
                        str(number),
                        "--stage",
                        stage,
                        "--job",
                        str(job),
                    ],
                    "timeout_seconds": timeout,
                    "success": {
                        "path": str(job / stage / "status.json"),
                        "fields": {"status": stage + "_complete"},
                    },
                }
            )
        tasks.append(
            {
                "id": name,
                "lane": "gpu",
                "depends_on": [] if not tasks else [tasks[0]["id"]],
                "observe": False,
                "exclusive_outputs": [str(job / s) for s in ("extract", "train", "online", "audit")],
                "commands": commands,
            }
        )
    manifest = {
        "schema": 1,
        "no_auto_retry": True,
        "python_version": sys.version,
        "source_sha256": {**sources, str(frozen): digest(frozen)},
        "gpu_lock": "results/analysis/gpu.lock",
        "tasks": tasks,
        "packages": {
            p: importlib.metadata.version(p)
            for p in (
                "numpy",
                "torch",
                "torchvision",
                "timm",
                "Pillow",
                "huggingface-hub",
                "safetensors",
                "scikit-learn",
            )
        },
        "scope": preflight["method"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"tasks": len(tasks), "manifest_sha256": digest(output / "manifest.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    prepare(parser.parse_args().output)
