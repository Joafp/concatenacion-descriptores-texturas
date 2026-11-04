from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from consolidate_paper_infra_recoveries import checked_coverage, summarize


def test_complete_fmd_aggregates_means_using_actual_calls():
    records = [dict(dataset='FMD', seed=s, outer_fold=f, calls=200,
                    macro_f1_online=0.5, mean_ms=20 + f)
               for s in (42,123,2026) for f in range(5)]
    summary = summarize(records, 'FMD', 'test')
    assert summary['calls'] == 3000 and summary['mean_ms_all_calls'] == 22
    assert summary['mean_split_macro_f1'] == 0.5
    assert not summary['paper_scores_reproduced']


def test_partial_duplicate_and_call_drift_rejected():
    records = [dict(seed=42, outer_fold=i, calls=200) for i in range(2)]
    assert checked_coverage(records, {(42,0),(42,1)}, 400)
    with pytest.raises(ValueError): checked_coverage(records[:1], {(42,0),(42,1)}, 400)
    with pytest.raises(ValueError): checked_coverage(records+[records[0]], {(42,0),(42,1)}, 600)
    with pytest.raises(ValueError): checked_coverage(records, {(42,0),(42,1)}, 399)
