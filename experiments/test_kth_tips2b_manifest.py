#!/usr/bin/env python3
"""Synthetic tests for the KTH-TIPS2-b manifest builder (no real dataset needed)."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

BUILDER_PATH = (
    Path(__file__).resolve().parents[1]
    / "results/confirmatory/recovery/kth_tips2b/build_kth_tips2b_manifest.py"
)
SPEC = importlib.util.spec_from_file_location("kth_tips2b_manifest_builder", BUILDER_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)


def make_synthetic_archive(root: Path) -> None:
    """11 materials x 4 samples x 108 images, each file with unique byte content."""
    for material_index in range(builder.EXPECTED_MATERIALS):
        material = f"material_{material_index:02d}"
        for sample in builder.SAMPLE_LETTERS:
            sample_dir = root / material / f"sample_{sample}"
            sample_dir.mkdir(parents=True)
            for image_index in range(builder.EXPECTED_IMAGES_PER_SAMPLE):
                path = sample_dir / f"img_{image_index:03d}.png"
                path.write_bytes(f"{material}-{sample}-{image_index}".encode())


class KthTips2bManifestTests(unittest.TestCase):
    def test_synthetic_archive_yields_expected_row_count_and_passes_all_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "KTH-TIPS2-b"
            make_synthetic_archive(root)
            rows = builder.build_rows(root, workspace=root)
            self.assertEqual(len(rows), builder.EXPECTED_TOTAL_IMAGES)
            checks = builder.validate(rows)
            self.assertTrue(all(checks.values()), checks)

    def test_official_split_columns_rotate_train_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "KTH-TIPS2-b"
            make_synthetic_archive(root)
            rows = builder.build_rows(root, workspace=root)
            for row in rows:
                for split_number, train_letter in enumerate(builder.SAMPLE_LETTERS, start=1):
                    expected_role = "train" if row["sample"] == train_letter else "test"
                    self.assertEqual(row[f"split_{split_number}"], expected_role)
            # Every row's own sample is "train" in exactly one of the four splits.
            for row in rows:
                train_splits = [
                    n for n in range(1, 5) if row[f"split_{n}"] == "train"
                ]
                self.assertEqual(len(train_splits), 1)

    def test_missing_sample_directory_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "KTH-TIPS2-b"
            make_synthetic_archive(root)
            # Remove one sample directory entirely for the first material.
            import shutil

            first_material = sorted(root.iterdir())[0]
            shutil.rmtree(first_material / "sample_d")
            with self.assertRaises(SystemExit):
                builder.build_rows(root, workspace=root)

    def test_wrong_image_count_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "KTH-TIPS2-b"
            make_synthetic_archive(root)
            first_material = sorted(root.iterdir())[0]
            extra = first_material / "sample_a" / "extra.png"
            extra.write_bytes(b"unexpected extra image")
            with self.assertRaises(SystemExit):
                builder.build_rows(root, workspace=root)

    def test_group_and_row_ids_are_unique_and_source_paths_relative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "KTH-TIPS2-b"
            make_synthetic_archive(root)
            rows = builder.build_rows(root, workspace=root)
            self.assertEqual(len({r["row_id"] for r in rows}), len(rows))
            self.assertEqual(len({r["group"] for r in rows}), len(rows))
            for row in rows:
                self.assertFalse(Path(row["source_path"]).is_absolute())


if __name__ == "__main__":
    unittest.main()
