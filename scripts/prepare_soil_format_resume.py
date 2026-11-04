"""Prepare only the explicitly approved Soil pre-model schema-failure resubmission."""
import argparse
import copy
import json
from pathlib import Path
import sys

from prepare_authorized_remediation import ROOT, digest, write


def prepare(folder):
    prior = ROOT / 'results/analysis/blocker_resolution_20261101/queue_v1/manifest.json'
    manifest = json.loads(prior.read_text())
    failed = prior.parent / 'tasks/extract_SoilOriginal/state.json'
    if json.loads(failed.read_text())['status'] != 'requires_review':
        raise ValueError('expected preserved failed preflight')
    adapter = ROOT / 'results/analysis/blocker_resolution_20261101/soil_schema_adapter_v1/receipt.json'
    receipt = json.loads(adapter.read_text())
    if receipt['status'] != 'SOIL_EXTRACTION_SCHEMA_VALIDATED_NO_MODEL_EXECUTED' or digest(receipt['adapted_manifest']) != receipt['adapted_manifest_sha256']:
        raise ValueError('schema adapter receipt drift')
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'embeddings/SoilOriginal').mkdir(parents=True)
    (folder / 'tasks').mkdir()
    (folder / 'configs').mkdir()
    sources = dict(manifest['source_sha256'])
    for path in (prior, failed, adapter, Path(receipt['adapted_manifest']), Path(__file__),
                 ROOT / 'scripts/prepare_soil_extraction_manifest.py'):
        sources[str(path.resolve())] = digest(path)
    new = folder / 'embeddings/SoilOriginal'
    for path in (ROOT / 'embeddings_extensions/SoilOriginal').iterdir():
        if path.is_file() and not path.name.startswith('deit_s'):
            (new / path.name).symlink_to(path.resolve())
    source_job = next(j for j in manifest['jobs'] if j['id'] == 'SoilOriginal_svm_s42_f0')
    cfg = copy.deepcopy(json.loads(Path(source_job['config']).read_text()))
    cfg['provenance']['arguments']['embedding_root'] = str(folder / 'embeddings')
    cfg_path = folder / 'configs/SoilOriginal_svm_s42_f0.json'
    write(cfg_path, cfg)
    sources[str(cfg_path)] = digest(cfg_path)
    extraction = copy.deepcopy(next(t for t in manifest['tasks'] if t['id'] == 'extract_SoilOriginal'))
    extraction['exclusive_outputs'] = [str(new / Path(p).name) for p in extraction['exclusive_outputs']]
    cmd = extraction['commands'][0]
    cmd['argv'][cmd['argv'].index('--manifest') + 1] = receipt['adapted_manifest']
    cmd['argv'][cmd['argv'].index('--output') + 1] = str(new)
    cmd['success']['path'] = str(new / 'deit_s_metadata.json')
    binding = copy.deepcopy(next(t for t in manifest['tasks'] if t['id'] == 'binding_SoilOriginal'))
    out = folder / 'binding_SoilOriginal'
    binding['exclusive_outputs'] = [str(out)]
    cmd = binding['commands'][0]
    cmd['argv'][cmd['argv'].index('--config') + 1] = str(cfg_path)
    cmd['argv'][cmd['argv'].index('--output') + 1] = str(out)
    cmd['success']['path'] = str(out / 'diagnostic.json')
    write(folder / 'manifest.json', {'schema': 1, 'source_sha256': sources,
        'packages': manifest['packages'], 'python_version': sys.version,
        'tasks': [extraction, binding], 'jobs': [], 'no_auto_retry': True,
        'authorization': 'Sí, despachar Soil con el formato corregido',
        'scope': 'new Soil extraction and binding only; quality/online need subsequent guarded queue after passing binding',
        'prior_failure': str(failed), 'original_queue': str(prior),
        'coverage_rule': 'preparation only, adds zero completed online conditions'})
    print(str(folder / 'manifest.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    prepare(parser.parse_args().folder.resolve())
