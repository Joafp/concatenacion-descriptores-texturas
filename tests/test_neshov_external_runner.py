import importlib.util
import json
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('neshov_external', SCRIPTS / 'run_neshov_external_condition.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def online_fixture(tmp_path):
    folder = tmp_path / 'online'
    folder.mkdir()
    calls = [{'row_index': i, 'truth': i, 'prediction': i, 'logits': [1., 0.] if i == 0 else [0., 1.],
              'repeat': 0, 'elapsed_ns': 1000000, 'elapsed_ms': 1.} for i in range(2)]
    (folder / 'calls.jsonl').write_text(''.join(json.dumps(c) + '\n' for c in calls))
    def receipt():
        module.write(folder / 'status.json', {'status': 'online_complete',
                     'output_sha256': {'calls.jsonl': module.digest(folder / 'calls.jsonl')}})
    receipt()
    output = tmp_path / 'audit'
    output.mkdir()
    return folder, output, calls, receipt


def test_same_call_audit_recalculates(tmp_path):
    folder, out, _, _ = online_fixture(tmp_path)
    result = module.audit_calls({'external_indices': [0, 1], 'labels': [0, 1]},
                               [{'label': '0'}, {'label': '1'}], folder, out)
    assert result['macro_f1_online'] == result['accuracy_online'] == 1.
    assert result['mean_ms'] == 1. and result['calls'] == 2


@pytest.mark.parametrize('mutation', ['duplicate', 'bad_prediction', 'bad_time'])
def test_audit_rejects_invalid_call_evidence(tmp_path, mutation):
    folder, out, calls, receipt = online_fixture(tmp_path)
    if mutation == 'duplicate':
        calls[1]['row_index'] = 0
    elif mutation == 'bad_prediction':
        calls[1]['prediction'] = 0
    else:
        calls[0]['elapsed_ns'] = -1
    (folder / 'calls.jsonl').write_text(''.join(json.dumps(c) + '\n' for c in calls))
    receipt()
    with pytest.raises(ValueError):
        module.audit_calls({'external_indices': [0, 1], 'labels': [0, 1]},
                           [{'label': '0'}, {'label': '1'}], folder, out)


def test_artifact_drift_rejected(tmp_path):
    folder, _, _, _ = online_fixture(tmp_path)
    (folder / 'calls.jsonl').write_text('modified')
    with pytest.raises(ValueError, match='drift'):
        module.verify_artifact(folder, 'online_complete')


def test_failed_stage_preserves_error_and_refuses_overwrite(tmp_path, monkeypatch):
    import torch
    monkeypatch.setattr(torch, 'set_num_threads', lambda _: None)
    manifest = tmp_path / 'manifest.json'
    rows = tmp_path / 'rows.csv'
    rows.write_text('label,path\n0,absent\n')
    module.write(manifest, {'source_sha256': {}, 'conditions': [{'seed': 42, 'outer_fold': 0,
                                                              'manifest': str(rows)}]})
    def fail(*args):
        raise ValueError('synthetic failure')
    monkeypatch.setattr(module, 'extract', fail)
    job = tmp_path / 'job'
    with pytest.raises(ValueError, match='synthetic'):
        module.run(manifest, 0, 'extract', job)
    assert module.read(job / 'extract/status.json')['status'] == 'requires_review'
    with pytest.raises(FileExistsError):
        module.run(manifest, 0, 'extract', job)
