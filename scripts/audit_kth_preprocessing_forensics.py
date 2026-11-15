#!/usr/bin/env python3
"""Read-only fidelity review: source/config hashes and CPU pixel transforms.

No neural model is constructed, no embeddings or predictions are produced,
and no timing benchmark or scientific retry is executed. Existing failure
statuses are hashed before and after and never rewritten.
"""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import torch
from PIL import Image
import timm
from torchvision import transforms
from transformers import AutoImageProcessor
from reference_preprocessing import eva02_reference_transform,siglip_reference_transform


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for part in iter(lambda:handle.read(1024*1024),b''):
            h.update(part)
    return h.hexdigest()


def write_json(path,data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def function_ast(source,name):
    node=next((n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name),None)
    return None if node is None else ast.dump(node,include_attributes=False)


def build(output):
    if output.exists():
        raise FileExistsError('Use a new forensic output folder')
    torch.set_num_threads(2)
    gpu_before=torch.cuda.is_initialized()
    protected=[ROOT/'results/analysis/kth_top4_component_profile_20261115_v2/status.json',
               ROOT/'results/analysis/kth_top4_remaining_components_20261115_v1/status.json',
               ROOT/'results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1/status.json']
    protected_before={p.relative_to(ROOT).as_posix():sha(p) for p in protected}
    sources={}

    def source(path):
        path=Path(path)
        if not path.is_absolute():
            path=ROOT/path
        sources[path.relative_to(ROOT).as_posix()]=sha(path)
        return path

    for path in protected+[Path(__file__),ROOT/'src/reference_preprocessing.py',
                           ROOT/'tests/test_reference_preprocessing.py',ROOT/'src/extract_sota_2024.py',
                           ROOT/'src/fsc_tex/executor.py',ROOT/'src/reextract_confirmatory_embeddings.py']:
        source(path)
    parent=ROOT/'results/analysis/kth_top4_component_profile_20261115_v2'
    frozen=json.loads(source(parent/'protocol_frozen.json').read_text())
    parent_tail=ROOT/'results/analysis/kth_top4_remaining_components_20261115_v1'
    source(parent_tail/'protocol_frozen.json')
    weights={}
    for block in ['eva02_base','siglip_base']:
        record=frozen['weights'][block]
        checks={p:{'expected_sha256':expected,'actual_sha256':sha(p)} for p,expected in record['files'].items()}
        if any(c['expected_sha256']!=c['actual_sha256'] for c in checks.values()):
            raise ValueError(f'frozen cached weight/config changed: {block}')
        weights[block]={'repository':record['repository'],'revision':record['revision'],'checks':checks}
    siglip_snapshot=Path(next(iter(frozen['weights']['siglip_base']['files']))).parent
    processor_config=json.loads((siglip_snapshot/'preprocessor_config.json').read_text())
    processor=AutoImageProcessor.from_pretrained(siglip_snapshot,local_files_only=True)
    eva_cfg=timm.data.resolve_model_data_config(None,pretrained_cfg=timm.get_pretrained_cfg('eva02_base_patch14_224').to_dict())
    reference_eva=eva02_reference_transform(eva_cfg)
    reference_siglip=siglip_reference_transform(processor_config)
    online_eva=transforms.Compose([
        transforms.Resize(eva_cfg['input_size'][1:]),transforms.CenterCrop(eva_cfg['input_size'][1:]),
        transforms.ToTensor(),transforms.Normalize(mean=eva_cfg['mean'],std=eva_cfg['std'])])
    expected=json.loads(source('results/analysis/top4_fixed_preparation_20261114_v1/conditions.json').read_text())
    condition=next(c for c in expected if c['dataset']=='KTHTIPS2b' and c['outer_fold']==0)
    manifest=source(condition['manifest_source'])
    with manifest.open(newline='') as handle:
        rows=list(csv.DictReader(handle))
    selected=frozen['indices']
    if len(selected)!=33 or not set(selected).issubset(condition['train_indices']):
        raise ValueError('forensics must preserve the 33 frozen training images')
    cache=ROOT/'embeddings_extensions/KTH-TIPS2-b'
    label_checks={}
    manifest_labels=[r['label'] for r in rows]
    for block in ['eva02_base','siglip_base']:
        path=source(cache/f'{block}.npy')
        relative=path.relative_to(ROOT).as_posix()
        if sources[relative]!=frozen['sources'][relative]:
            raise ValueError(f'reference embedding changed: {block}')
        labels=np.load(source(cache/f'{block}_labels.npy'),allow_pickle=False)
        classes=json.loads(source(cache/f'{block}_classes.json').read_text())
        names=[classes[int(v)] if np.issubdtype(labels.dtype,np.integer) else str(v) for v in labels]
        label_checks[block]={'rows':len(labels),'matches_manifest':names==manifest_labels,
                             'per_embedding_producer_metadata_exists':(cache/f'{block}_metadata.json').exists()}
        if names!=manifest_labels:
            raise ValueError(f'label ordering differs: {block}')
    recovery=source('results/confirmatory/recovery/kth/KTH-TIPS2-b_manifest.csv')
    with recovery.open(newline='') as handle:
        recovered=list(csv.DictReader(handle))
    recovery_check={'rows':len(recovered),'same_order_and_file_sha256':len(rows)==len(recovered) and all(
        a['source_sha256']==b['source_sha256'] and Path(a['source_path']).parts[-3:]==Path(b['source_path']).parts[-3:]
        for a,b in zip(rows,recovered))}
    current_source=(ROOT/'src/extract_sota_2024.py').read_text()
    historical={}
    for commit in ['2443995db5f053f69be63076f6ff883967f7fec7','e10bf4044df5ed535cb3c8d0f242d4882aa6b534']:
        result=subprocess.run(['git','show',f'{commit}:src/extract_sota_2024.py'],cwd=ROOT,capture_output=True,text=True)
        historical[commit]={'available':result.returncode==0,'same_loader_function_ast':result.returncode==0 and
                            function_ast(current_source,'load_model_and_transform')==function_ast(result.stdout,'load_model_and_transform')}
    versions={p:importlib.metadata.version(p) for p in ['torch','torchvision','timm','transformers','Pillow','numpy']}
    tensor_rows=[]

    def compare(image,identifier,kind):
        for block,reference,online in [
            ('eva02_base',reference_eva,lambda x:online_eva(x)),
            ('siglip_base',reference_siglip,lambda x:processor(images=x,return_tensors='pt')['pixel_values'][0])]:
            a,b=reference(image),online(image)
            if a.device.type!='cpu' or b.device.type!='cpu' or a.shape!=b.shape or tuple(a.shape)!=(3,224,224):
                raise ValueError('unexpected pixel tensor device or shape')
            a,b=a.numpy(),b.numpy()
            delta=np.abs(a.astype(np.float64)-b.astype(np.float64))
            tensor_rows.append(dict(block=block,identifier=identifier,kind=kind,width=image.width,height=image.height,
                pixel_tensor_equal=bool(np.array_equal(a,b)),mean_abs_pixel_tensor_difference=float(delta.mean()),
                max_abs_pixel_tensor_difference=float(delta.max()),fraction_elements_different_gt_1e_minus6=float((delta>1e-6).mean()),
                reference_pixel_sha256=hashlib.sha256(a.tobytes()).hexdigest(),online_pixel_sha256=hashlib.sha256(b.tobytes()).hexdigest()))
    for index in selected:
        path=source(rows[index]['source_path'])
        if sources[path.relative_to(ROOT).as_posix()]!=rows[index]['source_sha256']:
            raise ValueError('frozen training image bytes changed')
        with Image.open(path) as handle:
            compare(handle.convert('RGB'),str(index),'frozen_training_image')
    yy,xx=np.indices((137,319))
    pixels=np.stack([(xx%13)*20,(yy%11)*24,((xx+yy)%17)*15],axis=2).astype(np.uint8)
    compare(Image.fromarray(pixels),'synthetic_texture','synthetic')
    compare(Image.new('RGB',(224,224),(255,255,255)),'synthetic_constant','synthetic')
    all_inputs={block:[r for r in tensor_rows if r['block']==block and r['kind']=='frozen_training_image'] for block in ['eva02_base','siglip_base']}
    differences={block:{'images':len(items),'different_pixel_tensors':sum(not r['pixel_tensor_equal'] for r in items),
                        'mean_abs_pixel_tensor_difference':float(np.mean([r['mean_abs_pixel_tensor_difference'] for r in items])),
                        'largest_abs_pixel_tensor_difference':max(r['max_abs_pixel_tensor_difference'] for r in items)} for block,items in all_inputs.items()}
    unchanged={key:sha(ROOT/key)==value for key,value in protected_before.items()}
    if not all(unchanged.values()):
        raise ValueError('an existing experimental status changed during review')
    summary={'status':'input_pipeline_incompatibility_demonstrated_feature_fidelity_still_requires_review',
             'scope':'CPU pixel preprocessing and source/config audit only',
             'neural_models_constructed':0,'new_embedding_extractions':0,'new_predictions':0,'new_latency_benchmarks':0,
             'cuda_initialized_before':gpu_before,'cuda_initialized_after':torch.cuda.is_initialized(),
             'versions_observed_now':versions,'pixel_input_differences':differences,'label_checks':label_checks,
             'recovery_manifest_check':recovery_check,'historical_recipe_code':historical,
             'existing_statuses_unchanged':unchanged,'threshold_unchanged':.999,'failures_retried':False,
             'limits':['Different network inputs do not quantify their contribution to the failed embedding cosine.',
                       'The per-embedding original producer command, weights digest and full library versions were not recovered.',
                       'Candidate input adapters are not a validated replacement for the failed scientific pipeline.']}
    output.mkdir(parents=True,exist_ok=False)
    with (output/'pixel_preprocessing_pairs.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(tensor_rows[0]));writer.writeheader();writer.writerows(tensor_rows)
    write_json(output/'summary.json',summary)
    write_json(output/'pipeline_configuration.json',{'eva_resolved_config_now':eva_cfg,
        'eva_reference_transform':str(reference_eva),'eva_failed_online_transform':str(online_eva),
        'siglip_reference_transform':str(reference_siglip),'siglip_processor_config':processor_config,
        'siglip_current_processor_class':type(processor).__name__,'siglip_current_processor_backend':getattr(processor,'backend',None),
        'cached_weight_and_config_checks':weights})
    import transformers.models.siglip.modeling_siglip as siglip_module
    library_sources=[Path(inspect.getfile(transforms.Resize)),Path(inspect.getfile(timm.data.create_transform)),
                     Path(inspect.getfile(type(processor))),Path(inspect.getfile(siglip_module))]
    provenance={'source_sha256':sources,'environment_source_sha256':{str(p):sha(p) for p in library_sources},
                'protected_status_sha256':protected_before,'outputs_sha256':{p.name:sha(p) for p in output.iterdir() if p.is_file()}}
    write_json(output/'provenance.json',provenance)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    build(args.output.resolve())
