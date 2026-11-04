"""Independent DeepLumina dataset queues from frozen common-panel partitions."""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from consolidate_overnight_online_panel import digest, read
from run_authorized_remediation_queue import verify_sources
from deeplumina_reference import CHECKPOINT_SHA, METHOD, MODEL_NAME
from prepare_cellnn_dataset_queue import DATASETS, validate


def prepare(dataset, output):
    from huggingface_hub import hf_hub_download

    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    slug, n, calls, classes, nrows = DATASETS[dataset]
    previous = ROOT / f"results/analysis/hytex_{slug}_external_queue_20261102_v1"
    original, worker, old = [
        read(previous / f) for f in ("manifest.json", "gpu.json", "preflight.json")
    ]
    if worker["status"] != "all_tasks_terminal" or worker["manifest_sha256"] != digest(
        previous / "manifest.json"
    ):
        raise ValueError("frozen partition source queue required")
    verify_sources(original)
    parts = []
    for p in old["conditions"]:
        clean = {k: v for k, v in p.items() if k not in ("training_seed", "epochs", "head_batch")}
        parts.append(clean)
    mp = Path(parts[0]["manifest"])
    if any(Path(p["manifest"]) != mp for p in parts):
        raise ValueError("different manifests")
    with mp.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    validate(dataset, parts, rows)
    for r in rows:
        if digest(ROOT / r["path"]) != r["sha256"]:
            raise ValueError("image drift")
    previous_dl = ROOT / "results/analysis/deeplumina_fmd_external_queue_20261103_v1/manifest.json"
    base = read(previous_dl)
    verify_sources(base)
    sources = dict(base["source_sha256"])
    for f in (
        previous_dl,
        previous / "manifest.json",
        previous / "preflight.json",
        previous / "gpu.json",
        mp,
    ):
        sources[str(f)] = digest(f)
    sources.update(original["source_sha256"])
    sources[str(ROOT / "scripts/prepare_deeplumina_dataset_queue.py")] = digest(
        ROOT / "scripts/prepare_deeplumina_dataset_queue.py"
    )
    checkpoint = Path(
        hf_hub_download("timm/" + MODEL_NAME, "model.safetensors", local_files_only=True)
    )
    if digest(checkpoint) != CHECKPOINT_SHA:
        raise ValueError("checkpoint drift")
    output.mkdir(parents=True, exist_ok=False)
    target = output / "preflight.json"
    target.write_text(
        json.dumps(
            {
                "status": "DEEPLUMINA_NEW_DATASET_FROZEN_NOT_EXECUTED",
                "dataset": dataset,
                "conditions": parts,
                "source_sha256": sources,
                "unique_conditions": n,
                "planned_online_calls": calls,
                "unique_images_hashed": nrows,
                "checkpoint": str(checkpoint),
                "checkpoint_sha256": CHECKPOINT_SHA,
                "method": METHOD,
                "partition_source_only": str(previous),
            },
            indent=2,
        )
        + "\n"
    )
    tasks = []
    for number, p in enumerate(parts):
        name = f'DeepLumina_{dataset}_s{p["seed"]}_f{p["outer_fold"]}'
        job = output / "jobs" / name
        commands = []
        for stage, timeout in [("extract", 14400), ("train", 3600), ("online", 14400), ("audit", 300)]:
            commands.append(
                {
                    "argv": [
                        sys.executable,
                        str(ROOT / "scripts/run_deeplumina_external_condition.py"),
                        "--manifest",
                        str(target),
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
        **base,
        "source_sha256": {**sources, str(target): digest(target)},
        "tasks": tasks,
        "scope": dataset + ": " + METHOD,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"dataset": dataset, "tasks": n, "manifest_sha256": digest(output / "manifest.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    prepare(a.dataset, a.output)
