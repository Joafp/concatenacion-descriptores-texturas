"""Independent never-run CellNN dataset queues from frozen common-panel partitions."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from consolidate_overnight_online_panel import read,digest
from run_authorized_remediation_queue import verify_sources
from cellnn_online_adapter import head_params_json,METHOD
from cellnn_reference import CHECKPOINT_SHA
from prepare_hytex_dtd_queue import inherited_partition

DATASETS={'CUReT':('curet',2,5612,61,5612),'DTD':('dtd',10,18800,47,5640),
    'Outex13Official1360':('outex',1,680,68,1360),'SoilOriginal':('soil',15,3420,7,1140),
    'KTHTIPS2b':('kth',4,4752,11,4752)}


def validate(dataset,parts,rows):
    slug,n,calls,classes,nrows=DATASETS[dataset]
    expected_ids=({(s,f) for s in (42,123,2026) for f in range(5)} if dataset=='SoilOriginal' else {(42,f) for f in range(n)})
    if (len(rows)!=nrows or any(int(r['row_id'])!=i for i,r in enumerate(rows)) or len(parts)!=n
            or {(p['seed'],p['outer_fold']) for p in parts}!=expected_ids
            or sum(len(p['external_indices']) for p in parts)!=calls):
        raise ValueError('dataset identity/coverage mismatch')
    universe=set(range(nrows))
    for p in parts:
        a,b=p['training_indices'],p['external_indices'];sa,sb=set(a),set(b)
        excluded=set(p.get('excluded_training_indices',[]))
        if (p['dataset']!=dataset or len(a)!=len(sa) or len(b)!=len(sb) or sa&sb or sa|sb|excluded!=universe
                or excluded&(sa|sb) or p['labels']!=list(range(classes))
                or {int(rows[i]['label']) for i in a}!=set(range(classes))
                or {rows[i]['group'] for i in a}&{rows[i]['group'] for i in b}):
            raise ValueError('partition/classes/group mismatch')
        if dataset=='CUReT' and (len(a),len(b))!=(2806,2806): raise ValueError('CUReT count mismatch')
        if dataset=='DTD':
            if len(b)!=1880 or inherited_partition(rows,a,b,p['outer_fold'])!=sorted(excluded): raise ValueError('DTD exclusions drift')
        if dataset=='Outex13Official1360':
            if (a!=[i for i,r in enumerate(rows) if r['official_split']=='train']
                    or b!=[i for i,r in enumerate(rows) if r['official_split']=='test']): raise ValueError('Outex official split drift')
        if dataset=='KTHTIPS2b':
            if (len(a),len(b))!=(3564,1188) or {rows[i]['sample'] for i in a}&{rows[i]['sample'] for i in b}:
                raise ValueError('KTH physical sample drift')
    if dataset=='CUReT' and set(parts[0]['external_indices'])!=set(parts[1]['training_indices']): raise ValueError('directions not complementary')
    if dataset in ('SoilOriginal','KTHTIPS2b'):
        for seed in sorted({p['seed'] for p in parts}):
            if Counter(i for p in parts if p['seed']==seed for i in p['external_indices'])!=Counter({i:1 for i in universe}):
                raise ValueError('external universe mismatch')


def prepare(dataset,output):
    output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    slug,n,calls,classes,nrows=DATASETS[dataset]
    previous=ROOT/f'results/analysis/hytex_{slug}_external_queue_20261102_v1'
    original,worker,old=[read(previous/f) for f in ('manifest.json','gpu.json','preflight.json')]
    if worker['status']!='all_tasks_terminal' or worker['manifest_sha256']!=digest(previous/'manifest.json'):
        raise ValueError('frozen partition source queue required')
    verify_sources(original)
    parts=[]
    for p in old['conditions']:
        clean={k:v for k,v in p.items() if k not in ('training_seed','epochs','head_batch')}
        clean['head_params']=head_params_json();parts.append(clean)
    mp=Path(parts[0]['manifest'])
    if any(Path(p['manifest'])!=mp for p in parts): raise ValueError('different manifests')
    with mp.open(newline='') as stream: rows=list(csv.DictReader(stream))
    validate(dataset,parts,rows)
    for r in rows:
        if digest(ROOT/r['path'])!=r['sha256']: raise ValueError('image drift')
    previous_cell=ROOT/'results/analysis/cellnn_fmd_never_started_queue_20261102_v2/manifest.json'
    base=read(previous_cell);verify_sources(base)
    sources=dict(base['source_sha256'])
    for f in (previous_cell,previous/'manifest.json',previous/'preflight.json',previous/'gpu.json',mp): sources[str(f)]=digest(f)
    # Pin source partition provenance as well, without importing or running its method.
    sources.update(original['source_sha256'])
    for name in ('scripts/prepare_cellnn_dataset_queue.py','docs/fsc_tex/PROTOCOLO_CELLNN_EXTENSION_PANEL_COMUN_2026-11-02.md'):
        sources[str(ROOT/name)]=digest(ROOT/name)
    checkpoint=ROOT/'results/analysis/cellnn_author_bundle_20261102_v1/cellnn_model.ph'
    if digest(checkpoint)!=CHECKPOINT_SHA: raise ValueError('checkpoint drift')
    output.mkdir(parents=True,exist_ok=False);target=output/'preflight.json'
    target.write_text(json.dumps({'status':'CELLNN_NEW_DATASET_FROZEN_NOT_EXECUTED','conditions':parts,
        'source_sha256':sources,'unique_conditions':n,'planned_online_calls':calls,'unique_images_hashed':nrows,
        'checkpoint':str(checkpoint),'checkpoint_sha256':CHECKPOINT_SHA,'method':METHOD,
        'head_params':head_params_json(),'partition_source_only':str(previous)},indent=2)+'\n')
    tasks=[]
    for number,p in enumerate(parts):
        name=f'CellNN_{dataset}_s{p["seed"]}_f{p["outer_fold"]}';job=output/'jobs'/name;commands=[]
        for stage,timeout in [('extract',7200),('train',3600),('online',14400),('audit',300)]:
            commands.append({'argv':[sys.executable,str(ROOT/'scripts/run_cellnn_external_condition_v2.py'),
                '--manifest',str(target),'--number',str(number),'--stage',stage,'--job',str(job)],
                'timeout_seconds':timeout,'success':{'path':str(job/stage/'status.json'),'fields':{'status':stage+'_complete'}}})
        tasks.append({'id':name,'lane':'gpu','depends_on':[] if not tasks else [tasks[0]['id']],
            'observe':False,'exclusive_outputs':[str(job/s) for s in ('extract','train','online','audit')],'commands':commands})
    manifest={**base,'source_sha256':{**sources,str(target):digest(target)},'tasks':tasks,'scope':dataset+': '+METHOD}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'dataset':dataset,'tasks':n,'manifest_sha256':digest(output/'manifest.json')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dataset',choices=sorted(DATASETS),required=True)
    parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();prepare(a.dataset,a.output)
