#!/usr/bin/env python3
"""Three-round paired, same-session online budget timing for Outex/DTD."""
from __future__ import annotations
import argparse,csv,json,subprocess,sys,time
from pathlib import Path
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from run_confirmatory_nested import audit_gate,load_dataset,load_manifest,make_model,official_split_indices
from run_adaptive_descriptor_pilot import margin
from run_online_adaptive_validation import load_extractor,timed_predict

REPO=Path(__file__).resolve().parents[1]
def gpu_state():
    try:
        return subprocess.check_output(["nvidia-smi","--query-gpu=temperature.gpu,utilization.gpu,clocks.current.sm,clocks.current.memory","--format=csv,noheader"],text=True).strip()
    except Exception as e:return f"unavailable: {e}"

def main():
    p=argparse.ArgumentParser(); p.add_argument('--dataset',default='Outex13Official1360'); p.add_argument('--split',type=int,default=1); p.add_argument('--audit-root',type=Path,required=True); p.add_argument('--manifest-root',type=Path,required=True); p.add_argument('--embedding-root',type=Path,required=True); p.add_argument('--pilot',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--n',type=int,default=50); p.add_argument('--warmup',type=int,default=5); p.add_argument('--rounds',type=int,default=3); a=p.parse_args()
    audit=a.audit_root.resolve(); manifest=a.manifest_root.resolve(); emb=a.embedding_root.resolve(); out=a.output.resolve(); pilot=json.loads(a.pilot.read_text())
    audit_gate(manifest,a.dataset); cache,y=load_dataset(REPO,a.dataset,embedding_root=emb); groups,rows=load_manifest(manifest,a.dataset,y); train,test=official_split_indices(rows,a.split)
    if set(groups[train])&set(groups[test]):raise ValueError('group leakage')
    base_x=cache['resnet50']; full_x=np.concatenate([base_x,cache['beitv2_base_final']],axis=1); base_clf,full_clf=make_model('svm',42),make_model('svm',42); base_clf.fit(base_x[train],y[train]); full_clf.fit(full_x[train],y[train])
    indices=test[np.linspace(0,len(test)-1,min(a.n,len(test)),dtype=int)]; paths=[]
    for idx in indices:
        path=Path(rows[int(idx)].get('source_path') or rows[int(idx)]['path']); path=path if path.is_absolute() else REPO/path
        if not path.is_file():raise FileNotFoundError(path)
        paths.append(path)
    device='cuda' if torch.cuda.is_available() else 'cpu'; base=load_extractor('resnet50',device); extra=load_extractor('beitv2_base_final',device)
    budgets=pilot['budgets']; thresholds={float(r['target_budget']):float(r['threshold']) for r in budgets}; qlist=[.25,.5,.75]
    state_start=gpu_state()
    for q in qlist:
        for i in range(a.warmup):
            path=paths[i%len(paths)]; timed_predict(path,'adaptive',base,extra,base_clf,full_clf,thresholds[q],device); timed_predict(path,'full',base,extra,base_clf,full_clf,thresholds[q],device)
    measured=[]; round_stats=[]
    for q in qlist:
        for rnd in range(a.rounds):
            vals={'adaptive':[],'full':[]}; reqs=[]; predmatch=[]
            for j,(idx,path) in enumerate(zip(indices,paths)):
                order=('adaptive','full') if (j+rnd)%2==0 else ('full','adaptive'); both={}
                for pol in order: both[pol]=timed_predict(path,pol,base,extra,base_clf,full_clf,thresholds[q],device)
                for pol in ('adaptive','full'):
                    pred,needed,ms=both[pol]; vals[pol].append(ms)
                    measured.append({'budget':q,'round':rnd+1,'row_id':int(idx),'policy':pol,'latency_ms':ms,'prediction':pred,'request_extra':int(needed)})
                reqs.append(bool(both['adaptive'][1])); predmatch.append(int(both['adaptive'][0])==int(both['full'][0]))
            paired=np.asarray(vals['adaptive'])-np.asarray(vals['full'])
            round_stats.append({'budget':q,'round':rnd+1,'n_images':len(paths),'adaptive_mean_ms':float(np.mean(vals['adaptive'])),'adaptive_median_ms':float(np.median(vals['adaptive'])),'full_mean_ms':float(np.mean(vals['full'])),'full_median_ms':float(np.median(vals['full'])),'mean_paired_difference_adaptive_minus_full_ms':float(np.mean(paired)),'median_paired_difference_ms':float(np.median(paired)),'p50_paired_difference_ms':float(np.percentile(paired,50)),'adaptive_request_fraction':float(np.mean(reqs)),'adaptive_full_prediction_agreement':float(np.mean(predmatch)),'gpu_state_after_round':gpu_state()})
    out.mkdir(parents=True,exist_ok=True); stem=f'{a.dataset}_official{a.split}_online_budget_repeats'
    with (out/f'{stem}_per_image.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(measured[0]));w.writeheader();w.writerows(measured)
    result={'status':'exploratory_paired_same_session_timing','dataset':a.dataset,'official_split':a.split,'n_images':len(paths),'budgets':qlist,'rounds':a.rounds,'device':device,'warmup_per_budget_policy':a.warmup,'model_load_and_svm_fit_excluded':True,'gpu_state_start':state_start,'gpu_state_end':gpu_state(),'round_results':round_stats,'limitations':['Same 50 source images, per-image adaptive/full pairs, same resident models and same Python process.','Subset timing is not external accuracy evidence.','Does not measure Top-k/GFS/full22 descriptor pipelines.']}
    (out/f'{stem}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
