from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from diagnose_neshov_batch_parity import errors, frozen_path_from_queue
from consolidate_overnight_online_panel import digest


def test_errors_preserve_failure_and_repeat_agreement():
    x = np.zeros(4, dtype=np.float32)
    y = x.copy(); y[1] = 0.005
    assert errors(x, x)['max_abs'] == 0
    assert errors(x, y)['max_abs'] > 1e-4
    assert errors(x, y)['count_above_1e-4'] == 1


def test_nonfinite_and_shape_mismatch_fail():
    with pytest.raises(ValueError): errors([np.nan], [0])
    with pytest.raises(ValueError): errors([0], [0, 1])


def test_frozen_manifest_is_resolved_from_sealed_command(tmp_path):
    source = tmp_path / 'preflight.json'; source.write_text('{}')
    manifest = {'tasks': [{'id': 'Neshov_FMD_s42_f0', 'commands': [
        {'argv': ['python', '--manifest', str(source)]}]}],
        'source_sha256': {str(source): digest(source)}}
    assert frozen_path_from_queue(manifest) == source
    source.write_text('{"changed": true}')
    with pytest.raises(ValueError): frozen_path_from_queue(manifest)
