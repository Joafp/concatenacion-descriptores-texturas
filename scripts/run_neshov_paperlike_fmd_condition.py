"""Neshov FMD paper-like 10x10 approximation with explicit per-repeat seed."""
import argparse
from pathlib import Path
import run_neshov_external_condition as core
from run_neshov_batch1_condition import extract


def train_head(partition, rows, extract_dir, output):
    import numpy as np
    import torch
    from neshov_reference_training import fit_fixed_head
    core.verify_artifact(extract_dir,'extract_complete')
    data=np.load(extract_dir/'features.npz',allow_pickle=False)
    ids=partition['training_indices']
    if not np.array_equal(data['rows'],ids): raise ValueError('training order drift')
    labels=partition['labels'];mapping={label:i for i,label in enumerate(labels)}
    truth=[mapping[int(rows[i]['label'])] for i in ids]
    seed=partition['training_seed']
    head,history=fit_fixed_head(data['features'],truth,len(labels),epochs=100,batch_size=32,seed=seed)
    torch.save(head.state_dict(),output/'head.pt');core.write(output/'labels.json',labels)
    core.write(output/'training_history.json',history)
    with torch.inference_mode(): logits=head(torch.from_numpy(data['features'])).numpy()
    np.savez_compressed(output/'training_logits.npz',rows=data['rows'],logits=logits)
    return {'training_images':len(ids),'epochs':100,'training_seed':seed,
            'epoch_selection':'final; no early stopping',
            'extraction_status_sha256':core.digest(extract_dir/'status.json')}


def run(manifest,number,stage,job):
    core.extract=extract;core.train_head=train_head
    return core.run(manifest,number,stage,job)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--number',type=int,required=True)
    parser.add_argument('--stage',choices=['extract','train','online','audit'],required=True)
    parser.add_argument('--job',type=Path,required=True);a=parser.parse_args();run(a.manifest,a.number,a.stage,a.job)
