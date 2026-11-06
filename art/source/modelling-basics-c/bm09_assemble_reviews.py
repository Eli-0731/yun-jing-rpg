"""Compose the two unchanged-renderer LOD captures, left LOD0 / right LOD1."""
import sys
sys.dont_write_bytecode=True
import bpy
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(HERE))
from bm10_textures import png
PRE=ROOT/'art/previews/modelling-basics-c/BM09'
for pid in ['BM09_01','BM09_02']:
    arrays=[]
    for lod in [0,1]:
        im=bpy.data.images.load(str(PRE/(pid+f'-lod{lod}-nodetail-threequarter.png')));im.colorspace_settings.name='Non-Color'
        w,h=im.size;a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a);arrays.append(a.reshape(h,w,4))
    png(PRE/(pid+'-lod0-vs-lod1-nodetail.png'),np.concatenate(arrays,axis=1))
print('COMPOSITES_DONE')
