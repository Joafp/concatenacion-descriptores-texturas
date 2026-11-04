"""Local inference port of author mcellnn; complete-system adaptation components.

Author reference: UESTC-nnLab/LBP_Contour commit299502c. Not a paper-score replica.
No import-time CUDA/network/model/file operations. No missing-weight fallback.
"""
import hashlib
from pathlib import Path
import cv2
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from skimage.feature import local_binary_pattern

CHECKPOINT_SHA='af56a7e939c93e4ec7b0e2c8af348bff756ac25267af4ca45b52005552fba65f'
SCALES=((8,1),(16,2),(24,3),(8,3),(12,5),(16,7))


class ContourNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        for channel in ('x','u','d'):
            for kernel in ('A','B'):
                self.register_parameter(f'conv{kernel}{channel}',nn.Parameter(torch.zeros(1,1,3,3)))
            self.register_parameter(f'bias{channel}',nn.Parameter(torch.zeros(1)))
        for channel in ('x','u','d'):
            for step in (5,10,15):
                self.register_parameter(f'conv1x1_{channel}_{step}',nn.Parameter(torch.zeros(1,3,1,1)))
        self.conv1x1=nn.Parameter(torch.zeros(1,3,1,1))
        self.outBias=nn.Parameter(torch.zeros(1))

    def forward(self,image):
        if image.ndim!=4 or image.shape[:2]!=(1,1) or min(image.shape[2:])<4 or any(n%2 for n in image.shape[2:]):
            raise ValueError('single even-sized one-channel image required')
        if not torch.isfinite(image).all() or image.max()==image.min():
            raise ValueError('constant/nonfinite contour input requires review')
        h,w=image.shape[2:]
        image=torch.mul(torch.sub(image,torch.min(image)),2/(torch.max(image)-torch.min(image)))
        image=torch.sub(image,1)
        down=F.avg_pool2d(image,2)
        up=F.interpolate(image,size=[2*h,2*w],mode='nearest')
        bu=F.conv2d(image,self.convBx,padding=1)
        bd=F.conv2d(down,self.convBd,padding=1)
        bw=F.conv2d(up,self.convBu,padding=1)
        x=torch.zeros((1,1,h,w),device=image.device,dtype=image.dtype)
        down=torch.zeros((1,1,h//2,w//2),device=image.device,dtype=image.dtype)
        up=torch.zeros((1,1,2*h,2*w),device=image.device,dtype=image.dtype)
        for step in range(20):
            if step in (5,10,15):
                nx=torch.cat((F.avg_pool2d(up,2),x,F.interpolate(down,[h,w],mode='nearest')),dim=1)
                nu=torch.cat((up,F.interpolate(x,[2*h,2*w],mode='nearest'),F.interpolate(down,[2*h,2*w],mode='nearest')),dim=1)
                nd=torch.cat((F.avg_pool2d(up,4),F.avg_pool2d(x,2),down),dim=1)
                x=F.conv2d(nx,getattr(self,f'conv1x1_x_{step}'))
                down=F.conv2d(nd,getattr(self,f'conv1x1_d_{step}'))
                up=F.conv2d(nu,getattr(self,f'conv1x1_u_{step}'))
            x=torch.clamp(torch.add(F.conv2d(x,self.convAx,bias=self.biasx,padding=1),bu),-1,1)
            down=torch.clamp(torch.add(F.conv2d(down,self.convAd,bias=self.biasd,padding=1),bd),-1,1)
            up=torch.clamp(torch.add(F.conv2d(up,self.convAu,bias=self.biasu,padding=1),bw),-1,1)
        down=F.interpolate(down,[h,w],mode='nearest')
        up=F.avg_pool2d(up,2)
        output=F.conv2d(torch.cat((up,x,down),dim=1),self.conv1x1,bias=self.outBias)
        output=torch.clamp(output,-1,1)
        return output,(up>torch.mean(up)).int(),(x>torch.mean(x)).int(),(down>torch.mean(down)).int()


def load_network(path,device='cuda'):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=CHECKPOINT_SHA:
        raise ValueError('checkpoint drift')
    checkpoint=torch.load(path,map_location='cpu',weights_only=True)
    state=checkpoint['net']
    if any(not key.startswith('module.') for key in state): raise ValueError('unexpected weight prefix')
    clean={key[len('module.'):]:value for key,value in state.items()}
    if any(not isinstance(v,torch.Tensor) or v.dtype!=torch.float32 or not torch.isfinite(v).all() for v in clean.values()):
        raise ValueError('nonfinite or non-FP32 weights')
    model=ContourNetwork()
    model.load_state_dict(clean,strict=True)
    model.requires_grad_(False)
    return model.to(device).eval()


def preprocess_blue(blue):
    if blue.ndim!=2 or blue.dtype!=np.uint8 or not np.isfinite(blue).all() or np.std(blue)==0:
        raise ValueError('constant/nonfinite/invalid blue channel requires review')
    normalized=(blue-np.mean(blue))/np.std(blue)
    normalized=((normalized-np.min(normalized))/(np.max(normalized)-np.min(normalized)))*255
    normalized=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)).apply(np.array(normalized,dtype=np.uint8))
    table=np.array([((i/255.0)**(1.0/1.2))*255 for i in np.arange(0,256)]).astype('uint8')
    return cv2.LUT(normalized,table)


def fused_histograms(blue,contours):
    if blue.dtype!=np.uint8 or blue.ndim!=2 or len(contours)!=3:
        raise ValueError('invalid fusion inputs')
    a,b,c=[np.asarray(x).reshape(blue.shape) for x in contours]
    if any(not np.isin(x,(0,1)).all() for x in (a,b,c)):
        raise ValueError('binary contour maps required')
    features=[]
    for points,radius in SCALES:
        lbp=local_binary_pattern(blue,points,radius,method='uniform').astype(np.uint8)
        base=points+2
        fused=lbp+4*base*a+2*base*b+base*c
        hist=cv2.calcHist([fused.astype(np.uint8)],[0],None,[8*base],[0,8*base])
        features.append(hist.reshape(1,8*base))
    result=np.concatenate(features,axis=1)
    if result.shape!=(1,768) or not np.isfinite(result).all():
        raise ValueError('invalid 768D features')
    return result


def decode_blue(path):
    image=cv2.imread(str(path),cv2.IMREAD_COLOR)
    if image is None: raise ValueError('image decode failed')
    return cv2.resize(image,(128,128),interpolation=cv2.INTER_LINEAR)[:,:,0]


def extract_blue(blue,network,device='cuda'):
    preprocessed=preprocess_blue(blue)
    image=torch.from_numpy(preprocessed.reshape(1,1,*blue.shape)).to(device).float()
    with torch.inference_mode():
        outputs=network(image)
    contours=[v.cpu().numpy() for v in outputs[1:]]
    return fused_histograms(blue,contours)
