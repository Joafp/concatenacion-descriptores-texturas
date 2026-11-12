"""Read-only cross-check of completed Outex-13 online calls, not a benchmark."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / 'results/analysis'
LOCAL_QUEUE = ANALYSIS / 'blocker_resolution_20261101/queue_v1'
LOCAL_PROVENANCE = ANALYSIS / 'blocker_resolution_20261101/full_panel_online_v1/provenance.json'
EXTERNAL = {
    'CellNN adaptado': ('cellnn_outex_external_queue_20261102_v1', 'CellNN_Outex13Official1360_s42_f0'),
    'HyTex adaptado': ('authorized_paper_infra_recovery_20261102_v1', 'HyTex_Outex13Official1360_s42_f0'),
    'Neshov BEiTv2+MLP adaptado': ('neshov_batch1_extension_queue_20261102_v1', 'Neshov_Outex13Official1360_s42_f0'),
    'DeepLumina adaptado': ('deeplumina_outex_external_queue_20261103_v1', 'DeepLumina_Outex13Official1360_s42_f0'),
}


def read_json(path):
    return json.loads(path.read_text())


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def unique_by_id(rows):
    result = {}
    for row in rows:
        key = int(row['row_index'])
        if key in result:
            raise ValueError(f'duplicate row_index {key}')
        result[key] = row
    return result


def macro_f1(truth, predictions):
    if not truth or len(truth) != len(predictions):
        raise ValueError('invalid truth/prediction lengths')
    classes = set(truth) | set(predictions)
    f1 = []
    for cls in classes:
        tp = sum(a == cls and b == cls for a, b in zip(truth, predictions))
        fp = sum(a != cls and b == cls for a, b in zip(truth, predictions))
        fn = sum(a == cls and b != cls for a, b in zip(truth, predictions))
        f1.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
    return statistics.mean(f1)


def measurements(rows, truth_key, prediction_key, time_key):
    truth = [int(r[truth_key]) for r in rows]
    predictions = [int(r[prediction_key]) for r in rows]
    times = [float(r[time_key]) for r in rows]
    if any(not math.isfinite(t) or t <= 0 for t in times):
        raise ValueError('invalid online time')
    return {'calls': len(rows), 'macro_f1': macro_f1(truth, predictions),
            'accuracy': sum(a == b for a, b in zip(truth, predictions)) / len(truth),
            'mean_ms': statistics.mean(times)}


def audit(output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    provenance = {str(LOCAL_PROVENANCE): digest(LOCAL_PROVENANCE), str(Path(__file__).resolve()): digest(Path(__file__))}
    local_prov = read_json(LOCAL_PROVENANCE)
    local = {}
    local_statuses = {}
    for classifier in ('svm', 'resmlp'):
        job = LOCAL_QUEUE / 'jobs' / f'Outex13Official1360_{classifier}_s42_f0' / 'online'
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
        with calls_path.open(newline='') as stream:
            groups = defaultdict(list)
            for row in csv.DictReader(stream):
                groups[row['policy']].append(row)
        if len(groups) != 5:
            raise ValueError('five local policies required per classifier')
        for policy, records in groups.items():
            by_id = unique_by_id(records)
            if len(by_id) != 680 or any(int(r['repeat']) != 0 for r in records):
                raise ValueError('local Outex coverage/repeats differ')
            local[(classifier, policy)] = (by_id, measurements(records, 'label', 'prediction', 'ms'))

    first_local = next(iter(local.values()))[0]
    expected_ids = set(first_local)
    for records, _ in local.values():
        if set(records) != expected_ids or any(int(records[i]['label']) != int(first_local[i]['label']) for i in expected_ids):
            raise ValueError('local IDs or truth differ between policies')

    comparisons, references = [], {}
    seen_images = {}
    for name, (queue_name, task) in EXTERNAL.items():
        queue = ANALYSIS / queue_name
        job = queue / 'jobs' / task
        state_path, online_path = queue / 'tasks' / task / 'state.json', job / 'online/status.json'
        calls_path = job / 'online/calls.jsonl'
        state, status, worker = read_json(state_path), read_json(online_path), read_json(queue / 'gpu.json')
        if state['status'] != 'complete' or worker['outcomes'].get(task) != 'complete':
            raise ValueError(f'incomplete state: {name}')
        if state['manifest_sha256'] != digest(queue / 'manifest.json'):
            raise ValueError(f'manifest hash mismatch: {name}')
        receipts = [r for r in state['success_artifacts'] if r['path'] == str(online_path)]
        if len(receipts) != 1 or receipts[0]['sha256'] != digest(online_path):
            raise ValueError(f'online status receipt mismatch: {name}')
        if status['status'] != 'online_complete' or status['output_sha256']['calls.jsonl'] != digest(calls_path):
            raise ValueError(f'online calls receipt mismatch: {name}')
        for p in (queue / 'manifest.json', queue / 'gpu.json', state_path, online_path, calls_path):
            provenance[str(p)] = digest(p)
        with calls_path.open() as stream:
            records = [json.loads(line) for line in stream]
        by_id = unique_by_id(records)
        partition = status['partition']
        if set(by_id) != expected_ids or set(partition['external_indices']) != expected_ids:
            raise ValueError(f'external IDs differ: {name}')
        if any(int(by_id[i]['truth']) != int(first_local[i]['label']) for i in expected_ids):
            raise ValueError(f'external truth differs: {name}')
        manifest_path = Path(partition['manifest'])
        provenance[str(manifest_path)] = digest(manifest_path)
        with manifest_path.open(newline='') as stream:
            image_rows = {int(r['row_id']): r for r in csv.DictReader(stream)}
        for i in expected_ids:
            row = image_rows[i]
            image = Path(row['path'])
            if int(row['label']) != int(first_local[i]['label']):
                raise ValueError(f'manifest label mismatch: {name} {i}')
            for local_status in local_statuses.values():
                if local_status['image_sha256'].get(str(image)) != row['sha256']:
                    raise ValueError(f'local image identity mismatch: {name} {i}')
            if str(image) not in seen_images:
                seen_images[str(image)] = digest(image)
            if seen_images[str(image)] != row['sha256']:
                raise ValueError(f'current image checksum mismatch: {name} {i}')
        ref = measurements(records, 'truth', 'prediction', 'elapsed_ms')
        references[name] = ref
        for (classifier, policy), (_, loc) in sorted(local.items()):
            comparisons.append({'dataset': 'Outex13Official1360', 'seed': 42, 'fold': 0,
                'classifier': classifier, 'local_method': policy, 'reference_method': name,
                'calls_each': loc['calls'], 'local_macro_f1': loc['macro_f1'],
                'reference_macro_f1': ref['macro_f1'], 'delta_f1_local_minus_reference': loc['macro_f1'] - ref['macro_f1'],
                'local_mean_ms': loc['mean_ms'], 'reference_mean_ms': ref['mean_ms'],
                'delta_ms_local_minus_reference': loc['mean_ms'] - ref['mean_ms']})
    if len(seen_images) != 680 or len(comparisons) != 40:
        raise ValueError('incomplete Outex audit')
    summary = {'status': 'OUTEX_CROSSCALL_AUDIT_COMPLETE', 'dataset': 'Outex13Official1360',
        'conditions': 1, 'unique_images': 680, 'local_heads': 2, 'local_policies_per_head': 5,
        'external_adaptations': 4, 'comparisons': 40,
        'row_ids_truth_and_image_sha256_match': True, 'same_call_quality_and_timing': True,
        'hardware_timing_reservation': 'Measurements are from separate dates and shared hardware; differences are descriptive.',
        'paper_scores_reproduced': False, 'reference_results': references}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + '\n')
    with (output / 'comparisons.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparisons[0])); writer.writeheader(); writer.writerows(comparisons)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    audit(args.output)
