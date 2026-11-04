"""Source-bound inventory of thesis tables and physical records; no model fits."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata, norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_primary22_beitv2_paper import load_sources, SOURCES_22, METHODS


def main():
    out = ROOT / 'results/analysis/thesis_reaudit_20261025'
    out.mkdir(parents=True, exist_ok=False)
    df = load_sources(SOURCES_22, 22)
    df.groupby(['dataset', 'classifier', 'method']).agg(
        n=('macro_f1', 'size'), f1=('macro_f1', 'mean'),
        accuracy=('accuracy', 'mean'), dimensions=('dimensions', 'mean')).to_csv(out / 'static_summary.csv')
    stat = []
    for clf in ('svm', 'resmlp'):
        x = df[df.classifier == clf].groupby(['dataset', 'method']).macro_f1.mean().unstack()[METHODS]
        ranks = np.array([rankdata(-r) for r in x.to_numpy()])
        f = friedmanchisquare(*[x[m].to_numpy() for m in METHODS])
        pairs = []
        for i in range(5):
            for j in range(i + 1, 5):
                z = abs(ranks.mean(axis=0)[i] - ranks.mean(axis=0)[j]) / np.sqrt(5 * 6 / (6 * len(x)))
                pairs.append((METHODS[i], METHODS[j], float(2 * norm.sf(z))))
        pairs.sort(key=lambda t: t[2])
        last = 0.
        for k, (a, b, p) in enumerate(pairs):
            last = min(1., max(last, (len(pairs) - k) * p))
            stat.append({'classifier': clf, 'a': a, 'b': b, 'p': p,
                         'p_holm': last, 'friedman_p': float(f.pvalue)})
    pd.DataFrame(stat).to_csv(out / 'static_statistics_recalculated.csv', index=False)
    physical = []
    base = ROOT / 'results/exploratory/fsc_tex/physical_six_20261012'
    for directory in sorted(p for p in base.iterdir() if p.is_dir()):
        rows = pd.DataFrame([json.loads(s) for s in (directory / 'measurements.jsonl').read_text().splitlines()])
        status = json.loads((directory / 'status.json').read_text())
        parity = json.loads((directory / 'parity.json').read_text())
        minimum = min(v for a in parity for v in a['cosine'].values())
        assert len(rows) == status['pairs'] and rows['index'].nunique() == status['images']
        assert rows.groupby('index')['repeat'].apply(lambda a: sorted(a) == [0, 1, 2]).all()
        assert abs(rows.cascade_ms.mean() - status['mean_cascade_ms']) < 1e-9
        assert abs(rows.topk_ms.mean() - status['mean_topk_ms']) < 1e-9
        assert abs(minimum - status['minimum_cosine']) < 1e-8
        physical.append({'dataset': directory.name, 'images': rows['index'].nunique(),
            'pairs': len(rows), 'cascade_ms': rows.cascade_ms.mean(), 'topk_ms': rows.topk_ms.mean(),
            'saving_pct': 100 * (1 - rows.cascade_ms.sum() / rows.topk_ms.sum()),
            'minimum_cosine': minimum, 'representation_flag': minimum < .999,
            'early_exits': int((~rows.escalated).sum())})
    pd.DataFrame(physical).to_csv(out / 'physical_recalculated.csv', index=False)
    inputs = [p / 'nested_fold_results.csv' for p in SOURCES_22]
    inputs += [p / 'topk_individual_control/nested_fold_results.csv' for p in SOURCES_22]
    inputs += list(base.glob('*/*.json')) + list(base.glob('*/*.jsonl'))
    inputs += [ROOT / 'paper/tesis.tex'] + list((ROOT / 'paper/chapters').glob('*.tex'))
    summary = {'status': 'ANALYZED', 'date': '2026-10-25', 'static_rows': len(df),
        'static_conditions_per_classifier': df[df.method == 'full_concat'].groupby('classifier').size().to_dict(),
        'physical_images': int(sum(p['images'] for p in physical)),
        'physical_pairs': int(sum(p['pairs'] for p in physical)),
        'representation_flags': [p['dataset'] for p in physical if p['representation_flag']],
        'scope': 'CSV/statistic and physical-record recalculation; not independent feature extraction or model fitting',
        'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print({k: v for k, v in summary.items() if k != 'input_sha256'})


if __name__ == '__main__':
    main()
