"""Audit one complete KTH paper-like method without claiming an exact replica."""
import argparse
import csv
import json
from pathlib import Path
from consolidate_overnight_online_panel import digest, read
from consolidate_hytex_external_dataset import call_metrics
from run_cellnn_external_condition import audit_records
from run_authorized_remediation_queue import verify_sources
from prepare_kth_paperlike_queue import partition

PAPER_ACCURACY={'HyTex':0.9979,'CellNN':0.9129}
PAPER_DOI={'HyTex':'10.1016/j.knosys.2026.115482','CellNN':'10.1016/j.eswa.2023.122100'}


def validate_partition(p,rows):
    expected=partition(rows,p['manifest'])
    for key in ('training_indices','external_indices','labels','shared_physical_samples_train_test'):
        if p[key]!=expected[key]: raise ValueError('paper-like partition drift')
    if p['shared_physical_samples_train_test']!=44:
        raise ValueError('physical sample overlap must be disclosed')


def consolidate(queue,output,method):
    queue,output=Path(queue).resolve(),Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    manifest,worker=[read(queue/f) for f in ('manifest.json','gpu.json')]
    mh=digest(queue/'manifest.json')
    if worker['status']!='all_tasks_terminal' or worker.get('current_task') is not None or worker['manifest_sha256']!=mh:
        raise ValueError('terminal queue required')
    verify_sources(manifest)
    name=method+'_KTH_paperlike_s42_f0'
    tasks=[t for t in manifest['tasks'] if t['id']==name]
    if len(tasks)!=1: raise ValueError('exact task required')
    task=tasks[0];state_path=queue/'tasks'/name/'state.json';state=read(state_path)
    if (worker['outcomes'].get(name)!='complete' or state['status']!='complete'
            or state['manifest_sha256']!=mh or len(state['success_artifacts'])!=4):
        raise ValueError('all four task stages must be complete')
    preflight=Path(task['commands'][0]['argv'][3]);frozen=read(preflight)
    if (len(frozen['conditions'])!=1 or not frozen['physical_sample_overlap_explicit']
            or not frozen['split_choice_unverified_against_authors'] or frozen['paper_scores_reproduced']):
        raise ValueError('disclosure or partition mismatch')
    p=frozen['conditions'][0]
    with Path(p['manifest']).open(newline='') as stream: rows=list(csv.DictReader(stream))
    validate_partition(p,rows)
    job=queue/'jobs'/name;statuses={};sources=dict(manifest['source_sha256'])
    for stage,receipt,command in zip(('extract','train','online','audit'),state['success_artifacts'],task['commands']):
        path=job/stage/'status.json';status=read(path)
        if (receipt['path']!=str(path) or receipt['sha256']!=digest(path)
                or receipt['condition']!=command['success'] or status['status']!=stage+'_complete'
                or status['partition']!=p or status['manifest_sha256']!=digest(preflight)):
            raise ValueError('stage identity or receipt mismatch')
        for filename,sha in status['output_sha256'].items():
            artifact=job/stage/filename
            if digest(artifact)!=sha: raise ValueError('output hash drift')
            sources[str(artifact)]=sha
        statuses[stage]=status;sources[str(path)]=digest(path)
    for down,key,up in (('train','extraction_status_sha256','extract'),
                        ('online','head_status_sha256','train'),('audit','online_status_sha256','online')):
        if statuses[down][key]!=digest(job/up/'status.json'): raise ValueError('stage lineage mismatch')
    with (job/'online'/'calls.jsonl').open() as stream: calls=[json.loads(line) for line in stream]
    actual=call_metrics(calls,p,rows) if method=='HyTex' else audit_records(calls,p,rows)
    audited=read(job/'audit'/'summary.json')
    for key,value in actual.items():
        if isinstance(value,(int,float)):
            if abs(audited[key]-value)>1e-12: raise ValueError('raw reaggregation mismatch')
        elif audited[key]!=value: raise ValueError('audit declaration mismatch')
    if actual['calls']!=3168: raise ValueError('full test coverage required')
    sources[str(state_path)]=digest(state_path);sources[str(queue/'gpu.json')]=digest(queue/'gpu.json')
    sources[str(Path(__file__).resolve())]=digest(__file__)
    result={'status':'COMPLETE_KTH_PAPERLIKE_APPROXIMATION','method':method,**actual,
        'paper_reported_accuracy':PAPER_ACCURACY[method],'paper_doi':PAPER_DOI[method],
        'physical_samples_shared_across_train_test':44,'paper_scores_reproduced':False,
        'same_call_quality_and_timing':True,'reservations':['local selection of 2 poses and 6 scales; source selection unverified',
            'shared physical objects in fit and test','local method adaptation and versions',
            'not a paired comparison to physical-sample-separated local panel']}
    output.mkdir(parents=True,exist_ok=False)
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'provenance.json').write_text(json.dumps(sources,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--method',choices=sorted(PAPER_ACCURACY),required=True)
    a=parser.parse_args();consolidate(a.queue,a.output,a.method)
