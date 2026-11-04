"""DTD canonical schema and exact inherited group-purged splits; no models."""
import argparse
import csv
import importlib.metadata
import hashlib
import json
from pathlib import Path
import sys

from consolidate_overnight_online_panel import ROOT, select_jobs, read, digest
from prepare_hytex_fmd_queue import CHECKPOINT_SHA


def canonical_array_labels(path):
    import numpy as np
    raw = np.load(path, allow_pickle=False)
    mapping = {}
    values = np.asarray([mapping.setdefault(str(v), len(mapping)) for v in raw], dtype=np.int64)
    sha = hashlib.sha256()
    sha.update(values.dtype.str.encode('ascii'))
    sha.update(json.dumps(values.shape).encode('ascii'))
    sha.update(memoryview(np.ascontiguousarray(values)).cast('B'))
    return values.tolist(), sha.hexdigest()


def inherited_partition(rows, train, test, fold):
    if len(train) != len(set(train)) or len(test) != len(set(test)) or set(train) & set(test):
        raise ValueError('duplicate or overlapping indices')
    key = f'split_{fold + 1}'
    expected_test = {i for i, r in enumerate(rows) if r[key] == 'test'}
    testgroups = {rows[i]['group'] for i in expected_test}
    expected_train = {i for i, r in enumerate(rows) if r[key] in ('train', 'val') and r['group'] not in testgroups}
    if set(test) != expected_test or set(train) != expected_train:
        raise ValueError('official/group-purged partition disagreement')
    if {rows[i]['group'] for i in train} & testgroups:
        raise ValueError('group leakage')
    excluded = sorted(set(range(len(rows))) - set(train) - set(test))
    if any(rows[i]['group'] not in testgroups for i in excluded):
        raise ValueError('unexplained omitted fit row')
    return excluded


def add_mapping(mapping, class_name, label):
    label = int(label)
    if class_name in mapping and mapping[class_name] != label:
        raise ValueError('inconsistent class mapping')
    if any(name != class_name and value == label for name, value in mapping.items()):
        raise ValueError('nonbijective class mapping')
    mapping[class_name] = label


def prepare(output):
    from huggingface_hub import hf_hub_download
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    jobs, sources = select_jobs(ROOT)
    selected, dataset_rows, mapping, covered, ledger = {}, None, {}, set(), {}
    canonical_y = None
    for j in jobs:
        if j['dataset'] != 'DTD':
            continue
        qpath, opath = Path(j['quality_run']) / 'status.json', Path(j['online_run']) / 'status.json'
        q, online = read(qpath), read(opath)
        if digest(qpath) != online['quality_status_sha256'] or q['status'] != 'external_quality_complete_timing_pending':
            raise ValueError('quality lineage mismatch')
        if digest(j['config']) != j['config_sha256']:
            raise ValueError('config drift')
        arguments = read(j['config'])['provenance']['arguments']
        label_path = ROOT / arguments['embedding_root'] / 'DTD/hog_labels.npy'
        values, value_sha = canonical_array_labels(label_path)
        if value_sha != q['provenance']['labels_sha256'] or len(values) != 5640:
            raise ValueError('full canonical label array drift')
        if canonical_y is not None and values != canonical_y:
            raise ValueError('canonical label arrays disagree')
        canonical_y = values
        sources[str(label_path)] = digest(label_path)
        mp = ROOT / q['provenance']['manifest_path']
        if digest(mp) != q['provenance']['manifest_sha256']:
            raise ValueError('source manifest drift')
        with mp.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != 5640 or any(int(r['row_id']) != i for i, r in enumerate(rows)):
            raise ValueError('DTD row identity mismatch')
        if dataset_rows is not None and rows != dataset_rows:
            raise ValueError('head/split manifest disagreement')
        dataset_rows = rows
        pp = Path(j['quality_run']) / 'predictions.csv'
        if digest(pp) != q['output_sha256']['predictions.csv']:
            raise ValueError('source prediction drift')
        observed = set()
        with pp.open(newline='') as stream:
            for record in csv.DictReader(stream):
                index = int(record['row_index'])
                add_mapping(mapping, rows[index]['label'], record['label'])
                observed.add(index)
        if observed != set(q['external_indices']):
            raise ValueError('archived truth coverage mismatch')
        covered.update(observed)
        fold = j['outer_fold']
        excluded = inherited_partition(rows, q['training_indices'], q['external_indices'], fold)
        p = {'dataset': 'DTD', 'seed': j['seed'], 'outer_fold': fold,
             'official_split': fold + 1, 'training_indices': q['training_indices'],
             'external_indices': q['external_indices'], 'excluded_training_indices': excluded,
             'labels': list(range(47)), 'manifest': str(output / 'canonical_manifest.csv'),
             'training_seed': 42, 'epochs': 100, 'head_batch': 32}
        if fold in selected and selected[fold] != p:
            raise ValueError('SVM/ResMLP partition disagreement')
        selected[fold] = p
        ledger[str(fold)] = excluded
        for path in (qpath, opath, mp, pp, Path(j['config'])):
            sources[str(path)] = digest(path)
    official_test_union = {i for i, r in enumerate(dataset_rows)
                           if any(r[f'split_{f + 1}'] == 'test' for f in range(10))}
    if set(selected) != set(range(10)) or covered != official_test_union or set(mapping.values()) != set(range(47)):
        raise ValueError('full official10/class47/image5640 truth coverage required')
    if [mapping[r['label']] for r in dataset_rows] != canonical_y:
        raise ValueError('full manifest/canonical label array disagreement')
    fit_counts = [3753, 3753, 3757, 3754, 3754, 3753, 3752, 3752, 3751, 3749]
    for fold, p in selected.items():
        if p['seed'] != 42 or len(p['training_indices']) != fit_counts[fold] or len(p['external_indices']) != 1880:
            raise ValueError('frozen split coverage mismatch')
        if {mapping[dataset_rows[i]['label']] for i in p['training_indices']} != set(range(47)):
            raise ValueError('training classes missing')
    canonical = []
    for r in dataset_rows:
        path = ROOT / r['source_path']
        if digest(path) != r['source_sha256']:
            raise ValueError('image drift')
        canonical.append({**r, 'original_label': r['label'], 'class_name': r['label'],
                          'label': mapping[r['label']], 'path': str(path), 'sha256': r['source_sha256']})
    checkpoint = Path(hf_hub_download('timm/densenet121.tv_in1k', 'model.safetensors', local_files_only=True))
    if digest(checkpoint) != CHECKPOINT_SHA:
        raise ValueError('checkpoint drift')
    for name in ('src/hytex_reference.py', 'src/hytex_online_adapter.py', 'src/hytex_fixed_training.py',
                 'src/neshov_online_adapter.py', 'src/neshov_beit_reference.py',
                 'scripts/run_hytex_external_condition.py', 'scripts/run_neshov_external_condition.py',
                 'scripts/consolidate_overnight_online_panel.py', 'scripts/prepare_hytex_fmd_queue.py',
                 'scripts/prepare_hytex_dtd_queue.py', 'scripts/run_authorized_remediation_queue.py',
                 'docs/fsc_tex/PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md',
                 'docs/fsc_tex/PROTOCOLO_HYTEX_EXTENSION_DTD_2026-11-02.md'):
        sources[str(ROOT / name)] = digest(ROOT / name)
    sources[str(checkpoint)] = CHECKPOINT_SHA
    output.mkdir(parents=True, exist_ok=False)
    cp = output / 'canonical_manifest.csv'
    with cp.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(canonical[0]))
        writer.writeheader()
        writer.writerows(canonical)
    schema = output / 'schema_and_exclusions.json'
    schema.write_text(json.dumps({'class_mapping': mapping, 'excluded_fit_by_fold': ledger,
                                  'official_test_union_rows': len(covered),
                                  'never_external_test_indices': sorted(set(range(5640)) - covered),
                                  'canonical_labels_verified_rows': len(canonical_y),
                                  'row_order_preserved': True, 'images_modified': False}, indent=2) + '\n')
    sources[str(cp)], sources[str(schema)] = digest(cp), digest(schema)
    conditions = [selected[f] for f in range(10)]
    frozen = output / 'preflight.json'
    frozen.write_text(json.dumps({'dataset': 'DTD', 'conditions': conditions, 'source_sha256': sources,
        'unique_conditions': 10, 'planned_online_calls': 18800, 'unique_images_hashed': 5640,
        'checkpoint_sha256': CHECKPOINT_SHA, 'method': 'HyTexNet adapted; local fixed configuration'}, indent=2) + '\n')
    tasks = []
    for number, p in enumerate(conditions):
        name = f'HyTex_DTD_s42_f{p["outer_fold"]}'
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
        'source_sha256': {**sources, str(frozen): digest(frozen)}, 'gpu_lock': 'results/analysis/gpu.lock',
        'tasks': tasks, 'packages': {p: importlib.metadata.version(p) for p in
                ('numpy', 'torch', 'torchvision', 'timm', 'Pillow', 'huggingface-hub', 'safetensors')},
        'scope': 'DTD: HyTexNet adapted; local fixed configuration'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'tasks': len(tasks), 'manifest_sha256': digest(output / 'manifest.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    prepare(parser.parse_args().output)
