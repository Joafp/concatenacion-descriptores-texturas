"""Dispatch eligible never-started CellNN conditions only; never resume v1 partials."""
import argparse
import json
from pathlib import Path
import sys
from consolidate_overnight_online_panel import ROOT,read,digest
from run_authorized_remediation_queue import verify_sources


def eligible(state,job_exists):
    forbidden={'pid','stage','started_utc','success_artifacts','argv'}
    return (state.get('status')=='blocked' and state.get('reason')=='dependency_requires_review'
        and not forbidden.intersection(state) and not job_exists)


def prepare(previous,output):
    previous,output=Path(previous).resolve(),Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    manifest,worker,frozen=[read(previous/f) for f in ('manifest.json','gpu.json','preflight.json')]
    if (worker['status']!='all_tasks_terminal' or worker['current_task'] is not None
            or worker['manifest_sha256']!=digest(previous/'manifest.json')):
        raise ValueError('previous worker must be terminal')
    verify_sources(manifest)
    sources=dict(manifest['source_sha256'])
    for name in ('manifest.json','gpu.json','preflight.json'):
        sources[str(previous/name)]=digest(previous/name)
    selected=[]
    for task,p in zip(manifest['tasks'],frozen['conditions']):
        sp=previous/'tasks'/task['id']/'state.json';state=read(sp)
        sources[str(sp)]=digest(sp)
        if eligible(state,(previous/'jobs'/task['id']).exists()): selected.append((task,p))
    if len(selected)!=14 or any((p['seed'],p['outer_fold'])==(42,0) for _,p in selected):
        raise ValueError('exactly14 never-started conditions required; exclude failed42/f0')
    if sum(len(p['external_indices']) for _,p in selected)!=2800:
        raise ValueError('never-started coverage drift')
    for name in ('scripts/run_cellnn_external_condition_v2.py','scripts/prepare_cellnn_never_started_queue.py',
        'docs/fsc_tex/CELLNN_INFRA_CONDICIONES_NO_INICIADAS_2026-11-02.md'):
        sources[str(ROOT/name)]=digest(ROOT/name)
    output.mkdir(parents=True,exist_ok=False);target=output/'preflight.json'
    payload={**frozen,'conditions':[p for _,p in selected],'source_sha256':sources,
        'unique_conditions':14,'planned_online_calls':2800,'full_fmd_panel_complete':False,
        'excluded_requires_review_condition':'CellNN_FMD_s42_f0','prior_queue':str(previous),
        'status':'CELLNN_NEVER_STARTED_CONDITIONS_FROZEN_NOT_EXECUTED'}
    target.write_text(json.dumps(payload,indent=2)+'\n');tasks=[]
    for number,(old,p) in enumerate(selected):
        name=old['id'];job=output/'jobs'/name;commands=[]
        for stage,timeout in [('extract',7200),('train',3600),('online',14400),('audit',300)]:
            commands.append({'argv':[sys.executable,str(ROOT/'scripts/run_cellnn_external_condition_v2.py'),
                '--manifest',str(target),'--number',str(number),'--stage',stage,'--job',str(job)],
                'timeout_seconds':timeout,'success':{'path':str(job/stage/'status.json'),'fields':{'status':stage+'_complete'}}})
        tasks.append({'id':name,'lane':'gpu','depends_on':[] if not tasks else [tasks[0]['id']],
            'observe':False,'exclusive_outputs':[str(job/s) for s in ('extract','train','online','audit')],'commands':commands})
    fresh={**manifest,'tasks':tasks,'source_sha256':{**sources,str(target):digest(target)},
        'scope':'Only14 never-started CellNN conditions; no retry/complete FMD aggregate'}
    (output/'manifest.json').write_text(json.dumps(fresh,indent=2)+'\n')
    print(json.dumps({'tasks':14,'excluded_failed':True,'manifest_sha256':digest(output/'manifest.json')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();prepare(a.previous,a.output)
