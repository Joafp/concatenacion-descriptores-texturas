import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from run_topk_individual_control import outer_indices


class TopKControlTests(unittest.TestCase):
    def test_grouped_outer_split_has_no_leakage(self):
        y = np.repeat(np.arange(5), 20)
        groups = np.arange(len(y))
        train, test = outer_indices("Synthetic", 42, 0, y, groups, [])
        self.assertFalse(set(groups[train]).intersection(groups[test]))

    def test_split_is_deterministic(self):
        y = np.repeat(np.arange(5), 20)
        groups = np.arange(len(y))
        first = outer_indices("Synthetic", 42, 1, y, groups, [])
        second = outer_indices("Synthetic", 42, 1, y, groups, [])
        np.testing.assert_array_equal(first[0], second[0])
        np.testing.assert_array_equal(first[1], second[1])


if __name__ == "__main__":
    unittest.main()
