import copy
import importlib.util
from pathlib import Path


def module():
    path = Path(__file__).resolve().parents[1] / 'scripts/prepare_authorized_remediation.py'
    spec = importlib.util.spec_from_file_location('prepare_remediation_test', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_amendment_changes_only_representation_root_not_scientific_arguments():
    original = {'provenance': {'arguments': {'dataset': 'SoilOriginal', 'seed': 123,
        'fold': 3, 'embedding_root': 'embeddings_extensions', 'library': 22,
        'ngram_count_cache': 'same', 'budgets_ms': [15, 30, 60, 120]}},
        'panel_condition': {'historical_f1': .9}}
    before = copy.deepcopy(original)
    changed = module().amended_config(original, Path('/new'))
    assert original == before
    args = changed['provenance']['arguments']
    assert args.pop('embedding_root') == '/new'
    old = before['provenance']['arguments']
    old.pop('embedding_root')
    assert args == old
    assert changed['representation_amendment']['historical_panel_condition_metrics_are_not_new_results']


def test_manifest_write_exclusive(tmp_path):
    import pytest
    path = tmp_path / 'manifest.json'
    module().write(path, {'no_auto_retry': True})
    with pytest.raises(FileExistsError):
        module().write(path, {'no_auto_retry': False})
    assert 'true' in path.read_text()
