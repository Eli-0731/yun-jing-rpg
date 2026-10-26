"""Generate material separation and wireframe evidence for all v13 assets."""
from pathlib import Path
import sys
import bpy

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path.home()/'.codex/skills/blender-asset-qa/scripts'))
import review_shots

out=ROOT/'output/entry-v13-review'
out.mkdir(parents=True,exist_ok=True)
for name in ('NoviceCultivator','VillageGate','HerbBasket','RoadDressing'):
    objects=[o.name for o in bpy.data.collections['ASSET_QX13_'+name].objects if o.type=='MESH']
    for mode in ('random','wire'):
        review_shots.run(objects=objects,out=str(out/(name+'-'+mode+'.png')),
                         views=['front','right','back','top'],mode=mode,res=256)
