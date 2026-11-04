import importlib.util
from pathlib import Path

import numpy as np

path = Path(__file__).resolve().parents[1] / "scripts/diagnose_dinov2_small_gpu_parity.py"
spec = importlib.util.spec_from_file_location("gpu_parity_diagnostic", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_diagnostic_keeps_the_original_tolerance():
    assert module.TOLERANCE == 1e-4
    assert module.compare_vectors([0.00009, 1.], [0., 1.])["pass"]
    assert not module.compare_vectors([0.00011, 1.], [0., 1.])["pass"]


def test_nonfinite_or_wrong_shape_cannot_pass():
    assert not module.compare_vectors([np.nan], [0.])["pass"]
    assert not module.compare_vectors([1., 0.], [1.])["pass"]
