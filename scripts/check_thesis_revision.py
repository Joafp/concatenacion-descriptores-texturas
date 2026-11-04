"""Check active thesis dependencies/tables and save a post-revision hash manifest.

This checks saved artifacts, not independent training or bibliography semantics.
Run after compiling paper/tesis.tex. Refuses to overwrite its output.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--static-summary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--editorial', action='store_true',
                        help='Check editorial provenance and archived source preservation')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    paper = ROOT / 'paper'
    bs = chr(92)
    active = []
    pending = [paper / 'tesis.tex']
    while pending:
        path = pending.pop()
        if path in active:
            continue
        assert path.is_file(), path
        active.append(path)
        body = chr(10).join(line for line in path.read_text().splitlines()
                           if not line.lstrip().startswith('%'))
        for name in re.findall(re.escape(bs) + 'input[{]([^}]+)[}]', body):
            dep = paper / name
            pending.append(dep if dep.suffix else dep.with_suffix('.tex'))
    text = chr(10).join(line for p in active for line in p.read_text().splitlines()
                        if not line.lstrip().startswith('%'))
    keys = {k.strip() for m in re.findall(re.escape(bs) + 'cite[a-zA-Z]*[{]([^}]+)[}]', text)
            for k in m.split(',')}
    bib = paper / 'articulo/borrador_profesor/references.bib'
    available = set(re.findall('@[a-zA-Z]+ *[{] *([^,]+)', bib.read_text()))
    assert not keys - available, keys - available
    dependencies = []
    for name in re.findall(re.escape(bs) + 'input[{]([^}]+)[}]', text):
        path = paper / name
        dependencies.append(path if path.suffix else path.with_suffix('.tex'))
    for line in text.splitlines():
        if bs + 'includegraphics' in line:
            dependencies.append(paper / line.split(']{', 1)[1].split('}', 1)[0])
    assert all(p.is_file() for p in dependencies), dependencies
    log = (paper / 'tesis.log').read_text(errors='replace')
    assert 'Overfull' not in log and 'undefined' not in log.lower()
    assert 'Output written on tesis.pdf' in log
    info = subprocess.check_output(['pdfinfo', str(paper / 'tesis.pdf')], text=True)
    pages = int(re.search('^Pages: +([0-9]+)', info, re.M)[1])
    with args.static_summary.open() as stream:
        rows = list(csv.DictReader(stream))
    source = {(r['dataset'], r['classifier'], r['method']): r for r in rows}
    datasets = {'DTD': 'DTD', 'FMD': 'FMD', 'CUReT': 'CUReT',
                'Outex': 'Outex13Official1360', 'Soil': 'SoilOriginal',
                'KTH-TIPS2-b': 'KTHTIPS2b'}
    methods = ['best_individual', 'full_concat', 'topk_individual', 'gfs', 'homogeneous']
    cells = 0
    for name, metric in [('baseline_f1.tex', 'f1'), ('baseline_accuracy.tex', 'accuracy')]:
        path = paper / 'articulo/borrador_profesor/generated' / name
        for line in path.read_text().splitlines():
            fields = [v.strip() for v in line.split('&')]
            if len(fields) != 7 or fields[0] not in datasets:
                continue
            dataset, clf = datasets[fields[0]], fields[1].lower()
            for method, cell in zip(methods, fields[2:]):
                printed = float(re.search('0[{],[}]([0-9]+)', cell)[0].replace('{,}', '.'))
                expected = round(float(source[dataset, clf, method][metric]), 4)
                assert abs(printed - expected) < 1e-9, (dataset, clf, method, metric)
                cells += 1
    assert cells == 120, cells
    editorial = {}
    editorial_paths = []
    if args.editorial:
        provenance_path = paper / 'generated_editorial/provenance.json'
        provenance = json.loads(provenance_path.read_text())
        for group in ('input_sha256', 'output_sha256'):
            for name, expected in provenance[group].items():
                assert sha256(ROOT / name) == expected, (group, name)
                editorial_paths.append(ROOT / name)
        renderer = ROOT / 'scripts/build_editorial_thesis_artifacts.py'
        assert sha256(renderer) == provenance['script_sha256']
        preserved = {}
        for name in ('summary.json', 'canonical_predictions/summary.json'):
            report = ROOT / 'results/analysis/thesis_reaudit_20261025' / name
            for path, expected in json.loads(report.read_text())['input_sha256'].items():
                if not path.startswith('paper/'):
                    preserved[path] = expected
        for path, expected in preserved.items():
            assert sha256(ROOT / path) == expected, ('archived source changed', path)
        body_chapters = re.findall(re.escape(bs) + 'input[{](chapters/[0-9][^}]+)[}]',
                                   (paper / 'tesis.tex').read_text())
        assert len(body_chapters) == 7, body_chapters
        editorial = {
            'body_chapters': len(body_chapters),
            'editorial_inputs_unchanged': len(provenance['input_sha256']),
            'generated_outputs_unchanged': len(provenance['output_sha256']),
            'archived_inputs_unchanged': len(preserved),
        }
        editorial_paths += [provenance_path, renderer,
                            paper / 'revision_editorial_20261025_before.tar.gz',
                            ROOT / 'docs/fsc_tex/REVISION_EDITORIAL_APLICADA_2026-10-25.md']
    extra = [ROOT / name for name in (
        'paper/README.md', 'paper/revision_20261025_before.tar.gz',
        'paper/tesis.pdf', 'scripts/audit_thesis_state_20261025.py',
        'scripts/audit_archived_cascade_predictions.py', 'scripts/check_thesis_revision.py',
        'docs/fsc_tex/AUDITORIA_TESIS_Y_CIERRE_2026-10-25.md',
        'docs/fsc_tex/PLAN_CIERRE_VIGENTE_2026-10-25.md',
        'docs/fsc_tex/PLAN_INTEGRACION_CARLOS_CASCADA_2026-10-19.md',
        'docs/PROPUESTA_TESIS_FUSION_SECUENCIAL_COSTO_RIESGO.md')]
    paths = set(active + dependencies + [bib, args.static_summary.resolve()] + extra + editorial_paths)
    result = {
        'status': 'ANALYZED', 'cut_date': '2026-10-25',
        'scope': 'Post-revision local structural and printed-table checks; no fitting or citation-semantic certification',
        'formal_full_ars_certification': False,
        'citation_keys_used': len(keys), 'bib_entries': len(available),
        'missing_citation_keys': [], 'active_dependencies': len(dependencies),
        'static_table_cells_checked': cells, 'pdf_pages': pages,
        'underfull_warnings': log.count('Underfull'),
        'editorial_checks': editorial,
        'overfull_warnings': 0, 'undefined_references': 0,
        'sha256': {str(p.relative_to(ROOT)): sha256(p) for p in sorted(paths)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + chr(10))
    print({k: v for k, v in result.items() if k != 'sha256'})


if __name__ == '__main__':
    main()
