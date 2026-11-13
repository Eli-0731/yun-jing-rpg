"""產出溪畔夜間螢火粒子貼圖；鳥與蝶的新版預覽另由 make_lf_game_previews.py 製作。"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]/'exports/life-v1'
folder=ROOT/'LF03'; folder.mkdir(parents=True,exist_ok=True)
n=256
yy,xx=np.mgrid[0:n,0:n]
r=np.sqrt(((xx+0.5-n/2)/(n/2))**2+((yy+0.5-n/2)/(n/2))**2)
halo=np.exp(-r*r*10)*.35
core=np.exp(-r*r*155)*.70
alpha=np.uint8(np.clip(halo+core,0,1)*255)
rgba=np.zeros((n,n,4),dtype=np.uint8)
rgba[:,:,:3]=np.array([242,216,139],dtype=np.uint8)
rgba[:,:,3]=alpha
Image.fromarray(rgba,'RGBA').save(folder/'LF03_Glow.png')
preview=Image.new('RGB',(1024,512),(15,31,38))
for x,y,s in ((100,260,54),(268,124,32),(370,337,68),(580,196,48),(702,286,24),(860,116,62)):
    dot=Image.fromarray(rgba,'RGBA').resize((s,s),Image.Resampling.LANCZOS)
    preview.paste(dot,(x,y),dot)
preview.save(folder/'LF03_night-preview.png')
params={
    'id':'LF03','name_zh':'溪畔螢火','minTier':'high',
    'texture':'LF03_Glow.png','texture_resolution':[256,256],
    'unity_particle_recommendation':{
        'simulationSpace':'World','maxParticles':60,'emissionRatePerSecond':[3,8],
        'lifetimeSeconds':[2.5,5.0],'startSizeMetres':[.045,.11],
        'startSpeedMetresPerSecond':[.02,.10],
        'renderer':'Billboard, additive 或 premultiplied alpha，關閉陰影與光照',
        'motion':'低速上浮、平緩水平雜訊；高度約水面上 0.2–1.8 m',
        'colorOverLifetime':'暖黃淡入、峰值約 0.45 秒、末段淡出',
        'useCondition':'夜晚溪邊與 D5 蕈谷；白天停用',
        'performance':'需於 Unity 實測後調整數量與 overdraw'},
    'unity_import':'未驗證'}
(folder/'particle_params.json').write_text(json.dumps(params,ensure_ascii=False,indent=2),encoding='utf-8')
print('LF previews and glow done; alpha range',int(alpha.min()),int(alpha.max()))
