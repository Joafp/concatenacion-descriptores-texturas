"""Replay hybrid choices and audit saved routes; not independent model retraining."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score

from budgeted_rescue import acquisition_cost, select_policy
from carlos_hybrid import ensemble_scores, select_full_rescue
from fsc_tex.utility import compute_margins
from run_rescue_nested_selection import REPO, sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.run.resolve()
    meta = json.loads((root / 'metadata.json').read_text())
    assert meta['status'] == 'complete' and not meta['external_test_evaluated']
    for source, digest in meta['provenance']['source_sha256'].items():
        assert sha256_file(REPO / source) == digest, source
    for source, digest in meta['input_sha256'].items():
        assert sha256_file(REPO / source) == digest, source
    ref, cr = Path(meta['reference_run']), Path(meta['carlos_run'])
    refmeta = json.loads((ref / 'metadata.json').read_text())
    cfg = refmeta['provenance']['arguments']
    costprofile = meta['provenance']['cost_profile']
    costs, overhead = costprofile['per_descriptor_latency_ms'], costprofile['policy_overhead_ms']
    arrays = np.load(root / 'scores.npz', allow_pickle=False)
    original = np.load(ref / 'selection_oof_scores.npz', allow_pickle=False)
    vscores = np.load(cr / 'validation_scores.npz', allow_pickle=False)
    carlos = {r['producer_fold']: r for r in json.loads((cr / 'folds.json').read_text())}
    pred = pd.read_csv(root / 'predictions.csv')
    decisions = json.loads((root / 'selections.json').read_text())
    results = pd.read_csv(root / 'results.csv')
    reference_pred = pd.read_csv(ref / 'predictions.csv')
    labels_by_row = reference_pred.drop_duplicates('row_index').set_index('row_index').label
    assert np.array_equal(pred.label, labels_by_row.loc[pred.row_index].to_numpy())
    records, diagnostics = [], []
    allowed = set()
    for file in sorted(root.glob('fold*.json')):
        fold = json.loads(file.read_text())
        f = fold['producer_fold']
        prior = json.loads((ref / f'fold{f}.json').read_text())
        assert fold['fit_indices'] == prior['fit_indices'] == carlos[f]['fit_indices']
        assert fold['validation_indices'] == prior['validation_indices'] == carlos[f]['validation_indices']
        assert fold['selection_splits'] == prior['selection_splits']
        assert fold['members'] == carlos[f]['diversity_members']
        assert not set(fold['fit_indices']).intersection(fold['validation_indices'])
        allowed.update(fold['validation_indices'])
        assert np.array_equal(arrays[f'fold{f}_rows'], fold['fit_indices'])
        single = {n: original[f'fold{f}_single_scores'][i] for i, n in enumerate(prior['library_order'])}
        members = {tuple(m): arrays[f'fold{f}_member_scores'][i] for i, m in enumerate(fold['candidate_order'])}
        val_scores = {tuple(m): vscores[f'fold{f}_scores'][i] for i, m in enumerate(carlos[f]['unique_subset_order'])}
        y = original[f'fold{f}_labels']
        labels = np.unique(reference_pred.label)
        margins = {n: compute_margins(s) for n, s in single.items()}
        base_scores = dict(zip(arrays[f'fold{f}_validation_base_order'], arrays[f'fold{f}_validation_base_scores']))
        for d in [s for s in decisions if s['producer_fold'] == f]:
            policy = d['policy']
            actual = (select_full_rescue(single, members, fold['members'], y, labels, margins,
                        costs, d['budget_ms'], cfg['quantiles'], overhead)
                      if policy.startswith('full_') else select_policy(single, members, y, labels,
                        margins, costs, d['budget_ms'], cfg['quantiles'], cfg['max_members'],
                        overhead, 'marginal_cost' if policy.startswith('pruned_marginal') else 'relevance'))
            assert actual == {k: v for k, v in d.items() if k not in ('producer_fold', 'policy')}
            if not d['feasible']:
                continue
            s = d['selected']
            p = pred[(pred.producer_fold == f) & (pred.policy == policy)].set_index('row_index').loc[fold['validation_indices']]
            bp = labels[base_scores[s['base']].argmax(axis=1)]
            margin = compute_margins(base_scores[s['base']])
            gate = margin < s['threshold'] if s['members'] else np.zeros(len(p), dtype=bool)
            rp = labels[ensemble_scores(val_scores, s['members']).argmax(axis=1)] if s['members'] else bp
            assert np.array_equal(p.base_prediction, bp)
            np.testing.assert_allclose(p.base_margin, margin, atol=1e-12, rtol=0)
            assert np.array_equal(p.escalated, gate)
            assert np.array_equal(p.rescue_prediction, rp)
            assert np.array_equal(p.prediction, np.where(gate, rp, bp))
            union = {n for m in s['members'] for n in m} - {s['base']}
            cost = costs[s['base']] + (overhead + gate * sum(costs[n] for n in union) if s['members'] else np.zeros(len(p)))
            np.testing.assert_allclose(p.projected_ms, cost, atol=1e-9, rtol=0)
            assert np.array_equal(p.classifier_calls, 1 + gate * len({tuple(m) for m in s['members']}))
            traincost = acquisition_cost(s['base'], s['members'], s['training_escalation_fraction'], costs, overhead)
            assert abs(traincost - s['training_projected_ms']) < 1e-9 and traincost <= d['budget_ms'] + 1e-9
            records.append({'fold': f, 'policy': policy, 'replay_matches': True,
                'training_cost_ms': traincost, 'validation_cost_ms': float(cost.mean()),
                'budget_ms': d['budget_ms'], 'validation_budget_exceeded': bool(cost.mean() > d['budget_ms'] + 1e-9)})
            diagnostics.append({'fold': f, 'policy': policy, 'base': s['base'], 'routed': int(gate.sum()),
                'rows': len(p), 'unique_rescue_models': len({tuple(m) for m in s['members']}),
                'gate_corrected': int((gate & (bp != p.label.to_numpy()) & (rp == p.label.to_numpy())).sum()),
                'gate_harmed': int((gate & (bp == p.label.to_numpy()) & (rp != p.label.to_numpy())).sum())})
    cp = pd.read_csv(cr / 'predictions.csv')
    always = pred[pred.policy == 'carlos_diversity15_always'].set_index('row_index').sort_index()
    previous = cp[cp.policy == 'carlos_diversity15_soft'].set_index('row_index').sort_index()
    assert set(always.index) == allowed and always.index.is_unique
    assert np.array_equal(always.prediction, previous.prediction)
    np.testing.assert_allclose(always.projected_ms, previous.projected_ms, atol=1e-9, rtol=0)
    assert np.array_equal(always.classifier_calls, previous.unique_classifier_calls)
    for r in results.itertuples():
        p = pred[pred.policy == r.policy]
        assert r.complete_oof_coverage == (set(p.row_index) == allowed and p.row_index.is_unique)
        if r.complete_oof_coverage:
            assert abs(f1_score(p.label, p.prediction, average='macro', zero_division=0) - r.macro_f1_oof) < 1e-12
            assert abs(accuracy_score(p.label, p.prediction) - r.accuracy_oof) < 1e-12
            assert abs(p.projected_ms.mean() - r.projected_ms) < 1e-9
            assert abs(p.classifier_calls.mean() - r.classifier_calls) < 1e-12
    budget_rows = pd.read_csv(root / 'budget_checks.csv')
    assert len(budget_rows) == len(records)
    for r in records:
        saved = budget_rows[(budget_rows.producer_fold == r['fold']) & (budget_rows.policy == r['policy'])]
        assert len(saved) == 1
        saved = saved.iloc[0]
        assert abs(saved.training_cost_ms - r['training_cost_ms']) < 1e-9
        assert abs(saved.validation_cost_ms - r['validation_cost_ms']) < 1e-9
        assert saved.validation_budget_exceeded == r['validation_budget_exceeded']
    projections = json.loads((root / 'ngram_transforms.json').read_text())
    for a in projections:
        assert not set(a['train_indices']).intersection(a['evaluation_indices'])
        assert (set(a['train_indices']) | set(a['evaluation_indices'])).issubset(allowed)
        assert a['components'] == min(256, len(a['train_indices']) - 1, a['hash_bins'] - 1)
    args.output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(records).to_csv(args.output / 'selection_checks.csv', index=False)
    pd.DataFrame(diagnostics).to_csv(args.output / 'routing_diagnostics.csv', index=False)
    comparison = pd.concat([results.assign(family='carlos_hybrid'),
        pd.read_csv(ref / 'results.csv').assign(family='paired_pool_previous')], ignore_index=True)
    comparison.to_csv(args.output / 'comparison.csv', index=False)
    summary = {'status': 'ANALYZED', 'selections_replayed': len(decisions),
        'results_recalculated': len(results), 'ngram_projections': len(projections),
        'validation_budget_exceedances': sum(r['validation_budget_exceeded'] for r in records),
        'always_predictions_match_carlos': True, 'external_test_evaluated': False,
        'scope': 'saved-score replay and routing arithmetic; no independent fitting reproduction'}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
