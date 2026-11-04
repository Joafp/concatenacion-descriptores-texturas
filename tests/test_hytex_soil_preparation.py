import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_hytex_soil_queue import validate_soil,frozen_payload,CHECKPOINT_SHA


def fixture():
    rows=[{'row_id':str(i),'label':i%7,'group':str(i)} for i in range(1140)]
    conditions=[]
    for s in (42,123,2026):
        offset=0
        sizes=[228]*5 if s!=123 else [228,229,228,227,228]
        for f,n in enumerate(sizes):
            test=list(range(offset,offset+n));offset+=n
            conditions.append({'dataset':'SoilOriginal','seed':s,'outer_fold':f,
                'labels':list(range(7)),'external_indices':test,
                'training_indices':sorted(set(range(1140))-set(test))})
    return conditions,rows


def test_full_unequal_folds(): validate_soil(*fixture())


@pytest.mark.parametrize('kind',['count','identity','overlap','group','classes','rows'])
def test_reject_corruption(kind):
    c,r=fixture()
    if kind=='count': c.pop()
    elif kind=='identity': c[0]['seed']=0
    elif kind=='overlap': c[0]['training_indices'].append(0)
    elif kind=='group': r[0]['group']=r[300]['group']
    elif kind=='classes': c[0]['labels'].pop()
    else: r[0]['row_id']='1'
    with pytest.raises(ValueError): validate_soil(c,r)


def test_frozen_contract_includes_checkpoint_before_dispatch():
    conditions,_=fixture();p=frozen_payload(conditions,{})
    assert p['checkpoint_sha256']==CHECKPOINT_SHA and len(p['checkpoint_sha256'])==64
    assert p['conditions']==conditions and p['planned_online_calls']==sum(len(c['external_indices']) for c in conditions)
    assert p['method']=='HyTexNet adapted; local fixed configuration'
