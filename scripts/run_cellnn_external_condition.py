"""Four fixed CellNN adaptation stages. Scientific failure is terminal, never retry."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import sys
import warnings

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from run_neshov_external_condition import read,write,digest,utc,verify_artifact
from consolidate_overnight_online_panel import macro_f1
from cellnn_online_adapter import CellNNOnlineAdapter,METHOD,HEAD_PARAMS,head_params_json,checked_probabilities


def adapter(manifest,p,job=None):
    if job is None: return CellNNOnlineAdapter.from_offline(manifest['checkpoint'],manifest['checkpoint_sha256'],p['labels'])
    status=verify_artifact(job/'train','train_complete')
    return CellNNOnlineAdapter.from_offline(manifest['checkpoint'],manifest['checkpoint_sha256'],p['labels'],
        job/'train/head.joblib',status['output_sha256']['head.joblib'])


def extract(p,rows,manifest,output):
    import numpy as np
    route=adapter(manifest,p)
    features=[]
    for number,index in enumerate(p['training_indices']):
        path=ROOT/rows[index]['path']
        if digest(path)!=rows[index]['sha256']: raise ValueError('training image drift')
        vector=route.extract_file(path)
        if vector.shape!=(1,768) or not np.isfinite(vector).all(): raise ValueError('invalid training features')
        features.append(vector[0])
        if number%50==0: print(f'extracted {number+1}/{len(p["training_indices"])}',flush=True)
    features=np.asarray(features)
    np.savez_compressed(output/'features.npz',rows=p['training_indices'],features=features)
    again=np.asarray([route.extract_file(ROOT/rows[p['training_indices'][pos]]['path'])[0] for pos in (0,len(features)-1)])
    cached=features[[0,-1]]
    np.savez_compressed(output/'parity_vectors.npz',cached=cached,reextracted=again)
    exact=np.array_equal(cached,again)
    write(output/'parity.json',{'exact':exact,'max_abs_error':float(np.max(np.abs(cached-again))),
        'regime':'batch1 vs batch1; 768 count histograms'})
    if not exact: raise ValueError('own-route exact feature consistency failed; requires review')
    return {'fit_images':len(features),'parity_exact':True,'adapter':route.provenance}


def train(p,rows,job,output):
    import joblib
    import numpy as np
    from sklearn.neural_network import MLPClassifier
    from sklearn.exceptions import ConvergenceWarning
    previous=verify_artifact(job/'extract','extract_complete')
    data=np.load(job/'extract/features.npz',allow_pickle=False)
    if not np.array_equal(data['rows'],p['training_indices']): raise ValueError('fit order drift')
    if p['head_params']!=head_params_json(): raise ValueError('frozen head configuration drift')
    truth=np.asarray([int(rows[i]['label']) for i in p['training_indices']])
    model=MLPClassifier(**HEAD_PARAMS)
    with warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        model.fit(data['features'],truth)
    if list(model.classes_)!=p['labels'] or any(not np.isfinite(v).all() for v in model.coefs_+model.intercepts_):
        raise ValueError('invalid fitted classifier')
    joblib.dump(model,output/'head.joblib')
    write(output/'head_params.json',head_params_json())
    write(output/'training_history.json',{'n_iter':int(model.n_iter_),'loss_curve':model.loss_curve_,
        'stopping':'source MLP tol/n_iter_no_change; max_iter10000; no test validation'})
    return {'extraction_status_sha256':digest(job/'extract/status.json'),'iterations':int(model.n_iter_),
        'converged_within_budget':True,'head_params':head_params_json()}


def online(p,rows,manifest,job,output):
    import platform
    route=adapter(manifest,p,job)
    write(output/'environment.json',{'utc':utc(),'pid':os.getpid(),'platform':platform.platform(),
        'python':sys.version,'cpu_threads':2,'hardware_isolated':False,'adapter':route.provenance})
    for _ in range(5): route.predict_file(ROOT/rows[p['training_indices'][0]]['path'])
    with (output/'calls.jsonl').open('x') as stream:
        for number,index in enumerate(p['external_indices']):
            row=rows[index];path=ROOT/row['path']
            if digest(path)!=row['sha256']: raise ValueError('external image drift')
            stamp=utc();result=route.predict_file(path)
            stream.write(json.dumps({'row_index':index,'truth':int(row['label']),'repeat':0,
                'started_utc':stamp,**result},allow_nan=False)+'\n');stream.flush()
            if number%25==0: print(f'online {number+1}/{len(p["external_indices"])}',flush=True)
    return {'calls':len(p['external_indices']),'warmup_calls_excluded':5,
        'head_status_sha256':digest(job/'train/status.json'),'class_values':'probabilities'}


def audit_records(calls,p,rows):
    import numpy as np
    if not calls or [r['row_index'] for r in calls]!=p['external_indices'] or len(set(p['external_indices']))!=len(calls):
        raise ValueError('full unique ordered call coverage required')
    for r in calls:
        probabilities=checked_probabilities([r['probabilities']],p['labels'])
        if (r['class_order']!=p['labels'] or r['truth']!=int(rows[r['row_index']]['label']) or r['repeat']!=0
                or r['prediction']!=p['labels'][int(probabilities.argmax())] or type(r['elapsed_ns']) is not int
                or r['elapsed_ns']<=0 or not math.isfinite(r['elapsed_ms']) or r['elapsed_ms']!=r['elapsed_ns']/1e6):
            raise ValueError('same-call prediction/truth/timing mismatch')
    times=[r['elapsed_ms'] for r in calls]
    return {'calls':len(calls),'macro_f1_online':macro_f1([r['truth'] for r in calls],[r['prediction'] for r in calls]),
        'accuracy_online':sum(r['truth']==r['prediction'] for r in calls)/len(calls),
        'mean_ms':float(np.mean(times)),'median_ms':float(np.median(times)),
        'p95_ms':float(np.percentile(times,95)),'same_call_quality_and_timing':True,
        'class_values':'probabilities','method':METHOD}


def audit(p,rows,job,output):
    verify_artifact(job/'online','online_complete')
    calls=[json.loads(line) for line in (job/'online/calls.jsonl').read_text().splitlines()]
    result={**audit_records(calls,p,rows),'online_status_sha256':digest(job/'online/status.json')}
    write(output/'summary.json',result)
    return result


def run(manifest_path,number,stage,job):
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
    import torch
    import cv2
    torch.set_num_threads(2);cv2.setNumThreads(2);torch.manual_seed(42);torch.use_deterministic_algorithms(True)
    manifest=read(manifest_path)
    for path,sha in manifest['source_sha256'].items():
        if digest(path)!=sha: raise ValueError('source drift: '+path)
    p=manifest['conditions'][number]
    with Path(p['manifest']).open(newline='') as stream: rows=list(csv.DictReader(stream))
    job=Path(job);output=job/stage;output.mkdir(parents=True,exist_ok=False)
    report={'status':'running','stage':stage,'started_utc':utc(),'method':METHOD,'partition':p,
        'manifest_sha256':digest(manifest_path),'runner_sha256':digest(__file__)}
    write(output/'status.json',report)
    try:
        if stage=='extract': result=extract(p,rows,manifest,output)
        elif stage=='train': result=train(p,rows,job,output)
        elif stage=='online': result=online(p,rows,manifest,job,output)
        else: result=audit(p,rows,job,output)
        report.update(result,status=stage+'_complete',finished_utc=utc(),
            output_sha256={f.name:digest(f) for f in output.iterdir() if f.name!='status.json'})
        write(output/'status.json',report)
    except Exception as exc:
        report.update(status='requires_review',error=f'{type(exc).__name__}: {exc}',finished_utc=utc())
        write(output/'status.json',report)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--number',type=int,required=True);parser.add_argument('--stage',choices=['extract','train','online','audit'],required=True)
    parser.add_argument('--job',type=Path,required=True);a=parser.parse_args();run(a.manifest,a.number,a.stage,a.job)
