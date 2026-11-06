"""F01 for the creek test scene: no bed markers, soft grass. Each field is fed by its own inlet, so no bank is cut; the cutter stays for a variant that needs a slot.

blender --background --factory-startup --python art/source/creek-repair-b/cut_field_gap.py

Slot: round bottom hugging the bamboo (centre z 0.27, radius 0.125) at y = 2 (mid field), opening out above it like a notch dug by hand.
The bamboo fills the hole in the bank's inner face, so the field water does not run out around it.
"""
import json, math, random
from pathlib import Path
import bmesh, bpy
from mathutils import Vector, noise

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
    for _ in range(84):
        side = R.randrange(4)
        cx, cy = {0: (R.uniform(-2.97, -2.45), R.uniform(0, 4)), 1: (R.uniform(2.45, 2.97), R.uniform(0, 4)), 2: (R.uniform(-3, 3), R.uniform(.03, .5)), 3: (R.uniform(-3, 3), R.uniform(3.5, 3.97))}[side]
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
        if foot.z < -.1 or (o.matrix_world.to_3x3() @ normal).normalized().z < .3: continue
        R = random.Random(seed); grown += 1
        for _ in range(blades):
            a = R.uniform(0, math.tau); r = R.uniform(0, .028 * size); L = R.uniform(.1, .2) * size; w = R.uniform(.008, .014) * (.7 + size * .4)
            lean = Vector((math.cos(a), math.sin(a), 0)); across = Vector((-lean.y, lean.x, 0)); base = foot + lean * r - Vector((0, 0, .008)); over = R.uniform(.2, .62)
            shade = R.uniform(.82, 1.12); yellow = R.uniform(0, .22)
            def tone(k): return ((.17 + k * (.3 + yellow * .8)) * shade, (.27 + k * .24) * shade, (.075 + k * .09) * shade, 1)
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


W_, L_, BUND, BED_FOOT, FURROW_W, BEDS, PORT = 6., 4., .63, .245, .26, 5, .3


def spaced(a, b, step):
    n = max(1, round((b - a) / step)); return [a + (b - a) * k / n for k in range(n + 1)]


def plan_lines(edge, mid):
    """Grid lines that follow the field: close on the outer slopes, on every bed edge and furrow, on the port cheeks; a coarser step inside."""
    inner = W_ / 2 - BUND; bed = (2 * inner - (BEDS + 1) * FURROW_W) / BEDS; xs = spaced(-W_ / 2, -W_ / 2 + .3, edge) + spaced(-W_ / 2 + .3, -inner, edge)
    x = -inner
    for _ in range(BEDS):
        xs += spaced(x, x + FURROW_W, edge * 1.6) + spaced(x + FURROW_W, x + FURROW_W + bed, mid); x += FURROW_W + bed
    xs += spaced(x, x + FURROW_W, edge * 1.6) + spaced(inner, W_ / 2 - .3, edge) + spaced(W_ / 2 - .3, W_ / 2, edge) + [-PORT - .001, -PORT + .001, PORT - .001, PORT + .001]
    ys = [0, .002] + spaced(.0, .3, edge) + spaced(.3, BUND, edge) + spaced(BUND, BUND + .42, edge * 1.6) + spaced(BUND + .42, L_ - BUND - .42, mid) + spaced(L_ - BUND - .42, L_ - BUND, edge * 1.6) + spaced(L_ - BUND, L_ - .3, edge) + spaced(L_ - .3, L_, edge) + [L_ - .002, L_]
    def tidy(q):
        out = []
        for v in sorted(q):
            if not out or v - out[-1] > .012 or (v - out[-1] > .0015 and (abs(abs(v) - PORT) < .002 or v < .003 or v > L_ - .003)): out.append(v)
        return out
    return tidy(xs), tidy(ys)


def rounded(x, y, r=.34):
    """Square corners of the bank pulled into a quarter circle, as a bank settles; only inside the outer r of the plan."""
    ax, ay = abs(x) - (W_ / 2 - r), abs(y - L_ / 2) - (L_ / 2 - r)
    if ax <= 0 or ay <= 0: return x, y
    k = max(ax, ay) / math.hypot(ax, ay)
    return math.copysign(W_ / 2 - r + ax * k, x), L_ / 2 + math.copysign(L_ / 2 - r + ay * k, y - L_ / 2)


def footprints():
    """Where people walk the crest: left-right steps along the two long banks and the south one."""
    R = random.Random(2203); out = []
    for sx in (-1, 1):
        y = .75
        while y < 3.25:
            step = len(out) % 2 * 2 - 1; out.append((sx * (W_ / 2 - .4) + step * .055 + R.uniform(-.01, .01), y, 0.)); y += R.uniform(.26, .36)
    x = -2.3
    while x < 2.3:
        if abs(x) > .55:
            step = len(out) % 2 * 2 - 1; out.append((x, .4 + step * .055, 1.57))
        x += R.uniform(.26, .36)
    return out


FOOTPRINTS = footprints()


def trodden(x, y):
    """How far (x, y) is inside a footprint on the crest, 0 to 1."""
    t = 0.
    for fx, fy, a in FOOTPRINTS:
        dx, dy = x - fx, y - fy
        if abs(dx) > .13 or abs(dy) > .13: continue
        u, v = dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)
        t = max(t, max(0., 1 - (u / .06) ** 2 - (v / .115) ** 2))
    return min(1., t * 2.2)


def field_surface(base, x, y, bottom):
    """Height and colour of the soil at (x, y). 'base' is the old surface (None where the ports are): the layout stays, its surface gets dug, trodden and rained on."""
    d = min(W_ / 2 - abs(x), y, L_ - y); port = abs(x) < PORT + .001 and (y < BUND or y > L_ - BUND)
    if base is None: return (bottom if y < .001 or y > L_ - .001 else -.02), (.34, .32, .27)
    n = lambda f, s=0., a=x, b=y: noise.noise(Vector((a * f + s, b * f - s, s * .37)))
    near_port = min(1., max(0., (abs(x) - PORT) / .16)) if y < BUND + .1 or y > L_ - BUND - .1 else 1.
    inner = d > BUND + .01; bed = inner and base > BED_FOOT; furrow = inner and not bed
    if bed:   # hoe-turned clods and shallow lines across the bed; only ever up, so the bed never drops under the water
        top = min(1., (base - BED_FOOT) / .08)
        # the hoe lines across the bed are deep enough to throw a shadow when the whole field is in view (review, 2026-11-06)
        # the old beds rise .1 m over a long, soft shoulder: twice as steep, same top, so a bed reads as a dug block and not a mound
        rise = base - BED_FOOT; z = base + min(.105, rise * 2.) - min(.105, rise)
        z += top * (abs(n(13., 1.)) * .022 + abs(n(29., 3.)) * .01 + .013 * math.sin(y * math.tau / .31 + 1.6 * n(2., 9.)))
    elif furrow: z = base + n(6., 5.) * .004
    else:     # banks: slumped lumps, rain gullies down the outer face, the crest beaten flatter along its middle
        slope = max(0., min(1., 1 - (d - .25) / .1)); run = y if abs(x) > W_ / 2 - .5 else x
        gully = -abs(noise.noise(Vector((run * 3.1 + 11., d * .9, 4.)))) * .055 * slope * min(1., d / .1) + .012 * slope
        crest = 1 - .65 * max(0., 1 - abs(d - .4) / .12)
        z = base + near_port * (n(2.1, 7.) * .03 * crest + n(7., 2.) * .014 * crest + n(17., 8.) * .007 + gully) - .032 * trodden(x, y)
    foot = 1 - d / .25
    if d < .25 and not port: z += bottom * foot ** 1.5
    # colour multiplies the soil texture: dry pale crest, dark wet near the water, moss where the bank stays damp
    dry = max(0., min(1., (z - .3) / .09)) * (0. if bed else 1.); wet = max(0., min(1., (.3 - z) / .07)) if inner else 0.
    c = Vector((.68, .67, .6)).lerp(Vector((.88, .88, .76)), dry * (.55 + .45 * max(0., n(1.7, 4.) * 2.2 + .6))).lerp(Vector((.38, .36, .32)), wet * .9)
    if bed:   # fresh-dug: a darker, warmer brown than the beaten banks, darkest in the hoe lines
        c = Vector((.5, .43, .34)) * (.8 + abs(n(13., 1.)) * 1.1 + abs(n(29., 3.)) * .5) * (.88 + .12 * math.sin(y * math.tau / .31 + 1.6 * n(2., 9.)))
    if not bed and not furrow:
        patch = max(0., min(1., (n(1.6, 13.) + .5 * n(5., 6.) + .1 - (.0 if d < .3 or d > .52 else .16)) * 3.2))
        c = c.lerp(Vector((.46, .53, .25)), patch * .72)
    if not inner: c = c * (1 - .5 * trodden(x, y))
    c = c * (.93 + n(31., 2.) * .14)
    return z, (c.x, c.y, c.z)


def probe_scale(probe):
    """UV per metre of the old soil, so the texture keeps its scale."""
    me = probe.data; uv = me.uv_layers.active; s = []
    for poly in me.polygons[:4000]:
        a, b = poly.loop_indices[0], poly.loop_indices[1]; q = (me.vertices[me.loops[a].vertex_index].co - me.vertices[me.loops[b].vertex_index].co).length
        if q > .02: s.append((uv.data[a].uv - uv.data[b].uv).length / q)
    s.sort(); return s[len(s) // 2]


def resurface(o, probe, edge, mid, bottom):
    """The field's soil becomes one regular grid over the old layout, so it can carry lumps and colour on every LOD; stone, timber and bronze are left as they were."""
    me = o.data; soil = next(i for i, m in enumerate(me.materials) if m.name.startswith('ww_field_soil')); pinv = probe.matrix_world.inverted(); down = pinv.to_3x3() @ Vector((0, 0, -1)); inv = o.matrix_world.inverted()
    keep_faces(o, lambda f: f.material_index != soil)
    bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active; name = me.color_attributes.active_color.name
    col = bm.loops.layers.float_color.get(name) or bm.loops.layers.color.get(name)
    xs, ys = plan_lines(edge, mid); grid = []; colours = {}; k = probe_scale(probe)
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            sx, sy = x * .9985 if abs(x) > 2.99 else x, min(max(y, .004), L_ - .004)
            hit, at, _, _ = probe.ray_cast(pinv @ Vector((sx, sy, 2)), down)
            base = (probe.matrix_world @ at).z if hit else None
            z, c = field_surface(base, x, y, bottom); px, py = rounded(x, y); colours[(i, j)] = c
            row.append(bm.verts.new(inv @ Vector((px, py, z))))
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])); f.material_index = soil; f.smooth = True
            for l, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                v = o.matrix_world @ l.vert.co; out = max(0., min(1., 1 - min(W_ / 2 - abs(v.x), v.y, L_ - v.y) / .6))
                l[uvl].uv = ((v.x + math.copysign(v.z * out * .7, v.x)) * k, (v.y + math.copysign(v.z * out * .7, v.y - L_ / 2)) * k)
                c = colours[(a, b)]; l[col] = (c[0], c[1], c[2], 1)
    bm.to_mesh(me); me.update(); bm.free(); bpy.context.view_layer.update()
    return (len(xs) - 1) * (len(ys) - 1) * 2


def weather_stone(o):
    """The old channel stone is pale beside everything else on the site: same warm grey, a shade darker towards the wet."""
    me = o.data; slots = {i for i, m in enumerate(me.materials) if m.name.split('.')[0].startswith('ww_stone')}; col = me.color_attributes.active_color
    for poly in me.polygons:
        if poly.material_index in slots:
            for l in poly.loop_indices:
                c = col.data[l].color; z = (o.matrix_world @ me.vertices[me.loops[l].vertex_index].co).z; p_ = o.matrix_world @ me.vertices[me.loops[l].vertex_index].co; k = (.27 + .12 * max(0., min(1., (z - .15) / .3))) * (.85 + .5 * noise.noise(p_ * 5.)); g_ = max(0., noise.noise(p_ * 3. + Vector((7, 1, 2))) * 1.6 + .25 - z * .9)   # stained and damp, moss creeping up from the wet
                col.data[l].color = (c[0] * k * (1 - .35 * g_), c[1] * k * .97 * (1 - .05 * g_), c[2] * k * .88 * (1 - .55 * g_), c[3])


def foot_stones(o, count, sub, bottom):
    """Field stones turned up by the digging and rolled to the foot of the bank, half sunk; same place on every LOD."""
    me = o.data; slot = next(i for i, m in enumerate(me.materials) if m.name.split('.')[0] == 'ww_stone'); inv = o.matrix_world.inverted()
    bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active; name = me.color_attributes.active_color.name; col = bm.loops.layers.float_color.get(name) or bm.loops.layers.color.get(name)
    R = random.Random(1707); n = 0
    for s in range(22):
        side = R.randrange(4); t = R.uniform(.16, .84); d = R.uniform(.06, .17); size = R.uniform(.055, .15)
        x, y = {0: (-W_ / 2 + d, t * L_), 1: (W_ / 2 - d, t * L_), 2: ((t - .5) * W_, d), 3: ((t - .5) * W_, L_ - d)}[side]
        if (abs(x) < .55 and (y < 1 or y > 3)) or s >= count: continue
        z = bottom * (1 - d / .25) ** 1.5 + .25 * d / .12 * .9 - size * .1; x, y = rounded(x, y); yaw = R.uniform(0, math.tau); q = R.uniform(.55, .78); w = R.uniform(.72, 1.)
        ret = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.)
        for v in ret['verts']:
            p_ = Vector(v.co); p_ *= 1 + noise.noise(p_ * 1.6 + Vector((s, s * 2, 3))) * .28
            p_.x, p_.y, p_.z = p_.x * size * 1.15, p_.y * size * w, p_.z * size * q
            v.co = inv @ Vector((x + p_.x * math.cos(yaw) - p_.y * math.sin(yaw), y + p_.x * math.sin(yaw) + p_.y * math.cos(yaw), z + p_.z))
        shade = R.uniform(.34, .5); up = R.uniform(.1, .6)
        for f in {f for v in ret['verts'] for f in v.link_faces}:
            f.material_index = slot; f.smooth = False
            for l in f.loops:
                wp = o.matrix_world @ l.vert.co; top = max(0., min(1., (wp.z - z) / (size * q)))
                c = Vector((shade, shade * .97, shade * .9)).lerp(Vector((.5, .55, .3)), top * up)
                l[uvl].uv = (wp.x * .9 + wp.z * .5, wp.y * .9 + wp.z * .5); l[col] = (c.x, c.y, c.z, 1)
        n += 1
    bm.to_mesh(me); me.update(); bm.free(); bpy.context.view_layer.update()
    return n


def bank_gravel(o, count):
    """Grit and small stones lying on the banks and down their faces."""
    me = o.data; slot = next(i for i, m in enumerate(me.materials) if m.name.split('.')[0] == 'ww_stone'); inv = o.matrix_world.inverted(); down = inv.to_3x3() @ Vector((0, 0, -1))
    bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active; name = me.color_attributes.active_color.name; col = bm.loops.layers.float_color.get(name) or bm.loops.layers.color.get(name)
    R = random.Random(2401); n = 0
    for s in range(count * 3):
        if n >= count: break
        side = R.randrange(4); t = R.random(); d = R.uniform(.03, .58)
        x, y = {0: (-W_ / 2 + d, t * L_), 1: (W_ / 2 - d, t * L_), 2: ((t - .5) * W_, d), 3: ((t - .5) * W_, L_ - d)}[side]
        if abs(x) < .4 and (y < .8 or y > 3.2): continue
        hit, at, _, _ = o.ray_cast(inv @ Vector((x, y, 2)), down)
        if not hit or me.polygons[o.ray_cast(inv @ Vector((x, y, 2)), down)[3]].material_index == slot: continue
        p0 = o.matrix_world @ at; size = R.uniform(.009, .026); ret = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.); yaw = R.uniform(0, 6.28)
        for v in ret['verts']:
            q = Vector(v.co); q *= 1 + noise.noise(q * 2.4 + Vector((s, 2, 3))) * .35
            v.co = inv @ (p0 + Vector((q.x * size * 1.25 * math.cos(yaw) - q.y * size * math.sin(yaw), q.x * size * 1.25 * math.sin(yaw) + q.y * size * math.cos(yaw), q.z * size * .6)))
        k = R.uniform(.26, .5)
        for f in {f for v in ret['verts'] for f in v.link_faces}:
            f.material_index = slot; f.smooth = False
            for l in f.loops:
                wp = o.matrix_world @ l.vert.co; l[uvl].uv = (wp.x * 1.5, wp.y * 1.5 + wp.z); l[col] = (k, k * .97, k * .88, 1)
        n += 1
    bm.to_mesh(me); me.update(); bm.free(); bpy.context.view_layer.update()
    return n


def bed_clods(o, count, sub):
    """Clods the hoe turned over, lying on the beds: the part of a dug bed the grid is too coarse to carry. Same places on every LOD, only fewer."""
    me = o.data; soil = next(i for i, m in enumerate(me.materials) if m.name.startswith('ww_field_soil')); inv = o.matrix_world.inverted(); down = inv.to_3x3() @ Vector((0, 0, -1))
    bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active; name = me.color_attributes.active_color.name; col = bm.loops.layers.float_color.get(name) or bm.loops.layers.color.get(name)
    inner = W_ / 2 - BUND; bed = (2 * inner - (BEDS + 1) * FURROW_W) / BEDS; R = random.Random(1909); placed = []
    for s in range(count * 2):
        i = R.randrange(BEDS); x0 = -inner + FURROW_W + i * (bed + FURROW_W); placed.append((x0 + R.uniform(.09, bed - .09), R.uniform(BUND + .52, L_ - BUND - .52), R.uniform(.02, .05), s))
    n = 0
    for x, y, size, s in placed:
        if n >= count: break
        hit, at, _, _ = o.ray_cast(inv @ Vector((x, y, 2)), down)
        if not hit or (o.matrix_world @ at).z < BED_FOOT + .05: continue
        z = (o.matrix_world @ at).z; yaw = s * 2.399; ret = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.)
        for v in ret['verts']:
            p_ = Vector(v.co); p_ *= 1 + noise.noise(p_ * 2.2 + Vector((s, s * 3, 1))) * .4
            p_.x, p_.y, p_.z = p_.x * size * 1.2, p_.y * size, p_.z * size * .68
            v.co = inv @ Vector((x + p_.x * math.cos(yaw) - p_.y * math.sin(yaw), y + p_.x * math.sin(yaw) + p_.y * math.cos(yaw), z + p_.z))
        k = .4 + (s % 7) * .055
        for f in {f for v in ret['verts'] for f in v.link_faces}:
            f.material_index = soil; f.smooth = False
            for l in f.loops:
                wp = o.matrix_world @ l.vert.co; l[uvl].uv = (wp.x * .9 + wp.z, wp.y * .9 + wp.z); l[col] = (k * .98, k * .92, k * .8, 1)
        n += 1
    bm.to_mesh(me); me.update(); bm.free(); bpy.context.view_layer.update()
    return n


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
    bottom = min((bpy.data.objects['F01'].matrix_world @ v.co).z for v in bpy.data.objects['F01'].data.vertices)
    probe = bpy.data.objects['F01'].copy(); probe.data = bpy.data.objects['F01'].data.copy(); probe.name = 'probe'; bpy.context.scene.collection.objects.link(probe)
    soil = next(i for i, m in enumerate(probe.data.materials) if m.name.startswith('ww_field_soil')); keep_faces(probe, lambda f: f.material_index == soil); bpy.context.view_layer.update()
    report['tris_before_grass'] = {b: resurface(bpy.data.objects[b], probe, e, m_, bottom) for b, e, m_ in (('F01', .05, .075), ('F01_LOD1', .068, .1), ('F01_LOD2', .12, .18))}
    bpy.data.objects.remove(probe)
    for b in BODIES: weather_stone(bpy.data.objects[b])
    report['bed_clods'] = {b: bed_clods(bpy.data.objects[b], n, 1) for b, n in (('F01', 340), ('F01_LOD1', 180), ('F01_LOD2', 70))}
    report['bank_gravel'] = {b: bank_gravel(bpy.data.objects[b], n) for b, n in (('F01', 190), ('F01_LOD1', 70), ('F01_LOD2', 20))}
    report['foot_stones'] = {b: foot_stones(bpy.data.objects[b], n, sub, bottom) for b, n, sub in (('F01', 22, 2), ('F01_LOD1', 22, 1), ('F01_LOD2', 10, 1))}
    report['grass_tufts'] = {b: regrow(bpy.data.objects[b], keep, blades, joints) for b, keep, blades, joints in (('F01', 1, 13, 3), ('F01_LOD1', 1, 8, 2), ('F01_LOD2', 1, 5, 1))}
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
