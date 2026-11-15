"""Check the forensic receipt without repeating neural inference."""
from pathlib import Path
import csv
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'results/analysis/kth_preprocessing_forensics_20261115_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_forensics_is_pixel_only_and_preserves_scientific_failure_states():
    s=json.loads((AUDIT/'summary.json').read_text())
    assert s['neural_models_constructed']==s['new_embedding_extractions']==s['new_predictions']==s['new_latency_benchmarks']==0
    assert not s['cuda_initialized_before'] and not s['cuda_initialized_after']
    assert s['threshold_unchanged']==.999 and not s['failures_retried']
    p=json.loads((AUDIT/'provenance.json').read_text())
    for relative,expected in p['protected_status_sha256'].items():
        assert digest(ROOT/relative)==expected
    assert all(s['existing_statuses_unchanged'].values())


def test_every_frozen_image_is_included_and_inputs_are_not_claimed_as_features():
    with (AUDIT/'pixel_preprocessing_pairs.csv').open() as handle:
        rows=list(csv.DictReader(handle))
    assert len(rows)==70
    for block in ['eva02_base','siglip_base']:
        real=[r for r in rows if r['block']==block and r['kind']=='frozen_training_image']
        assert len(real)==len({r['identifier'] for r in real})==33
        assert all(r['pixel_tensor_equal']=='False' for r in real)
        assert all(float(r['mean_abs_pixel_tensor_difference'])>0 for r in real)
    s=json.loads((AUDIT/'summary.json').read_text())
    assert s['recovery_manifest_check']['same_order_and_file_sha256']
    assert all(v['matches_manifest'] and v['rows']==4752 for v in s['label_checks'].values())
    assert 'feature_fidelity_still_requires_review' in s['status']


def test_forensic_sources_and_generated_data_are_hash_bound():
    p=json.loads((AUDIT/'provenance.json').read_text())
    for name,expected in p['source_sha256'].items():
        assert digest(ROOT/name)==expected
    for name,expected in p['outputs_sha256'].items():
        assert digest(AUDIT/name)==expected
    config=json.loads((AUDIT/'pipeline_configuration.json').read_text())
    assert config['eva_resolved_config_now']['crop_pct']==.9
    assert config['eva_resolved_config_now']['interpolation']=='bicubic'
    assert config['siglip_processor_config']['resample']==3
    for block in config['cached_weight_and_config_checks'].values():
        assert all(c['actual_sha256']==c['expected_sha256'] for c in block['checks'].values())
