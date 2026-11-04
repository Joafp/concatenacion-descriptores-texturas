import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("static_general", ROOT / "scripts/run_static_budget_control_general.py")
general = importlib.util.module_from_spec(spec)
spec.loader.exec_module(general)


@pytest.mark.parametrize("size", [680, 800])
def test_coverage_is_computed_without_relaxing_unique_rows(size):
    assert general.development_coverage(np.array_split(np.arange(size), 3)) == size


def test_overlap_cannot_be_hidden_by_a_dataset_size_change():
    with pytest.raises(ValueError):
        general.development_coverage([[1, 2], [2, 3], [4]])


def test_the_selector_is_the_same_implementation_as_the_original():
    spec2 = importlib.util.spec_from_file_location("static_original", ROOT / "scripts/run_static_budget_control.py")
    original = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(original)
    assert general.select_static_ensembles is original.select_static_ensembles
    assert general.fit_scores is original.fit_scores
