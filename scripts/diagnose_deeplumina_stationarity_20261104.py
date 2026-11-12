"""Inspect primal gradients of saved DeepLumina binary heads; never refit."""
import argparse
from collections import defaultdict
import csv
import importlib.metadata
import json
from pathlib import Path
import sys

import joblib
import numpy as np

from audit_outex_crosscalls_20261104 import ANALYSIS, ROOT, digest, read_json

DATASETS = ('fmd', 'curet', 'outex', 'soil', 'kth', 'dtd')


def primal_objective_and_gradient(x, targets, weights, intercepts, c=1.0, intercept_scaling=1.0):
    """L2-regularized squared hinge; target zero excludes a row for that learner."""
    x = np.asarray(x, dtype=np.float64)
    targets = np.asarray(targets, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    intercepts = np.asarray(intercepts, dtype=np.float64)
    if (x.ndim != 2 or targets.ndim != 2 or weights.ndim != 2 or
            targets.shape != (x.shape[0], weights.shape[0]) or
            weights.shape[1] != x.shape[1] or intercepts.shape != (weights.shape[0],)):
        raise ValueError('incompatible input dimensions')
    if (not np.isin(targets, (-1, 0, 1)).all() or c <= 0 or intercept_scaling <= 0 or
            not all(np.isfinite(a).all() for a in (x, targets, weights, intercepts))):
        raise ValueError('invalid features, targets, coefficients or hyperparameters')
    if np.any(np.sum(targets == 1, axis=0) == 0) or np.any(np.sum(targets == -1, axis=0) == 0):
        raise ValueError('each learner requires both signs')
    margins = targets * (x @ weights.T + intercepts)
    hinge = np.maximum(0.0, 1.0 - margins) * (targets != 0)
    loss = 0.5 * (np.sum(weights * weights, axis=1) + (intercepts / intercept_scaling) ** 2)
    loss += c * np.sum(hinge * hinge, axis=0)
    grad_weights = weights - 2.0 * c * ((targets * hinge).T @ x)
    grad_intercepts = intercepts / (intercept_scaling ** 2) - 2.0 * c * np.sum(targets * hinge, axis=0)
    return loss, grad_weights, grad_intercepts


def gradient_ratio(x, targets, weights, intercepts, c=1.0, intercept_scaling=1.0):
    loss, grad_w, grad_b = primal_objective_and_gradient(x, targets, weights, intercepts, c, intercept_scaling)
    _, initial_w, initial_b = primal_objective_and_gradient(
        x, targets, np.zeros_like(weights), np.zeros_like(intercepts), c, intercept_scaling)
    norm = np.sqrt(np.sum(grad_w * grad_w, axis=1) + grad_b * grad_b)
    initial_norm = np.sqrt(np.sum(initial_w * initial_w, axis=1) + initial_b * initial_b)
    ratio = np.divide(norm, initial_norm, out=np.full_like(norm, np.nan), where=initial_norm > 0)
    return loss, norm, initial_norm, ratio


def run(output):
    output = Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    code = ROOT/'src/deeplumina_reference.py'
    provenance = {str(Path(__file__).resolve()): digest(Path(__file__)), str(code): digest(code)}
    learner_rows, condition_rows = [], []
    missing = []
    for dataset in DATASETS:
        queue = ANALYSIS/f'deeplumina_{dataset}_external_queue_20261103_v1'
        manifest_path, worker_path = queue/'manifest.json', queue/'gpu.json'
        manifest, worker = read_json(manifest_path), read_json(worker_path)
        if manifest['source_sha256'].get(str(code)) != digest(code): raise ValueError(f'code drift: {dataset}')
        for p in (manifest_path, worker_path): provenance[str(p)] = digest(p)
        for task, outcome in worker['outcomes'].items():
            if outcome != 'complete':
                missing.append({'dataset': dataset, 'task': task, 'execution_status': outcome})
                continue
            job, state_path = queue/'jobs'/task, queue/'tasks'/task/'state.json'
            state = read_json(state_path)
            if state['status'] != 'complete' or state['manifest_sha256'] != digest(manifest_path):
                raise ValueError(f'state mismatch: {task}')
            extract_path, train_path = job/'extract/status.json', job/'train/status.json'
            extract, train = read_json(extract_path), read_json(train_path)
            features_path, head_path = job/'extract/features.npz', job/'train/head.joblib'
            for status_path, status, name, payload in ((extract_path, extract, 'features.npz', features_path),
                                                       (train_path, train, 'head.joblib', head_path)):
                receipts = [r for r in state['success_artifacts'] if r['path'] == str(status_path)]
                if len(receipts) != 1 or receipts[0]['sha256'] != digest(status_path):
                    raise ValueError(f'status receipt mismatch: {task}')
                if status['output_sha256'][name] != digest(payload):
                    raise ValueError(f'payload checksum mismatch: {task}')
            for p in (state_path, extract_path, train_path, features_path, head_path): provenance[str(p)] = digest(p)
            with np.load(features_path, allow_pickle=False) as data:
                indices = data['rows'].astype(np.int64)
                x = np.asarray(data['features'], dtype=np.float64)
            partition = extract['partition']
            if not np.array_equal(indices, np.asarray(partition['training_indices'], dtype=np.int64)):
                raise ValueError(f'training index mismatch: {task}')
            manifest_csv = Path(partition['manifest']); provenance[str(manifest_csv)] = digest(manifest_csv)
            with manifest_csv.open(newline='') as stream:
                labels = {int(row['row_id']): int(row['label']) for row in csv.DictReader(stream)}
            y = np.asarray([labels[int(i)] for i in indices], dtype=np.int64)
            head = joblib.load(head_path)
            label_rows = {int(label): i for i, label in enumerate(head.labels)}
            targets = np.asarray(head.coding_matrix[[label_rows[int(label)] for label in y], :], dtype=np.float64)
            if len(head.estimators) != targets.shape[1] or x.shape[1] != 2000:
                raise ValueError(f'head/feature dimension mismatch: {task}')
            for estimator in head.estimators:
                params = estimator.get_params()
                if (params['C'] != 1.0 or params['loss'] != 'squared_hinge' or
                    params['penalty'] != 'l2' or params['dual'] is not True or
                    params['class_weight'] is not None or not params['fit_intercept'] or
                    params['intercept_scaling'] != 1 or list(estimator.classes_) != [-1, 1]):
                    raise ValueError(f'unsupported solver configuration: {task}')
            weights = np.vstack([est.coef_.reshape(-1) for est in head.estimators])
            intercepts = np.asarray([float(est.intercept_[0]) for est in head.estimators])
            loss, norm, norm0, ratios = gradient_ratio(x, targets, weights, intercepts)
            if not np.isfinite(ratios).all(): raise ValueError(f'undefined diagnostic: {task}')
            caps = np.asarray([int(est.n_iter_) >= int(est.max_iter) for est in head.estimators])
            for i, estimator in enumerate(head.estimators):
                learner_rows.append({'dataset': dataset, 'task': task, 'learner_column': i,
                    'n_iter': int(estimator.n_iter_), 'max_iter': int(estimator.max_iter), 'at_max_iter': bool(caps[i]),
                    'primal_objective': float(loss[i]), 'primal_gradient_l2': float(norm[i]),
                    'origin_gradient_l2': float(norm0[i]), 'gradient_ratio_to_origin': float(ratios[i])})
            condition_rows.append({'dataset': dataset, 'task': task, 'n_train': len(indices),
                'learners': len(caps), 'at_max_iter': int(caps.sum()),
                'median_gradient_ratio_capped': float(np.median(ratios[caps])) if caps.any() else None,
                'median_gradient_ratio_not_capped': float(np.median(ratios[~caps])) if (~caps).any() else None,
                'max_gradient_ratio': float(ratios.max())})
    if len(condition_rows) != 46 or len(learner_rows) != 2441 or len(missing) != 1:
        raise ValueError('unexpected coverage')
    totals = defaultdict(list)
    for row in learner_rows: totals[(row['dataset'], row['at_max_iter'])].append(row['gradient_ratio_to_origin'])
    dataset_summary = {}
    for dataset in DATASETS:
        capped, other = totals[(dataset, True)], totals[(dataset, False)]
        dataset_summary[dataset] = {'capped_count': len(capped), 'not_capped_count': len(other),
            'median_gradient_ratio_capped': float(np.median(capped)) if capped else None,
            'median_gradient_ratio_not_capped': float(np.median(other)) if other else None}
    summary = {'status': 'SAVED_TRAINING_PRIMAL_GRADIENTS_INSPECTED_REVIEW_REQUIRED',
        'complete_conditions': len(condition_rows), 'learners': len(learner_rows), 'missing': missing,
        'training_features_only': True, 'refit_or_test_inference': False,
        'definition': 'norm(primal gradient at saved solution) / norm(primal gradient at zero), L2 squared hinge with regularized intercept',
        'interpretation': 'Descriptive stationarity diagnostic; not the liblinear dual stopping test, not an F1-impact estimate, and no threshold asserts convergence.',
        'sources': ['https://github.com/cjlin1/liblinear/blob/master/README',
                    'https://www.csie.ntu.edu.tw/~cjlin/liblinear/FAQ_src.html',
                    'https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html'],
        'python': sys.version, 'numpy': importlib.metadata.version('numpy'),
        'scikit_learn': importlib.metadata.version('scikit-learn'), 'datasets': dataset_summary}
    output.mkdir(parents=True, exist_ok=False)
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    for name, rows in [('learners.csv', learner_rows), ('conditions.csv', condition_rows)]:
        with (output/name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', required=True)
    args = parser.parse_args(); run(args.output)
