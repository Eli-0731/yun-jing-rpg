"""從選定三視圖頂列擷取 MM06 遠山脊的透明遠景貼圖。"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
root=Path(__file__).resolve().parents[2]
src=Image.open(root/'references/midground-v1/MM06/three-view.png').convert('RGB')
image=np.asarray(src.crop((10,65,1764,305)),dtype=np.float32)
h,w=image.shape[:2]
y,x=np.mgrid[:h,:w]
d=image[:,:,2]-image[:,:,0]
a=np.clip((d-6)/11,0,1)
a=a*a*(3-2*a)
a*=np.clip(np.minimum(x,w-1-x)/100,0,1)
a*=1-np.clip((y-190)/50,0,1)
matte=Image.fromarray(np.uint8(a*200),'L').filter(ImageFilter.MedianFilter(7)).filter(ImageFilter.GaussianBlur(1.2))
rgba=np.dstack((image,np.asarray(matte))).astype(np.uint8)
patch=Image.fromarray(rgba,'RGBA').resize((2048,400),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(2048,1024),(169,184,196,0))
out.alpha_composite(patch,(0,520))
out.save(root/'exports/midground-v1/MM06/MM06_Albedo.png',optimize=True)
print('MM06 ridge alpha range',out.getchannel('A').getextrema())
