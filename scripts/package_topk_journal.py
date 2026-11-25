"""Export the English Top-k review manuscript and its editorial materials."""
from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

CARLOS = Path(__file__).resolve().parents[1] / "carlos"
FILES = (
    "main_en.tex",
    "main_topk_margen_en.pdf",
    "references.bib",
    "cas-sc.cls",
    "cas-common.sty",
    "figures/english/descriptor_pipeline.pdf",
    "figures/english/descriptor_pipeline.tex",
    "figures/english/curva_k.pdf",
    "figures/english/comparacion_pareada_e1.pdf",
    "figures/english/curves_by_dataset.pdf",
    "thumbnails/cas-email.jpeg",
    "thumbnails/cas-url.jpeg",
    "thumbnails/cas-facebook.jpeg",
    "thumbnails/cas-twitter.jpeg",
    "thumbnails/cas-gplus.jpeg",
    "thumbnails/cas-linkedin.jpeg",
    "revision_paper/Highlights.txt",
    "revision_paper/COVER_LETTER_DRAFT.md",
)
README = """# Top-k texture classification manuscript for author review

Open main_topk_margen_en.pdf to read the double-spaced English review manuscript.

Set main_en.tex as the main document when importing the ZIP into Overleaf.
Locally, with pdfLaTeX and BibTeX available, run from the extracted directory:

    pdflatex -halt-on-error main_en.tex
    bibtex main_en
    pdflatex -halt-on-error main_en.tex
    pdflatex -halt-on-error main_en.tex

The build uses the included Elsevier CAS class and the unsrtnat bibliography
style from the LaTeX distribution. Use a distribution with STIX fonts.

Highlights.txt and the draft cover letter are in revision_paper/. The authors
need to confirm the declarations and review the journal's submission form.
SHA256SUMS.json records the hashes of the source files and the supplied PDF.

Code and archived results:
https://github.com/Joafp/concatenacion-descriptores-texturas
"""


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Path to a new ZIP archive")
    args = parser.parse_args()
    files = {name: (CARLOS / name).read_bytes() for name in FILES}
    files["README.md"] = README.encode("utf-8")
    hashes = {name: sha256(content).hexdigest() for name, content in sorted(files.items())}
    files["SHA256SUMS.json"] = (dumps(hashes, indent=2) + "\n").encode("utf-8")
    with ZipFile(args.output, "x", compression=ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
