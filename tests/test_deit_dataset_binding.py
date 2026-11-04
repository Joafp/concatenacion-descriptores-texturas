import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/diagnose_deit_dataset_binding.py"
    spec = importlib.util.spec_from_file_location("deit_binding_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_rows_fixed_before_any_quality_observation():
    assert module().fixed_rows(1360) == [0, 1359]
    with pytest.raises(ValueError):
        module().fixed_rows(1)


def test_active_benchmark_detected(tmp_path):
    folder = tmp_path / "42"
    folder.mkdir()
    (folder / "cmdline").write_bytes(b"python\0/a/benchmark_local_single_image.py\0--run\0x\0")
    assert module().benchmarks_active(tmp_path)


def test_quality_worker_does_not_count_as_gpu_benchmark(tmp_path):
    folder = tmp_path / "42"
    folder.mkdir()
    (folder / "cmdline").write_bytes(b"python\0/a/run_local_external_panel.py\0")
    assert not module().benchmarks_active(tmp_path)
