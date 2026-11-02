"""BR02 young pine that the boar runs into (Johnnnny0823, day 3, from the saved three-view art/references/BR02/selected.png).

  blender -b --python-exit-code 1 --python art/source/zhuo-boar-a/build_pine.py -- A|B

Two different trees, not one rotated. One mesh with its pivot at the root: the game leans it 8 degrees by rotating the object. The pale
scar near the base opens through _Scar (Mask B). Needles are tufts of three-sided blades coloured by vertex colour (sunlit yellow-green
on top, cool teal below and inside) over a neutral swatch in the atlas, and lit with normals pushed out from the crown.
Front is -Y, origin at the root, z = 0 at the base, 1 unit = 1 m.
"""
import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise as mnoise

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K
from kitlib import L, N, math_, mix, mixf, noise, sep, smooth, voronoi, world_pos
from build_boar import coords_of, join, loft_path, set_coords, tag

VAR = sys.argv[sys.argv.index('--') + 1]
VER = 'v001'
KEY = f'BR02_YoungPine_{VAR}'
OUT = K.EXPORTS / KEY
rnd = random.Random(2203 if VAR == 'A' else 3307)
SUN, MID, SHADE = (.34, .47, .10), (.075, .22, .07), (.012, .068, .06)   # style guide crown colours, linear: #b6d07c, #4a8650, #1d4a46

# Two different figures: A leans one way with long low tiers; B forks near the top with a higher, rounder crown and a bare lower trunk.
SHAPES = {
    'A': dict(path=[(0, 0, 0), (.01, 0, .6), (.035, .012, 1.4), (.085, .03, 2.4), (.13, .04, 3.4), (.15, .03, 4.2), (.14, .02, 4.82)], first=1.2, tiers=8, count=(4, 5), reach=1.2, top_reach=.32, droop=.13),
    'B': dict(path=[(0, 0, 0), (-.012, .008, .7), (-.05, .03, 1.6), (-.075, .06, 2.5), (-.06, .085, 3.3), (-.02, .09, 4.0), (.03, .08, 4.75)], first=1.75, tiers=8, count=(4, 6), reach=1.12, top_reach=.5, droop=.04),
}


def m_bark():
    m, nt, b = K.new_mat('PineBark')
    P = world_pos(nt); x, y, z = sep(nt, P)
    mp = N(nt, 'ShaderNodeMapping'); L(nt, P, mp.inputs['Vector']); mp.inputs['Scale'].default_value = (17, 17, 4.5)
    plates = voronoi(nt, mp.outputs['Vector'], 1.0)
    cracks = smooth(nt, plates, .05, .32)
    grain = noise(nt, mp.outputs['Vector'], 3.0, 4.0, .6)
    base = mix(nt, cracks, (.018, .012, .012), mix(nt, smooth(nt, grain, .35, .65), (.095, .065, .045), (.25, .17, .11)))
    # Warm sun-faded plates up high, a darker damp base with moss.
    base = mix(nt, math_(nt, 'MULTIPLY', smooth(nt, z, .9, 2.8), .4), base, (.36, .22, .12))
    moss = math_(nt, 'MULTIPLY', smooth(nt, z, .42, .05), smooth(nt, noise(nt, P, 7.0, 3.0, .55), .44, .6))
    base = mix(nt, math_(nt, 'MULTIPLY', moss, .6), base, (.06, .085, .025))
    # Mask B: the patch a charging animal scrapes pale, wrapped most of the way round so any side can be hit.
    edge = noise(nt, P, 14.0, 3.0, .6)
    band = math_(nt, 'MULTIPLY', smooth(nt, math_(nt, 'ADD', z, math_(nt, 'MULTIPLY', edge, .22)), .32, .45), smooth(nt, math_(nt, 'ADD', z, math_(nt, 'MULTIPLY', edge, .3)), 1.0, .84))
    band = math_(nt, 'MULTIPLY', band, smooth(nt, noise(nt, P, 4.2, 3.0, .55), .36, .5))     # broken up round the trunk
    scar = math_(nt, 'MULTIPLY', band, mixf(nt, cracks, .2, .78))
    scar = math_(nt, 'ADD', scar, math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', band, smooth(nt, grain, .4, .6)), .22))
    cm = N(nt, 'ShaderNodeCombineColor'); L(nt, scar, cm.inputs[2])
    return K.finish(m, nt, b, base, mixf(nt, cracks, .95, .82), height=cracks, bump=.012, bump_strength=.9, mask=cm.outputs[0])


def m_resin():
    m, nt, b = K.new_mat('PineResin')
    return K.finish(m, nt, b, (.62, .31, .06), .28)


def m_swatch():
    # Neutral: the needles' colour comes from vertex colour.
    m, nt, b = K.new_mat('NeedleSwatch')
    return K.finish(m, nt, b, (.92, .92, .9), .95)


def trunk_nodes(path):
    pts = [Vector(p) for p in path]
    n = len(pts) - 1
    out = []
    for i, p in enumerate(pts):
        t = i / n
        # Tapers from the 0.25 m trunk to a leader; only a slight widening at the ground.
        r = .125 * (1 - t) ** .78 + .012
        out.append((p.x, p.y, p.z, r))
    base = out[0]
    return [(base[0], base[1], 0.0, .15), (base[0], base[1], .07, .137), (base[0], base[1], .2, .125)] + [o for o in out[1:]]


def trunk_at(path, z):
    pts = [Vector(p) for p in path]
    for a, b in zip(pts, pts[1:]):
        if a.z <= z <= b.z:
            return a.lerp(b, (z - a.z) / max(b.z - a.z, 1e-6))
    return pts[-1]


def branch(name, start, direction, length, r0, mat, droop, wobble=.1, segs=8):
    """A bent limb, with its node list returned for the twigs and needles."""
    nodes = []
    p = Vector(start); d = Vector(direction).normalized()
    steps = 5
    for i in range(steps + 1):
        t = i / steps
        nodes.append((p.x, p.y, p.z, r0 * (1 - t * .88)))
        d = (d + Vector((rnd.uniform(-wobble, wobble), rnd.uniform(-wobble, wobble), rnd.uniform(-wobble, wobble) - droop * (.2 + t)))).normalized()
        p = p + d * (length / steps)
    o = loft_path(name, nodes, mat, 0, per=3, segs=segs)
    return o, [Vector(n[:3]) for n in nodes]


def build_wood(shape, bark, resin):
    parts = []
    path = shape['path']
    trunk = loft_path('Trunk', trunk_nodes(path), bark, 0, per=11, segs=44)
    # Rough plated bark in the silhouette, not only in the bump.
    trunk.data.update()
    nrm = np.zeros(len(trunk.data.vertices) * 3, np.float32); trunk.data.vertex_normals.foreach_get('vector', nrm); nrm = nrm.reshape(-1, 3)
    c = coords_of(trunk)
    for i, co in enumerate(c):
        v = Vector((co[0] * 13, co[1] * 13, co[2] * 3.4))
        k = min(1.0, .35 + .65 * max(0.0, 1 - co[2] / 3))
        c[i] = co + nrm[i] * (mnoise.noise(v) * .013 + mnoise.noise(v * 2.7) * .005) * k
    set_coords(trunk, c)
    parts.append(trunk)
    # A few roots show briefly before diving into the soil.
    for i in range(5):
        a = i / 5 * math.tau + rnd.uniform(-.3, .3)
        d = Vector((math.cos(a), math.sin(a), 0))
        parts.append(loft_path(f'Root{i}', [(*(d * .08 + Vector((0, 0, .1))), .042), (*(d * .14 + Vector((0, 0, .045))), .034), (*(d * .19 + Vector((0, 0, .008))), .024), (*(d * .21 + Vector((0, 0, 0))), .012)], bark, 0, per=3, segs=9))
    tips = []
    z = shape['first']
    top = path[-1][2]
    n_tiers = shape['tiers']
    for tier in range(n_tiers):
        t = tier / max(n_tiers - 1, 1)
        z_t = z + (top - .5 - z) * t + rnd.uniform(-.07, .07)
        count = rnd.randint(*shape['count'])
        a0 = rnd.uniform(0, math.tau)
        for k in range(count):
            a = a0 + k / count * math.tau + rnd.uniform(-.34, .34)
            reach = (shape['reach'] * (1 - t) ** .8 + shape['top_reach'] * t) * rnd.uniform(.72, 1.1)
            zz = z_t + rnd.uniform(-.09, .09)
            start = trunk_at(path, zz)
            d = Vector((math.cos(a), math.sin(a), rnd.uniform(.05, .22) + t * .25))
            o, line = branch(f'Limb{tier}_{k}', start, d, reach, .037 * (1 - t * .55) + .006, bark, shape['droop'])
            parts.append(o)
            tips.append(line[-1])
            # Twigs off each limb; these carry the tufts.
            for j, node in enumerate(line[2:], 2):
                for s in (1, -1):
                    if rnd.random() < .22: continue
                    side = Vector((-math.sin(a), math.cos(a), 0)) * s
                    tw = (d.normalized() * .7 + side * .85 + Vector((0, 0, rnd.uniform(-.1, .25)))).normalized()
                    lt = reach * rnd.uniform(.2, .34) * (1.1 - j * .1)
                    oo, tl = branch(f'Twig{tier}_{k}_{j}_{s}', node, tw, lt, .009, bark, .05, wobble=.14, segs=5)
                    parts.append(oo)
                    tips += [tl[3], tl[-1]]
            tips += line[1:]
            tips += [n.lerp(m, .5) for n, m in zip(line[1:], line[2:])]
    # The leader's own tufts and broken stubs on the bare trunk.
    tips += [trunk_at(path, top - i * .14) for i in range(5)]
    for i in range(6):
        zz = rnd.uniform(.95, shape['first'] - .05)
        a = rnd.uniform(0, math.tau)
        s0 = trunk_at(path, zz)
        d = Vector((math.cos(a), math.sin(a), .25))
        o, _ = branch(f'Stub{i}', s0, d, rnd.uniform(.14, .3), .017, bark, .02, segs=6)
        parts.append(o)
    # Resin beads on the bark.
    for i in range(14):
        zz = rnd.uniform(.5, 2.2); a = rnd.uniform(0, math.tau)
        c = trunk_at(path, zz)
        r_t = .125 * (1 - zz / top) ** .78 + .012
        pos = c + Vector((math.cos(a), math.sin(a), 0)) * (r_t + .002)
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=.009)
        bmesh.ops.scale(bm, vec=(1, 1, 1.6), verts=bm.verts); bmesh.ops.translate(bm, vec=pos, verts=bm.verts)
        me = bpy.data.meshes.new(f'Resin{i}'); bm.to_mesh(me); bm.free()
        for pl in me.polygons: pl.use_smooth = True
        oo = bpy.data.objects.new(f'Resin{i}', me); K.link(oo); me.materials.append(resin); parts.append(oo)
    return parts, tips


def needle_mesh(name, tufts, blades, length_k, width, centre, seed):
    """Tufts at each twig point: three-sided blades in a brush, coloured and lit by where they sit in the crown."""
    r = random.Random(seed)
    verts, faces, cols, norms = [], [], [], []
    zs = [t.z for t in tufts] or [1]
    z0, z1 = min(zs), max(zs)
    for tuft in tufts:
        out = Vector((tuft.x - centre.x, tuft.y - centre.y, (tuft.z - (z0 + z1) / 2) * .55))
        rad = out.length
        out = out.normalized() if rad > 1e-3 else Vector((0, 0, 1))
        # How sun-facing and how far out this tuft is sets its colour.
        up = (tuft.z - z0) / max(z1 - z0, .01)
        outer = min(1, rad / 1.0)
        n_col = max(0, min(1, .4 * up + .42 * outer + r.uniform(-.14, .14)))
        for _ in range(blades):
            d = (out * .55 + Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-.55, 1.0)))).normalized()
            L_ = r.uniform(.15, .25) * length_k
            u = d.cross(Vector((0, 0, 1)))
            if u.length < 1e-3: u = Vector((1, 0, 0))
            u.normalize(); v = d.cross(u)
            base = len(verts)
            # Needle tops catch the sun; the undersides fall to teal, inside the blade's own length too.
            lit = n_col + .2 * d.z
            tip_col = lerp3(MID, SUN, clamp01(lit * 1.5 - .1)) if lit > .22 else lerp3(SHADE, MID, clamp01(lit / .22))
            root_col = lerp3(SHADE, tip_col, .35)
            for a in (0, 2.094, 4.189):
                verts.append(tuft + (u * math.cos(a) + v * math.sin(a)) * width)
                cols.append((*root_col, 1)); norms.append((out * .85 + d * .3 + Vector((0, 0, .25))).normalized())
            verts.append(tuft + d * L_ + Vector((0, 0, -L_ * .1)))
            cols.append((*tip_col, 1)); norms.append((out * .8 + d * .35 + Vector((0, 0, .3))).normalized())
            for k in range(3):
                faces.append((base + k, base + (k + 1) % 3, base + 3))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in verts], [], faces)
    me.update()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); K.link(o)
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT')
    col.data.foreach_set('color', np.array(cols, np.float32).ravel())
    me.normals_split_custom_set_from_vertices([tuple(n) for n in norms])
    return o


def lerp3(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def clamp01(v): return max(0.0, min(1.0, v))


def main():
    s = K.reset()
    K.gpu(s, 1)
    src = K.coll('Source')
    K.ACTIVE['coll'] = src
    bark = m_bark(); resin = m_resin(); swatch_mat = m_swatch()
    shape = SHAPES[VAR]
    parts, tips = build_wood(shape, bark, resin)
    # Raw tube ends sit a little below ground where a root dives: flatten to z = 0.
    for o in parts:
        c = coords_of(o); c[:, 2] = np.maximum(c[:, 2], 0); set_coords(o, c)
        for p in o.data.polygons: p.use_smooth = True
    # The neutral swatch the needles sample; deleted after the bake.
    bpy.ops.mesh.primitive_plane_add(size=.16, location=(0, -2, .001))
    sw = bpy.context.active_object; sw.name = 'Swatch'
    if sw.name not in K.ACTIVE['coll'].objects:
        for c in list(sw.users_collection): c.objects.unlink(sw)
        K.ACTIVE['coll'].objects.link(sw)
    sw.data.materials.append(swatch_mat)
    parts.append(sw)
    for o in parts:
        if not o.data.color_attributes.get('Col'):
            col = o.data.color_attributes.new('Col', 'BYTE_COLOR', 'POINT')
            col.data.foreach_set('color', np.ones(len(o.data.vertices) * 4, np.float32))
    K.finalize_parts(parts)
    gcoll = K.coll('Game')
    G, _ = K.game_mesh(KEY, parts, gcoll)
    K.ACTIVE['coll'] = gcoll
    for o in parts: o.hide_render = True
    src.hide_viewport = True
    imgs, _ = K.bake_asset(G, KEY, OUT / 'textures', res=1536, ao_samples=48)
    mat = K.game_material(KEY, imgs)
    # Find the swatch's atlas spot, then drop it.
    swatch_index = next(i for i, m in enumerate(G.data.materials) if m.name.startswith('NeedleSwatch'))
    uv = G.data.uv_layers['UVMap'].data
    us = [uv[li].uv.copy() for poly in G.data.polygons if poly.material_index == swatch_index for li in poly.loop_indices]
    centre_uv = sum(us, Vector((0, 0))) / len(us)
    bm = bmesh.new(); bm.from_mesh(G.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == swatch_index], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(G.data); bm.free()
    G.data.materials.clear(); G.data.materials.append(mat)
    for p in G.data.polygons: p.material_index = 0
    lods = [G] + K.make_lods(G, ratios=(.5, .15), gcoll=gcoll)
    centre = sum(tips, Vector((0, 0, 0))) / len(tips)
    finals = []
    for level, (lod, keep_frac, blades, lk, width) in enumerate(zip(lods, (.92, .6, .26), (13, 10, 5), (1.0, 1.15, 1.5), (.0105, .013, .023))):
        rr = random.Random(77)
        kept = [t for t in tips if rr.random() < keep_frac]
        nd = needle_mesh(f'Needles_L{level}', kept, blades, lk, width, centre, 41)
        nuv = nd.data.uv_layers.new(name='UVMap')
        arr = np.tile(np.array(centre_uv[:], np.float32), len(nd.data.loops))
        # Tiny spread so tangents stay valid.
        arr[::2] += (np.arange(len(nd.data.loops)) % 3) * 1e-4
        arr[1::2] += (np.arange(len(nd.data.loops)) % 5) * 1e-4
        nuv.data.foreach_set('uv', arr)
        nd.data.materials.append(mat)
        keep = lod.copy(); keep.data = lod.data.copy(); gcoll.objects.link(keep)
        finals.append(join([keep, nd], f'tmp{level}'))
    for o in lods: bpy.data.objects.remove(o)
    size = []
    for level, o in enumerate(finals):
        o.name = o.data.name = f'{KEY}_LOD{level}' if level else KEY
        for name in ('qa_lc', 'qa_seed', 'qa_node', 'qa_part'):
            at = o.data.attributes.get(name)
            if at: o.data.attributes.remove(at)
        for p in o.data.polygons: p.use_smooth = True
        c = coords_of(o)
        c[:, 2] = np.maximum(c[:, 2], 0)
        # Hold the tree inside the listed box.
        c[:, 0] = np.clip(c[:, 0], -1.25, 1.25); c[:, 1] = np.clip(c[:, 1], -1.25, 1.25); c[:, 2] = np.minimum(c[:, 2], 5.0)
        set_coords(o, c)
        if not level: size = (c.min(axis=0), c.max(axis=0))
    # Collision: the trunk as a convex cylinder, 0.35 m across and 2 m tall.
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=14, radius1=.175, radius2=.175, depth=2.0)
    bmesh.ops.translate(bm, vec=(0, 0, 1), verts=bm.verts)
    col_me = bpy.data.meshes.new(KEY + '_Collision'); bm.to_mesh(col_me); bm.free()
    col = bpy.data.objects.new(KEY + '_Collision', col_me); gcoll.objects.link(col); col.hide_render = True
    K.BLEND = K.HERE / 'blend'
    (K.HERE / 'blend').mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    glb = OUT / f'{KEY}_{VER}.glb'; fbx = OUT / f'{KEY}_{VER}.fbx'
    K.select_only(finals + [col], finals[0])
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_apply=False, export_yup=True, export_image_format='AUTO', export_materials='EXPORT', export_vertex_color='ACTIVE', export_extras=False)
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'}, axis_forward='-Z', axis_up='Y', apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, mesh_smooth_type='FACE', use_tspace=True, colors_type='LINEAR', path_mode='RELATIVE', embed_textures=False)
    mn, mx = size
    info = {
        'id': 'BR02', 'name': KEY, 'version': VER, 'unit': 'metre, 1 unit = 1 m', 'origin': 'at the root, lowest vertex at z = 0, no ground plate; the pivot is what the game rotates',
        'sizeM': {'width': round(float(mx[0] - mn[0]), 3), 'depth': round(float(mx[1] - mn[1]), 3), 'height': round(float(mx[2] - mn[2]), 3), 'trunkDiameterAtGround': .3, 'trunkDiameter': .25},
        'limitM': {'width': 2.5, 'depth': 2.5, 'height': 5.0, 'trunkDiameter': .25},
        'tris': {f'LOD{i}': K.tri_count(o) for i, o in enumerate(finals)},
        'collision': {'name': col.name, 'kind': 'convex cylinder', 'diameterM': .35, 'heightM': 2.0, 'tris': K.tri_count(col)},
        'material': {'name': mat.name, 'textures': [f'textures/T_{KEY}_{n}.png' for n in ('BaseColor', 'ORM', 'Normal', 'Mask')], 'atlas': 1536, 'unityShader': 'YunJing/QingxiZhuoBoar', 'vertexColour': 'needle colour, multiplied onto a neutral swatch'},
        'state': {'_Scar': {'range': [0, 1], 'meaning': '0 = whole bark, 1 = pale scraped patch near the base', 'mask': 'Mask B'}, 'lean': 'rotate the object about its origin; the game leans it 8 degrees'},
    }
    (OUT / f'{KEY}_model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(K.HERE / 'blend' / f'{KEY}_{VER}.blend'), compress=True)
    print('PINE_BUILD_PASS', KEY, json.dumps(info['tris']), info['sizeM'], flush=True)


main()
