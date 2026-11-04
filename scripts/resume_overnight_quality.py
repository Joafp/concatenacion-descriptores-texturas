"""Resume only never-dispatched quality jobs after the original worker exits."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from overnight_local_panel import alive, digest, read, worker, write


def eligible(job):
    if job["quality_hold"] or job["quality_external_managed"]:
        return False
    # Any previous attempt/partial result excludes automatic continuation.
    return not any(p.exists() for p in (
        Path(job["job_dir"]) / "quality_state.json", Path(job["quality_run"]), Path(job["quality_audit"])))


def build(original, folder):
    jobs = []
    for job in original["jobs"]:
        if not eligible(job):
            continue
        directory = folder / "jobs" / job["id"]
        directory.mkdir(parents=True, exist_ok=False)
        jobs.append(dict(job, job_dir=str(directory), quality_run=str(directory / "quality"),
                         quality_audit=str(directory / "quality_audit")))
    return dict(original, jobs=jobs, conditions=len(jobs),
                scope="quality continuation of never-dispatched jobs only; not a complete panel")


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    state_path = args.output / "continuation.json"
    state = {"status": "waiting_for_original_quality_worker", "pid": os.getpid(),
             "original": str(args.original), "original_sha256": digest(args.original),
             "source_sha256": digest(__file__), "started_utc": datetime.now(timezone.utc).isoformat(),
             "hours_after_handoff": args.hours, "no_auto_retry": True}
    write(state_path, state)
    origin_state = args.original.parent / "worker_quality.json"
    while alive(read(origin_state).get("pid")):
        time.sleep(30)
    prior = read(origin_state)
    if prior.get("status") != "dispatch_window_ended":
        state.update(status="requires_review", reason="original worker did not close its dispatch window normally")
        write(state_path, state)
        return
    original = read(args.original)
    if (digest(__file__) != state["source_sha256"]
            or digest(args.original) != state["original_sha256"]
            or any(digest(ROOT / p) != sha for p, sha in original["source_sha256"].items())):
        state.update(status="requires_review", reason="source or manifest drift; no jobs dispatched")
        write(state_path, state)
        return
    pending = [j for j in original["jobs"] if eligible(j)]
    if any(digest(j["config"]) != j["config_sha256"] for j in pending):
        state.update(status="requires_review", reason="pending config drift; no jobs dispatched")
        write(state_path, state)
        return
    manifest = build(original, args.output)
    manifest.update(original_manifest=str(args.original), original_manifest_sha256=digest(args.original))
    manifest["source_sha256"]["scripts/resume_overnight_quality.py"] = digest(__file__)
    for name in ("scripts/overnight_local_panel.py", "docs/fsc_tex/PROTOCOLO_COLA_NOCTURNA_2026-10-28.md"):
        manifest["source_sha256"][name] = digest(ROOT / name)
    write(args.output / "manifest.json", manifest)
    state.update(status="no_pending_jobs" if not pending else "running_quality_continuation",
                 conditions=len(pending), ids=[j["id"] for j in pending])
    write(state_path, state)
    if pending:
        worker(args.output, "quality", args.hours)
        state.update(status="quality_worker_returned", finished_utc=datetime.now(timezone.utc).isoformat())
        write(state_path, state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hours", type=float, default=3.)
    args = parser.parse_args()
    args.original, args.output = args.original.resolve(), args.output.resolve()
    run(args)
