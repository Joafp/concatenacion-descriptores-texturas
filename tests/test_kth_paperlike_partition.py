from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_kth_paperlike_queue import partition
from consolidate_kth_paperlike import validate_partition


def fixture():
    rows=[]
    for label in range(11):
        for sample in 'abcd':
            for scale in range(2,11):
                for image in range(1,13):
                    i=len(rows);rows.append({'row_id':str(i),'label':str(label),'sample':sample,
                        'path':f'/class{label}/sample_{sample}/x-scale_{scale}_im_{image}_col.png'})
    return rows


def test_paperlike_counts_and_physical_overlap_declared():
    p=partition(fixture(),'/manifest.csv')
    assert len(p['training_indices'])==1584 and len(p['external_indices'])==3168
    assert p['shared_physical_samples_train_test']==44
    assert not (set(p['training_indices']) & set(p['external_indices']))


def test_unknown_image_names_rejected():
    rows=fixture();rows[10]['path']='/bad.png'
    with pytest.raises(ValueError): partition(rows,'/manifest.csv')


def test_audit_rejects_missing_disclosure_and_changed_test_indices():
    rows=fixture();p=partition(rows,'/manifest.csv');validate_partition(p,rows)
    p['shared_physical_samples_train_test']=0
    with pytest.raises(ValueError): validate_partition(p,rows)
    p=partition(rows,'/manifest.csv');p['external_indices'].reverse()
    with pytest.raises(ValueError): validate_partition(p,rows)
