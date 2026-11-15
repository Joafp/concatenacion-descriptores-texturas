"""Geometry and normalization contracts; no model forward or feature extraction."""
import numpy as np
from PIL import Image
import pytest
from torchvision import transforms
from src.reference_preprocessing import eva02_reference_transform, siglip_reference_transform

SIGLIP = dict(image_mean=[.5]*3, image_std=[.5]*3, resample=3)
EVA = dict(input_size=(3,224,224), interpolation='bicubic', mean=(0.,0.,0.),
           std=(1.,1.,1.), crop_pct=.9, crop_mode='center')


def test_eva_preserves_reference_crop_geometry_instead_of_squashing():
    pixels=np.zeros((200,600,3),dtype=np.uint8)
    pixels[:,:,0]=255
    pixels[:,100:500,0]=0
    pixels[:,100:500,1]=255
    image=Image.fromarray(pixels)
    reference=eva02_reference_transform(EVA)(image)
    manual=transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor()])(image)
    assert reference.shape == manual.shape == (3,224,224)
    assert reference.device.type=='cpu'
    assert reference[0].mean().item() < .001
    assert manual[0].mean().item() > .25


@pytest.mark.parametrize('pixel,expected',[(0,-1.),(255,1.)])
def test_siglip_rgb_range_and_channel_normalization(pixel,expected):
    tensor=siglip_reference_transform(SIGLIP)(Image.new('RGB',(137,281),(pixel,)*3))
    assert tensor.shape==(3,224,224) and tensor.device.type=='cpu'
    np.testing.assert_allclose(tensor.numpy(),expected,atol=1e-6)


def test_siglip_uses_recorded_manual_resize_not_processor_bicubic():
    from torchvision.transforms import InterpolationMode
    transform=siglip_reference_transform(SIGLIP)
    assert transform.transforms[0].interpolation == InterpolationMode.BILINEAR


def test_eva_candidate_does_not_construct_a_model(monkeypatch):
    import timm
    def forbidden(*args,**kwargs):
        raise AssertionError('model construction forbidden in input adapter')
    monkeypatch.setattr(timm,'create_model',forbidden)
    transform=eva02_reference_transform()
    assert transform(Image.new('RGB',(200,200))).shape==(3,224,224)


@pytest.mark.parametrize('config',[
    dict(image_mean=[.5],image_std=[.5]),
    dict(image_mean=[.5]*3,image_std=[0.]*3),
    dict(image_mean=[float('nan')]*3,image_std=[.5]*3),
])
def test_invalid_normalization_is_rejected(config):
    with pytest.raises(ValueError):
        siglip_reference_transform(config)
