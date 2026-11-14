"""Render all saved k values and marginal gains; no fitting or inference."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'results/analysis/topk_margin_rewrite_20261113_v1'
ORDER = ['DTD', 'FMD', 'CUReT', 'Outex13Official1360', 'SoilOriginal', 'KTHTIPS2b']
NAMES = ['DTD', 'FMD', 'CUReT', 'Outex-13', 'Soil', 'KTH-TIPS2b (reserva)']
COLORS = {'svm': '#176c84', 'resmlp': '#b76b20'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(output, generated):
    if output.exists() or generated.exists():
        raise FileExistsError('Choose new output and generated directories')
    original = json.loads((AUDIT / 'summary.json').read_text())
    sources = {str((AUDIT / 'summary.json').relative_to(ROOT)): sha(AUDIT / 'summary.json'),
               str((AUDIT / 'curves.csv').relative_to(ROOT)): sha(AUDIT / 'curves.csv')}
    curve = pd.read_csv(AUDIT / 'curves.csv')
    assert len(curve) == 42 and not curve.duplicated(['classifier', 'k']).any()
    assert curve.conditions.eq(47).all()
    frames, per_dataset, stats = {}, [], []
    for clf, prefix in [('svm', 'results/exploratory/k_sweep'),
                        ('resmlp', 'results/exploratory/resmlp/k_sweep')]:
        paths = sorted((ROOT / prefix).glob('*/k_sweep.csv'))
        assert len(paths) == 6
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            assert sha(path) == original['source_sha256'][relative], relative
            sources[relative] = sha(path)
        frame = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
        assert len(frame) == 987 and frame.classifier.eq(clf).all()
        assert not frame.duplicated(['dataset', 'seed', 'outer_fold', 'k']).any()
        assert frame.groupby('k').size().eq(47).all()
        grouped = frame.groupby(['dataset', 'k'])[['macro_f1', 'pct_dimensions']].mean().reset_index()
        assert set(grouped.dataset) == set(ORDER) and len(grouped) == 126
        grouped['classifier'] = clf
        per_dataset.append(grouped)
        global_curve = grouped.groupby('k').macro_f1.mean()
        local = curve[curve.classifier.eq(clf)].sort_values('k').copy()
        assert np.allclose(global_curve.to_numpy(), local.macro_f1.to_numpy(), atol=1e-12, rtol=0)
        local['gain_pp_vs_previous_k'] = local.macro_f1.diff() * 100
        frames[clf] = local
        first, four, peak = (local[local.k.eq(k)].iloc[0] for k in
                             [1, 4, int(local.loc[local.macro_f1.idxmax(), 'k'])])
        stats.append({'classifier': clf, 'f1_k1': float(first.macro_f1),
                      'f1_k4': float(four.macro_f1), 'peak_k': int(peak.k),
                      'peak_f1': float(peak.macro_f1),
                      'gain_1_to_4_pp': float(100 * (four.macro_f1 - first.macro_f1)),
                      'gap_4_to_peak_pp': float(100 * (peak.macro_f1 - four.macro_f1)),
                      'fraction_of_gain_1_to_peak_at_4': float((four.macro_f1-first.macro_f1)/(peak.macro_f1-first.macro_f1)),
                      'dimensions_pct_k4': float(four.pct_dimensions_vs_21),
                      'dimensions_pct_peak': float(peak.pct_dimensions_vs_21),
                      'negative_steps_after_4': int((local[local.k.gt(4)].gain_pp_vs_previous_k < 0).sum()),
                      'positive_steps_after_4': int((local[local.k.gt(4)].gain_pp_vs_previous_k > 0).sum())})
    per = pd.concat(per_dataset, ignore_index=True)
    gains = pd.concat(frames.values(), ignore_index=True)
    gains = gains[gains.k.gt(1)].copy()
    example = pd.concat([pd.read_csv(p) for p in sorted((ROOT / 'results/exploratory/k_sweep').glob('*/k_sweep.csv'))])
    example = example[example.dataset.eq('FMD') & example.seed.eq(42) & example.outer_fold.eq(0) & example.k.eq(4)].iloc[0]
    output.mkdir(parents=True)
    generated.mkdir(parents=True)
    gains.to_csv(output / 'marginal_gains.csv', index=False)
    per.to_csv(output / 'per_dataset_curves.csv', index=False)
    summary = {'status': 'ANALYZED', 'new_fits': 0, 'new_predictions': 0, 'new_timings': 0,
               'estimand': 'mean within dataset, then equal mean across six datasets',
               'curve_axis': 'number of selected descriptor blocks, not training samples or epochs',
               'non_monotonic_after_four': True, 'statistics': stats,
               'example': {name: (int(example[name]) if name in ['k', 'dimensions', 'seed', 'outer_fold'] else example[name])
                           for name in ['dataset', 'seed', 'outer_fold', 'k', 'selected', 'dimensions']},
               'source_sha256': sources}
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.0), layout='constrained')
    for clf, local in frames.items():
        label = 'SVM' if clf == 'svm' else 'ResMLP'
        axes[0].plot(local.k, local.macro_f1 * 100, '.-', label=label, color=COLORS[clf], lw=1.5)
        four = local[local.k.eq(4)].iloc[0]
        axes[0].scatter([4], [four.macro_f1 * 100], facecolor='white', edgecolor=COLORS[clf], s=65, zorder=5)
        peak = local.loc[local.macro_f1.idxmax()]
        axes[0].annotate(f'Máximo {label}: k={int(peak.k)}', (peak.k, peak.macro_f1 * 100),
                         xytext=(8, 8 if clf == 'svm' else -22), textcoords='offset points', fontsize=8,
                         arrowprops={'arrowstyle': '-', 'color': COLORS[clf]}, color=COLORS[clf])
        added = local[local.k.gt(1)]
        offset = -.18 if clf == 'svm' else .18
        axes[1].bar(added.k + offset, added.gain_pp_vs_previous_k, width=.35, color=COLORS[clf], label=label)
    for ax in axes:
        ax.axvline(4, color='#666666', ls='--', lw=1)
        ax.set(xlabel='Número de descriptores k', xticks=[1, 2, 3, 4, 5, 7, 10, 15, 21], xlim=(.6, 21.6))
        ax.grid(axis='y', alpha=.2)
    axes[0].set(ylabel='Macro-F1 medio (%)', title='Calidad al ampliar la concatenación')
    axes[1].set(ylabel='Cambio frente a k anterior (puntos porcentuales)', title='Ganancia de cada bloque adicional')
    axes[1].axhline(0, color='#555555', lw=.8)
    axes[0].legend(loc='lower right', frameon=False)
    axes[1].legend(frameon=False)
    for suffix in ['pdf', 'png']:
        fig.savefig(generated / f'ganancias_k.{suffix}', dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(10.4, 6.6), layout='constrained')
    for ax, ds, name in zip(axes.flat, ORDER, NAMES):
        for clf in ['svm', 'resmlp']:
            local = per[per.dataset.eq(ds) & per.classifier.eq(clf)].sort_values('k')
            ax.plot(local.k, local.macro_f1 * 100, '.-', color=COLORS[clf], lw=1.2, ms=3,
                    label='SVM' if clf == 'svm' else 'ResMLP')
            four = local[local.k.eq(4)].iloc[0]
            ax.scatter([4], [four.macro_f1 * 100], facecolor='white', edgecolor=COLORS[clf], s=40, zorder=5)
        ax.axvline(4, color='#666666', ls='--', lw=.8)
        ax.set(title=name, xlabel='k descriptores', ylabel='Macro-F1 (%)', xticks=[1, 4, 10, 15, 21])
        ax.grid(alpha=.2)
    axes[0, 0].legend(frameon=False, fontsize=8)
    for suffix in ['pdf', 'png']:
        fig.savefig(generated / f'curvas_por_dataset.{suffix}', dpi=180)
    plt.close(fig)
    provenance = {'builder_sha256': sha(__file__), 'source_sha256': sources,
                  'output_sha256': {p.relative_to(ROOT).as_posix(): sha(p)
                                    for directory in [output, generated] for p in sorted(directory.iterdir())}}
    (output / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary['statistics'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/analysis/topk_marginal_gains_20261113_v1')
    parser.add_argument('--generated', type=Path, default=ROOT / 'paper/generated_topk_progression')
    args = parser.parse_args()
    build(args.output.resolve(), args.generated.resolve())
