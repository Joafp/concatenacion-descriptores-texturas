"""Make a compact secondary F1 table without changing the sealed original."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "paper/articulo/borrador_profesor/generated/baseline_f1.tex"
target = ROOT / "paper/generated_accuracy_primary_20261115_v3/baseline_f1_secondary.tex"
text = source.read_text()
assert r"\fontsize{8}{10}" in text and r"\tabcolsep}{3.0pt}" in text
text = text.replace(r"\fontsize{8}{10}", r"\fontsize{7.5}{9}").replace(r"\tabcolsep}{3.0pt}", r"\tabcolsep}{2.3pt}")
text = text.replace("Macro-F1 externo de cinco estrategias", "Macro-F1 complementario de cinco estrategias")
if target.exists():
    assert target.read_text() == text
else:
    target.write_text(text)
receipt = {"source": str(source.relative_to(ROOT)), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
           "output": str(target.relative_to(ROOT)), "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
           "data_changed": False, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
path = ROOT / "results/analysis/thesis_accuracy_primary_20261115_v3/layout_receipt.json"
if path.exists():
    assert json.loads(path.read_text()) == receipt
else:
    path.write_text(json.dumps(receipt, indent=2) + "\n")
