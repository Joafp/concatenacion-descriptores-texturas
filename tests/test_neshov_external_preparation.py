import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('neshov_prepare', SCRIPTS / 'prepare_neshov_fmd_external.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def records(n=6):
    return [{'label': str(i % 2), 'group': str(i)} for i in range(n)]


def test_explicit_valid_partition():
    assert module.validate_partition([0, 1, 2, 3], [4, 5], records()) == [0, 1]


@pytest.mark.parametrize('train,test', [([0, 1, 1], [2, 3, 4, 5]),
                                      ([0, 1, 2, 3], [3, 4, 5]),
                                      ([0, 1], [2, 3, 4]),
                                      ([0, 2, 4], [1, 3, 5])])
def test_bad_partitions_rejected(train, test):
    with pytest.raises(ValueError):
        module.validate_partition(train, test, records())


def test_group_overlap_rejected():
    rows = records()
    rows[4]['group'] = rows[0]['group']
    with pytest.raises(ValueError, match='group'):
        module.validate_partition([0, 1, 2, 3], [4, 5], rows)


def test_singleton_batch_rejected_without_dropping_image():
    with pytest.raises(ValueError, match='BatchNorm'):
        module.validate_partition(list(range(33)), [33, 34], records(35))
