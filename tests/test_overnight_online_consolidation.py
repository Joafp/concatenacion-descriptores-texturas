import importlib.util
import json
from pathlib import Path

import pytest


def module():
    p = Path(__file__).resolve().parents[1] / 'scripts/consolidate_overnight_online_panel.py'
    spec = importlib.util.spec_from_file_location('online_consolidation_test', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def identities(mod):
    return [{'id': f'{d}_{c}_{i}', 'dataset': d, 'classifier': c}
            for d, n in mod.EXPECTED.items() for c in ('svm', 'resmlp') for i in range(n)]


def test_complete_coverage_requires_all_conditions_and_heads():
    m = module()
    jobs = identities(m)
    m.validate_identities(jobs)
    with pytest.raises(ValueError):
        m.validate_identities(jobs[:-1])
    jobs[-1] = dict(jobs[0])
    with pytest.raises(ValueError):
        m.validate_identities(jobs)


def test_dataset_mismatch_cannot_preserve_coverage_by_count():
    m = module()
    jobs = identities(m)
    jobs[-1]['dataset'] = 'VisTex'
    with pytest.raises(ValueError):
        m.validate_identities(jobs)


def test_f1_recomputed_from_predictions_not_imported_metrics():
    m = module()
    assert m.macro_f1([0, 0, 1, 1], [0, 1, 1, 1]) == pytest.approx(11 / 15)
    assert m.macro_f1([0, 1], [0, 1]) == 1
    with pytest.raises(ValueError):
        m.macro_f1([0, 1], [0, 2])


def test_missing_condition_prevents_output_creation(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m, 'select_jobs', lambda repo: ([{'id': 'pending', 'online_audit': str(tmp_path / 'missing')}], {}))
    out = tmp_path / 'should_not_exist'
    with pytest.raises(ValueError, match='no complete means'):
        m.consolidate(tmp_path, out)
    assert not out.exists()


def test_readiness_is_explicitly_not_a_full_audit(tmp_path, monkeypatch, capsys):
    m = module()
    monkeypatch.setattr(m, 'select_jobs', lambda repo: ([{'id': 'pending', 'online_audit': str(tmp_path / 'missing')}], {}))
    m.consolidate(tmp_path, None, check_ready=True)
    report = json.loads(capsys.readouterr().out)
    assert report['missing'] == ['pending']
    assert 'not full audit' in report['scope']
