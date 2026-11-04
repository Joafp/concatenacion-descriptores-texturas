import copy
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_authorized_paper_infra_recovery import recover_payload, CHECKPOINT_SHA


def condition(dataset, seed=42, fold=0, n=680):
    return dict(dataset=dataset, seed=seed, outer_fold=fold,
                training_indices=[1001,1002], external_indices=list(range(n)), labels=[0,1])


def test_hytex_metadata_only_and_original_not_changed():
    p=condition('Outex13Official1360'); old={'conditions':[p],'source_sha256':{'x':'y'}}
    before=copy.deepcopy(old)
    new=recover_payload(old,'HyTex_Outex13Official1360_s42_f0',
        {'status':'requires_review','error':"KeyError: 'checkpoint_sha256'"},
        "KeyError: 'checkpoint_sha256'",CHECKPOINT_SHA)
    assert old==before and new['conditions']==old['conditions']
    assert new['checkpoint_sha256']==CHECKPOINT_SHA
    assert new['planned_online_calls']==680 and not new['paper_scores_reproduced']


def test_cellnn_only_failed_condition_same_indices():
    old={'conditions':[condition('FMD',n=200),condition('FMD',fold=1,n=200)]}
    err='TypeError: Object of type float32 is not JSON serializable'
    new=recover_payload(old,'CellNN_FMD_s42_f0',{'status':'requires_review','error':err},err,CHECKPOINT_SHA)
    assert new['conditions']==old['conditions'][:1] and len(old['conditions'])==2
    assert new['planned_online_calls']==200


@pytest.mark.parametrize('state',[{'status':'complete'}, {'status':'running'},
    {'status':'requires_review','error':'ValueError: batch1/batch8 feature parity failed; requires review'}])
def test_scientific_failures_and_other_states_excluded(state):
    with pytest.raises(ValueError):
        recover_payload({'conditions':[condition('Outex13Official1360')]},'HyTex_x',
                        state,"KeyError: 'checkpoint_sha256'",CHECKPOINT_SHA)


def test_hytex_wrong_hash_rejected():
    err="KeyError: 'checkpoint_sha256'"
    with pytest.raises(ValueError):
        recover_payload({'conditions':[condition('Outex13Official1360')]},'HyTex_x',
                        {'status':'requires_review','error':err},err,'bad')
