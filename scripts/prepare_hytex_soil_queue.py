"""Freeze never-executed Soil HyTex conditions; preserve exact local partitions."""
import argparse
from collections import Counter
import csv
import importlib.metadata
import json
from pathlib import Path
import sys

from consolidate_overnight_online_panel import ROOT, select_jobs, read, digest
from prepare_hytex_fmd_queue import CHECKPOINT_SHA
from prepare_hytex_dtd_queue import canonical_array_labels
from prepare_hytex_outex_queue import validate_archived_truth
from prepare_neshov_fmd_external import validate_partition

DATASET = 'SoilOriginal'


def validate_soil(conditions, rows):
    identities = {(p['seed'],p['outer_fold']) for p in conditions}
    if (len(rows) != 1140 or any(int(r['row_id']) != i for i,r in enumerate(rows))
            or len(conditions) != 15 or identities != {(s,f) for s in (42,123,2026) for f in range(5)}):
        raise ValueError('Soil full identity coverage required')
    for p in conditions:
        if p['dataset'] != DATASET or validate_partition(p['training_indices'],p['external_indices'],rows) != list(range(7)) or p['labels'] != list(range(7)):
            raise ValueError('Soil partition/classes mismatch')
        expected = 229 if (p['seed'],p['outer_fold']) == (123,1) else 227 if (p['seed'],p['outer_fold']) == (123,3) else 228
        if len(p['external_indices']) != expected:
            raise ValueError('Soil archived fold size mismatch')
    for seed in (42,123,2026):
        counts = Counter(i for p in conditions if p['seed'] == seed for i in p['external_indices'])
        if counts != Counter({i:1 for i in range(1140)}):
            raise ValueError('Soil per-seed universe mismatch')


def frozen_payload(conditions, sources):
    return {'dataset': DATASET, 'conditions': conditions, 'source_sha256': sources,
        'checkpoint_sha256': CHECKPOINT_SHA, 'unique_conditions':15,
        'planned_online_calls':3420, 'unique_images_hashed':1140,
        'method':'HyTexNet adapted; local fixed configuration'}


def prepare(output):
    from huggingface_hub import hf_hub_download
    output = Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    jobs,sources = select_jobs(ROOT)
    selected,canonical,canonical_y = {},None,None
    local = [j for j in jobs if j['dataset'] == DATASET]
    if len(local) != 30: raise ValueError('both heads and15partitions required')
    for j in local:
        qp,op = Path(j['quality_run'])/'status.json',Path(j['online_run'])/'status.json'
        q,o = read(qp),read(op)
        if (q['status'] != 'external_quality_complete_timing_pending' or digest(qp) != o['quality_status_sha256']
                or digest(j['config']) != j['config_sha256']): raise ValueError('local lineage drift')
        args = read(j['config'])['provenance']['arguments']
        lp = ROOT/args['embedding_root']/DATASET/'hog_labels.npy'
        values,sha = canonical_array_labels(lp)
        if len(values) != 1140 or sha != q['provenance']['labels_sha256']: raise ValueError('label array drift')
        if canonical_y is not None and values != canonical_y: raise ValueError('head labels disagree')
        canonical_y = values
        mp = ROOT/q['provenance']['manifest_path']
        if digest(mp) != q['provenance']['manifest_sha256']: raise ValueError('manifest drift')
        with mp.open(newline='') as stream: original = list(csv.DictReader(stream))
        mapping = {}
        labels = [mapping.setdefault(r['label'],len(mapping)) for r in original]
        if labels != values: raise ValueError('manifest label order disagreement')
        rows = [{**r,'original_label':r['label'],'label':labels[i],
            'path':str(ROOT/r['source_path']),'sha256':r['source_sha256']} for i,r in enumerate(original)]
        if canonical is not None and canonical != rows: raise ValueError('head manifests disagree')
        canonical = rows
        pp = Path(j['quality_run'])/'predictions.csv'
        if digest(pp) != q['output_sha256']['predictions.csv']: raise ValueError('truth file drift')
        with pp.open(newline='') as stream: validate_archived_truth(list(csv.DictReader(stream)),q['external_indices'],rows)
        p = {'dataset':DATASET,'seed':j['seed'],'outer_fold':j['outer_fold'],
            'training_indices':q['training_indices'],'external_indices':q['external_indices'],
            'labels':list(range(7)),'manifest':str(output/'canonical_manifest.csv'),
            'training_seed':42,'epochs':100,'head_batch':32}
        key = (p['seed'],p['outer_fold'])
        if key in selected and selected[key] != p: raise ValueError('head partitions disagree')
        selected[key] = p
        for path in (qp,op,mp,pp,lp,Path(j['config'])): sources[str(path)] = digest(path)
    conditions = [selected[k] for k in sorted(selected)]
    validate_soil(conditions,canonical)
    for r in canonical:
        if digest(r['path']) != r['sha256']: raise ValueError('image drift')
    checkpoint = Path(hf_hub_download('timm/densenet121.tv_in1k','model.safetensors',local_files_only=True))
    if digest(checkpoint) != CHECKPOINT_SHA: raise ValueError('checkpoint drift')
    for name in ('src/hytex_reference.py','src/hytex_online_adapter.py','src/hytex_fixed_training.py',
        'src/neshov_online_adapter.py','src/neshov_beit_reference.py',
        'scripts/run_hytex_external_condition.py','scripts/run_neshov_external_condition.py',
        'scripts/consolidate_overnight_online_panel.py','scripts/prepare_hytex_fmd_queue.py',
        'scripts/prepare_hytex_dtd_queue.py','scripts/prepare_hytex_outex_queue.py',
        'scripts/prepare_hytex_soil_queue.py','scripts/prepare_neshov_fmd_external.py',
        'scripts/run_authorized_remediation_queue.py',
        'docs/fsc_tex/PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md',
        'docs/fsc_tex/PROTOCOLO_HYTEX_EXTENSION_SOIL_2026-11-02.md'):
        sources[str(ROOT/name)] = digest(ROOT/name)
    sources[str(checkpoint)] = CHECKPOINT_SHA
    output.mkdir(parents=True,exist_ok=False)
    cp = output/'canonical_manifest.csv'
    with cp.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(canonical[0]));writer.writeheader();writer.writerows(canonical)
    sources[str(cp)] = digest(cp)
    frozen = output/'preflight.json'
    frozen.write_text(json.dumps(frozen_payload(conditions,sources),indent=2)+'\n')
    tasks=[]
    for number,p in enumerate(conditions):
        name=f'HyTex_{DATASET}_s{p["seed"]}_f{p["outer_fold"]}'
        job=output/'jobs'/name
        commands=[]
        for stage,timeout in [('extract',7200),('train',1800),('online',14400),('audit',300)]:
            commands.append({'argv':[sys.executable,str(ROOT/'scripts/run_hytex_external_condition.py'),
                '--manifest',str(frozen),'--number',str(number),'--stage',stage,'--job',str(job)],
                'timeout_seconds':timeout,'success':{'path':str(job/stage/'status.json'),'fields':{'status':stage+'_complete'}}})
        tasks.append({'id':name,'lane':'gpu','depends_on':[] if not tasks else [tasks[0]['id']],
            'observe':False,'exclusive_outputs':[str(job/s) for s in ('extract','train','online','audit')],'commands':commands})
    manifest={'schema':1,'no_auto_retry':True,'python_version':sys.version,
        'source_sha256':{**sources,str(frozen):digest(frozen)},'gpu_lock':'results/analysis/gpu.lock','tasks':tasks,
        'packages':{p:importlib.metadata.version(p) for p in ('numpy','torch','torchvision','timm','Pillow','huggingface-hub','safetensors')},
        'scope':'SoilOriginal: HyTexNet adapted; local fixed configuration'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'tasks':len(tasks),'manifest_sha256':digest(output/'manifest.json')}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
