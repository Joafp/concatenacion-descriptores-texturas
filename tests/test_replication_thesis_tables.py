import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("replica_tables", ROOT / "scripts/build_replication_thesis_tables.py")
tables = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tables)


def test_number_and_compact_table_keep_explicit_metric_cost_pair():
    assert tables.pair(0.977488805984743, 35.6892916666667) == "0,977489 / 35,689"
    result = tables.table("caption", "tab:test", ["Condition", "F1 / ms"], [["FMD/42", "0,9 / 15,000"]], True)
    assert r"\begin{table}" in result and "longtable" not in result
    assert r"\fontsize{8}{10}" in result


def test_generated_replication_tables_rebuild_identically(tmp_path):
    source = ROOT / "results/analysis/mesa_replication_20261026"
    if not (source / "summary.json").is_file():
        pytest.skip("local audited replication unavailable")
    tables.build(source, tmp_path)
    for generated in tmp_path.glob("*.tex"):
        assert generated.read_bytes() == (ROOT / "paper/generated_replication" / generated.name).read_bytes()
    provenance = json.loads((tmp_path / "provenance.json").read_text())
    assert provenance["metric_rows"] == 170 and provenance["p0_rows"] == 60
    assert provenance["table_rows"] == {"means": 8, "curves": 20, "references": 30, "p0": 24}


def test_full_sweep_keeps_losses_other_rules_and_all_budgets():
    folder = ROOT / "paper/generated_replication"
    if not folder.is_dir():
        pytest.skip("generated manuscript tables unavailable")
    sweep = (folder / "replica_barrido.tex").read_text()
    rows = [line for line in sweep.splitlines() if line.startswith(("FMD/", "Outex/"))]
    assert len(rows) == 20
    for condition in ("FMD/42", "FMD/123", "FMD/2026", "Outex/123", "Outex/2026"):
        assert len([line for line in rows if line.startswith(condition + " & ")]) == 4
    # The FMD/42 B60 static winner must not disappear from the table.
    loss = next(line for line in rows if line.startswith("FMD/42 & 60 &"))
    assert "0,977506 / 38,282" in loss and "0,978772 / 35,078" in loss
    p0 = (folder / "replica_p0.tex").read_text()
    assert "0,974596 / 281,061 & 0,977489 / 35,689" in p0
    assert "0,912135 / 134,273 & 0,905991 / 40,750" in p0
