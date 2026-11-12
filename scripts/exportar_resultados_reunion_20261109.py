from pathlib import Path
from pypdf import PdfReader, PdfWriter

root = Path(__file__).resolve().parents[1] / "results/presentation_reunion_20261109"
source = root / "presentacion_completa_exportada_20261109.pdf"
target = root / "Resultados_comparacion_seis_datasets_20261109.pdf"
reader = PdfReader(source)
assert len(reader.pages) == 16, f"Unexpected source page count: {len(reader.pages)}"
assert "FMD" in (reader.pages[8].extract_text() or ""), "First results page not found"
writer = PdfWriter()
for page in reader.pages[8:]:
    writer.add_page(page)
with target.open("xb") as output:
    writer.write(output)
check = PdfReader(target)
assert len(check.pages) == 8
assert "FMD" in (check.pages[0].extract_text() or "")
print(f"Created {target} with {len(check.pages)} pages; first slide is FMD.")
