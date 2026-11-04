"""Measure Neshov batch-shape differences on fixed training images only.

Diagnostic only: no heads, test predictions, F1, latency benchmark or retry.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from run_authorized_remediation_queue import lock, active_benchmarks, verify_sources
from consolidate_overnight_online_panel import digest, read

PREVIOUS = ROOT / 'results/analysis/neshov_fmd_external_queue_20261102_v1'
ERROR = 'ValueError: batch1/batch8 feature parity failed; requires review'


def frozen_path_from_queue(manifest):
    tasks = [t for t in manifest['tasks'] if t['id'] == 'Neshov_FMD_s42_f0']
    if len(tasks) != 1:
        raise ValueError('exact failed task required')
    argv = tasks[0]['commands'][0]['argv']
    path = Path(argv[argv.index('--manifest') + 1])
    if str(path) not in manifest['source_sha256'] or digest(path) != manifest['source_sha256'][str(path)]:
        raise ValueError('preflight must be bound to sealed queue sources')
    return path


def errors(a, b):
    import numpy as np
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('shape mismatch or non-finite values')
    diff = np.abs(a - b)
    return {'max_abs': float(diff.max()), 'mean_abs': float(diff.mean()),
            'l2': float(np.linalg.norm(diff)), 'count_above_1e-4': int((diff > 1e-4).sum())}


def main(output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1',
                      OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    import numpy as np
    import torch
    from PIL import Image
    from neshov_beit_reference import FrozenLayerAggregation, load_offline_backbone, preprocessing

    old_manifest = read(PREVIOUS / 'manifest.json')
    verify_sources(old_manifest)
    old_status = PREVIOUS / 'jobs/Neshov_FMD_s42_f0/extract/status.json'
    old_parity = PREVIOUS / 'jobs/Neshov_FMD_s42_f0/extract/parity.json'
    if read(old_status).get('error') != ERROR:
        raise ValueError('expected original scientific failure not found')
    frozen = read(frozen_path_from_queue(old_manifest))
    p = frozen['conditions'][0]
    if (p['dataset'], p['seed'], p['outer_fold']) != ('FMD', 42, 0):
        raise ValueError('partition mismatch')
    train = p['training_indices']
    test = set(p['external_indices'])
    if len(train) < 16 or set(train) & test:
        raise ValueError('invalid train/test separation')
    groups = {'first': train[:8], 'last': train[-8:]}
    selected = (('first', 0), ('last', 7))
    with Path(p['manifest']).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    torch.set_num_threads(2)
    torch.manual_seed(42)
    torch.use_deterministic_algorithms(True)
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA required to diagnose original hardware regime')
    output.mkdir(parents=True, exist_ok=False)
    report = {'status': 'running', 'diagnostic_only': True, 'head_trained': False,
        'external_test_evaluated': False, 'f1_or_latency_produced': False,
        'previous_failure_sha256': digest(old_status), 'previous_parity_sha256': digest(old_parity),
        'previous_manifest_sha256': digest(PREVIOUS / 'manifest.json'),
        'script_sha256': digest(__file__), 'selected_fit_groups': groups,
        'tolerance_from_original_protocol': 1e-4}

    def write():
        (output / 'status.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    write()
    try:
        with lock(ROOT / 'results/analysis/gpu.lock'):
            if active_benchmarks():
                raise RuntimeError('another benchmark is active')
            model, info = load_offline_backbone()
            if digest(info['local_weight_path']) != frozen['checkpoint_sha256']:
                raise ValueError('checkpoint hash drift')
            model = FrozenLayerAggregation(model).to('cuda', dtype=torch.float32).eval()
            transform = preprocessing()
            sources, tensors = {}, {}
            for group, indices in groups.items():
                images = []
                for index in indices:
                    row = rows[index]
                    image_path = ROOT / row['path']
                    sha = digest(image_path)
                    if sha != row['sha256']:
                        raise ValueError('input hash drift')
                    sources[str(image_path)] = sha
                    with Image.open(image_path) as image:
                        images.append(transform(image.convert('RGB')))
                tensors[group] = torch.stack(images).to('cuda')
            vectors, findings = {}, {}
            with torch.inference_mode():
                for group, pos in selected:
                    batch = tensors[group]
                    for iteration in range(2):
                        vectors[f'{group}_batch_{iteration}'] = model(batch).cpu().numpy()[pos]
                        vectors[f'{group}_single_{iteration}'] = model(batch[pos:pos+1]).cpu().numpy()[0]
                    findings[group] = {
                        'row': groups[group][pos],
                        'batch8_vs_batch1': errors(vectors[f'{group}_batch_0'], vectors[f'{group}_single_0']),
                        'batch8_repeated': errors(vectors[f'{group}_batch_0'], vectors[f'{group}_batch_1']),
                        'batch1_repeated': errors(vectors[f'{group}_single_0'], vectors[f'{group}_single_1']),
                    }
            np.savez_compressed(output / 'diagnostic_vectors.npz', **vectors)
            report.update(status='diagnostic_complete', observations=findings, image_sha256=sources,
                weights=info, weights_sha256=digest(info['local_weight_path']), torch_version=torch.__version__,
                gpu=torch.cuda.get_device_name(0), allow_tf32=torch.backends.cuda.matmul.allow_tf32,
                cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,
                deterministic=torch.are_deterministic_algorithms_enabled(),
                vectors_sha256=digest(output / 'diagnostic_vectors.npz'),
                interpretation='diagnosis only; original parity failure remains requires_review')
            write()
    except Exception as exc:
        report.update(status='requires_review', error=f'{type(exc).__name__}: {exc}',
                      traceback=traceback.format_exc())
        write()
        raise
    print(json.dumps(report['observations'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
