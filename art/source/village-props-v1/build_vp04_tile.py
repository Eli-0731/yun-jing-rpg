"""VP04 專用瓦圖；不使用 RK03 的貼圖或 UV。"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT=Path(__file__).resolve().parents[2]
folder=ROOT/'exports/village-props-v1/VP04'
image=np.array(Image.open(folder/'VP04_Tile_source.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)
for axis in (0,1):
    for i in range(96):
        n=image.shape[axis]
        a=np.take(image,i,axis=axis).copy()
        b=np.take(image,n-1-i,axis=axis).copy()
        t=.5*(1+np.cos(np.pi*i/96))
        mid=(a+b)/2
        s=[slice(None)]*3;s[axis]=i;image[tuple(s)]=a*(1-t)+mid*t
        s[axis]=n-1-i;image[tuple(s)]=b*(1-t)+mid*t
image=np.uint8(np.clip(image,0,255))
Image.fromarray(image,'RGB').save(folder/'VP04_Tile_Albedo.png')
lum=(image[:,:,0]*.21+image[:,:,1]*.72+image[:,:,2]*.07)/255
h=gaussian_filter(lum,1,mode='wrap')
dx=(np.roll(h,-1,1)-np.roll(h,1,1))*4
dy=(np.roll(h,-1,0)-np.roll(h,1,0))*4
n=np.stack((-dx,-dy,np.ones_like(dx)),axis=-1)
n/=np.linalg.norm(n,axis=-1,keepdims=True)
n=np.uint8(np.clip((n*.5+.5)*255,0,255))
n[:,0]=n[:,-1]=((n[:,0].astype(int)+n[:,-1].astype(int))//2).astype('uint8')
n[0]=n[-1]=((n[0].astype(int)+n[-1].astype(int))//2).astype('uint8')
Image.fromarray(n,'RGB').save(folder/'VP04_Tile_Normal.png')
wood=np.array(Image.open(folder/'VP04_Wood_source.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)
for axis in (0,1):
    for i in range(96):
        size=wood.shape[axis]
        a=np.take(wood,i,axis=axis).copy()
        b=np.take(wood,size-1-i,axis=axis).copy()
        t=.5*(1+np.cos(np.pi*i/96))
        middle=(a+b)*.5
        sl=[slice(None)]*3;sl[axis]=i;wood[tuple(sl)]=a*(1-t)+middle*t
        sl[axis]=size-1-i;wood[tuple(sl)]=b*(1-t)+middle*t
Image.fromarray(np.uint8(np.clip(wood*.83,0,255)),'RGB').save(folder/'VP04_Wood_Albedo.png')
Image.fromarray(np.uint8(np.clip(wood*1.13,0,255)),'RGB').save(folder/'VP04_WoodLight_Albedo.png')
print('VP04_TILE',image.shape)
