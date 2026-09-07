#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


RUNNER_PATH = Path(__file__).resolve().parents[1] / "src" / "run_confirmatory_nested.py"
SPEC = importlib.util.spec_from_file_location("confirmatory_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)

CURET_PROTOCOL_PATH = Path(__file__).resolve().parents[1] / "src" / "curet_confirmatory_protocol.py"
CURET_SPEC = importlib.util.spec_from_file_location("curet_confirmatory_protocol", CURET_PROTOCOL_PATH)
curet_protocol = importlib.util.module_from_spec(CURET_SPEC)
assert CURET_SPEC.loader is not None
CURET_SPEC.loader.exec_module(curet_protocol)


class ConfirmatoryProtocolTests(unittest.TestCase):
    def test_canonical_labels_accept_names_or_integers(self):
        a = runner.canonical_labels(np.array([0, 0, 1, 2, 1]))
        b = runner.canonical_labels(np.array(["cat", "cat", "dog", "soil", "dog"]))
        np.testing.assert_array_equal(a, b)

    def test_l2_rows_is_finite_and_normalized(self):
        x = runner.l2_rows(np.array([[3.0, 4.0], [0.0, 0.0]]))
        self.assertTrue(np.isfinite(x).all())
        self.assertAlmostEqual(float(np.linalg.norm(x[0])), 1.0)
        self.assertEqual(float(np.linalg.norm(x[1])), 0.0)

    def test_gate_rejects_blocked_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data_audit.csv"
            path.write_text("dataset,status\nDTD,BLOCKED_DATA_LEAKAGE_RISK\n")
            with self.assertRaisesRegex(RuntimeError, "BLOCKED_DATA_LEAKAGE_RISK"):
                runner.audit_gate(Path(tmp), "DTD")

    def test_synthetic_nested_gfs_has_no_group_overlap(self):
        rng = np.random.default_rng(42)
        # 4 clases, 8 grupos por clase, 2 observaciones relacionadas por grupo.
        y = np.repeat(np.arange(4), 16)
        groups = np.asarray([f"c{c}_g{g}" for c in range(4) for g in range(8) for _ in range(2)])
        signal = np.eye(4, dtype=np.float32)[y]
        cache = {
            "a": runner.l2_rows(np.c_[signal, rng.normal(0, 0.2, (len(y), 2))]),
            "b": runner.l2_rows(rng.normal(size=(len(y), 5))),
            "c": runner.l2_rows(np.c_[signal[:, ::-1], rng.normal(0, 0.3, (len(y), 2))]),
        }
        outer = runner.StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=42)
        train, test = next(outer.split(np.zeros(len(y)), y, groups))
        self.assertFalse(set(groups[train]).intersection(groups[test]))
        selected, score, history = runner.greedy(cache, list(cache), train, y, groups, "svm", 42, 2)
        self.assertGreaterEqual(len(selected), 1)
        self.assertTrue(np.isfinite(score))
        self.assertGreaterEqual(len(history), 1)

    def test_serial_parallel_greedy_equivalence(self):
        rng = np.random.default_rng(2026)
        y = np.repeat(np.arange(3), 24)
        groups = np.asarray([f"c{c}_g{g}" for c in range(3) for g in range(8) for _ in range(3)])
        signal = np.eye(3, dtype=np.float32)[y]
        cache = {
            "a": runner.l2_rows(np.c_[signal, rng.normal(0, .15, (len(y), 2))]),
            "b": runner.l2_rows(rng.normal(size=(len(y), 5))),
            "c": runner.l2_rows(np.c_[signal[:, ::-1], rng.normal(0, .2, (len(y), 2))]),
            "d": runner.l2_rows(rng.normal(size=(len(y), 4))),
        }
        idx = np.arange(len(y))
        serial = runner.greedy(cache, list(cache), idx, y, groups, "svm", 42, 2, n_jobs=1)
        parallel = runner.greedy(cache, list(cache), idx, y, groups, "svm", 42, 2, n_jobs=2)
        self.assertEqual(serial[0], parallel[0])
        self.assertAlmostEqual(serial[1], parallel[1], places=12)
        self.assertEqual(serial[2], parallel[2])

    def test_dtd_official_splits_cover_without_overlap(self):
        path = Path(__file__).resolve().parents[1] / "results/confirmatory/sample_manifests/DTD.csv"
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 5640)
        for split in range(1, 11):
            train, test = runner.official_split_indices(rows, split)
            self.assertLessEqual(len(train), 3760)
            self.assertGreaterEqual(len(train), 3740)
            self.assertEqual(len(test), 1880)
            self.assertFalse(set(train).intersection(test))
            self.assertFalse({rows[i]["group"] for i in train}.intersection(
                {rows[i]["group"] for i in test}
            ))

    def test_two_role_official_split_is_supported(self):
        rows = [
            {"official_split": "train", "group": "a"},
            {"official_split": "train", "group": "b"},
            {"official_split": "test", "group": "c"},
            {"official_split": "test", "group": "d"},
        ]
        train, test = runner.official_split_indices(rows, 1)
        self.assertEqual(train.tolist(), [0, 1])
        self.assertEqual(test.tolist(), [2, 3])

    def test_curet_manifest_preserves_condition_groups_and_halves(self):
        path = Path(__file__).resolve().parents[1] / "results/confirmatory/sample_manifests/CUReT.csv"
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 61 * 92)
        self.assertEqual([int(row["row_id"]) for row in rows], list(range(len(rows))))
        self.assertEqual(len({row["class_name"] for row in rows}), 61)
        self.assertEqual(Counter(row["class_name"] for row in rows),
                         Counter({f"sample{i:02d}": 92 for i in range(1, 62)}))
        by_group = defaultdict(list)
        for row in rows:
            by_group[row["group"]].append(row)
        self.assertEqual(len(by_group), 92)
        for group_rows in by_group.values():
            self.assertEqual(len(group_rows), 61)
            self.assertEqual(len({row["class_name"] for row in group_rows}), 61)
            self.assertEqual(len({row["benchmark_half"] for row in group_rows}), 1)
        group_halves = Counter(group_rows[0]["benchmark_half"] for group_rows in by_group.values())
        self.assertEqual(group_halves, Counter({"alternating_a": 46, "alternating_b": 46}))
        self.assertEqual(len({row["sha256"] for row in rows}), len(rows))
        self.assertEqual({row["split_provenance"] for row in rows},
                         {"deterministic alternating reproduction"})

    def test_reextract_datasets_are_not_linked(self):
        path = Path(__file__).resolve().parents[1] / "results/confirmatory/sample_manifests/manifest_status.json"
        statuses = {r["dataset"]: r["status"] for r in json.loads(path.read_text())["datasets"]}
        self.assertEqual(statuses["DTD"], "LINKED_ORDER_LABEL_EXACT")
        self.assertEqual(statuses["FMD"], "REEXTRACT_REQUIRED")
        self.assertEqual(statuses["VisTex_official"], "REEXTRACT_REQUIRED")
        self.assertEqual(statuses["CUReT_official_full"], "REEXTRACT_REQUIRED")

    def test_curet_half_indices_validate_both_directions(self):
        path = Path(__file__).resolve().parents[1] / "results/confirmatory/sample_manifests/CUReT.csv"
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        for direction, expected_train, expected_test in (
            ("a_to_b", "alternating_a", "alternating_b"),
            ("b_to_a", "alternating_b", "alternating_a"),
        ):
            train, test = curet_protocol.curet_half_indices(rows, direction)
            self.assertIsInstance(train, np.ndarray)
            self.assertIsInstance(test, np.ndarray)
            self.assertEqual(train.dtype, np.int64)
            self.assertEqual(test.dtype, np.int64)
            self.assertEqual(len(train), 2806)
            self.assertEqual(len(test), 2806)
            self.assertEqual({rows[index]["benchmark_half"] for index in train}, {expected_train})
            self.assertEqual({rows[index]["benchmark_half"] for index in test}, {expected_test})
            self.assertEqual(len({rows[index]["group"] for index in train}), 46)
            self.assertEqual(len({rows[index]["group"] for index in test}), 46)
            self.assertFalse(set(train).intersection(test))
            self.assertFalse(
                {rows[index]["group"] for index in train}.intersection(
                    {rows[index]["group"] for index in test}
                )
            )

    def test_curet_half_indices_reject_basic_manifest_errors(self):
        with self.assertRaisesRegex(ValueError, "direction"):
            curet_protocol.curet_half_indices([{
                "benchmark_half": "alternating_a", "group": "002", "label": "0"
            }], "invalid")
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            curet_protocol.curet_half_indices([], "a_to_b")
        with self.assertRaisesRegex(ValueError, "missing columns"):
            curet_protocol.curet_half_indices([{"benchmark_half": "alternating_a"}], "a_to_b")

    def test_curet_half_indices_reject_group_crossing_halves(self):
        path = Path(__file__).resolve().parents[1] / "results/confirmatory/sample_manifests/CUReT.csv"
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        corrupted = [dict(row) for row in rows]
        corrupted[0]["benchmark_half"] = "alternating_b"
        with self.assertRaisesRegex(ValueError, "spans multiple benchmark halves"):
            curet_protocol.curet_half_indices(corrupted, "a_to_b")

    def test_curet_runner_rejects_conflicting_or_misapplied_direction(self):
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            runner.run_condition(None, None, "CUReT", "svm", 42, 0, 100, 8, False,
                                 official_split=1, curet_direction="a_to_b")
        script = Path(__file__).resolve().parents[1] / "src/run_confirmatory_nested.py"
        completed = subprocess.run([
            sys.executable, str(script), "--dataset", "FMD", "--classifier", "svm",
            "--seed", "42", "--fold", "0", "--curet-direction", "a_to_b",
        ], text=True, capture_output=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("only valid with --dataset CUReT", completed.stderr)

    def test_curet_orchestrator_dry_run_directions_and_protocol(self):
        script = Path(__file__).resolve().parents[1] / "experiments/run_confirmatory.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            output = repo / "results/confirmatory"
            output.mkdir(parents=True)
            (output / "data_audit.csv").write_text("dataset,status\nCUReT,PASS_REEXTRACTED_GROUP_AWARE\n")
            for smoke, expected in ((False, ["a_to_b", "b_to_a"]), (True, ["a_to_b"])):
                command = [sys.executable, str(script), "--repo", str(repo),
                           "--datasets", "CUReT", "--classifiers", "svm"]
                if smoke:
                    command.append("--smoke")
                subprocess.run(command, check=True, text=True, capture_output=True)
                manifest = json.loads((output / "run_manifest.json").read_text())
                self.assertEqual([row["curet_direction"] for row in manifest["conditions"]], expected)
                self.assertEqual([row["fold"] for row in manifest["conditions"]], list(range(len(expected))))
                self.assertEqual({row["seed"] for row in manifest["conditions"]}, {42})
                self.assertEqual(
                    manifest["project_protocols"]["CUReT"],
                    "deterministic complementary reproduction; not an official historical split",
                )
                if not smoke:
                    checkpoints = output / "checkpoints"
                    checkpoints.mkdir(parents=True, exist_ok=True)
                    (checkpoints / "CUReT__svm__42__a_to_b__full.json").write_text("{}\n")
                    subprocess.run(command, check=True, text=True, capture_output=True)
                    resumed = json.loads((output / "run_manifest.json").read_text())["conditions"]
                    self.assertEqual([row["status"] for row in resumed], ["complete", "pending"])

    def test_confirmatory_orchestrator_preserves_dtd_fmd_default_schedule(self):
        script = Path(__file__).resolve().parents[1] / "experiments/run_confirmatory.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            output = repo / "results/confirmatory"
            output.mkdir(parents=True)
            (output / "data_audit.csv").write_text(
                "dataset,status\nDTD,PASS_OFFICIAL_SPLITS_PURGED_DUPLICATES\n"
                "FMD,PASS_REEXTRACTED_GROUP_AWARE\n"
            )
            subprocess.run([
                sys.executable, str(script), "--repo", str(repo),
                "--datasets", "DTD", "FMD", "--classifiers", "svm",
            ], check=True, text=True, capture_output=True)
            conditions = json.loads((output / "run_manifest.json").read_text())["conditions"]
            dtd = [row for row in conditions if row["dataset"] == "DTD"]
            fmd = [row for row in conditions if row["dataset"] == "FMD"]
            self.assertEqual(len(dtd), 10)
            self.assertEqual([row["official_split"] for row in dtd], list(range(1, 11)))
            self.assertEqual(len(fmd), 15)
            self.assertEqual({row["seed"] for row in fmd}, {42, 123, 2026})
            self.assertEqual(Counter(row["fold"] for row in fmd), Counter({i: 3 for i in range(5)}))


if __name__ == "__main__":
    unittest.main()
