"""Read-only numeric edge inspection of AI candidates; run with Blender 4.5.3."""
import bpy, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
out=ROOT/'art/previews/modelling-basics-c/BM10'
out.mkdir(parents=True,exist_ok=True)
results={}
for p in sorted((ROOT/'art/references/BM10').glob('*-cand-*.png')):
    im=bpy.data.images.load(str(p));im.colorspace_settings.name='Non-Color'
    w,h=im.size
    a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a)
    a=np.rint(a.reshape(h,w,4)*255).astype(np.int16)
    dx=np.abs(a[:,0]-a[:,-1]);dy=np.abs(a[0]-a[-1])
    results[p.name]={'size':[w,h],'left_right_max':int(dx.max()),'top_bottom_max':int(dy.max()),'left_right_mean_rgb':round(float(dx[:,:3].mean()),3),'top_bottom_mean_rgb':round(float(dy[:,:3].mean()),3)}
    bpy.data.images.remove(im)
(out/'reference_edges.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
