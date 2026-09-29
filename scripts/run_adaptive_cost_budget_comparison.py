#!/usr/bin/env python3
"""Exploratory matched-split accuracy for adaptive acquisition budgets.

Uses only train-side grouped OOF margins to derive each threshold. Embeddings
are cached: this script measures accuracy, not image-to-prediction latency.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, sys, time
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from run_confirmatory_nested import (audit_gate, load_dataset, load_manifest,
    make_model, official_split_indices)
from curet_confirmatory_protocol import curet_half_indices
from run_adaptive_descriptor_pilot import margin, metrics

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def run(dataset, split, direction, audit_root, manifest_root, embedding_root,
        output, repeats, budgets):
    started=time.perf_counter()
    audit_root,manifest_root,embedding_root,output=[p.resolve() for p in (audit_root,manifest_root,embedding_root,output)]
    audit_gate(audit_root,dataset)
    cache,y=load_dataset(REPO,dataset,embedding_root)
    groups,rows=load_manifest(manifest_root,dataset,y)
    if dataset=='CUReT': train,test=curet_half_indices(rows,direction)
    else: train,test=official_split_indices(rows,split)
    if set(groups[train]) & set(groups[test]): raise AssertionError('outer group leakage')
    base=cache['resnet50']; full=np.concatenate([base,cache['beitv2_base_final']],axis=1)
    bm,fm=make_model('svm',42),make_model('svm',42)
    bm.fit(base[train],y[train]); fm.fit(full[train],y[train])
    pb=np.asarray(bm.predict(base[test])); pf=np.asarray(fm.predict(full[test])); tm=margin(bm,base[test])
    inner=StratifiedGroupKFold(n_splits=4,shuffle=True,random_state=43)
    oof=np.full(len(train),np.nan); inner_classes=[]
    for itr,ival in inner.split(base[train],y[train],groups[train]):
        m=make_model('svm',42); m.fit(base[train[itr]],y[train[itr]])
        oof[ival]=margin(m,base[train[ival]])
        inner_classes.append(int(len(np.unique(y[train[itr]]))))
    if not np.isfinite(oof).all() or min(inner_classes)!=len(np.unique(y[train])):
        raise ValueError(f'{dataset} {direction or split}: invalid OOF coverage/classes')
    labels=np.unique(y); result={'dataset':dataset,'protocol':f'official{split}' if dataset!='CUReT' else f'curet_half_indices:{direction}',
        'seed':42,'n_train':len(train),'n_test':len(test),'n_classes':len(labels),
        'inner_folds':4,'inner_train_classes':inner_classes,'groups_intersection':0,
        'threshold_source':'quantiles of 4-fold StratifiedGroupKFold OOF margins on outer train only',
        'base_only':metrics(y[test],pb,labels),'two_blocks_always':metrics(y[test],pf,labels),'budgets':[],
        'provenance':{'audit_sha256':sha(audit_root/'data_audit.csv'),
          'manifest_sha256':sha(manifest_root/'sample_manifests'/f'{dataset}.csv'),
          'resnet50_sha256':sha(embedding_root/({'KTHTIPS2b':'KTH-TIPS2-b'}.get(dataset,dataset))/'resnet50.npy'),
          'beitv2_final_sha256':sha(embedding_root/({'KTHTIPS2b':'KTH-TIPS2-b'}.get(dataset,dataset))/'beitv2_base_final.npy'),
          'resnet50_labels_sha256':sha(embedding_root/({'KTHTIPS2b':'KTH-TIPS2-b'}.get(dataset,dataset))/'resnet50_labels.npy'),
          'beitv2_labels_sha256':sha(embedding_root/({'KTHTIPS2b':'KTH-TIPS2-b'}.get(dataset,dataset))/'beitv2_base_final_labels.npy'),
          'runner_sha256':sha(Path(__file__))},
        'latency':'NOT_MEASURED: cached embeddings; no E2E timing implied'}
    samples=[]; rng=np.random.default_rng(4200+split+(0 if direction=='a_to_b' else 1))
    for q in budgets:
        threshold=float(np.quantile(oof,q)); req=tm<=threshold
        pred=np.where(req,pf,pb); n=int(req.sum()); rand=[]
        for _ in range(repeats):
            mask=np.zeros(len(test),bool); mask[rng.choice(len(test),n,replace=False)]=True
            rand.append(metrics(y[test],np.where(mask,pf,pb),labels))
        row={'target_budget':q,'threshold':threshold,'observed_request_fraction':float(req.mean()),
          'adaptive':metrics(y[test],pred,labels),'random_same_count_mean_macro_f1':float(np.mean([x['macro_f1'] for x in rand])),
          'random_same_count_sd_macro_f1':float(np.std([x['macro_f1'] for x in rand],ddof=1)),
          'random_same_count_mean_accuracy':float(np.mean([x['accuracy'] for x in rand])),'random_repeats':repeats}
        result['budgets'].append(row)
        for j,idx in enumerate(test): samples.append({'budget':q,'row_id':int(idx),'label':int(y[idx]),'base_pred':int(pb[j]),'full_pred':int(pf[j]),'adaptive_pred':int(pred[j]),'margin':float(tm[j]),'request_extra':int(req[j])})
    result['duration_seconds']=time.perf_counter()-started
    output.mkdir(parents=True,exist_ok=True); tag=direction or f'official{split}'; stem=f'{dataset}_{tag}_budgets'
    (output/f'{stem}.json').write_text(json.dumps(result,indent=2)+'\n')
    with (output/f'{stem}_per_sample.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(samples[0])); w.writeheader(); w.writerows(samples)
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument('--dataset',required=True); p.add_argument('--split',type=int,default=1); p.add_argument('--direction',choices=['a_to_b','b_to_a']); p.add_argument('--audit-root',type=Path,required=True); p.add_argument('--manifest-root',type=Path,required=True); p.add_argument('--embedding-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--repeats',type=int,default=100); a=p.parse_args()
    if a.dataset=='CUReT' and not a.direction: p.error('CUReT requires --direction')
    print(json.dumps(run(a.dataset,a.split,a.direction,a.audit_root,a.manifest_root,a.embedding_root,a.output,a.repeats,(.25,.5,.75)),indent=2))
if __name__=='__main__': main()
