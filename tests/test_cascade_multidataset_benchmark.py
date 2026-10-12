import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    'physical_six', Path(__file__).resolve().parents[1] / 'scripts/benchmark_cascade_multidataset.py')
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


def test_six_fixed_protocols():
    assert len(benchmark.CONDITIONS) == 6
    assert benchmark.CONDITIONS['KTHTIPS2b'] == 'official1_inverted'
    assert benchmark.CONDITIONS['CUReT'] == 'curet_half_indices:a_to_b'
    assert benchmark.CONDITIONS['SoilOriginal'] == 'stratified_group_kfold5_fold0'


def test_output_cannot_overwrite(tmp_path):
    path = tmp_path / 'result.json'
    benchmark.write_new(path, {'status': 'original'})
    initial = path.read_bytes()
    with pytest.raises(FileExistsError):
        benchmark.write_new(path, {'status': 'changed'})
    assert path.read_bytes() == initial


def test_digest_is_bound_to_bytes(tmp_path):
    path = tmp_path / 'source'
    path.write_bytes(b'a')
    before = benchmark.digest(path)
    path.write_bytes(b'b')
    assert benchmark.digest(path) != before
