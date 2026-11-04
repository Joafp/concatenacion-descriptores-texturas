"""Audit 100 complete Neshov FMD paper-like folds and report accuracy honestly."""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import statistics
from consolidate_overnight_online_panel import digest, read
from consolidate_hytex_external_dataset import call_metrics
from consolidate_hytex_fmd_external import write_csv
from run_authorized_remediation_queue import verify_sources


def validate_panel(partitions):
    ids=[(p['repetition'],p['outer_fold']) for p in partitions]
    if len(ids)!=100 or len(set(ids))!=100 or set(ids)!={(r,f) for r in range(1,11) for f in range(10)}:
        raise ValueError('exactly 10 repetitions x 10 distinct folds required')
    for rep in range(1,11):
        parts=[p for p in partitions if p['repetition']==rep]
        if (any(p['dataset']!='FMD' or p['seed']!=42*rep or p['training_seed']!=42*rep
                or len(p['training_indices'])!=900 or len(p['external_indices'])!=100 for p in parts)
                or Counter(i for p in parts for i in p['external_indices'])!=Counter(range(1000))):
            raise ValueError('incomplete per-repetition coverage')


def consolidate(queue,output):
    queue,output=Path(queue).resolve(),Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    manifest,worker,frozen=[read(queue/f) for f in ('manifest.json','gpu.json','preflight.json')]
    mh,fh=digest(queue/'manifest.json'),digest(queue/'preflight.json')
    if (worker['status']!='all_tasks_terminal' or worker.get('current_task') is not None
            or worker['manifest_sha256']!=mh or len(manifest['tasks'])!=100):
        raise ValueError('100 complete terminal tasks required')
    verify_sources(manifest);parts=frozen['conditions'];validate_panel(parts)
    if frozen['paper_scores_reproduced'] is not False: raise ValueError('claim boundary drift')
    sources={**manifest['source_sha256'],**{str(queue/f):digest(queue/f) for f in ('manifest.json','gpu.json','preflight.json')}}
    records=[]
    for task,p in zip(manifest['tasks'],parts):
        name=f'NeshovPaperLike_FMD_r{p["repetition"]}_f{p["outer_fold"]}'
        state_path=queue/'tasks'/name/'state.json';state=read(state_path)
        if (task['id']!=name or worker['outcomes'].get(name)!='complete' or state['status']!='complete'
                or state['manifest_sha256']!=mh or len(state['success_artifacts'])!=4):
            raise ValueError('condition/receipt incomplete')
        job=queue/'jobs'/name;statuses={}
        for stage,receipt,command in zip(('extract','train','online','audit'),state['success_artifacts'],task['commands']):
            path=job/stage/'status.json';status=read(path)
            if (str(path)!=receipt['path'] or digest(path)!=receipt['sha256'] or receipt['condition']!=command['success']
                    or status['status']!=stage+'_complete' or status['partition']!=p or status['manifest_sha256']!=fh):
                raise ValueError('stage receipt or partition mismatch')
            for filename,sha in status['output_sha256'].items():
                artifact=job/stage/filename
                if digest(artifact)!=sha: raise ValueError('stage artifact drift')
                sources[str(artifact)]=sha
            statuses[stage]=status;sources[str(path)]=digest(path)
        if (statuses['extract']['fit_extraction_batch_size']!=1
                or statuses['extract']['parity_max_abs_error']>1e-4
                or statuses['train']['training_seed']!=p['training_seed']):
            raise ValueError('regime, parity or training seed drift')
        for down,key,up in (('train','extraction_status_sha256','extract'),
                            ('online','head_status_sha256','train'),('audit','online_status_sha256','online')):
            if statuses[down][key]!=digest(job/up/'status.json'): raise ValueError('stage chain drift')
        with Path(p['manifest']).open(newline='') as stream: rows=list(csv.DictReader(stream))
        with (job/'online'/'calls.jsonl').open() as stream: calls=[json.loads(line) for line in stream]
        computed,summary=call_metrics(calls,p,rows),read(job/'audit'/'summary.json')
        for key,value in computed.items():
            if abs(summary[key]-value)>1e-12: raise ValueError('raw calls mismatch')
        if not summary['same_call_quality_and_timing']: raise ValueError('same calls required')
        records.append({'repetition':p['repetition'],'seed':p['seed'],'outer_fold':p['outer_fold'],**computed})
        sources[str(state_path)]=digest(state_path)
    grouped=defaultdict(list)
    for r in records: grouped[r['repetition']].append(r)
    repetitions=[{'repetition':rep,'seed':42*rep,'folds':len(group),'calls':sum(r['calls'] for r in group),
        'accuracy':statistics.mean(r['accuracy_online'] for r in group),
        'mean_fold_macro_f1':statistics.mean(r['macro_f1_online'] for r in group),
        'mean_ms':sum(r['mean_ms']*r['calls'] for r in group)/sum(r['calls'] for r in group)}
        for rep,group in sorted(grouped.items())]
    if any(r['folds']!=10 or r['calls']!=1000 for r in repetitions): raise ValueError('incomplete repetition')
    sources[str(Path(__file__).resolve())]=digest(__file__)
    report={'status':'ALL_100_PAPERLIKE_FMD_FOLDS_AUDITED','method':'Neshov BEiTv2+MLP approximate 10x10',
        'conditions':100,'calls':sum(r['calls'] for r in records),
        'mean_accuracy_10_repetitions':statistics.mean(r['accuracy'] for r in repetitions),
        'sd_accuracy_across_repetitions_descriptive':statistics.stdev(r['accuracy'] for r in repetitions),
        'mean_fold_macro_f1':statistics.mean(r['macro_f1_online'] for r in records),
        'mean_ms_all_calls':sum(r['mean_ms']*r['calls'] for r in records)/sum(r['calls'] for r in records),
        'paper_reported_accuracy':0.967,'paper_doi':'10.3390/electronics14234779',
        'same_call_quality_and_timing':True,'paper_scores_reproduced':False,
        'reservations':['approximate split generation and seed decisions; original code not verified',
            'different Python/PyTorch/timm versions and hardware','previously observed benchmark',
            '10 repeats are not independent datasets; SD is descriptive, not confidence interval']}
    if report['calls']!=10000: raise ValueError('10000 calls required')
    output.mkdir(parents=True,exist_ok=False)
    write_csv(output/'fold_metrics.csv',records);write_csv(output/'repetition_metrics.csv',repetitions)
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'provenance.json').write_text(json.dumps(sources,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--queue',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();consolidate(a.queue,a.output)
