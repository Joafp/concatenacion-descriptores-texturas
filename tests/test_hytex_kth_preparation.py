import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_hytex_kth_queue import validate_kth,frozen_payload,CHECKPOINT_SHA


def fixture():
    rows=[]
    for i in range(4752):
        sample='abcd'[i%4]
        rows.append({'row_id':str(i),'label':i%11,'sample':sample,'group':str(i),
            **{f'split_{f+1}':'train' if i%4==f else 'test' for f in range(4)}})
    conditions=[{'dataset':'KTHTIPS2b','seed':42,'outer_fold':f,'labels':list(range(11)),
        'external_indices':[i for i in range(4752) if i%4==f],
        'training_indices':[i for i in range(4752) if i%4!=f]} for f in range(4)]
    return conditions,rows


def test_exact_three_train_one_test(): validate_kth(*fixture())


@pytest.mark.parametrize('kind',['missing','identity','inversion','sample','group','classes','row'])
def test_reject_corruption(kind):
    p,r=fixture()
    if kind=='missing': p.pop()
    elif kind=='identity': p[0]['seed']=123
    elif kind=='inversion': p[0]['training_indices'],p[0]['external_indices']=p[0]['external_indices'],p[0]['training_indices']
    elif kind=='sample': r[1]['sample']='a'
    elif kind=='group': r[0]['group']=r[1]['group']
    elif kind=='classes': p[0]['labels'].pop()
    else: r[0]['row_id']='99'
    with pytest.raises(ValueError): validate_kth(p,r)


def test_complete_runner_contract_and_reserve():
    p,r=fixture();payload=frozen_payload(p,{})
    assert payload['checkpoint_sha256']==CHECKPOINT_SHA
    assert payload['historical_kth_protocol_reserve'] is True
    assert payload['planned_online_calls']==sum(len(x['external_indices']) for x in p)==4752
