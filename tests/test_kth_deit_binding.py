"""Hermetic guards for a new KTH diagnostic, without models or GPU."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/diagnose_kth_deit_binding.py"
spec = importlib.util.spec_from_file_location("kth_binding", SCRIPT)
binding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binding)


def test_embedding_alias(tmp_path):
    cfg = {"dataset": "KTHTIPS2b", "embedding_root": "embeddings_extensions"}
    assert binding.embedding_directory(cfg, tmp_path) == tmp_path / "embeddings_extensions/KTH-TIPS2-b"
    cfg["embedding_root"] = str(tmp_path / "absolute")
    assert binding.embedding_directory(cfg, tmp_path) == tmp_path / "absolute/KTH-TIPS2-b"


@pytest.mark.parametrize("dataset", ["DTD", "FMD", "CUReT", "SoilOriginal", "Outex13Official1360", "KTH-TIPS2-b"])
def test_scope_kth_only(dataset):
    with pytest.raises(ValueError, match="KTH-only"):
        binding.embedding_directory({"dataset": dataset, "embedding_root": "unused"})


def test_fixed_rows():
    assert binding.fixed_rows(4752) == [0, 4751]
    with pytest.raises(ValueError):
        binding.fixed_rows(1)


def test_active_guard(tmp_path):
    folder = tmp_path / "123"
    folder.mkdir()
    (folder / "cmdline").write_bytes(b"python\0/path/benchmark_local_single_image.py\0--output\0unused")
    assert binding.benchmarks_active(tmp_path)
    (folder / "cmdline").write_bytes(b"python\0unrelated.py\0")
    assert not binding.benchmarks_active(tmp_path)


def test_execute_stops_before_inputs_when_benchmark_active(monkeypatch, tmp_path):
    from types import SimpleNamespace
    monkeypatch.setattr(binding, "benchmarks_active", lambda: True)
    with pytest.raises(RuntimeError, match="benchmark active"):
        binding.run(SimpleNamespace(execute=True, output=tmp_path / "new"))
    assert not (tmp_path / "new").exists()


def test_output_never_overwritten(tmp_path):
    from types import SimpleNamespace
    with pytest.raises(FileExistsError, match="exclusive"):
        binding.run(SimpleNamespace(execute=False, output=tmp_path))
