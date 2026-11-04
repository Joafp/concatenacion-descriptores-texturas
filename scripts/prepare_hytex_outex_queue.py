"""Freeze a new Outex HyTex adaptation queue; no model execution."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

from consolidate_overnight_online_panel import ROOT, read, digest, select_jobs
from prepare_neshov_fmd_external import validate_partition
from prepare_hytex_fmd_queue import CHECKPOINT_SHA

DATASET = 'Outex13Official1360'


def validate_outex(p, rows):
    if (len(rows) != 1360 or any(int(r['row_id']) != i for i, r in enumerate(rows))
            or (p['dataset'], p['seed'], p['outer_fold']) != (DATASET, 42, 0)):
        raise ValueError('Outex identity/count mismatch')
    train = [i for i, r in enumerate(rows) if r['official_split'] == 'train']
    test = [i for i, r in enumerate(rows) if r['official_split'] == 'test']
    if (len(train) != 680 or len(test) != 680 or p['training_indices'] != train
            or p['external_indices'] != test):
        raise ValueError('exact official Outex partition required')
    labels = validate_partition(train, test, rows)
    if labels != list(range(68)) or p['labels'] != labels:
        raise ValueError('Outex classes mismatch')


def label_digest(labels):
    return hashlib.sha256(labels.dtype.str.encode('ascii') +
        json.dumps(labels.shape).encode('ascii') + labels.tobytes(order='C')).hexdigest()


def validate_archived_truth(records, expected, rows):
    policies = {'Completa-22', 'Adaptive-selection-margin', 'Ens-diversidad', 'Ens-tombola', 'Top-4'}
    if {r['policy'] for r in records} != policies:
        raise ValueError('all five archived truth blocks required')
    for policy in policies:
        block = [r for r in records if r['policy'] == policy]
        if ([int(r['row_index']) for r in block] != expected
                or any(int(r['label']) != int(rows[int(r['row_index'])]['label']) for r in block)):
            raise ValueError('external canonical truth mismatch')


def prepare(output):
    import numpy as np
    from huggingface_hub import hf_hub_download
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    jobs, sources = select_jobs(ROOT)
    selected = [j for j in jobs if j['dataset'] == DATASET]
    if len(selected) != 2 or {j['classifier'] for j in selected} != {'svm', 'resmlp'}:
        raise ValueError('both canonical local heads required')
    canonical, partition = None, None
    for j in selected:
        quality_path, online_path = [Path(j[k]) / 'status.json' for k in ('quality_run', 'online_run')]
        q, online = read(quality_path), read(online_path)
        if (q['status'] != 'external_quality_complete_timing_pending'
                or online['quality_status_sha256'] != digest(quality_path)
                or digest(j['config']) != j['config_sha256']):
            raise ValueError('local lineage mismatch')
        args = read(j['config'])['provenance']['arguments']
        if args['official_split'] != 1 or args['invert_official_split']:
            raise ValueError('official direction drift')
        manifest_path = ROOT / q['provenance']['manifest_path']
        if digest(manifest_path) != q['provenance']['manifest_sha256']:
            raise ValueError('manifest drift')
        with manifest_path.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        for r in rows:
            r['sha256'] = r['source_sha256']
        if canonical is not None and rows != canonical:
            raise ValueError('head manifest disagreement')
        canonical = rows
        labels = np.asarray([int(r['label']) for r in rows], dtype=np.int64)
        if label_digest(labels) != q['provenance']['labels_sha256']:
            raise ValueError('full canonical label hash mismatch')
        prediction = Path(j['quality_run']) / 'predictions.csv'
        if digest(prediction) != q['output_sha256']['predictions.csv']:
            raise ValueError('archived truth file drift')
        with prediction.open(newline='') as stream:
            records = list(csv.DictReader(stream))
        validate_archived_truth(records, q['external_indices'], rows)
        p = {'dataset': DATASET, 'seed': j['seed'], 'outer_fold': j['outer_fold'],
             'training_indices': q['training_indices'], 'external_indices': q['external_indices'],
             'labels': list(range(68)), 'manifest': str(output / 'canonical_manifest.csv'),
             'training_seed': 42, 'epochs': 100, 'head_batch': 32}
        validate_outex(p, rows)
        if partition is not None and p != partition:
            raise ValueError('head partition disagreement')
        partition = p
        for path in (quality_path, online_path, manifest_path, prediction, Path(j['config'])):
            sources[str(path)] = digest(path)
    for r in canonical:
        if digest(ROOT / r['path']) != r['sha256']:
            raise ValueError('image drift')
    checkpoint = Path(hf_hub_download('timm/densenet121.tv_in1k', 'model.safetensors', local_files_only=True))
    if digest(checkpoint) != CHECKPOINT_SHA:
        raise ValueError('checkpoint drift')
    for name in ('src/hytex_reference.py', 'src/hytex_online_adapter.py', 'src/hytex_fixed_training.py',
                 'src/neshov_online_adapter.py', 'src/neshov_beit_reference.py',
                 'scripts/run_hytex_external_condition.py', 'scripts/run_neshov_external_condition.py',
                 'scripts/consolidate_overnight_online_panel.py', 'scripts/prepare_neshov_fmd_external.py',
                 'scripts/prepare_hytex_fmd_queue.py', 'scripts/prepare_hytex_outex_queue.py',
                 'scripts/run_authorized_remediation_queue.py',
                 'docs/fsc_tex/PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md',
                 'docs/fsc_tex/PROTOCOLO_HYTEX_EXTENSION_OUTEX_2026-11-02.md'):
        sources[str(ROOT / name)] = digest(ROOT / name)
    sources[str(checkpoint)] = CHECKPOINT_SHA
    output.mkdir(parents=True, exist_ok=False)
    normalized = output / 'canonical_manifest.csv'
    with normalized.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(canonical[0]))
        writer.writeheader()
        writer.writerows(canonical)
    sources[str(normalized)] = digest(normalized)
    frozen = output / 'preflight.json'
    frozen.write_text(json.dumps({'status': 'HYTEX_OUTEX_ADAPTATION_FROZEN_NOT_EXECUTED',
        'conditions': [partition], 'unique_conditions': 1, 'planned_online_calls': 680,
        'unique_images_hashed': 1360, 'source_sha256': sources,
        'method': 'HyTexNet adapted; local fixed configuration'}, indent=2) + '\n')
    name = 'HyTex_Outex13Official1360_s42_f0'
    job = output / 'jobs' / name
    commands = []
    for stage, timeout in [('extract',7200), ('train',1800), ('online',14400), ('audit',300)]:
        commands.append({'argv': [sys.executable, str(ROOT / 'scripts/run_hytex_external_condition.py'),
            '--manifest', str(frozen), '--number', '0', '--stage', stage, '--job', str(job)],
            'timeout_seconds': timeout,
            'success': {'path': str(job / stage / 'status.json'), 'fields': {'status': stage + '_complete'}}})
    manifest = {'schema': 1, 'no_auto_retry': True, 'python_version': sys.version,
        'source_sha256': {**sources, str(frozen): digest(frozen)}, 'gpu_lock': 'results/analysis/gpu.lock',
        'tasks': [{'id': name, 'lane': 'gpu', 'depends_on': [], 'observe': False,
            'exclusive_outputs': [str(job / s) for s in ('extract','train','online','audit')], 'commands': commands}],
        'packages': {p: importlib.metadata.version(p) for p in
            ('numpy','torch','torchvision','timm','Pillow','huggingface-hub','safetensors')},
        'scope': 'Outex official: HyTexNet adapted; local fixed configuration'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'tasks': 1, 'manifest_sha256': digest(output / 'manifest.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
