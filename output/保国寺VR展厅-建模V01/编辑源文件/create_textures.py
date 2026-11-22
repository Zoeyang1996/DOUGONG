from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ROOT=Path(__file__).resolve().parents[1]/'贴图'
ROOT.mkdir(exist_ok=True)
rng=np.random.default_rng(1122);N=1024
y,x=np.mgrid[0:N,0:N]/N
def noise(grid,blur=0):
 a=rng.random((grid,grid))*255
 im=Image.fromarray(a.astype('uint8')).resize((N,N),Image.Resampling.BICUBIC)
 if blur:im=im.filter(ImageFilter.GaussianBlur(blur))
 return np.asarray(im,dtype=float)/255-.5
def save(name,base,height,rough=.6,amp=18,normal_strength=4):
 h=(height-height.min())/max(np.ptp(height),1e-6)
 rgb=np.clip(np.array(base)[None,None,:]+(h[:,:,None]-.5)*amp,0,255).astype('uint8')
 Image.fromarray(rgb).save(ROOT/(name+'_BaseColor.png'))
 r=np.clip(rough+(h-.5)*.12,0,1)
 Image.fromarray(np.uint8(r*255)).save(ROOT/(name+'_Roughness.png'))
 dy,dx=np.gradient(h); v=np.stack((-dx*normal_strength,-dy*normal_strength,np.ones_like(h)),axis=-1)
 v/=np.linalg.norm(v,axis=-1,keepdims=True)
 Image.fromarray(np.uint8(np.clip(v*.5+.5,0,1)*255)).save(ROOT/(name+'_NormalGL.png'))
grain=(np.sin((y*84+1.6*np.sin(x*5)+noise(8)*.5)*np.pi)*.3+
       np.sin((y*231+3*np.sin(x*4))*np.pi)*.16+noise(32)*.23+noise(180)*.12)
save('SmokedOak',(73,53,38),grain,.52,30,2)
save('WarmPlaster',(181,170,151),noise(10)*.55+noise(130)*.2+noise(430)*.12,.88,15,3)
save('GreyStone',(125,128,122),noise(7)*.32+noise(45)*.18+noise(250)*.12,.7,22,2)
print('PBR maps',len(list(ROOT.glob('*.png'))))
