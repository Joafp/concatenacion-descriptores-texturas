"""Verify raw CellNN calls/receipts; aggregate datasets ONLY at full coverage."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from consolidate_overnight_online_panel import read,digest
from consolidate_hytex_fmd_external import LOCAL_SHA,write_csv
from run_authorized_remediation_queue import verify_sources
from run_cellnn_external_condition import audit_records
from cellnn_online_adapter import METHOD

EXPECTED={'FMD':(15,3000),'CUReT':(2,5612),'DTD':(10,18800),
    'Outex13Official1360':(1,680),'SoilOriginal':(15,3420),'KTHTIPS2b':(4,4752)}


def coverage(dataset,partitions,calls,partial):
    n,expected=EXPECTED[dataset]
    ids={(p['seed'],p['outer_fold']) for p in partitions}
    expected_ids=({(s,f) for s in (42,123,2026) for f in range(5)}
        if dataset in ('FMD','SoilOriginal') else {(42,f) for f in range(n)})
    if len(ids)!=len(partitions) or any(p['dataset']!=dataset for p in partitions):
        raise ValueError('condition identity drift')
    full=ids==expected_ids and calls==expected
    if not full and not (partial and dataset=='FMD' and ids==expected_ids-{(42,0)} and calls==2800):
        raise ValueError('complete dataset required for aggregation')
    return full


def consolidate(queue,output,dataset,partial=False):
    queue,output=Path(queue).resolve(),Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    manifest,worker,frozen=[read(queue/n) for n in ('manifest.json','gpu.json','preflight.json')]
    if worker['status']!='all_tasks_terminal' or worker['current_task'] is not None or worker['manifest_sha256']!=digest(queue/'manifest.json'):
        raise ValueError('terminal queue required')
    verify_sources(manifest)
    parts=frozen['conditions'];full=coverage(dataset,parts,sum(len(p['external_indices']) for p in parts),partial)
    if len(parts)!=len(manifest['tasks']): raise ValueError('task count drift')
    sources={**manifest['source_sha256'],**{str(queue/n):digest(queue/n) for n in ('manifest.json','gpu.json','preflight.json')}}
    records=[]
    for task,p in zip(manifest['tasks'],parts):
        name=f'CellNN_{dataset}_s{p["seed"]}_f{p["outer_fold"]}'
        sp=queue/'tasks'/name/'state.json';state=read(sp)
        if (task['id']!=name or worker['outcomes'].get(name)!='complete' or state['status']!='complete'
                or state['manifest_sha256']!=digest(queue/'manifest.json') or len(state['success_artifacts'])!=4):
            raise ValueError('complete matching condition required')
        job=queue/'jobs'/name;stages={}
        for stage,receipt,command in zip(('extract','train','online','audit'),state['success_artifacts'],task['commands']):
            path=job/stage/'status.json';s=read(path)
            if (receipt['path']!=str(path) or digest(path)!=receipt['sha256'] or receipt['condition']!=command['success']
                    or s['status']!=stage+'_complete' or s['partition']!=p or s['method']!=METHOD
                    or s['manifest_sha256']!=digest(queue/'preflight.json')):
                raise ValueError('stage identity/receipt mismatch')
            for filename,sha in s['output_sha256'].items():
                file=job/stage/filename
                if digest(file)!=sha: raise ValueError('artifact drift')
                sources[str(file)]=sha
            sources[str(path)]=digest(path);stages[stage]=s
        for downstream,key,upstream in (('train','extraction_status_sha256','extract'),
            ('online','head_status_sha256','train'),('audit','online_status_sha256','online')):
            if stages[downstream][key]!=digest(job/upstream/'status.json'): raise ValueError('stage chain drift')
        with Path(p['manifest']).open(newline='') as stream: rows=list(csv.DictReader(stream))
        calls=[json.loads(line) for line in (job/'online/calls.jsonl').read_text().splitlines()]
        metrics=audit_records(calls,p,rows);summary=read(job/'audit/summary.json')
        for key,value in metrics.items():
            if isinstance(value,(int,float)):
                if abs(summary[key]-value)>1e-12: raise ValueError('raw metric disagreement')
            elif summary[key]!=value: raise ValueError('raw call declaration disagreement')
        records.append({'dataset':dataset,'seed':p['seed'],'outer_fold':p['outer_fold'],**metrics})
        sources[str(sp)]=digest(sp)
    coverage(dataset,parts,sum(r['calls'] for r in records),partial)
    local_path=ROOT/'results/analysis/blocker_resolution_20261101/full_panel_online_v1/condition_summary.csv'
    if digest(local_path)!=LOCAL_SHA: raise ValueError('local frozen table drift')
    lookup={(r['seed'],r['outer_fold']):r for r in records};comparisons=[]
    with local_path.open(newline='') as stream:
        for row in csv.DictReader(stream):
            key=(int(row['seed']),int(row['outer_fold']))
            if row['dataset']!=dataset or key not in lookup: continue
            ref=lookup[key]
            if int(row['calls'])!=ref['calls']: raise ValueError('local/reference image count differs')
            comparisons.append({'dataset':dataset,'seed':key[0],'outer_fold':key[1],
                'local_classifier':row['classifier'],'local_method':row['method'],'reference_method':METHOD,
                'local_f1':float(row['macro_f1_online']),'reference_f1':ref['macro_f1_online'],
                'delta_f1_local_minus_reference':float(row['macro_f1_online'])-ref['macro_f1_online'],
                'local_mean_ms':float(row['mean_ms']),'reference_mean_ms':ref['mean_ms'],
                'calls':ref['calls'],'latency_ratio_reference_over_local':ref['mean_ms']/float(row['mean_ms']),
                'physical_timing_reserve_local':row['physical_timing_reserve']})
    if len(comparisons)!=10*len(records): raise ValueError('all local comparator pairs required')
    summary={'status':'COMPLETE_DATASET_ADAPTATION_REAGGREGATED' if full else 'INCOMPLETE_FMD_INDIVIDUAL_AUDITS_ONLY',
        'dataset':dataset,'method':METHOD,'conditions':len(records),'expected_conditions':EXPECTED[dataset][0],
        'calls':sum(r['calls'] for r in records),'full_dataset_complete':full,
        'dataset_means_reported':full,'paper_scores_reproduced':False,'global_inference_performed':False,
        'same_call_quality_and_timing':True,'reservations':['shared hardware and separate measurement times',
            'local common-panel adaptation; not source percentages','retain KTH historical and DTD physical timing reserves']}
    dataset_rows=[]
    if full:
        summary['mean_split_macro_f1']=statistics.mean(r['macro_f1_online'] for r in records)
        summary['mean_ms_all_calls']=sum(r['mean_ms']*r['calls'] for r in records)/summary['calls']
        groups=defaultdict(list)
        for row in comparisons: groups[row['local_classifier'],row['local_method']].append(row)
        for (classifier,method),group in sorted(groups.items()):
            dataset_rows.append({'dataset':dataset,'local_classifier':classifier,'local_method':method,
                'reference_method':METHOD,'conditions':len(group),
                'local_mean_split_f1':statistics.mean(r['local_f1'] for r in group),
                'reference_mean_split_f1':statistics.mean(r['reference_f1'] for r in group),
                'mean_delta_f1_local_minus_reference':statistics.mean(r['delta_f1_local_minus_reference'] for r in group),
                'local_mean_ms_all_calls':sum(r['local_mean_ms']*r['calls'] for r in group)/sum(r['calls'] for r in group),
                'reference_mean_ms_all_calls':summary['mean_ms_all_calls'],
                'physical_timing_reserve_local':any(r['physical_timing_reserve_local'].lower()=='true' for r in group)})
    sources[str(local_path)]=LOCAL_SHA;sources[str(Path(__file__).resolve())]=digest(__file__)
    output.mkdir(parents=True,exist_ok=False)
    write_csv(output/'condition_metrics.csv',records);write_csv(output/'comparison_by_condition.csv',comparisons)
    if full: write_csv(output/'comparison_dataset.csv',dataset_rows)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'provenance.json').write_text(json.dumps(sources,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--queue',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--dataset',choices=sorted(EXPECTED),required=True)
    parser.add_argument('--individual-audits-only',action='store_true');a=parser.parse_args()
    consolidate(a.queue,a.output,a.dataset,a.individual_audits_only)
