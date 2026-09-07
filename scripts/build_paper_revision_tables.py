#!/usr/bin/env python3
"""Build the September revision tables from completed conditions and Java output.

Does not alter experimental inputs, checkpoints or manuscripts. The primary
analysis uses all completed SVM and ResMLP conditions of the 21-block library.
"""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
from scipy.stats import chi2, f

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper/articulo/borrador_profesor/generated'
BASES = ['results/confirmatory', 'results/extensions/outex13_official1360']
DATASETS = ['DTD', 'FMD', 'CUReT', 'Outex13Official1360']
COUNTS = dict(zip(DATASETS, [10, 15, 2, 1]))
METHODS = ['best_individual', 'full_concat', 'topk_individual', 'gfs', 'homogeneous']
LABELS = ['Individual', 'Completa', r'Top-$k$', 'GFS', r'Homogénea']
SOURCE_HASHES = {}

def read(path):
    path = ROOT / path
    raw = path.read_bytes()
    SOURCE_HASHES[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    return pd.read_csv(path)

def frame(extension='', classifier=None):
    chunks = []
    for base in BASES:
        for suffix in ['nested_fold_results.csv', 'topk_individual_control/nested_fold_results.csv']:
            chunks.append(read(f'{base}{extension}/{suffix}'))
    df = pd.concat(chunks, ignore_index=True)
    if classifier:
        df = df[df.classifier == classifier].copy()
    df['method'] = df.method.str.replace(r'^best_homogeneous_.*', 'homogeneous', regex=True)
    keys = ['dataset', 'classifier', 'seed', 'outer_fold', 'method']
    assert not df.duplicated(keys).any(), 'Duplicate condition/method'
    assert np.isfinite(df[['macro_f1', 'accuracy', 'dimensions', 'k']].to_numpy()).all()
    dimensions={'convnext_v2_t':768,'deit_s':384,'densenet121':1024,'dinov2':768,
                'dinov2_large':1024,'dinov2_small':384,'drlbp':80,'efficientnet_b0':1280,
                'eva02_base':768,'gabor':48,'glcm':18,'hog':1764,'lbp':54,'mae_base':768,
                'resnet101':2048,'resnet50':2048,'siglip_base':768,'swin_t':768,
                'vgg16':4096,'vit_b16':768,'rgb_ngram_svd':256}
    for row in df.itertuples():
        blocks=row.selected.split('+')
        assert len(blocks)==len(set(blocks))==row.k
        assert sum(dimensions[b] for b in blocks)==row.dimensions
        if row.method=='full_concat':
            assert row.k==(21 if extension else 20)
    classifiers = [classifier] if classifier else ['svm', 'resmlp']
    for dataset in DATASETS:
        for clf in classifiers:
            x = df[(df.dataset == dataset) & (df.classifier == clf)]
            assert x.groupby('method').size().to_dict() == {m:COUNTS[dataset] for m in METHODS}, (dataset, clf)
            # All five methods must refer to exactly the same external conditions.
            assert x.groupby(['seed', 'outer_fold']).method.nunique().eq(5).all()
    return df

def n(value, digits=4):
    if abs(value)<0.5*10**(-digits):
        value=0.0
    return f'{value:.{digits}f}'.replace('.', '{,}')

def table(name, caption, label, columns, header, rows, note=''):
    text = '\n'.join([r'\begin{resulttable}', r'\centering\fontsize{9}{11}\selectfont\setlength{\tabcolsep}{3.6pt}',
        '\\caption{' + caption + '}', '\\label{' + label + '}',
        '\\begin{tabular}{@{}' + columns + '@{}}', r'\toprule', header + r' \\',
        r'\midrule', *[r + r' \\' for r in rows], r'\bottomrule',
        r'\end{tabular}', ('\\par\\smallskip{\\footnotesize ' + note + '}') if note else '',
        r'\end{resulttable}', r'\FloatBarrier', ''])
    (OUT / name).write_text(text)

def dataset_name(d):
    return 'Outex' if d.startswith('Outex') else d

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reference = frame()
    old = frame('/ngram21')
    new = old.copy()
    summary = old.groupby(['dataset','classifier','method'])[['macro_f1','accuracy','dimensions','k']].agg(['mean','std'])
    for metric, filename, label in [('macro_f1','baseline_f1.tex','tab:resultados-confirmatorios'),('accuracy','baseline_accuracy.tex','tab:accuracy')]:
        rows=[]
        for d in DATASETS:
            for c in ['svm','resmlp']:
                vals=[summary.loc[(d,c,m),(metric,'mean')] for m in METHODS]
                cells=[]
                for m,v in zip(METHODS,vals):
                    cell=n(v)
                    if v == max(vals): cell=r'\mathbf{' + cell + '}'
                    if COUNTS[d]>1: cell+=r'\,\pm\,'+n(summary.loc[(d,c,m),(metric,'std')])
                    cells.append('$'+cell+'$')
                rows.append(' & '.join([dataset_name(d), 'SVM' if c=='svm' else 'ResMLP',*cells]))
        title='Macro-F1 externo' if metric=='macro_f1' else 'Exactitud externa'
        table(filename,title+' de las cinco estrategias con la biblioteca de 21 descriptores. Media y desviación estándar entre particiones; Outex tiene un único split. El máximo de cada fila se destaca sin implicar significancia estadística.',label,'llccccc','Dataset & Clasif. & '+' & '.join(LABELS),rows)
    names={'siglip_base':'SigLIP-B','dinov2_large':'DINOv2-L','dinov2_small':'DINOv2-S','rgb_ngram_svd':'N-gramas + SVD'}
    dimension_rows=[]
    for d in DATASETS:
        for c in ['svm','resmlp']:
            dimension_rows.append(' & '.join([dataset_name(d),'SVM' if c=='svm' else 'ResMLP',*['$'+n(summary.loc[(d,c,m),('dimensions','mean')],1)+'$' for m in METHODS]]))
    table('dimensions_primary.tex','Dimensión media de las representaciones por dataset y clasificador. Se cuentan coordenadas del vector de entrada, con los mismos subconjuntos usados para medir macro-F1 y exactitud.','tab:dimensiones','llrrrrr','Dataset & Clasif. & '+' & '.join(LABELS),dimension_rows,'Las medias pueden ser fraccionarias porque el subconjunto seleccionado cambia entre particiones. La dimensión no equivale a tiempo de extracción ni a memoria total de ejecución.')
    rows=[]
    for d in DATASETS:
        for c in ['svm','resmlp']:
            x=old[(old.dataset==d)&(old.classifier==c)&(old.method=='best_individual')]
            desc='; '.join(f'{names.get(k,k)} ({v}/{len(x)})' for k,v in x.selected.value_counts().items())
            rows.append(' & '.join([dataset_name(d),'SVM' if c=='svm' else 'ResMLP',desc]))
    table('individual_identity.tex','Identidad del mejor descriptor individual elegido en validación interna, para las condiciones de la Tabla~\\ref{tab:resultados-confirmatorios}. Las frecuencias explicitan cuándo la media reúne descriptores diferentes.','tab:individual-identidad','lll','Dataset & Clasificador & Descriptor (frecuencia)',rows)
    # Identity is panel B of the performance table, as requested by the tutor.
    identity = (OUT/'individual_identity.tex').read_text()
    identity_body = identity[identity.index(r'\begin{tabular}'):identity.index(r'\end{tabular}')+len(r'\end{tabular}')]
    f1_path = OUT/'baseline_f1.tex'
    f1_text = f1_path.read_text().replace(r'\begin{tabular}', r'\textbf{Panel A: macro-F1 externo}\par\smallskip'+'\n'+r'\begin{tabular}', 1)
    panel = r'\par\medskip\textbf{Panel B: descriptor Individual seleccionado}\par\smallskip'+'\n'+r'\label{tab:individual-identidad}'+'\n'+identity_body+'\n'+r'\par\smallskip{\footnotesize Frecuencias de selección interna; cuando cambia el descriptor, la media del panel A reúne esas elecciones.}'+'\n'
    f1_path.write_text(f1_text.replace(r'\end{resulttable}',panel+r'\end{resulttable}'))
    for clf, clf_label in [('svm','SVM'),('resmlp','ResMLP')]:
        rows=[]
        for d in DATASETS:
            for m,l in zip(METHODS,LABELS):
                a=reference[(reference.dataset==d)&(reference.classifier==clf)&(reference.method==m)].set_index(['seed','outer_fold'])
                b=new[(new.dataset==d)&(new.classifier==clf)&(new.method==m)].set_index(['seed','outer_fold'])
                assert a.index.sort_values().equals(b.index.sort_values())
                delta = b.macro_f1-a.macro_f1
                delta_cell = n(delta.mean())
                if len(delta)>1:
                    delta_cell += r'\,\pm\,' + n(delta.std())
                rows.append(' & '.join([dataset_name(d),l,'$'+n(a.macro_f1.mean())+'$','$'+n(b.macro_f1.mean())+'$','$'+delta_cell+'$','$'+n(b.accuracy.mean())+'$']))
        table(f'ngram_{clf}.tex',f'Comparación completa con {clf_label}: medias con 20 frente a 21 bloques, incluyendo RGB Pixel N-grams + SVD. Mismas 28 condiciones externas: DTD (10), FMD (15), CUReT (2) y Outex (1). La selección se repite dentro del entrenamiento.','tab:ngram-multibase' if clf=='resmlp' else 'tab:ngram-svm','llrrrr','Dataset & Estrategia & F1 (20) & F1 (21) & $\\Delta$ F1 & Exactitud (21)',rows,'F1 designa macro-F1. $\\Delta$ es la media de las diferencias pareadas (21 menos 20), acompañada de su desviación estándar cuando hay más de una partición; no es un intervalo de confianza ni una prueba de significancia.')
    # Extract adjusted p-values from the original Java output, never thresholds.
    np_root=ROOT/'results/confirmatory/ngram21/nonparametric'
    expected = read('results/confirmatory/ngram21/nonparametric/primary_by_dataset.csv').set_index('Data-set')
    derived = old.groupby(['dataset','classifier','method']).macro_f1.mean().unstack('method').groupby('dataset').mean()
    derived.index = derived.index.map(dataset_name)
    derived = derived.rename(columns=dict(zip(METHODS,['Individual','Completa','Top-k','GFS','Homogenea'])))
    assert np.allclose(derived.loc[expected.index, expected.columns], expected, rtol=0, atol=5e-12), 'Java input does not match displayed baseline'
    java=(np_root/'primary_multipletest.tex').read_text()
    SOURCE_HASHES[str((np_root/'primary_multipletest.tex').relative_to(ROOT))] = hashlib.sha256(java.encode()).hexdigest()
    adjusted=java.split(r'\caption{Adjusted $p$-values}')[-1]
    pairs={}
    for line in adjusted.splitlines():
        fields=line.rstrip('\\').split('&')
        if len(fields)==7 and fields[0].isdigit():
            a,b=re.split(r'\s+vs\s*\.?\s*',fields[1])
            pairs[frozenset([a.strip(),b.strip()])]=min(1.,float(fields[4]))
    assert len(pairs)==10
    focused=[]
    for method,label in [('GFS','GFS'),('Top-k',r'Top-$k$'),('Completa','Completa'),('Homogenea','Homogénea')]:
        differences=derived[method]-derived['Individual']
        adjusted_p=pairs[frozenset([method,'Individual'])]
        focused.append(' & '.join([label+' vs. Individual','$'+n(differences.mean())+'$',str(int((differences>0).sum()))+'/4','$'+n(adjusted_p)+'$','Sí' if adjusted_p<0.05 else 'No']))
    table('vs_individual_primary.tex','Comparaciones de cada estrategia combinada frente a Individual con 21 descriptores. Diferencia media de macro-F1 entre datasets y valores $p$ de las comparaciones basadas en rangos de Friedman, ajustados con Holm.','tab:vs-individual','lrccl','Comparación & $\\Delta$ macro-F1 & Datasets a favor & $p_{\\mathrm{Holm}}$ & Significativa',focused,'Se promedian primero las condiciones de cada clasificador y luego ambos clasificadores por dataset. Holm conserva la familia de diez pares; mostrar estos cuatro contrastes no reduce la corrección. Nivel $\\alpha=0{,}05$.')
    raw_names=['Individual','Completa','Top-k','GFS','Homogenea']
    rows=[]
    for i,(a,l) in enumerate(zip(raw_names,LABELS)):
        rows.append(' & '.join([l,*['---' if j<=i else '$'+n(pairs[frozenset([a,b])])+'$' for j,b in enumerate(raw_names)]]))
    table('holm_primary.tex','Valores $p$ ajustados mediante Holm para las diez comparaciones de macro-F1 entre estrategias (21 descriptores; cuatro datasets). Ninguna comparación rechaza a $\\alpha=0{,}05$.','tab:holm-primary','lccccc','Estrategia & '+' & '.join(LABELS),rows,'Se presentan como información complementaria: Friedman no rechazó la hipótesis global. Los valores ajustados que el programa imprime por encima de 1 se acotan a 1; los originales se conservan.')
    ctrl=(np_root/'primary_controltest.tex').read_text()
    SOURCE_HASHES[str((np_root/'primary_controltest.tex').relative_to(ROOT))] = hashlib.sha256(ctrl.encode()).hexdigest()
    rankings={}
    for test in ['Friedman','Quade']:
        chunk=ctrl.split(f'Average Rankings of the algorithms ({test})')[1].split(r'\end{tabular}')[0]
        rankings[test]={a:float(v) for a,v in re.findall(r'^([^&\n]+)&([0-9.]+)\\\\',chunk,re.M)}
    table('rankings_primary.tex','Rankings medios según Friedman y Quade para macro-F1. Análisis principal con un bloque por dataset y biblioteca de 21 descriptores. Menor ranking indica mejor desempeño relativo.','tab:friedman-quade-replica','lrr','Estrategia & Friedman & Quade',[' & '.join([l,'$'+n(rankings['Friedman'][a],3)+'$','$'+n(rankings['Quade'][a],3)+'$']) for a,l in zip(raw_names,LABELS)])
    global_rows = []
    for test, distribution, tail in [('Friedman',r'$\chi^2(4)$',lambda s:chi2.sf(s,4)),('Quade',r'$F(4,12)$',lambda s:f.sf(s,4,12))]:
        statistic = float(re.search(r'^'+test+r' statistic .*freedom: ([0-9.eE+-]+)\.\s',ctrl,re.M).group(1))
        p = float(re.search(r'P-value computed by '+test+r' Test: ([0-9.eE+-]+)\.\\',ctrl).group(1))
        assert abs(tail(statistic)-p)<1e-9, (test, statistic, p)
        global_rows.append(' & '.join([test,distribution,'$'+n(statistic)+'$','$'+n(p)+'$','No rechazo' if p>=0.05 else 'Rechazo']))
    table('global_primary.tex','Contrastes globales del análisis principal de macro-F1, con cuatro datasets y cinco estrategias (21 descriptores). Distribución de referencia y grados de libertad entre paréntesis.','tab:global-primary','llrrl','Prueba & Distribución (gl) & Estadístico & $p$ & Decisión ($\\alpha=0{,}05$)',global_rows)
    old.to_csv(OUT/'baseline_source_rows.csv',index=False)
    new[new.classifier=='resmlp'].to_csv(OUT/'ngram_resmlp_source_rows.csv',index=False)
    new.to_csv(OUT/'ngram21_source_rows.csv',index=False)
    reference.to_csv(OUT/'reference20_source_rows.csv',index=False)
    (OUT/'provenance.json').write_text(json.dumps({'sources_sha256':SOURCE_HASHES,'baseline_conditions':56,'resmlp_ngram_conditions':28,'ngram_svm_included':True,'primary_library_size':21,'ngram_conditions':56,'statistics_sources':[str(np_root/'primary_controltest.tex'),str(np_root/'primary_multipletest.tex')]},indent=2))
    print('Validated 56 reference and 56 complete 21-block conditions; Java inputs match reported results.')

if __name__=='__main__':
    main()
