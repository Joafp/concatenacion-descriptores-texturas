"""Build a new immutable dispatch queue; no experiment execution."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

from consolidate_overnight_online_panel import ROOT, read, digest


def prepare(output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    frozen = ROOT / 'results/analysis/neshov_fmd_external_preflight_20261102_v1/manifest.json'
    preflight = read(frozen)
    if preflight['unique_conditions'] != 15 or len(preflight['conditions']) != 15:
        raise ValueError('15 frozen conditions required')
    sources = {str(frozen): digest(frozen)}
    sources.update(preflight['source_sha256'])
    for name in ('scripts/run_neshov_external_condition.py', 'scripts/prepare_neshov_fmd_queue.py',
                 'scripts/run_authorized_remediation_queue.py', 'scripts/consolidate_overnight_online_panel.py'):
        sources[str(ROOT / name)] = digest(ROOT / name)
    tasks = []
    for number, p in enumerate(preflight['conditions']):
        name = f'Neshov_FMD_s{p["seed"]}_f{p["outer_fold"]}'
        job = output / 'jobs' / name
        commands = []
        for stage, timeout in [('extract', 7200), ('train', 1800), ('online', 14400), ('audit', 300)]:
            commands.append({'argv': [sys.executable, str(ROOT / 'scripts/run_neshov_external_condition.py'),
                '--manifest', str(frozen), '--number', str(number), '--stage', stage, '--job', str(job)],
                'timeout_seconds': timeout,
                'success': {'path': str(job / stage / 'status.json'), 'fields': {'status': stage + '_complete'}}})
        tasks.append({'id': name, 'lane': 'gpu', 'depends_on': [] if number == 0 else [tasks[0]['id']],
                      'observe': False, 'exclusive_outputs': [str(job / s) for s in ('extract', 'train', 'online', 'audit')],
                      'commands': commands})
    manifest = {'schema': 1, 'no_auto_retry': True, 'python_version': sys.version,
                'source_sha256': sources, 'gpu_lock': 'results/analysis/gpu.lock',
                'packages': {p: importlib.metadata.version(p) for p in
                             ('numpy', 'torch', 'torchvision', 'timm', 'Pillow', 'huggingface-hub', 'safetensors')},
                'tasks': tasks, 'scope': '15 FMD external adaptations; not original paper protocol'}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'tasks': len(tasks), 'manifest_sha256': digest(output / 'manifest.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    prepare(parser.parse_args().output)
