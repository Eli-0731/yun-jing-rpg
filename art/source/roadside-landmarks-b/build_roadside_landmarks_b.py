"""roadside-landmarks-b v001 (work pack 2026-11-09 B-112h, batch B): PS01 old post station (first, the batch sample), BS01 boundary stone (bs_stele.py), FS01 field shrine (fs_shrine.py), RI04 scarecrows A / B (ri_scarecrow.py), FE04 net rack and mooring posts (fe_netrack.py), PS02 broken bridge (ps_bridge.py), BT01 beacon tower (bt_beacon.py).
ti_pipeline.py in village-houses-b is the batch A branch's (detach_zero for small zero-area UV islands, off unless an asset sets uv_detach_zero).

Built with the village-houses-b pipeline (art/source/village-houses-b/build_village_houses_b.py, imported, not copied: same join, UV atlas,
bake, LOD 50 / 15 %, FBX/GLB, ten views, model_info and validation), the VL material set and the VL roof tiles. vh_roof.py is copied from
the batch A branch (art/b-1109-vh-village-houses) so this branch does not depend on it.

Run (from the repo root):
  blender --background --factory-startup --python art/source/roadside-landmarks-b/build_roadside_landmarks_b.py -- PS01_OldPostStation [--force]
  ... -- PS01_OldPostStation --preview <dir>      procedural look only
Writes art/exports/roadside-landmarks-b/<ID>/, art/previews/roadside-landmarks-b/<ID>/, art/source/roadside-landmarks-b/blend/<ID>_v001.blend
  ... -- BS01_BoundaryStone [--force]
"""
import sys, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'village-houses-b'))
sys.path.insert(0, str(HERE))                    # vh_roof from here
import build_village_houses_b as B
import ps_station, bs_stele, fs_shrine, ri_scarecrow, fe_netrack, ps_bridge, bt_beacon

KIT = 'roadside-landmarks-b'
ART = HERE.parents[1]
B.KIT = KIT
ps_station.register(B.ASSETS)
B.station_checks = ps_station.station_checks
bs_stele.register(B.ASSETS)        # BS01
B.stele_checks = bs_stele.stele_checks
fs_shrine.register(B.ASSETS)       # FS01
B.shrine_checks = fs_shrine.shrine_checks
ri_scarecrow.register(B.ASSETS)     # RI04 A / B
B.scarecrow_checks = ri_scarecrow.scarecrow_checks
fe_netrack.register(B.ASSETS)       # FE04
B.netrack_checks = fe_netrack.netrack_checks
ps_bridge.register(B.ASSETS)        # PS02
B.bridge_checks = ps_bridge.bridge_checks
bt_beacon.register(B.ASSETS)        # BT01
B.beacon_checks = bt_beacon.beacon_checks
OURS = ('PS0', 'PS02', 'BT01', 'FS01', 'RI04', 'FE04', 'BS01')


def wire(objs, path):
    """Wireframe over the baked colour, same 3/4 angle as the hero. main's village-houses-b wire() puts 4 mm wires on the last material
    slot (the roof tile there) and at the hero distance they fall under a pixel; here, as on the VH branch, the wires get their own dark
    material appended as the last slot, sized to the asset (about 1.3 px at the hero framing)."""
    import bpy
    wm = bpy.data.materials.get('QA_Wire_Orange') or bpy.data.materials.new('QA_Wire_Orange')
    wm.use_nodes = True; bs = wm.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (.95, .45, .05, 1); bs.inputs['Roughness'].default_value = 1.     # orange: reads on dark tile and on lime plaster
    bs.inputs['Emission Color'].default_value = (.95, .45, .05, 1); bs.inputs['Emission Strength'].default_value = .6
    lo, hi = B.pl.eval_bounds(objs); th = max(.008, max(hi - lo) / 600)      # about 1.5 px at the hero framing, whatever the size
    for o in objs:
        o.data.materials.append(wm)
        m = o.modifiers.new('QA_Wire', 'WIREFRAME'); m.thickness = th; m.use_replace = False; m.material_offset = 999; m.use_even_offset = False   # even offset throws spikes off acute corners
    B.pl.persp_shot(objs, path, samples=24)
    for o in objs:
        o.modifiers.remove(o.modifiers['QA_Wire']); o.data.materials.pop()


B.wire = wire

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ids = [a for a in argv if a in B.ASSETS and a.startswith(OURS)] or ['PS01_OldPostStation']
    if '--preview' in argv:
        for aid in ids: B.preview(aid, Path(argv[argv.index('--preview') + 1]))
    else:
        for aid in ids:
            B.run(aid, '--force' in argv)
            mi = ART / 'exports' / KIT / aid / 'model_info.json'
            if mi.exists():
                info = json.loads(mi.read_text(encoding='utf-8'))
                info['unity_import_verified'] = 'see artifacts/village-houses-unity/ (local Unity batch check VillageHousesModelCheck, not committed)'
                mi.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
