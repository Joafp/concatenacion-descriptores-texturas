"""Validate the complete 21-block experiment and run the original SCI2S Java tests."""
import json
import subprocess
import pandas as pd
from build_paper_revision_tables import ROOT, frame, SOURCE_HASHES
from build_nonparametric_analysis import validation

OUT = ROOT/'results/confirmatory/ngram21/nonparametric'
NAMES = {'gfs':'GFS','topk_individual':'Top-k','full_concat':'Completa',
         'best_individual':'Individual','homogeneous':'Homogenea'}

def main():
    df = frame('/ngram21')
    OUT.mkdir(exist_ok=True)
    means = df.groupby(['dataset','classifier','method']).macro_f1.mean().unstack()
    means = means.rename(columns=NAMES)[list(NAMES.values())]
    means.index = pd.MultiIndex.from_tuples([(d.replace('Outex13Official1360','Outex'),c) for d,c in means.index],names=['dataset','classifier'])
    primary = means.groupby(level='dataset').mean()
    sensitivity = means.copy()
    sensitivity.index = [f'{d}-{c.upper()}' for d,c in sensitivity.index]
    records=[]
    for scope, matrix, name in [('primary',primary,'primary_by_dataset'),('sensitivity',sensitivity,'sensitivity_dataset_classifier')]:
        matrix.index.name='Data-set'
        csv=OUT/(name+'.csv')
        matrix.to_csv(csv,float_format='%.12f')
        records.append(validation(name,pd.read_csv(csv)))
        for kind,folder in [('controltest','controlTest'),('multipletest','multipleTest')]:
            result=subprocess.run(['java','Friedman',str(csv)],cwd=ROOT/'.tools/nonparametric'/folder,capture_output=True,text=True,check=True)
            assert '\\end{document}' in result.stdout
            (OUT/f'{scope}_{kind}.tex').write_text(result.stdout)
    (OUT/'validation.json').write_text(json.dumps({'library_size':21,'conditions':56,'rows':len(df),'source_sha256':SOURCE_HASHES,'analyses':records},indent=2))
    print(primary.to_string())
    print(json.dumps(records,indent=2))

if __name__=='__main__':
    main()
