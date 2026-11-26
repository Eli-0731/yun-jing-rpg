"""在 Blender 中檢查 VP04 全部網格。"""
import bpy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.agents/skills/blender-asset-qa/scripts'))
import qa_check
names=[o.name for o in bpy.data.objects if o.type=='MESH']
r=qa_check.run(objects=names,profile='game')
print('VP04_QA',json.dumps({'pass':r['pass'],'objects':len(names),'errors':r['errors'][:30],
                            'error_count':len(r['errors']),'warning_count':len(r['warnings']),
                            'warning_sample':r['warnings'][:10],
                            'zfighting':r['zfighting'],'floating':r['floating']},
                           ensure_ascii=False))
