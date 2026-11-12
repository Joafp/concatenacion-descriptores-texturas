import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_outex_crosscalls_20261104 import macro_f1, unique_by_id


def test_macro_f1_counts_missing_predictions_and_all_classes():
    assert macro_f1([0, 0, 1, 1], [0, 0, 0, 0]) == pytest.approx(1 / 3)
    assert macro_f1([0, 1], [0, 1]) == 1.0
    with pytest.raises(ValueError):
        macro_f1([0], [])


def test_duplicate_image_ids_rejected():
    with pytest.raises(ValueError):
        unique_by_id([{'row_index': '3'}, {'row_index': '3'}])
