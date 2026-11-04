"""Point the frozen static-control runner at another completed hybrid run.

The selector and original script remain unchanged for historical provenance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import run_static_budget_control as original


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hybrid-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    hybrid = args.hybrid_run.resolve()
    output = args.output.resolve()
    meta = json.loads((hybrid / "metadata.json").read_text())
    if meta["status"] != "complete":
        raise ValueError("completed hybrid required")
    original.HYBRID = hybrid
    sys.argv = [str(Path(original.__file__)), "--output", str(output)]
    original.main()
    sources = [Path(__file__), Path(original.__file__), args.protocol.resolve()]
    receipt = {"scope": "Input-directory adapter; unchanged static ensemble selector",
               "hybrid_run": str(hybrid), "output": str(output),
               "input_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (output / "adapter_provenance.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
