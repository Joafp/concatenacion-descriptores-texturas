import copy
import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('hytex_curet_prepare', SCRIPTS / 'prepare_hytex_curet_queue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    rows = [{'row_id': str(i), 'label': str(i % 61), 'group': str(i)} for i in range(5612)]
    a, b = list(range(0, 5612, 2)), list(range(1, 5612, 2))
    partitions = [{'seed': 42, 'outer_fold': f, 'curet_direction': d,
                   'training_indices': train, 'external_indices': test, 'labels': list(range(61))}
                  for f, d, train, test in [(0, 'a_to_b', a, b), (1, 'b_to_a', b, a)]]
    return partitions, rows


def test_two_canonical_complementary_directions():
    p, rows = fixture()
    module.validate_curet(p, rows)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'direction', 'classes', 'coverage', 'rows', 'group'])
def test_invalid_curet_sources_fail_closed(mutation):
    p, rows = copy.deepcopy(fixture())
    if mutation == 'missing':
        p = p[:1]
    elif mutation == 'duplicate':
        p[1] = copy.deepcopy(p[0])
    elif mutation == 'direction':
        p[0]['curet_direction'] = 'b_to_a'
    elif mutation == 'classes':
        p[0]['labels'] = p[0]['labels'][:-1]
    elif mutation == 'coverage':
        p[0]['external_indices'] = p[0]['external_indices'][:-1]
    elif mutation == 'rows':
        rows[0]['row_id'] = '999'
    else:
        rows[1]['group'] = rows[0]['group']
    with pytest.raises(ValueError):
        module.validate_curet(p, rows)
