import importlib.util
from pathlib import Path


def module():
    root = Path(__file__).resolve().parents[1]
    import sys
    sys.path.insert(0, str(root / 'scripts'))
    spec = importlib.util.spec_from_file_location('soil_pending_test', root / 'scripts/prepare_soil_pending_queue.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_only_exact_directory_prefix_relocated():
    assert module().relocate('/old/jobs/id', '/old', '/new') == '/new/jobs/id'
    assert module().relocate('/older/jobs/id', '/old', '/new') == '/older/jobs/id'
    assert module().relocate('SoilOriginal', '/old', '/new') == 'SoilOriginal'


def test_nested_tasks_keep_scientific_arguments_and_input_immutable():
    old = {'commands': [{'argv': ['python', '/old/jobs/a', '--budget-ms', '60']}],
           'depends_on': ['quality_SoilOriginal_svm_s42_f0'], 'observe': True}
    new = module().relocate(old, '/old', '/new')
    assert new['commands'][0]['argv'] == ['python', '/new/jobs/a', '--budget-ms', '60']
    assert old['commands'][0]['argv'][1] == '/old/jobs/a'
    assert new['depends_on'] == old['depends_on'] and new['observe'] is True
