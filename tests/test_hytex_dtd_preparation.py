import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('hytex_dtd_prepare', SCRIPTS / 'prepare_hytex_dtd_queue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def rows():
    # Row1 must stay excluded: its physical group is present in the test.
    return [{'group': g, 'split_1': split} for g, split in
            [('a', 'test'), ('a', 'train'), ('b', 'test'), ('c', 'train'), ('d', 'val'), ('e', 'train')]]


def test_inherited_exclusions_retained_without_dropping_test_duplicates():
    assert module.inherited_partition(rows(), [3, 4, 5], [0, 2], 0) == [1]
    duplicate_test = rows()
    duplicate_test[2]['group'] = 'a'
    assert module.inherited_partition(duplicate_test, [3, 4, 5], [0, 2], 0) == [1]


@pytest.mark.parametrize('train,test', [([1, 3, 4, 5], [0, 2]), ([3, 5], [0, 2]),
                                      ([3, 4, 5], [0]), ([3, 3, 4, 5], [0, 2])])
def test_new_leakage_omission_or_duplicate_rejected(train, test):
    with pytest.raises(ValueError):
        module.inherited_partition(rows(), train, test, 0)


def test_class_mapping_bijective_and_consistent():
    mapping = {}
    module.add_mapping(mapping, 'banded', '0')
    module.add_mapping(mapping, 'banded', '0')
    module.add_mapping(mapping, 'blotchy', '1')
    assert mapping == {'banded': 0, 'blotchy': 1}
    with pytest.raises(ValueError):
        module.add_mapping(mapping, 'banded', '1')
    with pytest.raises(ValueError):
        module.add_mapping(mapping, 'braided', '0')


def test_canonical_full_array_preserves_first_occurrence_convention(tmp_path):
    import numpy as np
    path = tmp_path / 'labels.npy'
    np.save(path, np.asarray(['b', 'b', 'a', 'c']))
    values, sha = module.canonical_array_labels(path)
    assert values == [0, 0, 1, 2] and len(sha) == 64
    np.save(path, np.asarray(['b', 'a', 'a', 'c']))
    changed, new_sha = module.canonical_array_labels(path)
    assert changed == [0, 1, 1, 2] and sha != new_sha
