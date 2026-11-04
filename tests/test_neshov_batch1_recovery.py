import json
from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_neshov_batch1_condition import extract_individually
from prepare_neshov_batch1_queue import check_diagnostic


def test_individual_extract_keeps_order_and_gate(tmp_path):
    def one(i): return np.full(3072, i, dtype=np.float32)
    info = extract_individually([3, 1, 7], one, tmp_path)
    saved = np.load(tmp_path / 'features.npz')
    assert saved['rows'].tolist() == [3,1,7]
    assert saved['features'][:,0].tolist() == [3,1,7]
    assert info['fit_extraction_batch_size'] == 1
    assert json.loads((tmp_path/'parity.json').read_text())['max_abs_errors'] == [0,0]


def test_unstable_reextraction_fails_without_deleting_vectors(tmp_path):
    seen = {}
    def one(i):
        seen[i] = seen.get(i,0)+1
        return np.full(3072, i + (0.01 if seen[i] > 1 else 0), dtype=np.float32)
    with pytest.raises(ValueError): extract_individually([3,7], one, tmp_path)
    assert (tmp_path/'features.npz').exists() and (tmp_path/'parity_vectors.npz').exists()


def test_original_batch_shape_failure_remains_evident():
    prior={'max_abs_errors':[0.004,0.006], 'tolerance':1e-4}
    observations={k:{'batch1_repeated':{'max_abs':0},'batch8_repeated':{'max_abs':0},
                     'batch8_vs_batch1':{'max_abs':v}} for k,v in zip(('first','last'),prior['max_abs_errors'])}
    diagnostic={'status':'diagnostic_complete','diagnostic_only':True,
                'external_test_evaluated':False,'f1_or_latency_produced':False,'observations':observations}
    check_diagnostic(diagnostic,prior)
    diagnostic['observations']['first']['batch1_repeated']['max_abs']=0.1
    with pytest.raises(ValueError): check_diagnostic(diagnostic,prior)
