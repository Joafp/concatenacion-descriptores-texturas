#!/usr/bin/env python3
"""Paired physical pilot for the six archived cascade datasets.

One fixed condition per dataset, one image/class, three randomized paired
repetitions by default. Not a full-test quality evaluation or a timing claim
against Complete/GFS. Outputs are new, exclusive-create artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'scripts')]
CONDITIONS = {
    'DTD': 'official1',
    'FMD': 'stratified_group_kfold5_fold0',
    'CUReT': 'curet_half_indices:a_to_b',
    'Outex13Official1360': 'official1',
    'SoilOriginal': 'stratified_group_kfold5_fold0',
    'KTHTIPS2b': 'official1_inverted',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def extractor(name, device):
    """Reuse extraction-source preprocessing, not a new test-tuned transform."""
    import numpy as np
    import torch
    if name in {'siglip_base', 'eva02_base', 'mae_base'}:
        sota = module('physical_sota', REPO / 'src/extract_sota_2024.py')
        sota.DEVICE = device
        model, transform, kind = sota.load_model_and_transform(name)
        def raw(image):
            tensor = transform(image).unsqueeze(0).to(device)
            with torch.inference_mode():
                output = model(tensor) if kind == 'timm' else model(pixel_values=tensor)
                feature = output if kind == 'timm' else (output.pooler_output if getattr(output, 'pooler_output', None) is not None else output.last_hidden_state[:, 0])
            return feature.cpu().numpy().ravel()
    elif name == 'beitv2_base_final':
        from fsc_tex.executor import OnlineExtractorRegistry
        registry = OnlineExtractorRegistry(device=device)
        raw = registry.load_extractor(name)
    else:
        base = module('physical_base', REPO / 'src/01_extract_features.py')
        ext = base.get_extractor(name, device=device)
        if not hasattr(ext, 'transform') and not hasattr(ext, 'processor'):
            raise ValueError(f'No in-memory image adapter for {name}')
        def raw(image):
            with torch.inference_mode():
                if hasattr(ext, 'transform'):
                    tensor = ext.transform(image).unsqueeze(0).to(device)
                    feature = ext.model(tensor)
                else:
                    inputs = ext.processor(images=[image], return_tensors='pt').to(device)
                    output = ext.model(**inputs)
                    feature = output.pooler_output if getattr(output, 'pooler_output', None) is not None else output.last_hidden_state[:, 0, :]
            return feature.cpu().numpy().ravel()
    def normalized(image):
        vector = np.asarray(raw(image), dtype=np.float32)
        return vector / max(float(np.linalg.norm(vector)), 1e-12)
    return normalized


def run_condition(args):
    import numpy as np
    import torch
    from PIL import Image
    from run_adaptive_descriptor_pilot import margin
    from run_confirmatory_nested import load_dataset, load_manifest, make_model
    from run_train_selected_topk_cascade import outer_split, result_root
    from report_cost_aware_topk import CASCADE, SOURCES
    from benchmark_cascade_physical_pareado import sample_stratified_test_indices

    ds, protocol = args.dataset, CONDITIONS[args.dataset]
    folder = args.output / ds
    folder.mkdir(parents=True, exist_ok=False)
    archive = CASCADE / 'cheap_stage_selected_primary22'
    stem = f'{ds}_{protocol}'
    sources = [archive / (stem + suffix) for suffix in
               ('_result.json', '_selection_pretest.json', '_predictions.json')]
    result, pretest, predictions = [json.loads(p.read_text()) for p in sources]
    entries = [json.loads(p.read_text()) for p in
               (CASCADE / SOURCES[ds] / 'exact_archive').glob('*_topk_cascade.json')]
    entries = [entry for entry in entries if entry['protocol'] == protocol]
    if len(entries) != 1:
        raise ValueError('Expected one archive entry')
    root = result_root(ds, SOURCES[ds])
    embeddings = REPO / ('embeddings_extensions' if ds in {'SoilOriginal', 'KTHTIPS2b', 'Outex13Official1360'}
                         else 'embeddings' if ds == 'DTD' else 'embeddings_confirmatory')
    cache, y = load_dataset(REPO, ds, embedding_root=embeddings)
    groups, rows = load_manifest(root, ds, y)
    train, test = outer_split(entries[0], y, groups, rows)
    if not np.array_equal(test, predictions['test_indices']):
        raise ValueError('Archived test index mismatch')
    if not np.array_equal(y[test], predictions['y_true']):
        raise ValueError('Archived test labels mismatch')
    if set(groups[train]) & set(groups[test]):
        raise ValueError('Outer source-group overlap')
    selected = sample_stratified_test_indices(y[test], test, args.n_per_class, args.seed)
    paths, hashes, missing = {}, {}, []
    for idx in selected:
        row = rows[int(idx)]
        source_path = row.get('source_path') or row.get('path')
        if not source_path:
            raise ValueError(f'Manifest lacks image path at row {idx}')
        path = REPO / source_path
        if not path.is_file():
            missing.append(str(path))
            continue
        actual = digest(path)
        expected = row.get('source_sha256') or row.get('sha256')
        if not expected or actual != expected:
            raise ValueError(f'Source hash missing/mismatch: {path}')
        paths[int(idx)], hashes[int(idx)] = path, actual
    if missing:
        write_new(folder / 'status.json', {'status': 'blocked_missing_images', 'dataset': ds,
                  'protocol': protocol, 'missing': missing})
        return
    blocks = result['topk_blocks']
    if blocks != entries[0]['expensive_blocks']:
        raise ValueError('Top-k blocks differ from source archive')
    chosen = pretest['selected_cheap_stage']['selected']
    cheap = chosen.get('cheap') if chosen['route'] == 'cascade' else None
    names = list(dict.fromkeys(blocks + ([cheap] if cheap else [])))
    provenance = {str(p.relative_to(REPO)): digest(p) for p in sources}
    provenance[str(Path(__file__).relative_to(REPO))] = digest(__file__)
    for source in ['src/01_extract_features.py', 'src/extract_sota_2024.py', 'src/fsc_tex/executor.py']:
        provenance[source] = digest(REPO / source)
    write_new(folder / 'preflight.json', {'dataset': ds, 'protocol': protocol,
              'indices': selected.tolist(), 'source_sha256': hashes, 'blocks': blocks,
              'selection': chosen, 'provenance': provenance, 'repetitions': args.repeats,
              'seed': args.seed, 'timing_scope': 'decoded RGB to prediction, resident models',
              'kth_reference': 'historical variant; not corrected' if ds == 'KTHTIPS2b' else None})
    if args.preflight_only:
        write_new(folder / 'status.json', {'status': 'preflight_passed_not_measured', 'dataset': ds})
        return
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable; no silent CPU substitution')
    torch.manual_seed(args.seed)
    topk_model = make_model('svm', 42)
    topk_model.fit(np.concatenate([cache[b][train] for b in blocks], axis=1), y[train])
    cheap_model = None
    if cheap:
        cheap_model = make_model('svm', 42)
        cheap_model.fit(cache[cheap][train], y[train])
    funcs = {name: extractor(name, 'cuda') for name in names}
    print(ds, 'models loaded', names, flush=True)
    with Image.open(paths[int(selected[0])]) as image:
        warm = image.convert('RGB')
    for fn in funcs.values():
        for _ in range(3):
            fn(warm)
    torch.cuda.synchronize()

    def route(image, adaptive):
        acquired, escalate = {}, True
        if adaptive and cheap:
            acquired[cheap] = funcs[cheap](image)
            features = acquired[cheap][None, :]
            escalate = float(margin(cheap_model, features)[0]) <= chosen['threshold']
            if not escalate:
                return int(cheap_model.predict(features)[0]), False
        for block in blocks:
            if block not in acquired:
                acquired[block] = funcs[block](image)
        x = np.concatenate([acquired[b] for b in blocks])[None, :]
        return int(topk_model.predict(x)[0]), bool(escalate)

    rng = np.random.RandomState(args.seed)
    lookup = {int(idx): pos for pos, idx in enumerate(test)}
    measurements, parity = [], []
    with (folder / 'measurements.jsonl').open('x') as stream:
        for idx in rng.permutation(selected):
            idx = int(idx)
            with Image.open(paths[idx]) as image:
                image = image.convert('RGB')
            cosines = {}
            for name in names:
                observed, reference = funcs[name](image), cache[name][idx]
                cosines[name] = float(np.dot(observed, reference) / max(float(np.linalg.norm(reference)), 1e-12))
            parity.append({'index': idx, 'cosine': cosines})
            for rep in range(args.repeats):
                order = list(rng.permutation(['cascade', 'topk']))
                row = {'index': idx, 'class_id': int(y[idx]), 'repeat': rep, 'order': order}
                for name in order:
                    torch.cuda.synchronize()
                    start = time.perf_counter()
                    pred, escalated = route(image, name == 'cascade')
                    torch.cuda.synchronize()
                    row[name + '_ms'] = (time.perf_counter() - start) * 1000
                    row[name + '_pred'] = pred
                    if name == 'cascade':
                        row['escalated'] = escalated
                pos = lookup[idx]
                row['cascade_matches_cache'] = row['cascade_pred'] == predictions['y_pred_adaptive_cascade'][pos]
                row['topk_matches_cache'] = row['topk_pred'] == predictions['y_pred_topk_direct'][pos]
                row['route_matches_cache'] = row['escalated'] == predictions['requested_topk_adaptive'][pos]
                measurements.append(row)
                stream.write(json.dumps(row) + '\n')
                stream.flush()
            print(ds, 'image', len(parity), '/', len(selected), flush=True)
    a = np.mean([r['cascade_ms'] for r in measurements])
    b = np.mean([r['topk_ms'] for r in measurements])
    agreement = {key: float(np.mean([r[key] for r in measurements])) for key in
                 ['cascade_matches_cache', 'topk_matches_cache', 'route_matches_cache']}
    minimum_cosine = min(v for row in parity for v in row['cosine'].values())
    status = 'measured_matched_pilot' if min(agreement.values()) == 1 and minimum_cosine >= .999 else 'measured_with_fidelity_discrepancies'
    write_new(folder / 'parity.json', parity)
    write_new(folder / 'status.json', {'status': status, 'dataset': ds, 'protocol': protocol,
              'images': len(selected), 'pairs': len(measurements), 'mean_cascade_ms': float(a),
              'mean_topk_ms': float(b), 'ratio_sums': float(b/a), 'saving_pct': float(100*(1-a/b)),
              'agreement': agreement, 'minimum_cosine': minimum_cosine,
              'gpu': torch.cuda.get_device_name(0), 'torch': torch.__version__,
              'limits': ['One condition per dataset; stratified pilot, not full-test evaluation.',
                         'No Complete/GFS timing; repeated measurements are not independent images.',
                         'KTH uses its archived variant, not a reconciled corrected Top-k.']})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--dataset', choices=CONDITIONS)
    p.add_argument('--n-per-class', type=int, default=1)
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--timeout', type=int, default=1800)
    p.add_argument('--preflight-only', action='store_true')
    args = p.parse_args()
    if min(args.n_per_class, args.repeats, args.timeout) < 1:
        p.error('Counts and timeout must be positive')
    if args.dataset:
        run_condition(args)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    statuses = []
    for ds in CONDITIONS:
        command = [sys.executable, '-u', __file__, '--dataset', ds, '--output', str(args.output),
                   '--repeats', str(args.repeats), '--n-per-class', str(args.n_per_class), '--seed', str(args.seed)]
        if args.preflight_only:
            command.append('--preflight-only')
        with (args.output / (ds + '.log')).open('x') as log:
            try:
                completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
                status = {'dataset': ds, 'exit_code': completed.returncode}
            except subprocess.TimeoutExpired:
                status = {'dataset': ds, 'status': 'hard_timeout', 'timeout_seconds': args.timeout}
        statuses.append(status)
        print(status, flush=True)
    write_new(args.output / 'suite.json', statuses)


if __name__ == '__main__':
    main()
