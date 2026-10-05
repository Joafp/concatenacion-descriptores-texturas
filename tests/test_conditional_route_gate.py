"""Invariants for the exploratory train-fitted routing evaluation."""

import sys
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_conditional_route_gate import (  # noqa: E402
    choose, matched_component_sample, metrics, route_predictions,
)


class ConditionalRouteGateTests(unittest.TestCase):
    def test_gate_selects_base_below_train_only_threshold(self):
        utility = np.array([
            [0.4, 0.1, 0.2, 0.3],
            [0.1, 0.5, 0.2, 0.3],
            [-0.2, -0.1, -0.3, -0.4],
        ])
        self.assertEqual(choose(utility, 0.5, 0.35).tolist(), [1, 2, 0])

    def test_selected_predictions_and_costs_follow_route_ids(self):
        y = np.array([0, 1, 0])
        route_ids = np.array([0, 1, 2])
        predictions = {
            "small": np.array([0, 0, 1]),
            "small_beit": np.array([1, 1, 1]),
            "small_base": np.array([1, 0, 0]),
            "small_large": np.array([1, 0, 1]),
            "small_base_large": np.array([1, 0, 1]),
        }
        costs = {
            "small": 10.0,
            "small_beit": 20.0,
            "small_base": 30.0,
            "small_large": 40.0,
            "small_base_large": 50.0,
        }
        selected = route_predictions(route_ids, predictions)
        self.assertEqual(selected.tolist(), y.tolist())
        result = metrics(y, selected, route_ids, costs)
        self.assertEqual(result["macro_f1"], 1.0)
        self.assertEqual(result["component_cost_mean_ms"], 20.0)
        self.assertEqual(result["request_fraction"], 2 / 3)

    def test_matched_component_cost_uses_selected_row_and_route(self):
        timing = {
            "rows": [20, 10],
            "per_descriptor_latency_ms": {
                "dinov2_small": {"durations_ms": [10.0, 20.0]},
                "beitv2_base_final": {"durations_ms": [3.0, 4.0]},
                "dinov2": {"durations_ms": [7.0, 8.0]},
                "dinov2_large": {"durations_ms": [9.0, 11.0]},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "timing.json"
            path.write_text(json.dumps(timing), encoding="utf-8")
            result = matched_component_sample(
                path, np.array([10, 20]), np.array([1, 0])
            )
        self.assertEqual(result["mean_ms"], 17.0)


if __name__ == "__main__":
    unittest.main()
