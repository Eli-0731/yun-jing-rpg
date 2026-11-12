"""將同批實際 SK 背景、MM 石峰渲染與樹丘貼片放在一張驗收畫面。"""
from pathlib import Path
from PIL import Image, ImageEnhance
import json

ROOT=Path(__file__).resolve().parents[2]/'exports'
dest=ROOT/'midground-v1/C-pack-review'
bg=Image.open(ROOT/'sky-and-distance-v1/SK/SK03_sky-preview.png').convert('RGB').resize((2048,1024),Image.Resampling.LANCZOS).convert('RGBA')

def place(path,x,bottom,width,opacity=1):
    im=Image.open(path).convert('RGBA')
    bounds=im.getchannel('A').getbbox()
    assert bounds,path
    im=im.crop(bounds)
    height=round(im.height*width/im.width)
    im=im.resize((width,height),Image.Resampling.LANCZOS)
    if opacity<1:
        im.putalpha(im.getchannel('A').point(lambda v:round(v*opacity)))
    bg.alpha_composite(im,(x,bottom-height))
    return {'file':str(path.relative_to(ROOT)).replace('\\','/'),'x':x,'bottom':bottom,'width':width,'height':height}

items=[]
items.append(place(dest/'MM01_transparent.png',45,900,420,.90))
items.append(place(dest/'MM02_transparent.png',425,910,415,.86))
items.append(place(ROOT/'midground-v1/MM03/MM03_Albedo.png',825,895,1120,.90))
bg.convert('RGB').save(dest/'C-midground-with-SK03.png',quality=95)
info={'background':'sky-and-distance-v1/SK/SK03_sky-preview.png','foreground':items,
      'purpose':'中景石峰、樹丘與 SK 遠山同畫面尺度與色彩檢查；非遊戲鏡頭或 Unity 實機',
      'finding':'石峰與遠景色階可分辨；MM01/02 岩面仍偏單調，需在實際地形與植被中再審。'}
(dest/'review.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPOSED',dest/'C-midground-with-SK03.png')
