"""Small invariants for the exploratory conditional-route screen."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_conditional_route_feasibility import oof_predictions, summarize  # noqa: E402


class ConditionalRouteFeasibilityTests(unittest.TestCase):
    def test_oracle_is_retrospective_union_of_correct_predictions(self):
        y = np.array([0, 1, 0, 1])
        predictions = {
            "small": np.array([0, 0, 0, 0]),
            "extension": np.array([1, 1, 0, 1]),
        }
        result = summarize(predictions, y)
        self.assertEqual(result["oracle_correct"], 4)
        self.assertEqual(result["correction_vs_small"]["extension"], {
            "fixes_small": 2,
            "breaks_small": 1,
        })

    def test_oof_never_uses_the_outer_test_or_crosses_groups(self):
        y = np.array([0, 1] * 8)
        groups = np.array([f"g{i}" for i in range(len(y))])
        x = np.column_stack([y, np.arange(len(y)) / len(y)])
        outer_train = np.arange(12)
        predictions, audit = oof_predictions(
            {"small": x}, y, groups, outer_train, seed=42, n_splits=3
        )
        self.assertEqual(len(predictions["small"]), len(outer_train))
        self.assertTrue(np.all(predictions["small"] >= 0))
        self.assertEqual(sum(fold["n_validation"] for fold in audit), len(outer_train))
        self.assertTrue(all(fold["n_fit"] < len(y) for fold in audit))


if __name__ == "__main__":
    unittest.main()
