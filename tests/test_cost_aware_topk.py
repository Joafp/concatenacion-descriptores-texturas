"""The cost-aware route never consults held-out labels for selection."""

import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from report_cost_aware_topk import choose_route, component_costs, evaluate_one  # noqa: E402


class CostAwareTopkTests(unittest.TestCase):
    def test_direct_topk_when_cheap_stage_would_add_cost(self):
        route, base, incremental, direct = choose_route(
            ["resnet50"], ["beit"], {"resnet50": 37.0, "beit": 33.0}, 0.5
        )
        self.assertEqual((route, base, incremental, direct),
                         ("topk_direct", 37.0, 33.0, 33.0))

    def test_reuse_of_shared_block_is_incremental(self):
        route, base, incremental, direct = choose_route(
            ["beit"], ["beit", "dino"], {"beit": 33.0, "dino": 476.0}, 0.5
        )
        self.assertEqual((route, base, incremental, direct),
                         ("cascade", 33.0, 476.0, 509.0))

    def test_test_request_rate_and_scores_do_not_select_route(self):
        entry = {
            "dataset": "toy", "protocol": "split", "outer_fold": 0,
            "cheap_blocks": ["cheap"], "expensive_blocks": ["expensive"],
            "topk_always": {"macro_f1": 0.9},
        }
        row = {"target_budget": 0.5, "observed_request_fraction": 0.01,
               "adaptive": {"macro_f1": 1.0}}
        result = evaluate_one(entry, row, {"cheap": 80.0, "expensive": 100.0})
        self.assertEqual(result["selected_route"], "topk_direct")
        self.assertEqual(result["macro_f1"], 0.9)
        self.assertEqual(result["component_cost_ms"], 100.0)

    def test_mismatched_extractor_cannot_supply_cost_evidence(self):
        source = {
            "per_descriptor_latency_ms": {
                "ok": {"mean": 20.0}, "bad": {"mean": 10.0},
            },
            "method_routes": {
                "route": {"extractor_min_cosine": {"ok": 0.9999, "bad": 0.5}},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "timing.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            self.assertEqual(component_costs(path), {"ok": 20.0})


if __name__ == "__main__":
    unittest.main()
