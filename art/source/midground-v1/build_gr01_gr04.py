"""以 AI 生成的地表來源製作可平鋪的 URP 地形貼圖。"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT=Path(__file__).resolve().parents[2]
SIZE=2048
EDGE=160
SPECS={
    'GR01':{'name':'苔地','smooth':.13,'normal':3.0},
    'GR04':{'name':'濕泥地','smooth':.32,'normal':4.0},
}

def seamless(a):
    a=a.astype(np.float32)
    for axis in (1,0):
        n=a.shape[axis]
        for i in range(EDGE):
            left=np.take(a,i,axis=axis).copy()
            right=np.take(a,n-1-i,axis=axis).copy()
            t=.5*(1+np.cos(np.pi*i/EDGE))
            mean=(left+right)*.5
            sl=[slice(None)]*a.ndim
            sl[axis]=i
            a[tuple(sl)]=left*(1-t)+mean*t
            sl[axis]=n-1-i
            a[tuple(sl)]=right*(1-t)+mean*t
    return np.clip(a,0,255)

def exact_edges(a):
    edge=((a[:,0].astype(np.uint16)+a[:,-1].astype(np.uint16))//2).astype(np.uint8)
    a[:,0]=edge
    a[:,-1]=edge
    edge=((a[0].astype(np.uint16)+a[-1].astype(np.uint16))//2).astype(np.uint8)
    a[0]=edge
    a[-1]=edge
    return a

for asset,spec in SPECS.items():
    source=ROOT/'references/ground-textures-v1'/asset/'source.png'
    folder=ROOT/'exports/ground-textures-v1'/asset
    folder.mkdir(parents=True,exist_ok=True)
    rgb=np.array(Image.open(source).convert('RGB').resize((SIZE,SIZE),Image.Resampling.LANCZOS))
    rgb=seamless(rgb)
    if asset=='GR01':
        rgb=np.clip(rgb*np.array([1.05,1.10,.85]),0,255)
    else:
        rgb=np.clip(rgb*np.array([1.40,1.35,1.20])+np.array([4,4,2]),0,255)
    albedo=np.uint8(rgb)
    Image.fromarray(albedo,'RGB').save(folder/(asset+'_Albedo.png'))
    linear=rgb/255
    lum=linear[:,:,0]*.2126+linear[:,:,1]*.7152+linear[:,:,2]*.0722
    height=gaussian_filter(lum,1.1,mode='wrap')
    dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*spec['normal']
    dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*spec['normal']
    normal=np.stack((-dx,-dy,np.ones_like(dx)),axis=-1)
    normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    normal=exact_edges(np.uint8(np.clip((normal*.5+.5)*255,0,255)))
    Image.fromarray(normal,'RGB').save(folder/(asset+'_Normal.png'))
    broad=gaussian_filter(lum,5.0,mode='wrap')
    ao=np.clip(.88+(lum-broad)*1.1,.62,1)
    smooth=np.clip(spec['smooth']+(broad-lum)*.35,.05,.48)
    mask=np.empty((SIZE,SIZE,4),dtype=np.uint8)
    mask[:,:,0]=0                 # 無金屬
    mask[:,:,1]=np.uint8(ao*255)  # 遮蔽
    mask[:,:,2]=255               # 細節遮罩
    mask[:,:,3]=np.uint8(smooth*255)
    mask=exact_edges(mask)
    Image.fromarray(mask,'RGBA').save(folder/(asset+'_MaskURP.png'))
    tile=Image.fromarray(albedo,'RGB').resize((512,512),Image.Resampling.LANCZOS)
    preview=Image.new('RGB',(1024,1024))
    for y in (0,512):
        for x in (0,512):
            preview.paste(tile,(x,y))
    preview.save(folder/(asset+'_2x2-preview.png'))
    errs={}
    for suffix,img in [('Albedo',albedo),('Normal',normal),('MaskURP',mask)]:
        errs[suffix]=int(max(np.abs(img[:,0].astype(int)-img[:,-1].astype(int)).max(),
                             np.abs(img[0].astype(int)-img[-1].astype(int)).max()))
    info={'id':asset,'name_zh':spec['name'],'resolution':[SIZE,SIZE],
          'source':str(source.relative_to(ROOT)).replace('\\','/'),
          'outputs':['Albedo RGB','Normal RGB','MaskURP RGBA: R metallic=0, G AO, B detail=1, A smoothness'],
          'seam_max_channel_delta':errs,
          'unity_import':'未驗證；Albedo sRGB、Normal 為 Normal Map、MaskURP 線性'}
    (folder/'material_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print(asset,'seam',errs,'rgb_mean',np.round(rgb.mean(axis=(0,1)),1))
