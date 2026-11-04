"""Audit authorized recovery calls and rebuild complete per-dataset coverage."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from consolidate_overnight_online_panel import digest, read
from consolidate_hytex_fmd_external import LOCAL_SHA, write_csv
from consolidate_hytex_external_dataset import call_metrics
from run_cellnn_external_condition import audit_records
from run_authorized_remediation_queue import verify_sources

QUEUE = ROOT / 'results/analysis/authorized_paper_infra_recovery_20261102_v1'
BASE = ROOT / 'results/analysis/external_adaptation_coverage_20261102_v1'
PRIOR = ROOT / 'results/analysis/cellnn_fmd_individual_audits_20261102_v1'
EXPECTED_BASE = '7ca8af60a326bfe3cbfd62111baeaf4e50d9fead13b4df20a0b015365dfabf8e'
EXPECTED_PRIOR = '28509cffa320bf36954e682789c6187b09580ea4e48c691bc2e144d9a90c7401'
SPECS = {
    'HyTex_Outex13Official1360_s42_f0': ('HyTexNet adapted', 'Outex13Official1360'),
    'CellNN_FMD_s42_f0': ('LBP+dCellNN adapted', 'FMD'),
}


def checked_coverage(records, expected_ids, expected_calls):
    ids = [(int(r['seed']), int(r['outer_fold'])) for r in records]
    if len(ids) != len(set(ids)) or set(ids) != set(expected_ids):
        raise ValueError('missing, extra or duplicated conditions')
    if sum(int(r['calls']) for r in records) != expected_calls:
        raise ValueError('complete expected call count required')
    return True


def audit_task(task, manifest_hash, worker, sources):
    name = task['id']
    state_path = QUEUE / 'tasks' / name / 'state.json'
    state = read(state_path)
    if (worker['outcomes'].get(name) != 'complete' or state['status'] != 'complete'
            or state['manifest_sha256'] != manifest_hash or len(state['success_artifacts']) != 4):
        raise ValueError('condition must be complete')
    commands = task['commands']
    if len(commands) != 4:
        raise ValueError('four stages required')
    frozen_path = Path(commands[0]['argv'][commands[0]['argv'].index('--manifest') + 1])
    frozen = read(frozen_path)
    if len(frozen['conditions']) != 1:
        raise ValueError('one frozen partition per recovery')
    partition = frozen['conditions'][0]
    job = QUEUE / 'jobs' / name
    stages = {}
    for stage, receipt, command in zip(('extract', 'train', 'online', 'audit'),
                                       state['success_artifacts'], commands):
        path = job / stage / 'status.json'
        status = read(path)
        if (str(path) != receipt['path'] or digest(path) != receipt['sha256']
                or receipt['condition'] != command['success']
                or status['status'] != stage + '_complete'
                or status['partition'] != partition
                or status['manifest_sha256'] != digest(frozen_path)):
            raise ValueError('receipt, stage identity or partition mismatch')
        for filename, expected in status['output_sha256'].items():
            artifact = job / stage / filename
            if digest(artifact) != expected:
                raise ValueError('stage artifact drift')
            sources[str(artifact)] = expected
        sources[str(path)] = digest(path)
        stages[stage] = status
    for down, key, up in (('train', 'extraction_status_sha256', 'extract'),
                          ('online', 'head_status_sha256', 'train'),
                          ('audit', 'online_status_sha256', 'online')):
        if stages[down][key] != digest(job / up / 'status.json'):
            raise ValueError('cross-stage lineage mismatch')
    with Path(partition['manifest']).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    with (job / 'online' / 'calls.jsonl').open() as stream:
        calls = [json.loads(line) for line in stream]
    metrics = (call_metrics(calls, partition, rows) if name.startswith('HyTex_')
               else audit_records(calls, partition, rows))
    summary = read(job / 'audit' / 'summary.json')
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            if abs(summary[key] - value) > 1e-12:
                raise ValueError('independent call reaggregation mismatch')
        elif summary[key] != value:
            raise ValueError('call declaration mismatch')
    sources[str(state_path)] = digest(state_path)
    sources[str(frozen_path)] = digest(frozen_path)
    return {'dataset': partition['dataset'], 'seed': partition['seed'],
            'outer_fold': partition['outer_fold'], **metrics}


def comparisons(dataset, records, method):
    local = ROOT / 'results/analysis/blocker_resolution_20261101/full_panel_online_v1/condition_summary.csv'
    if digest(local) != LOCAL_SHA:
        raise ValueError('local baseline hash drift')
    lookup = {(int(r['seed']), int(r['outer_fold'])): r for r in records}
    result = []
    with local.open(newline='') as stream:
        for row in csv.DictReader(stream):
            key = (int(row['seed']), int(row['outer_fold']))
            if row['dataset'] != dataset or key not in lookup:
                continue
            ref = lookup[key]
            if int(row['calls']) != int(ref['calls']):
                raise ValueError('call coverage differs')
            result.append({'dataset': dataset, 'seed': key[0], 'outer_fold': key[1],
                'local_classifier': row['classifier'], 'local_method': row['method'],
                'reference_method': method, 'local_f1': float(row['macro_f1_online']),
                'reference_f1': float(ref['macro_f1_online']),
                'delta_f1_local_minus_reference': float(row['macro_f1_online']) - float(ref['macro_f1_online']),
                'local_mean_ms': float(row['mean_ms']), 'reference_mean_ms': float(ref['mean_ms']),
                'calls': int(ref['calls']), 'physical_timing_reserve_local': row['physical_timing_reserve']})
    if len(result) != 10 * len(records):
        raise ValueError('all local comparator conditions required')
    return result


def summarize(records, dataset, method):
    if dataset == 'FMD':
        ids, calls = {(s, f) for s in (42, 123, 2026) for f in range(5)}, 3000
    else:
        ids, calls = {(42, 0)}, 680
    checked_coverage(records, ids, calls)
    if any(r['dataset'] != dataset for r in records):
        raise ValueError('dataset identity drift')
    return {'status': 'COMPLETE_DATASET_ADAPTATION_REAGGREGATED', 'dataset': dataset,
        'method': method, 'conditions': len(records), 'calls': calls,
        'mean_split_macro_f1': statistics.mean(float(r['macro_f1_online']) for r in records),
        'mean_ms_all_calls': sum(float(r['mean_ms']) * int(r['calls']) for r in records) / calls,
        'same_call_quality_and_timing': True, 'paper_scores_reproduced': False,
        'global_inference_performed': False}


def main(output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest, worker = read(QUEUE / 'manifest.json'), read(QUEUE / 'gpu.json')
    mh = digest(QUEUE / 'manifest.json')
    if worker['status'] != 'all_tasks_terminal' or worker.get('current_task') is not None or worker['manifest_sha256'] != mh:
        raise ValueError('terminal worker required; do not audit during benchmark')
    verify_sources(manifest)
    if {t['id'] for t in manifest['tasks']} != set(SPECS):
        raise ValueError('unexpected recovery scope')
    if digest(BASE / 'coverage.json') != EXPECTED_BASE or digest(PRIOR / 'summary.json') != EXPECTED_PRIOR:
        raise ValueError('prior baseline drift')
    sources = {str(QUEUE / 'manifest.json'): mh, str(QUEUE / 'gpu.json'): digest(QUEUE / 'gpu.json'),
               str(BASE / 'coverage.json'): EXPECTED_BASE, str(PRIOR / 'summary.json'): EXPECTED_PRIOR}
    recovered = {t['id']: audit_task(t, mh, worker, sources) for t in manifest['tasks']}
    # Existing 14-condition audit has its own pinned source lineage; verify it afresh.
    previous_sources = read(PRIOR / 'provenance.json')
    for name, sha in previous_sources.items():
        if digest(name) != sha:
            raise ValueError('prior 14-condition source drift: ' + name)
        sources[name] = sha
    with (PRIOR / 'condition_metrics.csv').open(newline='') as stream:
        previous = list(csv.DictReader(stream))
    sources[str(PRIOR / 'condition_metrics.csv')] = digest(PRIOR / 'condition_metrics.csv')
    conditions = {'HyTexNet adapted': [recovered['HyTex_Outex13Official1360_s42_f0']],
                  'LBP+dCellNN adapted': previous + [recovered['CellNN_FMD_s42_f0']]}
    summaries, all_comparisons = {}, []
    for method, dataset in (('HyTexNet adapted', 'Outex13Official1360'), ('LBP+dCellNN adapted', 'FMD')):
        records = conditions[method]
        summaries[method] = summarize(records, dataset, method)
        all_comparisons.extend(comparisons(dataset, records, method))
    baseline = read(BASE / 'coverage.json')
    rows = baseline['rows']
    for row in rows:
        if (row['method'], row['dataset']) in (("HyTexNet adapted", "Outex13Official1360"),
                                               ("LBP+dCellNN adapted", "FMD")):
            summary = summaries[row['method']]
            row.update(status='complete_dataset', complete_conditions=summary['conditions'],
                       audited_online_calls=summary['calls'], full_dataset_complete=True,
                       mean_split_macro_f1=summary['mean_split_macro_f1'],
                       mean_ms_all_calls=summary['mean_ms_all_calls'])
    coverage = {}
    for method in conditions:
        subset = [r for r in rows if r['method'] == method]
        coverage[method] = {'complete_datasets': sum(r['full_dataset_complete'] for r in subset),
            'expected_datasets': 6, 'complete_conditions': sum(r['complete_conditions'] for r in subset),
            'expected_conditions': 47, 'audited_online_calls': sum(r['audited_online_calls'] for r in subset),
            'expected_online_calls': 36264, 'six_dataset_panel_complete': all(r['full_dataset_complete'] for r in subset)}
        if coverage[method] != {'complete_datasets': 6, 'expected_datasets': 6,
                'complete_conditions': 47, 'expected_conditions': 47, 'audited_online_calls': 36264,
                'expected_online_calls': 36264, 'six_dataset_panel_complete': True}:
            raise ValueError('full panel coverage mismatch')
    sources[str(Path(__file__).resolve())] = digest(__file__)
    report = {'status': 'BOTH_ADAPTED_PANELS_COMPLETE', 'coverage': coverage, 'rows': rows,
        'pooled_f1_or_latency_reported': False, 'faithful_paper_percentage_reproductions': 0,
        'reservations': ['adaptations, not original published scores',
            'shared hardware and separate measurement dates', 'KTH historical and DTD physical reserves retained']}
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / 'coverage.csv', rows)
    write_csv(output / 'comparison_by_condition.csv', all_comparisons)
    for name, recs in conditions.items():
        slug = 'hytex_outex' if name.startswith('HyTex') else 'cellnn_fmd'
        write_csv(output / (slug + '_conditions.csv'), recs)
    (output / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'summaries.json').write_text(json.dumps(summaries, indent=2) + '\n')
    (output / 'provenance.json').write_text(json.dumps(sources, indent=2) + '\n')
    print(json.dumps({'coverage': coverage, 'summaries': summaries}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
