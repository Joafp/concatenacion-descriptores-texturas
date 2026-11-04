"""Read bounded primary artifacts; static AST and safe CPU weight metadata only."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import urllib.request

REPO='https://raw.githubusercontent.com/UESTC-nnLab/LBP_Contour'
OLD='299502cbb2243ecb78018110236871f261aa92b2'
NEW='89fc3d6097ab13f800c8d2828f4d6ed2225f3eb1'


def fetch(commit,name,expected_blob,expected_size):
    url=f'{REPO}/{commit}/{name}'
    with urllib.request.urlopen(url,timeout=30) as response:
        data=response.read(expected_size+1)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if len(data)!=expected_size or blob!=expected_blob:
        raise ValueError('primary artifact size/blob mismatch: '+url)
    return data,{'url':url,'bytes':len(data),'git_blob_sha1':blob,'sha256':hashlib.sha256(data).hexdigest()}


def declared_parameters(source,class_name):
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name)
    names=[]
    for node in ast.walk(cls):
        if not isinstance(node,ast.Assign): continue
        if not isinstance(node.value,ast.Call): continue
        fun=node.value.func
        if not isinstance(fun,ast.Attribute) or fun.attr!='Parameter': continue
        for target in node.targets:
            if isinstance(target,ast.Attribute) and isinstance(target.value,ast.Name) and target.value.id=='self':
                names.append(target.attr)
    return sorted(names)


def audit(output):
    import torch
    output=Path(output)
    if output.exists(): raise FileExistsError(output)
    old,old_receipt=fetch(OLD,'cellnn.py','fdfe763311df3a34d428ba0fb11073e3fc02793a',11157)
    new,new_receipt=fetch(NEW,'cellnn.py','6b2d5c1c80fad326cb5fa03aa0a7f05a35860124',17494)
    weights,weight_receipt=fetch(OLD,'cellnn_model.ph','319d4deb633488c077f5193c99568e9c5ac7496c',10311)
    checkpoint=torch.load(io.BytesIO(weights),map_location='cpu',weights_only=True)
    state=checkpoint['net']
    if not all(isinstance(v,torch.Tensor) and torch.isfinite(v).all().item() for v in state.values()):
        raise ValueError('nonfinite/non-tensor checkpoint state')
    actual=sorted(k.removeprefix('module.') for k in state)
    expected=declared_parameters(old.decode(),'mcellnn')
    if actual!=expected: raise ValueError('author old-version checkpoint keys disagree')
    latest=declared_parameters(new.decode(),'cellula')
    report={'status':'AUTHOR_PRIOR_VERSION_STATIC_KEYS_MATCH_NOT_NUMERICAL_REPLAY',
        'candidate_commit':OLD,'latest_commit_reviewed':NEW,
        'artifacts':[old_receipt,new_receipt,weight_receipt],
        'downloaded_bytes_in_memory':sum(r['bytes'] for r in (old_receipt,new_receipt,weight_receipt)),
        'safe_load':{'weights_only':True,'map_location':'cpu','checkpoint_keys':list(checkpoint)},
        'candidate_parameter_names':expected,'state_parameter_count':len(state),
        'state_tensors':{k:{'shape':list(v.shape),'dtype':str(v.dtype),'finite':True} for k,v in state.items()},
        'latest_cellula_registered_parameter_names':latest,
        'latest_entry_point_compatible':actual==latest,
        'author_source_executed':False,'images_extracted':0,'models_fitted':0,'online_calls':0,
        'scope':'metadata/static compatibility only; source-paper numerical identity not verified'}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'state_parameters':len(state),
        'candidate_commit':OLD,'latest_compatible':report['latest_entry_point_compatible'],
        'receipt_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    audit(parser.parse_args().output)
