"""Record unfiltered Blender asset QA findings for the Qingxi v13 assets."""
import json
import sys
import re
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path.home()/'.codex/skills/blender-asset-qa/scripts'))
import qa_check

report={}
for slug,name in (
    ('novice-cultivator','ASSET_QX13_NoviceCultivator'),
    ('village-gate','ASSET_QX13_VillageGate'),
    ('herb-basket','ASSET_QX13_HerbBasket'),
    ('road-dressing','ASSET_QX13_RoadDressing'),
):
    names=[o.name for o in bpy.data.collections[name].objects if o.type=='MESH']
    if slug=='road-dressing':
        # This collection is a palette of separate placeable stones/plants.
        # Test each placement unit for detached parts, not the empty air between units.
        units={}
        for name in names:
            if '_Gravel_' in name:
                unit=name
            else:
                number=re.search(r'_(\d+)(?:_\d+)?$',name).group(1)
                unit='plant_'+str(int(number))
            units.setdefault(unit,[]).append(name)
        results=[qa_check.run(objects=unit,profile='game',max_tris=300000) for unit in units.values()]
        result={'pass':all(r['pass'] for r in results),'errors':sum((r['errors'] for r in results),[]),
                'warnings':sum((r['warnings'] for r in results),[]),'ground_z':None,
                'objects':{k:v for r in results for k,v in r['objects'].items()}}
    else:
        result=qa_check.run(objects=names,profile='game',max_tris=300000)
    report[slug]={
        'pass':result['pass'],
        'errors':result['errors'],
        'warnings':result['warnings'],
        'ground_z':result['ground_z'],
        'mesh_count':len(result['objects']),
        'triangles':sum(o['tris'] for o in result['objects'].values()),
        'scope':'independent scatter units; scene grounding requires visual review' if slug=='road-dressing' else 'whole asset including converted curves',
    }
out=ROOT/'art/exports/qingxi-entry-assets-v13/qa-report.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('@@QINGXI_ENTRY_QA@@'+json.dumps({k:{'pass':v['pass'],'errors':len(v['errors']),'warnings':len(v['warnings'])} for k,v in report.items()}))
if not all(v['pass'] for v in report.values()):
    raise RuntimeError('Asset QA failed; inspect qa-report.json')
