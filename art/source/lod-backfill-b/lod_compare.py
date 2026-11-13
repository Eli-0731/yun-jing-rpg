"""Before/after sheet for one LOD backfill asset: the same three-quarter camera on LOD0, LOD1, LOD2 and LOD0/LOD1 without Detail_*.
usage: blender --background <out>/<ID>/<ID>_LOD_v001.blend --python lod_compare.py -- <ID> <png_dir> [material|grey]
Renders with EEVEE; one PNG per panel plus a joined sheet (joined by lod_compare_sheet.py)."""
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
AID, OUT = a[0], a[1]; mode = a[2] if len(a) > 2 else 'material'
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
objs = {o.name: o for o in sc.objects if o.type == 'MESH'}
def lod(level, detail=True):
    return [o for n, o in objs.items() if n.endswith('_' + level) and (detail or 'Detail' not in n)]
xs = [o.matrix_world @ Vector(c) for o in lod('LOD0') for c in o.bound_box]
lo = Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs))); hi = Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
c = (lo + hi) / 2; r = (hi - lo).length / 2
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 900, 760
sc.render.film_transparent = False
w = bpy.data.worlds.new('W'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.62, .6, .57, 1); w.node_tree.nodes['Background'].inputs[1].default_value = .9
sc.world = w
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(52), 0, math.radians(-38))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
d = Vector((1, -1.25, .62)).normalized(); cam.location = c + d * (r * 3.1)
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
if mode == 'grey':
    g = bpy.data.materials.new('Grey'); g.use_nodes = True; g.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (.6, .6, .6, 1)
    for o in objs.values():
        o.data.materials.clear(); o.data.materials.append(g)
panels = [('LOD0', True), ('LOD1', True), ('LOD2', True), ('LOD0', False), ('LOD1', False)]
for i, (lv, det) in enumerate(panels):
    show = set(lod(lv, det))
    for o in objs.values(): o.hide_render = o not in show
    sc.render.filepath = os.path.join(OUT, f'{AID}_{i + 1}_{lv}{"" if det else "_no_detail"}_{mode}.png')
    bpy.ops.render.render(write_still=True)
    tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in show)
    print('PANEL', AID, lv, det, tri, flush=True)
