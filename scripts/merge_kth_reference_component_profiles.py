#!/usr/bin/env python3
"""Index accepted EVA/SigLIP calls from separate sessions without remeasuring either."""
import argparse
import json
from pathlib import Path
import shutil
import math

from validate_kth_reference_recipe import sha, dump, ROOT
from validate_kth_siglip_unexecuted import verify_unexecuted_parent


def validate_calls(calls, block, samples):
    if len(calls) != 33 or [r["row_id"] for r in calls] != [r["row_id"] for r in samples]:
        raise ValueError("call order or coverage differs from the 33 frozen images")
    for call, sample in zip(calls, samples, strict=True):
        if call.get("status") != "accepted" or not math.isfinite(call["reference_cosine"]) or call["reference_cosine"] < .999:
            raise ValueError("individual call does not pass fidelity")
        if call["input_pixel_sha256"] != sample["candidate_input_sha256"][block]:
            raise ValueError("call did not use the frozen candidate input")
        if not math.isfinite(call["ms"]) or call["ms"] <= 0:
            raise ValueError("invalid component timing")


def merge(eva_folder, siglip_folder, output):
    if output.exists():
        raise FileExistsError("new accepted-profile directory required")
    eva = json.loads((eva_folder / "status.json").read_text())
    siglip = json.loads((siglip_folder / "status.json").read_text())
    verify_unexecuted_parent(eva)
    if (siglip["status"] != "complete" or set(siglip["blocks"]) != {"siglip_base"}
            or siglip["evaluated_calls"] != 33 or siglip["warmup_calls"] != 5
            or siglip["neural_forward_calls_invoked"] != 38):
        raise ValueError("SigLIP does not have complete, single-session accepted coverage")
    sources = {}
    for folder, status in [(eva_folder, eva), (siglip_folder, siglip)]:
        sources[str((folder / "status.json").relative_to(ROOT))] = sha(folder / "status.json")
        for name, expected in status["outputs_sha256"].items():
            if sha(folder / name) != expected:
                raise ValueError(f"source changed: {folder/name}")
            sources[str((folder / name).relative_to(ROOT))] = expected
    blocks = {"eva02_base": eva["blocks"]["eva02_base"], "siglip_base": siglip["blocks"]["siglip_base"]}
    for block, row in blocks.items():
        if row["min_reference_cosine"] < .999 or row["n_timed_images"] != 33:
            raise ValueError(f"incomplete/failed block: {block}")
    proposal = json.loads((ROOT / "results/analysis/kth_reference_validation_proposal_20261115_v1/proposal.json").read_text())
    for block, folder in [("eva02_base", eva_folder), ("siglip_base", siglip_folder)]:
        calls = json.loads((folder / f"{block}_calls.json").read_text())
        validate_calls(calls, block, proposal["images"])
        if min(r["reference_cosine"] for r in calls) != blocks[block]["min_reference_cosine"]:
            raise ValueError("reported minimum cosine differs from per-image calls")
    for relative, expected in proposal["existing_status_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"original failure state changed: {relative}")
    output.mkdir(parents=True, exist_ok=False)
    frozen = {"sources": sources, "script_sha256": sha(__file__),
              "tests_sha256": sha(ROOT / "tests/test_merge_kth_reference_profiles.py"), "minimum_cosine": .999,
              "method": "reference historical preprocessing and representation, pinned weights",
              "timing_sessions": {"eva02_base": str(eva_folder.relative_to(ROOT)),
                                  "siglip_base": str(siglip_folder.relative_to(ROOT))},
              "distinct_timing_sessions": True, "scientific_calls_repeated": 0,
              "infrastructure_correction": "sets in model-loading report serialized as sorted lists before first SigLIP forward"}
    dump(output / "protocol_frozen.json", frozen)
    for block, folder in [("eva02_base", eva_folder), ("siglip_base", siglip_folder)]:
        shutil.copyfile(folder / f"{block}_calls.json", output / f"{block}_calls.json")
    status = {"status": "complete", "blocks": blocks, "evaluated_calls": 66, "warmup_calls": 10,
              "neural_forward_calls_invoked": 76, "minimum_cosine": .999,
              "scope": "accepted component profile from two explicit sessions; not online policy latency",
              "protocol_sha256": sha(output / "protocol_frozen.json"), "source_statuses_preserved": True}
    dump(output / "profile.json", status)
    status["outputs_sha256"] = {f.name: sha(f) for f in output.iterdir() if f.is_file()}
    dump(output / "status.json", status)
    print(json.dumps({block: {k: v for k, v in row.items() if k in ["min_reference_cosine", "mean_ms", "n_timed_images"]}
                      for block, row in blocks.items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eva-folder", type=Path, required=True)
    parser.add_argument("--siglip-folder", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    merge(args.eva_folder.resolve(), args.siglip_folder.resolve(), args.output.resolve())
