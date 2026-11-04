"""Audit the active SVM pilot, then run/audit ResMLP without GPU overlap."""
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


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"status": "waiting_for_svm", "pid": os.getpid(), "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "completed_stages": []}

    def save():
        (args.output / "sequence_status.json").write_text(json.dumps(report, indent=2) + "\n")

    save()
    deadline = time.monotonic() + 1900
    while True:
        previous = json.loads((args.svm_online / "status.json").read_text())
        if previous["status"] == "batch1_online_f1_and_timing_complete":
            # The GPU context can survive until the first process exits.
            try:
                os.kill(previous["pid"], 0)
            except ProcessLookupError:
                break
        elif previous["status"] == "blocked_online_execution":
            report.update(status="stopped_on_svm_failure", previous_error=previous.get("error"))
            save()
            raise SystemExit(1)
        if time.monotonic() > deadline:
            report.update(status="wait_deadline_exceeded")
            save()
            raise SystemExit(1)
        time.sleep(10)
    stages = [
        ("audit_svm", ["timeout", "120s", sys.executable, str(ROOT / "scripts/audit_local_batch1_calls.py"),
            "--online-run", str(args.svm_online), "--quality-run", str(args.svm_quality), "--output", str(args.output / "svm_audit")]),
        ("measure_resmlp", ["timeout", "1800s", sys.executable, str(ROOT / "scripts/benchmark_local_single_image.py"),
            "--run", str(args.resmlp_quality), "--deit-reconstruction", str(args.deit_reconstruction),
            "--protocol", str(args.protocol), "--output", str(args.output / "resmlp_online"), "--repeats", "1"]),
        ("audit_resmlp", ["timeout", "120s", sys.executable, str(ROOT / "scripts/audit_local_batch1_calls.py"),
            "--online-run", str(args.output / "resmlp_online"), "--quality-run", str(args.resmlp_quality),
            "--output", str(args.output / "resmlp_audit")]),
    ]
    environment = dict(os.environ, OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2")
    for name, command in stages:
        report.update(status="running", current_stage=name, command=command)
        save()
        print(f"Physical followup: {name}", flush=True)
        with (args.output / f"{name}.log").open("x") as handle:
            code = subprocess.run(command, cwd=ROOT, env=environment, stdout=handle, stderr=subprocess.STDOUT).returncode
        if code:
            report.update(status="stopped_on_failure", exit_code=code)
            save()
            raise SystemExit(code)
        report["completed_stages"].append(name)
        save()
    report.update(status="both_pilots_and_call_audits_complete", finished_utc=datetime.now(timezone.utc).isoformat())
    save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svm-online", type=Path, required=True)
    parser.add_argument("--svm-quality", type=Path, required=True)
    parser.add_argument("--resmlp-quality", type=Path, required=True)
    parser.add_argument("--deit-reconstruction", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
