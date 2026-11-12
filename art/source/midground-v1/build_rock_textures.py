"""建立石峰的環向高度圖與灰藍層岩貼圖。"""
from pathlib import Path
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[2]
out=root/'exports/midground-v1';out.mkdir(parents=True,exist_ok=True)
for name,seed in [('MM01',401),('MM02',402)]:
    rng=np.random.default_rng(seed)
    h,w=256,256
    y,x=np.mgrid[:h,:w]
    p=2*np.pi*x/(w-1)
    q=y/(h-1)
    field=np.zeros((h,w),dtype=float)
    for k in (2,3,5,7,11,17):
        amp=.24/(k**.58)
        field+=amp*np.sin(k*p+rng.uniform(0,6.28)+q*rng.uniform(1,9))
    field+=.09*np.sin(2*np.pi*q*8+p*.8)+.035*np.sin(2*np.pi*q*29+3*p)
    field=(field-field.min())/(field.max()-field.min())
    arr=np.uint8(np.clip(field*255,0,255));arr[:,-1]=arr[:,0]
    Image.fromarray(arr,'L').save(out/f'{name}_height.png')
source=Image.open(root/'source/midground-v1/rock-source.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
a=np.array(source,dtype=np.float32)
# 四邊漸混到相同值，方便中景重複貼圖。
for axis in (0,1):
    edge=(np.take(a,0,axis=axis)+np.take(a,-1,axis=axis))/2
    for i in range(65):
        t=i/64;t=t*t*(3-2*t)
        sl=[slice(None)]*3;sl[axis]=i
        a[tuple(sl)]=a[tuple(sl)]*t+edge*(1-t)
        sl[axis]=-1-i
        a[tuple(sl)]=a[tuple(sl)]*t+edge*(1-t)
    sl=[slice(None)]*3;sl[axis]=0;a[tuple(sl)]=edge
    sl[axis]=-1;a[tuple(sl)]=edge
Image.fromarray(np.uint8(np.clip(a,0,255)),'RGB').save(out/'T_KarstRock.png')
print('heightmaps + texture',out)
