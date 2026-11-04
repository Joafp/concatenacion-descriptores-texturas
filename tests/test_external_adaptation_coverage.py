import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_external_adaptation_coverage import row_from_summary,DATASETS


def test_no_means_from_partial():
    s={'conditions':14,'calls':2800,'full_dataset_complete':False,'dataset_means_reported':False,
        'paper_scores_reproduced':False,'same_call_quality_and_timing':True}
    r=row_from_summary('LBP+dCellNN adapted','FMD',s)
    assert not r['full_dataset_complete'] and r['mean_split_macro_f1'] is None and r['mean_ms_all_calls'] is None
    with pytest.raises(ValueError): row_from_summary('LBP+dCellNN adapted','FMD',{**s,'mean_split_macro_f1':0.5})


def test_full_dataset_keeps_own_means_only():
    s={'conditions':2,'calls':5612,'mean_split_macro_f1':0.7,'mean_ms_all_calls':31,
        'paper_scores_reproduced':False,'same_call_quality_and_timing':True}
    assert row_from_summary('LBP+dCellNN adapted','CUReT',s)['mean_split_macro_f1']==0.7


def test_per_system_not_two_heads_arithmetic():
    assert sum(x[1] for x in DATASETS.values())==47
    assert sum(x[2] for x in DATASETS.values())==36264
