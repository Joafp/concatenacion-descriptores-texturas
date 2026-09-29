#!/usr/bin/env python3
"""Measure real Outex image->descriptor costs on one matched 50-image test subset.

Extractor model loading and SVM fit are excluded. RGB N-gram is reported as
unavailable because its train-fold-fitted SVD route is not implemented here.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,sys,time
from pathlib import Path
import numpy as np, torch
from PIL import Image
from sklearn.metrics import accuracy_score,f1_score
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
REPO=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(REPO/'src'))
from run_confirmatory_nested import audit_gate,load_dataset,load_manifest,make_model,official_split_indices

def l2(x):
 x=np.asarray(x,dtype=np.float32); return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def sh(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def module_from_file(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def gpu_sync():
 if torch.cuda.is_available():torch.cuda.synchronize()
def main():
 p=argparse.ArgumentParser();p.add_argument('--audit-root',type=Path,required=True);p.add_argument('--manifest-root',type=Path,required=True);p.add_argument('--embedding-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--n',type=int,default=50);a=p.parse_args()
 audit,manifest,emb,out=[x.resolve() for x in (a.audit_root,a.manifest_root,a.embedding_root,a.output)];ds='Outex13Official1360';audit_gate(audit,ds);cache,y=load_dataset(REPO,ds,embedding_root=emb);groups,rows=load_manifest(manifest,ds,y);train,test=official_split_indices(rows,1)
 indices=test[np.linspace(0,len(test)-1,min(a.n,len(test)),dtype=int)];paths=[];source_hashes=[]
 for idx in indices:
  q=Path(rows[int(idx)].get('source_path') or rows[int(idx)]['path']);q=q if q.is_absolute() else REPO/q
  if not q.is_file():raise FileNotFoundError(q)
  expected=rows[int(idx)].get('source_sha256') or rows[int(idx)].get('sha256')
  if not expected or sh(q)!=expected:raise ValueError(f'source SHA mismatch: row {idx}')
  source_hashes.append(expected);paths.append(q)
 base=module_from_file('legacy_extractors',REPO/'src'/'01_extract_features.py'); sota=module_from_file('sota_extractors',REPO/'src'/'extract_sota_2024.py'); sota.DEVICE='cuda' if torch.cuda.is_available() else 'cpu'; device=sota.DEVICE
 topk_csv=manifest.parent.parent/'extensions'/'outex13_official1360'/'ngram22_beitv2'/'topk_individual_control'/'nested_fold_results.csv'
 # Caller-provided locations may not correspond to a confirmatory checkout; resolve canonical files.
 topk_csv=REPO/'results/extensions/outex13_official1360/ngram22_beitv2/topk_individual_control/nested_fold_results.csv'
 main_csv=REPO/'results/extensions/outex13_official1360/ngram22_beitv2/nested_fold_results.csv'
 def find_row(path,method):
  with path.open(newline='') as f:
   rows0=[r for r in csv.DictReader(f) if r['classifier']=='svm' and r['seed']=='42' and r['outer_fold']=='0' and r['method']==method]
  if len(rows0)!=1:raise ValueError(f'baseline row not unique: {path} {method}')
  return rows0[0]
 baselines={'Top-k22':find_row(topk_csv,'topk_individual'),'GFS':find_row(main_csv,'gfs'),'full22':find_row(main_csv,'full_concat')}
 selections={k:r['selected'].split('+') for k,r in baselines.items()}
 ngram_counts=None
 if any('rgb_ngram_svd' in names for names in selections.values()):
  from rgb_ngram_descriptor import _manifest_digest,RGBNgramSVDBlock
  count_dir=REPO/'results/extensions/outex13_official1360/rgb_ngram_count_cache/Outex13Official1360/rgb_ngram_impl1'
  metadata=json.loads((count_dir/'metadata.json').read_text())
  if metadata.get('manifest_sha256')!=_manifest_digest(rows,REPO) or metadata.get('samples')!=len(rows):raise ValueError('label-free count cache manifest mismatch')
  ngram_counts={k:np.load(count_dir/f'{k}.npy',mmap_mode='r') for k in ('keys','counts','indptr')}
  ng_train,ng_test,ng_audit=RGBNgramSVDBlock(ngram_counts,n_components=256,random_state=42,hash_bins=8192).transform(train,test)
  ng_full=np.empty((len(y),256),dtype=np.float32);ng_full[train]=ng_train;ng_full[test]=ng_test;cache['rgb_ngram_svd']=ng_full
 name_union=list(dict.fromkeys(n for ns in selections.values() for n in ns))
 # Load SVMs on the exact archived training embeddings/subsets.
 models={}
 for method,names in selections.items():
  xtr=np.concatenate([cache[n][train] for n in names],axis=1); clf=make_model('svm',42); clf.fit(xtr,y[train]);models[method]=clf
 timings={}; extracted={}; cosines={}; failed={}
 for name in name_union:
  try:
   if name=='rgb_ngram_svd':
    from run_rgb_ngram_outex_official import count_image
    from rgb_ngram_descriptor import RGBNgramSVDBlock
    counts=ngram_counts
    block0=RGBNgramSVDBlock(counts,n_components=256,random_state=42,hash_bins=8192)
    svd=TruncatedSVD(n_components=256,algorithm='randomized',n_iter=5,random_state=42)
    svd.fit_transform(block0._hashed_rows(train))
    def fn(path,svd=svd):
     with Image.open(path) as im: rgb=np.asarray(im.convert('RGB'),dtype=np.uint8)
     keys,values=count_image(rgb,'rgb_ngram_impl1'); bins=np.asarray(keys,dtype=np.uint64)%np.uint64(8192); order=np.argsort(bins,kind='stable'); bins,values=bins[order],np.asarray(values,dtype=np.float32)[order]; unique,starts=np.unique(bins,return_index=True); summed=np.add.reduceat(values,starts)
     from scipy import sparse
     row=sparse.csr_matrix((summed,unique,np.asarray([0,len(unique)],dtype=np.int32)),shape=(1,8192),dtype=np.float32)
     return normalize(svd.transform(row).astype(np.float32,copy=False),norm='l2',copy=False)[0]
   elif name=='beitv2_base_final':
    from run_online_adaptive_validation import load_extractor,extract
    ext=load_extractor(name,device)
    fn=lambda path:extract(path,*ext,device)[0]
   elif name in {'eva02_base','mae_base','siglip_base'}:
    model,transform,kind=sota.load_model_and_transform(name)
    def fn(path,model=model,transform=transform,kind=kind):
     with Image.open(path) as im: tensor=transform(im.convert('RGB')).unsqueeze(0).to(device)
     with torch.inference_mode():
      if kind=='timm': feat=model(tensor)
      else:
       out0=model(pixel_values=tensor); feat=out0.pooler_output if getattr(out0,'pooler_output',None) is not None else out0.last_hidden_state[:,0]
     return feat.cpu().numpy()[0]
   else:
    ext=base.get_extractor(name,device=device)
    if getattr(ext,'method',None):
     def fn(path,ext=ext):
      gray=ext._load_gray(str(path)); method={'lbp_multiscale':ext._lbp_multiscale,'glcm':ext._glcm,'gabor':ext._gabor,'hog':ext._hog,'drlbp':ext._drlbp}[ext.method]; return method(gray)
    else:
     def fn(path,ext=ext):return ext.extract([str(path)],batch_size=1)[0]
   # Two excluded warmups; synchronize GPU at boundaries.
   fn(paths[0]);fn(paths[1]);gpu_sync();block=[];ms=[]
   for path in paths:
    gpu_sync();t=time.perf_counter(); feat=fn(path);gpu_sync();ms.append((time.perf_counter()-t)*1000);block.append(np.asarray(feat,dtype=np.float32))
   arr=l2(np.stack(block)); extracted[name]=arr; timings[name]=ms
   ref=cache[name][indices]; cosines[name]=np.sum(arr*l2(ref),axis=1).tolist()
   # Rebinding these locals on the next iteration releases the prior model.
  except Exception as e:
   failed[name]=f'{type(e).__name__}: {e}'
 # Method route estimate: sum real single-block image pipeline durations + measured predict call.
 method_results={}
 for method,names in selections.items():
  available=[n for n in names if n in extracted]
  missing=[n for n in names if n not in extracted]
  route_ms=[]; pred_agreement=[]; cosmin={n:float(np.min(cosines[n])) for n in available}
  if available:
   feats=np.concatenate([extracted[n] for n in available],axis=1)
   pred=[]; clf=models.get(method)
   if clf is not None:
    for i in range(len(indices)):
     gpu_sync();t=time.perf_counter();pred.append(int(clf.predict(feats[i:i+1])[0]));predms=(time.perf_counter()-t)*1000
     route_ms.append(sum(timings[n][i] for n in available)+predms)
    pred_agreement=[int(pred[i])==int(clf.predict(np.concatenate([cache[n][indices[i:i+1]] for n in names],axis=1))[0]) for i in range(len(indices))]
  method_results[method]={'selected':names,'measured_extractors':available,'missing':missing,'complete_route':not missing,'mean_image_to_prediction_ms_partial_or_complete':float(np.mean(route_ms)) if route_ms else None,'median_ms':float(np.median(route_ms)) if route_ms else None,'p95_ms':float(np.percentile(route_ms,95)) if route_ms else None,'prediction_agreement_vs_cached_baseline':float(np.mean(pred_agreement)) if pred_agreement else None,'extractor_min_cosine':cosmin,'baseline_macro_f1':float(baselines[method]['macro_f1']),'baseline_accuracy':float(baselines[method]['accuracy']),'baseline_selected_k':int(baselines[method]['k'])}
 out.mkdir(parents=True,exist_ok=True);result={'status':'exploratory_online_extractor_cost_components','dataset':ds,'protocol':'official1 test; common deterministic 50-row subset','rows':indices.tolist(),'source_sha256':source_hashes,'device':device,'warmup_images_per_descriptor':2,'load_model_and_svm_fit_excluded':True,'per_descriptor_latency_ms':{k:{'mean':float(np.mean(v)),'median':float(np.median(v)),'p95':float(np.percentile(v,95))} for k,v in timings.items()},'method_routes':method_results,'failed_descriptors':failed,'provenance':{'manifest_sha256':sh(manifest/'sample_manifests'/f'{ds}.csv'),'audit_sha256':sh(audit/'data_audit.csv'),'topk_csv_sha256':sh(topk_csv),'main_csv_sha256':sh(main_csv),'extractor_script_sha256':sh(REPO/'src'/'01_extract_features.py'),'rgb_ngram_count_metadata_sha256':sh(REPO/'results/extensions/outex13_official1360/rgb_ngram_count_cache/Outex13Official1360/rgb_ngram_impl1/metadata.json')},'limitations':['Serial per-descriptor image pipelines with model loading excluded; models are not resident simultaneously. Costs sum measured per-descriptor extraction for the same images plus measured SVM prediction.','Descriptor cosine checks disclose extractor implementation mismatch; route prediction agreement is required before timing is considered matched.']}
 (out/'Outex_official1_primary22_online_components.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
