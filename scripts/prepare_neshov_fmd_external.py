"""Freeze existing FMD external partitions for Neshov; no models, fits or timing."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from consolidate_overnight_online_panel import ROOT, digest, read, select_jobs


def validate_partition(train, test, rows):
    if any(type(i) is not int for i in train + test):
        raise ValueError("integer indices required")
    if len(set(train)) != len(train) or len(set(test)) != len(test):
        raise ValueError("duplicate indices")
    if set(train) & set(test) or set(train) | set(test) != set(range(len(rows))):
        raise ValueError("partition overlap or incomplete universe")
    if len(train) < 2 or len(train) % 32 == 1:
        raise ValueError("invalid final BatchNorm batch")
    labels = sorted({int(r['label']) for r in rows})
    if set(int(rows[i]['label']) for i in train) != set(labels):
        raise ValueError("missing training classes")
    if {rows[i]['group'] for i in train} & {rows[i]['group'] for i in test}:
        raise ValueError("group leakage")
    return labels


def prepare(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    jobs, sources = select_jobs(ROOT)
    grouped = {}
    image_rows = None
    for job in jobs:
        if job['dataset'] != 'FMD':
            continue
        quality_path = Path(job['quality_run']) / 'status.json'
        online_path = Path(job['online_run']) / 'status.json'
        q, online = read(quality_path), read(online_path)
        if digest(quality_path) != online['quality_status_sha256']:
            raise ValueError("quality lineage drift")
        if q['status'] != 'external_quality_complete_timing_pending':
            raise ValueError("incomplete quality source")
        provenance = q['provenance']
        path = ROOT / provenance['manifest_path']
        if digest(path) != provenance['manifest_sha256']:
            raise ValueError("manifest drift")
        with path.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != 1000 or any(int(r['row_id']) != i for i, r in enumerate(rows)):
            raise ValueError("FMD manifest order or count mismatch")
        if image_rows is not None and rows != image_rows:
            raise ValueError("different manifests between conditions")
        image_rows = rows
        train, test = q['training_indices'], q['external_indices']
        labels = validate_partition(train, test, rows)
        if len(train) != 800 or len(test) != 200 or labels != list(range(10)):
            raise ValueError("unexpected FMD coverage")
        key = (job['seed'], job['outer_fold'])
        partition = {'dataset': 'FMD', 'seed': key[0], 'outer_fold': key[1],
                     'training_indices': train, 'external_indices': test,
                     'labels': labels, 'manifest': str(path),
                     'training_seed': 42, 'epochs': 100, 'head_batch': 32}
        if key in grouped and grouped[key] != partition:
            raise ValueError("SVM/ResMLP external partition disagreement")
        grouped[key] = partition
        for source in (quality_path, online_path, path):
            sources[str(source)] = digest(source)
    if set(grouped) != {(s, f) for s in (42, 123, 2026) for f in range(5)}:
        raise ValueError("15 FMD conditions required")
    for seed in (42, 123, 2026):
        counts = Counter(i for (s, _), p in grouped.items() if s == seed for i in p['external_indices'])
        if counts != Counter(range(1000)):
            raise ValueError("outer test coverage per seed mismatch")
    # Hash each physical file once; no extraction/decoding and no GPU access.
    for row in image_rows:
        path = ROOT / row['path']
        if digest(path) != row['sha256']:
            raise ValueError("image drift: " + str(path))
    pilot_path = ROOT / 'results/exploratory/reference_papers/neshov_fmd_development_20261028/status.json'
    pilot = read(pilot_path)
    checkpoint = Path(pilot['weights']['local_weight_path'])
    if digest(checkpoint) != pilot['checkpoint_sha256']:
        raise ValueError("offline backbone drift")
    for source in (pilot_path, checkpoint, Path(__file__),
                   ROOT / 'src/neshov_online_adapter.py',
                   ROOT / 'src/neshov_beit_reference.py',
                   ROOT / 'src/neshov_reference_training.py',
                   ROOT / 'docs/fsc_tex/PROTOCOLO_NESHOV_PANEL_COMUN_2026-11-02.md'):
        sources[str(source)] = digest(source)
    report = {'status': 'FMD_PARTITIONS_AND_OFFLINE_INPUTS_FROZEN_NOT_EXECUTED',
              'conditions': [grouped[k] for k in sorted(grouped)],
              'unique_conditions': 15, 'planned_online_calls': 3000,
              'unique_images_hashed': 1000, 'source_sha256': sources,
              'checkpoint': str(checkpoint), 'checkpoint_sha256': digest(checkpoint),
              'models_loaded': False, 'training_started': False,
              'external_predictions_produced': False, 'latency_measured': False,
              'executable_runner_ready': False}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('conditions', 'source_sha256')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    prepare(parser.parse_args().output)
