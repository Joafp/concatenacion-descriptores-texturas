import sys
from pathlib import Path
import numpy as np
import pytest
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from cellnn_reference import ContourNetwork,preprocess_blue,fused_histograms,SCALES


def test_parameter_registration_matches_published_checkpoint_layout():
    model=ContourNetwork()
    assert len(model.state_dict())==20
    assert model.state_dict()['convAx'].shape==(1,1,3,3)
    assert model.state_dict()['conv1x1_u_15'].shape==(1,3,1,1)


def test_fusion_counts_and_dimension():
    blue=np.arange(256,dtype=np.uint8).reshape(16,16)
    zero=np.zeros_like(blue)
    f=fused_histograms(blue,(zero,zero,zero))
    assert f.shape==(1,768) and f.sum()==blue.size*6
    assert tuple(p for p,_ in SCALES)==(8,16,24,8,12,16)


def test_highest_contour_codes_stay_in_declared_bins():
    blue=np.arange(256,dtype=np.uint8).reshape(16,16)
    one=np.ones_like(blue)
    f=fused_histograms(blue,(one,one,one))
    assert f.sum()==1536
    assert f[0,:70].sum()==0


@pytest.mark.parametrize('bad',[np.zeros((16,16),dtype=np.uint8),np.full((16,16),np.nan),np.zeros((16,16,3),dtype=np.uint8)])
def test_preprocessing_rejects_invalid_without_fallback(bad):
    with pytest.raises(ValueError): preprocess_blue(bad)


def test_fusion_rejects_nonbinary_contour():
    blue=np.arange(256,dtype=np.uint8).reshape(16,16)
    with pytest.raises(ValueError): fused_histograms(blue,(blue,blue,blue))


def test_network_rejects_constant_input():
    with pytest.raises(ValueError): ContourNetwork()(torch.zeros(1,1,16,16))
