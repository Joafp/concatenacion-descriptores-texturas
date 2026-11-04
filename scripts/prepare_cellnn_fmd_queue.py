"""Freeze independent complete CellNN ADAPTED FMD system; no fits or predictions."""
import argparse
from collections import Counter
import csv
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from consolidate_overnight_online_panel import read,digest
from prepare_neshov_fmd_external import validate_partition
from cellnn_reference import CHECKPOINT_SHA
from cellnn_online_adapter import head_params_json,METHOD


def validate_fmd(conditions,rows):
    ids={(p['seed'],p['outer_fold']) for p in conditions}
    if len(conditions)!=15 or ids!={(s,f) for s in (42,123,2026) for f in range(5)} or len(rows)!=1000:
        raise ValueError('complete FMD identities required')
    if any(int(r['row_id'])!=i for i,r in enumerate(rows)): raise ValueError('row order drift')
    for p in conditions:
        if (p['dataset']!='FMD' or len(p['training_indices'])!=800 or len(p['external_indices'])!=200
                or validate_partition(p['training_indices'],p['external_indices'],rows)!=list(range(10))
                or p['labels']!=list(range(10)) or p['head_params']!=head_params_json()):
            raise ValueError('FMD coverage/class/config mismatch')
    for seed in (42,123,2026):
        if Counter(i for p in conditions if p['seed']==seed for i in p['external_indices'])!=Counter({i:1 for i in range(1000)}):
            raise ValueError('full external coverage per seed required')


def prepare(output):
    output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    origin=ROOT/'results/analysis/hytex_fmd_external_queue_20261102_v1/preflight.json'
    previous=read(origin)
    for path,sha in previous['source_sha256'].items():
        if digest(path)!=sha: raise ValueError('archived FMD source drift')
    conditions=[]
    for old in previous['conditions']:
        p={key:old[key] for key in ('dataset','seed','outer_fold','training_indices','external_indices','labels','manifest')}
        p['head_params']=head_params_json();conditions.append(p)
    mp=Path(conditions[0]['manifest'])
    if any(Path(p['manifest'])!=mp for p in conditions): raise ValueError('inconsistent manifests')
    with mp.open(newline='') as stream: rows=list(csv.DictReader(stream))
    validate_fmd(conditions,rows)
    for r in rows:
        if digest(ROOT/r['path'])!=r['sha256']: raise ValueError('image drift')
    parity=ROOT/'results/analysis/cellnn_synthetic_parity_20261102_v1/status.json'
    if digest(parity)!='623308ebbda02ff562dd428e01e3dc91f5ba0be5a0d686de80c2d232b2cbe92e' or read(parity)['status']!='synthetic_parity_complete':
        raise ValueError('fixed synthetic gate required')
    provenance=parity.parent/'provenance.json'
    for path,sha in read(provenance)['source_sha256'].items():
        if digest(ROOT/path)!=sha: raise ValueError('synthetic gate source drift')
    bundle=ROOT/'results/analysis/cellnn_author_bundle_20261102_v1/receipt.json'
    sources={str(p):digest(p) for p in (origin,mp,parity,provenance,bundle)}
    for r in read(bundle)['artifacts']:
        if digest(r['local_path'])!=r['sha256']: raise ValueError('author artifact drift')
        sources[r['local_path']]=r['sha256']
    checkpoint=bundle.parent/'cellnn_model.ph'
    if digest(checkpoint)!=CHECKPOINT_SHA: raise ValueError('checkpoint drift')
    for name in ('src/cellnn_reference.py','src/cellnn_online_adapter.py',
        'scripts/run_cellnn_external_condition.py','scripts/prepare_cellnn_fmd_queue.py',
        'scripts/run_authorized_remediation_queue.py','scripts/run_neshov_external_condition.py',
        'scripts/consolidate_overnight_online_panel.py','scripts/prepare_neshov_fmd_external.py',
        'src/neshov_online_adapter.py','src/neshov_beit_reference.py',
        'docs/fsc_tex/PROTOCOLO_CELLNN_ADAPTACION_FMD_2026-11-02.md'):
        sources[str(ROOT/name)]=digest(ROOT/name)
    output.mkdir(parents=True,exist_ok=False);frozen=output/'preflight.json'
    frozen.write_text(json.dumps({'status':'CELLNN_FMD_ADAPTATION_FROZEN_NOT_EXECUTED',
        'conditions':conditions,'source_sha256':sources,'unique_conditions':15,'planned_online_calls':3000,
        'unique_images_hashed':1000,'checkpoint':str(checkpoint),'checkpoint_sha256':CHECKPOINT_SHA,
        'method':METHOD,'head_params':head_params_json()},indent=2)+'\n')
    tasks=[]
    for number,p in enumerate(conditions):
        name=f'CellNN_FMD_s{p["seed"]}_f{p["outer_fold"]}';job=output/'jobs'/name;commands=[]
        for stage,timeout in [('extract',7200),('train',3600),('online',14400),('audit',300)]:
            commands.append({'argv':[sys.executable,str(ROOT/'scripts/run_cellnn_external_condition.py'),
                '--manifest',str(frozen),'--number',str(number),'--stage',stage,'--job',str(job)],
                'timeout_seconds':timeout,'success':{'path':str(job/stage/'status.json'),'fields':{'status':stage+'_complete'}}})
        tasks.append({'id':name,'lane':'gpu','depends_on':[] if not tasks else [tasks[0]['id']],
            'observe':False,'exclusive_outputs':[str(job/s) for s in ('extract','train','online','audit')],'commands':commands})
    manifest={'schema':1,'no_auto_retry':True,'python_version':sys.version,
        'source_sha256':{**sources,str(frozen):digest(frozen)},'tasks':tasks,'gpu_lock':'results/analysis/gpu.lock',
        'packages':{p:importlib.metadata.version(p) for p in ('numpy','torch','opencv-python','scikit-image','scikit-learn','scipy','joblib')},
        'scope':METHOD}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'tasks':len(tasks),'manifest_sha256':digest(output/'manifest.json')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
