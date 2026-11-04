"""New CUReT queue, frozen local HyTex adaptation, exact archived partitions."""
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
import sys

from consolidate_overnight_online_panel import ROOT, read, digest, select_jobs
from prepare_neshov_fmd_external import validate_partition
from prepare_hytex_fmd_queue import CHECKPOINT_SHA


def validate_curet(partitions, rows):
    if len(partitions) != 2 or {(p['seed'], p['outer_fold']) for p in partitions} != {(42, 0), (42, 1)}:
        raise ValueError('two fixed CUReT directions required')
    if len(rows) != 5612 or any(int(row['row_id']) != i for i, row in enumerate(rows)):
        raise ValueError('CUReT row identity/count mismatch')
    for p in partitions:
        if p.get('curet_direction') != ('a_to_b' if p['outer_fold'] == 0 else 'b_to_a'):
            raise ValueError('CUReT direction identity mismatch')
        labels = validate_partition(p['training_indices'], p['external_indices'], rows)
        if (len(p['training_indices']) != 2806 or len(p['external_indices']) != 2806
                or labels != list(range(61)) or labels != p['labels']):
            raise ValueError('CUReT coverage/classes mismatch')
    if (set(partitions[0]['external_indices']) != set(partitions[1]['training_indices'])
            or set(partitions[1]['external_indices']) != set(partitions[0]['training_indices'])):
        raise ValueError('CUReT direction complement mismatch')


def prepare(output):
    from huggingface_hub import hf_hub_download
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    jobs, sources = select_jobs(ROOT)
    selected, dataset_rows = {}, None
    for j in jobs:
        if j['dataset'] != 'CUReT':
            continue
        quality_path = Path(j['quality_run']) / 'status.json'
        online_path = Path(j['online_run']) / 'status.json'
        q, online = read(quality_path), read(online_path)
        if digest(quality_path) != online['quality_status_sha256'] or q['status'] != 'external_quality_complete_timing_pending':
            raise ValueError('quality status lineage mismatch')
        if digest(j['config']) != j['config_sha256']:
            raise ValueError('local configuration drift')
        manifest_path = ROOT / q['provenance']['manifest_path']
        if digest(manifest_path) != q['provenance']['manifest_sha256']:
            raise ValueError('manifest drift')
        with manifest_path.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        if dataset_rows is not None and rows != dataset_rows:
            raise ValueError('inconsistent manifests across heads/directions')
        dataset_rows = rows
        prediction_path = Path(j['quality_run']) / 'predictions.csv'
        if digest(prediction_path) != q['output_sha256']['predictions.csv']:
            raise ValueError('archived predictions drift')
        observed = set()
        with prediction_path.open(newline='') as stream:
            for record in csv.DictReader(stream):
                index = int(record['row_index'])
                if int(record['label']) != int(rows[index]['label']):
                    raise ValueError('canonical label mapping mismatch')
                observed.add(index)
        if observed != set(q['external_indices']):
            raise ValueError('external truth coverage mismatch')
        args = read(j['config'])['provenance']['arguments']
        p = {'dataset': 'CUReT', 'seed': j['seed'], 'outer_fold': j['outer_fold'],
             'curet_direction': args['curet_direction'],
             'training_indices': q['training_indices'], 'external_indices': q['external_indices'],
             'labels': sorted({int(r['label']) for r in rows}), 'manifest': str(manifest_path),
             'training_seed': 42, 'epochs': 100, 'head_batch': 32}
        key = (p['seed'], p['outer_fold'])
        if key in selected and selected[key] != p:
            raise ValueError('SVM/ResMLP partition disagreement')
        selected[key] = p
        for path in (quality_path, online_path, manifest_path, prediction_path, Path(j['config'])):
            sources[str(path)] = digest(path)
    conditions = [selected[k] for k in sorted(selected)]
    validate_curet(conditions, dataset_rows)
    for row in dataset_rows:
        if digest(ROOT / row['path']) != row['sha256']:
            raise ValueError('image drift')
    checkpoint = Path(hf_hub_download('timm/densenet121.tv_in1k', 'model.safetensors', local_files_only=True))
    if digest(checkpoint) != CHECKPOINT_SHA:
        raise ValueError('checkpoint drift')
    # Pin existing generic runner and inference sources without editing FMD artifacts.
    for name in ('src/hytex_reference.py', 'src/hytex_online_adapter.py', 'src/hytex_fixed_training.py',
                 'src/neshov_online_adapter.py', 'src/neshov_beit_reference.py',
                 'scripts/run_hytex_external_condition.py', 'scripts/run_neshov_external_condition.py',
                 'scripts/consolidate_overnight_online_panel.py', 'scripts/prepare_neshov_fmd_external.py',
                 'scripts/prepare_hytex_fmd_queue.py', 'scripts/prepare_hytex_curet_queue.py',
                 'scripts/run_authorized_remediation_queue.py',
                 'docs/fsc_tex/PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md',
                 'docs/fsc_tex/PROTOCOLO_HYTEX_EXTENSION_CURET_2026-11-02.md'):
        sources[str(ROOT / name)] = digest(ROOT / name)
    sources[str(checkpoint)] = CHECKPOINT_SHA
    preflight = {'status': 'HYTEX_CURET_ADAPTATION_FROZEN_NOT_EXECUTED',
                 'dataset': 'CUReT', 'conditions': conditions, 'source_sha256': sources,
                 'unique_conditions': 2, 'planned_online_calls': 5612,
                 'unique_images_hashed': len(dataset_rows), 'checkpoint_sha256': CHECKPOINT_SHA,
                 'method': 'HyTexNet adapted; local fixed configuration'}
    output.mkdir(parents=True, exist_ok=False)
    frozen = output / 'preflight.json'
    frozen.write_text(json.dumps(preflight, indent=2) + '\n')
    tasks = []
    for number, p in enumerate(conditions):
        name = f'HyTex_CUReT_s{p["seed"]}_f{p["outer_fold"]}'
        job = output / 'jobs' / name
        commands = []
        for stage, timeout in [('extract', 7200), ('train', 1800), ('online', 14400), ('audit', 300)]:
            commands.append({'argv': [sys.executable, str(ROOT / 'scripts/run_hytex_external_condition.py'),
                '--manifest', str(frozen), '--number', str(number), '--stage', stage, '--job', str(job)],
                'timeout_seconds': timeout,
                'success': {'path': str(job / stage / 'status.json'), 'fields': {'status': stage + '_complete'}}})
        tasks.append({'id': name, 'lane': 'gpu', 'depends_on': [] if not tasks else [tasks[0]['id']],
                      'observe': False, 'exclusive_outputs': [str(job / s) for s in ('extract', 'train', 'online', 'audit')],
                      'commands': commands})
    manifest = {'schema': 1, 'no_auto_retry': True, 'python_version': sys.version,
                'source_sha256': {**sources, str(frozen): digest(frozen)},
                'gpu_lock': 'results/analysis/gpu.lock', 'tasks': tasks,
                'packages': {p: importlib.metadata.version(p) for p in
                             ('numpy', 'torch', 'torchvision', 'timm', 'Pillow', 'huggingface-hub', 'safetensors')},
                'scope': 'CUReT: ' + preflight['method']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'tasks': len(tasks), 'manifest_sha256': digest(output / 'manifest.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    prepare(parser.parse_args().output)
