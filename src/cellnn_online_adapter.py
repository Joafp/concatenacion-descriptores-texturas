"""Full file-to-class CellNN ADAPTED route, including synchronized single-call time."""
import hashlib
import json
from pathlib import Path
from time import perf_counter_ns
import numpy as np
import torch
from sklearn.neural_network import MLPClassifier
from cellnn_reference import load_network,decode_blue,extract_blue,CHECKPOINT_SHA

METHOD='6LBP+dCellNN+MLP adapted; author299502c; local fixed configuration'
HEAD_PARAMS=dict(hidden_layer_sizes=(400,),activation='relu',solver='adam',alpha=0.0001,
    batch_size='auto',learning_rate='constant',learning_rate_init=0.001,power_t=0.5,
    max_iter=10000,shuffle=True,random_state=42,tol=0.0001,verbose=False,warm_start=False,
    momentum=0.9,nesterovs_momentum=True,early_stopping=False,validation_fraction=0.1,
    beta_1=0.9,beta_2=0.999,epsilon=1e-8,n_iter_no_change=10,max_fun=15000)


def checked_hash(path,expected):
    if not expected or hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:
        raise ValueError('artifact SHA256 mismatch')


def head_params_json():
    return json.loads(json.dumps(MLPClassifier(**HEAD_PARAMS).get_params()))


def checked_probabilities(values,labels):
    values=np.asarray(values)
    if (values.shape!=(1,len(labels)) or not np.isfinite(values).all()
            or np.any(values<0) or np.any(values>1) or abs(float(values.sum())-1)>1e-6):
        raise ValueError('invalid class probabilities')
    return values


class CellNNOnlineAdapter:
    def __init__(self,network,labels,head=None,device='cpu'):
        self.device=torch.device(device)
        if self.device.type not in ('cpu','cuda'): raise ValueError('CPU/CUDA required')
        self.labels=tuple(labels)
        if len(self.labels)<2 or len(set(self.labels))!=len(self.labels): raise ValueError('distinct labels required')
        self.network=network.to(self.device).eval();self.network.requires_grad_(False)
        self.head=head
        if head is not None:
            if list(head.classes_)!=list(self.labels) or head.n_features_in_!=768:
                raise ValueError('head class order/dimension mismatch')
            if json.loads(json.dumps(head.get_params()))!=head_params_json():
                raise ValueError('head parameters drift')

    @classmethod
    def from_offline(cls,checkpoint,checkpoint_sha,labels,head_path=None,head_sha=None,device='cuda'):
        if checkpoint_sha!=CHECKPOINT_SHA: raise ValueError('unapproved checkpoint')
        checked_hash(checkpoint,checkpoint_sha)
        network=load_network(checkpoint,device=device)
        head=None
        if head_path is not None:
            import joblib
            checked_hash(head_path,head_sha)
            head=joblib.load(head_path)
            if not isinstance(head,MLPClassifier): raise ValueError('MLP head required')
        result=cls(network,labels,head,device)
        result.provenance={'method':METHOD,'checkpoint':str(checkpoint),'checkpoint_sha256':checkpoint_sha,
            'head_sha256':head_sha,'contour_device':str(result.device),'head_device':'cpu',
            'contour_precision':'float32','feature_cache':False,'class_values':'predict_proba'}
        return result

    def synchronize(self):
        if self.device.type=='cuda': torch.cuda.synchronize(self.device)

    def extract_file(self,path):
        return extract_blue(decode_blue(path),self.network,str(self.device))

    def predict_file(self,path):
        if self.head is None: raise ValueError('trained head required')
        self.synchronize();started=perf_counter_ns()
        features=self.extract_file(path)
        probabilities=checked_probabilities(self.head.predict_proba(features),self.labels)
        prediction=self.labels[int(np.argmax(probabilities[0]))]
        self.synchronize();elapsed=perf_counter_ns()-started
        return {'prediction':int(prediction),'probabilities':probabilities[0].tolist(),
            'class_order':list(self.labels),'elapsed_ns':elapsed,'elapsed_ms':elapsed/1e6}
