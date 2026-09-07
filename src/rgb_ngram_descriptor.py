"""Leakage-safe RGB Pixel N-gram block for the nested texture protocol.

The image-level counts are label-free and may be cached once.  The vocabulary
and TruncatedSVD projection are fitted anew from the training indices supplied
by each inner/outer split.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from scipy import sparse

from run_rgb_ngram_outex13_official import IMPLEMENTATIONS, count_image


BLOCK_NAME = "rgb_ngram_svd"


def _manifest_path(row: dict, repo: Path) -> Path:
    value = row.get("path") or row.get("source_path")
    if not value:
        raise ValueError("manifest needs path or source_path for RGB N-grams")
    path = Path(value)
    return path if path.is_absolute() else repo / path


def _manifest_digest(rows: list[dict], repo: Path) -> str:
    payload = "\n".join(
        f"{row.get('row_id', i)}\t{_manifest_path(row, repo)}\t"
        f"{row.get('source_sha256') or row.get('sha256', '')}"
        for i, row in enumerate(rows)
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def build_count_cache(
    rows: list[dict], repo: Path, destination: Path,
    implementation: str = "rgb_ngram_impl1",
) -> dict[str, np.ndarray]:
    """Create/resume label-free per-image counts in manifest row order."""
    if implementation not in IMPLEMENTATIONS:
        raise KeyError(implementation)
    destination.mkdir(parents=True, exist_ok=True)
    digest = _manifest_digest(rows, repo)
    required = [destination / name for name in ("keys.npy", "counts.npy", "indptr.npy")]
    metadata_path = destination / "metadata.json"
    if all(path.exists() for path in required) and metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        if metadata.get("manifest_sha256") == digest and metadata.get("samples") == len(rows):
            return {name: np.load(destination / f"{name}.npy", mmap_mode="r")
                    for name in ("keys", "counts", "indptr")}

    keys_parts: list[np.ndarray] = []
    count_parts: list[np.ndarray] = []
    lengths: list[int] = []
    for index, row in enumerate(rows):
        path = _manifest_path(row, repo)
        if not path.is_file():
            raise FileNotFoundError(path)
        with Image.open(path) as image:
            rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
        keys, counts = count_image(rgb, implementation)
        keys_parts.append(keys)
        count_parts.append(counts)
        lengths.append(len(keys))
        if (index + 1) % 200 == 0 or index + 1 == len(rows):
            print(f"{implementation} counts: {index + 1}/{len(rows)}", flush=True)

    indptr = np.concatenate((np.asarray([0], dtype=np.int64),
                             np.cumsum(lengths, dtype=np.int64)))
    np.save(destination / "keys.npy", np.concatenate(keys_parts))
    np.save(destination / "counts.npy", np.concatenate(count_parts))
    np.save(destination / "indptr.npy", indptr)
    metadata_path.write_text(json.dumps({
        "schema": "rgb-ngram-count-cache/1",
        "implementation": implementation,
        "config": IMPLEMENTATIONS[implementation],
        "samples": len(rows),
        "manifest_sha256": digest,
        "label_free_cache": True,
    }, indent=2) + "\n")
    return {name: np.load(destination / f"{name}.npy", mmap_mode="r")
            for name in ("keys", "counts", "indptr")}


class RGBNgramSVDBlock:
    """Fold-aware dense representation derived from sparse RGB N-grams."""

    name = BLOCK_NAME

    def __init__(self, counts: dict[str, np.ndarray], n_components: int = 256,
                 random_state: int = 42, hash_bins: int = 8192):
        self.counts = counts
        self.n_components = int(n_components)
        self.random_state = int(random_state)
        self.hash_bins = int(hash_bins)
        if self.hash_bins < 2:
            raise ValueError("hash_bins must be >= 2")
        self._cache: dict[tuple, tuple[np.ndarray, np.ndarray, dict]] = {}
        self._lock = threading.Lock()

    @property
    def output_dim(self) -> int:
        return self.n_components

    def transform(self, train: np.ndarray, evaluation: np.ndarray):
        train = np.asarray(train, dtype=np.int64)
        evaluation = np.asarray(evaluation, dtype=np.int64)
        key = (tuple(train.tolist()), tuple(evaluation.tolist()))
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                return cached
            raw_train = self._hashed_rows(train)
            raw_eval = self._hashed_rows(evaluation)
            max_components = min(len(train) - 1, self.hash_bins - 1)
            components = min(self.n_components, max_components)
            if components < 1:
                raise ValueError("RGB N-gram split is too small for TruncatedSVD")
            svd = TruncatedSVD(n_components=components, algorithm="randomized",
                               n_iter=5, random_state=self.random_state)
            x_train = svd.fit_transform(raw_train).astype(np.float32, copy=False)
            x_eval = svd.transform(raw_eval).astype(np.float32, copy=False)
            x_train = normalize(x_train, norm="l2", copy=False)
            x_eval = normalize(x_eval, norm="l2", copy=False)
            audit = {
                "train_rows": len(train), "evaluation_rows": len(evaluation),
                "hash_bins": self.hash_bins, "components": components,
                "fixed_label_free_hashing": True,
                "svd_from_training_only": True,
            }
            result = (np.asarray(x_train), np.asarray(x_eval), audit)
            self._cache[key] = result
            return result

    def _hashed_rows(self, rows: np.ndarray) -> sparse.csr_matrix:
        """Map uint64 n-gram codes deterministically to a bounded sparse space."""
        source_indptr = self.counts["indptr"]
        indptr = [0]
        columns: list[np.ndarray] = []
        values: list[np.ndarray] = []
        for row in rows:
            start, end = int(source_indptr[row]), int(source_indptr[row + 1])
            keys = np.asarray(self.counts["keys"][start:end], dtype=np.uint64)
            counts = np.asarray(self.counts["counts"][start:end], dtype=np.float32)
            bins = np.asarray(keys % np.uint64(self.hash_bins), dtype=np.int32)
            order = np.argsort(bins, kind="stable")
            bins, counts = bins[order], counts[order]
            unique, starts = np.unique(bins, return_index=True)
            summed = np.add.reduceat(counts, starts)
            columns.append(unique)
            values.append(summed)
            indptr.append(indptr[-1] + len(unique))
        return sparse.csr_matrix(
            (np.concatenate(values), np.concatenate(columns), np.asarray(indptr, dtype=np.int64)),
            shape=(len(rows), self.hash_bins), dtype=np.float32,
        )
