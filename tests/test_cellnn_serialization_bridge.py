import json
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_cellnn_external_condition_v2 as bridge
from prepare_cellnn_never_started_queue import eligible


def test_reproduce_original_float32_json_failure_then_exact_bridge(tmp_path):
    value=np.float32(0.123456789)
    original={'n_iter':2,'loss_curve':[value,np.float32(0.01)]}
    with pytest.raises(TypeError): json.dumps(original,allow_nan=False)
    path=tmp_path/'training_history.json';bridge.write(path,original)
    restored=json.loads(path.read_text())
    assert restored['loss_curve'][0]==float(value)
    assert np.float32(restored['loss_curve'][0]).tobytes()==value.tobytes()


@pytest.mark.parametrize('bad',[np.float32(np.nan),np.float32(np.inf),np.float64(-np.inf)])
def test_nonfinite_remains_error(tmp_path,bad):
    with pytest.raises(ValueError): bridge.write(tmp_path/'bad.json',{'loss':bad})


def test_unexpected_arrays_not_silently_converted(tmp_path):
    with pytest.raises(TypeError): bridge.write(tmp_path/'bad.json',{'loss':np.ones(3)})


def test_status_records_bridge_hash(tmp_path):
    path=tmp_path/'status.json';bridge.write(path,{'status':'running','count':np.int64(8)})
    result=json.loads(path.read_text())
    assert result['count']==8 and len(result['serialization_bridge_sha256'])==64


def test_only_never_started_dependency_blocked_allowed():
    state={'status':'blocked','reason':'dependency_requires_review'}
    assert eligible(state,False)
    assert not eligible(state,True)
    for key in ('pid','stage','started_utc','success_artifacts','argv'):
        assert not eligible({**state,key:None},False)
    assert not eligible({'status':'requires_review'},False)
    assert not eligible({'status':'complete'},False)
