import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rgb_ngram_descriptor import RGBNgramSVDBlock


class RGBNgramDescriptorTests(unittest.TestCase):
    def test_hashing_is_fixed_and_svd_is_fitted_from_training_only(self):
        counts = {
            "keys": np.asarray([1, 2, 1, 3, 2, 3, 999], dtype=np.uint64),
            "counts": np.asarray([2, 1, 1, 2, 2, 1, 10], dtype=np.int64),
            "indptr": np.asarray([0, 2, 4, 6, 7], dtype=np.int64),
        }
        block = RGBNgramSVDBlock(counts, n_components=2, random_state=7, hash_bins=16)
        x_train, x_eval, audit = block.transform(np.asarray([0, 1, 2]), np.asarray([3]))
        self.assertEqual(x_train.shape, (3, 2))
        self.assertEqual(x_eval.shape, (1, 2))
        self.assertEqual(audit["hash_bins"], 16)
        self.assertTrue(audit["fixed_label_free_hashing"])
        self.assertTrue(audit["svd_from_training_only"])
        self.assertTrue(np.isfinite(x_eval).all())

    def test_fold_cache_is_keyed_by_train_and_evaluation_rows(self):
        counts = {
            "keys": np.asarray([1, 2, 1, 3, 2, 3], dtype=np.uint64),
            "counts": np.ones(6, dtype=np.int64),
            "indptr": np.asarray([0, 2, 4, 6], dtype=np.int64),
        }
        block = RGBNgramSVDBlock(counts, n_components=1, random_state=3)
        first = block.transform(np.asarray([0, 1]), np.asarray([2]))
        second = block.transform(np.asarray([0, 1]), np.asarray([2]))
        self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main()
