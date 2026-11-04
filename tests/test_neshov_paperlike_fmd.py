from collections import Counter
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_neshov_paperlike_fmd import build_partitions
import run_neshov_paperlike_fmd_condition as runner


def rows():
    return [{'row_id':str(i),'label':str(i//100),'group':str(i)} for i in range(1000)]


def test_100_stratified_folds_cover_all_images_once_per_repetition():
    parts=build_partitions(rows(),'/fmd.csv')
    assert len(parts)==100 and {p['seed'] for p in parts}==set(range(42,421,42))
    for rep in range(1,11):
        group=[p for p in parts if p['repetition']==rep]
        assert Counter(i for p in group for i in p['external_indices'])==Counter(range(1000))
        assert all(len(p['training_indices'])==900 and len(p['external_indices'])==100 for p in group)
    assert build_partitions(rows(),'/fmd.csv')==parts


def test_rejects_group_leak_and_class_drift():
    data=rows();data[-1]['label']='8'
    with pytest.raises(ValueError): build_partitions(data,'/fmd.csv')
    data=rows();data[0]['group']=data[1]['group']
    with pytest.raises(ValueError): build_partitions(data,'/fmd.csv')


def test_head_training_uses_recorded_repetition_seed(tmp_path,monkeypatch):
    import numpy as np
    import torch
    import neshov_reference_training as training
    extract=tmp_path/'extract';extract.mkdir();out=tmp_path/'train';out.mkdir()
    np.savez_compressed(extract/'features.npz',rows=[0,1,2,3],features=np.zeros((4,3072),dtype=np.float32))
    seen={}
    def fake_fit(x,y,n_classes,**kwargs):
        seen.update(kwargs);return torch.nn.Linear(3072,n_classes),[{'epoch':1}]
    monkeypatch.setattr(runner.core,'verify_artifact',lambda *args: None)
    monkeypatch.setattr(runner.core,'digest',lambda *args:'synthetic')
    monkeypatch.setattr(training,'fit_fixed_head',fake_fit)
    part={'training_indices':[0,1,2,3],'labels':[0,1],'training_seed':84}
    result=runner.train_head(part,[{'label':str(i%2)} for i in range(4)],extract,out)
    assert seen['seed']==84 and seen['epochs']==100 and seen['batch_size']==32
    assert result['training_seed']==84
