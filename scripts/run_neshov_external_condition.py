"""Frozen FMD external adaptation stages. No retries or checkpoint downloads."""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from consolidate_overnight_online_panel import digest, read, macro_f1


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def verify_artifact(folder, expected_status):
    status = read(folder / 'status.json')
    if status['status'] != expected_status:
        raise ValueError('incomplete upstream stage')
    for name, sha in status['output_sha256'].items():
        if digest(folder / name) != sha:
            raise ValueError('upstream artifact drift: ' + name)
    return status


def extract(partition, rows, preflight, output):
    import numpy as np
    import torch
    from PIL import Image
    from neshov_beit_reference import FrozenLayerAggregation, load_offline_backbone, preprocessing
    model, info = load_offline_backbone()
    if digest(info['local_weight_path']) != preflight['checkpoint_sha256']:
        raise ValueError('checkpoint mismatch')
    model = FrozenLayerAggregation(model).to('cuda', dtype=torch.float32).eval()
    transform = preprocessing()

    def image(index):
        row = rows[index]
        path = ROOT / row['path']
        if digest(path) != row['sha256']:
            raise ValueError('image drift')
        with Image.open(path) as source:
            return transform(source.convert('RGB'))

    train = partition['training_indices']
    chunks = []
    with torch.inference_mode():
        for start in range(0, len(train), 8):
            x = torch.stack([image(i) for i in train[start:start + 8]]).to('cuda')
            chunk = model(x).cpu().numpy()
            if chunk.shape != (len(x), 3072) or not np.isfinite(chunk).all():
                raise ValueError('invalid extracted features')
            chunks.append(chunk)
            print(f'extracted {start + len(x)}/{len(train)}', flush=True)
        features = np.concatenate(chunks)
        errors = []
        for pos in (0, len(train) - 1):
            actual = model(image(train[pos]).unsqueeze(0).to('cuda')).cpu().numpy()[0]
            errors.append(float(np.max(np.abs(actual - features[pos]))))
        # Preserve comparison evidence before accepting or rejecting tolerance.
        write(output / 'parity.json', {'training_rows': [train[0], train[-1]],
                                      'max_abs_errors': errors, 'tolerance': 1e-4})
        if max(errors) > 1e-4:
            raise ValueError('batch1/batch8 feature parity failed; requires review')
    np.savez_compressed(output / 'features.npz', rows=np.asarray(train), features=features)
    return {'parity_max_abs_error': max(errors), 'training_images': len(train)}


def train_head(partition, rows, extract_dir, output):
    import numpy as np
    import torch
    from neshov_reference_training import fit_fixed_head
    verify_artifact(extract_dir, 'extract_complete')
    data = np.load(extract_dir / 'features.npz', allow_pickle=False)
    ids = partition['training_indices']
    if not np.array_equal(data['rows'], ids):
        raise ValueError('training row order drift')
    labels = partition['labels']
    mapping = {label: i for i, label in enumerate(labels)}
    truth = [mapping[int(rows[i]['label'])] for i in ids]
    head, history = fit_fixed_head(data['features'], truth, len(labels),
                                   epochs=100, batch_size=32, seed=42)
    torch.save(head.state_dict(), output / 'head.pt')
    write(output / 'labels.json', labels)
    write(output / 'training_history.json', history)
    with torch.inference_mode():
        logits = head(torch.from_numpy(data['features'])).numpy()
    np.savez_compressed(output / 'training_logits.npz', rows=data['rows'], logits=logits)
    return {'training_images': len(ids), 'epochs': 100, 'training_seed': 42,
            'epoch_selection': 'final; no early stopping',
            'extraction_status_sha256': digest(extract_dir / 'status.json')}


def online(partition, rows, preflight, head_dir, output):
    import platform
    from neshov_online_adapter import NeshovOnlineAdapter
    head_status = verify_artifact(head_dir, 'train_complete')
    labels = read(head_dir / 'labels.json')
    if labels != partition['labels']:
        raise ValueError('class mapping drift')
    adapter = NeshovOnlineAdapter.from_saved_head(
        head_dir / 'head.pt', head_status['output_sha256']['head.pt'],
        preflight['checkpoint_sha256'], labels, 'cuda')
    write(output / 'environment.json', {'utc': utc(), 'pid': os.getpid(),
          'platform': platform.platform(), 'python': sys.version,
          'cpu_threads': 2, 'hardware_isolated': False, 'adapter': adapter.provenance})
    for _ in range(5):
        adapter.predict_file(ROOT / rows[partition['training_indices'][0]]['path'])
    with (output / 'calls.jsonl').open('x') as stream:
        for number, index in enumerate(partition['external_indices']):
            row = rows[index]
            path = ROOT / row['path']
            if digest(path) != row['sha256']:
                raise ValueError('external image drift')
            timestamp = utc()
            result = adapter.predict_file(path)
            record = {'row_index': index, 'truth': int(row['label']),
                      'repeat': 0, 'started_utc': timestamp, **result}
            stream.write(json.dumps(record, allow_nan=False) + '\n')
            stream.flush()
            if number % 25 == 0:
                print(f'online {number + 1}/{len(partition["external_indices"])}', flush=True)
    return {'head_status_sha256': digest(head_dir / 'status.json'),
            'calls': len(partition['external_indices']), 'warmup_calls_excluded': 5}


def audit_calls(partition, rows, online_dir, output):
    import math
    import statistics
    import numpy as np
    verify_artifact(online_dir, 'online_complete')
    calls = [json.loads(line) for line in (online_dir / 'calls.jsonl').read_text().splitlines()]
    if [c['row_index'] for c in calls] != partition['external_indices']:
        raise ValueError('online coverage or ordering mismatch')
    for call in calls:
        if (call['truth'] != int(rows[call['row_index']]['label']) or call['repeat'] != 0
                or call['prediction'] not in partition['labels']
                or len(call['logits']) != len(partition['labels'])
                or not all(math.isfinite(v) for v in call['logits'])
                or partition['labels'][int(np.argmax(call['logits']))] != call['prediction']
                or not math.isfinite(call['elapsed_ms']) or call['elapsed_ns'] <= 0
                or call['elapsed_ms'] != call['elapsed_ns'] / 1e6):
            raise ValueError('invalid same-call prediction/timing')
    truth, prediction = [c['truth'] for c in calls], [c['prediction'] for c in calls]
    times = [c['elapsed_ms'] for c in calls]
    result = {'calls': len(calls), 'macro_f1_online': macro_f1(truth, prediction),
              'accuracy_online': statistics.mean(t == p for t, p in zip(truth, prediction)),
              'mean_ms': statistics.mean(times), 'median_ms': statistics.median(times),
              'p95_ms': float(np.percentile(times, 95)), 'same_call_quality_and_timing': True,
              'online_status_sha256': digest(online_dir / 'status.json')}
    write(output / 'summary.json', result)
    return result


def run(manifest_path, number, stage, job):
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import torch
    torch.set_num_threads(2)
    torch.manual_seed(42)
    torch.use_deterministic_algorithms(True)
    preflight = read(manifest_path)
    for name, sha in preflight['source_sha256'].items():
        if digest(name) != sha:
            raise ValueError('preflight source drift: ' + name)
    partition = preflight['conditions'][number]
    with Path(partition['manifest']).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    output = Path(job) / stage
    output.mkdir(parents=True, exist_ok=False)
    report = {'status': 'running', 'stage': stage, 'started_utc': utc(),
              'seed': partition['seed'], 'outer_fold': partition['outer_fold'],
              'partition': partition, 'manifest_sha256': digest(manifest_path),
              'runner_sha256': digest(__file__)}
    write(output / 'status.json', report)
    try:
        if stage == 'extract':
            extra = extract(partition, rows, preflight, output)
        elif stage == 'train':
            extra = train_head(partition, rows, Path(job) / 'extract', output)
        elif stage == 'online':
            extra = online(partition, rows, preflight, Path(job) / 'train', output)
        else:
            extra = audit_calls(partition, rows, Path(job) / 'online', output)
        report.update(extra, status=stage + '_complete', finished_utc=utc(),
                      output_sha256={p.name: digest(p) for p in output.iterdir() if p.name != 'status.json'})
        write(output / 'status.json', report)
    except Exception as exc:
        report.update(status='requires_review', error=f'{type(exc).__name__}: {exc}', finished_utc=utc())
        write(output / 'status.json', report)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--number', type=int, required=True)
    parser.add_argument('--stage', choices=['extract', 'train', 'online', 'audit'], required=True)
    parser.add_argument('--job', type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.number, args.stage, args.job)
