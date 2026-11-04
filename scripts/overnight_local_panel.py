"""Explicit 94-condition ledger and bounded independent CPU/GPU workers.

Only ready jobs run. Failures are preserved and never automatically retried.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (ProcessLookupError, TypeError, ValueError):
        return False


def prepare(folder):
    import pandas as pd

    folder.mkdir(parents=True, exist_ok=False)
    (folder / "configs").mkdir()
    (folder / "jobs").mkdir()
    source = ROOT / "results/analysis/local_f1_latency_panel_20261028_v2/reference_conditions.csv"
    conditions = pd.read_csv(source)
    if len(conditions) != 94 or conditions.duplicated(["classifier", "dataset", "seed", "outer_fold"]).any():
        raise ValueError("expected unique audited 94-condition panel")
    original_path = ROOT / "results/exploratory/integration_v11/replication_20261026/FMD_s42/paired/metadata.json"
    original = read(original_path)["provenance"]["arguments"]
    paths = {
        "DTD": ("results/confirmatory", None),
        "FMD": ("results/confirmatory", None),
        "CUReT": ("results/confirmatory", None),
        "Outex13Official1360": ("results/extensions/outex13_official1360", "embeddings_extensions"),
        "SoilOriginal": ("results/extensions/soil_original", "embeddings_extensions"),
        "KTHTIPS2b": ("results/extensions/kth_tips2b", "embeddings_extensions"),
    }
    priority = {"FMD": 0, "Outex13Official1360": 1, "SoilOriginal": 2, "CUReT": 3, "DTD": 4, "KTHTIPS2b": 5}
    jobs = []
    for item in conditions.to_dict("records"):
        ds, clf, seed, outer = item["dataset"], item["classifier"], int(item["seed"]), int(item["outer_fold"])
        manifest_root, embedding_root = paths[ds]
        if embedding_root is None:
            embedding_root = "embeddings_confirmatory" if (ROOT / "embeddings_confirmatory" / ds).is_dir() else "embeddings"
        cfg = dict(original, dataset=ds, seed=seed, fold=outer, manifest_root=manifest_root,
            embedding_root=embedding_root, official_split=None, curet_direction=None,
            invert_official_split=False, inner_group_column=None,
            ngram_count_cache=f"{manifest_root}/rgb_ngram_count_cache/{ds}/rgb_ngram_impl1")
        if ds in ("DTD", "Outex13Official1360", "KTHTIPS2b"):
            cfg.update(fold=0, official_split=outer + 1)
        if ds == "CUReT":
            cfg.update(fold=0, curet_direction=("a_to_b" if outer == 0 else "b_to_a"))
        if ds == "KTHTIPS2b":
            cfg.update(invert_official_split=True, inner_group_column="sample")
        key = f"{ds}_{clf}_s{seed}_f{outer}"
        config_path = folder / "configs" / f"{key}.json"
        write(config_path, {"provenance": {"arguments": cfg}, "panel_condition": item,
            "original_config_sha256": digest(original_path), "scope": "new external comparison; protocol per manifest"})
        job_dir = folder / "jobs" / key
        job_dir.mkdir()
        managed = ds == "FMD" and seed == 42
        quality_run = job_dir / "quality"
        quality_audit = job_dir / "quality_audit"
        online_run, online_audit = job_dir / "online", job_dir / "online_audit"
        physical_managed = False
        if managed:
            if outer == 0:
                quality_run = ROOT / f"results/exploratory/local_external_panel_20261028/FMD_s42_f0_{clf}"
                quality_audit = ROOT / f"results/analysis/local_external_panel_20261028/FMD_s42_f0_{clf}"
                physical_managed = True
                if clf == "svm":
                    online_run = ROOT / "results/exploratory/local_batch1_20261028/FMD_s42_f0_svm"
                    online_audit = ROOT / "results/exploratory/local_batch1_followup_20261028/FMD_s42_f0/svm_audit"
                else:
                    online_run = ROOT / "results/exploratory/local_batch1_followup_20261028/FMD_s42_f0/resmlp_online"
                    online_audit = ROOT / "results/exploratory/local_batch1_followup_20261028/FMD_s42_f0/resmlp_audit"
            else:
                base = ROOT / f"results/exploratory/local_external_followup_20261028/FMD_s42_{clf}"
                quality_run, quality_audit = base / f"fold{outer}", base / f"fold{outer}_audit"
        required = [ROOT / manifest_root / "sample_manifests" / f"{ds}.csv",
            ROOT / cfg["ngram_count_cache"] / "metadata.json"]
        from run_rescue_nested_selection import COMMON_21
        embedding_ds = "KTH-TIPS2-b" if ds == "KTHTIPS2b" else ds
        required += [ROOT / embedding_root / embedding_ds / f"{n}.npy" for n in COMMON_21]
        required += [ROOT / embedding_root / embedding_ds / f"{n}_labels.npy" for n in COMMON_21]
        missing = [str(p) for p in required if not p.is_file()]
        hold = "kth_protocol_reconciliation" if ds == "KTHTIPS2b" else ("missing_inputs" if missing else None)
        jobs.append({"id": key, "dataset": ds, "classifier": clf, "seed": seed, "outer_fold": outer,
            "config": str(config_path), "config_sha256": digest(config_path), "job_dir": str(job_dir),
            "quality_run": str(quality_run), "quality_audit": str(quality_audit),
            "online_run": str(online_run), "online_audit": str(online_audit),
            "quality_external_managed": managed, "online_external_managed": physical_managed,
            "quality_hold": hold, "missing_inputs": missing,
            "online_hold": None if ds == "FMD" else "dataset_adapter_binding_review",
            "priority": [priority[ds], 0 if clf == "svm" else 1, seed, outer],
            "quality_timeout_seconds": 7200 if clf == "svm" else 10800,
            "replay_timeout_seconds": 1800, "online_timeout_seconds": 14400})
    jobs.sort(key=lambda j: j["priority"])
    scripts = ["scripts/run_local_external_panel.py", "src/local_external_panel.py", "scripts/audit_local_external_predictions.py",
        "scripts/benchmark_local_single_image.py", "scripts/audit_local_batch1_calls.py"]
    report = {"schema": "local-panel-overnight/1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "conditions": 94, "methods_per_condition": 5, "main_table_cells": 60,
        "source_condition_sha256": digest(source), "source_sha256": {p: digest(ROOT / p) for p in scripts},
        "jobs": jobs, "papers": "deferred until local panel is audited; no implicit replication protocol",
        "no_auto_retry": True, "runtime_hours_per_worker": 10}
    write(folder / "manifest.json", report)
    print(json.dumps({"conditions": len(jobs), "quality_new_runnable": sum(not j["quality_external_managed"] and not j["quality_hold"] for j in jobs),
        "quality_external_managed": sum(j["quality_external_managed"] for j in jobs),
        "quality_hold": sum(bool(j["quality_hold"]) for j in jobs),
        "fmd_online_eligible_after_dependencies": sum(not j["online_hold"] and not j["online_external_managed"] for j in jobs)}, indent=2))


def worker(folder, lane, hours):
    manifest = read(folder / "manifest.json")
    lock_path = folder / f"{lane}.lock"
    import fcntl
    lock = lock_path.open("a")
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(f"{lane} worker already exists")
    state_path = folder / f"worker_{lane}.json"
    state = {"status": "waiting", "lane": lane, "pid": os.getpid(), "completed": [], "requires_review": [],
        "started_utc": datetime.now(timezone.utc).isoformat(), "hours": hours}
    write(state_path, state)
    deadline = time.monotonic() + hours * 3600
    environment = dict(os.environ, OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
    dependencies = [ROOT / "results/exploratory/local_batch1_followup_20261028/FMD_s42_f0/sequence_status.json"]
    if lane == "quality":
        dependencies.append(ROOT / "results/exploratory/local_external_followup_20261028/FMD_s42_resmlp/queue_status.json")
    while time.monotonic() < deadline:
        if any(p.exists() and alive(read(p).get("pid")) for p in dependencies):
            time.sleep(20)
            continue
        selected = None
        for job in manifest["jobs"]:
            phase = "quality" if lane == "quality" else "online"
            if job[phase + "_external_managed"] or job[phase + "_hold"]:
                continue
            marker = Path(job["job_dir"]) / f"{lane}_state.json"
            if marker.exists():
                continue
            result = Path(job[phase + "_run"])
            if result.exists():
                if (result / "status.json").exists() and alive(read(result / "status.json").get("pid")):
                    continue
                write(marker, {"status": "requires_review", "reason": "output exists; never overwrite or retry", "id": job["id"]})
                continue
            if lane == "online":
                quality = Path(job["quality_run"]) / "status.json"
                replay = Path(job["quality_audit"]) / "audit.json"
                if not quality.exists() or read(quality)["status"] != "external_quality_complete_timing_pending" or not replay.exists():
                    continue
                if read(replay).get("source_status_sha256") != digest(quality):
                    continue
            selected = (job, marker)
            break
        if selected is None:
            state.update(status="waiting_for_dependencies_or_review")
            write(state_path, state)
            time.sleep(30)
            continue
        job, marker = selected
        if any(digest(ROOT / p) != expected for p, expected in manifest["source_sha256"].items()) or digest(job["config"]) != job["config_sha256"]:
            state.update(status="stopped_source_drift")
            write(state_path, state)
            return
        phase = "quality" if lane == "quality" else "online"
        if lane == "quality":
            command = ["timeout", str(job["quality_timeout_seconds"]), sys.executable, str(ROOT / "scripts/run_local_external_panel.py"),
                "--reference-config", job["config"], "--protocol", str(ROOT / "docs/fsc_tex/PROTOCOLO_COLA_NOCTURNA_2026-10-28.md"),
                "--classifier", job["classifier"], "--output", job["quality_run"]]
            audit_command = ["timeout", str(job["replay_timeout_seconds"]), sys.executable, str(ROOT / "scripts/audit_local_external_predictions.py"),
                "--run", job["quality_run"], "--output", job["quality_audit"]]
        else:
            command = ["timeout", str(job["online_timeout_seconds"]), sys.executable, str(ROOT / "scripts/benchmark_local_single_image.py"),
                "--run", job["quality_run"], "--deit-reconstruction", str(ROOT / "results/analysis/deit_seed42_diagnostic_20261028/diagnostic.json"),
                "--protocol", str(ROOT / "docs/fsc_tex/PROTOCOLO_COLA_NOCTURNA_2026-10-28.md"), "--output", job["online_run"], "--repeats", "1"]
            audit_command = ["timeout", "300", sys.executable, str(ROOT / "scripts/audit_local_batch1_calls.py"),
                "--online-run", job["online_run"], "--quality-run", job["quality_run"], "--output", job["online_audit"]]
        state.update(status="running", current_job=job["id"], command=command)
        write(state_path, state)
        write(marker, {"status": "running", "id": job["id"], "worker_pid": os.getpid(), "command": command})
        code = 0
        for stage, cmd in (("execute", command), ("audit", audit_command)):
            with (Path(job["job_dir"]) / f"{lane}_{stage}.log").open("x") as handle:
                code = subprocess.run(cmd, cwd=ROOT, env=environment, stdout=handle, stderr=subprocess.STDOUT).returncode
            if code:
                break
        outcome = "complete" if code == 0 else "requires_review"
        write(marker, {"status": outcome, "id": job["id"], "exit_code": code, "stage": stage})
        state["completed" if code == 0 else "requires_review"].append(job["id"])
        write(state_path, state)
        print(f"{lane}: {job['id']} -> {outcome}", flush=True)
    state.update(status="dispatch_window_ended", finished_utc=datetime.now(timezone.utc).isoformat())
    write(state_path, state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "quality", "online"))
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--hours", type=float, default=10)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "src"))
    if args.mode == "prepare":
        prepare(args.folder.resolve())
    else:
        worker(args.folder.resolve(), args.mode, args.hours)
