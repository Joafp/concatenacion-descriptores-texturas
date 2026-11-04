"""One-attempt queue for predeclared concatenation controls; no prior outputs changed."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from run_mesa_replication import ROOT, digest, write_json


def command_for(config, condition, target):
    return [sys.executable, "-u", "src/run_matched_concat_controls.py",
            "--reference-run", str(ROOT / condition["reference"]),
            "--expected-images", str(condition["expected_images"]),
            "--protocol", config["protocol_document"], "--output", str(target)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    suite = ROOT / config["output_root"]
    jobs = [{"condition": c, "command": command_for(config, c, suite / c["id"] / "controls")}
            for c in config["conditions"]]
    if not args.execute:
        print(json.dumps(jobs, indent=2))
        return
    if suite.exists():
        raise FileExistsError(suite)
    paths = {args.config.resolve(), ROOT / config["protocol_document"], Path(__file__),
             ROOT / "scripts/run_mesa_replication.py", ROOT / "src/run_matched_concat_controls.py",
             ROOT / "src/static_concat_controls.py"}
    for c in config["conditions"]:
        ref = ROOT / c["reference"]
        parent = json.loads((ref / "metadata.json").read_text())
        assert parent["status"] == "complete" and parent["dataset"] == c["dataset"]
        assert parent["provenance"]["arguments"]["seed"] == c["seed"]
        for name, expected in parent["provenance"]["source_sha256"].items():
            assert digest(ROOT / name) == expected, name
            paths.add(ROOT / name)
        paths.update([ref / "metadata.json", ref / "selection_oof_scores.npz",
                      *[ref / f"fold{i}.json" for i in range(3)]])
    bindings = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}
    suite.mkdir(parents=True)
    write_json(suite / "frozen_protocol.json", {"config": config, "jobs": jobs,
               "captured_utc": datetime.now(timezone.utc).isoformat(), "input_sha256": bindings,
               "status": "frozen_before_execution"})
    env = dict(os.environ, OPENBLAS_NUM_THREADS=str(config["threads"]),
               OMP_NUM_THREADS=str(config["threads"]), MKL_NUM_THREADS=str(config["threads"]),
               PYTHONPATH=str(ROOT / "src"), PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
    def run(job):
        condition = job["condition"]
        path = suite / condition["id"]
        path.mkdir()
        for name, expected in bindings.items():
            assert digest(ROOT / name) == expected, name
        state = {"status": "running", "condition": condition, "command": job["command"],
                 "started_utc": datetime.now(timezone.utc).isoformat()}
        log_path = path / "controls.log"
        started = time.monotonic()
        with log_path.open("x") as log:
            proc = subprocess.Popen(job["command"], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            state["pid"] = proc.pid
            print(f"{condition['id']}: started matched concatenations, pid {proc.pid}", flush=True)
            while proc.poll() is None:
                state.update(elapsed_seconds=time.monotonic() - started, log_bytes=log_path.stat().st_size)
                write_json(path / "state.json", state)
                if state["elapsed_seconds"] > config["timeout_seconds"]:
                    print(f"{condition['id']}: hard timeout; terminating", flush=True)
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                    state["timeout"] = True
                    break
                time.sleep(10)
        meta_path = path / "controls/metadata.json"
        complete = (proc.returncode == 0 and meta_path.is_file() and
                    json.loads(meta_path.read_text())["status"] == "complete")
        state.update(status="complete_pending_audit" if complete else "failed", returncode=proc.returncode,
                     elapsed_seconds=time.monotonic() - started, log_bytes=log_path.stat().st_size)
        write_json(path / "state.json", state)
        print(f"{condition['id']}: {state['status']}; no automatic retry", flush=True)
        return state
    with ThreadPoolExecutor(max_workers=config["workers"]) as pool:
        states = list(pool.map(run, jobs))
    write_json(suite / "queue_summary.json", {"conditions": states,
        "status": "complete_pending_audit" if all(s["status"] == "complete_pending_audit" for s in states)
                  else "attention_required"})


if __name__ == "__main__":
    main()
