import hashlib
import importlib.util
from pathlib import Path

import pytest


def module():
    p = Path(__file__).resolve().parents[1] / 'scripts/prepare_soil_extraction_manifest.py'
    spec = importlib.util.spec_from_file_location('soil_schema_test', p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def row(tmp_path, index, label):
    p = tmp_path / f'{index}.jpg'
    p.write_bytes(f'image{index}'.encode())
    return {'row_id': str(index), 'label': label, 'group': f'tray{index}',
            'source_path': p.name, 'source_sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def test_schema_maps_classes_without_reordering_or_mutating(tmp_path):
    rows = [row(tmp_path, 0, 'Yellow'), row(tmp_path, 1, 'Alluvial')]
    result, classes = module().convert_rows(rows, tmp_path)
    assert classes == ['Alluvial', 'Yellow']
    assert [r['label'] for r in result] == [1, 0]
    assert [r['source_label'] for r in result] == ['Yellow', 'Alluvial']
    assert [r['group'] for r in result] == [r['group'] for r in rows]
    assert rows[0]['label'] == 'Yellow'


def test_hash_mismatch_fails(tmp_path):
    item = row(tmp_path, 0, 'Soil')
    item['source_sha256'] = 'wrong'
    with pytest.raises(ValueError, match='hash'):
        module().convert_rows([item], tmp_path)


def test_order_not_repaired_silently(tmp_path):
    item = row(tmp_path, 1, 'Soil')
    with pytest.raises(ValueError, match='ordered'):
        module().convert_rows([item], tmp_path)


def test_missing_fields_rejected(tmp_path):
    with pytest.raises(ValueError, match='schema'):
        module().convert_rows([{'row_id': '0'}], tmp_path)
