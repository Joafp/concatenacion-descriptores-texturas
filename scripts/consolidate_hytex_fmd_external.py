"""Audit complete HyTex ADAPTED FMD panel and compare with frozen local calls."""
import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import statistics

from consolidate_overnight_online_panel import ROOT, digest, read, macro_f1
from run_authorized_remediation_queue import verify_sources

LOCAL_SHA = 'bd490536bd178fa3f329257d991639c0791865dedca00711bb66ada988fc9838'
METHOD = 'HyTexNet adapted; local fixed configuration'
IDENTITIES = {(s, f) for s in (42, 123, 2026) for f in range(5)}


def validate_identities(partitions):
    identities = [(p['seed'], p['outer_fold']) for p in partitions]
    if len(identities) != 15 or len(set(identities)) != 15 or set(identities) != IDENTITIES:
        raise ValueError('all 15 unique FMD conditions required')


def metrics(calls, partition, rows):
    import numpy as np
    if [c['row_index'] for c in calls] != partition['external_indices'] or len(calls) != 200:
        raise ValueError('full ordered 200-call coverage required')
    labels = partition['labels']
    for c in calls:
        if (c['truth'] != int(rows[c['row_index']]['label']) or c['repeat'] != 0
                or c['prediction'] not in labels or len(c['logits']) != len(labels)
                or not all(math.isfinite(v) for v in c['logits'])
                or labels[int(np.argmax(c['logits']))] != c['prediction']
                or not math.isfinite(c['elapsed_ms']) or c['elapsed_ns'] <= 0
                or c['elapsed_ms'] != c['elapsed_ns'] / 1e6):
            raise ValueError('same-call truth/logits/timing integrity failure')
    times = [c['elapsed_ms'] for c in calls]
    return {'calls': len(calls), 'macro_f1_online': macro_f1([c['truth'] for c in calls], [c['prediction'] for c in calls]),
            'accuracy_online': statistics.mean(c['truth'] == c['prediction'] for c in calls),
            'mean_ms': statistics.mean(times), 'median_ms': statistics.median(times),
            'p95_ms': float(np.percentile(times, 95))}


def write_csv(path, records):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def consolidate(queue, output):
    queue, output = Path(queue).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest = read(queue / 'manifest.json')
    worker = read(queue / 'gpu.json')
    if (worker['status'] != 'all_tasks_terminal' or worker['current_task'] is not None
            or worker['manifest_sha256'] != digest(queue / 'manifest.json')
            or len(manifest['tasks']) != 15):
        raise ValueError('complete terminal queue required; do not audit during benchmarks')
    verify_sources(manifest)
    frozen = read(queue / 'preflight.json')
    partitions = frozen['conditions']
    validate_identities(partitions)
    records, all_calls = [], []
    sources = {str(queue / f): digest(queue / f) for f in ('manifest.json', 'preflight.json', 'gpu.json')}
    sources.update(manifest['source_sha256'])
    for task, partition in zip(manifest['tasks'], partitions):
        name = f'HyTex_FMD_s{partition["seed"]}_f{partition["outer_fold"]}'
        if task['id'] != name or worker['outcomes'].get(name) != 'complete':
            raise ValueError('incomplete or mismatched task')
        state_path = queue / 'tasks' / name / 'state.json'
        state = read(state_path)
        if state['status'] != 'complete' or state['manifest_sha256'] != digest(queue / 'manifest.json'):
            raise ValueError('task receipt drift')
        receipts = state['success_artifacts']
        if len(receipts) != 4 or [a['condition'] for a in receipts] != [c['success'] for c in task['commands']]:
            raise ValueError('stage receipt coverage mismatch')
        job = queue / 'jobs' / name
        stages = {}
        for stage, receipt in zip(('extract', 'train', 'online', 'audit'), receipts):
            path = job / stage / 'status.json'
            if str(path) != receipt['path'] or digest(path) != receipt['sha256']:
                raise ValueError('stage/status hash mismatch')
            status = read(path)
            if (status['status'] != stage + '_complete' or status['partition'] != partition
                    or status['manifest_sha256'] != digest(queue / 'preflight.json')
                    or status['method'] != METHOD):
                raise ValueError('stage identity or scientific recipe drift')
            for filename, sha in status['output_sha256'].items():
                artifact = job / stage / filename
                if digest(artifact) != sha:
                    raise ValueError('stage output drift')
                sources[str(artifact)] = sha
            sources[str(path)] = digest(path)
            stages[stage] = status
        for downstream, key, upstream in (('train', 'extraction_status_sha256', 'extract'),
                ('online', 'head_status_sha256', 'train'), ('audit', 'online_status_sha256', 'online')):
            if stages[downstream][key] != digest(job / upstream / 'status.json'):
                raise ValueError('cross-stage provenance drift')
        with Path(partition['manifest']).open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        calls = [json.loads(line) for line in (job / 'online/calls.jsonl').read_text().splitlines()]
        calculated = metrics(calls, partition, rows)
        summary = read(job / 'audit/summary.json')
        if summary['method'] != METHOD or not summary['same_call_quality_and_timing']:
            raise ValueError('method or same-call identity missing')
        for key, value in calculated.items():
            if abs(value - summary[key]) > 1e-12:
                raise ValueError('raw-call reaggregation mismatch: ' + key)
        records.append({'dataset': 'FMD', 'seed': partition['seed'], 'outer_fold': partition['outer_fold'],
                        'method': METHOD, **calculated})
        all_calls.extend(calls)
        sources[str(state_path)] = digest(state_path)
    local_path = ROOT / 'results/analysis/blocker_resolution_20261101/full_panel_online_v1/condition_summary.csv'
    if digest(local_path) != LOCAL_SHA:
        raise ValueError('frozen local comparison table drift')
    with local_path.open(newline='') as stream:
        local = [r for r in csv.DictReader(stream) if r['dataset'] == 'FMD']
    comparisons = []
    lookup = {(r['seed'], r['outer_fold']): r for r in records}
    for r in local:
        reference = lookup[int(r['seed']), int(r['outer_fold'])]
        if int(r['calls']) != reference['calls']:
            raise ValueError('local/reference image-count mismatch')
        comparisons.append({'dataset': 'FMD', 'seed': r['seed'], 'outer_fold': r['outer_fold'],
            'local_classifier': r['classifier'], 'local_method': r['method'], 'reference_method': METHOD,
            'local_f1': float(r['macro_f1_online']), 'reference_f1': reference['macro_f1_online'],
            'delta_f1_local_minus_reference': float(r['macro_f1_online']) - reference['macro_f1_online'],
            'local_mean_ms': float(r['mean_ms']), 'reference_mean_ms': reference['mean_ms'],
            'latency_ratio_reference_over_local': reference['mean_ms'] / float(r['mean_ms'])})
    if len(comparisons) != 150 or len({(r['seed'], r['outer_fold'], r['local_classifier'], r['local_method']) for r in comparisons}) != 150:
        raise ValueError('complete local/reference pair coverage required')
    groups = defaultdict(list)
    for r in comparisons:
        groups[r['local_classifier'], r['local_method']].append(r)
    dataset = []
    for (classifier, method), group in sorted(groups.items()):
        local_ms = statistics.mean(r['local_mean_ms'] for r in group)
        reference_ms = statistics.mean(r['reference_mean_ms'] for r in group)
        dataset.append({'dataset': 'FMD', 'local_classifier': classifier, 'local_method': method,
            'reference_method': METHOD, 'conditions': len(group),
            'local_mean_split_f1': statistics.mean(r['local_f1'] for r in group),
            'reference_mean_split_f1': statistics.mean(r['reference_f1'] for r in group),
            'mean_delta_f1_local_minus_reference': statistics.mean(r['delta_f1_local_minus_reference'] for r in group),
            'local_mean_ms_all_calls': local_ms, 'reference_mean_ms_all_calls': reference_ms,
            'latency_ratio_reference_over_local': reference_ms / local_ms})
    sources[str(local_path)] = LOCAL_SHA
    sources[str(Path(__file__).resolve())] = digest(Path(__file__))
    summary = {'status': 'ALL_15_FMD_ADAPTATION_CONDITIONS_REAGGREGATED', 'method': METHOD,
        'unique_conditions': 15, 'calls': len(all_calls), 'datasets': 1,
        'mean_split_macro_f1': statistics.mean(r['macro_f1_online'] for r in records),
        'mean_ms_all_calls': statistics.mean(c['elapsed_ms'] for c in all_calls),
        'same_call_quality_and_timing': True, 'paper_scores_reproduced': False,
        'global_inference_performed': False,
        'reservations': ['local fixed adaptation, not author implementation or source hyperparameters',
            'shared hardware and separate dates from local panel; no paired contemporaneous timing claim',
            'three seeds/five folds are not independent datasets; previously observed benchmark']}
    if len(all_calls) != 3000:
        raise ValueError('3000 calls required')
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / 'condition_metrics.csv', records)
    write_csv(output / 'comparison_by_condition.csv', comparisons)
    write_csv(output / 'comparison_dataset.csv', dataset)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (output / 'provenance.json').write_text(json.dumps(sources, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    consolidate(args.queue, args.output)
