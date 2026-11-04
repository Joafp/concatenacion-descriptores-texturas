"""Retrieve only reviewed small immutable author artifacts; never execute them."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_cellnn_author_sources import fetch,OLD

ARTIFACTS=(('cellnn.py','fdfe763311df3a34d428ba0fb11073e3fc02793a',11157),
    ('main_otc12.py','6aabcf137bba914a5401666162f374bcf33009bf',13030),
    ('tools.py','31da78d97d395d3d19814e362fe16aec0fa6304b',8783),
    ('cellnn_model.ph','319d4deb633488c077f5193c99568e9c5ac7496c',10311))


def prepare(output):
    output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    retrieved=[]
    for name,blob,size in ARTIFACTS:
        data,receipt=fetch(OLD,name,blob,size)
        retrieved.append((name,data,receipt))
    output.mkdir(parents=True,exist_ok=False)
    receipts=[]
    for name,data,receipt in retrieved:
        local=output/(name+'.source.txt' if name.endswith('.py') else name)
        local.write_bytes(data)
        receipts.append({**receipt,'local_path':str(local)})
    report={'status':'REVIEWED_AUTHOR_BUNDLE_NOT_EXECUTED','author_commit':OLD,
        'total_bytes':sum(x[2]['bytes'] for x in retrieved),'artifacts':receipts,
        'source_executed':False,'models_fitted':0,'online_calls':0}
    target=output/'receipt.json';target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'total_bytes':report['total_bytes'],'receipt_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    prepare(parser.parse_args().output)
