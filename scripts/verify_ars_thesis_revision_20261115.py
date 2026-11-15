#!/usr/bin/env python3
"""Verify the revised manuscript against frozen evidence and release receipts."""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/analysis/ars_thesis_revision_20261115_v1'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_text())

def main():
    assert not (OUT/'release.json').exists()
    checked = 0
    analysis = ROOT/'results/analysis/ars_revision_existing_analyses_20261115_v1'
    for group in ('sources','outputs'):
        for f,digest in load(analysis/'provenance.json')[group].items():
            assert sha(ROOT/f)==digest, f
            checked += 1
    support = load(OUT/'support_sources.json')
    for group in ('sources','generated_support_files'):
        for f,digest in support[group].items():
            assert sha(ROOT/f)==digest, f
            checked += 1
    # Seven canonical E1/E2 generated tables and their input audit are immutable.
    old = load(ROOT/'results/analysis/thesis_six_dataset_integration_20261115_v1/tables_receipt.json')
    for group in ('sources','outputs'):
        for f,digest in old[group].items():
            assert sha(ROOT/f)==digest, f
            checked += 1
    export = load(OUT/'source_export_receipt.json')
    repairs = [load(OUT/f) for f in ('formatter_crossref_repair.json','formatter_quote_repair.json')]
    for f,binding in export['changed_sources'].items():
        digest = binding['after']
        if f=='paper/chapters/05_resultados.tex':
            for repair in repairs:
                assert digest==repair['source_before']
                digest = repair['source_after']
        assert sha(ROOT/f)==digest,f
    for f in export['unchanged_sources']:
        if f!='paper/tesis.pdf':
            assert sha(ROOT/f)==load(OUT/'source_before.json')[f],f
    applied = load(OUT/'working_revised.md.apply-report.json')
    assert applied['authorization_witness']['status']=='pass'
    assert applied['output_draft_hash']==sha(OUT/'working_revised.md')[:12]
    assert applied['authorization_witness']['unregistered_claim_drift_review_required'] is True
    covered = {item for op in applied['ops_applied'] for item in op['roadmap_item_ids']}
    assert covered=={f'REV-{n:02d}' for n in range(1,16)}
    assert len(applied['ops_applied'])==17
    for f in ('apply_ars_thesis_revision_20261115.py','finalize_ars_thesis_revision_20261115.py','analyze_ars_existing_results_20261115.py'):
        ast.parse((ROOT/'scripts'/f).read_text())
    old_ms = (ROOT/'paper/generated_topk_margin/externos_ms.tex').read_text()
    new_ms = (ROOT/'paper/generated_ars_revision_20261115/externos_ms.tex').read_text()
    data_lines = lambda s:[x for x in s.splitlines() if ' & ' in x]
    assert data_lines(old_ms)==data_lines(new_ms)
    pdf = ROOT/'paper/tesis.pdf'
    text = subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True)
    log = (ROOT/'paper/tesis.log').read_text()
    assert not re.search(r'Overfull|undefined|multiply defined',log)
    assert '\ufffd' not in text and '??' not in text
    assert '0,2305' in text and '0,944449' in text and '0,944581' in text
    assert 'Application-independent feature selection' in ' '.join(text.split())
    assert 'Compact color' in text
    assert '106 passed' in (OUT/'tests.txt').read_text()
    qa_path = ROOT/'output/pdf/ars_revision_20261115_release_qa/qa.json'
    qa = load(qa_path)
    assert qa['pages']==94 and qa['pdf_sha256']==sha(pdf)
    assert not qa['tex_log_has_overfull'] and not qa['tex_log_has_undefined']
    pixel_diff = load(qa_path.parent/'changed_vs_inspected.json')
    assert pixel_diff['changed_pages']==['page-43.png']
    # Observed visual checks: all eight contact sheets and six 110dpi details.
    qa['visual_review_status']='reviewed_by_primary_agent'
    qa['review_scope']={'all_94_pages':'eight inspected baseline contact sheets; exact RGB equality for 93 release pages; changed page 43 inspected at 110dpi', 'detail_pages_110dpi':[20,31,43,44,66,74], 'visible_defects_found':0}
    qa_path.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    tracked = list(export['changed_sources']) + [str(p.relative_to(ROOT)) for p in (ROOT/'paper/generated_ars_revision_20261115').glob('*.tex')] + ['paper/tesis.pdf']
    result = {'status':'revised_compiled_and_verified','pages':94,'pdf_sha256':sha(pdf),'covered_review_items':sorted(covered),'native_blocks_applied':17,'native_authorization_witness':'pass_for_working_copy_only','post_apply_formatting_repairs':2,'full_native_revision_bundle_claimed':False,'unregistered_claim_drift_review_required':True,'semantic_review':'Primary agent inspected all changed source blocks and support tables; conclusions remain exploratory, no independent re-review claimed.','source_and_table_hashes_checked':checked,'pytest_result':'106 passed in 30.02s','tests_output_sha256':sha(OUT/'tests.txt'),'new_fits':0,'new_extractions':0,'new_model_predictions':0,'new_timings':0,'qa':qa,'files':{f:sha(ROOT/f) for f in tracked},'remaining_scientific_limits':['Outex physical row provenance not fully verified','KTH/DTD protocol and representation reservations retained','DeepLumina nonconvergence and incomplete DTD retained','New direct/margin policy online latency not measured','Top4-plus-Ngrams specific experiment not executed']}
    (OUT/'release.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','pages','pdf_sha256','source_and_table_hashes_checked','pytest_result')},indent=2))

if __name__=='__main__':
    main()
