"""Freeze four never-executed KTH common-panel adaptation conditions."""
import argparse
from collections import Counter
import csv
import importlib.metadata
import json
from pathlib import Path
import sys

from consolidate_overnight_online_panel import ROOT,read,digest,select_jobs
from prepare_hytex_fmd_queue import CHECKPOINT_SHA
from prepare_hytex_outex_queue import label_digest,validate_archived_truth
from prepare_neshov_fmd_external import validate_partition

DATASET='KTHTIPS2b'


def validate_kth(conditions,rows):
    if (len(rows)!=4752 or any(int(r['row_id'])!=i for i,r in enumerate(rows)) or len(conditions)!=4
            or {(p['seed'],p['outer_fold']) for p in conditions}!={(42,f) for f in range(4)}):
        raise ValueError('full KTH identities required')
    for p in conditions:
        f=p['outer_fold'];test=[i for i,r in enumerate(rows) if r[f'split_{f+1}']=='train']
        train=[i for i,r in enumerate(rows) if r[f'split_{f+1}']=='test']
        if (p['dataset']!=DATASET or len(train)!=3564 or len(test)!=1188
                or train!=p['training_indices'] or test!=p['external_indices']
                or validate_partition(train,test,rows)!=list(range(11)) or p['labels']!=list(range(11))):
            raise ValueError('exact inverted common KTH partition required')
        a,b={rows[i]['sample'] for i in train},{rows[i]['sample'] for i in test}
        if len(a)!=3 or len(b)!=1 or a&b or a|b!={'a','b','c','d'}:
            raise ValueError('physical sample leakage/coverage')
    if Counter(i for p in conditions for i in p['external_indices'])!=Counter({i:1 for i in range(4752)}):
        raise ValueError('KTH full external coverage required')


def frozen_payload(conditions,sources):
    return {'dataset':DATASET,'conditions':conditions,'source_sha256':sources,
        'checkpoint_sha256':CHECKPOINT_SHA,'unique_conditions':4,'planned_online_calls':4752,
        'unique_images_hashed':4752,'method':'HyTexNet adapted; local fixed configuration',
        'historical_kth_protocol_reserve':True}


def prepare(output):
    import numpy as np
    from huggingface_hub import hf_hub_download
    output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    jobs,sources=select_jobs(ROOT);local=[j for j in jobs if j['dataset']==DATASET]
    if len(local)!=8: raise ValueError('both heads and4folds required')
    selected,canonical={},None
    for j in local:
        qp,op=Path(j['quality_run'])/'status.json',Path(j['online_run'])/'status.json'
        q,o=read(qp),read(op)
        if (q['status']!='external_quality_complete_timing_pending' or digest(qp)!=o['quality_status_sha256']
                or digest(j['config'])!=j['config_sha256']): raise ValueError('local lineage drift')
        args=read(j['config'])['provenance']['arguments']
        if args['official_split']!=j['outer_fold']+1 or args['invert_official_split'] is not True or args['inner_group_column']!='sample':
            raise ValueError('KTH protocol drift')
        mp=ROOT/q['provenance']['manifest_path']
        if digest(mp)!=q['provenance']['manifest_sha256']: raise ValueError('manifest drift')
        with mp.open(newline='') as stream: original=list(csv.DictReader(stream))
        mapping={};values=np.asarray([mapping.setdefault(r['label'],len(mapping)) for r in original],dtype=np.int64)
        if label_digest(values)!=q['provenance']['labels_sha256']: raise ValueError('full canonical label hash mismatch')
        rows=[{**r,'original_label':r['label'],'label':int(values[i]),
            'path':str(ROOT/r['source_path']),'sha256':r['source_sha256']} for i,r in enumerate(original)]
        if canonical is not None and rows!=canonical: raise ValueError('head manifests disagree')
        canonical=rows
        pp=Path(j['quality_run'])/'predictions.csv'
        if digest(pp)!=q['output_sha256']['predictions.csv']: raise ValueError('truth file drift')
        with pp.open(newline='') as stream: validate_archived_truth(list(csv.DictReader(stream)),q['external_indices'],rows)
        p={'dataset':DATASET,'seed':j['seed'],'outer_fold':j['outer_fold'],
            'official_split':j['outer_fold']+1,'invert_official_split':True,'inner_group_column':'sample',
            'training_indices':q['training_indices'],'external_indices':q['external_indices'],
            'labels':list(range(11)),'manifest':str(output/'canonical_manifest.csv'),
            'training_seed':42,'epochs':100,'head_batch':32}
        if p['outer_fold'] in selected and selected[p['outer_fold']]!=p: raise ValueError('head partition disagreement')
        selected[p['outer_fold']]=p
        for path in (qp,op,mp,pp,Path(j['config'])): sources[str(path)]=digest(path)
    conditions=[selected[f] for f in range(4)];validate_kth(conditions,canonical)
    for r in canonical:
        if digest(r['path'])!=r['sha256']: raise ValueError('image drift')
    checkpoint=Path(hf_hub_download('timm/densenet121.tv_in1k','model.safetensors',local_files_only=True))
    if digest(checkpoint)!=CHECKPOINT_SHA: raise ValueError('checkpoint drift')
    for name in ('src/hytex_reference.py','src/hytex_online_adapter.py','src/hytex_fixed_training.py',
        'src/neshov_online_adapter.py','src/neshov_beit_reference.py',
        'scripts/run_hytex_external_condition.py','scripts/run_neshov_external_condition.py',
        'scripts/consolidate_overnight_online_panel.py','scripts/prepare_hytex_fmd_queue.py',
        'scripts/prepare_hytex_outex_queue.py','scripts/prepare_hytex_kth_queue.py',
        'scripts/prepare_neshov_fmd_external.py','scripts/run_authorized_remediation_queue.py',
        'docs/fsc_tex/PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md',
        'docs/fsc_tex/PROTOCOLO_HYTEX_EXTENSION_KTH_2026-11-02.md'):
        sources[str(ROOT/name)]=digest(ROOT/name)
    sources[str(checkpoint)]=CHECKPOINT_SHA
    output.mkdir(parents=True,exist_ok=False);cp=output/'canonical_manifest.csv'
    with cp.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(canonical[0]));writer.writeheader();writer.writerows(canonical)
    sources[str(cp)]=digest(cp);frozen=output/'preflight.json'
    frozen.write_text(json.dumps(frozen_payload(conditions,sources),indent=2)+'\n')
    tasks=[]
    for number,p in enumerate(conditions):
        name=f'HyTex_{DATASET}_s42_f{number}';job=output/'jobs'/name;commands=[]
        for stage,timeout in [('extract',7200),('train',1800),('online',14400),('audit',300)]:
            commands.append({'argv':[sys.executable,str(ROOT/'scripts/run_hytex_external_condition.py'),
                '--manifest',str(frozen),'--number',str(number),'--stage',stage,'--job',str(job)],
                'timeout_seconds':timeout,'success':{'path':str(job/stage/'status.json'),'fields':{'status':stage+'_complete'}}})
        tasks.append({'id':name,'lane':'gpu','depends_on':[] if not tasks else [tasks[0]['id']],
            'observe':False,'exclusive_outputs':[str(job/s) for s in ('extract','train','online','audit')],'commands':commands})
    manifest={'schema':1,'no_auto_retry':True,'python_version':sys.version,
        'source_sha256':{**sources,str(frozen):digest(frozen)},'gpu_lock':'results/analysis/gpu.lock','tasks':tasks,
        'packages':{p:importlib.metadata.version(p) for p in ('numpy','torch','torchvision','timm','Pillow','huggingface-hub','safetensors')},
        'scope':'KTH common panel: HyTexNet adapted; historical reserve retained'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'tasks':len(tasks),'manifest_sha256':digest(output/'manifest.json')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
