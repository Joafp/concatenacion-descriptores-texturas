"""Prepare eight explicitly authorized KTH online redispatches; no fitting or execution."""
import argparse
import copy
import json
from pathlib import Path

from prepare_authorized_remediation import ROOT, digest, write


def online_task(task, old_job, new_job):
    """Change output paths and alias-aware executable, preserving frozen inputs."""
    if task['lane'] != 'gpu' or len(task['commands']) != 2:
        raise ValueError('expected benchmark plus audit')
    result = copy.deepcopy(task)
    result['depends_on'] = []  # existing quality/binding are independently hash-guarded
    result['exclusive_outputs'] = [str(new_job / 'online'), str(new_job / 'online_audit')]
    for cmd in result['commands']:
        cmd['argv'] = [str(new_job) + v[len(str(old_job)):] if v.startswith(str(old_job) + '/') else v
                       for v in cmd['argv']]
        if 'success' in cmd:
            value = cmd['success']['path']
            if not value.startswith(str(old_job) + '/'):
                raise ValueError('unexpected success path')
            cmd['success']['path'] = str(new_job) + value[len(str(old_job)):]
    argv = result['commands'][0]['argv']
    if Path(argv[1]).name != 'benchmark_local_single_image.py':
        raise ValueError('unexpected benchmark')
    argv[1] = str(ROOT / 'scripts/benchmark_local_single_image_alias_v1.py')
    # --run and --quality-run must remain the original completed quality paths.
    for cmd in result['commands']:
        for flag in ('--run', '--quality-run'):
            if flag in cmd['argv']:
                cmd['argv'][cmd['argv'].index(flag) + 1] = str(old_job / 'quality')
    return result


def prepare(folder):
    from local_deit_reconstruction import verified_state_path
    from overnight_multidataset_online import quality_ready
    from run_authorized_remediation_queue import verify_sources

    original_path = ROOT / 'results/analysis/blocker_resolution_20261101/queue_v1/manifest.json'
    original = json.loads(original_path.read_text())
    jobs = [j for j in original['jobs'] if j['dataset'] == 'KTHTIPS2b']
    if len(jobs) != 8:
        raise ValueError('eight KTH conditions required')
    binding = original_path.parent / 'bindings/KTHTIPS2b/diagnostic.json'
    pooler, evidence = verified_state_path(binding)
    if evidence.get('dataset') != 'KTHTIPS2b' or evidence.get('row_indices') != [0, 4751]:
        raise ValueError('wrong KTH binding')
    sources = dict(original['source_sha256'])
    for path in (original_path, binding, pooler, Path(__file__),
                 ROOT / 'scripts/benchmark_local_single_image_alias_v1.py',
                 ROOT / 'docs/fsc_tex/AUTORIZACION_REDESPACHO_KTH_2026-11-01.md'):
        sources[str(path.resolve())] = digest(path)
    for job in jobs:
        if not quality_ready(job):
            raise ValueError('completed quality/replay required')
        previous = original_path.parent / 'tasks' / ('online_' + job['id']) / 'state.json'
        if json.loads(previous.read_text())['status'] != 'requires_review':
            raise ValueError('expected preserved pre-model route failure')
        if (Path(job['online_run']) / 'online_calls.csv').exists():
            raise ValueError('previous timing calls exist; different adjudication required')
        sources[str(previous)] = digest(previous)
        for path in Path(job['quality_run']).iterdir():
            if path.is_file():
                sources[str(path)] = digest(path)
        audit = Path(job['quality_audit']) / 'audit.json'
        sources[str(audit)] = digest(audit)
    verify_sources(dict(original, source_sha256=sources))
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'jobs').mkdir()
    (folder / 'tasks').mkdir()
    tasks, updated = [], []
    for job in jobs:
        directory = folder / 'jobs' / job['id']
        directory.mkdir()
        task = next(t for t in original['tasks'] if t['id'] == 'online_' + job['id'])
        tasks.append(online_task(task, Path(job['job_dir']), directory))
        updated.append(dict(job, job_dir=str(directory), online_run=str(directory / 'online'),
                            online_audit=str(directory / 'online_audit'), online_hold=None))
    manifest = {k: original[k] for k in ('schema', 'packages', 'python_version', 'no_auto_retry', 'amendment')}
    manifest.update(source_sha256=sources, jobs=updated, tasks=tasks,
        authorization='Sí, despachar las ocho mediciones con la ruta corregida',
        scope='eight KTH online conditions only; unchanged frozen quality/selection; original failures preserved',
        prior_queue=str(original_path), historical_reserves_preserved=True)
    write(folder / 'manifest.json', manifest)
    print(json.dumps({'conditions': len(updated), 'tasks': len(tasks),
                      'manifest_sha256': digest(folder / 'manifest.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    prepare(parser.parse_args().folder.resolve())
