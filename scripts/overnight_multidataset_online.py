"""Supplemental online queue after FMD, preserving the original ledger and holds."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from diagnose_deit_dataset_binding import benchmarks_active


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def fmd_closed(manifest):
    jobs = [j for j in manifest["jobs"] if j["dataset"] == "FMD"]
    if len(jobs) != 30:
        raise ValueError("expected thirty FMD conditions")
    for job in jobs:
        status_path = Path(job["online_run"]) / "status.json"
        audit_path = Path(job["online_audit"]) / "audit.json"
        if not status_path.exists() or not audit_path.exists():
            return False
        if read(status_path).get("status") != "batch1_online_f1_and_timing_complete":
            return False
        audit = read(audit_path)
        if audit.get("status") != "ONLINE_CALL_RECORDS_REAGGREGATED" or audit.get("source_status_sha256") != digest(status_path):
            return False
    return True


def quality_ready(job):
    status_path = Path(job["quality_run"]) / "status.json"
    audit_path = Path(job["quality_audit"]) / "audit.json"
    return (status_path.exists() and audit_path.exists()
        and read(status_path).get("status") == "external_quality_complete_timing_pending"
        and read(audit_path).get("status") == "CACHED_HEAD_PREDICTIONS_REPLAYED"
        and read(audit_path).get("source_status_sha256") == digest(status_path))


def prepare(args):
    original = read(args.original)
    # The original worker cannot dispatch these jobs: its immutable gates stay set.
    jobs = [j for j in original["jobs"] if j["dataset"] not in {"FMD", "KTHTIPS2b"}]
    if len(jobs) != 56 or any(j["online_hold"] != "dataset_adapter_binding_review" for j in jobs):
        raise ValueError("unexpected supplemental scope or original gate state")
    args.folder.mkdir(parents=True, exist_ok=False)
    (args.folder / "jobs").mkdir()
    (args.folder / "bindings").mkdir()
    updated = []
    for job in jobs:
        directory = args.folder / "jobs" / job["id"]
        directory.mkdir()
        updated.append(dict(job, online_run=str(directory / "online"),
                            online_audit=str(directory / "online_audit"), job_dir=str(directory)))
    sources = dict(original["source_sha256"])
    for name in ("scripts/overnight_multidataset_online.py", "scripts/diagnose_deit_dataset_binding.py",
                 "src/local_deit_reconstruction.py"):
        sources[name] = digest(ROOT / name)
    reconstruction = ROOT / "results/analysis/deit_seed42_diagnostic_20261028/diagnostic.json"
    manifest = {"status": "prepared_not_executed", "original": str(args.original),
        "original_sha256": digest(args.original), "source_sha256": sources, "jobs": updated,
        "reconstruction": str(reconstruction), "reconstruction_sha256": digest(reconstruction),
        "protocol_sha256": digest(ROOT / "docs/fsc_tex/PROTOCOLO_COLA_NOCTURNA_2026-10-28.md"),
        "deadline_utc": "2026-10-29T09:42:43+00:00", "no_auto_retry": True,
        "scope": "56 non-FMD/non-KTH online conditions; original frozen scientific recipes; one GPU route at a time"}
    write(args.folder / "manifest.json", manifest)
    print(json.dumps({"status": "prepared_not_executed", "conditions": len(updated)}))


def worker(args):
    manifest_path = args.folder / "manifest.json"
    manifest = read(manifest_path)
    lock = (args.folder / "worker.lock").open("a")
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = {"status": "waiting_for_fmd", "pid": os.getpid(), "completed": [], "requires_review": [],
             "manifest_sha256": digest(manifest_path), "started_utc": datetime.now(timezone.utc).isoformat()}
    state_path = args.folder / "worker.json"
    write(state_path, state)
    env = dict(os.environ, OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2",
               HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    protocol = ROOT / "docs/fsc_tex/PROTOCOLO_COLA_NOCTURNA_2026-10-28.md"
    deadline = datetime.fromisoformat(manifest["deadline_utc"])
    while datetime.now(timezone.utc) < deadline:
        if (digest(manifest_path) != state["manifest_sha256"]
                or digest(protocol) != manifest["protocol_sha256"]
                or digest(manifest["original"]) != manifest["original_sha256"]
                or digest(manifest["reconstruction"]) != manifest["reconstruction_sha256"]
                or any(digest(ROOT / p) != sha for p, sha in manifest["source_sha256"].items())):
            state["status"] = "requires_review_source_drift"
            write(state_path, state)
            return
        if not fmd_closed(read(manifest["original"])) or benchmarks_active():
            state["status"] = "waiting_for_fmd_or_gpu"
            write(state_path, state)
            time.sleep(30)
            continue
        candidate = None
        for job in manifest["jobs"]:
            marker = Path(job["job_dir"]) / "online_state.json"
            if not marker.exists() and quality_ready(job):
                candidate = (job, marker)
                break
        if candidate is None:
            all_done = all((Path(j["job_dir"]) / "online_state.json").exists() for j in manifest["jobs"])
            state["status"] = "all_jobs_terminal" if all_done else "waiting_for_quality"
            write(state_path, state)
            if all_done:
                return
            time.sleep(30)
            continue
        job, marker = candidate
        if digest(job["config"]) != job["config_sha256"]:
            write(marker, {"status": "requires_review", "reason": "configuration drift"})
            state["requires_review"].append(job["id"])
            continue
        diagnostic_dir = args.folder / "bindings" / job["dataset"]
        diagnostic = diagnostic_dir / "diagnostic.json"
        # A partially created diagnostic is a terminal review case, never retried.
        if not diagnostic_dir.exists():
            state.update(status="diagnosing_binding", current_job=job["id"])
            write(state_path, state)
            command = ["timeout", "600", sys.executable, str(ROOT / "scripts/diagnose_deit_dataset_binding.py"),
                "--config", job["config"], "--reconstruction", manifest["reconstruction"],
                "--protocol", str(protocol), "--output", str(diagnostic_dir), "--execute"]
            with (args.folder / "bindings" / f"{job['dataset']}.log").open("x") as handle:
                code = subprocess.run(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT).returncode
            if code and not diagnostic_dir.exists():
                diagnostic_dir.mkdir()
                write(diagnostic, {"status": "diagnostic_launch_failed", "requires_review": True, "exit_code": code})
        evidence = read(diagnostic) if diagnostic.exists() else {}
        if evidence.get("status") != "diagnostic_complete" or evidence.get("all_rows_pass") is not True:
            write(marker, {"status": "requires_review", "reason": "dataset binding did not pass; no benchmark executed",
                           "diagnostic": str(diagnostic)})
            state["requires_review"].append(job["id"])
            write(state_path, state)
            continue
        if Path(job["online_run"]).exists() or Path(job["online_audit"]).exists():
            write(marker, {"status": "requires_review", "reason": "output exists; never overwrite or retry"})
            state["requires_review"].append(job["id"])
            write(state_path, state)
            continue
        if benchmarks_active():
            time.sleep(30)
            continue
        commands = [
            ["timeout", str(job["online_timeout_seconds"]), sys.executable, str(ROOT / "scripts/benchmark_local_single_image.py"),
             "--run", job["quality_run"], "--deit-reconstruction", str(diagnostic), "--protocol", str(protocol),
             "--output", job["online_run"], "--repeats", "1"],
            ["timeout", "300", sys.executable, str(ROOT / "scripts/audit_local_batch1_calls.py"),
             "--online-run", job["online_run"], "--quality-run", job["quality_run"], "--output", job["online_audit"]]]
        state.update(status="running", current_job=job["id"], command=commands[0])
        write(state_path, state)
        write(marker, {"status": "running", "pid": os.getpid(), "id": job["id"]})
        for stage, command in zip(("execute", "audit"), commands):
            with (Path(job["job_dir"]) / f"online_{stage}.log").open("x") as handle:
                code = subprocess.run(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT).returncode
            if code:
                break
        outcome = "complete" if code == 0 else "requires_review"
        write(marker, {"status": outcome, "id": job["id"], "exit_code": code, "stage": stage})
        state["completed" if code == 0 else "requires_review"].append(job["id"])
        write(state_path, state)
    state.update(status="dispatch_window_ended", finished_utc=datetime.now(timezone.utc).isoformat())
    write(state_path, state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "worker"))
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--original", type=Path)
    args = parser.parse_args()
    args.folder = args.folder.resolve()
    if args.mode == "prepare":
        args.original = args.original.resolve()
        prepare(args)
    else:
        worker(args)
