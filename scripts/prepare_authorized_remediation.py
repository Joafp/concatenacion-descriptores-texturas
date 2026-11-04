"""Prepare the explicitly approved November 1 amendment; never execute it."""
import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'docs/fsc_tex/ENMIENDA_DESBLOQUEO_PANEL_2026-11-01.md'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x') as f:
        f.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def amended_config(original, embedding_root):
    value = copy.deepcopy(original)
    value['provenance']['arguments']['embedding_root'] = str(embedding_root)
    value['representation_amendment'] = {
        'protocol': str(PROTOCOL), 'only_regenerated_block': 'deit_s',
        'controls': 'archived membership unchanged; adaptive OOF and all heads refitted train-only',
        'historical_panel_condition_metrics_are_not_new_results': True}
    return value


def prepare(folder):
    original_path = ROOT / 'results/analysis/overnight_f1_latency_20261028/manifest.json'
    original = json.loads(original_path.read_text())
    jobs = [j for j in original['jobs'] if j['dataset'] in
            {'KTHTIPS2b', 'Outex13Official1360', 'SoilOriginal'}]
    if len(jobs) != 40:
        raise ValueError('expected exactly forty unique pending conditions')
    folder.mkdir(parents=True, exist_ok=False)
    for name in ('configs', 'jobs', 'bindings', 'tasks', 'embeddings'):
        (folder / name).mkdir()
    sources = {str(ROOT / p): sha for p, sha in original['source_sha256'].items()}
    for path in (original_path, PROTOCOL,
                 ROOT / 'results/analysis/blocker_resolution_20261101/kth_reconciliation.json',
                 ROOT / 'src/reextract_confirmatory_embeddings.py',
                 ROOT / 'src/01_extract_features.py',
                 ROOT / 'src/local_deit_reconstruction.py',
                 ROOT / 'src/run_confirmatory_nested.py',
                 ROOT / 'src/resmlp_classifier.py',
                 ROOT / 'src/run_rescue_nested_selection.py',
                 ROOT / 'src/run_topk_individual_control.py',
                 ROOT / 'src/rgb_ngram_descriptor.py',
                 ROOT / 'src/ensemble_scoring.py',
                 ROOT / 'src/frozen_ensemble_route.py',
                 ROOT / 'scripts/benchmark_cascade_multidataset.py',
                 ROOT / 'src/extract_sota_2024.py',
                 ROOT / 'scripts/diagnose_deit_dataset_binding.py',
                 ROOT / 'scripts/diagnose_kth_deit_binding.py',
                 ROOT / 'scripts/observe_benchmark_process.py',
                 ROOT / 'scripts/run_authorized_remediation_queue.py', Path(__file__)):
        sources[str(path.resolve())] = digest(path)
    reconciled = json.loads((ROOT / 'results/analysis/blocker_resolution_20261101/kth_reconciliation.json').read_text())
    if not reconciled.get('quality_eligible_for_new_manifest') or reconciled.get('historical_equivalence_claimed'):
        raise ValueError('KTH reconciliation does not permit the new quality panel')
    for name, sha in reconciled['files'].items():
        path = ROOT / name
        if digest(path) != sha:
            raise ValueError('KTH reconciled input drift: ' + name)
        sources[str(path)] = sha
    kth_manifest = ROOT / reconciled['manifest_path']
    if digest(kth_manifest) != reconciled['manifest_csv_sha256']:
        raise ValueError('KTH manifest drift')
    sources[str(kth_manifest)] = digest(kth_manifest)
    tasks = []
    py = str(ROOT / '.venv-confirmatory/bin/python')
    reconstruction = ROOT / 'results/analysis/deit_seed42_diagnostic_20261028/diagnostic.json'
    sources[str(reconstruction)] = digest(reconstruction)
    sources[str(reconstruction.with_name('pooler_state.pt'))] = digest(reconstruction.with_name('pooler_state.pt'))

    def command(script, flags, timeout, success=None):
        result = {'argv': [py, str(ROOT / script)] + list(map(str, flags)),
                  'timeout_seconds': timeout}
        if success:
            result['success'] = success
        return result

    def success(path, **fields):
        return {'path': str(path), 'fields': fields}

    # No files from the previous representation are overwritten. Non-DeiT
    # features are read-only references whose source hashes are guarded.
    for ds, size in [('Outex13Official1360', 1360), ('SoilOriginal', 1140)]:
        old = ROOT / 'embeddings_extensions' / ds
        new = folder / 'embeddings' / ds
        new.mkdir()
        for p in sorted(old.iterdir()):
            if p.is_file() and not p.name.startswith('deit_s'):
                (new / p.name).symlink_to(p.resolve())
                sources[str(p.resolve())] = digest(p)
        cfg = json.loads(Path(next(j['config'] for j in jobs if j['dataset'] == ds)).read_text())
        manifest = ROOT / cfg['provenance']['arguments']['manifest_root'] / 'sample_manifests' / (ds + '.csv')
        sources[str(manifest)] = digest(manifest)
        tasks.append({'id': 'extract_' + ds, 'lane': 'gpu', 'depends_on': [],
            'exclusive_outputs': [str(new / name) for name in ('deit_s.npy', 'deit_s_labels.npy', 'deit_s_metadata.json', 'deit_s_classes.json')],
            'commands': [command('src/reextract_confirmatory_embeddings.py',
                ['--manifest', manifest, '--extractor', 'deit_s', '--output', new,
                 '--batch-size', 16, '--seed', 42], 1800,
                success(new / 'deit_s_metadata.json', extractor='deit_s', rows=size, seed=42))]})
    updated = []
    for j in jobs:
        cfg_path = Path(j['config'])
        if digest(cfg_path) != j['config_sha256']:
            raise ValueError('original config drift')
        cfg = json.loads(cfg_path.read_text())
        if j['dataset'] != 'KTHTIPS2b':
            cfg = amended_config(cfg, folder / 'embeddings')
        new_config = folder / 'configs' / cfg_path.name
        write(new_config, cfg)
        sources[str(new_config)] = digest(new_config)
        # Bind frozen recipe sources, including the Top-4 sweep, to this queue.
        prefix = ROOT / 'results/exploratory'
        if j['classifier'] == 'resmlp':
            prefix /= 'resmlp'
        for family in ('diversity', 'lottery'):
            for p in (prefix / 'k4' / family).glob('*/*.json'):
                v = json.loads(p.read_text())
                if (v.get('dataset'), v.get('classifier'), v.get('seed'), v.get('outer_fold')) == (j['dataset'], j['classifier'], j['seed'], j['outer_fold']):
                    sources[str(p)] = digest(p)
        for p in (prefix / 'k_sweep').glob('*/k_sweep.csv'):
            sources[str(p)] = digest(p)
        out = folder / 'jobs' / j['id']
        out.mkdir()
        updated.append(dict(j, config=str(new_config), config_sha256=digest(new_config),
            job_dir=str(out), quality_run=str(out / 'quality'), quality_audit=str(out / 'quality_audit'),
            online_run=str(out / 'online'), online_audit=str(out / 'online_audit'),
            quality_hold=None, online_hold='requires_new_binding', amendment=str(PROTOCOL)))
    for ds in ('KTHTIPS2b', 'Outex13Official1360', 'SoilOriginal'):
        j = next(j for j in updated if j['dataset'] == ds)
        script = 'scripts/diagnose_kth_deit_binding.py' if ds == 'KTHTIPS2b' else 'scripts/diagnose_deit_dataset_binding.py'
        out = folder / 'bindings' / ds
        tasks.append({'id': 'binding_' + ds, 'lane': 'gpu',
            'depends_on': [] if ds == 'KTHTIPS2b' else ['extract_' + ds],
            'exclusive_outputs': [str(out)], 'commands': [command(script,
                ['--config', j['config'], '--reconstruction', reconstruction, '--protocol', PROTOCOL,
                 '--output', out, '--execute'], 600,
                success(out / 'diagnostic.json', status='diagnostic_complete', all_rows_pass=True))]})
    # Additional authorized DTD observation, never substitutes the original.
    old = next(j for j in original['jobs'] if j['id'] == 'DTD_svm_s42_f6')
    old_binding = ROOT / 'results/analysis/overnight_online_resume_20261029_v4/bindings/DTD/diagnostic.json'
    for p in [old_binding, old_binding.with_name('pooler_state.pt')]:
        sources[str(p)] = digest(p)
    for p in Path(old['quality_run']).iterdir():
        if p.is_file():
            sources[str(p)] = digest(p)
    retry = folder / 'jobs/DTD_svm_s42_f6_additional'
    retry.mkdir()
    tasks.append({'id': 'DTD_svm_s42_f6_additional', 'lane': 'gpu', 'depends_on': [],
        'observe': True, 'exclusive_outputs': [str(retry / 'online'), str(retry / 'online_audit')],
        'commands': [command('scripts/benchmark_local_single_image.py',
            ['--run', old['quality_run'], '--deit-reconstruction', old_binding, '--protocol', PROTOCOL,
             '--output', retry / 'online', '--repeats', 1], 14400,
            success(retry / 'online/status.json', status='batch1_online_f1_and_timing_complete')),
            command('scripts/audit_local_batch1_calls.py', ['--online-run', retry / 'online',
                '--quality-run', old['quality_run'], '--output', retry / 'online_audit'], 300,
                success(retry / 'online_audit/audit.json', status='ONLINE_CALL_RECORDS_REAGGREGATED'))]})
    # KTH quality is independent of binding; its physical stage is not.
    updated.sort(key=lambda j: (j['dataset'] != 'KTHTIPS2b', j['dataset'], j['classifier'], j['seed'], j['outer_fold']))
    for j in updated:
        out, ds = Path(j['job_dir']), j['dataset']
        tasks.append({'id': 'quality_' + j['id'], 'lane': 'cpu',
            'depends_on': [] if ds == 'KTHTIPS2b' else ['binding_' + ds],
            'exclusive_outputs': [j['quality_run'], j['quality_audit']],
            'commands': [command('scripts/run_local_external_panel.py',
                ['--reference-config', j['config'], '--protocol', PROTOCOL, '--classifier', j['classifier'],
                 '--budget-ms', 60, '--threads', 2, '--output', j['quality_run']],
                j['quality_timeout_seconds'], success(out / 'quality/status.json', status='external_quality_complete_timing_pending')),
                command('scripts/audit_local_external_predictions.py', ['--run', j['quality_run'],
                    '--output', j['quality_audit']], 1800,
                    success(out / 'quality_audit/audit.json', status='CACHED_HEAD_PREDICTIONS_REPLAYED'))]})
        tasks.append({'id': 'online_' + j['id'], 'lane': 'gpu',
            'depends_on': ['quality_' + j['id'], 'binding_' + ds],
            'observe': True, 'exclusive_outputs': [j['online_run'], j['online_audit']],
            'commands': [command('scripts/benchmark_local_single_image.py',
                ['--run', j['quality_run'], '--deit-reconstruction', folder / 'bindings' / ds / 'diagnostic.json',
                 '--protocol', PROTOCOL, '--output', j['online_run'], '--repeats', 1], 14400,
                success(out / 'online/status.json', status='batch1_online_f1_and_timing_complete')),
                command('scripts/audit_local_batch1_calls.py', ['--online-run', j['online_run'],
                    '--quality-run', j['quality_run'], '--output', j['online_audit']], 300,
                    success(out / 'online_audit/audit.json', status='ONLINE_CALL_RECORDS_REAGGREGATED'))]})
    write(folder / 'manifest.json', {'schema': 1, 'status': 'prepared_not_executed',
        'original': str(original_path), 'amendment': str(PROTOCOL),
        'authorization': ['Sí, autorizo esa enmienda versionada', 'Sí, repetir el split completo con observabilidad'],
        'no_auto_retry': True, 'source_sha256': sources, 'jobs': updated, 'tasks': tasks,
        'packages': {name: importlib.metadata.version(name) for name in
                     ('numpy', 'torch', 'torchvision', 'scikit-learn', 'scipy', 'transformers', 'timm', 'Pillow', 'pandas', 'joblib', 'scikit-image')},
        'python_version': sys.version,
        'coverage_rule': '40 pending unique conditions; DTD additional run adds zero unique coverage',
        'historical_reserves_preserved': True})
    print(json.dumps({'folder': str(folder), 'tasks': len(tasks), 'conditions': len(updated)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', type=Path, required=True)
    prepare(p.parse_args().folder.resolve())
