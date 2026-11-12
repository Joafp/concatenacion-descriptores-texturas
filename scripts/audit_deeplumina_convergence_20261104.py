"""Audit existing solver warnings without changing execution receipts."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from audit_outex_crosscalls_20261104 import ANALYSIS, digest, read_json

MARKER = 'ConvergenceWarning: Liblinear failed to converge'
DATASETS = ('fmd', 'curet', 'outex', 'soil', 'kth', 'dtd')


def audit(output):
    output = Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    rows, provenance = [], {str(Path(__file__).resolve()): digest(Path(__file__))}
    for dataset in DATASETS:
        queue = ANALYSIS / f'deeplumina_{dataset}_external_queue_20261103_v1'
        worker_path = queue/'gpu.json'; worker = read_json(worker_path)
        manifest_path = queue/'manifest.json'
        for p in (worker_path, manifest_path): provenance[str(p)] = digest(p)
        if worker['status'] != 'all_tasks_terminal' or worker.get('current_task') is not None:
            raise ValueError(f'queue not terminal: {dataset}')
        for task, outcome in worker['outcomes'].items():
            state_path = queue/'tasks'/task/'state.json'
            log_path = queue/'tasks'/task/'stage_1.log'
            state = read_json(state_path)
            if state['status'] != outcome or state['manifest_sha256'] != digest(manifest_path):
                raise ValueError(f'state mismatch: {task}')
            if not log_path.is_file(): raise ValueError(f'missing training log: {task}')
            text = log_path.read_text(errors='replace')
            count = text.count(MARKER)
            for p in (state_path, log_path): provenance[str(p)] = digest(p)
            rows.append({'dataset': dataset, 'task': task, 'execution_status': outcome,
                         'liblinear_nonconvergence_warning_lines': count,
                         'scientific_review_required': bool(count or outcome != 'complete'),
                         'stage_1_log': str(log_path), 'stage_1_log_sha256': digest(log_path),
                         'state_sha256': digest(state_path)})
    counts = Counter(r['execution_status'] for r in rows)
    if len(rows) != 47 or counts != {'complete': 46, 'requires_review': 1}:
        raise ValueError('unexpected DeepLumina coverage/state')
    summary = {'status': 'DEEPLUMINA_CONVERGENCE_REVIEW_REQUIRED', 'conditions': len(rows),
        'execution_outcomes': dict(counts), 'complete_conditions_with_warnings':
            sum(r['execution_status'] == 'complete' and r['liblinear_nonconvergence_warning_lines'] > 0 for r in rows),
        'all_warning_lines': sum(r['liblinear_nonconvergence_warning_lines'] for r in rows),
        'scope': 'Warning lines are not independently counted learners; no claim about numerical impact without further evidence.',
        'action': 'Preserve predictions and states; inspect convergence and record scientific review, without automatic retry.'}
    output.mkdir(parents=True, exist_ok=False)
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    with (output/'conditions.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    audit(args.output)
