"""One-shot synthetic fidelity gate; no benchmark dataset reads or classifier fits."""
import argparse
import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
from enum import Enum

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def selected_scope(path,names,scope):
    tree=ast.parse(Path(path).read_text())
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    if {n.name for n in nodes}!=set(names): raise ValueError('reference source definitions missing')
    # Only previously reviewed tensor/feature definitions: no imports or module entrypoint.
    module=ast.Module(body=nodes,type_ignores=[])
    exec(compile(module,str(path),'exec'),scope)


def run(bundle,output):
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
    import numpy as np
    import cv2
    import torch
    import skimage.feature
    from cellnn_reference import load_network,preprocess_blue,extract_blue
    bundle,output=Path(bundle).resolve(),Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    receipt=json.loads((bundle/'receipt.json').read_text())
    for r in receipt['artifacts']:
        if hashlib.sha256(Path(r['local_path']).read_bytes()).hexdigest()!=r['sha256']:
            raise ValueError('author bundle drift')
    lock=(ROOT/'results/analysis/gpu.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    torch.set_num_threads(2);cv2.setNumThreads(2)
    torch.manual_seed(42);torch.use_deterministic_algorithms(True)
    output.mkdir(parents=True,exist_ok=False)
    report={'status':'running','gate':'synthetic author route vs local port',
        'author_commit':receipt['author_commit'],'tolerance':1e-4,
        'binary_and_histograms_exact_required':True,'dataset_images':0,'classifier_fits':0,'online_calls':0}
    status=output/'status.json'
    status.write_text(json.dumps(report,indent=2)+'\n')
    try:
        scope={'t':torch,'nn':torch.nn,'np':np,'cv2':cv2,'skimage':skimage,'Enum':Enum}
        selected_scope(bundle/'cellnn.py.source.txt',('mcellnn','activeFun'),scope)
        selected_scope(bundle/'tools.py.source.txt',('dataset_normalized','clahe_equalized','adjust_gamma'),scope)
        selected_scope(bundle/'main_otc12.py.source.txt',('Type','getHist'),scope)
        reference=scope['mcellnn']().cuda().eval()
        raw=torch.load(bundle/'cellnn_model.ph',map_location='cpu',weights_only=True)['net']
        reference.load_state_dict({k.removeprefix('module.'):v for k,v in raw.items()},strict=True)
        reference.requires_grad_(False)
        scope['mnet']=reference
        local=load_network(bundle/'cellnn_model.ph')
        rng=np.random.default_rng(42)
        inputs={'gradient':np.tile(np.arange(128,dtype=np.uint8)*2,(128,1)),
            'checkerboard':((np.indices((128,128)).sum(axis=0)%2)*255).astype(np.uint8),
            'random':rng.integers(0,256,size=(128,128),dtype=np.uint8)}
        results=[]
        for name,blue in inputs.items():
            image=np.dstack((blue,np.flipud(blue),np.fliplr(blue)))
            path=output/(name+'.png')
            if not cv2.imwrite(str(path),image): raise ValueError('synthetic image write failed')
            ref_pre=scope['adjust_gamma'](scope['clahe_equalized'](scope['dataset_normalized'](blue)),1.2)
            own_pre=preprocess_blue(blue)
            if not np.array_equal(ref_pre,own_pre): raise ValueError('preprocess parity failure')
            tensor=torch.from_numpy(ref_pre.reshape(1,1,128,128)).cuda().float()
            with torch.inference_mode():
                ref_outputs=reference(tensor)
                own_outputs=local(tensor)
            ref_values=[v.cpu().numpy() for v in ref_outputs]
            own_values=[v.cpu().numpy() for v in own_outputs]
            ref_hist=scope['getHist'](str(path),768,scope['Type'].LBP_6S_MCELLNN,0,0,128,128)
            own_hist=extract_blue(blue,local)
            np.savez_compressed(output/(name+'_vectors.npz'),reference_float=ref_values[0],local_float=own_values[0],
                reference_binary=np.concatenate(ref_values[1:],axis=1),local_binary=np.concatenate(own_values[1:],axis=1),
                reference_hist=ref_hist,local_hist=own_hist)
            error=float(np.max(np.abs(ref_values[0]-own_values[0])))
            binary=all(np.array_equal(a,b) for a,b in zip(ref_values[1:],own_values[1:]))
            hist=np.array_equal(ref_hist,own_hist)
            row={'input':name,'max_abs_float_error':error,'binary_exact':binary,'histogram_exact':hist,
                'histogram_shape':list(own_hist.shape),'histogram_sum':float(own_hist.sum())}
            results.append(row)
            report['cases']=results
            status.write_text(json.dumps(report,indent=2)+'\n')
            if not np.isfinite(error) or error>1e-4 or not binary or not hist:
                raise ValueError('scientific parity failure; requires_review; no retry')
        try:
            preprocess_blue(np.zeros((128,128),dtype=np.uint8))
        except ValueError:
            report['constant_input_negative_test']='rejected as specified'
        else: raise ValueError('constant rejection missing')
        report['status']='synthetic_parity_complete'
        report['output_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p!=status}
        status.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'status':report['status'],'cases':results,'status_sha256':hashlib.sha256(status.read_bytes()).hexdigest()}))
    except Exception as exc:
        report.update(status='requires_review',error=f'{type(exc).__name__}: {exc}')
        status.write_text(json.dumps(report,indent=2)+'\n')
        raise
    finally:
        fcntl.flock(lock,fcntl.LOCK_UN);lock.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    run(args.bundle,args.output)
