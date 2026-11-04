import importlib.util
import json
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('hytex_dataset_summary', SCRIPTS / 'consolidate_hytex_external_dataset.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_dataset_call_budgets_do_not_duplicate_local_heads():
    assert sum(n for _, n in module.EXPECTED.values()) + 3000 == 36264
    assert sum(n for n, _ in module.EXPECTED.values()) + 15 == 47


def test_full_curet_condition_and_call_coverage_required():
    partitions = [{'dataset': 'CUReT', 'seed': 42, 'outer_fold': f} for f in (0, 1)]
    module.validate_coverage('CUReT', partitions, 5612)
    with pytest.raises(ValueError):
        module.validate_coverage('CUReT', partitions[:1], 2806)
    with pytest.raises(ValueError):
        module.validate_coverage('CUReT', partitions, 5611)
    with pytest.raises(ValueError):
        module.validate_coverage('CUReT', [partitions[0]] * 2, 5612)


def fixture():
    calls = [{'row_index': i, 'truth': i % 2, 'prediction': i % 2,
              'logits': [1., 0.] if i % 2 == 0 else [0., 1.], 'repeat': 0,
              'elapsed_ns': (i + 1) * 1000000, 'elapsed_ms': float(i + 1)} for i in range(10)]
    return calls, {'external_indices': list(range(10)), 'labels': [0, 1]}, [{'label': str(i % 2)} for i in range(10)]


def test_generic_raw_call_reaggregation_has_no_200_image_assumption():
    calls, p, rows = fixture()
    result = module.call_metrics(calls, p, rows)
    assert result['calls'] == 10 and result['macro_f1_online'] == 1. and result['mean_ms'] == 5.5


@pytest.mark.parametrize('change', ['coverage', 'truth', 'logits', 'time'])
def test_generic_call_integrity(change):
    calls, p, rows = fixture()
    if change == 'coverage':
        calls = calls[:-1]
    elif change == 'truth':
        calls[0]['truth'] = 1
    elif change == 'logits':
        calls[0]['logits'] = [float('nan'), 0.]
    else:
        calls[0]['elapsed_ms'] = -1.
    with pytest.raises(ValueError):
        module.call_metrics(calls, p, rows)


def test_running_queue_not_consolidated(tmp_path):
    queue = tmp_path / 'queue'
    queue.mkdir()
    for name, data in [('manifest.json', {}), ('preflight.json', {}),
                       ('gpu.json', {'status': 'running', 'current_task': 'active'})]:
        (queue / name).write_text(json.dumps(data))
    output = tmp_path / 'summary'
    with pytest.raises(ValueError, match='terminal'):
        module.consolidate(queue, output, 'CUReT')
    assert not output.exists()
