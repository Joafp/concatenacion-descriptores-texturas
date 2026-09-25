"""Publish classifier-separated SCI2S results and exact sensitivity checks."""
import re
import json
import numpy as np
from scipy.stats import wilcoxon
from build_primary20_soil import load, DATASETS, METHODS, LABELS, ROOT, OUT, NP_OUT, tex_table, number

def main():
    df = load()
    base = NP_OUT / 'classifier_specific'
    rankings, globals_, pairs, checks = [], [], [], []
    for clf, label in [('svm', 'SVM'), ('resmlp', 'ResMLP')]:
        text = (base / f'{clf}_controltest.tex').read_text()
        rankcols = []
        for test in ['Friedman', 'Quade']:
            chunk = text.split(f'Average Rankings of the algorithms ({test})')[1].split(r'\end{tabular}')[0]
            values = dict((k.strip(), float(v)) for k,v in re.findall(r'^([^&\n]+)&([0-9.]+)\\\\', chunk, re.M))
            rankcols.append(values)
        for name in LABELS:
            rankings.append(' & '.join([label, name, *[number(c[name],3) for c in rankcols]]))
        for test in ['Friedman', 'Quade']:
            p = float(re.search(r'P-value computed by '+test+r' Test: ([0-9.Ee+-]+)',text)[1].rstrip('.'))
            globals_.append(f'{label} & {test} & {number(p)} & '+('Rechazo' if p < .05 else 'No rechazo'))
        multiple = (base / f'{clf}_multipletest.tex').read_text().split('i&hypothesis&unadjusted')[1]
        for line in multiple.splitlines():
            cols=line.rstrip('\\').split('&')
            if len(cols)==7 and cols[0].isdigit():
                raw, adjusted=float(cols[2]),min(1.,float(cols[4]))
                comparison = cols[1].replace('vs .', 'vs. ')
                pairs.append(f'{label} & {comparison} & {number(raw)} & {number(adjusted)}')
        matrix=df[df.classifier.eq(clf)].groupby(['dataset','method']).macro_f1.mean().unstack().loc[DATASETS]
        delta=matrix.full_concat-matrix.best_individual
        test=wilcoxon(delta,alternative='two-sided',method='exact')
        checks.append((label, float(delta.mean()),int((delta>0).sum()),float(test.statistic),float(test.pvalue)))
    tex_table('classifier_rankings.tex','Rankings medios de macro-F1 según Friedman y Quade. Seis datasets por clasificador; menor ranking indica mejor desempeño relativo.','tab:classifier-rankings','llrr','Clasif. & Estrategia & Friedman & Quade',rankings)
    tex_table('classifier_global.tex','Pruebas globales por clasificador sobre cinco estrategias y seis datasets, calculadas con SCI2S. Nivel nominal $\\alpha=0{,}05$.','tab:classifier-global','llrl','Clasif. & Prueba & $p$ & Decisión',globals_)
    tex_table('classifier_holm.tex','Comparaciones por pares basadas en rangos de Friedman (MULTIPLETEST). Holm se aplica a los diez pares dentro de cada clasificador; valores ajustados limitados a 1. El panel ResMLP es exploratorio dado que su Friedman global no rechaza.','tab:classifier-holm','llrr','Clasif. & Comparación & $p$ sin ajustar & $p$ Holm',pairs)
    tex_table('classifier_sensitivity.tex','Sensibilidad: Completa menos Individual mediante Wilcoxon exacto bilateral, seis pares por clasificador. Valores $p$ sin ajuste; V indica datasets con diferencia positiva y $W$ la menor suma de rangos.','tab:classifier-sensitivity','lrrrr','Clasif. & $\\Delta$ medio & V/6 & $W$ & $p$', [f'{c} & {number(d)} & {v}/6 & {number(w,0)} & {number(p)}' for c,d,v,w,p in checks])
    (base/'paper_validation.json').write_text(json.dumps({'n_blocks':6,'classifiers_separate':True,'holm_family_size':10,'sensitivity':checks},indent=2))

if __name__=='__main__':
    main()
