"""Freeze a new prospectively documented FMD batch-1 adaptation queue."""
import argparse
import copy
import json
from pathlib import Path
import sys
from consolidate_overnight_online_panel import ROOT, read, digest
from run_authorized_remediation_queue import verify_sources

OLD = ROOT / 'results/analysis/neshov_fmd_external_queue_20261102_v1'
DIAG = ROOT / 'results/analysis/neshov_batch_parity_diagnostic_20261102_v1'
PROTOCOL = ROOT / 'docs/fsc_tex/PROTOCOLO_NESHOV_BATCH1_CORREGIDO_2026-11-02.md'


def check_diagnostic(diagnostic, original):
    if diagnostic.get('status') != 'diagnostic_complete' or not diagnostic.get('diagnostic_only'):
        raise ValueError('completed diagnostic required')
    if diagnostic.get('external_test_evaluated') or diagnostic.get('f1_or_latency_produced'):
        raise ValueError('diagnostic must exclude test and scores')
    for group, prior in zip(('first', 'last'), original['max_abs_errors']):
        obs = diagnostic['observations'][group]
        if (obs['batch1_repeated']['max_abs'] != 0 or obs['batch8_repeated']['max_abs'] != 0
                or abs(obs['batch8_vs_batch1']['max_abs'] - prior) > 1e-12
                or obs['batch8_vs_batch1']['max_abs'] <= original['tolerance']):
            raise ValueError('unexpected diagnostic observations')


def prepare(output):
    output = Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    old = read(OLD / 'manifest.json'); worker = read(OLD / 'gpu.json')
    if worker['status'] != 'all_tasks_terminal' or worker.get('current_task') is not None:
        raise ValueError('prior worker must be terminal')
    verify_sources(old)
    diagnostic = read(DIAG / 'status.json')
    original_path = OLD / 'jobs/Neshov_FMD_s42_f0/extract/parity.json'
    check_diagnostic(diagnostic, read(original_path))
    if digest(DIAG / 'diagnostic_vectors.npz') != diagnostic['vectors_sha256']:
        raise ValueError('diagnostic vector hash mismatch')
    old_preflight = Path(old['tasks'][0]['commands'][0]['argv'][3])
    if str(old_preflight) not in old['source_sha256'] or digest(old_preflight) != old['source_sha256'][str(old_preflight)]:
        raise ValueError('source preflight mismatch')
    frozen = read(old_preflight)
    ids = {(p['seed'], p['outer_fold']) for p in frozen['conditions']}
    if ids != {(s, f) for s in (42, 123, 2026) for f in range(5)}:
        raise ValueError('expected exact 15 conditions')
    sources = dict(old['source_sha256'])
    for path in (OLD / 'manifest.json', OLD / 'gpu.json', original_path,
                 OLD / 'jobs/Neshov_FMD_s42_f0/extract/status.json', DIAG / 'status.json',
                 DIAG / 'diagnostic_vectors.npz', PROTOCOL,
                 ROOT / 'scripts/run_neshov_batch1_condition.py', Path(__file__).resolve()):
        sources[str(path)] = digest(path)
    payload = copy.deepcopy(frozen)
    payload.update(source_sha256=sources, status='BATCH1_FMD_ADAPTATION_FROZEN_NOT_EXECUTED',
        extraction_regime='batch1 fit and batch1 online', original_batch8_failure_retained=True,
        paper_scores_reproduced=False, protocol=str(PROTOCOL))
    output.mkdir(parents=True, exist_ok=False)
    preflight = output / 'preflight.json'; preflight.write_text(json.dumps(payload, indent=2) + '\n')
    sources[str(preflight)] = digest(preflight)
    tasks = []
    for number, p in enumerate(payload['conditions']):
        name = f'Neshov_FMD_s{p["seed"]}_f{p["outer_fold"]}'
        job = output / 'jobs' / name; commands = []
        for stage, timeout in [('extract',7200),('train',1800),('online',14400),('audit',300)]:
            commands.append({'argv':[sys.executable, str(ROOT/'scripts/run_neshov_batch1_condition.py'),
                '--manifest',str(preflight),'--number',str(number),'--stage',stage,'--job',str(job)],
                'timeout_seconds':timeout,'success':{'path':str(job/stage/'status.json'),
                'fields':{'status':stage+'_complete'}}})
        tasks.append({'id':name,'lane':'gpu','depends_on':[] if not tasks else [tasks[0]['id']],
            'observe':False,'exclusive_outputs':[str(job/s) for s in ('extract','train','online','audit')],
            'commands':commands})
    manifest = {**old,'tasks':tasks,'source_sha256':sources,
        'scope':'Neshov batch1 common-panel adaptation; original batch8 gate failure retained'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'tasks':len(tasks),'planned_calls':3000,'manifest_sha256':digest(output/'manifest.json')}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
