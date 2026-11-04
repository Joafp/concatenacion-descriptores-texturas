"""Run the frozen replication queue without changing historical algorithms.

New output roots only; no automatic retries. Each worker advances one condition
through dependent stages. State updates are atomic and per condition.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commands(config, condition, output_root, python):
    root = output_root / condition["id"]
    paired, carlos, hybrid, static = [root / n for n in ("paired", "carlos", "hybrid", "static")]
    first = [python, "-u", "src/run_budgeted_rescue_paired.py", "--dataset", condition["dataset"],
             "--manifest-root", condition["manifest_root"], "--embedding-root", condition["embedding_root"],
             "--seed", str(condition["seed"]), "--fold", str(condition.get("fold", 0)),
             "--library", str(config["library"]), "--ngram-count-cache", condition["ngram_count_cache"],
             "--producer-folds", str(config["producer_folds"]), "--selection-folds", str(config["selection_folds"]),
             "--budgets-ms", *map(str, config["budgets_ms"]), "--quantiles", *map(str, config["quantiles"]),
             "--candidate-draws", str(config["candidate_draws"]), "--subset-size", str(config["subset_size"]),
             "--max-members", str(config["max_members"]), "--output", str(paired)]
    if "official_split" in condition:
        first += ["--official-split", str(condition["official_split"])]
    return [
        ("paired", first, paired),
        ("carlos", [python, "-u", "src/run_carlos_paired_controls.py", "--reference-run", str(paired),
                    "--output", str(carlos)], carlos),
        ("hybrid", [python, "-u", "src/run_carlos_hybrid.py", "--reference-run", str(paired),
                    "--carlos-run", str(carlos), "--output", str(hybrid)], hybrid),
        ("static", [python, "-u", "scripts/run_replication_static_control.py", "--hybrid-run", str(hybrid),
                    "--output", str(static), "--protocol", config["protocol_document"]], static),
    ]


def write_json(path, payload):
    temporary = path.with_suffix(".tmp.json")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def run_condition(config, condition, output_root, sources):
    root = output_root / condition["id"]
    root.mkdir()
    state = {"condition": condition, "status": "running", "stages": [], "runner_pid": os.getpid()}
    write_json(root / "state.json", state)
    env = dict(os.environ, OPENBLAS_NUM_THREADS=str(config["threads_per_process"]),
               OMP_NUM_THREADS=str(config["threads_per_process"]),
               MKL_NUM_THREADS=str(config["threads_per_process"]), PYTHONPATH=str(ROOT / "src"),
               PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
    for name, command, target in commands(config, condition, output_root, sys.executable):
        if any(digest(ROOT / p) != h for p, h in sources.items()):
            state.update(status="failed", error="source drift before stage", failed_stage=name)
            break
        record = {"stage": name, "command": command, "status": "running", "started_utc": datetime.now(timezone.utc).isoformat()}
        state["stages"].append(record)
        log_path = root / f"{name}.log"
        print(f"{condition['id']}: starting {name}", flush=True)
        start = time.monotonic()
        with log_path.open("w") as log:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True)
            record.update(pid=proc.pid, log=str(log_path), last_output_size=0)
            write_json(root / "state.json", state)
            while proc.poll() is None:
                elapsed = time.monotonic() - start
                record.update(elapsed_seconds=elapsed, last_output_size=log_path.stat().st_size)
                write_json(root / "state.json", state)
                if elapsed > config["stage_timeout_seconds"]:
                    print(f"{condition['id']}/{name}: hard timeout; terminating stage", flush=True)
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                    record["timeout"] = True
                    break
                time.sleep(10)
        record.update(returncode=proc.returncode, elapsed_seconds=time.monotonic() - start)
        metadata = target / "metadata.json"
        complete = (proc.returncode == 0 and metadata.is_file() and
                    json.loads(metadata.read_text()).get("status") == "complete")
        record["status"] = "complete" if complete else "failed"
        if not complete:
            state.update(status="failed", failed_stage=name)
            print(f"{condition['id']}: failed {name}; no automatic retry", flush=True)
            break
        write_json(root / "state.json", state)
    else:
        state["status"] = "complete_pending_audit"
        print(f"{condition['id']}: four stages complete; audit required", flush=True)
    write_json(root / "state.json", state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    output_root = ROOT / config["output_root"]
    jobs = [{"condition": c, "commands": [cmd for _, cmd, _ in commands(config, c, output_root, sys.executable)]}
            for c in config["conditions"]]
    if not args.execute:
        print(json.dumps(jobs, indent=2))
        return
    output_root.mkdir(parents=True, exist_ok=False)
    paths = [ROOT / "src" / name for name in (
        "run_budgeted_rescue_paired.py", "run_carlos_paired_controls.py", "run_carlos_hybrid.py",
        "budgeted_rescue.py", "carlos_hybrid.py", "ensemble_scoring.py", "singleton_ranking.py",
        "run_confirmatory_nested.py", "run_topk_individual_control.py", "run_rescue_nested_selection.py",
        "run_weighted_lottery_selection.py", "run_diversity_lottery.py", "rgb_ngram_descriptor.py",
        "run_rgb_ngram_outex13_official.py", "static_budget_control.py", "fsc_tex/cost_model.py", "fsc_tex/utility.py")]
    paths += [Path(__file__), ROOT / "scripts/run_static_budget_control.py",
              ROOT / "scripts/run_replication_static_control.py", args.config.resolve(),
              ROOT / config["protocol_document"], ROOT / "results/analysis/selection_tables/svm.json"]
    sources = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    write_json(output_root / "frozen_protocol.json", {"config": config, "jobs": jobs,
               "captured_utc": datetime.now(timezone.utc).isoformat(), "source_sha256": sources,
               "runner_pid": os.getpid(), "status": "frozen_before_execution"})
    with ThreadPoolExecutor(max_workers=config["max_workers"]) as pool:
        states = list(pool.map(lambda c: run_condition(config, c, output_root, sources), config["conditions"]))
    write_json(output_root / "queue_summary.json", {"conditions": states,
               "status": "complete_pending_audit" if all(s["status"] == "complete_pending_audit" for s in states) else "attention_required"})


if __name__ == "__main__":
    main()
