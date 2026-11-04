import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('hytex_summary', SCRIPTS / 'consolidate_hytex_fmd_external.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_full_condition_matrix_required():
    rows = [{'seed': s, 'outer_fold': f} for s in (42, 123, 2026) for f in range(5)]
    module.validate_identities(rows)
    for bad in (rows[:-1], rows + rows[:1], rows[:-1] + rows[:1]):
        with pytest.raises(ValueError):
            module.validate_identities(bad)


def fixture():
    calls = [{'row_index': i, 'truth': i % 2, 'prediction': i % 2,
              'logits': [1., 0.] if i % 2 == 0 else [0., 1.], 'repeat': 0,
              'elapsed_ns': 2000000, 'elapsed_ms': 2.} for i in range(200)]
    return calls, {'external_indices': list(range(200)), 'labels': [0, 1]}, [{'label': str(i % 2)} for i in range(200)]


def test_raw_metrics_recomputed_from_same_calls():
    calls, partition, rows = fixture()
    summary = module.metrics(calls, partition, rows)
    assert summary['macro_f1_online'] == 1. and summary['mean_ms'] == 2.


@pytest.mark.parametrize('change', ['coverage', 'truth', 'prediction', 'logits', 'time'])
def test_call_integrity_fails_closed(change):
    calls, partition, rows = fixture()
    if change == 'coverage':
        calls = calls[:-1]
    elif change == 'truth':
        calls[0]['truth'] = 1
    elif change == 'prediction':
        calls[0]['prediction'] = 1
    elif change == 'logits':
        calls[0]['logits'][0] = float('nan')
    else:
        calls[0]['elapsed_ns'] = -2
    with pytest.raises(ValueError):
        module.metrics(calls, partition, rows)
