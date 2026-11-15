"""Saved-data ARS analyses preserve estimands, dependence limits and sources."""
from pathlib import Path
import hashlib
import importlib.util
import json

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ars_existing", ROOT/"scripts/analyze_ars_existing_results_20261115.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
AUDIT = ROOT/"results/analysis/ars_revision_existing_analyses_20261115_v1"


def test_observed_ranges_and_lodo_are_dataset_balanced_not_condition_pooled():
    frame = pd.DataFrame({"id":["a1","a2","b1"],"dataset":["A","A","B"],
                          "direct_accuracy":[.5,.5,.5],"cascade_accuracy":[.4,.6,.8]})
    rows, ranges, lodo = module.observed_variation(frame)
    a = ranges.set_index("dataset").loc["A"]
    assert a.min_difference_pp == pytest.approx(-10)
    assert a.q25_difference_pp == pytest.approx(-5)
    assert a.median_difference_pp == pytest.approx(0)
    assert a.q75_difference_pp == pytest.approx(5)
    assert a.max_difference_pp == pytest.approx(10)
    assert lodo.iloc[0].mean_difference_pp == pytest.approx(15)
    assert rows.accuracy_difference_pp.mean() == pytest.approx(10)
    assert lodo.set_index("excluded_dataset").loc["A","mean_difference_pp"] == pytest.approx(30)


def test_duplicate_or_nonfinite_conditions_cannot_enter_descriptive_ranges():
    frame = pd.DataFrame({"id":["a","a"],"dataset":["A","A"],
                          "direct_accuracy":[.5,.5],"cascade_accuracy":[.6,.7]})
    with pytest.raises(ValueError):
        module.observed_variation(frame)
    frame.loc[1,"id"] = "b"
    frame.loc[1,"cascade_accuracy"] = np.nan
    with pytest.raises(ValueError):
        module.observed_variation(frame)


def test_sensitivity_keeps_families_and_explicit_exclusion_scope():
    result=json.loads((AUDIT/"static_accuracy_sensitivity.json").read_text())
    for classifier, scopes in result.items():
        full=scopes["all_six"]
        assert full["datasets"] == 6 and full["permutations"] == 46656
        five=scopes["without_kth"]
        assert five["datasets"] == 5 and five["permutations"] == 7776
        assert "KTHTIPS2b" not in five["included_datasets"]
        assert five["excluded_datasets"] == ["KTHTIPS2b"]
        assert five["methods"] == ["Individual","Completa-22","Top-4"]
        assert len(five["pairs"]) == 3
        assert all(r["p_exact"] <= r["p_holm"] <= 1 for r in five["pairs"])
    assert result["svm"]["without_kth"]["friedman_p_exact"] == pytest.approx(.12422839506172839)
    assert result["resmlp"]["without_kth"]["friedman_p_exact"] == pytest.approx(.5216049382716049)


def test_source_integrity_and_no_new_experiments_or_population_intervals():
    p=json.loads((AUDIT/"provenance.json").read_text())
    for group in ["sources","outputs"]:
        for name, expected in p[group].items():
            assert module.sha(ROOT/name) == expected
    s=json.loads((AUDIT/"summary.json").read_text())
    assert s["new_fits"] == s["new_extractions"] == s["new_model_predictions"] == s["new_timing_calls"] == 0
    assert not s["confidence_intervals_reported"] and s["canonical_sources_unchanged"]
    ranges=pd.read_csv(AUDIT/"e1_dataset_observed_ranges.csv")
    assert ranges.conditions.sum() == 27 and len(ranges) == 6
    lodo=pd.read_csv(AUDIT/"e1_leave_one_dataset_out.csv")
    assert len(lodo) == 7 and lodo.iloc[0].datasets == 6
