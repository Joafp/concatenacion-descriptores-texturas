"""One fresh, explicitly authorized recovery per infrastructure failure.

Never modify or resume old jobs. Does not include the Neshov scientific failure.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

from consolidate_overnight_online_panel import ROOT, read, digest
from prepare_hytex_fmd_queue import CHECKPOINT_SHA
from run_authorized_remediation_queue import verify_sources

AUTH = 'docs/fsc_tex/RECUPERACION_AUTORIZADA_Y_FIDELIDAD_PAPERS_2026-11-02.md'
CASES = (
    ('hytex_outex_external_queue_20261102_v1', 'HyTex_Outex13Official1360_s42_f0',
     'extract', "KeyError: 'checkpoint_sha256'", 'run_hytex_external_condition.py'),
    ('cellnn_fmd_external_queue_20261102_v1', 'CellNN_FMD_s42_f0',
     'train', 'TypeError: Object of type float32 is not JSON serializable',
     'run_cellnn_external_condition_v2.py'),
)


def recover_payload(frozen, task_id, status, expected_error, checkpoint_sha):
    if status.get('status') != 'requires_review' or status.get('error') != expected_error:
        raise ValueError('only exact authorized infrastructure failure accepted')
    payload = copy.deepcopy(frozen)
    if task_id.startswith('HyTex_'):
        if 'checkpoint_sha256' in payload or checkpoint_sha != CHECKPOINT_SHA:
            raise ValueError('expected missing checkpoint field and exact sealed hash')
        selected = payload['conditions']
        if len(selected) != 1 or selected[0]['dataset'] != 'Outex13Official1360':
            raise ValueError('exact one Outex condition required')
        payload['checkpoint_sha256'] = checkpoint_sha
        expected_calls = 680
    else:
        selected = [p for p in payload['conditions'] if
                    (p['dataset'], p['seed'], p['outer_fold']) == ('FMD', 42, 0)]
        if len(selected) != 1:
            raise ValueError('exact failed CellNN condition required')
        expected_calls = 200
    if sum(len(p['external_indices']) for p in selected) != expected_calls:
        raise ValueError('external coverage mismatch')
    payload.update(conditions=selected, unique_conditions=1,
                   planned_online_calls=expected_calls,
                   status='EXPLICITLY_AUTHORIZED_FRESH_INFRA_RECOVERY_NOT_EXECUTED',
                   prior_failed_task=task_id, paper_scores_reproduced=False)
    return payload


def prepare(output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    tasks, sources, packages = [], {}, None
    python_version = None
    prepared = []
    for directory, task_id, failed_stage, expected_error, runner in CASES:
        previous = ROOT / 'results/analysis' / directory
        old = read(previous / 'manifest.json')
        worker = read(previous / 'gpu.json')
        if worker['status'] != 'all_tasks_terminal' or worker.get('current_task') is not None:
            raise ValueError('old worker must be terminal')
        verify_sources(old)
        if packages is not None and any(packages.get(k, v) != v for k, v in old['packages'].items()):
            raise ValueError('runtime disagreement')
        packages = {**(packages or {}), **old['packages']}
        python_version = old['python_version']
        status_path = previous / 'jobs' / task_id / failed_stage / 'status.json'
        frozen = read(previous / 'preflight.json')
        payload = recover_payload(frozen, task_id, read(status_path), expected_error, CHECKPOINT_SHA)
        pins = {**old['source_sha256'], str(status_path): digest(status_path),
                str(previous / 'manifest.json'): digest(previous / 'manifest.json'),
                str(previous / 'preflight.json'): digest(previous / 'preflight.json')}
        for rel in (AUTH, 'scripts/prepare_authorized_paper_infra_recovery.py',
                    'scripts/' + runner):
            pins[str(ROOT / rel)] = digest(ROOT / rel)
        if task_id.startswith('HyTex_') and CHECKPOINT_SHA not in pins.values():
            raise ValueError('checkpoint not sealed in old sources')
        payload['source_sha256'] = pins
        payload['recovery_authority'] = str(ROOT / AUTH)
        prepared.append((task_id, runner, payload))
        sources.update(pins)
    output.mkdir(parents=True, exist_ok=False)
    for task_id, runner, payload in prepared:
        frozen_path = output / (task_id + '_preflight.json')
        frozen_path.write_text(json.dumps(payload, indent=2) + '\n')
        sources[str(frozen_path)] = digest(frozen_path)
        job = output / 'jobs' / task_id
        commands = []
        for stage, timeout in [('extract', 7200), ('train', 3600), ('online', 14400), ('audit', 300)]:
            commands.append({'argv': [sys.executable, str(ROOT / 'scripts' / runner),
                '--manifest', str(frozen_path), '--number', '0', '--stage', stage,
                '--job', str(job)], 'timeout_seconds': timeout,
                'success': {'path': str(job / stage / 'status.json'),
                            'fields': {'status': stage + '_complete'}}})
        tasks.append({'id': task_id, 'lane': 'gpu', 'depends_on': [], 'observe': False,
            'exclusive_outputs': [str(job / s) for s in ('extract', 'train', 'online', 'audit')],
            'commands': commands})
    manifest = {'schema': 1, 'no_auto_retry': True, 'python_version': python_version,
        'packages': packages, 'source_sha256': sources, 'gpu_lock': 'results/analysis/gpu.lock',
        'tasks': tasks, 'scope': 'two explicit fresh infrastructure recoveries, not faithful paper-score reproduction'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'tasks': len(tasks), 'planned_online_calls': 880,
                      'manifest_sha256': digest(output / 'manifest.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
