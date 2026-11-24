"""village-yards-b v001 (work pack 2026-11-11 B-40h, batch A): WE01 village well and well pavilion (first, the batch sample);
CW01 courtyard wall set, CW02 courtyard gate, XB01 stone slab bridge and stepping stones follow after the sample is approved.

Built with the village-houses-b pipeline (art/source/village-houses-b/build_village_houses_b.py, imported, not copied: same join, UV atlas,
bake, LOD 50 / 15 %, FBX/GLB, ten views, model_info and validation), the VL material set and the VL roof tiles. vh_roof.py is copied
from the 11/09 roadside branch so this branch does not depend on it.

Run (from the repo root):
  blender --background --factory-startup --python art/source/village-yards-b/build_village_yards_b.py -- WE01_VillageWell [--force]
Writes art/exports/village-yards-b/<ID>/, art/previews/village-yards-b/<ID>/, art/source/village-yards-b/blend/<ID>_v001.blend
"""
import sys, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'village-houses-b'))
sys.path.insert(0, str(HERE))
import build_village_houses_b as B
import we_well, cw_wall, cw_gate, xb_bridge

KIT = 'village-yards-b'
ART = HERE.parents[1]
B.KIT = KIT
we_well.register(B.ASSETS)
B.well_checks = we_well.well_checks
cw_wall.register(B.ASSETS)
B.yardwall_checks = cw_wall.yardwall_checks
cw_gate.register(B.ASSETS)
B.gate_checks = cw_gate.gate_checks
xb_bridge.register(B.ASSETS)
B.slabbridge_checks = xb_bridge.slabbridge_checks
B.steppingstones_checks = xb_bridge.steppingstones_checks
OURS = ('WE01', 'CW01', 'CW02', 'XB01')


def wire(objs, path):
    """Wireframe over the baked colour at the hero angle, wires on their own orange material sized to the asset (as on the roadside branch)."""
    import bpy
    wm = bpy.data.materials.get('QA_Wire_Orange') or bpy.data.materials.new('QA_Wire_Orange')
    wm.use_nodes = True; bs = wm.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (.95, .45, .05, 1); bs.inputs['Roughness'].default_value = 1.
    bs.inputs['Emission Color'].default_value = (.95, .45, .05, 1); bs.inputs['Emission Strength'].default_value = .6
    lo, hi = B.pl.eval_bounds(objs); th = max(.008, max(hi - lo) / 600)
    for o in objs:
        o.data.materials.append(wm)
        m = o.modifiers.new('QA_Wire', 'WIREFRAME'); m.thickness = th; m.use_replace = False; m.material_offset = 999; m.use_even_offset = False
    B.pl.persp_shot(objs, path, samples=24)
    for o in objs:
        o.modifiers.remove(o.modifiers['QA_Wire']); o.data.materials.pop()


B.wire = wire

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ids = [a for a in argv if a in B.ASSETS and a.startswith(OURS)] or ['WE01_VillageWell']
    if '--preview' in argv:
        for aid in ids: B.preview(aid, Path(argv[argv.index('--preview') + 1]))
    else:
        # --info-only: rewrite the kit-specific model_info fields of already exported assets without rebuilding them
        info_only = '--info-only' in argv
        for aid in ids:
            if not info_only: B.run(aid, '--force' in argv)
            mi = ART / 'exports' / KIT / aid / 'model_info.json'
            if mi.exists():
                info = json.loads(mi.read_text(encoding='utf-8'))
                info['unity_import_verified'] = 'see artifacts/village-yards-unity/ (local Unity batch check VillageYardsModelCheck, not committed)'
                # the shared pipeline writes the village-houses wording (StarterHouse outline, VL shared tiles); use this kit's own
                if B.ASSETS[aid].get('method'): info['modeling_method'] = B.ASSETS[aid]['method']
                mi.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
                print('MODEL_INFO', aid, info['modeling_method'][:90])
