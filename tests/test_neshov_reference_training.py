import numpy as np
import pytest
import torch
from neshov_reference_training import validate_partition_panel, fit_fixed_head


def test_panel_rejects_overlap_repeats_and_different_universes():
    good = [{"fit_indices": [2, 3], "validation_indices": [0, 1]},
            {"fit_indices": [0, 1], "validation_indices": [2, 3]}]
    assert validate_partition_panel(good).tolist() == [0, 1, 2, 3]
    for bad in [good + [good[0]],
                [{"fit_indices": [0, 2, 3], "validation_indices": [0, 1]}, good[1]],
                [{"fit_indices": [2], "validation_indices": [0, 1]}, good[1]]]:
        with pytest.raises(ValueError):
            validate_partition_panel(bad)


def test_fixed_head_is_deterministic_and_uses_fit_only():
    torch.set_num_threads(1)
    x = np.arange(48, dtype=np.float32).reshape(12, 4) / 48
    y = np.arange(12) % 3
    a, ha = fit_fixed_head(x, y, 3, epochs=2, batch_size=4)
    b, hb = fit_fixed_head(x, y, 3, epochs=2, batch_size=4)
    assert ha == hb and [r["epoch"] for r in ha] == [1, 2]
    assert not a.training
    assert all(torch.equal(a.state_dict()[k], b.state_dict()[k]) for k in a.state_dict())


def test_singleton_batch_is_not_silently_dropped():
    with pytest.raises(ValueError):
        fit_fixed_head(np.ones((33, 4)), np.zeros(33), 2, epochs=1, batch_size=32)
