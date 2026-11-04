#!/usr/bin/env python3
"""Nested development pilot: Carlos diversity ensemble as fixed or pruned rescue."""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score

from budgeted_rescue import select_policy
from carlos_hybrid import ensemble_scores, select_full_rescue
from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS as LATENCIES, DEFAULT_POLICY_OVERHEAD_MS as OVERHEAD
from fsc_tex.utility import compute_margins
from run_confirmatory_nested import load_dataset, load_manifest, manifest_groups
from run_budgeted_rescue_paired import oof_scores
from run_rescue_nested_selection import REPO, COMMON_21, fit_scores, load_existing_ngram, launch_provenance, sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-run', type=Path, required=True)
    parser.add_argument('--carlos-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    def resolve(p):
        p = Path(p) if p else None
        return (REPO / p).resolve() if p and not p.is_absolute() else p
    ref, carlos, output = map(resolve, (args.reference_run, args.carlos_run, args.output))
    if output.exists() and any(output.iterdir()):
        parser.error('choose an empty output directory')
    meta, cm = [json.loads((p / 'metadata.json').read_text()) for p in (ref, carlos)]
    assert meta['status'] == cm['status'] == 'complete'
    assert meta['library'] == cm['library']
    for key in ('outer_train_indices_sha256', 'external_test_indices_sha256'):
        assert meta[key] == cm[key]
    for m in (meta, cm):
        for source, digest in m['provenance']['source_sha256'].items():
            assert sha256_file(REPO / source) == digest, source
    cfg = meta['provenance']['arguments']
    cache, y = load_dataset(REPO, meta['dataset'], resolve(cfg['embedding_root']))
    cache = {n: cache[n] for n in COMMON_21}
    manifest = resolve(cfg['manifest_root'])
    groups, rows = load_manifest(manifest, meta['dataset'], y)
    inner_groups = manifest_groups(rows, cfg['inner_group_column']) if cfg['inner_group_column'] else groups
    ng, ngp = (load_existing_ngram(rows, resolve(cfg['ngram_count_cache']), 256, 8192, cfg['seed'])
               if len(meta['library']) == 22 else (None, None))
    provenance = launch_provenance(args, manifest / 'sample_manifests' / f"{meta['dataset']}.csv",
        cache, y, {'per_descriptor_latency_ms': LATENCIES, 'policy_overhead_ms': OVERHEAD})
    for key in ('manifest_sha256', 'labels_sha256', 'embedding_array_sha256'):
        assert provenance[key] == meta['provenance'][key] == cm['provenance'][key], key
    assert ngp == meta['provenance']['ngram_count_cache'] == cm['provenance']['ngram_count_cache']
    provenance['ngram_count_cache'] = ngp
    for name in ('run_carlos_hybrid.py', 'carlos_hybrid.py', 'budgeted_rescue.py',
                 'run_budgeted_rescue_paired.py', 'run_carlos_paired_controls.py'):
        provenance['source_sha256']['src/' + name] = sha256_file(REPO / 'src' / name)
    input_hashes = {str(p.relative_to(REPO)): sha256_file(p)
        for root in (ref, carlos) for p in root.iterdir() if p.is_file()}
    metadata = {'status': 'running', 'dataset': meta['dataset'], 'library': meta['library'],
        'provenance': provenance, 'input_sha256': input_hashes,
        'reference_run': str(ref), 'carlos_run': str(carlos),
        'external_test_evaluated': False, 'classifier_latency_included': False,
        'scope': 'producer-validation score reuse; new internal OOF fits for diversity members; no external test',
        'selection_config': {'budgets_ms': cfg['budgets_ms'], 'quantiles': cfg['quantiles'],
                             'max_pruned_members': cfg['max_members']},
        'outer_train_indices_sha256': meta['outer_train_indices_sha256'],
        'external_test_indices_sha256': meta['external_test_indices_sha256']}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    start = time.perf_counter()
    labels = np.unique(y)
    saved = np.load(ref / 'selection_oof_scores.npz', allow_pickle=False)
    validation = np.load(carlos / 'validation_scores.npz', allow_pickle=False)
    records = json.loads((carlos / 'folds.json').read_text())
    predictions, decisions, checks, arrays = [], [], [], {}
    for record in records:
        f = record['producer_fold']
        fold = json.loads((ref / f'fold{f}.json').read_text())
        fit, val = np.array(fold['fit_indices']), np.array(fold['validation_indices'])
        assert record['fit_indices'] == fit.tolist() and record['validation_indices'] == val.tolist()
        assert np.array_equal(validation[f'fold{f}_rows'], val)
        assert not set(inner_groups[fit]).intersection(inner_groups[val])
        members = [tuple(m) for m in record['diversity_members']]
        candidates = sorted(set(members))
        existing = {tuple(m): saved[f'fold{f}_member_scores'][i]
                    for i, m in enumerate(fold['candidate_order'])}
        missing = [m for m in candidates if m not in existing]
        fresh, splits = oof_scores(cache, missing, fit, y, inner_groups, labels,
                                   cfg['seed'], cfg['selection_folds'], ng)
        assert splits == fold['selection_splits']
        internal = {m: existing[m] if m in existing else fresh[m] for m in candidates}
        singles = {n: saved[f'fold{f}_single_scores'][i] for i, n in enumerate(fold['library_order'])}
        margins = {n: compute_margins(s) for n, s in singles.items()}
        vscore = {tuple(m): validation[f'fold{f}_scores'][i]
                  for i, m in enumerate(record['unique_subset_order'])}
        base_cache = {}
        def base_scores(base):
            if base not in base_cache:
                base_cache[base] = fit_scores(cache, [base], fit, val, y, labels, cfg['seed'], ng)[0]
            return base_cache[base]
        full_pred = labels[np.argmax(ensemble_scores(vscore, members), axis=1)]
        union = {n for m in members for n in m}
        for i, row in enumerate(val):
            predictions.append({'row_index': int(row), 'label': int(y[row]), 'producer_fold': f,
                'policy': 'carlos_diversity15_always', 'prediction': int(full_pred[i]),
                'projected_ms': sum(LATENCIES[n] for n in union),
                'classifier_calls': len(candidates), 'escalated': True})
        for budget in cfg['budgets_ms']:
            for variant in ('full', 'pruned_marginal', 'pruned_relevance'):
                d = (select_full_rescue(singles, internal, members, y[fit], labels, margins,
                        LATENCIES, budget, cfg['quantiles'], OVERHEAD)
                     if variant == 'full' else select_policy(singles, internal, y[fit], labels,
                        margins, LATENCIES, budget, cfg['quantiles'], cfg['max_members'],
                        OVERHEAD, 'marginal_cost' if variant == 'pruned_marginal' else 'relevance'))
                policy = f'{variant}_B{budget:g}'
                decisions.append({'producer_fold': f, 'policy': policy, **d})
                if not d['feasible']:
                    continue
                s = d['selected']
                score = base_scores(s['base'])
                bp = labels[np.argmax(score, axis=1)]
                margin = compute_margins(score)
                gate = margin < s['threshold'] if s['members'] else np.zeros(len(val), dtype=bool)
                rp = (labels[np.argmax(ensemble_scores(vscore, s['members']), axis=1)]
                      if s['members'] else bp)
                pred = np.where(gate, rp, bp)
                extra = {n for m in s['members'] for n in m} - {s['base']}
                cost = LATENCIES[s['base']] + (OVERHEAD + gate * sum(LATENCIES[n] for n in extra)
                        if s['members'] else np.zeros(len(val)))
                calls = 1 + gate * len({tuple(m) for m in s['members']})
                checks.append({'producer_fold': f, 'policy': policy, 'budget_ms': budget,
                    'training_cost_ms': s['training_projected_ms'], 'validation_cost_ms': float(cost.mean()),
                    'validation_budget_exceeded': bool(cost.mean() > budget + 1e-10)})
                for i, row in enumerate(val):
                    predictions.append({'row_index': int(row), 'label': int(y[row]), 'producer_fold': f,
                        'policy': policy, 'prediction': int(pred[i]), 'base': s['base'],
                        'base_prediction': int(bp[i]), 'base_margin': float(margin[i]),
                        'rescue_prediction': int(rp[i]), 'escalated': bool(gate[i]),
                        'projected_ms': float(cost[i]), 'classifier_calls': int(calls[i])})
        arrays[f'fold{f}_rows'] = fit
        arrays[f'fold{f}_member_scores'] = np.stack([internal[m] for m in candidates])
        arrays[f'fold{f}_validation_base_order'] = np.array(sorted(base_cache))
        arrays[f'fold{f}_validation_base_scores'] = np.stack([base_cache[b] for b in sorted(base_cache)])
        (output / f'fold{f}.json').write_text(json.dumps({'producer_fold': f,
            'fit_indices': fit.tolist(), 'validation_indices': val.tolist(), 'selection_splits': splits,
            'members': [list(m) for m in members], 'candidate_order': [list(m) for m in candidates],
            'new_inner_candidate_fits': len(missing) * len(splits),
            'reused_inner_candidates': len(candidates) - len(missing)}, indent=2) + '\n')
        print(f'completed hybrid fold {f}: {len(candidates)} unique diversity models', flush=True)
    pred = pd.DataFrame(predictions)
    expected = len({i for r in records for i in r['validation_indices']})
    results = []
    policies = ['carlos_diversity15_always'] + [f'{v}_B{b:g}' for b in cfg['budgets_ms']
        for v in ('full', 'pruned_marginal', 'pruned_relevance')]
    for name in policies:
        p = pred[pred.policy == name]
        complete = len(p) == p.row_index.nunique() == expected
        results.append({'policy': name, 'complete_oof_coverage': complete, 'n_rows': len(p),
            'macro_f1_oof': f1_score(p.label, p.prediction, average='macro', zero_division=0) if complete else None,
            'accuracy_oof': accuracy_score(p.label, p.prediction) if complete else None,
            'projected_ms': p.projected_ms.mean() if complete else None,
            'classifier_calls': p.classifier_calls.mean() if complete else None})
    pred.to_csv(output / 'predictions.csv', index=False)
    pd.DataFrame(results).to_csv(output / 'results.csv', index=False)
    pd.DataFrame(checks).to_csv(output / 'budget_checks.csv', index=False)
    (output / 'selections.json').write_text(json.dumps(decisions, indent=2) + '\n')
    np.savez_compressed(output / 'scores.npz', **arrays)
    audits = ng.transformation_audits() if ng else []
    allowed = {i for r in records for i in r['validation_indices']}
    for a in audits:
        assert not set(a['train_indices']).intersection(a['evaluation_indices'])
        assert (set(a['train_indices']) | set(a['evaluation_indices'])).issubset(allowed)
    (output / 'ngram_transforms.json').write_text(json.dumps(audits, indent=2) + '\n')
    metadata.update(status='complete', elapsed_seconds=time.perf_counter()-start)
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(pd.DataFrame(results).to_string(index=False))


if __name__ == '__main__':
    main()
