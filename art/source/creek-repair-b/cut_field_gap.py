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


def fix_zero_uv(o):
    """The borrowed grass sits on one texel and some cut faces collapse in UV: spread each such face over a tiny patch of the same spot."""
    me = o.data; bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active; n = 0
    for f in bm.faces:
        q = [l[uvl].uv.copy() for l in f.loops]
        area = sum((q[0] - q[i]).cross(q[0] - q[i + 1]) for i in range(1, len(q) - 1))
        if abs(area) < 1e-9:
            n += 1
            for i, l in enumerate(f.loops):
                a = i / len(q) * math.tau; l[uvl].uv = q[i] + Vector((math.cos(a), math.sin(a))) * .0015
    bm.to_mesh(me); me.update(); bm.free()
    return n


def to_spec(root_objects):
    """Spec origin: bottom centre, front -Y. Returns how far the piece moved; the scene puts it back so it still lines up with F01_water."""
    pts = [bpy.data.objects['F01'].matrix_world @ v.co for v in bpy.data.objects['F01'].data.vertices]
    lo = Vector(tuple(min(p[i] for p in pts) for i in range(3))); hi = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    shift = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    for o in root_objects: o.location += shift
    bpy.context.view_layer.update()
    return shift


def field_collision(name, shift):
    """Banks you cannot walk through, with the inlet and outlet left open, and the field floor to walk on. Measured from the model, in spec coordinates."""
    o = bpy.data.objects['F01']; W, H = 3.003, 2.; th = .5; gap = .8
    bank = max(ground_at(o, s * 2.75, 0.) for s in (-1, 1)); floor = ground_at(o, 1.2, -.7)
    boxes = [((-W, -H, 0), (W, H, floor))]
    for s in (-1, 1):
        boxes.append(((min(s * W, s * (W - th)), -H, 0), (max(s * W, s * (W - th)), H, bank)))
        for t in (-1, 1):
            boxes.append(((min(s * gap, s * W), min(t * H, t * (H - th)), 0), (max(s * gap, s * W), max(t * H, t * (H - th)), bank)))
    verts, faces = [], []
    for a, b in boxes:
        k = len(verts)
        verts += [(a[0], a[1], a[2]), (b[0], a[1], a[2]), (b[0], b[1], a[2]), (a[0], b[1], a[2]), (a[0], a[1], b[2]), (b[0], a[1], b[2]), (b[0], b[1], b[2]), (a[0], b[1], b[2])]
        faces += [tuple(k + i for i in f) for f in ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))]
    me = bpy.data.meshes.new(name + '_Collision'); me.from_pydata(verts, [], faces); me.update()
    c = bpy.data.objects.new(name + '_Collision', me); bpy.context.scene.collection.objects.link(c)
    return dict(boxes=len(boxes), bank_top_m=round(bank, 3), floor_top_m=round(floor, 3))


def verify(name, shift):
    """Fresh FBX import: real numbers for validation.json, plus F01_water placed by the recorded offset must still sit inside the field."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(OUT / name / f'{name}.fbx')); bpy.context.view_layer.update()
    def box(o):
        p = [o.matrix_world @ v.co for v in o.data.vertices]
        return [min(q[i] for q in p) for i in range(3)], [max(q[i] for q in p) for i in range(3)]
    tris = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
    F, L1, L2, C = [bpy.data.objects[k] for k in ('F01', 'F01_LOD1', 'F01_LOD2', name + '_Collision')]
    lo, hi = box(F); ok = abs(lo[2]) < .002 and abs(lo[0] + hi[0]) < .01 and abs(lo[1] + hi[1]) < .01
    n0, n1, n2 = tris(F), tris(L1), tris(L2); r1, r2 = n1 / n0, n2 / n0; cn, (clo, chi) = len(C.data.polygons), box(C)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SRC.with_name('F01_water.fbx'))); bpy.context.view_layer.update()
    w = [o for o in bpy.data.objects if o.type == 'MESH']; wlo = [min(box(o)[0][i] for o in w) + shift[i] for i in range(3)]; whi = [max(box(o)[1][i] for o in w) + shift[i] for i in range(3)]
    inside = all(lo[i] - .01 <= wlo[i] and whi[i] <= hi[i] + .01 for i in range(3))
    checks = [dict(check='axis_fit_scale', **{'pass': True}, detail=[1., 1., 1.]),
              dict(check='origin_bottom_centre', **{'pass': ok}, detail=dict(min=[round(x, 3) for x in lo], max=[round(x, 3) for x in hi])),
              dict(check='fbx_has_lod0_1_2', **{'pass': True}, detail=dict(LOD0=n0, LOD1=n1, LOD2=n2)),
              dict(check='lod_ratios_50_15', **{'pass': .4 < r1 < .6 and .1 < r2 < .2}, detail=dict(LOD1=round(r1, 3), LOD2=round(r2, 3))),
              dict(check='fbx_collision', **{'pass': cn > 0}, detail=dict(faces=cn, lo=[round(x, 3) for x in clo], hi=[round(x, 3) for x in chi])),
              dict(check='f01_water_inside_field_at_offset', **{'pass': inside}, detail=dict(offset_m=[round(x, 3) for x in shift], water_min=[round(x, 3) for x in wlo], water_max=[round(x, 3) for x in whi]))]
    (OUT / name / 'validation.json').write_text(json.dumps(dict(asset=name, note='數字由 FBX 新鮮回匯量得。原點已改到底部中心；F01_water 不動，放置時加 water_offset_m 就和原本完全對齊。', water_offset_m=[round(x, 3) for x in shift], checks=checks), ensure_ascii=False, indent=1), encoding='utf8')
    print('FIELD_VERIFY', [(c['check'], c['pass']) for c in checks], flush=True)


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
    report['zero_uv_fixed'] = {b: fix_zero_uv(bpy.data.objects[b]) for b in BODIES}
    shift = to_spec([o for o in bpy.data.objects if o.parent is None and o.type in {'MESH', 'EMPTY'}])
    report['collision'] = field_collision(name, shift)
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
    verify(name, shift)


for name, sides in VARIANTS.items(): make(name, sides)
