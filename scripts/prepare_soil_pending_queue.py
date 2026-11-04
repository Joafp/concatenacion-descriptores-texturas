"""Prepare thirty never-started Soil amendment conditions after passed new binding."""
import argparse
import copy
import json
from pathlib import Path

from prepare_authorized_remediation import ROOT, digest, write


def relocate(value, before, after):
    if isinstance(value, str):
        return after + value[len(before):] if value.startswith(before + '/') else value
    if isinstance(value, list):
        return [relocate(v, before, after) for v in value]
    if isinstance(value, dict):
        return {k: relocate(v, before, after) for k, v in value.items()}
    return value


def prepare(folder):
    from local_deit_reconstruction import verified_state_path
    from run_authorized_remediation_queue import verify_sources

    base = ROOT / 'results/analysis/blocker_resolution_20261101'
    old = base / 'queue_v1'
    original = json.loads((old / 'manifest.json').read_text())
    inputs = base / 'soil_format_resume_v1'
    binding = inputs / 'binding_SoilOriginal/diagnostic.json'
    state, evidence = verified_state_path(binding)
    if evidence.get('dataset') != 'SoilOriginal' or evidence.get('row_indices') != [0, 1139]:
        raise ValueError('wrong dataset binding')
    cache = inputs / 'embeddings/SoilOriginal'
    if digest(cache / 'deit_s.npy') != evidence['embedding_sha256']:
        raise ValueError('new DeiT archive drift')
    jobs = [j for j in original['jobs'] if j['dataset'] == 'SoilOriginal']
    if len(jobs) != 30 or len({j['id'] for j in jobs}) != 30:
        raise ValueError('expected exactly thirty unique Soil conditions')
    for job in jobs:
        if Path(job['quality_run']).exists() or Path(job['online_run']).exists():
            raise ValueError('condition already dispatched in the amendment; no automatic retry')
    sources = dict(original['source_sha256'])
    for path in [old / 'manifest.json', inputs / 'manifest.json', binding, state, Path(__file__)]:
        sources[str(path.resolve())] = digest(path)
    for path in cache.iterdir():
        if path.is_file():
            sources[str(path)] = digest(path)
    folder.mkdir(parents=True, exist_ok=False)
    for name in ('configs', 'jobs', 'tasks'):
        (folder / name).mkdir()
    updated = []
    for job in jobs:
        value = relocate(copy.deepcopy(job), str(old), str(folder))
        cfg = json.loads(Path(job['config']).read_text())
        cfg['provenance']['arguments']['embedding_root'] = str(inputs / 'embeddings')
        cfg_path = Path(value['config'])
        write(cfg_path, cfg)
        value.update(config_sha256=digest(cfg_path), quality_hold=None, online_hold=None)
        sources[str(cfg_path)] = digest(cfg_path)
        Path(value['job_dir']).mkdir()
        updated.append(value)
    ids = {j['id'] for j in jobs}
    tasks = []
    for task in original['tasks']:
        if not any(task['id'] == prefix + name for name in ids for prefix in ('quality_', 'online_')):
            continue
        value = relocate(copy.deepcopy(task), str(old), str(folder))
        value['depends_on'] = [d for d in value['depends_on'] if d.startswith('quality_')]
        if value['lane'] == 'gpu':
            argv = value['commands'][0]['argv']
            argv[argv.index('--deit-reconstruction') + 1] = str(binding)
        tasks.append(value)
    assert len(tasks) == 60
    manifest = {k: original[k] for k in ('schema', 'packages', 'python_version', 'no_auto_retry', 'amendment', 'authorization')}
    manifest.update(source_sha256=sources, jobs=updated, tasks=tasks,
        scope='thirty previously blocked and never-started Soil conditions, authorized new representation; not KTH retry',
        binding=str(binding), prior_queue=str(old / 'manifest.json'),
        coverage_rule='count only complete audited online conditions, full means after all 15 per classifier',
        historical_reserves_preserved=True)
    verify_sources(manifest)
    write(folder / 'manifest.json', manifest)
    print(json.dumps({'conditions': len(updated), 'tasks': len(tasks),
                      'manifest_sha256': digest(folder / 'manifest.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    prepare(parser.parse_args().folder.resolve())
