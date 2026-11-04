"""Coverage ledger from sealed per-dataset reaggregations; never pooled F1 means."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATASETS={'FMD':('fmd',15,3000),'CUReT':('curet',2,5612),'DTD':('dtd',10,18800),
    'Outex13Official1360':('outex',1,680),'SoilOriginal':('soil',15,3420),'KTHTIPS2b':('kth',4,4752)}
PINS={
    ('HyTexNet adapted','FMD'):'43ca6a521b0a03cb0c701d6a587398f5e4d8cac13d78d881b926991184aa9dc8',
    ('HyTexNet adapted','CUReT'):'6f6716fed152aefcccb00978abe16de1f55bd970986e52ea0e71867ccf2bf571',
    ('HyTexNet adapted','DTD'):'82710cc3de9959567c124c03b6b8438bba1308b4fe51f16a47d189fe57553c57',
    ('HyTexNet adapted','SoilOriginal'):'0cdb9d1881e5afa77f953d0865ea175120ce074b27e3f8cda27b20c6a08bcf17',
    ('HyTexNet adapted','KTHTIPS2b'):'b988d2c5fc1768e4998c7bbba99ddbee9ac0573ca126987f28ca3d7446536edd',
    ('LBP+dCellNN adapted','FMD'):'28509cffa320bf36954e682789c6187b09580ea4e48c691bc2e144d9a90c7401',
    ('LBP+dCellNN adapted','CUReT'):'7990d0529d7dc3f69020de0776c9ffec9e1dad1bb5ac918a275aed103e64002f',
    ('LBP+dCellNN adapted','DTD'):'51688085e4f884b421ef44b31d6a464dcb9a99b8cf6e2d650b177428c3158ac9',
    ('LBP+dCellNN adapted','Outex13Official1360'):'fc051d62dcdf7b9967aa7b95d7e734a039b197b29f7b99ee3169d75af5c87497',
    ('LBP+dCellNN adapted','SoilOriginal'):'55e3c517f58651710b7a768dbf2b677cc6709bcc6ba1a526e840f5d94abcbee1',
    ('LBP+dCellNN adapted','KTHTIPS2b'):'5fd8fd876f7b696cfd099d6f5b06b9fd52eace5b38f05d2cc725e141959aec7c'}


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row_from_summary(method,dataset,summary):
    _,expected_n,expected_calls=DATASETS[dataset]
    n=summary.get('unique_conditions',summary.get('conditions'))
    full=n==expected_n and summary['calls']==expected_calls
    if not full:
        if (method!='LBP+dCellNN adapted' or dataset!='FMD' or n!=14 or summary['calls']!=2800
                or summary.get('full_dataset_complete') is not False or summary.get('dataset_means_reported') is not False
                or 'mean_split_macro_f1' in summary or 'mean_ms_all_calls' in summary):
            raise ValueError('partial dataset must not carry means')
    if summary['paper_scores_reproduced'] is not False or summary['same_call_quality_and_timing'] is not True:
        raise ValueError('method fidelity/same-call declaration drift')
    return {'method':method,'dataset':dataset,'status':'complete_dataset' if full else 'incomplete_individual_audits_only',
        'complete_conditions':n,'expected_conditions':expected_n,'audited_online_calls':summary['calls'],
        'expected_online_calls':expected_calls,'full_dataset_complete':full,
        'mean_split_macro_f1':summary['mean_split_macro_f1'] if full else None,
        'mean_ms_all_calls':summary['mean_ms_all_calls'] if full else None}


def build(output):
    output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    rows=[];sources={}
    for method,prefix in (('HyTexNet adapted','hytex'),('LBP+dCellNN adapted','cellnn')):
        for dataset,(slug,n,calls) in DATASETS.items():
            if (method,dataset) not in PINS:
                state=ROOT/'results/analysis/hytex_outex_external_queue_20261102_v1/tasks/HyTex_Outex13Official1360_s42_f0/state.json'
                if json.loads(state.read_text())['status']!='requires_review': raise ValueError('Outex disposition changed')
                sources[str(state)]=digest(state)
                rows.append({'method':method,'dataset':dataset,'status':'requires_review_not_measured',
                    'complete_conditions':0,'expected_conditions':n,'audited_online_calls':0,
                    'expected_online_calls':calls,'full_dataset_complete':False,
                    'mean_split_macro_f1':None,'mean_ms_all_calls':None})
                continue
            path=ROOT/f'results/analysis/{prefix}_{slug}_external_summary_20261102_v1/summary.json'
            if method=='LBP+dCellNN adapted' and dataset=='FMD':
                path=ROOT/'results/analysis/cellnn_fmd_individual_audits_20261102_v1/summary.json'
            if digest(path)!=PINS[method,dataset]: raise ValueError('sealed summary drift: '+str(path))
            summary=json.loads(path.read_text());row=row_from_summary(method,dataset,summary)
            sources[str(path)]=digest(path)
            for filename in ('provenance.json','condition_metrics.csv','comparison_by_condition.csv'):
                source=path.parent/filename;sources[str(source)]=digest(source)
            if row['full_dataset_complete']:
                source=path.parent/'comparison_dataset.csv';sources[str(source)]=digest(source)
            rows.append(row)
    coverage={}
    for method in ('HyTexNet adapted','LBP+dCellNN adapted'):
        part=[r for r in rows if r['method']==method]
        coverage[method]={'complete_datasets':sum(r['full_dataset_complete'] for r in part),
            'expected_datasets':6,'complete_conditions':sum(r['complete_conditions'] for r in part),
            'expected_conditions':47,'audited_online_calls':sum(r['audited_online_calls'] for r in part),
            'expected_online_calls':36264,'six_dataset_panel_complete':all(r['full_dataset_complete'] for r in part)}
    if (coverage['HyTexNet adapted']['audited_online_calls']!=35584
            or coverage['LBP+dCellNN adapted']['audited_online_calls']!=36064
            or any(r['six_dataset_panel_complete'] for r in coverage.values())):
        raise ValueError('coverage arithmetic changed')
    sources[str(Path(__file__).resolve())]=digest(__file__)
    report={'status':'PER_DATASET_COVERAGE_ONLY_BOTH_SIX_DATASET_PANELS_INCOMPLETE',
        'coverage':coverage,'pooled_f1_or_latency_reported':False,'faithful_paper_percentage_reproductions':0,
        'reservations':['adaptations, not original published scores','shared hardware and separate measurement dates',
            'KTH historical and DTD physical reserves retained','CellNN FMD42/f0 and HyTex Outex not retried'],
        'rows':rows}
    output.mkdir(parents=True,exist_ok=False)
    with (output/'coverage.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (output/'coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'provenance.json').write_text(json.dumps(sources,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'coverage':coverage,'coverage_sha256':digest(output/'coverage.json')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args().output)
