"""Read-only external process observer; never launches, signals or retries targets.

JSONL timestamps describe observation time, not per-call benchmark timing.
CPU ticks and RSS pages are raw Linux /proc units, with conversion metadata.
"""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import time


def parse_proc_stat(text):
    """Parse Linux proc stat even when comm contains spaces or ')' characters."""
    opening, closing = text.find("("), text.rfind(")")
    if opening < 1 or closing <= opening:
        raise ValueError("invalid proc stat command delimiters")
    fields = text[closing + 1:].split()
    if len(fields) < 22:
        raise ValueError("truncated proc stat")
    return {
        "pid": int(text[:opening].strip()), "comm": text[opening + 1:closing],
        "state": fields[0], "utime_ticks": int(fields[11]),
        "stime_ticks": int(fields[12]), "start_ticks": int(fields[19]),
        "rss_pages": int(fields[21]),
    }


def timestamps():
    return {
        "utc": datetime.now(timezone.utc).isoformat(),
        "monotonic_seconds": time.monotonic(),
        "boottime_seconds": time.clock_gettime(time.CLOCK_BOOTTIME)
        if hasattr(time, "CLOCK_BOOTTIME") else None,
    }


def gpu_snapshot(timeout_seconds):
    try:
        result = subprocess.run([
            "/usr/lib/wsl/lib/nvidia-smi",
            "--query-gpu=timestamp,index,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader",
        ], capture_output=True, text=True, timeout=timeout_seconds, check=False)
        return {"returncode": result.returncode, "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": type(exc).__name__, "detail": str(exc)}


def observe(pid, output, *, expected_start_ticks=None, interval_seconds=30,
            max_seconds=14400, gpu=False, gpu_timeout_seconds=2,
            proc_root="/proc"):
    """Observe one PID identity until exit/reuse/zombie/deadline; return reason.

    Supply expected_start_ticks from launch for strongest identity binding. If
    omitted, identity binds to the first successfully read stat. Deadline only
    stops this observer. Existing output is never overwritten or appended.
    """
    if (pid <= 0 or not all(math.isfinite(v) for v in
                           (interval_seconds, max_seconds, gpu_timeout_seconds))
            or interval_seconds < 5 or max_seconds <= 0 or gpu_timeout_seconds <= 0):
        raise ValueError("require positive PID/deadline/timeout and interval >= 5 seconds")
    started = time.monotonic()
    stat_path = Path(proc_root) / str(pid) / "stat"
    identity = expected_start_ticks
    with Path(output).open("x", encoding="utf-8") as stream:
        def emit(event, **data):
            stream.write(json.dumps({"event": event, "pid": pid, **timestamps(),
                                     **data}, allow_nan=False) + "\n")
            stream.flush()

        emit("observer_started", expected_start_ticks=identity,
             interval_seconds=interval_seconds, max_seconds=max_seconds,
             gpu_enabled=gpu, clock_ticks_per_second=os.sysconf("SC_CLK_TCK"),
             page_size_bytes=os.sysconf("SC_PAGE_SIZE"),
             scope="external snapshots only; not hardware isolation or call-level timing")
        while True:
            if time.monotonic() - started >= max_seconds:
                reason = "deadline_reached"
                break
            try:
                sample = parse_proc_stat(stat_path.read_text())
            except (FileNotFoundError, ProcessLookupError):
                reason = "target_exited"
                break
            except (OSError, ValueError) as exc:
                reason = "observation_error"
                emit(reason, error=type(exc).__name__, detail=str(exc))
                break
            if sample["pid"] != pid:
                reason = "pid_mismatch"
                emit(reason, observed=sample)
                break
            if identity is None:
                identity = sample["start_ticks"]
                emit("identity_bound", start_ticks=identity)
            if sample["start_ticks"] != identity:
                reason = "pid_reused"
                emit(reason, expected_start_ticks=identity, observed=sample)
                break
            emit("process_snapshot", **{k: v for k, v in sample.items() if k != "pid"})
            if sample["state"] in {"Z", "X", "x"}:
                reason = "target_terminal_state"
                break
            if gpu:
                remaining = max_seconds - (time.monotonic() - started)
                if remaining > 0:
                    emit("gpu_snapshot", snapshot=gpu_snapshot(min(gpu_timeout_seconds, remaining)))
            remaining = max_seconds - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(min(interval_seconds, remaining))
        emit("observer_finished", reason=reason, bound_start_ticks=identity,
             elapsed_seconds=time.monotonic() - started, target_signalled=False)
    return reason


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-start-ticks", type=int)
    parser.add_argument("--interval-seconds", type=float, default=30)
    parser.add_argument("--max-seconds", type=float, default=14400)
    parser.add_argument("--gpu", action="store_true", help="Optional nvidia-smi snapshots; default disabled")
    parser.add_argument("--gpu-timeout-seconds", type=float, default=2)
    args = parser.parse_args()
    print(observe(args.pid, args.output, expected_start_ticks=args.expected_start_ticks,
                  interval_seconds=args.interval_seconds, max_seconds=args.max_seconds,
                  gpu=args.gpu, gpu_timeout_seconds=args.gpu_timeout_seconds))


if __name__ == "__main__":
    main()
