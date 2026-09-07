#!/usr/bin/env python3
"""Sequential, checkpointed re-extraction of confirmatory CUReT descriptors."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


EXTRACTORS = (
    "convnext_v2_t", "deit_s", "densenet121", "dinov2", "dinov2_large",
    "dinov2_small", "drlbp", "efficientnet_b0", "eva02_base", "gabor",
    "glcm", "hog", "lbp", "mae_base", "resnet101", "resnet50",
    "siglip_base", "swin_t", "vgg16", "vit_b16",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument(
        "--extractors",
        nargs="+",
        choices=EXTRACTORS,
        default=list(EXTRACTORS),
        help="Optional ordered subset to run; completed metadata checkpoints are skipped.",
    )
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")

    repo = args.repo.resolve()
    output = repo / "embeddings_confirmatory" / "CUReT"
    logs = repo / "results" / "confirmatory" / "logs" / "reextract_CUReT"
    output.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    manifest = repo / "results" / "confirmatory" / "sample_manifests" / "CUReT.csv"
    script = repo / "src" / "reextract_confirmatory_embeddings.py"
    python = repo / ".venv-confirmatory" / "bin" / "python"

    for extractor in args.extractors:
        metadata = output / f"{extractor}_metadata.json"
        if metadata.exists():
            print(f"RESUME skip {extractor}", flush=True)
            continue
        command = [
            str(python), str(script),
            "--manifest", str(manifest),
            "--extractor", extractor,
            "--output", str(output),
            "--batch-size", str(args.batch_size),
        ]
        started = time.time()
        completed = subprocess.run(command, cwd=repo, text=True, capture_output=True)
        record = {
            "extractor": extractor,
            "command": command,
            "returncode": completed.returncode,
            "elapsed_seconds": time.time() - started,
            "stdout": completed.stdout[-8000:],
            "stderr": completed.stderr[-8000:],
        }
        log_path = logs / f"{extractor}.json"
        log_path.write_text(json.dumps(record, indent=2) + "\n")
        if completed.returncode:
            print(completed.stderr, file=sys.stderr)
            raise SystemExit(f"FAILED {extractor}; see {log_path}")
        print(f"COMPLETE {extractor} ({record['elapsed_seconds']:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
