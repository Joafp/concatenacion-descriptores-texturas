"""Check matched pools and partitions; summarize saved development predictions."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from run_budgeted_rescue_paired import candidate_pool
from run_rescue_nested_selection import sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plain', type=Path, required=True)
    parser.add_argument('--color', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    roots = [args.plain, args.color]
    metas = [json.loads((p / 'metadata.json').read_text()) for p in roots]
    assert all(m['status'] == 'complete' for m in metas)
    assert all(m['candidate_pool_version'] == 'paired_static_core_v1' for m in metas)
    for field in ('outer_train_indices_sha256', 'external_test_indices_sha256'):
        assert metas[0][field] == metas[1][field]
    assert all(not m['external_test_evaluated'] for m in metas)
    configs = [m['provenance']['arguments'] for m in metas]
    for key in configs[0]:
        if key not in ('library', 'ngram_count_cache', 'output'):
            assert configs[0][key] == configs[1][key], key
    checks = []
    for file in sorted(roots[0].glob('fold*.json')):
        folds = [json.loads((p / file.name).read_text()) for p in roots]
        for field in ('fit_indices', 'validation_indices', 'selection_splits'):
            assert folds[0][field] == folds[1][field]
        ranks = [[n for n in f['ranked_blocks'] if n != 'rgb_ngram_svd'] for f in folds]
        assert ranks[0] == ranks[1]
        pools = [{tuple(s) for s in f['candidate_order']} for f in folds]
        assert pools[0] == {s for s in pools[1] if 'rgb_ngram_svd' not in s}
        assert pools[1] == pools[0] | {tuple(sorted((*s, 'rgb_ngram_svd'))) for s in pools[0]}
        assert tuple(sorted(ranks[0][:2])) in pools[0]
        fold_id = int(file.stem.removeprefix('fold'))
        for i, cfg in enumerate(configs):
            expected = candidate_pool(folds[i]['ranked_blocks'],
                cfg['seed'] * 10000 + cfg['fold'] * 100 + fold_id,
                cfg['candidate_draws'], cfg['subset_size'], i == 1)
            assert set(expected) == pools[i]
        arrays = [np.load(p / 'selection_oof_scores.npz') for p in roots]
        common = folds[0]['library_order']
        for j, name in enumerate(common):
            k = folds[1]['library_order'].index(name)
            np.testing.assert_allclose(arrays[0][f'fold{fold_id}_single_scores'][j],
                arrays[1][f'fold{fold_id}_single_scores'][k], atol=1e-12, rtol=0)
        for subset in pools[0]:
            positions = [f['candidate_order'].index(list(subset)) for f in folds]
            np.testing.assert_allclose(arrays[0][f'fold{fold_id}_member_scores'][positions[0]],
                arrays[1][f'fold{fold_id}_member_scores'][positions[1]], atol=1e-12, rtol=0)
        checks.append({'fold': fold_id, 'plain_candidates': len(pools[0]),
                       'color_candidates': len(pools[1]), 'matched': True})
    frames = []
    for root, library in zip(roots, (21, 22)):
        result = pd.read_csv(root / 'results.csv')
        predictions = pd.read_csv(root / 'predictions.csv')
        for row in result.itertuples():
            p = predictions[predictions.policy == row.policy]
            if row.complete_oof_coverage:
                actual = f1_score(p.label, p.prediction, average='macro', zero_division=0)
                assert abs(actual - row.macro_f1_oof) < 1e-12
                assert p.row_index.nunique() == row.n_rows
        result.insert(0, 'library', library)
        frames.append(result)
    args.output.mkdir(parents=True, exist_ok=False)
    pd.concat(frames).to_csv(args.output / 'comparison.csv', index=False)
    pd.DataFrame(checks).to_csv(args.output / 'pool_checks.csv', index=False)
    summary = {'status': 'ANALYZED', 'matched_folds': len(checks),
               'result_rows': sum(len(f) for f in frames),
               'external_test_evaluated': False,
               'input_metadata_sha256': {str(p): sha256_file(p / 'metadata.json') for p in roots}}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
