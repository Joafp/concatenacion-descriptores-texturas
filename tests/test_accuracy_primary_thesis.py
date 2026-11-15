from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from scripts.consolidate_top4_fixed_e1_e2 import complete_datasets
from scripts.build_accuracy_primary_thesis_20261115_v3 import exact_signed_rank, holm
from scripts.prepare_top4_fixed_cascade import sha256

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT/'results/analysis/thesis_accuracy_primary_20261115_v3'


def test_reconstruction_sources_and_outputs_retain_their_hashes():
    p=json.loads((AUDIT/'provenance.json').read_text())
    assert len(p['sources']) == 144
    for key in ['sources','outputs']:
        for name, expected in p[key].items():
            assert sha256(ROOT/name) == expected


def test_accuracy_is_reconstructed_not_renamed_f1():
    p=json.loads((AUDIT/'summary.json').read_text())
    assert p['primary_metric']=='accuracy' and p['historical_selection_metric']=='macro_f1'
    a,b=p['curve_statistics']
    assert a['accuracy_k4']==pytest.approx(.9442137857740577)
    assert a['peak_k']==10 and b['peak_k']==5
    d=pd.read_csv(AUDIT/'online_means.csv')
    soil=d[(d.dataset=='SoilOriginal') & (d.classifier=='svm') & (d.policy=='Top-4')].iloc[0]
    assert abs(soil.accuracy-soil.macro_f1) > .05


def test_partial_dataset_cannot_enter_a_complete_mean():
    c=[{'dataset':'A','id':'a1'},{'dataset':'A','id':'a2'},{'dataset':'B','id':'b1'}]
    assert complete_datasets(c,{'a1':'complete','a2':'requires_review','b1':'complete'})==['B']


def test_exact_paired_test_and_holm_family():
    assert exact_signed_rank(np.zeros(6)) == 1.
    assert exact_signed_rank(np.ones(6)) == 2/64
    assert holm([.01,.04,.03])==pytest.approx([.03,.06,.06])


def test_primary_scope_and_historical_criterion_both_remain_explicit():
    design=(ROOT/'paper/chapters/04_diseno_experimental.tex').read_text()
    assert 'La métrica principal es accuracy' in design
    assert '15-11-2026' in design and 'macro-F1 permanecen' in design
    text=(ROOT/'paper/tesis.tex').read_text()
    assert 'Accuracy (exactitud) es la métrica principal' in text
    assert 'Accuracy is the primary reporting metric' in text


def test_ngram_table_keeps_all_five_comparators():
    text=(ROOT/'paper/generated_accuracy_primary_20261115_v3/ngram_svm.tex').read_text()
    assert text.count('Homogénea') == 4
    assert r'a\_to\_b' in (ROOT/'paper/generated_accuracy_primary_20261115_v3/top4_margin_subset.tex').read_text()


def test_e1_e2_audit_does_not_promote_partial_kth_to_a_full_dataset():
    audit=ROOT/'results/analysis/top4_fixed_e1_e2_audit_20261115_v1'
    summary=json.loads((audit/'summary.json').read_text())
    assert summary['completed_conditions']==25 and summary['expected_conditions']==27
    assert len(summary['complete_datasets'])==5 and 'KTHTIPS2b' not in summary['complete_datasets']
    assert not summary['incomplete_dataset_averages_reported']
    frame=pd.read_csv(audit/'e1_complete_dataset_means.csv')
    assert len(frame)==5 and 'KTHTIPS2b' not in set(frame.dataset)
    gates=pd.read_csv(audit/'e2_conditions.csv')
    diagnostic=gates[gates['mode']=='matched_test_count_diagnostic']
    assert diagnostic.groupby(['id','q']).request_fraction.nunique().eq(1).all()
    assert len(gates)==25*18
    assert summary['all_escalated_predictions_match_direct']
