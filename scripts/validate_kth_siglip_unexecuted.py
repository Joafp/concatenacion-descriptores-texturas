#!/usr/bin/env python3
"""Repair loading-report serialization; run only SigLIP, which had zero forwards."""
from pathlib import Path
import argparse
import json
import sys

import validate_kth_reference_recipe as bench

ROOT = Path(__file__).resolve().parents[1]
PARENT = Path("results/analysis/kth_reference_validation_20261115_v1")
ORIGINAL_VERIFY = bench.verify_authorization
ORIGINAL_DUMP = bench.dump


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return [json_safe(item) for item in sorted(value)]
    if isinstance(value, (tuple, list)):
        return [json_safe(item) for item in value]
    return value


def verify_unexecuted_parent(parent):
    if (parent.get("status") != "infrastructure_error" or parent.get("active_block") != "siglip_base"
            or parent.get("phase") != "model_loading" or parent.get("evaluated_calls") != 33
            or parent.get("warmup_calls") != 5 or parent.get("neural_forward_calls_invoked") != 38
            or "Object of type set is not JSON serializable" not in parent.get("error", "")
            or set(parent.get("blocks", {})) != {"eva02_base"}):
        raise ValueError("parent does not demonstrate zero SigLIP forwards; do not resume")
    eva = parent["blocks"]["eva02_base"]
    if eva["n_timed_images"] != 33 or eva["min_reference_cosine"] < .999:
        raise ValueError("parent EVA is not completely accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--author-decision", type=Path, required=True)
    args = parser.parse_args()
    parent = json.loads((ROOT / PARENT / "status.json").read_text())
    verify_unexecuted_parent(parent)
    for name, expected in parent["outputs_sha256"].items():
        if bench.sha(ROOT / PARENT / name) != expected:
            raise ValueError(f"parent evidence changed: {name}")

    def verify(proposal, decision):
        p = ORIGINAL_VERIFY(proposal, decision)
        bench.BLOCKS = ["siglip_base"]
        return p

    def dump(path, value):
        value = json_safe(value)
        if Path(path).name == "protocol_frozen.json":
            value.update(unexecuted_only="siglip_base", accepted_eva_not_repeated=True,
                         infrastructure_fix="JSON serialization of loading-info sets only; no model or preprocessing change",
                         parent=str(PARENT), parent_status_sha256=bench.sha(ROOT / PARENT / "status.json"))
            value["source_sha256"].update({str(Path(__file__).relative_to(ROOT)): bench.sha(__file__),
                                          "tests/test_validate_kth_siglip_unexecuted.py": bench.sha(ROOT / "tests/test_validate_kth_siglip_unexecuted.py")})
        ORIGINAL_DUMP(path, value)

    bench.verify_authorization = verify
    bench.dump = dump
    bench.run(args.output.resolve(), args.author_decision.resolve())


if __name__ == "__main__":
    bench.os.environ["HF_HUB_OFFLINE"] = "1"
    bench.os.environ["TRANSFORMERS_OFFLINE"] = "1"
    main()
