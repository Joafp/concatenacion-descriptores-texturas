"""Lossless Soil CSV schema adapter; no extractor, GPU or experiment execution."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def convert_rows(rows, root):
    required = {'row_id', 'label', 'group', 'source_path', 'source_sha256'}
    if not rows or not required.issubset(rows[0]):
        raise ValueError('source Soil schema missing fields')
    if [int(r['row_id']) for r in rows] != list(range(len(rows))):
        raise ValueError('source rows must remain contiguous and ordered')
    classes = sorted({r['label'] for r in rows})
    if not all(classes):
        raise ValueError('empty class name')
    mapping = {name: i for i, name in enumerate(classes)}
    converted = []
    for row in rows:
        p = Path(row['source_path'])
        p = p if p.is_absolute() else root / p
        if digest(p) != row['source_sha256']:
            raise ValueError('source image hash mismatch')
        converted.append(dict(row, label=mapping[row['label']],
                              source_label=row['label'], class_name=row['label'],
                              path=str(p.resolve())))
    return converted, classes


def prepare(source, output):
    import numpy as np
    from reextract_confirmatory_embeddings import read_manifest
    from run_confirmatory_nested import canonical_labels

    if output.exists():
        raise FileExistsError(output)
    with source.open(newline='') as f:
        original = list(csv.DictReader(f))
    rows, classes = convert_rows(original, ROOT)
    labels = canonical_labels(np.load(ROOT / 'embeddings_extensions/SoilOriginal/deit_s_labels.npy', allow_pickle=False))
    if len(rows) != 1140 or len(classes) != 7 or not np.array_equal(labels, [r['label'] for r in rows]):
        raise ValueError('Soil row/class/label partition drift')
    output.mkdir(parents=True, exist_ok=False)
    path = output / 'SoilOriginal_extraction_schema.csv'
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    # Exercise the exact existing loader, not just the adapter's own assertions.
    paths, observed_labels, observed_classes = read_manifest(path)
    assert observed_classes == classes and np.array_equal(observed_labels, labels)
    assert [str(p) for p in paths] == [r['path'] for r in rows]
    receipt = {'status': 'SOIL_EXTRACTION_SCHEMA_VALIDATED_NO_MODEL_EXECUTED',
        'source_manifest': str(source.resolve()), 'source_manifest_sha256': digest(source),
        'adapted_manifest': str(path.resolve()), 'adapted_manifest_sha256': digest(path),
        'rows': len(rows), 'classes': classes, 'image_hashes_verified': len(rows),
        'row_order_unchanged': True, 'source_groups_unchanged': True,
        'canonical_labels_match_original_embedding': True,
        'changes': 'absolute path alias for source_path; canonical integer label; class_name/source_label retain original string',
        'source_sha256': digest(__file__), 'gpu_executed': False,
        'retry_authorized_by_this_receipt': False}
    with (output / 'receipt.json').open('x') as f:
        f.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    prepare(ROOT / 'results/extensions/soil_original/sample_manifests/SoilOriginal.csv', args.output.resolve())
