import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("replication_queue", ROOT / "scripts/run_mesa_replication.py")
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def test_frozen_protocol_has_five_new_conditions_only():
    cfg = json.loads((ROOT / "configs/fsc_tex/replication_mesa_20261026.json").read_text())
    assert len({c["id"] for c in cfg["conditions"]}) == 5
    assert {(c["dataset"], c["seed"]) for c in cfg["conditions"]} == {
        ("FMD", 42), ("FMD", 123), ("FMD", 2026),
        ("Outex13Official1360", 123), ("Outex13Official1360", 2026)}
    assert cfg["budgets_ms"] == [15, 30, 60, 120]
    assert cfg["producer_folds"] == cfg["selection_folds"] == 3


def test_pipeline_freezes_explicit_algorithm_parameters_and_separate_outputs():
    cfg = json.loads((ROOT / "configs/fsc_tex/replication_mesa_20261026.json").read_text())
    for condition in cfg["conditions"]:
        commands = queue.commands(cfg, condition, Path("/new-run"), "/python")
        assert [name for name, _, _ in commands] == ["paired", "carlos", "hybrid", "static"]
        first = commands[0][1]
        assert first[first.index("--selection-folds") + 1] == "3"
        assert first[first.index("--library") + 1] == "22"
        assert ("--official-split" in first) == (condition["dataset"] == "Outex13Official1360")
        assert len({str(target) for _, _, target in commands}) == 4
        assert all(str(target).startswith("/new-run/") for _, _, target in commands)
