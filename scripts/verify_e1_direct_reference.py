"""Compare new E1 direct predictions with the existing fixed-four CSV reference."""
from pathlib import Path
import json
import pandas as pd
from prepare_top4_fixed_cascade import sha256

ROOT=Path(__file__).resolve().parents[1]
audit=ROOT/'results/analysis/top4_fixed_e1_e2_audit_20261115_v1'
paths=sorted((ROOT/'results/exploratory/k_sweep').glob('*/k_sweep.csv'))
reference=pd.concat([pd.read_csv(p) for p in paths],ignore_index=True)
reference=reference[(reference.classifier=='svm') & (reference.seed==42) & (reference.k==4)]
rows=[]
for row in pd.read_csv(audit/'e1_conditions.csv').itertuples():
    fold=int(row.id.rsplit('_f',1)[1])
    old=reference[(reference.dataset==row.dataset) & (reference.outer_fold==fold)]
    assert len(old)==1
    old=old.iloc[0]
    rows.append(dict(id=row.id,dataset=row.dataset,outer_fold=fold,
                     new_direct_accuracy=row.direct_accuracy,saved_accuracy=float(old.accuracy),
                     accuracy_delta=row.direct_accuracy-float(old.accuracy),
                     new_direct_macro_f1=row.direct_macro_f1,saved_macro_f1=float(old.macro_f1),
                     macro_f1_delta=row.direct_macro_f1-float(old.macro_f1)))
d=pd.DataFrame(rows)
assert len(d)==25
output=audit/'direct_reference_comparison.csv'
d.to_csv(output,index=False)
receipt={'conditions':len(d),'max_absolute_accuracy_delta':float(d.accuracy_delta.abs().max()),
         'max_absolute_macro_f1_delta':float(d.macro_f1_delta.abs().max()),
         'scope':'cached representation replay, not an independent RGB benchmark',
         'script_sha256':sha256(Path(__file__)),
         'sources':{str(p.relative_to(ROOT)):sha256(p) for p in paths+[audit/'e1_conditions.csv']},
         'output_sha256':sha256(output)}
(audit/'direct_reference_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='sources'},indent=2))
