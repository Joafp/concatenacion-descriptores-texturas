"""Inspect saved, hash-verified DeepLumina heads without training or inference."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path

import joblib

from audit_outex_crosscalls_20261104 import ANALYSIS, ROOT, digest, read_json

DATASETS = ('fmd', 'curet', 'outex', 'soil', 'kth', 'dtd')
WARNING = 'ConvergenceWarning: Liblinear failed to converge'


def audit(output):
    output = Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    code = ROOT/'src/deeplumina_reference.py'
    provenance = {str(Path(__file__).resolve()): digest(Path(__file__)), str(code): digest(code)}
    rows = []
    for dataset in DATASETS:
        queue = ANALYSIS/f'deeplumina_{dataset}_external_queue_20261103_v1'
        manifest_path = queue/'manifest.json'; manifest = read_json(manifest_path)
        worker_path = queue/'gpu.json'; worker = read_json(worker_path)
        if manifest['source_sha256'].get(str(code)) != digest(code):
            raise ValueError(f'code hash drift: {dataset}')
        for p in (manifest_path, worker_path): provenance[str(p)] = digest(p)
        for task, outcome in worker['outcomes'].items():
            if outcome != 'complete': continue
            state_path = queue/'tasks'/task/'state.json'; state = read_json(state_path)
            train_path = queue/'jobs'/task/'train/status.json'; train = read_json(train_path)
            head_path = queue/'jobs'/task/'train/head.joblib'
            log_path = queue/'tasks'/task/'stage_1.log'
            if state['status'] != 'complete' or state['manifest_sha256'] != digest(manifest_path):
                raise ValueError(f'state mismatch: {task}')
            receipts = [x for x in state['success_artifacts'] if x['path'] == str(train_path)]
            if len(receipts) != 1 or receipts[0]['sha256'] != digest(train_path):
                raise ValueError(f'train receipt mismatch: {task}')
            if train['status'] != 'train_complete' or train['output_sha256']['head.joblib'] != digest(head_path):
                raise ValueError(f'head checksum mismatch: {task}')
            for p in (state_path, train_path, head_path, log_path): provenance[str(p)] = digest(p)
            head = joblib.load(head_path)
            if not head.estimators: raise ValueError(f'no fitted estimators: {task}')
            iterations = [int(e.n_iter_) for e in head.estimators]
            limits = [int(e.max_iter) for e in head.estimators]
            capped = sum(n >= limit for n, limit in zip(iterations, limits))
            warnings = log_path.read_text(errors='replace').count(WARNING)
            rows.append({'dataset': dataset, 'task': task, 'estimators': len(iterations),
                'estimators_at_max_iter': capped, 'max_iter_setting': max(limits),
                'max_observed_iter': max(iterations), 'warning_lines': warnings,
                'warnings_equal_capped_estimators': warnings == capped,
                'head_sha256': digest(head_path)})
    if len(rows) != 46: raise ValueError('expected 46 complete heads')
    totals = defaultdict(lambda: {'conditions': 0, 'estimators': 0, 'estimators_at_max_iter': 0,
                                  'warning_lines': 0, 'conditions_warning_count_mismatch': 0})
    for r in rows:
        t = totals[r['dataset']]; t['conditions'] += 1
        for key in ('estimators', 'estimators_at_max_iter', 'warning_lines'): t[key] += r[key]
        t['conditions_warning_count_mismatch'] += not r['warnings_equal_capped_estimators']
    summary = {'status': 'DEEPLUMINA_CONVERGENCE_REVIEW_REQUIRED', 'complete_heads_inspected': len(rows),
        'estimators': sum(r['estimators'] for r in rows),
        'estimators_at_max_iter': sum(r['estimators_at_max_iter'] for r in rows),
        'conditions_with_at_least_one_at_max_iter': sum(r['estimators_at_max_iter'] > 0 for r in rows),
        'conditions_warning_count_mismatch': sum(not r['warnings_equal_capped_estimators'] for r in rows),
        'datasets': dict(totals), 'dtd_missing_condition': 's42_f3 timed out; no trained head to inspect',
        'limitations': 'Reaching max_iter and solver warnings identify an unresolved convergence issue; they do not quantify its effect on F1 or timings.',
        'no_fit_or_inference': True}
    output.mkdir(parents=True, exist_ok=False)
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    with (output/'conditions.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', required=True)
    args = parser.parse_args(); audit(args.output)
