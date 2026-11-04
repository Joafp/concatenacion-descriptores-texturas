"""Infrastructure-only JSON scalar bridge for NEVER-STARTED conditions.

Core method, fit, timer and auditing remain the sealed v1 runner. No retry logic.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import run_cellnn_external_condition as core


def json_scalars(value):
    if isinstance(value,np.generic): return value.item()
    if isinstance(value,dict): return {k:json_scalars(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [json_scalars(v) for v in value]
    return value


def write(path,data):
    # Convert numpy scalars losslessly to Python scalars; do not alter arrays,
    # model state, tolerances, prediction values, features or stopping decisions.
    converted=json_scalars(data)
    if Path(path).name=='status.json':
        converted={**converted,'serialization_bridge_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    Path(path).write_text(json.dumps(converted,indent=2,allow_nan=False)+'\n')


def run(manifest,number,stage,job):
    core.write=write
    return core.run(manifest,number,stage,job)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--number',type=int,required=True);parser.add_argument('--stage',choices=['extract','train','online','audit'],required=True)
    parser.add_argument('--job',type=Path,required=True);a=parser.parse_args();run(a.manifest,a.number,a.stage,a.job)
