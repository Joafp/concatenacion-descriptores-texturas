#!/usr/bin/env python3
"""Apply the author-approved ARS corrections through the native block gate.

No models or scientific runners are called. Old audit folders remain immutable.
The source export replaces only exact original blocks, preserving other bytes.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ARS = Path('/mnt/c/Users/Joaquin/.codex/skills/academic-research-suite/ars/scripts')
sys.path.insert(0, str(ARS))
from revision_roadmap import author_decision_digest

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def dump(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def resume_schema_reemission():
    """One complete re-emission: installed schema also requires emitted_by."""
    out = ROOT / 'results/analysis/ars_thesis_revision_20261115_v1'
    base = out/'working_base.md'
    edits = json.loads((out/'proposed_edits.json').read_text())
    adjud = json.loads((out/'author_adjudication.json').read_text())
    hashes = {b['block_id']:b['old_hash'] for b in json.loads((out/'block_manifest.json').read_text())['blocks']}
    shutil.copyfile(out/'revision_patch_round1.json', out/'revision_patch_first_schema_rejected.json')
    patch = {'patch_format_version':'1.1','authorization_context':'review_roadmap','revision_round':1,'emitted_by':'Codex primary agent; exact approved action mapping', 'base_draft_hash':sha(base)[:12],'roadmap_sha256':sha(out/'revision_roadmap_adapter.json'),'author_adjudication_sha256':sha(out/'author_adjudication.json'),'author_decision_digest':author_decision_digest(adjud),'claim_surface_manifest_sha256':sha(out/'claim_surface_manifest.json'),'ops':[{'op':'replace_block','block_id':bid,'old_hash':hashes[bid],'new_text':e['new'],'roadmap_item_ids':e['items'],'claim_strength_changes':[],'collateral_authorization_ids':[]} for bid,e in edits.items()]}
    dump(out/'revision_patch_round1.json',patch)
    result = subprocess.run([sys.executable,str(ARS/'ars_apply_revision_patch.py'),str(base),str(out/'revision_patch_round1.json'),'--block-manifest',str(out/'block_manifest.json'),'--roadmap',str(out/'revision_roadmap_adapter.json'),'--author-adjudication',str(out/'author_adjudication.json'),'--claim-surface-manifest',str(out/'claim_surface_manifest.json'),'--artifact-root',str(out),'--output',str(out/'working_revised.md')],capture_output=True,text=True)
    (out/'native_apply_stdout.json').write_text(result.stdout)
    (out/'native_apply_stderr.txt').write_text(result.stderr)
    result.check_returncode()
    chunks = re.split(r'<!--block:(B\d+)-->\n',base.read_text())
    blocks = {chunks[i]:chunks[i+1].strip() for i in range(1,len(chunks),2)}
    current = None
    by_file = {}
    for bid,old in blocks.items():
        if old.startswith('# FILE: '):
            current = old.removeprefix('# FILE: ')
        elif bid in edits:
            src = by_file.setdefault(current,(ROOT/current).read_text())
            assert src.count(old)==1,(bid,current)
            by_file[current] = src.replace(old,edits[bid]['new'],1)
    pre = json.loads((out/'source_before.json').read_text())
    assert all(sha(ROOT/f)==digest for f,digest in pre.items())
    for f,content in by_file.items():
        (ROOT/f).write_text(content)
    dump(out/'source_export_receipt.json',{'working_draft_sha256':sha(out/'working_revised.md'),'changed_sources':{f:{'before':pre[f],'after':sha(ROOT/f)} for f in by_file},'unchanged_sources':[f for f in pre if f not in by_file],'new_scientific_calls':0,'scope_note':'Native gate protects working-copy blocks; exact-match source export and support tables are separately audited.'})
    print('Native gate and exact-match export passed:',len(edits),'blocks;',len(by_file),'files.')

def main():
    out = ROOT / 'results/analysis/ars_thesis_revision_20261115_v1'
    out.mkdir(exist_ok=False)
    review = ROOT / 'results/analysis/ars_thesis_review_20261115_v1'
    base = out / 'working_base.md'
    shutil.copyfile(review / 'inputs/review_working_draft.md', base)
    shutil.copyfile(review / 'inputs/block_manifest.json', out / 'block_manifest.json')
    raw = base.read_text()
    chunks = re.split(r'<!--block:(B\d+)-->\n', raw)
    blocks = {chunks[i]: chunks[i+1].strip() for i in range(1, len(chunks), 2)}
    block_file = {}
    current = None
    for bid, text in blocks.items():
        if text.startswith('# FILE: '):
            current = text.removeprefix('# FILE: ')
        else:
            block_file[bid] = current
    backup = ROOT / 'archive/local/tesis_before_ars_revision_20261115_v1'
    backup.mkdir(parents=True, exist_ok=False)
    files = sorted(set(block_file.values())) + ['paper/tesis.pdf']
    pre = {}
    for f in files:
        src = ROOT / f
        pre[f] = sha(src)
        dest = backup / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    dump(out / 'source_before.json', pre)
    edits = {}
    def set_edit(bid, new, *items):
        edits[bid] = {'new': new, 'items': list(items)}
    def append(bid, text, *items):
        set_edit(bid, blocks[bid] + '\n\n' + text, *items)

    set_edit('B0125', blocks['B0125'].replace('0,212 puntos más', '0,2305 puntos porcentuales de accuracy más'), 'REV-01')
    set_edit('B0129', blocks['B0129'].replace(r'\ref{tab:ngram-svm}', r'\ref{tab:ngram-accuracy-svm}') + r' El complemento de macro-F1 se conserva por separado en la Tabla~\ref{tab:ngram-svm}.', 'REV-02')
    set_edit('B0134', blocks['B0134'].replace('generated_topk_margin/externos_ms.tex', 'generated_ars_revision_20261115/externos_ms.tex'), 'REV-03')
    append('B0040', r'''Puig et al.\ propusieron una selección de métodos de textura de familias distintas para reducir el costo de su integración \citep{puig2010selection}. Su selección busca transferirse entre problemas y no equivale a nuestro ranking específico de cada entrenamiento externo. Este antecedente impide atribuir novedad a la idea general de seleccionar e integrar métodos de textura.

Khan et al.\ combinaron descriptores locales y comprimieron la representación heterogénea mediante un criterio de información; además estudiaron fusión tardía con color \citep{khan2015compact}. Nuestro Top-\(k\) selecciona bloques enteros sin reproducir esa compresión. La contribución evaluada aquí es la comparación de tamaños y de uso directo frente a activación por margen bajo los archivos identificados, no la invención de concatenar descriptores.''', 'REV-10', 'REV-11')
    append('B0045', r'''La Tabla~\ref{tab:ars-recetas} resume las implementaciones efectivamente comparadas. Las elecciones locales y las diferencias no verificadas forman parte del nombre de adaptación: ni el empleo de código de autor en un componente ni una dimensión coincidente acreditan reproducir los porcentajes del sistema completo.
\input{generated_ars_revision_20261115/recetas_externas.tex}''', 'REV-12')
    append('B0073', r'''Debe distinguirse una segunda dependencia de selección. Tanto en la cascada histórica como en E1, el subconjunto de rescate se toma del archivo de selección del entrenamiento externo y se mantiene fijo al generar sus predicciones OOF. No se vuelve a aprender el ranking ni el subconjunto dentro de cada entrenamiento OOF. Por ello son predicciones OOF de los clasificadores condicionadas al subconjunto archivado, no una evaluación completamente anidada de todo el procedimiento de selección. Esta dependencia puede hacer optimistas los puntajes internos y es distinta de reutilizar esos puntajes para elegir base y cuantil. No implica que se ajustaran los modelos con las etiquetas del test externo; la exposición histórica a ese test es una limitación adicional ya declarada.''', 'REV-07', 'REV-15')
    append('B0147', r'En E1, ``OOF'' conserva el alcance condicionado descrito en el método: se fija el Top-4 archivado y se reajusta el clasificador por pliegue, sin reaprender el ranking dentro de cada pliegue OOF. No se presenta este cierre como validación anidada integral de la selección.', 'REV-07')
    append('B0148', r'''La variación observada se informa sin tratar pliegues que comparten imágenes como réplicas independientes. La Tabla~\ref{tab:ars-e1-ranges} muestra los rangos y cuantiles de las diferencias por condición; no son intervalos de confianza poblacionales. La Tabla~\ref{tab:ars-e1-lodo} recalcula la media al dejar fuera, por turno, cada dataset: la diferencia va de \(-0,0192\) a \(+0,0747\) puntos porcentuales. Cambiar el conjunto de datasets puede incluso cambiar el signo; no se elige una exclusión favorable como resultado principal.
\input{generated_ars_revision_20261115/e1_observed_ranges.tex}
\input{generated_ars_revision_20261115/e1_dataset_sensitivity.tex}''', 'REV-05')
    append('B0109', r'Además se repite la misma familia principal de accuracy sin el KTH archivado: cinco medias por dataset, 7.776 permutaciones exactas de Friedman y los mismos tres pares con Holm por clasificador. Esta sensibilidad del benchmark estático no excluye las cuatro condiciones KTH del cierre E1, que constituye otro archivo.', 'REV-06')
    append('B0243', r'''La sensibilidad anterior corresponde a macro-F1 y a su familia histórica. Para la métrica principal actual se añade separadamente Individual/Completa-22/Top-4 sobre los mismos cinco datasets. Friedman exacto da \(p=0,1242\) en SVM y \(p=0,5216\) en ResMLP; ningún par es significativo tras Holm. Las exclusiones diagnósticas de Outex y de ambos datasets quedan en el CSV de sensibilidad, sin sustituir la comparación canónica ni demostrar que los datos excluidos estén dañados.
\input{generated_ars_revision_20261115/static_accuracy_without_kth.tex}
\input{generated_ars_revision_20261115/static_accuracy_without_kth_pairs.tex}''', 'REV-06')
    append('B0090', r'''El alcance se distingue en la Tabla~\ref{tab:ars-outex-scope}. Los recibos del panel coinciden con el array ViT normalizado y con el DeiT enmendado; el DeiT histórico no coincide con ese recibo. Esta comprobación identifica matrices utilizadas, pero no valida independientemente la procedencia de todas sus filas. Para los archivos estáticos y el barrido no se ha establecido en esta revisión una identidad completa con esas matrices del panel. Se conserva la reserva y se proporciona una sensibilidad sin Outex en los análisis guardados; ninguna tabla canónica se reemplaza ni se declara afectada por inferencia a partir de otra receta.
\input{generated_ars_revision_20261115/outex_scope.tex}''', 'REV-08', 'REV-09')
    glossary = blocks['B0016'].replace('ResMLP & MLP residual', r'''CNN & Red neuronal convolucional (\emph{convolutional neural network})\\
MLP & Perceptrón multicapa (\emph{multilayer perceptron})\\
SFFS & Selección secuencial flotante hacia delante: admite retirar bloques tras añadirlos\\
ResMLP & MLP residual''')
    set_edit('B0016', glossary, 'REV-13')
    set_edit('B0081', blocks['B0081'].replace('SFFS y selecciones aleatorias', 'selección secuencial flotante hacia delante (SFFS), que permite revisar y retirar bloques tras una incorporación, y selecciones aleatorias'), 'REV-13')
    append('B0153', r'''La similitud coseno compara, para una misma imagen, el vector de referencia \(u\) y el extraído \(v\), ambos no nulos:
\begin{equation}
\operatorname{cos}(u,v)=\frac{u^{\mathsf T}v}{\|u\|_2\|v\|_2}\in[-1,1].
\end{equation}
Mide concordancia de dirección y es invariante a multiplicar los vectores por factores positivos. Un valor próximo a uno no prueba igualdad de magnitudes ni identidad global del pipeline. El mínimo 0,999 es un criterio de aceptación registrado para estas muestras, no un nivel de confianza estadística ni una garantía de calibración.''', 'REV-14')
    set_edit('B0154', r'''La revisión identificó diferencias de preprocesamiento en EVA-02 y SigLIP. Tras autorización del autor, las recetas corregidas se validaron con los mismos pesos y las mismas 33 imágenes, conservando el mínimo 0,999. Ambos bloques alcanzaron mínimos mayores que 0,99999999999. Las sesiones y las seis constantes aceptadas previamente permanecen identificadas; el Anexo~\ref{sec:ars-kth-infra} conserva el detalle operativo sin sustituir los estados fallidos originales.''', 'REV-04')
    append('B0263', r'''\subsection{Detalle operativo de la corrección KTH}\label{sec:ars-kth-infra}
EVA-02 requería resize bicúbico del lado corto a 248 y recorte central 224; SigLIP histórico usaba resize bilineal explícito a 224. La validación corregida utilizó 33 imágenes de entrenamiento por bloque, tres por clase: 66 llamadas evaluadas y diez calentamientos. Un error de serialización del informe de carga se corrigió antes del primer forward SigLIP, sin repetir EVA ni llamadas científicas fallidas. Se preservaron las seis constantes aceptadas y se añadieron las dos nuevas, con sesiones temporales distintas. Los recibos están en \path{results/analysis/kth_reference_validated_profile_20261115_v1/}.

La revisión ARS del 15-11 añade análisis de resultados guardados mediante \path{scripts/analyze_ars_existing_results_20261115.py}. Sus fuentes, diferencias por condición, cuantiles y sensibilidades están vinculados por hashes en \path{results/analysis/ars_revision_existing_analyses_20261115_v1/}. No se realizaron nuevos fits, extracciones, predicciones de modelos ni cronometrajes. La matriz de alcance Outex se apoya en los recibos y en \path{docs/fsc_tex/AVANCE_OUTEX_HUELLAS_2026-11-09.md}; los detalles no verificados siguen abiertos.''', 'REV-04', 'REV-05', 'REV-06', 'REV-08')
    bib = r'''@article{puig2010selection,
  author={Puig, Domenec and Garcia, Miguel Angel and Melendez, Jaime},
  title={Application-independent feature selection for texture classification},
  journal={Pattern Recognition}, volume={43}, number={10}, pages={3282--3297},
  year={2010}, doi={10.1016/j.patcog.2010.05.005}
}

@article{khan2015compact,
  author={Khan, Fahad Shahbaz and Anwer, Rao Muhammad and van de Weijer, Joost and Felsberg, Michael and Laaksonen, Jorma},
  title={Compact color--texture description for texture classification},
  journal={Pattern Recognition Letters}, volume={51}, pages={16--22},
  year={2015}, doi={10.1016/j.patrec.2014.07.020}
}'''
    append('B0424', bib, 'REV-10', 'REV-11')
    dump(out / 'proposed_edits.json', edits)

    # Preserve the original roadmap; this adapter adds only source-export targets
    # necessary for the same author-approved corrections (annex and references).
    roadmap = json.loads((review / 'revision_roadmap.json').read_text())
    for item in roadmap['items']:
        relevant = [bid for bid, e in edits.items() if item['id'] in e['items']]
        item['proposed_targets'] = [{'block_id': bid, 'allowed_operations': ['replace_block']} for bid in relevant]
    dump(out / 'revision_roadmap_adapter.json', roadmap)
    dump(out / 'adapter_mapping.json', {'original_roadmap_sha256': sha(review/'revision_roadmap.json'), 'scope': 'Same 15 approved actions; exact source blocks mapped by orchestrator. No new review judgment or author quotation.', 'export_support_files': ['paper/generated_ars_revision_20261115/externos_ms.tex', 'paper/generated_ars_revision_20261115/recetas_externas.tex', 'paper/generated_ars_revision_20261115/outex_scope.tex']})
    event = {'event_id':'AUTHOR-EVENT-20261115-revision', 'source':'explicit_session_user_message', 'author_text':'si', 'context':'Acceptance of the proposed ARS corrections and saved-results analyses, followed by continua. No new scientific run authorized by this revision.'}
    dump(out / 'author_event.json', event)
    event_id = event['event_id']
    choices = {'schema_version':'author-adjudication-input/1.0', 'author_events':[{'event_id':event_id,'source':'explicit_session_user_message','actor_role':'author','input_sha256':sha(out/'author_event.json')}], 'display_order':{'mode':'source_traceability','item_ids':[x['id'] for x in roadmap['items']],'author_event_id':event_id},'author_adjudications':[{'item_id':x['id'],'author_event_id':event_id,'author_triage':'will_address','authorized_targets':x['proposed_targets'],'claim_strength_authorizations':[]} for x in roadmap['items']], 'collateral_authorizations':[]}
    dump(out/'author_choices.json', choices)
    dump(out/'claim_surface_manifest.json', {'schema_version':'claim-surface-manifest/1.0','revision_round':1,'roadmap_sha256':sha(out/'revision_roadmap_adapter.json'),'base_draft_sha256':sha(base),'claim_intent_sources':[],'surfaces':[]})
    cmd = [sys.executable, str(ARS/'revision_roadmap.py'), 'build-adjudication', str(out/'revision_roadmap_adapter.json'), '--base',str(base),'--block-manifest',str(out/'block_manifest.json'),'--claim-surface',str(out/'claim_surface_manifest.json'),'--author-choices',str(out/'author_choices.json'),'--artifact-root',str(out),'--output',str(out/'author_adjudication.json')]
    subprocess.run(cmd, check=True)
    adjud = json.loads((out/'author_adjudication.json').read_text())
    manifest = json.loads((out/'block_manifest.json').read_text())
    hashes = {b['block_id']:b['old_hash'] for b in manifest['blocks']}
    patch = {'patch_format_version':'1.1','authorization_context':'review_roadmap','revision_round':1,'base_draft_hash':sha(base)[:12],'roadmap_sha256':sha(out/'revision_roadmap_adapter.json'),'author_adjudication_sha256':sha(out/'author_adjudication.json'),'author_decision_digest':author_decision_digest(adjud),'claim_surface_manifest_sha256':sha(out/'claim_surface_manifest.json'),'ops':[{'op':'replace_block','block_id':bid,'old_hash':hashes[bid],'new_text':e['new'],'roadmap_item_ids':e['items'],'claim_strength_changes':[],'collateral_authorization_ids':[]} for bid,e in edits.items()]}
    patch['emitted_by'] = 'Codex primary agent; exact approved action mapping'
    dump(out/'revision_patch_round1.json',patch)
    subprocess.run([sys.executable,str(ARS/'ars_apply_revision_patch.py'),str(base),str(out/'revision_patch_round1.json'),'--block-manifest',str(out/'block_manifest.json'),'--roadmap',str(out/'revision_roadmap_adapter.json'),'--author-adjudication',str(out/'author_adjudication.json'),'--claim-surface-manifest',str(out/'claim_surface_manifest.json'),'--artifact-root',str(out),'--output',str(out/'working_revised.md')],check=True)
    # Check every source and replacement before any source export.
    by_file = {}
    for bid,e in edits.items():
        f = block_file[bid]
        source = by_file.setdefault(f, (ROOT/f).read_text())
        assert source.count(blocks[bid]) == 1, (bid, f, 'not an exact unique source block')
        by_file[f] = source.replace(blocks[bid], e['new'], 1)
    for f,digest in pre.items():
        assert sha(ROOT/f) == digest, f
    for f,content in by_file.items():
        (ROOT/f).write_text(content)
    dump(out/'source_export_receipt.json', {'working_draft_sha256':sha(out/'working_revised.md'), 'changed_sources':{f:{'before':pre[f],'after':sha(ROOT/f)} for f in by_file}, 'unchanged_sources':[f for f in pre if f not in by_file], 'new_scientific_calls':0, 'scope_note':'Native gate covers working-copy edits. Exact-match source export and generated support files are recorded separately; no claim that the native gate audits LaTeX rendering.'})
    print('Applied',len(edits),'blocks in',len(by_file),'source files; support tables still required before compilation.')

if __name__ == '__main__':
    if '--resume-schema-reemission' in sys.argv:
        resume_schema_reemission()
    else:
        main()
