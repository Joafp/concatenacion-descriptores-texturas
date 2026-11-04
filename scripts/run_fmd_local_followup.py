"""Continue the frozen local panel on remaining FMD/42 folds, new outputs only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    source = json.loads(args.reference_config.read_text())
    original = source["provenance"]["arguments"]
    if original["dataset"] != "FMD" or original["seed"] != 42:
        raise ValueError("this queue is explicitly restricted to FMD seed42")
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"status": "queued", "classifier": args.classifier, "seed": 42,
        "dataset": "FMD", "folds": [1, 2, 3, 4], "completed": [],
        "physical_latency_published": False, "pid": os.getpid(),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_config_sha256": hashlib.sha256(args.reference_config.read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(args.protocol.read_bytes()).hexdigest()}

    def save():
        (args.output / "queue_status.json").write_text(json.dumps(report, indent=2) + "\n")

    save()
    environment = dict(os.environ, OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2")
    for fold in report["folds"]:
        cfg = dict(original, fold=fold)
        config_path = args.output / f"fold{fold}_config.json"
        config_path.write_text(json.dumps({"provenance": {"arguments": cfg},
            "derived_from_sha256": report["reference_config_sha256"],
            "change": "outer fold only; seed, library, budget and recipe unchanged"}, indent=2) + "\n")
        result = args.output / f"fold{fold}"
        commands = [
            ["timeout", "1800s", sys.executable, str(ROOT / "scripts/run_local_external_panel.py"),
             "--reference-config", str(config_path), "--protocol", str(args.protocol),
             "--classifier", args.classifier, "--output", str(result)],
            ["timeout", "300s", sys.executable, str(ROOT / "scripts/audit_local_external_predictions.py"),
             "--run", str(result), "--output", str(args.output / f"fold{fold}_audit")],
        ]
        for stage, command in zip(("quality", "replay"), commands):
            report.update(status="running", current_fold=fold, stage=stage, command=command)
            save()
            print(f"FMD/{args.classifier}/seed42/fold{fold}: {stage}", flush=True)
            with (args.output / f"fold{fold}_{stage}.log").open("x") as log:
                code = subprocess.run(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT).returncode
            if code:
                report.update(status="stopped_on_failure", exit_code=code)
                save()
                raise SystemExit(code)
        report["completed"].append(fold)
        save()
    report.update(status="complete_quality_and_replay", finished_utc=datetime.now(timezone.utc).isoformat())
    save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-config", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
