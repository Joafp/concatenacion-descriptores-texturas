from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_neshov_batch1_extension import neshov_partition


def test_preserves_indices_and_discards_foreign_head():
    original={'dataset':'x','training_indices':list(range(64)),'external_indices':[65],
              'excluded_training_indices':[64],'head_params':{'cellnn':True},'labels':[0,1]}
    new=neshov_partition(original)
    assert new['training_indices']==original['training_indices']
    assert new['external_indices']==[65] and new['excluded_training_indices']==[64]
    assert 'head_params' not in new and original['head_params']=={'cellnn':True}
    assert (new['training_seed'],new['epochs'],new['head_batch'])==(42,100,32)


def test_rejects_singleton_batch_without_skipping_row():
    with pytest.raises(ValueError):
        neshov_partition({'training_indices':list(range(65)),'external_indices':[66]})
