"""Reconcile the 15 complete FMD conditions from saved online calls only."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics

from audit_outex_crosscalls_20261104 import (
    ROOT, ANALYSIS, LOCAL_PROVENANCE, digest, measurements, read_json, unique_by_id,
)

METHODS = ('CellNN', 'HyTex', 'Neshov', 'DeepLumina')


def local_job(classifier, seed, fold):
    if (seed, fold) == (42, 0):
        if classifier == 'svm':
            return ROOT / 'results/exploratory/local_batch1_20261028/FMD_s42_f0_svm'
        return ROOT / 'results/exploratory/local_batch1_followup_20261028/FMD_s42_f0/resmlp_online'
    return ANALYSIS / 'overnight_f1_latency_20261028/jobs' / f'FMD_{classifier}_s{seed}_f{fold}' / 'online'


def external_job(method, seed, fold):
    task = f'{method}_FMD_s{seed}_f{fold}'
    if method == 'CellNN':
        queue_name = ('authorized_paper_infra_recovery_20261102_v1' if (seed, fold) == (42, 0)
                      else 'cellnn_fmd_never_started_queue_20261102_v2')
    else:
        queue_name = {'HyTex': 'hytex_fmd_external_queue_20261102_v1',
                      'Neshov': 'neshov_fmd_batch1_queue_20261102_v1',
                      'DeepLumina': 'deeplumina_fmd_external_queue_20261103_v1'}[method]
    return ANALYSIS / queue_name, task


def audit(output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    local_prov = read_json(LOCAL_PROVENANCE)
    provenance = {str(LOCAL_PROVENANCE): digest(LOCAL_PROVENANCE),
                  str(Path(__file__).resolve()): digest(Path(__file__)),
                  str(Path(__file__).with_name('audit_outex_crosscalls_20261104.py')):
                      digest(Path(__file__).with_name('audit_outex_crosscalls_20261104.py'))}
    seen_images, comparisons, condition_refs = {}, [], []
    condition_ids = [(s, f) for s in (42, 123, 2026) for f in range(5)]
    for seed, fold in condition_ids:
        local, local_statuses = {}, {}
        for classifier in ('svm', 'resmlp'):
            job = local_job(classifier, seed, fold)
            status_path, calls_path = job / 'status.json', job / 'online_calls.csv'
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
                for row in csv.DictReader(stream):
                    groups[row['policy']].append(row)
            if len(groups) != 5:
                raise ValueError('five local policies required per classifier')
            for policy, records in groups.items():
                by_id = unique_by_id(records)
                if len(by_id) != 200 or any(int(r['repeat']) != 0 for r in records):
                    raise ValueError('FMD local coverage/repeats differ')
                local[(classifier, policy)] = (by_id, measurements(records, 'label', 'prediction', 'ms'))
        first_local = next(iter(local.values()))[0]
        ids = set(first_local)
        for records, _ in local.values():
            if set(records) != ids or any(int(records[i]['label']) != int(first_local[i]['label']) for i in ids):
                raise ValueError('local IDs or truth differ between policies')

        for method in METHODS:
            queue, task = external_job(method, seed, fold)
            state_path = queue / 'tasks' / task / 'state.json'
            online_path = queue / 'jobs' / task / 'online/status.json'
            calls_path = queue / 'jobs' / task / 'online/calls.jsonl'
            state, status, worker = read_json(state_path), read_json(online_path), read_json(queue / 'gpu.json')
            if state['status'] != 'complete' or worker['outcomes'].get(task) != 'complete':
                raise ValueError(f'incomplete state: {task}')
            if state['manifest_sha256'] != digest(queue / 'manifest.json'):
                raise ValueError(f'manifest hash mismatch: {task}')
            receipts = [r for r in state['success_artifacts'] if r['path'] == str(online_path)]
            if len(receipts) != 1 or receipts[0]['sha256'] != digest(online_path):
                raise ValueError(f'online receipt mismatch: {task}')
            if status['status'] != 'online_complete' or status['output_sha256']['calls.jsonl'] != digest(calls_path):
                raise ValueError(f'calls checksum mismatch: {task}')
            for p in (queue / 'manifest.json', queue / 'gpu.json', state_path, online_path, calls_path):
                provenance[str(p)] = digest(p)
            with calls_path.open() as stream:
                records = [json.loads(line) for line in stream]
            by_id = unique_by_id(records)
            partition = status['partition']
            if set(by_id) != ids or set(partition['external_indices']) != ids:
                raise ValueError(f'external IDs differ: {task}')
            if any(int(by_id[i]['truth']) != int(first_local[i]['label']) for i in ids):
                raise ValueError(f'external truth differs: {task}')
            manifest_path = Path(partition['manifest'])
            provenance[str(manifest_path)] = digest(manifest_path)
            with manifest_path.open(newline='') as stream:
                image_rows = {int(row['row_id']): row for row in csv.DictReader(stream)}
            for i in ids:
                row = image_rows[i]
                image = Path(row['path'])
                if int(row['label']) != int(first_local[i]['label']):
                    raise ValueError(f'manifest label mismatch: {task} {i}')
                for local_status in local_statuses.values():
                    if local_status['image_sha256'].get(str(image)) != row['sha256']:
                        raise ValueError(f'local image identity mismatch: {task} {i}')
                if str(image) not in seen_images:
                    seen_images[str(image)] = digest(image)
                if seen_images[str(image)] != row['sha256']:
                    raise ValueError(f'current image checksum mismatch: {task} {i}')
            ref = measurements(records, 'truth', 'prediction', 'elapsed_ms')
            condition_refs.append({'seed': seed, 'fold': fold, 'method': method, **ref})
            for (classifier, policy), (_, loc) in sorted(local.items()):
                comparisons.append({'dataset': 'FMD', 'seed': seed, 'fold': fold,
                    'classifier': classifier, 'local_method': policy, 'reference_method': method,
                    'calls_each': loc['calls'], 'local_macro_f1': loc['macro_f1'],
                    'reference_macro_f1': ref['macro_f1'], 'delta_f1_local_minus_reference': loc['macro_f1']-ref['macro_f1'],
                    'local_mean_ms': loc['mean_ms'], 'reference_mean_ms': ref['mean_ms'],
                    'delta_ms_local_minus_reference': loc['mean_ms']-ref['mean_ms']})
    if len(seen_images) != 1000 or len(condition_refs) != 60 or len(comparisons) != 600:
        raise ValueError('incomplete FMD coverage')
    grouped = defaultdict(list)
    for row in comparisons:
        grouped[(row['classifier'], row['local_method'], row['reference_method'])].append(row)
    dataset_comparisons = []
    for (classifier, policy, ref), rows in sorted(grouped.items()):
        if len(rows) != 15:
            raise ValueError('dataset comparison requires all 15 conditions')
        dataset_comparisons.append({'classifier': classifier, 'local_method': policy, 'reference_method': ref,
            'conditions': len(rows), 'calls_each': sum(r['calls_each'] for r in rows),
            'local_mean_split_f1': statistics.mean(r['local_macro_f1'] for r in rows),
            'reference_mean_split_f1': statistics.mean(r['reference_macro_f1'] for r in rows),
            'mean_delta_f1_local_minus_reference': statistics.mean(r['delta_f1_local_minus_reference'] for r in rows),
            'local_mean_ms': statistics.mean(r['local_mean_ms'] for r in rows),
            'reference_mean_ms': statistics.mean(r['reference_mean_ms'] for r in rows)})
    results = {}
    for method in METHODS:
        rows = [x for x in condition_refs if x['method'] == method]
        results[method] = {'conditions': len(rows), 'calls': sum(r['calls'] for r in rows),
            'mean_split_macro_f1': statistics.mean(r['macro_f1'] for r in rows),
            'mean_split_accuracy': statistics.mean(r['accuracy'] for r in rows),
            'mean_ms': statistics.mean(r['mean_ms'] for r in rows)}
    summary = {'status': 'FMD_CROSSCALL_AUDIT_COMPLETE', 'conditions': 15,
        'calls_per_method': 3000, 'unique_images': len(seen_images), 'comparisons': len(comparisons),
        'row_ids_truth_and_image_sha256_match': True, 'same_call_quality_and_timing': True,
        'hardware_timing_reservation': 'Separate dates and shared hardware; latency differences are descriptive.',
        'paper_scores_reproduced': False, 'reference_results': results}
    output.mkdir(parents=True, exist_ok=False)
    (output/'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n')
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2, ensure_ascii=False)+'\n')
    for filename, rows in [('condition_references.csv', condition_refs), ('condition_comparisons.csv', comparisons),
                           ('dataset_comparisons.csv', dataset_comparisons)]:
        with (output/filename).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    audit(args.output)
