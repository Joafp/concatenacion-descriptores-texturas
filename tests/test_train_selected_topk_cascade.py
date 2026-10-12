import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_train_selected_topk_cascade import select_route


class TrainSelectionTests(unittest.TestCase):
    def setUp(self):
        self.margins = np.array([0.1, 0.2, 0.7, 0.8])
        self.labels = np.array([0, 1, 0, 1])
        self.cheap = np.array([1, 1, 0, 1])
        self.topk = self.labels.copy()
        self.costs = {"cheap": 1.0, "other": 9.0}

    def test_selection_uses_only_training_inputs(self):
        result = select_route(self.margins, self.cheap, self.topk, self.labels,
                              self.costs, ["cheap"], ["cheap", "other"], 0.005)
        self.assertEqual(result["selected"]["route"], "cascade")
        self.assertEqual(result["selected"]["budget"], 0.25)
        self.assertEqual(result["selected"]["oof_macro_f1"], 1.0)

    def test_accuracy_guard_falls_back_to_direct(self):
        result = select_route(self.margins, self.cheap, self.topk, self.labels,
                              self.costs, ["cheap"], ["cheap", "other"], 0)
        # First low-margin error can be fixed with the 25% request.
        self.assertEqual(result["selected"]["route"], "cascade")
        result = select_route(self.margins, np.array([1, 0, 1, 0]), self.topk,
                              self.labels, self.costs, ["cheap"],
                              ["cheap", "other"], 0)
        self.assertEqual(result["selected"]["route"], "topk_direct")

    def test_rejects_missing_costs_and_invalid_tolerance(self):
        with self.assertRaises(ValueError):
            select_route(self.margins, self.cheap, self.topk, self.labels,
                         {"cheap": 1.0}, ["cheap"], ["cheap", "other"], 0.005)
        with self.assertRaises(ValueError):
            select_route(self.margins, self.cheap, self.topk, self.labels,
                         self.costs, ["cheap"], ["cheap", "other"], -0.1)


if __name__ == "__main__":
    unittest.main()
