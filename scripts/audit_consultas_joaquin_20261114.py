"""Audit existing records for Carlos's questions; no fits or new measurements."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/analysis/consultas_joaquin_20261114_v1'
PANEL = ROOT / 'results/analysis/blocker_resolution_20261101/full_panel_online_v1'
CASCADE = ROOT / 'results/exploratory/topk_cascade'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(output):
    if output.exists():
        raise FileExistsError('Choose a new audit directory')
    sources = {}

    def source(path):
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        relative = path.relative_to(ROOT).as_posix()
        sources[relative] = sha(path)
        return path

    def read_json(path):
        return json.loads(source(path).read_text())

    provenance = read_json(PANEL / 'provenance.json')
    coverage = read_json(PANEL / 'coverage.json')
    condition = pd.read_csv(source(PANEL / 'condition_summary.csv'))
    additional = ROOT / 'results/analysis/blocker_resolution_20261101/queue_v1/jobs/DTD_svm_s42_f6_additional/online/online_calls.csv'
    all_calls = {Path(p): h for p, h in provenance.items() if p.endswith('/online_calls.csv')}
    assert len(all_calls) == 95 and additional in all_calls
    canonical = []
    for path, expected in all_calls.items():
        if path == additional:
            continue
        assert sha(source(path)) == expected, path
        status = read_json(path.parent / 'status.json')
        identity = {key: status[key] for key in ['dataset', 'classifier', 'seed', 'outer_fold']}
        identity['seed'], identity['outer_fold'] = int(identity['seed']), int(identity['outer_fold'])
        identity['id'] = f"{identity['dataset']}_{identity['classifier']}_s{identity['seed']}_f{identity['outer_fold']}"
        calls = pd.read_csv(path)
        assert 'ms' in calls and np.isfinite(calls.ms).all()
        expected_rows = condition[condition.id.eq(identity['id'])]
        assert len(expected_rows) == 5 and len(calls) == int(expected_rows.calls.sum())
        canonical.append(identity | {'online_directory': path.parent.relative_to(ROOT).as_posix(),
                                      'calls_csv': path.relative_to(ROOT).as_posix(),
                                      'status_json': (path.parent / 'status.json').relative_to(ROOT).as_posix(),
                                      'sha256': expected, 'calls': len(calls)})
    canonical = pd.DataFrame(canonical).sort_values(['dataset', 'classifier', 'seed', 'outer_fold'])
    assert len(canonical) == canonical.id.nunique() == coverage['unique_conditions'] == 94
    assert int(canonical.calls.sum()) == coverage['primary_calls'] == 362640

    # Locate the Soil discrepancy without refitting or extracting anything.
    sweep = pd.read_csv(source('results/exploratory/k_sweep/soil_original/k_sweep.csv'))
    sweep = sweep[sweep.classifier.eq('svm') & sweep.k.eq(4)]
    soil = []
    for _, row in canonical[canonical.dataset.eq('SoilOriginal') & canonical.classifier.eq('svm')].iterrows():
        online_dir = ROOT / row.online_directory
        quality = online_dir.parent / 'quality'
        frozen = read_json(quality / 'frozen_decisions.json')
        cached = pd.read_csv(source(quality / 'metrics.csv'))
        cached = cached[cached.policy.eq('Top-4')].iloc[0]
        old = sweep[sweep.seed.eq(row.seed) & sweep.outer_fold.eq(row.outer_fold)].iloc[0]
        selected = frozen['recipes']['Top-4']['members'][0]
        assert selected == old.selected.split('+')
        assert abs(cached.macro_f1 - old.macro_f1) < 1e-12
        online = condition[condition.id.eq(row.id) & condition.method.eq('Top-4')].iloc[0]
        soil.append({'id': row.id, 'seed': int(row.seed), 'outer_fold': int(row.outer_fold),
                     'same_blocks_in_order': True, 'selected': '+'.join(selected),
                     'contains_vit_b16': 'vit_b16' in selected,
                     'static_f1': float(old.macro_f1), 'cached_panel_f1': float(cached.macro_f1),
                     'online_f1': float(online.macro_f1_online),
                     'online_minus_static': float(online.macro_f1_online-old.macro_f1),
                     'quality_directory': quality.relative_to(ROOT).as_posix()})
    soil = pd.DataFrame(soil)
    assert len(soil) == 15
    changed = soil.online_minus_static.abs().gt(1e-12)
    assert changed.sum() == 8 and soil.loc[changed, 'contains_vit_b16'].all()
    assert not soil.loc[~changed, 'contains_vit_b16'].any()

    parity = []
    for ds in ['DTD', 'FMD', 'CUReT', 'Outex13Official1360', 'SoilOriginal', 'KTHTIPS2b']:
        folder = ROOT / 'results/exploratory/fsc_tex/physical_six_20261012' / ds
        values = read_json(folder / 'parity.json')
        status = read_json(folder / 'status.json')
        assert len(values) == len({row['index'] for row in values}) == status['images']
        failing = [row for row in values if any(c < .99 for c in row['cosine'].values())]
        blocks = sorted({b for row in values for b, c in row['cosine'].items() if c < .99})
        parity.append({'dataset': ds, 'images': len(values), 'images_any_cosine_lt_0_99': len(failing),
                       'failing_blocks': '+'.join(blocks),
                       'minimum_cosine': min(c for row in values for c in row['cosine'].values()),
                       'temporal_pairs': int(status['pairs']), 'status': status['status']})
    parity = pd.DataFrame(parity)
    assert parity.images.sum() == 204 and parity.temporal_pairs.sum() == 612
    assert parity.set_index('dataset').loc['CUReT', 'images_any_cosine_lt_0_99'] == 61
    assert parity.set_index('dataset').loc['SoilOriginal', 'images_any_cosine_lt_0_99'] == 7

    random_rows = []
    archives = sorted(CASCADE.glob('*/exact_archive/*_topk_cascade.json'))
    assert len(archives) == 27
    for path in archives:
        record = read_json(path)
        assert record['cheap_blocks'] == ['resnet50']
        for budget in record['budgets']:
            assert budget['random_repeats'] == 100
            random_rows.append({'dataset': record['dataset'], 'protocol': record['protocol'],
                                'q': budget['target_budget'], 'margin_f1': budget['adaptive']['macro_f1'],
                                'random_mean_f1': budget['random_same_count_mean_macro_f1'],
                                'random_repeats': budget['random_repeats']})
    random_rows = pd.DataFrame(random_rows)
    random_summary = []
    for q, group in random_rows.groupby('q'):
        by_dataset = group.groupby('dataset')[['margin_f1', 'random_mean_f1']].mean()
        w = wilcoxon(by_dataset.margin_f1, by_dataset.random_mean_f1, alternative='two-sided', method='exact')
        assert len(group) == 27 and len(by_dataset) == 6
        random_summary.append({'q': float(q), 'conditions_winning_against_random_mean': int((group.margin_f1 > group.random_mean_f1).sum()),
                               'mean_margin_six_datasets': float(by_dataset.margin_f1.mean()),
                               'mean_random_six_datasets': float(by_dataset.random_mean_f1.mean()),
                               'wilcoxon_W': float(w.statistic), 'p_exact_two_sided': float(w.pvalue)})
    running = 0.0
    for i, row in enumerate(sorted(random_summary, key=lambda x: x['p_exact_two_sided'])):
        running = max(running, min(1.0, (len(random_summary)-i)*row['p_exact_two_sided']))
        row['p_holm_family_three_quantiles'] = running
    assert all(r['conditions_winning_against_random_mean'] == 27 and r['p_exact_two_sided'] == .03125
               and r['p_holm_family_three_quantiles'] == .09375 for r in random_summary)

    selected = pd.read_csv(source(CASCADE / 'cheap_stage_selected_primary22/rows.csv'))
    assert len(selected) == 27
    means = selected.groupby('dataset')[['new_f1', 'resnet_f1', 'topk_f1']].mean()
    ledger = pd.read_csv(source('results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.csv'))
    five = means.drop(index='KTHTIPS2b').copy()
    reference = ledger[~ledger.dataset.eq('KTHTIPS2b')].copy()
    assert len(reference) == 23 and reference.full_22_macro_f1.notna().all()
    five['full22_f1'] = reference.groupby('dataset').full_22_macro_f1.mean()
    friedman = friedmanchisquare(*(five[c].to_numpy() for c in five.columns))
    assert np.isclose(friedman.pvalue, .4517937789603155, atol=1e-10, rtol=0)
    statistics = {'random_control_original_resnet50': random_summary,
                  'selected_cascade_six_datasets_descriptive': means.mean().to_dict(),
                  'selected_cascade_five_datasets': five.mean().to_dict(),
                  'friedman_four_methods_five_datasets': {'chi2': float(friedman.statistic), 'p': float(friedman.pvalue)},
                  'aggregation': 'mean over conditions within dataset, then equal mean over datasets',
                  'complete22_kth_ledger_incomplete_not_used_for_a_complete_six_dataset_mean': True,
                  'no_rejection_is_not_equivalence': True}

    comparison = pd.read_csv(source('results/analysis/reconciliation_full_panel_20261104_v1/comparison_by_dataset.csv'))
    group = comparison.groupby(['dataset', 'classifier', 'local_method'])
    assert group.local_mean_ms.nunique().eq(1).all()
    times = comparison.drop_duplicates(['dataset', 'classifier', 'local_method']).pivot(
        index=['dataset', 'classifier'], columns='local_method', values='local_mean_ms')
    ratios = times[['Top-4', 'Ens-diversidad', 'Completa-22']].div(times['Adaptive-selection-margin'], axis=0)

    kth_old = pd.read_csv(source('results/extensions/kth_tips2b/ngram22_beitv2/topk_individual_control/nested_fold_results.csv'))
    kth_corrected = pd.read_csv(source('results/extensions/kth_tips2b/ngram22_beitv2_innergrp_sample_v1/topk_individual_control/nested_fold_results.csv'))
    kth_old = kth_old[kth_old.classifier.eq('svm') & kth_old.seed.eq(42)]
    kth_corrected = kth_corrected[kth_corrected.classifier.eq('svm') & kth_corrected.seed.eq(42)]
    assert len(kth_old) == len(kth_corrected) == 4
    kth = kth_old[['outer_fold', 'k', 'macro_f1', 'selected']].merge(
        kth_corrected[['outer_fold', 'k', 'macro_f1', 'selected']], on='outer_fold', suffixes=('_archived', '_corrected')).sort_values('outer_fold')
    assert (kth.selected_archived != kth.selected_corrected).all()

    profile_counts = {}
    for path in sorted((CASCADE / 'cheap_stage_selected_primary22').glob('*_result.json')):
        record = read_json(path)
        profile = record['cost_profile']
        profile_counts[profile] = profile_counts.get(profile, 0) + 1
    assert sorted(profile_counts.values()) == [4, 23]
    subset = read_json('results/analysis/topk_margin_rewrite_20261113_v1/top4_margin_subset.json')
    assert len(subset) == 5
    deep = read_json('results/analysis/deeplumina_convergence_review_20261104_v1/summary.json')

    output.mkdir(parents=True)
    outputs = {'canonical_panel_calls_94.csv': canonical, 'soil_top4_alignment_15.csv': soil,
               'physical_parity_by_dataset.csv': parity, 'random_control_original_81.csv': random_rows,
               'selected_cascade_five_dataset_means.csv': five.reset_index(),
               'timing_ratios.csv': ratios.reset_index(), 'kth_old_vs_corrected.csv': kth}
    for name, frame in outputs.items():
        frame.to_csv(output / name, index=False)
    (output / 'a11_statistics.json').write_text(json.dumps(statistics, ensure_ascii=False, indent=2) + '\n')
    summary = {'status': 'ANALYZED_FROM_SAVED_RECORDS', 'date': '2026-11-14', 'new_fits': 0,
               'new_extractions': 0, 'new_predictions': 0, 'new_timings': 0,
               'canonical_conditions': 94, 'canonical_calls': 362640,
               'excluded_additional_call_file': additional.relative_to(ROOT).as_posix(),
               'soil_static_mean_f1': float(soil.static_f1.mean()),
               'soil_cached_panel_mean_f1': float(soil.cached_panel_f1.mean()),
               'soil_online_mean_f1': float(soil.online_f1.mean()),
               'soil_block_identity_conditions': 15, 'soil_online_changed_conditions_with_vit': 8,
               'soil_exact_primary_cause': 'not diagnosed; discrepancy localized to online feature representation',
               'historical_cost_profile_counts': profile_counts,
               'matching_top4_rescue_conditions': 5,
               'B1_full_fixed4_panel': 'pending, not performed by this audit',
               'B2_alternative_confidence_gates': 'not located as an audited matched panel',
               'B3_same_archived_cascade_ResMLP': 'not located as an audited matched panel',
               'B4_fixed_top4_plus_ngram': 'pending specific control',
               'deeplumina_current_status_record': deep,
               'source_sha256': sources}
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    provenance_out = {'script_sha256': sha(__file__), 'source_sha256': sources,
                      'output_sha256': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output / 'provenance.json').write_text(json.dumps(provenance_out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': summary['status'], 'sources': len(sources), 'canonical_conditions': 94,
                      'soil_static_f1': summary['soil_static_mean_f1'], 'soil_online_f1': summary['soil_online_mean_f1'],
                      'friedman_p': float(friedman.pvalue), 'output': str(output.relative_to(ROOT))}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    main(parser.parse_args().output.resolve())
