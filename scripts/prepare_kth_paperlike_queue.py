"""Prepare one disclosed 1/3 KTH adaptation per method, without model execution."""
import argparse
from collections import Counter
import copy
import csv
import json
from pathlib import Path
import re
import sys
from consolidate_overnight_online_panel import ROOT, digest, read
from run_authorized_remediation_queue import verify_sources

PROTOCOL=ROOT/'docs/fsc_tex/PROTOCOLO_KTH_TERCIO_PAPERLIKE_2026-11-02.md'
METHODS=(('HyTex','hytex_kth_external_queue_20261102_v1','run_hytex_external_condition.py'),
         ('CellNN','cellnn_kth_external_queue_20261102_v1','run_cellnn_external_condition_v2.py'))


def partition(rows,manifest_path):
    if len(rows)!=4752 or any(int(r['row_id'])!=i for i,r in enumerate(rows)):
        raise ValueError('exact KTH row identity required')
    train=[];test=[];training_samples=set();test_samples=set()
    for i,row in enumerate(rows):
        match=re.search(r'scale_(\d+)_im_(\d+)_col\.png$',row['path'],re.IGNORECASE)
        if not match: raise ValueError('unrecognized KTH image identity')
        scale,image=map(int,match.groups())
        if scale not in range(2,11) or image not in range(1,13): raise ValueError('KTH code outside official range')
        sample=(int(row['label']),row['sample'])
        if scale in range(2,8) and image in range(1,7):
            train.append(i);training_samples.add(sample)
        else:
            test.append(i);test_samples.add(sample)
    if (len(train)!=1584 or len(test)!=3168 or len(training_samples)!=44
            or training_samples!=test_samples or set(train)&set(test)
            or Counter(int(rows[i]['label']) for i in train)!=Counter({i:144 for i in range(11)})
            or Counter(int(rows[i]['label']) for i in test)!=Counter({i:288 for i in range(11)})):
        raise ValueError('paper-like split coverage or declared sample overlap mismatch')
    return {'dataset':'KTHTIPS2b','seed':42,'outer_fold':0,'training_indices':train,
        'external_indices':test,'labels':list(range(11)),'manifest':str(manifest_path),
        'training_seed':42,'epochs':100,'head_batch':32,
        'split_identity':'local approximation: scales 2-7 and image ids 1-6 as fit',
        'shared_physical_samples_train_test':44}


def prepare(output):
    output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    sources={};prepared=[];packages={};python_version=None;canonical=None
    for name,dirname,runner in METHODS:
        old=ROOT/'results/analysis'/dirname
        manifest,worker,frozen=[read(old/f) for f in ('manifest.json','gpu.json','preflight.json')]
        if (worker['status']!='all_tasks_terminal' or worker.get('current_task') is not None
                or worker['manifest_sha256']!=digest(old/'manifest.json')):
            raise ValueError('terminal prior KTH queue required')
        verify_sources(manifest)
        for package,version in manifest['packages'].items():
            if package in packages and packages[package]!=version: raise ValueError('package mismatch')
            packages[package]=version
        if python_version and manifest['python_version']!=python_version: raise ValueError('Python mismatch')
        python_version=manifest['python_version']
        image_manifest=Path(frozen['conditions'][0]['manifest'])
        with image_manifest.open(newline='') as stream: rows=list(csv.DictReader(stream))
        if canonical is not None and rows!=canonical: raise ValueError('source manifests differ')
        canonical=rows
        p=partition(rows,image_manifest)
        if name=='CellNN':
            p.pop('training_seed');p.pop('epochs');p.pop('head_batch')
            p['head_params']=copy.deepcopy(frozen['conditions'][0]['head_params'])
        sources.update(manifest['source_sha256'])
        for path in (old/'manifest.json',old/'gpu.json',old/'preflight.json',image_manifest,
                     ROOT/'scripts'/runner,PROTOCOL,Path(__file__).resolve()): sources[str(path)]=digest(path)
        prepared.append((name,runner,frozen,p))
    for row in canonical:
        if digest(ROOT/row['path'])!=row['sha256']: raise ValueError('image hash drift')
    output.mkdir(parents=True,exist_ok=False);tasks=[]
    for name,runner,old,p in prepared:
        frozen={**old,'conditions':[p],'unique_conditions':1,'planned_online_calls':3168,
            'source_sha256':sources,'status':'KTH_PAPERLIKE_ONE_THIRD_FROZEN',
            'paper_scores_reproduced':False,'physical_sample_overlap_explicit':True,
            'split_choice_unverified_against_authors':True,'protocol':str(PROTOCOL)}
        preflight=output/(name+'_preflight.json');preflight.write_text(json.dumps(frozen,indent=2)+'\n')
        sources[str(preflight)]=digest(preflight)
        task_name=name+'_KTH_paperlike_s42_f0';job=output/'jobs'/task_name;commands=[]
        for stage,timeout in [('extract',7200),('train',3600),('online',14400),('audit',300)]:
            commands.append({'argv':[sys.executable,str(ROOT/'scripts'/runner),'--manifest',str(preflight),
                '--number','0','--stage',stage,'--job',str(job)],'timeout_seconds':timeout,
                'success':{'path':str(job/stage/'status.json'),'fields':{'status':stage+'_complete'}}})
        tasks.append({'id':task_name,'lane':'gpu','depends_on':[],'observe':False,
            'exclusive_outputs':[str(job/s) for s in ('extract','train','online','audit')],'commands':commands})
    manifest={'schema':1,'no_auto_retry':True,'python_version':python_version,'packages':packages,
        'source_sha256':sources,'gpu_lock':'results/analysis/gpu.lock','tasks':tasks,
        'scope':'KTH one-third paper-like approximate split; shared physical samples disclosed'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'tasks':2,'planned_calls':6336,'manifest_sha256':digest(output/'manifest.json')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
