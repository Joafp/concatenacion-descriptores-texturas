#!/usr/bin/env python3
"""Measure only blocks never executed after the terminal EVA-02 parity failure."""
from pathlib import Path
import json
import sys

import benchmark_kth_top4_components as bench

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "results/analysis/kth_top4_component_profile_20261115_v2/status.json"
parent = json.loads(PARENT.read_text())
if parent["status"] != "requires_review" or "eva02_base" not in parent["blocks"]:
    raise RuntimeError("unexpected parent audit state")
remaining = ["convnext_v2_t", "siglip_base"]
if any(b in parent["blocks"] for b in remaining):
    raise RuntimeError("cannot repeat an executed block")
bench.BLOCKS = {k: bench.BLOCKS[k] for k in remaining}
original_dump = bench.dump


def dump(path, value):
    if Path(path).name == "protocol_frozen.json":
        value.update(parent_profile=str(PARENT.relative_to(ROOT)), parent_sha256=bench.sha(PARENT),
                     wrapper_sha256=bench.sha(Path(__file__)),
                     failed_block_not_repeated="eva02_base", allowed_unexecuted_blocks=remaining)
    original_dump(path, value)


if __name__ == "__main__":
    bench.dump = dump
    bench.os.environ["HF_HUB_OFFLINE"] = "1"
    bench.os.environ["TRANSFORMERS_OFFLINE"] = "1"
    bench.main()
