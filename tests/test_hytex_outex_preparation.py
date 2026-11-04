import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_hytex_outex_queue import validate_outex, DATASET, label_digest
from prepare_hytex_outex_queue import validate_archived_truth


def fixture():
    rows = [{'row_id': str(i), 'label': str((i // 2) % 68), 'group': str(i),
             'official_split': 'train' if i % 2 == 0 else 'test'} for i in range(1360)]
    p = {'dataset': DATASET, 'seed': 42, 'outer_fold': 0, 'labels': list(range(68)),
         'training_indices': list(range(0,1360,2)), 'external_indices': list(range(1,1360,2))}
    return p, rows


def test_exact_official_partition():
    validate_outex(*fixture())


@pytest.mark.parametrize('kind', ['missing','order','group','labels','identity','row'])
def test_reject_corruption(kind):
    p, rows = fixture()
    if kind == 'missing': p['external_indices'].pop()
    elif kind == 'order': p['training_indices'].reverse()
    elif kind == 'group': rows[1]['group'] = rows[0]['group']
    elif kind == 'labels': p['labels'].pop()
    elif kind == 'identity': p['seed'] = 123
    else: rows[0]['row_id'] = '8'
    with pytest.raises(ValueError): validate_outex(p, rows)


def test_label_digest_binds_every_row():
    import numpy as np
    labels = np.arange(1360, dtype=np.int64) % 68
    before = label_digest(labels)
    labels[-1] = 0
    assert before != label_digest(labels)


def test_all_policy_blocks_verified_not_deduplicated():
    p, rows = fixture()
    records = [{'policy': policy, 'row_index': str(i), 'label': rows[i]['label']}
        for policy in ('Completa-22','Adaptive-selection-margin','Ens-diversidad','Ens-tombola','Top-4')
        for i in p['external_indices']]
    validate_archived_truth(records, p['external_indices'], rows)
    records[-1]['label'] = '-1'
    with pytest.raises(ValueError): validate_archived_truth(records, p['external_indices'], rows)
    records.pop()
    with pytest.raises(ValueError): validate_archived_truth(records, p['external_indices'], rows)
