"""Render saved historical accuracy/cost values with separated labels."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'results/analysis/thesis_accuracy_primary_20261115_v3/historical_cascade.csv'
generated=ROOT/'paper/generated_accuracy_primary_20261115_v3'
d=pd.read_csv(source).groupby('dataset').mean(numeric_only=True)
names={'DTD':'DTD','FMD':'FMD','CUReT':'CUReT','Outex13Official1360':'Outex-13','SoilOriginal':'Soil','KTHTIPS2b':'KTH-TIPS2b'}
fig,axes=plt.subplots(1,2,figsize=(10.4,4),layout='constrained')
for ax,metric in zip(axes,['accuracy','projected_ms']):
    x,y=d[f'direct_{metric}'],d[f'conditional_{metric}']
    ax.scatter(x,y,color='#176c84')
    offsets=({'KTHTIPS2b':(-40,12),'Outex13Official1360':(5,-13)} if metric=='accuracy' else
             {'DTD':(5,18),'CUReT':(5,-13),'Outex13Official1360':(6,0),'FMD':(-20,-18),'SoilOriginal':(-20,12),'KTHTIPS2b':(-36,-18)})
    for ds in d.index:
        ax.annotate(names[ds],(x[ds],y[ds]),xytext=offsets.get(ds,(5,5)),textcoords='offset points',fontsize=8)
    lo,hi=min(x.min(),y.min()),max(x.max(),y.max())
    pad=max((hi-lo)*.16,.005)
    ax.plot([lo-pad,hi+pad],[lo-pad,hi+pad],'--',color='.6')
    ax.set(xlabel='Directo: '+('accuracy' if metric=='accuracy' else 'costo proyectado (ms)'),
           ylabel='Margen: '+('accuracy' if metric=='accuracy' else 'costo proyectado (ms)'),
           xlim=(lo-pad,hi+pad),ylim=(lo-pad,hi+pad))
    ax.spines[['top','right']].set_visible(False)
for ext in ['pdf','png']:
    fig.savefig(generated/f'directo_margen_legible.{ext}',dpi=170)
plt.close(fig)
receipt={'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
         'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'outputs':{f'directo_margen_legible.{ext}':hashlib.sha256((generated/f'directo_margen_legible.{ext}').read_bytes()).hexdigest() for ext in ['pdf','png']},
         'data_changed':False}
(ROOT/'results/analysis/thesis_accuracy_primary_20261115_v3/figure_layout_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
