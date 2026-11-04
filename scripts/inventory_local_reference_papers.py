"""Inventory supplied PDFs without uploading, copying, or interpreting PDF contents."""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(output):
    if output.exists():
        raise FileExistsError(output)
    folder = ROOT / 'docs/referencias'
    catalog = folder / 'README.md'
    text = catalog.read_text()
    papers = []
    for path in sorted(folder.glob('*.pdf')):
        lines = [line for line in text.splitlines() if '`' + path.name + '`' in line]
        papers.append({'file': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                       'sha256': digest(path), 'catalog_entry': lines[0] if lines else None,
                       'status': 'LOCAL_PDF_PRESENT_RECIPE_AUDIT_PENDING',
                       'method_replication_complete': False, 'online_latency_measured': False,
                       'code_and_weights_verified': False})
    report = {'status': 'LOCAL_SOURCE_INVENTORY_NOT_REPLICATION',
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'pdf_count': len(papers), 'papers': papers,
              'catalog_sha256': digest(catalog), 'script_sha256': digest(Path(__file__)),
              'scope': 'Catalog and file hashes only; not PDF reading, source verification or license clearance',
              'uploads': 0, 'downloads': 0}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'pdf_count': len(papers), 'missing_catalog_entries':
                      [p['file'] for p in papers if p['catalog_entry'] is None]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    inventory(parser.parse_args().output)
