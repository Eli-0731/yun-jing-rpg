"""F01 for the creek test scene: no bed markers, soft grass. Each field is fed by its own inlet, so no bank is cut; the cutter stays for a variant that needs a slot.

blender --background --factory-startup --python art/source/creek-repair-b/cut_field_gap.py

Slot: round bottom hugging the bamboo (centre z 0.27, radius 0.125) at y = 2 (mid field), opening out above it like a notch dug by hand.
The bamboo fills the hole in the bank's inner face, so the field water does not run out around it.
"""
import json, math, random
from pathlib import Path
import bmesh, bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'art' / 'exports' / 'qingxi-waterworks-b' / 'F01' / 'F01.fbx'
OUT = ROOT / 'art' / 'exports' / 'creek-repair-b'
Y, CENTRE, R, TOP = 2., .27, .125, 1.
BODIES = ('F01', 'F01_LOD1', 'F01_LOD2')
FLARE, FLARE_H = .19, .15
VARIANTS = {'F01_Field': ()}


def half_width(z, flare=FLARE):
    """Half the notch's width at height z, above the round bottom."""
    return R + flare * (min(max(z - CENTRE, 0.), FLARE_H) / FLARE_H) ** 1.5


def cutter(side):
    """The notch as a closed loft across the bank, from inside the field to past its outer edge; its sides wander a little, as a spade leaves them."""
    bottom = [(R * math.cos(math.pi * (1 + k / 16)), CENTRE + R * math.sin(math.pi * (1 + k / 16))) for k in range(17)]
    heights = [CENTRE + FLARE_H * k / 6 for k in range(1, 7)]
    bm = bmesh.new(); xs = [2.2 + .1 * k for k in range(10)]; n = 17 + 2 * len(heights) + 2; rings = []
    for x in xs:
        wander, flare = .012 * math.sin(x * 5 + side), FLARE + .025 * math.sin(x * 7 + side * 2)
        section = list(bottom) + [(half_width(z, flare) + wander * (z - CENTRE) / FLARE_H, z) for z in heights] + [(half_width(TOP, flare) + wander, TOP), (-half_width(TOP, flare) + wander, TOP)]
        section += [(-half_width(z, flare) + wander * (z - CENTRE) / FLARE_H, z) for z in reversed(heights)]
        rings.append([bm.verts.new((side * x, Y + y, z)) for y, z in section])
    bm.faces.new(rings[0]); bm.faces.new(rings[-1])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([r0[i], r0[j], r1[j], r1[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('cut'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('cut', me); bpy.context.scene.collection.objects.link(o)
    return o


def ground_at(o, x, y):
    """Highest surface of the mesh under (x, y), in model space."""
    hit, at, _, _ = o.ray_cast(o.matrix_world.inverted() @ Vector((x, y, 2)), o.matrix_world.inverted().to_3x3() @ Vector((0, 0, -1)))
    return round((o.matrix_world @ at).z, 3) if hit else None


def dress_cut_faces(o):
    """The faces the cutter made carry no colour or UV: give them the bank's own soil, and bring back the hard edges the boolean smoothed over."""
    me = o.data; col = me.color_attributes.active_color; uv = me.uv_layers.active
    assert col is not None and col.domain == 'CORNER' and uv is not None, (o.name, col and col.domain)
    def on_slot(q): return abs(q.y - Y) <= half_width(q.z, FLARE + .025) + .016 and q.z >= CENTRE - R - .002 and (q.z >= CENTRE or math.hypot(q.y - Y, q.z - CENTRE) >= R - .002) and abs(q.x) >= 2.19
    soil_slot = next(i for i, m in enumerate(me.materials) if m.name.startswith('ww_field_soil'))
    cut, soil, scale = [], [], []
    for poly in me.polygons:
        ps = [me.vertices[i].co for i in poly.vertices]
        n = poly.normal
        if all(on_slot(q) for q in ps) and abs(n.x) < .6 or sum(col.data[l].color[0] + col.data[l].color[1] + col.data[l].color[2] for l in poly.loop_indices) < .001:
            cut.append(poly); continue
        if poly.material_index == soil_slot and abs(ps[0].y - Y) < 1.2 and abs(ps[0].x) > 2.4 and n.z > .5:
            soil.append(sum((Vector(col.data[l].color) for l in poly.loop_indices), Vector((0, 0, 0, 0))) / poly.loop_total)
            a, b = poly.loop_indices[0], poly.loop_indices[1]; length = (ps[1] - ps[0]).length
            if length > .01: scale.append((uv.data[a].uv - uv.data[b].uv).length / length)
    soil.sort(key=lambda c: c.length); tint = soil[len(soil) // 2]; scale.sort(); k = scale[len(scale) // 2]
    for poly in cut:
        poly.material_index = soil_slot
        for l in poly.loop_indices:
            q = me.vertices[me.loops[l].vertex_index].co
            col.data[l].color = tint; uv.data[l].uv = (q.x * k, (q.y + q.z) * k)
    if me.has_custom_normals:
        bpy.context.view_layer.objects.active = o; bpy.ops.mesh.customdata_custom_splitnormals_clear()
    me.set_sharp_from_angle(angle=math.radians(35))
    me.update()
    return len(cut)


def drop_bed_markers(o):
    """F01's little stones round the planting beds read as crystals, in the water and out of it. The stone inlet and outlet lie outside this box and stay."""
    stone = {i for i, m in enumerate(o.data.materials) if m and m.name.startswith('ww_stone')}; world = o.matrix_world
    bm = bmesh.new(); bm.from_mesh(o.data)
    def marker(f):
        c = world @ f.calc_center_median()
        return f.material_index in stone and abs(c.x) < 2.6 and .3 < c.y < 3.45 and not (abs(c.x) < .8 and (c.y < .85 or c.y > 3.0))
    drop = [f for f in bm.faces if marker(f)]
    bmesh.ops.delete(bm, geom=drop, context='FACES_ONLY')
    bm.to_mesh(o.data); o.data.update(); bm.free()
    return len(drop)


def bank_spots():
    """Where grass takes: patches along the banks, thicker near the corners; a seed per patch keeps it the same on every LOD."""
    R = random.Random(1501); spots = []
    for _ in range(26):
        side = R.randrange(4)
        cx, cy = {0: (R.uniform(-2.95, -2.5), R.uniform(0, 4)), 1: (R.uniform(2.5, 2.95), R.uniform(0, 4)), 2: (R.uniform(-3, 3), R.uniform(.02, .3)), 3: (R.uniform(-3, 3), R.uniform(3.7, 3.98))}[side]
        for _ in range(R.randint(1, 4)):
            spots.append((cx + R.gauss(0, .1), cy + R.gauss(0, .1), R.uniform(.6, 1.15), R.randrange(1 << 30)))
    return spots


def regrow(o, keep, blades, joints):
    """Swap the model's stiff single spikes for soft tufts: thin blades that arch over and droop, straw-green at the tips."""
    me = o.data; slot = next(i for i, m in enumerate(me.materials) if m.name.startswith('ww_grass'))
    bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active
    old = [f for f in bm.faces if f.material_index == slot]
    uv = sum((l[uvl].uv for f in old for l in f.loops), old[0].loops[0][uvl].uv * 0) / sum(len(f.loops) for f in old)
    verts = {v for f in old for v in f.verts}; bmesh.ops.delete(bm, geom=old, context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[v for v in verts if not v.link_faces], context='VERTS')
    bm.to_mesh(me); me.update(); bm.free(); bpy.context.view_layer.update()
    inv = o.matrix_world.inverted(); down = inv.to_3x3() @ Vector((0, 0, -1)); soil = next(i for i, m in enumerate(me.materials) if m.name.startswith('ww_field_soil'))
    bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active; name = me.color_attributes.active_color.name
    col = bm.loops.layers.float_color.get(name) or bm.loops.layers.color.get(name); grown = 0
    for n, (x, y, size, seed) in enumerate(bank_spots()):
        if n % keep or (y < .9 and abs(x) < .9) or (y > 3.3 and abs(x) < .9): continue
        hit, at, normal, index = o.ray_cast(inv @ Vector((x, y, 2)), down)
        if not hit or me.polygons[index].material_index != soil: continue
        foot = o.matrix_world @ at
        if foot.z < .3 or (o.matrix_world.to_3x3() @ normal).normalized().z < .6: continue
        R = random.Random(seed); grown += 1
        for _ in range(blades):
            a = R.uniform(0, math.tau); r = R.uniform(0, .028 * size); L = R.uniform(.1, .2) * size; w = R.uniform(.008, .014) * (.7 + size * .4)
            lean = Vector((math.cos(a), math.sin(a), 0)); across = Vector((-lean.y, lean.x, 0)); base = foot + lean * r - Vector((0, 0, .008)); over = R.uniform(.2, .62)
            shade = R.uniform(.82, 1.12); yellow = R.uniform(0, .22)
            def tone(k): return ((.2 + k * (.34 + yellow * .7)) * shade, (.36 + k * .3) * shade, (.09 + k * .1) * shade, 1)
            line = [(base + lean * L * over * (j / joints) ** 2 + Vector((0, 0, L * math.sin(min(j / joints * 1.5, 1) * math.pi / 2) * (1 - .3 * over * (j / joints) ** 2))), j / joints) for j in range(joints + 1)]
            for facing in (1, -1):
                row = []
                for p, k in line:
                    half = w / 2 * (1 - k ** 2.4)
                    row.append((bm.verts.new(inv @ (p - across * half)), bm.verts.new(inv @ (p + across * half)), k))
                for (a0, a1, k0), (b0, b1, k1) in zip(row, row[1:]):
                    quad = [a0, a1, b1] if k1 == 1 else [a0, a1, b1, b0]
                    if facing < 0: quad.reverse()
                    f = bm.faces.new(quad); f.material_index = slot; f.smooth = False
                    for l in f.loops:
                        l[uvl].uv = uv; l[col] = tone(k0 if l.vert in (a0, a1) else k1)
    bm.to_mesh(me); me.update(); bm.free()
    return grown


def keep_faces(o, wanted):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not wanted(f)], context='FACES')
    bm.to_mesh(me); me.update(); bm.free()


def lighten(o, target):
    """The boolean splits far more of the soil than it cuts: bring only the soil back to its budget, so stone and timber keep their edges."""
    soil = next(i for i, m in enumerate(o.data.materials) if m.name.startswith('ww_field_soil'))
    part = o.copy(); part.data = o.data.copy(); part.name = o.name + '_soil'; bpy.context.scene.collection.objects.link(part)
    keep_faces(part, lambda f: f.material_index == soil); keep_faces(o, lambda f: f.material_index != soil)
    bpy.ops.object.select_all(action='DESELECT'); part.select_set(True); bpy.context.view_layer.objects.active = part
    t = part.modifiers.new('tri', 'TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=t.name)
    before = len(part.data.polygons)
    m = part.modifiers.new('budget', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = min(1., target / before)
    bpy.ops.object.modifier_apply(modifier=m.name)
    after = len(part.data.polygons)
    o.select_set(True); bpy.context.view_layer.objects.active = o; bpy.ops.object.join()
    return {'soil_before': before, 'soil_after': after}


def make(name, sides):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SRC))
    report = {}
    for side in sides:
        c = cutter(side)
        for body in BODIES:
            o = bpy.data.objects[body]
            bpy.context.view_layer.objects.active = o
            m = o.modifiers.new('slot', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.use_self = True; m.use_hole_tolerant = True; m.object = c
            before = len(o.data.polygons)
            bpy.ops.object.modifier_apply(modifier=m.name)
            report.setdefault(body, []).append({'side': side, 'faces_before': before, 'faces_after': len(o.data.polygons)})
        bpy.data.objects.remove(c)
    bpy.context.view_layer.update()
    if sides: report['dressed_faces'] = {b: dress_cut_faces(bpy.data.objects[b]) for b in BODIES}
    if sides: assert all(max((bpy.data.objects[b].matrix_world @ v.co).z for v in bpy.data.objects[b].data.vertices) < .56 for b in BODIES), 'part of the cutter stayed in the mesh'
    checks = {b: {f'slot_floor_{s}': ground_at(bpy.data.objects[b], s * 2.7, Y) for s in (-1, 1)} | {f'bank_beside_{s}': ground_at(bpy.data.objects[b], s * 2.7, Y + .6) for s in (-1, 1)} for b in BODIES}
    report['bed_marker_faces_removed'] = {b: drop_bed_markers(bpy.data.objects[b]) for b in BODIES}
    report['tris_before_grass'] = {b: lighten(bpy.data.objects[b], n) for b, n in (('F01', 6400), ('F01_LOD1', 3300), ('F01_LOD2', 700))}
    report['grass_tufts'] = {b: regrow(bpy.data.objects[b], keep, blades, joints) for b, keep, blades, joints in (('F01', 1, 14, 3), ('F01_LOD1', 1, 13, 2), ('F01_LOD2', 1, 6, 2))}
    report['tris'] = {b: sum(len(p.vertices) - 2 for p in bpy.data.objects[b].data.polygons) for b in BODIES}
    print('GRASS', name, report['bed_marker_faces_removed'], report['tris_before_grass'], report['grass_tufts'], report['tris'], flush=True)
    objs = [o for o in bpy.data.objects if o.type in {'MESH', 'EMPTY'}]
    mods = []
    for o in objs:
        if o.type == 'MESH':
            t = o.modifiers.new('fbx_tri', 'TRIANGULATE'); t.quad_method, t.ngon_method = 'BEAUTY', 'BEAUTY'; mods.append(t)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    (OUT / name).mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(OUT / name / f'{name}.fbx'), use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                             axis_forward='-Z', axis_up='Y', object_types={'MESH', 'EMPTY'}, mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             path_mode='COPY', embed_textures=False, bake_anim=False)
    (OUT / name / 'cut_report.json').write_text(json.dumps({'source': 'art/exports/qingxi-waterworks-b/F01/F01.fbx', 'sides': sides, 'booleans': report, 'heights_m': checks}, indent=1), encoding='utf8')
    print('GAP_DONE', name, json.dumps(checks), flush=True)
    # for art/source/creek-repair-b/ruler_views.py: it wants <ID>/<ID>_LOD0 in a .blend and a model_info.json
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    body = bpy.data.objects['F01']; world = body.matrix_world.copy(); dims = list(body.dimensions); body.name = name + '_LOD0'; body.parent = root; body.matrix_world = world
    (OUT / name / 'model_info.json').write_text(json.dumps({'asset': name, 'name_zh': '田（配水版）', 'minTier': 'standard', 'source': 'F01', 'lod_tris': report['tris'], 'note': '工作單外加：F01 拿掉苗床邊小石頭、換細葉草叢；每塊田由自己的進水口進水'}, ensure_ascii=False, indent=1), encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'art' / 'source' / 'creek-repair-b' / 'blend' / f'{name}_v001.blend'))


for name, sides in VARIANTS.items(): make(name, sides)
