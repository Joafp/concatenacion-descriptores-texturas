"""Readable tables for all KTH states and the separate matched-count E2 diagnostic."""
from pathlib import Path
import json
import pandas as pd
from build_topk_margin_thesis_20261113 import table, number
from prepare_top4_fixed_cascade import sha256

ROOT=Path(__file__).resolve().parents[1]
audit=ROOT/'results/analysis/top4_fixed_e1_e2_audit_20261115_v1'
run=ROOT/'results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1'
generated=ROOT/'paper/generated_top4_fixed_e1_e2_20261115'
s=json.loads((audit/'summary.json').read_text())
frozen=json.loads((run/'protocol_frozen.json').read_text())
rows=[]
for c in frozen['conditions']:
    if c['dataset']!='KTHTIPS2b':
        continue
    state=s['states'][c['id']]
    if state=='complete':
        r=json.loads((run/'conditions'/c['id']/'result.json').read_text())
        rows.append([c['outer_fold']+1,'Completada',number(r['metrics']['top4_direct']['accuracy'],6),number(r['selected_cascade']['metrics']['accuracy'],6),'--'])
    else:
        block='SigLIP' if c['outer_fold']==0 else 'EVA-02'
        rows.append([c['outer_fold']+1,'En revisión','--','--',block])
(generated/'kth_status.tex').write_text(table('E1: estado de las cuatro condiciones KTH, sin media incompleta.', 'tab:e1-kth-state', ['Partición','Estado','Directo Acc','Margen Acc','Reserva'],rows,'Las condiciones en revisión dependen de costos cuyos extractores fallaron el umbral de fidelidad congelado. No se repiten ni se sustituyen por otra receta.',size=8))
g=pd.read_csv(audit/'e2_complete_dataset_means.csv')
names={'margin':'Margen','maximum_score':'Máximo','softmax_entropy':'Entropía softmax'}
for mode,filename,label,caption in [
    ('oof_quantile','e2_accuracy_legible.tex','tab:e2-confidence-readable','E2: umbrales OOF y fracciones reales de activación.'),
    ('matched_test_count_diagnostic','e2_matched_count.tex','tab:e2-matched','E2: diagnóstico por lote con igual cantidad de imágenes derivadas.')]:
    d=g[g['mode'].eq(mode)].groupby(['q','gate']).mean(numeric_only=True)
    rows=[[str(q).replace('.',','),names[gate],number(r.accuracy,6),number(100*r.request_fraction,2)] for (q,gate),r in d.iterrows()]
    note=('Media equiponderada de cinco datasets completos. Mismo cuantil OOF no garantiza mismo rescate en test.' if mode=='oof_quantile' else
          'En cada condición se deriva exactamente la cantidad de imágenes que activó el margen. El orden usa puntuaciones de test sin sus etiquetas; es un diagnóstico por lote, no una compuerta individual online.')
    (generated/filename).write_text(table(caption,label,['q','Compuerta','Accuracy',r'Rescate real \%'],rows,note,size=8))
means=pd.read_csv(audit/'e1_complete_dataset_means.csv')
direct,cascade=means.direct_projected_ms.mean(),means.cascade_projected_ms.mean()
report={**s,'mean_direct_projected_ms':float(direct),'mean_cascade_projected_ms':float(cascade),
        'reduction_ratio_of_five_dataset_mean_costs':float(1-cascade/direct),
        'random_mean_accuracy':float(means.random_accuracy.mean())}
(audit/'readable_summary.json').write_text(json.dumps(report,indent=2)+'\n')
paths=[generated/'kth_status.tex',generated/'e2_accuracy_legible.tex',generated/'e2_matched_count.tex',audit/'readable_summary.json']
receipt={'script_sha256':sha256(Path(__file__)),
         'sources':{str(p.relative_to(ROOT)):sha256(p) for p in [audit/'summary.json',audit/'e2_complete_dataset_means.csv',audit/'e1_complete_dataset_means.csv',run/'protocol_frozen.json']},
         'outputs':{str(p.relative_to(ROOT)):sha256(p) for p in paths}}
(audit/'readable_report_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(report,indent=2))
