"""Audit all 15 corrected Neshov/FMD conditions from raw online calls."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics
from consolidate_overnight_online_panel import ROOT, digest, read
from consolidate_hytex_fmd_external import LOCAL_SHA, metrics, validate_identities, write_csv
from run_authorized_remediation_queue import verify_sources

METHOD = 'Neshov BEiTv2+MLP adapted; batch1 fit and online'


def aggregate(comparisons):
    groups = defaultdict(list)
    for r in comparisons:
        groups[r['local_classifier'], r['local_method']].append(r)
    if len(groups) != 10 or any(len(g) != 15 for g in groups.values()):
        raise ValueError('complete paired classifier/method coverage required')
    result = []
    for (classifier, method), group in sorted(groups.items()):
        total = sum(r['calls'] for r in group)
        local_ms = sum(r['local_mean_ms'] * r['calls'] for r in group) / total
        ref_ms = sum(r['reference_mean_ms'] * r['calls'] for r in group) / total
        result.append({'dataset': 'FMD', 'local_classifier': classifier, 'local_method': method,
            'reference_method': METHOD, 'conditions': 15, 'calls': total,
            'local_mean_split_f1': statistics.mean(r['local_f1'] for r in group),
            'reference_mean_split_f1': statistics.mean(r['reference_f1'] for r in group),
            'mean_delta_f1_local_minus_reference': statistics.mean(r['local_f1']-r['reference_f1'] for r in group),
            'local_mean_ms_all_calls': local_ms, 'reference_mean_ms_all_calls': ref_ms,
            'latency_ratio_reference_over_local': ref_ms/local_ms})
    return result


def consolidate(queue, output):
    queue, output = Path(queue).resolve(), Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    manifest, worker, frozen = [read(queue/f) for f in ('manifest.json','gpu.json','preflight.json')]
    manifest_sha, frozen_sha = digest(queue/'manifest.json'), digest(queue/'preflight.json')
    if (worker['status'] != 'all_tasks_terminal' or worker.get('current_task') is not None
            or worker['manifest_sha256'] != manifest_sha or len(manifest['tasks']) != 15):
        raise ValueError('complete terminal queue required')
    verify_sources(manifest)
    partitions = frozen['conditions']; validate_identities(partitions)
    if frozen['extraction_regime'] != 'batch1 fit and batch1 online' or not frozen['original_batch8_failure_retained']:
        raise ValueError('incorrect frozen extraction regime')
    sources = {**manifest['source_sha256'], **{str(queue/f):digest(queue/f) for f in ('manifest.json','gpu.json','preflight.json')}}
    records = []
    for task, p in zip(manifest['tasks'], partitions):
        name = f'Neshov_FMD_s{p["seed"]}_f{p["outer_fold"]}'
        state_path = queue/'tasks'/name/'state.json'; state = read(state_path)
        if (task['id'] != name or worker['outcomes'].get(name) != 'complete'
                or state['status'] != 'complete' or state['manifest_sha256'] != manifest_sha):
            raise ValueError('incomplete condition')
        receipts = state['success_artifacts']; commands = task['commands']
        if len(receipts) != 4 or [r['condition'] for r in receipts] != [c['success'] for c in commands]:
            raise ValueError('four bound receipts required')
        job = queue/'jobs'/name; statuses = {}
        for stage, receipt in zip(('extract','train','online','audit'), receipts):
            path = job/stage/'status.json'; status = read(path)
            if (str(path) != receipt['path'] or digest(path) != receipt['sha256']
                    or status['status'] != stage+'_complete' or status['partition'] != p
                    or status['manifest_sha256'] != frozen_sha):
                raise ValueError('stage identity mismatch')
            for name, sha in status['output_sha256'].items():
                artifact = job/stage/name
                if digest(artifact) != sha: raise ValueError('stage artifact drift')
                sources[str(artifact)] = sha
            sources[str(path)] = digest(path); statuses[stage] = status
        if (statuses['extract']['fit_extraction_batch_size'] != 1
                or statuses['extract']['parity_max_abs_error'] > 1e-4):
            raise ValueError('batch1 parity gate failed')
        for down,key,up in (('train','extraction_status_sha256','extract'),
                            ('online','head_status_sha256','train'),('audit','online_status_sha256','online')):
            if statuses[down][key] != digest(job/up/'status.json'): raise ValueError('stage chain drift')
        with Path(p['manifest']).open(newline='') as stream: rows = list(csv.DictReader(stream))
        with (job/'online'/'calls.jsonl').open() as stream: calls = [json.loads(line) for line in stream]
        computed, summary = metrics(calls,p,rows), read(job/'audit'/'summary.json')
        for key,value in computed.items():
            if abs(summary[key]-value) > 1e-12: raise ValueError('raw call reaggregation differs')
        if not summary['same_call_quality_and_timing']: raise ValueError('same calls required')
        records.append({'dataset':'FMD','seed':p['seed'],'outer_fold':p['outer_fold'],
                        'method':METHOD,**computed})
        sources[str(state_path)] = digest(state_path)
    if sum(r['calls'] for r in records) != 3000: raise ValueError('3000 calls required')
    local_path = ROOT/'results/analysis/blocker_resolution_20261101/full_panel_online_v1/condition_summary.csv'
    if digest(local_path) != LOCAL_SHA: raise ValueError('local panel drift')
    with local_path.open(newline='') as stream: local = [r for r in csv.DictReader(stream) if r['dataset']=='FMD']
    lookup = {(r['seed'],r['outer_fold']):r for r in records}; comparisons = []
    for row in local:
        ref = lookup[(int(row['seed']),int(row['outer_fold']))]
        if int(row['calls']) != ref['calls']: raise ValueError('call count mismatch')
        comparisons.append({'dataset':'FMD','seed':int(row['seed']),'outer_fold':int(row['outer_fold']),
            'local_classifier':row['classifier'],'local_method':row['method'],'reference_method':METHOD,
            'local_f1':float(row['macro_f1_online']),'reference_f1':ref['macro_f1_online'],
            'local_mean_ms':float(row['mean_ms']),'reference_mean_ms':ref['mean_ms'],'calls':ref['calls']})
    dataset_rows = aggregate(comparisons)
    sources[str(local_path)] = LOCAL_SHA; sources[str(Path(__file__).resolve())] = digest(__file__)
    report = {'status':'ALL_15_FMD_ADAPTATION_CONDITIONS_REAGGREGATED','method':METHOD,
        'conditions':15,'calls':3000,'mean_split_macro_f1':statistics.mean(r['macro_f1_online'] for r in records),
        'mean_ms_all_calls':sum(r['mean_ms']*r['calls'] for r in records)/3000,
        'same_call_quality_and_timing':True,'paper_scores_reproduced':False,'global_inference_performed':False,
        'reservations':['adaptation to common panel, not published FMD 10x10 protocol',
            'original batch8 vs batch1 parity failure retained','shared hardware and separate dates']}
    output.mkdir(parents=True,exist_ok=False)
    write_csv(output/'condition_metrics.csv',records);write_csv(output/'comparison_by_condition.csv',comparisons)
    write_csv(output/'comparison_dataset.csv',dataset_rows)
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'provenance.json').write_text(json.dumps(sources,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();consolidate(args.queue,args.output)
