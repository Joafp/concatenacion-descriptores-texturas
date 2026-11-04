"""Recalculate all saved canonical cascade predictions without fitting models."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import f1_score, accuracy_score

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT / 'results/exploratory/topk_cascade/cheap_stage_selected_primary22'
    rows, hashes = [], {}
    for p in sorted(source.glob('*_predictions.json')):
        a = json.loads(p.read_text())
        n = len(a['y_true'])
        assert n == a['n_test_samples'] == len(set(a['test_indices']))
        assert len(a['test_indices']) == n
        for name, key in [('adaptive_cascade', 'y_pred_adaptive_cascade'),
                          ('resnet50_cascade', 'y_pred_resnet50_cascade'),
                          ('topk_direct', 'y_pred_topk_direct')]:
            assert len(a[key]) == n
            f1 = f1_score(a['y_true'], a[key], average='macro', zero_division=0)
            acc = accuracy_score(a['y_true'], a[key])
            assert abs(f1 - a['metrics_recomputed'][name + '_macro_f1']) < 1e-12
            assert abs(acc - a['metrics_recomputed'][name + '_accuracy']) < 1e-12
            rows.append({'dataset': a['dataset'], 'protocol': a['protocol'],
                         'method': name, 'n': n, 'macro_f1': f1, 'accuracy': acc})
        hashes[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    assert len(hashes) == 27
    args.output.mkdir(parents=True, exist_ok=False)
    frame = pd.DataFrame(rows)
    frame.to_csv(args.output / 'metrics.csv', index=False)
    frame.groupby(['dataset', 'method'])[['macro_f1', 'accuracy']].mean().to_csv(args.output / 'dataset_means.csv')
    summary = {'status': 'ANALYZED', 'conditions': len(hashes), 'metric_rows': len(rows),
        'test_observations': int(frame[frame.method == 'adaptive_cascade'].n.sum()),
        'scope': 'saved-prediction recalculation, not historical split identity or model fitting certification',
        'input_sha256': hashes}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print({k: v for k, v in summary.items() if k != 'input_sha256'})


if __name__ == '__main__':
    main()
