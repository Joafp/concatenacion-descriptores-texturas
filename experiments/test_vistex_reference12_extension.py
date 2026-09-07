#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


extension = load("vistex_reference12", REPO / "src/vistex_reference12_extension.py")
runner = load("confirmatory_runner_vistex", REPO / "src/run_confirmatory_nested.py")


class VisTexReference12Tests(unittest.TestCase):
    def test_manifest_discovery_is_canonical(self):
        paths, classes, labels = extension.discover_manifest_images()
        self.assertEqual(len(paths), 140)
        self.assertEqual(len(classes), 12)
        self.assertEqual(labels.shape, (140,))
        self.assertEqual(classes, sorted(classes))
        self.assertEqual(set(np.unique(labels)), set(range(12)))
        self.assertTrue(all(Path(path).is_file() for path in paths))

    def test_manifest_gate_counts_hashes_and_groups(self):
        result = extension.validate_manifest()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["rows"], 140)
        self.assertEqual(result["classes"], 12)
        self.assertGreaterEqual(min(result["counts"].values()), 7)

    def test_embedding_validator_and_runner_use_isolated_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset_dir = root / "VisTexReference12"
            dataset_dir.mkdir()
            _, classes, labels = extension.load_manifest()
            for index, extractor in enumerate(extension.CANONICAL_EXTRACTORS):
                np.save(dataset_dir / f"{extractor}.npy",
                        np.full((len(labels), 2), index + 1, dtype=np.float32))
                np.save(dataset_dir / f"{extractor}_labels.npy", labels)
                (dataset_dir / f"{extractor}_classes.json").write_text(json.dumps(classes))
            validated = extension.validate_embeddings(dataset_dir, labels, classes)
            self.assertEqual(validated["status"], "PASS_REEXTRACTED_GROUP_AWARE")
            cache, observed = runner.load_dataset(REPO, "VisTexReference12", embedding_root=root)
            self.assertEqual(set(cache), set(extension.CANONICAL_EXTRACTORS))
            np.testing.assert_array_equal(observed, labels)

    def test_runner_gate_accepts_extension_audit_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            (output / "sample_manifests").mkdir()
            (output / "data_audit.csv").write_text(
                "dataset,status\nVisTexReference12,PASS_REEXTRACTED_GROUP_AWARE\n"
            )
            source = extension.DEFAULT_MANIFEST
            (output / "sample_manifests/VisTexReference12.csv").write_bytes(source.read_bytes())
            runner.audit_gate(output, "VisTexReference12")
            _, _, labels = extension.load_manifest()
            groups, rows = runner.load_manifest(output, "VisTexReference12", labels)
            self.assertEqual(len(groups), 140)
            self.assertEqual(len(rows), 140)
            self.assertEqual(len(set(groups)), 140)


if __name__ == "__main__":
    unittest.main()
