import importlib.util
from pathlib import Path
import sys

import pytest


def module():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'scripts'))
    spec = importlib.util.spec_from_file_location('kth_redispatch_test', root / 'scripts/prepare_kth_authorized_redispatch.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_outputs_new_inputs_and_scientific_arguments_unchanged():
    task = {'lane': 'gpu', 'depends_on': ['quality_case'], 'observe': True,
        'commands': [
            {'argv': ['python', '/scripts/benchmark_local_single_image.py', '--run', '/old/quality',
                      '--output', '/old/online', '--repeats', '1'], 'timeout_seconds': 14400,
             'success': {'path': '/old/online/status.json', 'fields': {'status': 'done'}}},
            {'argv': ['python', '/scripts/audit_local_batch1_calls.py', '--online-run', '/old/online',
                      '--quality-run', '/old/quality', '--output', '/old/online_audit'],
             'timeout_seconds': 300, 'success': {'path': '/old/online_audit/audit.json', 'fields': {'status': 'audit'}}}]}
    new = module().online_task(task, Path('/old'), Path('/new'))
    first, second = [c['argv'] for c in new['commands']]
    assert first[first.index('--run') + 1] == '/old/quality'
    assert second[second.index('--quality-run') + 1] == '/old/quality'
    assert '/new/online' in new['commands'][0]['argv']
    assert new['commands'][0]['argv'][-2:] == ['--repeats', '1']
    assert new['commands'][0]['timeout_seconds'] == 14400
    assert task['commands'][0]['success']['path'] == '/old/online/status.json'
    assert new['observe'] and not new['depends_on']


def test_wrong_scope_fails():
    with pytest.raises(ValueError):
        module().online_task({'lane': 'cpu', 'commands': []}, Path('/old'), Path('/new'))
