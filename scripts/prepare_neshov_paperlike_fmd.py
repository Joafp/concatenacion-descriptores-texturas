"""Freeze an explicitly approximate Neshov FMD 10x10 split panel."""
import argparse
from collections import Counter
import csv
import importlib.metadata
import json
from pathlib import Path
import sys
from consolidate_overnight_online_panel import ROOT, read, digest
from run_authorized_remediation_queue import verify_sources

FMD=ROOT/'results/analysis/neshov_fmd_batch1_queue_20261102_v1'
SUMMARY=ROOT/'results/analysis/neshov_fmd_batch1_external_summary_20261102_v1/summary.json'
PROTOCOL=ROOT/'docs/fsc_tex/PROTOCOLO_NESHOV_FMD_10X10_APROX_2026-11-02.md'


def build_partitions(rows, manifest_path):
    import numpy as np
    from sklearn.model_selection import StratifiedKFold
    if len(rows)!=1000 or any(int(r['row_id'])!=i for i,r in enumerate(rows)):
        raise ValueError('expected ordered 1000-row FMD manifest')
    labels=np.asarray([int(r['label']) for r in rows]); groups=[r['group'] for r in rows]
    if sorted(set(labels))!=list(range(10)) or Counter(labels)!=Counter({i:100 for i in range(10)}):
        raise ValueError('ten balanced FMD classes required')
    partitions=[]
    for repetition in range(1,11):
        seed=42*repetition;folds=StratifiedKFold(n_splits=10,shuffle=True,random_state=seed)
        seen=[]
        for fold,(train,test) in enumerate(folds.split(np.zeros(len(rows)),labels)):
            train,test=train.tolist(),test.tolist()
            if (len(train)!=900 or len(test)!=100 or set(train)&set(test)
                    or {groups[i] for i in train}&{groups[i] for i in test}
                    or Counter(labels[test])!=Counter({i:10 for i in range(10)})):
                raise ValueError('fold identity, class or group mismatch')
            seen.extend(test)
            partitions.append({'dataset':'FMD','seed':seed,'repetition':repetition,'outer_fold':fold,
                'training_indices':train,'external_indices':test,'labels':list(range(10)),
                'manifest':str(manifest_path),'training_seed':seed,'epochs':100,'head_batch':32})
        if Counter(seen)!=Counter(range(1000)): raise ValueError('test coverage drift')
    return partitions


def prepare(output):
    output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    base,worker,old=[read(FMD/f) for f in ('manifest.json','gpu.json','preflight.json')];summary=read(SUMMARY)
    if (worker['status']!='all_tasks_terminal' or worker.get('current_task') is not None
            or worker['manifest_sha256']!=digest(FMD/'manifest.json') or len(worker['outcomes'])!=15
            or set(worker['outcomes'].values())!={'complete'} or summary['conditions']!=15 or summary['calls']!=3000):
        raise ValueError('complete common FMD prerequisite')
    verify_sources(base)
    image_manifest=Path(old['conditions'][0]['manifest'])
    with image_manifest.open(newline='') as stream: rows=list(csv.DictReader(stream))
    for row in rows:
        if digest(ROOT/row['path'])!=row['sha256']: raise ValueError('image hash drift')
    parts=build_partitions(rows,image_manifest)
    if len(parts)!=100 or sum(len(p['external_indices']) for p in parts)!=10000:
        raise ValueError('complete 10x10 expected')
    sources=dict(base['source_sha256'])
    for path in (FMD/'manifest.json',FMD/'gpu.json',SUMMARY,image_manifest,PROTOCOL,
                 ROOT/'scripts/run_neshov_paperlike_fmd_condition.py',Path(__file__).resolve()):
        sources[str(path)]=digest(path)
    split_version=importlib.metadata.version('scikit-learn')
    payload={**old,'status':'NESHOV_FMD_PAPERLIKE_10X10_FROZEN_NOT_EXECUTED',
        'conditions':parts,'unique_conditions':100,'planned_online_calls':10000,
        'source_sha256':sources,'protocol':str(PROTOCOL),'paper_scores_reproduced':False,
        'split_generator_version':split_version,
        'split_assumptions':'stratified; repetitions 1..10; seed=42*repetition; reset head per fold',
        'claim_boundary':'paper-like approximation, not exact source reproduction'}
    output.mkdir(parents=True,exist_ok=False);preflight=output/'preflight.json'
    preflight.write_text(json.dumps(payload,indent=2)+'\n');sources[str(preflight)]=digest(preflight)
    tasks=[]
    for number,p in enumerate(parts):
        name=f'NeshovPaperLike_FMD_r{p["repetition"]}_f{p["outer_fold"]}';job=output/'jobs'/name;commands=[]
        for stage,timeout in [('extract',7200),('train',1800),('online',14400),('audit',300)]:
            commands.append({'argv':[sys.executable,str(ROOT/'scripts/run_neshov_paperlike_fmd_condition.py'),
                '--manifest',str(preflight),'--number',str(number),'--stage',stage,'--job',str(job)],
                'timeout_seconds':timeout,'success':{'path':str(job/stage/'status.json'),
                'fields':{'status':stage+'_complete'}}})
        tasks.append({'id':name,'lane':'gpu','depends_on':[] if not tasks else [tasks[0]['id']],
            'observe':False,'exclusive_outputs':[str(job/s) for s in ('extract','train','online','audit')],
            'commands':commands})
    manifest={**base,'tasks':tasks,'source_sha256':sources,
        'packages':{**base['packages'],'scikit-learn':split_version},
        'scope':'Neshov FMD 10x10 paper-like approximation; exact original splits/versions unverified'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'conditions':100,'planned_calls':10000,'manifest_sha256':digest(output/'manifest.json')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
