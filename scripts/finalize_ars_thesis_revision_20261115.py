#!/usr/bin/env python3
"""Record a mechanical cross-reference repair and material provenance."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/analysis/ars_thesis_revision_20261115_v1'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p, obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def main():
    receipt = OUT/'formatter_crossref_repair.json'
    assert not receipt.exists(), 'Finalization already performed'
    old, new = 'tab:ars-e1-ranges', 'tab:ars-e1-variation'
    source = ROOT/'paper/chapters/05_resultados.tex'
    draft = OUT/'working_revised.md'
    final = OUT/'working_finalized.md'
    before = sha(source)
    for p in (source,draft):
        assert p.read_text().count(old)==1
    source.write_text(source.read_text().replace(old,new))
    final.write_text(draft.read_text().replace(old,new))
    dump(receipt,{'scope':'One mechanical reference repair to an existing generated label; native applied draft and apply report preserved. No claim or numerical change. Not a new native authorization PASS.', 'old':old,'new':new,'source_before':before,'source_after':sha(source),'native_draft_sha256':sha(draft),'finalized_draft_sha256':sha(final)})
    run = subprocess.run([str(ROOT/'.venv-confirmatory/bin/python'),'scripts/audit_outex_embedding_identity_20261109.py'],cwd=ROOT,capture_output=True,text=True,check=True)
    (OUT/'outex_identity_replay.jsonl').write_text(run.stdout)
    paths = ['docs/fsc_tex/AVANCE_OUTEX_HUELLAS_2026-11-09.md','scripts/audit_outex_embedding_identity_20261109.py',
             'docs/fsc_tex/PROTOCOLO_NESHOV_PANEL_COMUN_2026-11-02.md',
             'docs/fsc_tex/PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md',
             'docs/fsc_tex/PROTOCOLO_CELLNN_ADAPTACION_FMD_2026-11-02.md',
             'docs/fsc_tex/PROTOCOLO_DEEPLUMINA_ADAPTACION_FMD_2026-11-03.md']
    jobs = 'results/analysis/blocker_resolution_20261101/queue_v1/jobs'
    paths += [f'{jobs}/Outex13Official1360_{clf}_s42_f0/quality/status.json' for clf in ('svm','resmlp')]
    dump(OUT/'support_sources.json',{'sources':{f:sha(ROOT/f) for f in paths},
        'generated_support_files':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'paper/generated_ars_revision_20261115').glob('*.tex')},
        'primary_references_checked':[
            {'title':'Application-independent feature selection for texture classification','doi':'10.1016/j.patcog.2010.05.005','year':2010,'url':'https://www.sciencedirect.com/science/article/abs/pii/S0031320310002062','verification':'Publisher title/authors/journal/volume/pages/DOI and abstract checked on 2026-11-15. Abstract-based contextual citation; no claim of full-text replication.'},
            {'title':'Compact color-texture description for texture classification','doi':'10.1016/j.patrec.2014.07.020','year':2015,'url':'https://www.sciencedirect.com/science/article/abs/pii/S0167865514002451','author_copy':'https://research.cs.aalto.fi/cbir/papers/prl2015.pdf','verification':'Publisher metadata and abstract/highlights checked on 2026-11-15; compression and late-fusion distinction checked against author-hosted paper excerpt.'}],
        'outex_limit':'Normalized-array receipt matches do not establish physical row provenance. Historical/static identities remain qualified.',
        'scientific_calls':0})
    print('Finalized cross-reference and support-source receipts.')

if __name__=='__main__':
    if '--repair-quote' in sys.argv:
        receipt = OUT/'formatter_quote_repair.json'
        assert not receipt.exists()
        source = ROOT/'paper/chapters/05_resultados.tex'
        draft = OUT/'working_finalized.md'
        old, new = 'En E1, ``OOF conserva', 'En E1, OOF conserva'
        before = sha(source)
        assert source.read_text().count(old)==1 and draft.read_text().count(old)==1
        source.write_text(source.read_text().replace(old,new))
        final = OUT/'working_finalized_v2.md'
        final.write_text(draft.read_text().replace(old,new))
        dump(receipt,{'scope':'Mechanical removal of unmatched opening quote; no semantic or numerical change.', 'source_before':before,'source_after':sha(source),'input_draft_sha256':sha(draft),'output_draft_sha256':sha(final)})
    else:
        main()
