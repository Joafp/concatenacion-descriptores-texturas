"""Infrastructure fix cannot authorize repeating an executed neural block."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_kth_siglip_unexecuted import json_safe, verify_unexecuted_parent


def parent():
    return json.loads((ROOT / "results/analysis/kth_reference_validation_20261115_v1/status.json").read_text())


def test_loading_report_sets_are_serialized_without_dropping_keys():
    value = {"missing_keys": set(), "unexpected_keys": {"text_model.b", "text_model.a"},
             "mismatched_keys": set(), "nested": [{"a": frozenset(["x", "y"])}]}
    actual = json.loads(json.dumps(json_safe(value)))
    assert actual == {"missing_keys": [], "unexpected_keys": ["text_model.a", "text_model.b"],
                      "mismatched_keys": [], "nested": [{"a": ["x", "y"]}]}


def test_actual_parent_has_zero_siglip_forwards_and_accepted_eva():
    verify_unexecuted_parent(parent())


@pytest.mark.parametrize("field,value", [("neural_forward_calls_invoked", 39), ("warmup_calls", 6),
                                         ("evaluated_calls", 34), ("status", "requires_review"),
                                         ("phase", "measurement")])
def test_even_one_executed_siglip_call_or_scientific_failure_forbids_continuation(field, value):
    record = parent()
    record[field] = value
    with pytest.raises(ValueError):
        verify_unexecuted_parent(record)
