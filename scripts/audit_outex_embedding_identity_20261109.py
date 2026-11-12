#!/usr/bin/env python3
"""Read-only check of Outex stored arrays against frozen training receipts."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "results/analysis/blocker_resolution_20261101/queue_v1/jobs"
ARRAYS = {
    "historical": ROOT / "embeddings_extensions/Outex13Official1360",
    "panel_amended": JOBS.parent / "embeddings/Outex13Official1360",
}


def array_hash(array):
    array = np.ascontiguousarray(array)
    h = hashlib.sha256()
    h.update(array.dtype.str.encode("ascii"))
    h.update(json.dumps(array.shape).encode("ascii"))
    h.update(memoryview(array).cast("B"))
    return h.hexdigest()


def main():
    for source, folder in ARRAYS.items():
      for name in ("vit_b16", "deit_s"):
        a = np.load(folder / f"{name}.npy", allow_pickle=False)
        # The historical loader hashes row-L2-normalized float32 arrays, not
        # raw .npy bytes; reproduce that exact transformation before comparing.
        norms = np.linalg.norm(a, axis=1, keepdims=True)
        normalized = a / np.maximum(norms, 1e-12)
        digest = array_hash(normalized)
        receipts = {}
        for clf in ("svm", "resmlp"):
            path = JOBS / f"Outex13Official1360_{clf}_s42_f0/quality/status.json"
            receipt = json.loads(path.read_text(encoding="utf-8"))
            saved = receipt["provenance"]["embedding_array_sha256"][name]
            receipts[clf] = {"receipt_array_sha256": saved, "matches": saved == digest}
        print(json.dumps({"source": source, "name": name, "shape": list(a.shape), "dtype": str(a.dtype),
                          "normalized_array_sha256": digest, "receipts": receipts}))


if __name__ == "__main__":
    main()
