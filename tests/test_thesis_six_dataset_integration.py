"""The thesis must use closed evidence and retain its scientific limitations."""
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "paper/generated_top4_fixed_closure_20261115"


def test_tables_are_hash_bound_to_the_complete_audit():
    r = json.loads((ROOT / "results/analysis/thesis_six_dataset_integration_20261115_v1/tables_receipt.json").read_text())
    assert r["summary"]["completed_conditions"] == 27
    assert len(r["outputs"]) == 7
    for section in ["sources", "outputs"]:
        for name, expected in r[section].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected


def test_kth_bases_are_absent_instead_of_invented_zero_metrics():
    text = (GENERATED / "e1_bases.tex").read_text()
    row = next(line for line in text.splitlines() if line.startswith("KTH-TIPS2b &"))
    assert row.count("--") == 2
    assert "no accuracy cero" in text
    assert "KTH-TIPS2b" in (GENERATED / "e1_accuracy.tex").read_text()


def test_current_results_use_six_datasets_without_stale_e1_means():
    text = (ROOT / "paper/chapters/05_resultados.tex").read_text()
    current = text.split(r"\section{Ampliación E1:", 1)[1].split(r"\section{Adquisición proyectada", 1)[0]
    assert "0,944449" in current and "0,944581" in current and "p=0,5625" in current
    assert "75,00" in current
    assert "0,941840" not in current and "generated_top4_fixed_e1_e2_20261115" not in current
    assert "no tiempos de ejecución online" in current


def test_abstracts_and_conclusion_keep_reporting_and_selection_distinct():
    abstract = (ROOT / "paper/tesis.tex").read_text()
    conclusion = (ROOT / "paper/chapters/07_conclusion.tex").read_text()
    assert "0,944449" in abstract and "0.944449" in abstract
    assert "0,944581" in abstract and "0.944581" in abstract
    assert "Accuracy is the primary reporting metric" in abstract
    assert "macro-F1-based historical rankings" in abstract
    assert "27 condiciones y seis datasets" in conclusion
    assert "no representa latencia online" in conclusion
    assert "no acredita equivalencia" in conclusion
