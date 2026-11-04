"""Manifest-only, fail-closed remediation dispatcher. No retries or fallbacks."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
TERMINAL = {"complete", "requires_review", "blocked"}


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def verify_sources(manifest):
    for name, expected in manifest.get('packages', {}).items():
        if importlib.metadata.version(name) != expected:
            raise ValueError('package version drift: ' + name)
    if manifest.get('python_version', sys.version) != sys.version:
        raise ValueError('Python runtime drift')
    if manifest.get("_manifest_path") and digest(manifest["_manifest_path"]) != manifest["_manifest_sha256"]:
        raise ValueError("manifest drift")
    if not manifest.get("source_sha256"):
        raise ValueError("source_sha256 must not be empty")
    for name, expected in manifest["source_sha256"].items():
        if hashlib.sha256(resolve(name).read_bytes()).hexdigest() != expected:
            raise ValueError("source drift: " + name)


def start_ticks(pid):
    from observe_benchmark_process import parse_proc_stat
    return parse_proc_stat(Path(f"/proc/{pid}/stat").read_text())["start_ticks"]


@contextmanager
def lock(path):
    import fcntl
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def active_benchmarks():
    result = subprocess.run(["ps", "-eo", "pid=,args="], capture_output=True,
                            text=True, timeout=10, check=True)
    names = ("benchmark_local_single_image.py", "benchmark_local_batch1",
             "benchmark_cascade_multidataset.py")
    return [line.strip() for line in result.stdout.splitlines()
            if any(name in line for name in names)]


def validate_success(condition):
    data = read(resolve(condition["path"]))
    for key, expected in condition.get("fields", {}).items():
        actual = data
        for part in key.split("."):
            actual = actual[part]
        if actual != expected:
            raise ValueError(f"success field mismatch: {key}")


def command_environment(lane):
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2",
               NUMEXPR_NUM_THREADS="2", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
               HF_DATASETS_OFFLINE="1", PYTHONPATH=str(ROOT / "src"))
    if lane == "cpu":
        env["CUDA_VISIBLE_DEVICES"] = ""
    return env


def run_command(command, task, folder, stage, save_state):
    argv = command["argv"]
    timeout = command["timeout_seconds"]
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise ValueError("argv must be a nonempty string list")
    if not isinstance(timeout, (int, float)) or not 0 < timeout < float("inf"):
        raise ValueError("invalid hard timeout")
    observer = None
    observe = task.get("observe", False) and stage == 0
    with (folder / f"stage_{stage}.log").open("x") as log:
        process = subprocess.Popen(argv, cwd=ROOT, env=command_environment(task["lane"]),
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        identity = None
        try:
            try:
                identity = start_ticks(process.pid)
            except FileNotFoundError:
                if observe:
                    raise RuntimeError("target exited before observer identity binding")
            save_state(status="running", stage=stage, pid=process.pid, start_ticks=identity,
                       argv=argv, hard_timeout_seconds=timeout)
            if observe:
                with (folder / f"observer_{stage}.log").open("x") as obslog:
                    observer = subprocess.Popen([
                        sys.executable, str(ROOT / "scripts/observe_benchmark_process.py"),
                        "--pid", str(process.pid), "--expected-start-ticks", str(identity),
                        "--output", str(folder / f"observer_{stage}.jsonl"),
                        "--max-seconds", str(timeout + 60), "--interval-seconds", "30",
                    ], cwd=ROOT, env=command_environment("cpu"), stdout=obslog,
                       stderr=subprocess.STDOUT)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                save_state(status="requires_review", reason="hard_timeout_before_termination",
                           pid=process.pid, start_ticks=identity, stage=stage)
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
                raise RuntimeError("hard timeout; process group terminated")
        finally:
            # No target signals outside the hard-timeout path, including observer failures.
            if process.poll() is None:
                process.wait(timeout=max(1, timeout))
            if observer is not None:
                obs_code = observer.wait(timeout=45)
                rows = [json.loads(line) for line in
                        (folder / f"observer_{stage}.jsonl").read_text().splitlines()]
                if (obs_code != 0 or not rows or rows[-1].get("event") != "observer_finished"
                        or rows[-1].get("reason") not in {"target_exited", "target_terminal_state"}):
                    raise RuntimeError("observer did not audit target termination")
    if code != 0:
        raise RuntimeError(f"command exit {code}")
    if "success" in command:
        validate_success(command["success"])
        path = resolve(command["success"]["path"])
        return {"path": str(path), "sha256": digest(path), "condition": command["success"]}
    return None


def run_task(task, folder, manifest, on_state=None):
    state_path = folder / "state.json"
    manifest_sha = manifest.get("_manifest_sha256") or hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    state = {"id": task["id"], "lane": task["lane"], "started_utc": utc(),
             "manifest_sha256": manifest_sha, "success_artifacts": []}
    def save_state(**updates):
        state.update(updates, updated_utc=utc())
        write(state_path, state)
        if on_state:
            on_state(state)
    try:
        verify_sources(manifest)
        occupied = [str(resolve(p)) for p in task.get("exclusive_outputs", []) if resolve(p).exists()]
        if occupied:
            raise ValueError("exclusive outputs already exist: " + repr(occupied))
        if not task.get("commands"):
            raise ValueError("task has no commands")
        save_state(status="running")
        for stage, command in enumerate(task["commands"]):
            verify_sources(manifest)
            artifact = run_command(command, task, folder, stage, save_state)
            if artifact:
                state["success_artifacts"].append(artifact)
                save_state()
        save_state(status="complete", finished_utc=utc())
    except Exception as exc:
        save_state(status="requires_review", error=f"{type(exc).__name__}: {exc}", finished_utc=utc())
    return state


def run_queue(folder, lane, window_hours=10):
    folder = Path(folder).resolve()
    manifest = read(folder / "manifest.json")
    manifest["_manifest_sha256"] = digest(folder / "manifest.json")
    manifest["_manifest_path"] = str(folder / "manifest.json")
    tasks = manifest["tasks"]
    ids = [t["id"] for t in tasks]
    if (len(set(ids)) != len(ids) or any(Path(i).name != i or i in {".", ".."} for i in ids)
            or any(t["lane"] not in {"cpu", "gpu"} for t in tasks)
            or any(d not in ids for t in tasks for d in t.get("depends_on", []))
            or not 0 < window_hours < float("inf")):
        raise ValueError("invalid task identities, dependencies, lane or window")
    deadline = time.monotonic() + window_hours * 3600
    worker = {"lane": lane, "pid": os.getpid(), "start_ticks": start_ticks(os.getpid()),
              "manifest_sha256": manifest["_manifest_sha256"],
              "started_utc": utc(), "status": "running", "outcomes": {}}
    worker_path = folder / f"{lane}.json"
    def states():
        return {t["id"]: read(folder / "tasks" / t["id"] / "state.json")
                for t in tasks if (folder / "tasks" / t["id"] / "state.json").exists()}
    with lock(folder / f"{lane}.lock"):
        for task in tasks:
            if task["lane"] != lane:
                continue
            path = folder / "tasks" / task["id"] / "state.json"
            if path.exists():
                old = read(path)
                if old.get("status") not in TERMINAL:
                    old.update(status="requires_review", reason="existing_partial_state_no_retry", updated_utc=utc())
                    write(path, old)
        while time.monotonic() < deadline:
            prior = states()
            # Revalidate completed dependencies before any downstream dispatch.
            for task_id, completed in prior.items():
                if completed.get("status") != "complete":
                    continue
                try:
                    if completed.get("manifest_sha256") != manifest["_manifest_sha256"]:
                        raise ValueError("completed state manifest binding mismatch")
                    expected_conditions = [command["success"] for task in tasks if task["id"] == task_id
                                           for command in task["commands"] if "success" in command]
                    if [a.get("condition") for a in completed.get("success_artifacts", [])] != expected_conditions:
                        raise ValueError("completed success receipt coverage mismatch")
                    for artifact in completed.get("success_artifacts", []):
                        if digest(artifact["path"]) != artifact["sha256"]:
                            raise ValueError("completed success artifact changed: " + artifact["path"])
                        validate_success(artifact["condition"])
                except Exception as exc:
                    completed.update(status="requires_review", reason="completed_dependency_integrity",
                                     error=f"{type(exc).__name__}: {exc}", updated_utc=utc())
                    write(folder / "tasks" / task_id / "state.json", completed)
            ready = []
            pending = False
            for task in tasks:
                if task["lane"] != lane or task["id"] in prior:
                    continue
                dependencies = [prior.get(d, {}).get("status") for d in task.get("depends_on", [])]
                if any(s in {"requires_review", "blocked"} for s in dependencies):
                    write(folder / "tasks" / task["id"] / "state.json",
                          {"id": task["id"], "status": "blocked", "reason": "dependency_requires_review", "updated_utc": utc()})
                elif all(s == "complete" for s in dependencies):
                    ready.append(task)
                else:
                    pending = True
            worker["outcomes"] = {i: s["status"] for i, s in states().items()}
            write(worker_path, worker)
            if not ready:
                if not pending:
                    break
                time.sleep(min(5, max(0, deadline - time.monotonic())))
                continue
            task = ready[0]
            def dispatch():
                worker.update(current_task=task["id"], updated_utc=utc())
                write(worker_path, worker)
                task_folder = folder / "tasks" / task["id"]
                task_folder.mkdir(parents=True, exist_ok=True)
                def on_state(state):
                    worker.update(current_pid=state.get("pid"),
                                  current_start_ticks=state.get("start_ticks"),
                                  current_stage=state.get("stage"), updated_utc=utc())
                    write(worker_path, worker)
                return run_task(task, task_folder, manifest, on_state)
            if lane == "gpu":
                try:
                    with lock(resolve(manifest.get("gpu_lock", "results/analysis/gpu.lock"))):
                        if active_benchmarks():
                            time.sleep(min(5, max(0, deadline - time.monotonic())))
                            continue
                        dispatch()
                except BlockingIOError:
                    time.sleep(min(5, max(0, deadline - time.monotonic())))
            else:
                dispatch()
        worker.update(status="dispatch_window_ended" if time.monotonic() >= deadline else "all_tasks_terminal",
                      current_task=None, finished_utc=utc(),
                      current_pid=None, current_start_ticks=None,
                      outcomes={i: s["status"] for i, s in states().items()})
        write(worker_path, worker)
    return worker


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--lane", choices=["cpu", "gpu"], required=True)
    parser.add_argument("--window-hours", type=float, default=10)
    args = parser.parse_args()
    run_queue(args.folder, args.lane, args.window_hours)
