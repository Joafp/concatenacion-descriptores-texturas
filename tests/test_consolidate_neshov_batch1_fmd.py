from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from consolidate_neshov_batch1_fmd import aggregate


def test_aggregate_complete_and_time_weighted():
    rows=[dict(local_classifier=h,local_method=m,calls=200,local_f1=0.8,reference_f1=0.7,
               local_mean_ms=40.,reference_mean_ms=20.) for h in ('svm','resmlp')
               for m in ('a','b','c','d','e') for _ in range(15)]
    output=aggregate(rows)
    assert len(output)==10 and output[0]['calls']==3000
    assert output[0]['reference_mean_ms_all_calls']==20 and output[0]['latency_ratio_reference_over_local']==0.5
    with pytest.raises(ValueError): aggregate(rows[:-1])
