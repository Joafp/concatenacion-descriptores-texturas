"""Fresh Neshov common-panel version with consistent batch-1 extraction."""
import argparse
from pathlib import Path
import run_neshov_external_condition as core


def extract_individually(indices, extract_one, output):
    import numpy as np
    if not indices:
        raise ValueError('training set empty')
    features = []
    for pos, index in enumerate(indices):
        vector = np.asarray(extract_one(index))
        if vector.shape != (3072,) or not np.isfinite(vector).all():
            raise ValueError('invalid feature vector')
        features.append(vector)
        if pos % 50 == 0:
            print(f'extracted {pos + 1}/{len(indices)}', flush=True)
    features = np.stack(features)
    np.savez_compressed(output / 'features.npz', rows=np.asarray(indices), features=features)
    positions = (0, len(indices) - 1)
    again = np.stack([extract_one(indices[pos]) for pos in positions])
    errors = [float(np.max(np.abs(again[i] - features[pos]))) for i, pos in enumerate(positions)]
    np.savez_compressed(output / 'parity_vectors.npz', cached=features[list(positions)], reextracted=again)
    core.write(output / 'parity.json', {'training_rows': [indices[0], indices[-1]],
        'max_abs_errors': errors, 'tolerance': 1e-4, 'regime': 'batch1 fit vs batch1 reextraction',
        'prior_batch1_vs_batch8_failure_retained': True})
    if max(errors) > 1e-4:
        raise ValueError('batch1 route consistency failed; requires review')
    return {'parity_max_abs_error': max(errors), 'training_images': len(indices),
            'fit_extraction_batch_size': 1, 'prior_batch8_failure_not_reinterpreted': True}


def extract(partition, rows, preflight, output):
    import torch
    from PIL import Image
    from neshov_beit_reference import FrozenLayerAggregation, load_offline_backbone, preprocessing
    model, info = load_offline_backbone()
    if core.digest(info['local_weight_path']) != preflight['checkpoint_sha256']:
        raise ValueError('checkpoint mismatch')
    model = FrozenLayerAggregation(model).to('cuda', dtype=torch.float32).eval()
    transform = preprocessing()

    def one(index):
        row = rows[index]
        path = core.ROOT / row['path']
        if core.digest(path) != row['sha256']:
            raise ValueError('image drift')
        with Image.open(path) as image:
            x = transform(image.convert('RGB')).unsqueeze(0).to('cuda')
        with torch.inference_mode():
            return model(x).cpu().numpy()[0]
    return extract_individually(partition['training_indices'], one, output)


def run(manifest_path, number, stage, job):
    core.extract = extract
    return core.run(manifest_path, number, stage, job)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--number', type=int, required=True)
    parser.add_argument('--stage', choices=['extract', 'train', 'online', 'audit'], required=True)
    parser.add_argument('--job', type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.number, args.stage, args.job)
