"""在 Blender 載入 MM01/02，驗證中景重建後的網格預算與資產檢查。"""
from pathlib import Path
import bpy, json, sys
sys.path.insert(0,str(Path.home()/'.agents/skills/blender-asset-qa/scripts'))
import qa_check

root=Path.cwd()/'art/exports/midground-v1'
for code in ('MM01','MM02'):
    bpy.ops.wm.open_mainfile(filepath=str(root/code/f'{code}.blend'))
    names=[o.name for o in bpy.data.objects if o.type=='MESH']
    qa=qa_check.run(objects=names,profile='game')
    tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH')
    assert qa['pass'] and tris<=15000,(code,qa['errors'],tris)
    print(code,json.dumps({'triangles':tris,'errors':qa['errors'],'warnings':qa['warnings'][:5]},ensure_ascii=False))
