"""Assemble a traceable comparison from completed cross-call audits."""
import argparse
import csv
import json
from pathlib import Path

from audit_outex_crosscalls_20261104 import ANALYSIS, digest, read_json

DATA = {'FMD': 'fmd', 'CUReT': 'curet', 'Outex13Official1360': 'outex',
        'SoilOriginal': 'soil', 'KTHTIPS2b': 'kth', 'DTD': 'dtd'}
OUTEX_NAMES = {'CellNN adaptado': 'CellNN', 'HyTex adaptado': 'HyTex',
               'Neshov BEiTv2+MLP adaptado': 'Neshov', 'DeepLumina adaptado': 'DeepLumina'}
BOARD_NAMES = {'CellNN': 'CellNN_6LBP_2024', 'HyTex': 'HyTexNet_2026_MobileNetV2_235D_MLP',
               'Neshov': 'Neshov_2025_BEiTv2_LogReg', 'DeepLumina': 'DeepLumina_2022_ResNet101_RGB_YIQ_ECOC'}
BOARD_DATASETS = {'Outex13Official1360': 'Outex13'}


def build(output):
    output = Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    provenance = {str(Path(__file__).resolve()): digest(Path(__file__))}
    conv_path = ANALYSIS/'deeplumina_convergence_review_20261104_v1/summary.json'
    conv = read_json(conv_path); provenance[str(conv_path)] = digest(conv_path)
    if conv['complete_conditions_with_warnings'] != 46:
        raise ValueError('unexpected solver warning coverage')
    board_path = ANALYSIS/'external_sota_full_panel_summary_20261104_v1/summary.json'
    board = read_json(board_path); provenance[str(board_path)] = digest(board_path)
    comparisons, board_rows, sources = [], [], {}
    for dataset, code in DATA.items():
        folder = ANALYSIS/f'reconciliation_{code}_calls_20261104_v1'
        summary_path = folder/'summary.json'; summary = read_json(summary_path)
        csv_path = folder/('comparisons.csv' if code == 'outex' else 'dataset_comparisons.csv')
        for p in (summary_path, csv_path): provenance[str(p)] = digest(p)
        if summary['status'] not in ('FMD_CROSSCALL_AUDIT_COMPLETE', 'OUTEX_CROSSCALL_AUDIT_COMPLETE', 'DATASET_CROSSCALL_AUDIT_COMPLETE'):
            raise ValueError(f'audit not complete: {dataset}')
        if not summary['row_ids_truth_and_image_sha256_match'] or not summary['same_call_quality_and_timing']:
            raise ValueError(f'pairing contract failed: {dataset}')
        refs = summary['reference_results']
        if code == 'outex': refs = {OUTEX_NAMES[k]: v for k, v in refs.items()}
        sources[dataset] = refs
        with csv_path.open(newline='') as stream:
            for row in csv.DictReader(stream):
                if code == 'outex':
                    ref = OUTEX_NAMES[row['reference_method']]
                    local_f1, ref_f1 = float(row['local_macro_f1']), float(row['reference_macro_f1'])
                    local_ms, ref_ms = float(row['local_mean_ms']), float(row['reference_mean_ms'])
                    ncond, calls, reserve = 1, int(row['calls_each']), False
                else:
                    ref = row['reference_method']
                    local_f1, ref_f1 = float(row['local_mean_split_f1']), float(row['reference_mean_split_f1'])
                    local_ms, ref_ms = float(row['local_mean_ms']), float(row['reference_mean_ms'])
                    ncond, calls = int(row['conditions']), int(row['calls_each'])
                    reserve = row.get('physical_timing_reserve_local', 'False').lower() == 'true'
                comparisons.append({'dataset': dataset, 'classifier': row['classifier'],
                    'local_method': row['local_method'], 'reference_method': ref,
                    'conditions': ncond, 'calls_each': calls, 'local_mean_split_f1': local_f1,
                    'reference_mean_split_f1': ref_f1, 'delta_f1_local_minus_reference': local_f1-ref_f1,
                    'local_mean_ms': local_ms, 'reference_mean_ms': ref_ms,
                    'delta_ms_local_minus_reference': local_ms-ref_ms,
                    'scientific_status_reference': 'requires_review_solver_nonconvergence' if ref == 'DeepLumina' else 'crosscall_audited_adaptation',
                    'physical_timing_reserve_local': reserve})
        board_dataset = BOARD_DATASETS.get(dataset, dataset)
        for method in ('CellNN', 'HyTex', 'Neshov', 'DeepLumina'):
            claim = board['methods'][BOARD_NAMES[method]]['datasets'][board_dataset]
            audited = refs.get(method)
            audited_f1 = None if audited is None else audited.get('mean_split_macro_f1', audited.get('macro_f1'))
            notes = ('different_classifier_LogReg_vs_MLP_not_directly_comparable' if method == 'Neshov'
                     else 'incomplete_9_of_10_requires_review' if audited is None
                     else 'adaptation_requires_convergence_review' if method == 'DeepLumina'
                     else 'source_of_board_value_not_established')
            board_rows.append({'dataset': dataset, 'method': method, 'board_f1': claim['macro_f1'],
                'board_conditions': claim['conditions'], 'audited_f1': audited_f1,
                'numeric_board_minus_audited': None if audited_f1 is None else claim['macro_f1']-audited_f1,
                'interpretation': notes})
    if len(comparisons) != 230 or len(board_rows) != 24:
        raise ValueError('dataset comparison coverage mismatch')
    for dataset in DATA:
        rows = [r for r in comparisons if r['dataset'] == dataset]
        if len(rows) != (30 if dataset == 'DTD' else 40): raise ValueError('missing local/reference pairing')
    summary = {'status': 'CROSSCALL_RECONCILIATION_COMPLETE_WITH_SCIENTIFIC_RESERVES',
        'datasets': 6, 'condition_comparisons': 1780, 'dataset_comparisons': len(comparisons),
        'deep_dtd': '9/10 requires_review; omitted from dataset averages',
        'deeplumina': '46/46 completed conditions have solver nonconvergence warning lines; scientific review required',
        'new_board': 'Some figures differ; source and Neshov classifier require reconciliation.',
        'same_call_quality_and_timing': True,
        'hardware_timing_reservation': 'Separate dates/shared hardware; latency differences are descriptive.',
        'paper_scores_reproduced': False}
    output.mkdir(parents=True, exist_ok=False)
    (output/'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n')
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2, ensure_ascii=False)+'\n')
    (output/'reference_results.json').write_text(json.dumps(sources, indent=2, ensure_ascii=False)+'\n')
    for name, rows in [('comparison_by_dataset.csv', comparisons), ('board_reconciliation.csv', board_rows)]:
        with (output/name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', required=True)
    args = parser.parse_args(); build(args.output)
