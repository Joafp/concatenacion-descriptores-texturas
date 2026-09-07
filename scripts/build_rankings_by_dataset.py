"""Descriptive within-dataset rankings, averaging the two classifier results."""
import hashlib
import json
import re
import subprocess
import numpy as np
from scipy.stats import rankdata
from build_paper_revision_tables import ROOT, DATASETS, METHODS, LABELS, frame, table, n, dataset_name

def main():
    source=frame('/ngram21')
    destination=ROOT/'results/confirmatory/ngram21/rankings_by_dataset'
    destination.mkdir(exist_ok=True)
    labels=['Individual','Completa','Top-k','GFS','Homogenea']
    ranks={test:{} for test in ['Friedman','Quade']}
    hashes={}
    for dataset in DATASETS:
        matrix=source[source.dataset==dataset].groupby(['classifier','method']).macro_f1.mean().unstack()[METHODS]
        matrix.columns=labels
        matrix.index.name='Classifier'
        path=destination/(dataset_name(dataset)+'.csv')
        matrix.to_csv(path,float_format='%.12f')
        result=subprocess.run(['java','Friedman',str(path)],cwd=ROOT/'.tools/nonparametric/controlTest',capture_output=True,text=True,check=True)
        assert r'\end{document}' in result.stdout
        (destination/(dataset_name(dataset)+'_controltest.tex')).write_text(result.stdout)
        local_ranks=np.array([rankdata(-row) for row in matrix.to_numpy()])
        weights=rankdata(np.ptp(matrix.to_numpy(),axis=1))
        for test in ranks:
            chunk=result.stdout.split(f'Average Rankings of the algorithms ({test})')[1].split(r'\end{tabular}')[0]
            parsed={a:float(v) for a,v in re.findall(r'^([^&\n]+)&([0-9.]+)\\\\',chunk,re.M)}
            expected=local_ranks.mean(axis=0) if test=='Friedman' else np.average(local_ranks,axis=0,weights=weights)
            assert np.allclose([parsed[label] for label in labels],expected)
            ranks[test][dataset]=parsed
        hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    for test in ranks:
        rows=[]
        for key,label in zip(labels,LABELS):
            cells=[]
            for dataset in DATASETS:
                value=ranks[test][dataset][key]
                text=n(value,3)
                if value==min(ranks[test][dataset].values()):
                    text=r'\mathbf{'+text+'}'
                cells.append('$'+text+'$')
            rows.append(' & '.join([label,*cells]))
        table(f'rankings_by_dataset_{test.lower()}.tex',f'Rankings medios por dataset según {test}, calculados sobre macro-F1 para las cinco estrategias y 21 descriptores.','tab:rank-dataset-'+test.lower(),'lrrrr','Estrategia & DTD & FMD & CUReT & Outex',rows,'Se promedian primero las particiones de cada clasificador. Los rankings se calculan dentro de cada dataset usando SVM y ResMLP; el menor de cada columna se destaca. Son resúmenes descriptivos: los clasificadores comparten datos y estos rankings no demuestran significancia estadística.')
    (destination/'provenance.json').write_text(json.dumps({'metric':'macro_f1','classifier_rows_per_dataset':2,'interpretation':'descriptive_only','input_sha256':hashes,'rankings':ranks},indent=2))
    print(json.dumps(ranks,indent=2))

if __name__=='__main__':
    main()
