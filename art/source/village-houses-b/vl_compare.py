"""VL acceptance sheet: StarterHouse v004 (untouched original) and VL01-03 LOD0 side by side in one render, same light and camera.
Reads only; the source .blend files are linked, not changed.

blender --background --factory-startup --python vl_compare.py -- <repo root> <out.png>
"""
import sys, math
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

sys.path.insert(0, str(Path(__file__).parent))
import ti_pipeline as pl

args = sys.argv[sys.argv.index('--') + 1:]
ROOT, OUT = Path(args[0]), Path(args[1])
SRC = ROOT / 'art/source/village-houses-b/blend'
HOUSES = [('StarterHouse', ROOT / 'art/incoming/dondon/StarterHouse/v004/StarterHouse_v004.blend', None),
          ('VL01_LongEmptyHouse', SRC / 'VL01_LongEmptyHouse_v001.blend', 'LOD0'),
          ('VL02_MovedInHouse', SRC / 'VL02_MovedInHouse_v001.blend', 'LOD0'),
          ('VL03_HalfCollapsedHouse', SRC / 'VL03_HalfCollapsedHouse_v001.blend', 'LOD0')]
GAP = 12.6


def bring(path, lod):
    """lod None: StarterHouse, its model collections 01-07 linked whole (parents, hinges and all), studio collection left out.
    Otherwise the asset's exported LOD objects (hidden editable source parts left out)."""
    if lod is None:
        with bpy.data.libraries.load(str(path), link=False) as (src, dst):
            dst.collections = [c for c in src.collections if c[:2].isdigit() and not c.startswith('90_')]
        objs = set()
        for c in dst.collections:
            bpy.context.scene.collection.children.link(c); objs |= set(c.all_objects)
        bpy.context.view_layer.update()
        out = [o for o in objs if o.type == 'MESH' and not o.hide_render]
        roots = [o for o in objs if o.parent is None or o.parent not in objs]
        print('COMPARE_OBJECTS', path.stem, len(out), 'roots', len(roots), flush=True)
        return out, roots
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.endswith(lod) and 'Collision' not in n]
    out = []
    for o in dst.objects:
        if o is None or o.type != 'MESH' or o.hide_render: continue
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
        bpy.context.scene.collection.objects.link(o); out.append(o)
    print('COMPARE_OBJECTS', path.stem, sorted(o.name for o in out), flush=True)
    return out, out


bpy.ops.wm.read_factory_settings(use_empty=True)
groups = []
for i, (aid, path, lod) in enumerate(HOUSES):
    objs, roots = bring(path, lod)
    for o in roots: o.location.x += (i - 1.5) * GAP
    bpy.context.view_layer.update()
    groups.append((aid, objs))
    print('COMPARE_LOADED', aid, len(objs), flush=True)
bpy.context.view_layer.update()
allobjs = [o for _, g in groups for o in g]
for aid, g in groups:
    lo, hi = pl.eval_bounds(g); print('COMPARE_BOUNDS', aid, [round(v, 3) for v in lo], [round(v, 3) for v in hi], flush=True)
# one shot per house, identical camera relative to each house's origin (same angle, distance and lens, so the same scale) and the
# studio lights placed for each; the panels are joined side by side with labels by vl_compare_sheet.py
D = Vector((1, -1.3, .55)).normalized(); DIST = 19.5
sc = bpy.context.scene
for i, (aid, g) in enumerate(groups):
    pl.show_only(g); cam, _, _ = pl.studio(g, 64)
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1000
    target = Vector(((i - 1.5) * GAP, -.6, 2.3))
    cam.data.type = 'PERSP'; cam.data.lens = 50; cam.data.sensor_fit = 'AUTO'
    cam.location = target + D * DIST; cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    path = OUT.with_name(f'{OUT.stem}_{i}_{aid}.png'); sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    print('COMPARE_PANEL', aid, path.name, flush=True)
