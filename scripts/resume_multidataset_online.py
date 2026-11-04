"""Continue never-dispatched physical conditions after the prior GPU worker exits."""
import argparse
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from overnight_local_panel import alive
from overnight_multidataset_online import digest, read, write, worker
from diagnose_deit_dataset_binding import benchmarks_active
from local_deit_reconstruction import verified_state_path


def eligible(job):
    return not any(p.exists() for p in (Path(job["job_dir"]) / "online_state.json",
        Path(job["online_run"]), Path(job["online_audit"])))


def quality_override(job, replacements):
    replacement = replacements.get(job["id"])
    if replacement is None:
        return dict(job)
    if replacement["config_sha256"] != job["config_sha256"] or replacement["config"] != job["config"]:
        raise ValueError("quality continuation has a different scientific config")
    return dict(job, quality_run=replacement["quality_run"], quality_audit=replacement["quality_audit"])


def copy_approved_binding(source, target):
    path = source / "diagnostic.json"
    if not path.exists():
        return False
    evidence = read(path)
    if evidence.get("status") != "diagnostic_complete" or evidence.get("all_rows_pass") is not True:
        return False
    verified_state_path(path)
    shutil.copytree(source, target)
    if any(digest(p) != digest(target / p.name) for p in source.iterdir() if p.is_file()):
        raise ValueError("binding copy drift")
    return True


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    state_path = args.output / "continuation.json"
    state = {"status": "waiting_for_previous_online_worker", "pid": os.getpid(),
        "previous_manifest": str(args.previous / "manifest.json"),
        "previous_manifest_sha256": digest(args.previous / "manifest.json"),
        "source_sha256": digest(__file__), "hours_after_handoff": args.hours,
        "started_utc": datetime.now(timezone.utc).isoformat(), "no_auto_retry": True}
    write(state_path, state)
    prior_state = args.previous / "worker.json"
    while alive(read(prior_state).get("pid")) or benchmarks_active():
        time.sleep(30)
    if read(prior_state).get("status") not in {"dispatch_window_ended", "all_jobs_terminal"}:
        state.update(status="requires_review", reason="previous worker did not finish normally")
        write(state_path, state)
        return
    previous = read(args.previous / "manifest.json")
    if (digest(__file__) != state["source_sha256"]
            or digest(args.previous / "manifest.json") != state["previous_manifest_sha256"]
            or digest(previous["original"]) != previous["original_sha256"]
            or digest(previous["reconstruction"]) != previous["reconstruction_sha256"]
            or digest(ROOT / "docs/fsc_tex/PROTOCOLO_COLA_NOCTURNA_2026-10-28.md") != previous["protocol_sha256"]
            or any(digest(ROOT / p) != sha for p, sha in previous["source_sha256"].items())):
        state.update(status="requires_review", reason="source drift; no continuation dispatched")
        write(state_path, state)
        return
    replacements = {}
    if args.quality_manifest.exists():
        replacements = {j["id"]: j for j in read(args.quality_manifest)["jobs"]}
        state["quality_manifest_sha256"] = digest(args.quality_manifest)
    jobs = []
    (args.output / "jobs").mkdir()
    (args.output / "bindings").mkdir()
    for job in previous["jobs"]:
        if not eligible(job):
            continue
        new = quality_override(job, replacements)
        directory = args.output / "jobs" / job["id"]
        directory.mkdir()
        new.update(job_dir=str(directory), online_run=str(directory / "online"), online_audit=str(directory / "online_audit"))
        jobs.append(new)
    if not jobs:
        state.update(status="no_never_dispatched_jobs", conditions=0)
        write(state_path, state)
        return
    if any(digest(j["config"]) != j["config_sha256"] for j in jobs):
        state.update(status="requires_review", reason="config drift")
        write(state_path, state)
        return
    manifest = dict(previous, jobs=jobs, status="pending_continuation", scope="never-dispatched online jobs only; prior failures excluded",
                    previous_manifest_sha256=state["previous_manifest_sha256"],
                    deadline_utc=(datetime.now(timezone.utc) + timedelta(hours=args.hours)).isoformat())
    manifest["source_sha256"]["scripts/resume_multidataset_online.py"] = digest(__file__)
    for dataset in sorted({j["dataset"] for j in jobs}):
        copy_approved_binding(args.previous / "bindings" / dataset, args.output / "bindings" / dataset)
    write(args.output / "manifest.json", manifest)
    state.update(status="preparing_untried_bindings", conditions=len(jobs), ids=[j["id"] for j in jobs])
    write(state_path, state)
    # Diagnose short outstanding dependencies before starting another long benchmark.
    # Existing failing bindings never enter this queue because their jobs have markers.
    env = dict(os.environ, OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2",
               HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    for dataset in sorted({j["dataset"] for j in jobs}):
        directory = args.output / "bindings" / dataset
        if directory.exists():
            continue
        if benchmarks_active():
            state.update(status="requires_review", reason="unexpected benchmark before preflight; no concurrent diagnostic")
            write(state_path, state)
            return
        job = next(j for j in jobs if j["dataset"] == dataset)
        command = ["timeout", "600", sys.executable, str(ROOT / "scripts/diagnose_deit_dataset_binding.py"),
            "--config", job["config"], "--reconstruction", manifest["reconstruction"],
            "--protocol", str(ROOT / "docs/fsc_tex/PROTOCOLO_COLA_NOCTURNA_2026-10-28.md"),
            "--output", str(directory), "--execute"]
        with (args.output / "bindings" / f"{dataset}.log").open("x") as handle:
            code = subprocess.run(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT).returncode
        if code and not directory.exists():
            directory.mkdir()
            write(directory / "diagnostic.json", {"status": "diagnostic_launch_failed", "requires_review": True, "exit_code": code})
    state.update(status="running_online_continuation")
    write(state_path, state)
    worker(argparse.Namespace(folder=args.output))
    state.update(status="online_worker_returned", finished_utc=datetime.now(timezone.utc).isoformat())
    write(state_path, state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--quality-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hours", type=float, default=3.)
    args = parser.parse_args()
    args.previous, args.quality_manifest, args.output = args.previous.resolve(), args.quality_manifest.resolve(), args.output.resolve()
    run(args)
