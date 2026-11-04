"""Audit one complete Neshov batch-1 adaptation dataset from raw online calls."""
import argparse
import csv
import json
import math
import statistics
from pathlib import Path

from consolidate_overnight_online_panel import ROOT, digest, read, macro_f1
from consolidate_hytex_fmd_external import LOCAL_SHA, write_csv
from run_authorized_remediation_queue import verify_sources

METHOD = 'Neshov BEiTv2+MLP adapted; batch1 fit and online'
EXPECTED = {
    'CUReT': (2, 5612), 'DTD': (10, 18800),
    'Outex13Official1360': (1, 680), 'SoilOriginal': (15, 3420),
    'KTHTIPS2b': (4, 4752),
}


def metrics(calls, partition, rows):
    import numpy as np
    indices = partition['external_indices']
    labels = partition['labels']
    if not calls or [c['row_index'] for c in calls] != indices or len(indices) != len(set(indices)):
        raise ValueError('full unique ordered online-call coverage required')
    truths, predictions, times = [], [], []
    for c in calls:
        logits = c['logits']
        if (c['truth'] != int(rows[c['row_index']]['label']) or c['repeat'] != 0
                or c['prediction'] not in labels or len(logits) != len(labels)
                or not all(math.isfinite(v) for v in logits)
                or labels[int(np.argmax(logits))] != c['prediction']
                or not math.isfinite(c['elapsed_ms']) or c['elapsed_ns'] <= 0
                or c['elapsed_ms'] != c['elapsed_ns'] / 1e6):
            raise ValueError('same-call label/logit/timing integrity failure')
        truths.append(c['truth']); predictions.append(c['prediction']); times.append(c['elapsed_ms'])
    return {'calls': len(calls), 'macro_f1_online': macro_f1(truths, predictions),
            'accuracy_online': statistics.mean(a == b for a, b in zip(truths, predictions)),
            'mean_ms': statistics.mean(times), 'median_ms': statistics.median(times),
            'p95_ms': float(np.percentile(times, 95))}


def consolidate(queue, output, dataset):
    queue, output = Path(queue).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest, worker, frozen = [read(queue / n) for n in ('manifest.json', 'gpu.json', 'preflight.json')]
    manifest_sha, frozen_sha = digest(queue / 'manifest.json'), digest(queue / 'preflight.json')
    if (worker['status'] != 'all_tasks_terminal' or worker.get('current_task') is not None
            or worker['manifest_sha256'] != manifest_sha):
        raise ValueError('terminal queue required before audit')
    verify_sources(manifest)
    n_expected, calls_expected = EXPECTED[dataset]
    partitions = [p for p in frozen['conditions'] if p['dataset'] == dataset]
    tasks = [t for t in manifest['tasks'] if t['id'].startswith(f'Neshov_{dataset}_')]
    if (len(partitions) != n_expected or len(tasks) != n_expected
            or sum(len(p['external_indices']) for p in partitions) != calls_expected):
        raise ValueError('full per-dataset partition/call coverage required')
    sources = {**manifest['source_sha256'], **{str(queue/n): digest(queue/n)
               for n in ('manifest.json', 'gpu.json', 'preflight.json')}}
    records = []
    for task, p in zip(tasks, partitions):
        name = f'Neshov_{dataset}_s{p["seed"]}_f{p["outer_fold"]}'
        if task['id'] != name or worker['outcomes'].get(name) != 'complete':
            raise ValueError('task identity or terminal outcome mismatch')
        state_path = queue/'tasks'/name/'state.json'; state = read(state_path)
        if state['status'] != 'complete' or state['manifest_sha256'] != manifest_sha:
            raise ValueError('condition state incomplete or from another manifest')
        receipts = state['success_artifacts']
        if len(receipts) != 4 or [r['condition'] for r in receipts] != [c['success'] for c in task['commands']]:
            raise ValueError('four ordered stage receipts required')
        job, statuses = queue/'jobs'/name, {}
        for stage, receipt in zip(('extract', 'train', 'online', 'audit'), receipts):
            status_path = job/stage/'status.json'; status = read(status_path)
            if (receipt['path'] != str(status_path) or receipt['sha256'] != digest(status_path)
                    or status['status'] != stage+'_complete' or status['partition'] != p
                    or status['manifest_sha256'] != frozen_sha):
                raise ValueError('stage receipt, identity, or frozen recipe mismatch')
            for filename, sha in status['output_sha256'].items():
                artifact = job/stage/filename
                if digest(artifact) != sha:
                    raise ValueError('stage output hash drift')
                sources[str(artifact)] = sha
            sources[str(status_path)] = digest(status_path); statuses[stage] = status
        for downstream, key, upstream in (('train','extraction_status_sha256','extract'),
                ('online','head_status_sha256','train'), ('audit','online_status_sha256','online')):
            if statuses[downstream][key] != digest(job/upstream/'status.json'):
                raise ValueError('stage lineage mismatch')
        if (statuses['extract']['fit_extraction_batch_size'] != 1
                or statuses['extract']['parity_max_abs_error'] > 1e-4):
            raise ValueError('batch1 parity gate failed')
        with Path(p['manifest']).open(newline='') as f:
            rows = list(csv.DictReader(f))
        calls = [json.loads(line) for line in (job/'online/calls.jsonl').read_text().splitlines()]
        measured = metrics(calls, p, rows); audited = read(job/'audit'/'summary.json')
        if not audited['same_call_quality_and_timing']:
            raise ValueError('audit does not bind quality and timing to same calls')
        for key, value in measured.items():
            if abs(audited[key] - value) > 1e-12:
                raise ValueError(f'raw call reaggregation mismatch: {key}')
        records.append({'dataset': dataset, 'seed': p['seed'], 'outer_fold': p['outer_fold'],
                        'method': METHOD, **measured})
        sources[str(state_path)] = digest(state_path)
    if sum(r['calls'] for r in records) != calls_expected:
        raise ValueError('aggregate online call count mismatch')

    local_path = ROOT/'results/analysis/blocker_resolution_20261101/full_panel_online_v1/condition_summary.csv'
    if digest(local_path) != LOCAL_SHA:
        raise ValueError('sealed local panel drift')
    with local_path.open(newline='') as f:
        local = [r for r in csv.DictReader(f) if r['dataset'] == dataset]
    lookup = {(r['seed'], r['outer_fold']): r for r in records}
    comparisons = []
    for row in local:
        ref = lookup[int(row['seed']), int(row['outer_fold'])]
        if int(row['calls']) != ref['calls']:
            raise ValueError('local/reference online sample count mismatch')
        comparisons.append({'dataset': dataset, 'seed': row['seed'], 'outer_fold': row['outer_fold'],
            'local_classifier': row['classifier'], 'local_method': row['method'], 'reference_method': METHOD,
            'local_f1': float(row['macro_f1_online']), 'reference_f1': ref['macro_f1_online'],
            'delta_f1_local_minus_reference': float(row['macro_f1_online'])-ref['macro_f1_online'],
            'local_mean_ms': float(row['mean_ms']), 'reference_mean_ms': ref['mean_ms'],
            'local_calls': int(row['calls']), 'reference_calls': ref['calls'],
            'latency_ratio_reference_over_local': ref['mean_ms']/float(row['mean_ms']),
            'physical_timing_reserve_local': row['physical_timing_reserve']})
    if len(comparisons) != len(records)*10:
        raise ValueError('paired comparison coverage mismatch')
    groups = {}
    for row in comparisons:
        groups.setdefault((row['local_classifier'], row['local_method']), []).append(row)
    dataset_rows = []
    for (classifier, method), group in sorted(groups.items()):
        local_calls = sum(r['local_calls'] for r in group); ref_calls = sum(r['reference_calls'] for r in group)
        local_ms = sum(r['local_mean_ms']*r['local_calls'] for r in group)/local_calls
        ref_ms = sum(r['reference_mean_ms']*r['reference_calls'] for r in group)/ref_calls
        dataset_rows.append({'dataset': dataset, 'local_classifier': classifier, 'local_method': method,
            'reference_method': METHOD, 'conditions': len(group), 'calls': ref_calls,
            'local_mean_split_f1': statistics.mean(r['local_f1'] for r in group),
            'reference_mean_split_f1': statistics.mean(r['reference_f1'] for r in group),
            'mean_delta_f1_local_minus_reference': statistics.mean(r['delta_f1_local_minus_reference'] for r in group),
            'local_mean_ms_all_calls': local_ms, 'reference_mean_ms_all_calls': ref_ms,
            'latency_ratio_reference_over_local': ref_ms/local_ms,
            'physical_timing_reserve_local': any(r['physical_timing_reserve_local'].lower() == 'true' for r in group)})
    sources[str(local_path)] = LOCAL_SHA; sources[str(Path(__file__).resolve())] = digest(Path(__file__))
    summary = {'status':'COMPLETE_DATASET_NESHOV_BATCH1_ADAPTATION_REAGGREGATED', 'dataset':dataset,
        'method':METHOD, 'conditions':len(records), 'calls':sum(r['calls'] for r in records),
        'mean_split_macro_f1':statistics.mean(r['macro_f1_online'] for r in records),
        'mean_accuracy':statistics.mean(r['accuracy_online'] for r in records),
        'mean_ms_all_calls':sum(r['mean_ms']*r['calls'] for r in records)/sum(r['calls'] for r in records),
        'same_call_quality_and_timing':True, 'paper_scores_reproduced':False,
        'global_inference_performed':False,
        'reservations':['common-panel adaptation, not reproduction of paper metrics or split',
            'batch8/batch1 discrepancy remains recorded; this queue uses fixed batch1 extraction and inference',
            'shared hardware and separate measurement dates',
            'retain DTD physical-sample and KTH physical-sample/protocol reservations']}
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output/'condition_metrics.csv', records)
    write_csv(output/'comparison_by_condition.csv', comparisons)
    write_csv(output/'comparison_dataset.csv', dataset_rows)
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (output/'provenance.json').write_text(json.dumps(sources, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dataset', choices=sorted(EXPECTED), required=True)
    args = parser.parse_args()
    consolidate(args.queue, args.output, args.dataset)
