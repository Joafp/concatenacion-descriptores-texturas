import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_cellnn_dataset_queue import validate


def fixture():
    rows=[{'row_id':str(i),'label':str(i%61),'group':str(i)} for i in range(5612)]
    p=[{'dataset':'CUReT','seed':42,'outer_fold':f,'labels':list(range(61)),
        'training_indices':list(range(f,5612,2)),'external_indices':list(range(1-f,5612,2))} for f in range(2)]
    return p,rows


def test_curet_complementary(): validate('CUReT',*fixture())


@pytest.mark.parametrize('kind',['count','identity','classes','group','rows','overlap'])
def test_reject_corruption(kind):
    p,r=fixture()
    if kind=='count': p.pop()
    elif kind=='identity': p[0]['seed']=123
    elif kind=='classes': p[0]['labels'].pop()
    elif kind=='group': r[0]['group']=r[1]['group']
    elif kind=='rows': r.pop()
    else: p[0]['external_indices'][0]=p[0]['training_indices'][0]
    with pytest.raises(ValueError): validate('CUReT',p,r)


def dtd_fixture():
    rows=[{'row_id':str(i),'label':str(i%47),'group':str(i),
        **{f'split_{f+1}':'test' if i//1880==f%3 else 'train' for f in range(10)}} for i in range(5640)]
    rows[1880]['group']=rows[0]['group']
    parts=[]
    for f in range(10):
        test=[i for i,r in enumerate(rows) if r[f'split_{f+1}']=='test']
        groups={rows[i]['group'] for i in test}
        train=[i for i,r in enumerate(rows) if r[f'split_{f+1}']=='train' and r['group'] not in groups]
        parts.append({'dataset':'DTD','seed':42,'outer_fold':f,'labels':list(range(47)),
            'training_indices':train,'external_indices':test,
            'excluded_training_indices':sorted(set(range(5640))-set(train)-set(test))})
    return parts,rows


def test_dtd_keeps_all_tests_and_exact_group_exclusions():
    p,r=dtd_fixture();validate('DTD',p,r)
    assert p[0]['excluded_training_indices']==[1880]


@pytest.mark.parametrize('kind',['reinstate','omit','exclusion','test','duplicate'])
def test_dtd_rejects_partition_changes(kind):
    p,r=dtd_fixture()
    if kind=='reinstate': p[0]['training_indices'].append(1880)
    elif kind=='omit': p[0]['training_indices'].pop()
    elif kind=='exclusion': p[0]['excluded_training_indices']=[]
    elif kind=='test': p[0]['external_indices'].pop()
    else: p[0]['external_indices'][1]=p[0]['external_indices'][0]
    with pytest.raises(ValueError): validate('DTD',p,r)


def outex_fixture():
    rows=[{'row_id':str(i),'label':str(i//20),'group':str(i),
        'official_split':'train' if i%2==0 else 'test'} for i in range(1360)]
    p=[{'dataset':'Outex13Official1360','seed':42,'outer_fold':0,'labels':list(range(68)),
        'training_indices':list(range(0,1360,2)),'external_indices':list(range(1,1360,2))}]
    return p,rows


def test_outex_exact_official(): validate('Outex13Official1360',*outex_fixture())


@pytest.mark.parametrize('kind',['inversion','order','group','class','test','official'])
def test_outex_rejects_changes(kind):
    p,r=outex_fixture()
    if kind=='inversion': p[0]['training_indices'],p[0]['external_indices']=p[0]['external_indices'],p[0]['training_indices']
    elif kind=='order': p[0]['external_indices'].reverse()
    elif kind=='group': r[0]['group']=r[1]['group']
    elif kind=='class': p[0]['labels'].pop()
    elif kind=='test': p[0]['external_indices'].pop()
    else: r[0]['official_split']='test'
    with pytest.raises(ValueError): validate('Outex13Official1360',p,r)


def soil_fixture():
    rows=[{'row_id':str(i),'label':str(i%7),'group':str(i)} for i in range(1140)]
    parts=[]
    for seed in (42,123,2026):
        offset=0
        for f,size in enumerate([228,229,228,227,228] if seed==123 else [228]*5):
            test=list(range(offset,offset+size));offset+=size
            parts.append({'dataset':'SoilOriginal','seed':seed,'outer_fold':f,'labels':list(range(7)),
                'external_indices':test,'training_indices':sorted(set(range(1140))-set(test))})
    return parts,rows


def test_soil_unequal_folds_retained():
    p,r=soil_fixture();validate('SoilOriginal',p,r)
    assert [len(x['external_indices']) for x in p[5:10]]==[228,229,228,227,228]


@pytest.mark.parametrize('kind',['identity','group','class','test','universe'])
def test_soil_rejects_changes(kind):
    p,r=soil_fixture()
    if kind=='identity': p[0]['seed']=0
    elif kind=='group': r[0]['group']=r[300]['group']
    elif kind=='class': p[0]['labels'].pop()
    elif kind=='test': p[0]['external_indices'].pop()
    else: p[1]=dict(p[0],outer_fold=1)
    with pytest.raises(ValueError): validate('SoilOriginal',p,r)


def kth_fixture():
    rows=[{'row_id':str(i),'label':str(i%11),'group':str(i),'sample':'abcd'[i%4]} for i in range(4752)]
    p=[{'dataset':'KTHTIPS2b','seed':42,'outer_fold':f,'labels':list(range(11)),
        'training_indices':[i for i in range(4752) if i%4!=f],
        'external_indices':[i for i in range(4752) if i%4==f]} for f in range(4)]
    return p,rows


def test_kth_three_train_one_physical_test(): validate('KTHTIPS2b',*kth_fixture())


@pytest.mark.parametrize('kind',['inversion','sample','group','identity','class','test'])
def test_kth_rejects_changes(kind):
    p,r=kth_fixture()
    if kind=='inversion': p[0]['training_indices'],p[0]['external_indices']=p[0]['external_indices'],p[0]['training_indices']
    elif kind=='sample': r[1]['sample']='a'
    elif kind=='group': r[0]['group']=r[1]['group']
    elif kind=='identity': p[0]['seed']=0
    elif kind=='class': p[0]['labels'].pop()
    else: p[0]['external_indices'].pop()
    with pytest.raises(ValueError): validate('KTHTIPS2b',p,r)
