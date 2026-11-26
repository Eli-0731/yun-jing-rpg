"""TX02 AI 青銅來源整理為可環繞鐘身的材質。"""
from pathlib import Path
import numpy as np
from PIL import Image

folder=Path(__file__).resolve().parents[2]/'exports/mountain-city-v1/TX02'
a=np.array(Image.open(folder/'TX02_Bronze_source.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)
for i in range(128):
    left=a[:,i].copy()
    right=a[:,-1-i].copy()
    t=.5*(1+np.cos(np.pi*i/128))
    mid=(left+right)*.5
    a[:,i]=left*(1-t)+mid*t
    a[:,-1-i]=right*(1-t)+mid*t
a=np.uint8(np.clip(a,0,255))
Image.fromarray(a,'RGB').save(folder/'TX02_Bronze_Albedo.png')
print('TX02_BRONZE_SEAM',np.abs(a[:,0].astype(int)-a[:,-1].astype(int)).max())
