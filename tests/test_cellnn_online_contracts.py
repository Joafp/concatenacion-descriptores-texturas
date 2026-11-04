import copy
import csv
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pytest
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
import cellnn_online_adapter as module
from cellnn_online_adapter import head_params_json,checked_probabilities,CellNNOnlineAdapter
from run_cellnn_external_condition import audit_records
from prepare_cellnn_fmd_queue import validate_fmd


class FakeHead:
    classes_=np.arange(10)
    n_features_in_=768
    def get_params(self): return head_params_json()
    def predict_proba(self,features):
        assert features.shape==(1,768)
        return np.asarray([[0,0,0,1,0,0,0,0,0,0]],dtype=float)


def test_full_timer_encloses_extract_and_head(monkeypatch):
    route=CellNNOnlineAdapter(torch.nn.Identity(),list(range(10)),FakeHead())
    events=[]
    route.synchronize=lambda:events.append('sync')
    route.extract_file=lambda path:events.append('extract') or np.zeros((1,768))
    clock=iter((100,350));monkeypatch.setattr(module,'perf_counter_ns',lambda:events.append('clock') or next(clock))
    result=route.predict_file('synthetic')
    assert events==['sync','clock','extract','sync','clock']
    assert result['prediction']==3 and result['elapsed_ns']==250 and result['elapsed_ms']==0.00025
    assert 'probabilities' in result and 'logits' not in result


@pytest.mark.parametrize('values',[[[0.1]*9],[[float('nan')]*10],[[0.2]*10],[[-1]+[2]+[0]*8]])
def test_reject_invalid_probabilities(values):
    with pytest.raises(ValueError): checked_probabilities(values,list(range(10)))


def test_head_class_order_is_frozen():
    with pytest.raises(ValueError): CellNNOnlineAdapter(torch.nn.Identity(),list(reversed(range(10))),FakeHead())


def records():
    p={'external_indices':[0,1],'labels':[0,1]};rows=[{'label':'0'},{'label':'1'}]
    calls=[{'row_index':i,'truth':i,'repeat':0,'class_order':[0,1],'prediction':i,
        'probabilities':[1-i,i],'elapsed_ns':1000000,'elapsed_ms':1.0} for i in (0,1)]
    return calls,p,rows


def test_same_call_audit():
    result=audit_records(*records())
    assert result['macro_f1_online']==1 and result['calls']==2 and result['mean_ms']==1


@pytest.mark.parametrize('kind',['missing','duplicate','truth','prediction','class_order','time','repeat'])
def test_audit_rejects_corrupt_calls(kind):
    calls,p,rows=records()
    if kind=='missing': calls.pop()
    elif kind=='duplicate': calls[1]['row_index']=0
    elif kind=='truth': calls[1]['truth']=0
    elif kind=='prediction': calls[1]['prediction']=0
    elif kind=='class_order': calls[1]['class_order']=[1,0]
    elif kind=='time': calls[1]['elapsed_ms']=2
    else: calls[1]['repeat']=1
    with pytest.raises(ValueError): audit_records(calls,p,rows)


def fmd_fixture():
    rows=[{'row_id':str(i),'label':str(i%10),'group':str(i)} for i in range(1000)]
    conditions=[{'dataset':'FMD','seed':s,'outer_fold':f,'head_params':head_params_json(),'labels':list(range(10)),
        'external_indices':list(range(200*f,200*(f+1))),
        'training_indices':[i for i in range(1000) if i not in range(200*f,200*(f+1))]}
        for s in (42,123,2026) for f in range(5)]
    return conditions,rows


def test_fixed_fmd_coverage_and_head_params(): validate_fmd(*fmd_fixture())


@pytest.mark.parametrize('kind',['missing','identity','classes','head','groups'])
def test_preflight_rejects_drift(kind):
    p,rows=fmd_fixture()
    if kind=='missing': p.pop()
    elif kind=='identity': p[0]['seed']=0
    elif kind=='classes': p[0]['labels'].pop()
    elif kind=='head': p[0]['head_params']['max_iter']=100
    else: rows[0]['group']=rows[300]['group']
    with pytest.raises(ValueError): validate_fmd(p,rows)


class SyntheticMLP:
    def __init__(self,**params): self.params=params
    def fit(self,x,y):
        self.classes_=np.unique(y);self.coefs_=[np.zeros((768,10))];self.intercepts_=[np.zeros(10)]
        self.n_iter_=2;self.loss_curve_=[2.0,1.0];return self


class SyntheticRoute:
    provenance={'synthetic_test_only':True}
    def extract_file(self,path): return np.ones((1,768),dtype=np.float32)
    def predict_file(self,path):
        return {'prediction':0,'probabilities':[1.0]+[0.0]*9,'class_order':list(range(10)),
            'elapsed_ns':1000000,'elapsed_ms':1.0}


def test_four_stage_receipts_without_network_gpu_or_real_images(tmp_path,monkeypatch):
    import run_cellnn_external_condition as runner
    import sklearn.neural_network
    monkeypatch.setattr(sklearn.neural_network,'MLPClassifier',SyntheticMLP)
    monkeypatch.setattr(runner,'adapter',lambda *args,**kwargs:SyntheticRoute())
    rows=[]
    for i in range(20):
        path=tmp_path/f'{i}.synthetic';path.write_bytes(str(i).encode())
        rows.append({'row_id':i,'path':str(path),'label':i%10,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    csv_path=tmp_path/'manifest.csv'
    with csv_path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    p={'dataset':'synthetic','seed':42,'outer_fold':0,'training_indices':list(range(10)),
        'external_indices':list(range(10,20)),'labels':list(range(10)),
        'manifest':str(csv_path),'head_params':head_params_json()}
    manifest=tmp_path/'preflight.json'
    manifest.write_text(json.dumps({'conditions':[p],'source_sha256':{},'checkpoint':'not loaded in test',
        'checkpoint_sha256':'synthetic only'}))
    job=tmp_path/'job'
    for stage in ('extract','train','online','audit'):
        runner.run(manifest,0,stage,job)
        assert json.loads((job/stage/'status.json').read_text())['status']==stage+'_complete'
    summary=json.loads((job/'audit/summary.json').read_text())
    assert summary['calls']==10 and summary['same_call_quality_and_timing'] is True
    assert summary['class_values']=='probabilities'
