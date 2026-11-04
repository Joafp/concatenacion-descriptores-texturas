"""Run only the explicitly approved FMD static-stage recoveries, once each."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from run_mesa_replication import ROOT, digest, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    suite = args.suite.resolve()
    frozen = json.loads((suite / "frozen_protocol.json").read_text())
    for name, expected in frozen["source_sha256"].items():
        assert digest(ROOT / name) == expected, name
    jobs = []
    for condition in frozen["config"]["conditions"]:
        if condition["dataset"] != "FMD":
            continue
        path = suite / condition["id"]
        state = json.loads((path / "state.json").read_text())
        assert state["status"] == "failed" and state["failed_stage"] == "static"
        assert all(s["status"] == "complete" for s in state["stages"][:-1])
        assert "part.row_index.nunique() == 680" in (path / "static.log").read_text()
        assert condition["expected_development_images"] == 800
        command = [sys.executable, "-u", "scripts/run_static_budget_control_general.py",
                   "--hybrid-run", str(path / "hybrid"), "--expected-images", "800",
                   "--protocol", frozen["config"]["protocol_document"],
                   "--output", str(path / "static_recovery")]
        jobs.append((path, command))
    assert len(jobs) == 3
    if not args.execute:
        print(json.dumps([cmd for _, cmd in jobs], indent=2))
        return
    receipt = suite / "static_recovery_authorization.json"
    if receipt.exists() or any((p / "static_recovery").exists() for p, _ in jobs):
        raise FileExistsError("Recovery already recorded; no automatic second attempt")
    bindings = {str(p.relative_to(ROOT)): digest(p) for p in (
        Path(__file__), ROOT / "scripts/run_static_budget_control_general.py",
        suite / "frozen_protocol.json",
        *[p / name for p, _ in jobs for name in ("state.json", "static.log", "static/decisions.json")])}
    write_json(receipt, {"authorization": "User: Sí, corregir y repetir solo esas etapas",
                        "scope": "Only failed FMD static stages; new output directories; no method changes",
                        "recorded_utc": datetime.now(timezone.utc).isoformat(),
                        "input_sha256": bindings, "commands": [cmd for _, cmd in jobs]})
    env = dict(os.environ, OPENBLAS_NUM_THREADS="2", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2",
               PYTHONPATH=str(ROOT / "src"),
               PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
    for path, command in jobs:
        state = {"status": "running", "command": command, "authorization_sha256": digest(receipt)}
        state_path = path / "static_recovery_state.json"
        log_path = path / "static_recovery.log"
        start = time.monotonic()
        with log_path.open("x") as log:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            state.update(pid=proc.pid, started_utc=datetime.now(timezone.utc).isoformat())
            print(f"{path.name}: recovering static only (pid {proc.pid})", flush=True)
            while proc.poll() is None:
                state.update(elapsed_seconds=time.monotonic() - start, log_bytes=log_path.stat().st_size)
                write_json(state_path, state)
                if state["elapsed_seconds"] > 1800:
                    print(f"{path.name}: hard timeout; terminating recovery", flush=True)
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                    break
                time.sleep(10)
        state.update(returncode=proc.returncode, elapsed_seconds=time.monotonic() - start)
        meta = path / "static_recovery/metadata.json"
        complete = proc.returncode == 0 and meta.is_file() and json.loads(meta.read_text())["status"] == "complete"
        if complete:
            assert digest(path / "static/decisions.json") == digest(path / "static_recovery/decisions.json")
        state["status"] = "complete_pending_audit" if complete else "failed"
        write_json(state_path, state)
        print(f"{path.name}: {state['status']}; no automatic retry", flush=True)
    for name, expected in bindings.items():
        assert digest(ROOT / name) == expected, name


if __name__ == "__main__":
    main()
