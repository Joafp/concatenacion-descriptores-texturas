"""Freeze a documented five-dataset Neshov batch-1 adaptation after complete FMD."""
import argparse
import copy
import csv
import json
from pathlib import Path
import sys
from consolidate_overnight_online_panel import ROOT, read, digest
from prepare_cellnn_dataset_queue import DATASETS, validate
from run_authorized_remediation_queue import verify_sources

FMD = ROOT/'results/analysis/neshov_fmd_batch1_queue_20261102_v1'
SUMMARY = ROOT/'results/analysis/neshov_fmd_batch1_external_summary_20261102_v1/summary.json'
PROTOCOL = ROOT/'docs/fsc_tex/PROTOCOLO_NESHOV_BATCH1_EXTENSION_2026-11-02.md'
ORDER = ('CUReT','DTD','Outex13Official1360','SoilOriginal','KTHTIPS2b')


def neshov_partition(p):
    result = {k: copy.deepcopy(v) for k,v in p.items() if k != 'head_params'}
    if len(result['training_indices']) < 2 or len(result['training_indices']) % 32 == 1:
        raise ValueError('singleton final training batch; requires review')
    result.update(training_seed=42, epochs=100, head_batch=32)
    return result


def prepare(output):
    output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    base, worker, frozen = [read(FMD/f) for f in ('manifest.json','gpu.json','preflight.json')]
    summary=read(SUMMARY)
    if (worker['status']!='all_tasks_terminal' or worker.get('current_task') is not None
            or worker['manifest_sha256']!=digest(FMD/'manifest.json')
            or len(worker['outcomes'])!=15 or set(worker['outcomes'].values())!={'complete'}
            or summary['status']!='ALL_15_FMD_ADAPTATION_CONDITIONS_REAGGREGATED'
            or summary['conditions']!=15 or summary['calls']!=3000):
        raise ValueError('complete and audited FMD prerequisite required')
    verify_sources(base)
    sources=dict(base['source_sha256'])
    for path in (FMD/'manifest.json',FMD/'gpu.json',SUMMARY,PROTOCOL,Path(__file__).resolve()):
        sources[str(path)]=digest(path)
    all_parts=[]
    for dataset in ORDER:
        slug,n,calls,_,_ = DATASETS[dataset]
        prev=ROOT/f'results/analysis/cellnn_{slug}_external_queue_20261102_v1'
        prior,old_worker,partition_doc=[read(prev/f) for f in ('manifest.json','gpu.json','preflight.json')]
        if (old_worker['status']!='all_tasks_terminal' or old_worker.get('current_task') is not None
                or old_worker['manifest_sha256']!=digest(prev/'manifest.json')):
            raise ValueError('source queue not terminal')
        verify_sources(prior)
        parts=partition_doc['conditions']; manifest_path=Path(parts[0]['manifest'])
        if any(Path(p['manifest'])!=manifest_path for p in parts): raise ValueError('manifest disagreement')
        with manifest_path.open(newline='') as stream: rows=list(csv.DictReader(stream))
        validate(dataset,parts,rows)
        for row in rows:
            if digest(ROOT/row['path'])!=row['sha256']: raise ValueError('image hash drift')
        for path in (prev/'manifest.json',prev/'gpu.json',prev/'preflight.json',manifest_path):
            sources[str(path)]=digest(path)
        sources.update(prior['source_sha256'])
        all_parts.extend(neshov_partition(p) for p in parts)
    if len(all_parts)!=32 or sum(len(p['external_indices']) for p in all_parts)!=33264:
        raise ValueError('five-dataset coverage mismatch')
    payload={**frozen,'status':'NESHOV_BATCH1_FIVE_DATASET_EXTENSION_FROZEN',
        'conditions':all_parts,'unique_conditions':32,'planned_online_calls':33264,
        'source_sha256':sources,'protocol':str(PROTOCOL),'paper_scores_reproduced':False}
    output.mkdir(parents=True,exist_ok=False);preflight=output/'preflight.json'
    preflight.write_text(json.dumps(payload,indent=2)+'\n');sources[str(preflight)]=digest(preflight)
    tasks=[]; first={}
    for number,p in enumerate(all_parts):
        name=f'Neshov_{p["dataset"]}_s{p["seed"]}_f{p["outer_fold"]}';job=output/'jobs'/name
        dependencies=[] if p['dataset'] not in first else [first[p['dataset']]]
        first.setdefault(p['dataset'],name);commands=[]
        for stage,timeout in [('extract',7200),('train',1800),('online',14400),('audit',300)]:
            commands.append({'argv':[sys.executable,str(ROOT/'scripts/run_neshov_batch1_condition.py'),
                '--manifest',str(preflight),'--number',str(number),'--stage',stage,'--job',str(job)],
                'timeout_seconds':timeout,'success':{'path':str(job/stage/'status.json'),
                'fields':{'status':stage+'_complete'}}})
        tasks.append({'id':name,'lane':'gpu','depends_on':dependencies,'observe':False,
            'exclusive_outputs':[str(job/s) for s in ('extract','train','online','audit')],'commands':commands})
    manifest={**base,'tasks':tasks,'source_sha256':sources,
        'scope':'Neshov batch1 five-dataset common-panel adaptation; paper scores not reproduced'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'conditions':len(tasks),'planned_calls':33264,'manifest_sha256':digest(output/'manifest.json')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
