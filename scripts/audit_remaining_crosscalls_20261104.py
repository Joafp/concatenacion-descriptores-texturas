"""Independently reconcile complete dataset conditions from frozen online calls."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import re
import statistics

from audit_outex_crosscalls_20261104 import (
    ANALYSIS, LOCAL_PROVENANCE, digest, measurements, read_json, unique_by_id,
)

DATASETS = {'CUReT': ('curet', 2), 'DTD': ('dtd', 10),
            'SoilOriginal': ('soil', 15), 'KTHTIPS2b': ('kth', 4)}
NESHOV_NAMES = {'CUReT': 'curet', 'DTD': 'dtd', 'SoilOriginal': 'soiloriginal', 'KTHTIPS2b': 'kthtips2b'}


def paths_for_method(dataset, code, method):
    if method == 'Neshov':
        queue = ANALYSIS / 'neshov_batch1_extension_queue_20261102_v1'
        summary = ANALYSIS / f'neshov_batch1_{NESHOV_NAMES[dataset]}_summary_20261103_v1'
    elif method == 'DeepLumina':
        queue = ANALYSIS / f'deeplumina_{code}_external_queue_20261103_v1'
        summary = ANALYSIS / f'deeplumina_{code}_external_summary_20261103_v1'
    else:
        queue = ANALYSIS / f'{method.lower()}_{code}_external_queue_20261102_v1'
        summary = ANALYSIS / f'{method.lower()}_{code}_external_summary_20261102_v1'
    return queue, summary


def audit(dataset, output):
    code, n_conditions = DATASETS[dataset]
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    provenance = {str(LOCAL_PROVENANCE): digest(LOCAL_PROVENANCE),
                  str(Path(__file__).resolve()): digest(Path(__file__)),
                  str(Path(__file__).with_name('audit_outex_crosscalls_20261104.py')):
                      digest(Path(__file__).with_name('audit_outex_crosscalls_20261104.py'))}
    local_prov = read_json(LOCAL_PROVENANCE)
    source_index = {}
    expression = re.compile(r'/jobs/([^/]+)_(svm|resmlp)_s([0-9]+)_f([0-9]+)/online/online_calls\.csv$')
    for name, sha in local_prov.items():
        match = expression.search(name)
        if match and match.group(1) == dataset:
            key = (match.group(2), int(match.group(3)), int(match.group(4)))
            if key in source_index:
                raise ValueError(f'ambiguous local source: {key}')
            source_index[key] = Path(name)
    ids_by_condition = ([(s, f) for s in (42, 123, 2026) for f in range(5)]
                        if dataset == 'SoilOriginal' else [(42, f) for f in range(n_conditions)])
    if set(source_index) != {(c, s, f) for c in ('svm', 'resmlp') for s, f in ids_by_condition}:
        raise ValueError('local source condition coverage mismatch')
    methods = ('CellNN', 'HyTex', 'Neshov') if dataset == 'DTD' else ('CellNN', 'HyTex', 'Neshov', 'DeepLumina')
    local_summary_path = ANALYSIS / 'blocker_resolution_20261101/full_panel_online_v1/condition_summary.csv'
    with local_summary_path.open(newline='') as stream:
        local_summary = {(r['classifier'], int(r['seed']), int(r['outer_fold']), r['method']): r
                         for r in csv.DictReader(stream) if r['dataset'] == dataset}
    provenance[str(local_summary_path)] = digest(local_summary_path)
    dataset_sources = {}
    for method in methods:
        queue, summary_dir = paths_for_method(dataset, code, method)
        source_prov = summary_dir / 'provenance.json'
        dataset_sources[method] = (queue, summary_dir, read_json(source_prov))
        provenance[str(source_prov)] = digest(source_prov)
    image_cache, manifest_cache, comparison_rows, ref_rows = {}, {}, [], []
    for seed, fold in ids_by_condition:
        local, local_statuses = {}, {}
        for classifier in ('svm', 'resmlp'):
            calls_path = source_index[(classifier, seed, fold)]
            status_path = calls_path.with_name('status.json')
            for p in (status_path, calls_path):
                sha = digest(p)
                if local_prov.get(str(p)) != sha:
                    raise ValueError(f'local provenance mismatch: {p}')
                provenance[str(p)] = sha
            status = read_json(status_path)
            if status['output_sha256']['online_calls.csv'] != digest(calls_path):
                raise ValueError('local receipt mismatch')
            local_statuses[classifier] = status
            groups = defaultdict(list)
            with calls_path.open(newline='') as stream:
                for row in csv.DictReader(stream): groups[row['policy']].append(row)
            if len(groups) != 5: raise ValueError('five local policies required')
            for policy, records in groups.items():
                by_id = unique_by_id(records)
                if len(by_id) != len(records) or any(int(r['repeat']) != 0 for r in records):
                    raise ValueError('local repeats or duplicates')
                metrics = measurements(records, 'label', 'prediction', 'ms')
                expected = local_summary[(classifier, seed, fold, policy)]
                if (len(by_id) != int(expected['calls']) or
                    abs(metrics['macro_f1']-float(expected['macro_f1_online'])) > 1e-12 or
                    abs(metrics['mean_ms']-float(expected['mean_ms'])) > 1e-8):
                    raise ValueError(f'local summary mismatch: {classifier} {seed} {fold} {policy}')
                local[(classifier, policy)] = (by_id, metrics, expected['physical_timing_reserve'])
        first_local = next(iter(local.values()))[0]
        ids = set(first_local)
        for records, _, _ in local.values():
            if set(records) != ids or any(int(records[i]['label']) != int(first_local[i]['label']) for i in ids):
                raise ValueError('local IDs or truth differ')
        for method in methods:
            queue, summary_dir, source_prov = dataset_sources[method]
            task = f'{method}_{dataset}_s{seed}_f{fold}'
            state_path = queue / 'tasks' / task / 'state.json'
            status_path = queue / 'jobs' / task / 'online/status.json'
            calls_path = queue / 'jobs' / task / 'online/calls.jsonl'
            state, status, worker = read_json(state_path), read_json(status_path), read_json(queue/'gpu.json')
            if state['status'] != 'complete' or worker['outcomes'].get(task) != 'complete':
                raise ValueError(f'incomplete condition: {task}')
            if state['manifest_sha256'] != digest(queue/'manifest.json'):
                raise ValueError(f'manifest hash mismatch: {task}')
            receipts = [r for r in state['success_artifacts'] if r['path'] == str(status_path)]
            if len(receipts) != 1 or receipts[0]['sha256'] != digest(status_path):
                raise ValueError(f'status receipt mismatch: {task}')
            if status['status'] != 'online_complete' or status['output_sha256']['calls.jsonl'] != digest(calls_path):
                raise ValueError(f'calls receipt mismatch: {task}')
            if source_prov.get(str(calls_path)) != digest(calls_path):
                raise ValueError(f'previous provenance mismatch: {task}')
            for p in (queue/'manifest.json', queue/'gpu.json', state_path, status_path, calls_path):
                provenance[str(p)] = digest(p)
            with calls_path.open() as stream: records = [json.loads(line) for line in stream]
            by_id = unique_by_id(records)
            partition = status['partition']
            if set(by_id) != ids or set(partition['external_indices']) != ids:
                raise ValueError(f'external IDs differ: {task}')
            if any(int(by_id[i]['truth']) != int(first_local[i]['label']) for i in ids):
                raise ValueError(f'external truth differs: {task}')
            manifest_path = Path(partition['manifest'])
            if manifest_path not in manifest_cache:
                with manifest_path.open(newline='') as stream:
                    manifest_cache[manifest_path] = {int(r['row_id']): r for r in csv.DictReader(stream)}
                provenance[str(manifest_path)] = digest(manifest_path)
            image_rows = manifest_cache[manifest_path]
            for i in ids:
                row = image_rows[i]; image = Path(row['path'])
                if int(row['label']) != int(first_local[i]['label']):
                    raise ValueError(f'manifest label mismatch: {task} {i}')
                for local_status in local_statuses.values():
                    if local_status['image_sha256'].get(str(image)) != row['sha256']:
                        raise ValueError(f'image identity mismatch: {task} {i}')
                if str(image) not in image_cache: image_cache[str(image)] = digest(image)
                if image_cache[str(image)] != row['sha256']:
                    raise ValueError(f'image checksum mismatch: {task} {i}')
            ref = measurements(records, 'truth', 'prediction', 'elapsed_ms')
            ref_rows.append({'dataset': dataset, 'seed': seed, 'fold': fold, 'method': method, **ref})
            for (classifier, policy), (_, loc, reserve) in sorted(local.items()):
                comparison_rows.append({'dataset': dataset, 'seed': seed, 'fold': fold,
                    'classifier': classifier, 'local_method': policy, 'reference_method': method,
                    'calls_each': loc['calls'], 'local_macro_f1': loc['macro_f1'],
                    'reference_macro_f1': ref['macro_f1'], 'delta_f1_local_minus_reference': loc['macro_f1']-ref['macro_f1'],
                    'local_mean_ms': loc['mean_ms'], 'reference_mean_ms': ref['mean_ms'],
                    'delta_ms_local_minus_reference': loc['mean_ms']-ref['mean_ms'],
                    'physical_timing_reserve_local': reserve})
    if len(ref_rows) != len(methods)*n_conditions or len(comparison_rows) != len(methods)*n_conditions*10:
        raise ValueError('incomplete comparison coverage')
    results, dataset_comparisons = {}, []
    for method in methods:
        rows = [r for r in ref_rows if r['method'] == method]
        calls = sum(r['calls'] for r in rows)
        results[method] = {'conditions': len(rows), 'calls': calls,
            'mean_split_macro_f1': statistics.mean(r['macro_f1'] for r in rows),
            'mean_split_accuracy': statistics.mean(r['accuracy'] for r in rows),
            'mean_ms': sum(r['mean_ms']*r['calls'] for r in rows)/calls}
        summary_dir = dataset_sources[method][1]
        expected_path = summary_dir/'summary.json'; expected = read_json(expected_path)
        provenance[str(expected_path)] = digest(expected_path)
        if (abs(expected['mean_split_macro_f1']-results[method]['mean_split_macro_f1']) > 1e-12 or
            abs(expected['mean_ms_all_calls']-results[method]['mean_ms']) > 1e-9):
            raise ValueError(f'prior audited aggregate mismatch: {method} {dataset}')
    grouped = defaultdict(list)
    for r in comparison_rows: grouped[(r['classifier'], r['local_method'], r['reference_method'])].append(r)
    for (classifier, policy, method), rows in sorted(grouped.items()):
        if len(rows) != n_conditions: raise ValueError('incomplete paired comparison')
        calls = sum(r['calls_each'] for r in rows)
        dataset_comparisons.append({'dataset': dataset, 'classifier': classifier, 'local_method': policy,
            'reference_method': method, 'conditions': len(rows), 'calls_each': calls,
            'local_mean_split_f1': statistics.mean(r['local_macro_f1'] for r in rows),
            'reference_mean_split_f1': statistics.mean(r['reference_macro_f1'] for r in rows),
            'mean_delta_f1_local_minus_reference': statistics.mean(r['delta_f1_local_minus_reference'] for r in rows),
            'local_mean_ms': sum(r['local_mean_ms']*r['calls_each'] for r in rows)/calls,
            'reference_mean_ms': sum(r['reference_mean_ms']*r['calls_each'] for r in rows)/calls,
            'physical_timing_reserve_local': any(str(r['physical_timing_reserve_local']).lower() == 'true' for r in rows)})
    summary = {'status': 'DATASET_CROSSCALL_AUDIT_COMPLETE', 'dataset': dataset, 'conditions': n_conditions,
        'unique_images': len(image_cache), 'completed_external_methods': list(methods),
        'excluded_incomplete_methods': ['DeepLumina 9/10 requires_review'] if dataset == 'DTD' else [],
        'condition_comparisons': len(comparison_rows), 'row_ids_truth_and_image_sha256_match': True,
        'same_call_quality_and_timing': True,
        'hardware_timing_reservation': 'Separate dates and shared hardware; latency differences are descriptive.',
        'paper_scores_reproduced': False, 'reference_results': results}
    output.mkdir(parents=True, exist_ok=False)
    (output/'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n')
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2, ensure_ascii=False)+'\n')
    for name, rows in [('condition_references.csv', ref_rows), ('condition_comparisons.csv', comparison_rows),
                       ('dataset_comparisons.csv', dataset_comparisons)]:
        with (output/name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=sorted(DATASETS), required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    audit(args.dataset, args.output)
