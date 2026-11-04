import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from consolidate_cellnn_external import coverage


def parts(n,dataset='FMD'):
    return [{'dataset':dataset,'seed':42,'outer_fold':f} for f in range(n)]


def test_no_partial_dataset_aggregate():
    with pytest.raises(ValueError): coverage('FMD',parts(14),2800,False)


def test_individual_only_requires_exact_missing_failed_identity():
    p=[{'dataset':'FMD','seed':s,'outer_fold':f} for s in (42,123,2026) for f in range(5) if (s,f)!=(42,0)]
    assert coverage('FMD',p,2800,True) is False
    p[0]={'dataset':'FMD','seed':42,'outer_fold':0}
    with pytest.raises(ValueError): coverage('FMD',p,2800,True)


def test_full_other_dataset():
    assert coverage('CUReT',parts(2,'CUReT'),5612,False) is True
    with pytest.raises(ValueError): coverage('CUReT',parts(1,'CUReT'),2806,True)


def test_duplicate_and_wrong_call_counts_fail():
    p=parts(2,'CUReT')
    with pytest.raises(ValueError): coverage('CUReT',[p[0],p[0]],5612,False)
    with pytest.raises(ValueError): coverage('CUReT',p,5600,False)
