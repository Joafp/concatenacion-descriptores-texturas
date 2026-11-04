import importlib.util
from pathlib import Path
import sys

import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('hytex_runner', SCRIPTS / 'run_hytex_external_condition.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeAdapter:
    provenance = {'method': 'synthetic test only'}

    @classmethod
    def from_offline(cls, *args, **kwargs):
        return cls()

    def extract_file(self, path):
        return torch.full((1, 1538), int(Path(path).stem) / 10., dtype=torch.float32)

    def predict_file(self, path):
        label = int(Path(path).stem) % 2
        return {'prediction': label, 'logits': [1., 0.] if label == 0 else [0., 1.],
                'elapsed_ns': 1000000, 'elapsed_ms': 1.}


def fixture(tmp_path):
    rows = []
    for i in range(6):
        path = tmp_path / f'{i}.png'
        path.write_bytes(b'synthetic file; adapter mocked')
        rows.append({'path': str(path), 'label': str(i % 2), 'sha256': module.digest(path)})
    p = {'training_indices': [0, 1, 2, 3], 'external_indices': [4, 5], 'labels': [0, 1]}
    return p, rows


def receipt(folder, stage):
    module.write(folder / 'status.json', {'status': stage + '_complete',
                 'output_sha256': {f.name: module.digest(f) for f in folder.iterdir() if f.name != 'status.json'}})


def test_all_stage_contracts_with_synthetic_features_only(tmp_path, monkeypatch):
    import hytex_online_adapter
    monkeypatch.setattr(hytex_online_adapter, 'HyTexOnlineAdapter', FakeAdapter)
    torch.set_num_threads(2)
    p, rows = fixture(tmp_path)
    manifest = {'checkpoint_sha256': 'unused'}
    job = tmp_path / 'job'
    for stage in ('extract', 'train', 'online', 'audit'):
        (job / stage).mkdir(parents=True)
    result = module.extract(p, rows, manifest, job / 'extract')
    assert result['parity_max_abs_error'] == 0.
    assert (job / 'extract/parity_vectors.npz').exists()
    receipt(job / 'extract', 'extract')
    trained = module.train(p, rows, job, job / 'train')
    assert trained['epochs'] == 100
    receipt(job / 'train', 'train')
    online = module.online(p, rows, manifest, job, job / 'online')
    assert online['calls'] == 2 and online['warmup_calls_excluded'] == 5
    receipt(job / 'online', 'online')
    summary = module.audit_calls(p, rows, job / 'online', job / 'audit')
    assert summary['calls'] == 2 and summary['macro_f1_online'] == 1.


def test_fidelity_failure_saves_vectors_and_does_not_retry(tmp_path, monkeypatch):
    import hytex_online_adapter
    class Drift(FakeAdapter):
        calls = 0
        def extract_file(self, path):
            self.calls += 1
            return super().extract_file(path) + (1. if self.calls > 4 else 0.)
    monkeypatch.setattr(hytex_online_adapter, 'HyTexOnlineAdapter', Drift)
    p, rows = fixture(tmp_path)
    output = tmp_path / 'extract'
    output.mkdir()
    with pytest.raises(ValueError, match='consistency'):
        module.extract(p, rows, {'checkpoint_sha256': 'unused'}, output)
    assert (output / 'features.npz').exists() and (output / 'parity_vectors.npz').exists()
    assert max(module.read(output / 'parity.json')['max_abs_errors']) > 1e-4


def test_corrupt_upstream_receipt_stops_training(tmp_path):
    p, rows = fixture(tmp_path)
    job = tmp_path / 'job'
    output = job / 'train'
    output.mkdir(parents=True)
    (job / 'extract').mkdir()
    module.write(job / 'extract/status.json', {'status': 'requires_review'})
    with pytest.raises(ValueError, match='incomplete'):
        module.train(p, rows, job, output)
    assert not (output / 'head.pt').exists()
