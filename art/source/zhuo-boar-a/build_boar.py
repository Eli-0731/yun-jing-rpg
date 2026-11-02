"""BR01 sick mountain boar (Johnnnny0823, day 3, from the saved three-view art/references/BR01/selected.png).

  blender -b --python-exit-code 1 --python art/source/zhuo-boar-a/build_boar.py

Original procedural model, no third-party mesh. Body: lofted sections and muscle masses, voxel-remeshed into one skin, sculpted
with dents and noise, decimated. Atlas baked from procedural materials (position-driven), including the state mask for _Zhuo.
Fur and bristles are tapered blade clusters that sample the body's atlas at their root and carry a root-to-tip gradient in vertex
colour, so they cost no atlas space. Rig: Root + 24 bones. Animations are authored with IK on the feet, then baked to FK.
Front is -Y, origin between the feet at z = 0, 1 unit = 1 m.
"""
import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector, kdtree, noise as mnoise
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K
from kitlib import L, N, math_, mix, mixf, noise, sep, smooth, voronoi, world_pos

KEY = 'BR01_ZhuoBoar'
VER = 'v001'
OUT = K.EXPORTS / KEY
BLEND = K.HERE / 'blend'
PART_BODY, PART_EAR_L, PART_EAR_R, PART_HEAD, PART_HOOF_FL, PART_HOOF_FR, PART_HOOF_HL, PART_HOOF_HR, PART_TAIL, PART_FUR, PART_JAW = range(11)
rnd = random.Random(1103)
EYE_NODES = []
EYES = []   # eye centres, so fur keeps off them and never samples their red


# ----------------------------------------------------------------------------- geometry
def catmull(points, per):
    pts = [np.array(p, float) for p in points]
    pts = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1:i + 3]
        for k in range(per):
            t = k / per
            out.append(.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-2])
    return out


def part(name, verts, faces, mat, part_id):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    K.link(o)
    if mat: me.materials.append(mat)
    tag(o, part_id)
    return o


def tag(o, part_id):
    a = o.data.attributes.get('qa_part') or o.data.attributes.new('qa_part', 'FLOAT', 'POINT')
    a.data.foreach_set('value', [float(part_id)] * len(o.data.vertices))


def loft_y(name, sections, mat, per=5, segs=56, power=2.5):
    """Body along -Y: sections are (y, zc, half width, up, down)."""
    rings = catmull(sections, per)
    verts, faces = [], []
    for r in rings:
        y, zc, w, up, dn = r
        for i in range(segs):
            a = math.tau * i / segs
            ca, sa = math.cos(a), math.sin(a)
            # A superellipse: square shoulders, a flatter back than a plain ellipse.
            x = w * math.copysign(abs(ca) ** (2 / power), ca)
            z = (up if sa > 0 else dn) * math.copysign(abs(sa) ** (2 / power), sa)
            verts.append((x, y, zc + z))
    n = len(rings)
    for k in range(n - 1):
        for i in range(segs):
            j = (i + 1) % segs
            faces.append((k * segs + i, k * segs + j, (k + 1) * segs + j, (k + 1) * segs + i))
    a0 = len(verts); verts.append((0, rings[0][0], rings[0][1]))
    a1 = len(verts); verts.append((0, rings[-1][0], rings[-1][1]))
    for i in range(segs):
        j = (i + 1) % segs
        faces.append((a0, j, i))
        faces.append((a1, (n - 1) * segs + i, (n - 1) * segs + j))
    return part(name, verts, faces, mat, PART_BODY)


def loft_path(name, nodes, mat, part_id=PART_BODY, per=5, segs=18):
    """A round limb through (x, y, z, r) nodes, capped at both ends."""
    rings = catmull(nodes, per)
    verts, faces = [], []
    frames = []
    for i, r in enumerate(rings):
        a = rings[max(0, i - 1)][:3]; b = rings[min(len(rings) - 1, i + 1)][:3]
        t = Vector(b - a).normalized()
        side = t.cross(Vector((0, 1, 0)))
        if side.length < 1e-3: side = t.cross(Vector((1, 0, 0)))
        side.normalize()
        frames.append((Vector(r[:3]), side, t.cross(side).normalized(), r[3]))
    for c, u, v, rad in frames:
        for i in range(segs):
            a = math.tau * i / segs
            verts.append(c + (u * math.cos(a) + v * math.sin(a)) * rad)
    n = len(frames)
    for k in range(n - 1):
        for i in range(segs):
            j = (i + 1) % segs
            faces.append((k * segs + i, k * segs + j, (k + 1) * segs + j, (k + 1) * segs + i))
    a0 = len(verts); verts.append(frames[0][0] - frames[0][1].cross(frames[0][2]) * 0)
    a1 = len(verts); verts.append(frames[-1][0])
    for i in range(segs):
        j = (i + 1) % segs
        faces.append((a0, j, i))
        faces.append((a1, (n - 1) * segs + i, (n - 1) * segs + j))
    o = part(name, verts, faces, mat, part_id)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def blob(name, centre, radii, mat, rot=(0, 0, 0), part_id=PART_BODY, subd=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subd, radius=1.0)
    m = Matrix.Translation(centre) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*radii, 1))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); K.link(o)
    if mat: me.materials.append(mat)
    tag(o, part_id)
    return o


def join(objs, name):
    K.select_only(objs, objs[0])
    bpy.ops.object.join()
    g = bpy.context.view_layer.objects.active
    g.name = name; g.data.name = name
    return g


def coords_of(o):
    a = np.zeros(len(o.data.vertices) * 3, np.float64)
    o.data.vertices.foreach_get('co', a)
    return a.reshape(-1, 3)


def set_coords(o, a):
    o.data.vertices.foreach_set('co', a.ravel().astype(np.float32))
    o.data.update()


def normals_of(o):
    o.data.update()
    a = np.zeros(len(o.data.vertices) * 3, np.float32)
    o.data.vertex_normals.foreach_get('vector', a)
    return a.reshape(-1, 3)


def seg_dist(p, a, b):
    """Distance from points p (N,3) to the segment a-b."""
    a, b = np.array(a, float), np.array(b, float)
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def dent(p, n, a, b, radius, depth):
    """Pushes the skin along its normals around the segment a-b. Positive depth digs in."""
    d = seg_dist(p, a, b)
    k = np.clip(1 - d / radius, 0, 1)
    k = k * k * (3 - 2 * k)
    return p - n * (k * depth)[:, None]


# ----------------------------------------------------------------------------- materials
def m_fur():
    m, nt, b = K.new_mat('BoarFur')
    P = world_pos(nt); x, y, z = sep(nt, P)
    ax = math_(nt, 'ABSOLUTE', x)
    # Fur runs back along the body and down the legs: stretched noise, plus large soft patches for the painted look.
    mp = N(nt, 'ShaderNodeMapping'); L(nt, P, mp.inputs['Vector']); mp.inputs['Scale'].default_value = (70, 11, 46)
    streak = noise(nt, mp.outputs['Vector'], 1.0, 4.0, .6)
    big = noise(nt, P, 5.5, 3.0, .5)
    mid = noise(nt, P, 17.0, 3.0, .55)
    base = mix(nt, smooth(nt, streak, .34, .68), (.105, .052, .024), (.26, .133, .058))
    base = mix(nt, math_(nt, 'MULTIPLY', smooth(nt, big, .36, .66), .4), base, (.34, .19, .082))
    # Dark along the spine, paler and greyer towards the belly.
    spine = math_(nt, 'MULTIPLY', smooth(nt, math_(nt, 'SUBTRACT', .13, ax), 0, .11), smooth(nt, z, .62, .78))
    base = mix(nt, math_(nt, 'MULTIPLY', spine, .78), base, (.05, .03, .022))
    belly = math_(nt, 'MULTIPLY', smooth(nt, z, .46, .32), smooth(nt, y, -.5, -.35))
    base = mix(nt, math_(nt, 'MULTIPLY', belly, .4), base, (.40, .29, .18))
    # Lower legs: dark hair under caked mud in lumps, drier at the edges.
    legs = smooth(nt, z, .37, .2)
    base = mix(nt, legs, base, (.085, .053, .034))
    lump = voronoi(nt, P, 34.0)
    mud_mask = math_(nt, 'MULTIPLY', smooth(nt, z, .34, .16), smooth(nt, math_(nt, 'ADD', noise(nt, P, 13.0, 3.0, .6), math_(nt, 'MULTIPLY', lump, .3)), .55, .72))
    base = mix(nt, mud_mask, base, (.30, .205, .105))
    # The head: grey-brown speckle, bare skin on the snout, a dark wet nose.
    head = smooth(nt, y, -.5, -.62)
    face = mix(nt, smooth(nt, mid, .4, .62), (.085, .052, .03), (.205, .13, .074))
    base = mix(nt, math_(nt, 'MULTIPLY', head, .9), base, face)
    snout = smooth(nt, y, -.72, -.76)
    base = mix(nt, snout, base, (.10, .06, .046))
    nose = smooth(nt, y, -.778, -.79)
    base = mix(nt, nose, base, (.075, .045, .05))
    # The skin round the eyes is dark and bare, as on a real boar, so the eye sits in a shadow rather than a pale patch.
    eye_at = N(nt, 'ShaderNodeCombineXYZ'); EYE_NODES.append(eye_at)
    abs_p = N(nt, 'ShaderNodeCombineXYZ'); L(nt, ax, abs_p.inputs[0]); L(nt, y, abs_p.inputs[1]); L(nt, z, abs_p.inputs[2])
    eye_d = N(nt, 'ShaderNodeVectorMath', operation='DISTANCE'); L(nt, abs_p.outputs[0], eye_d.inputs[0]); L(nt, eye_at.outputs[0], eye_d.inputs[1])
    eye_rim = smooth(nt, eye_d.outputs['Value'], .05, .018)
    # A dark lip line and creases on the bare snout; pores in the nose leather.
    lip = math_(nt, 'MULTIPLY', smooth(nt, z, .385, .372), smooth(nt, y, -.62, -.68))
    base = mix(nt, math_(nt, 'MULTIPLY', lip, .7), base, (.05, .03, .028))
    # Worn lighter on the brow and cheeks.
    brow = math_(nt, 'MULTIPLY', head, math_(nt, 'MULTIPLY', smooth(nt, z, .55, .62), .08))
    base = mix(nt, brow, base, (.27, .19, .115))
    base = mix(nt, math_(nt, 'MULTIPLY', eye_rim, .85), base, (.045, .028, .022))

    # Mask R: ink-like dark qi, branching across the shoulder and haunch and along the spine.
    w1 = noise(nt, P, 7.0, 4.0, .55); w2 = noise(nt, P, 21.0, 3.0, .5)
    warp = N(nt, 'ShaderNodeCombineXYZ'); L(nt, math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', w1, .5), .22), warp.inputs[0]); L(nt, math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', w2, .5), .16), warp.inputs[1]); L(nt, math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', w1, .5), .3), warp.inputs[2])
    add = N(nt, 'ShaderNodeVectorMath', operation='ADD'); L(nt, P, add.inputs[0]); L(nt, warp.outputs[0], add.inputs[1])
    Q = add.outputs[0]
    # Ridged noise stretched along the coat: long branching strands running with the fur, not cells.
    flow_map = N(nt, 'ShaderNodeMapping'); L(nt, Q, flow_map.inputs['Vector']); flow_map.inputs['Scale'].default_value = (1.0, .42, .85)
    def ridge(scale, lo, hi):
        n = noise(nt, flow_map.outputs['Vector'], scale, 3.0, .45)
        r = math_(nt, 'SUBTRACT', 1.0, math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', n, 2.0), 1.0)))
        return smooth(nt, r, lo, hi)
    v1 = ridge(4.6, .955, .995); v2 = math_(nt, 'MULTIPLY', ridge(10.5, .965, .995), .75)
    def blobm(cx, cy, cz, r):
        c = N(nt, 'ShaderNodeCombineXYZ'); c.inputs[0].default_value = cx; c.inputs[1].default_value = cy; c.inputs[2].default_value = cz
        absv = N(nt, 'ShaderNodeCombineXYZ'); L(nt, ax, absv.inputs[0]); L(nt, y, absv.inputs[1]); L(nt, z, absv.inputs[2])
        d = N(nt, 'ShaderNodeVectorMath', operation='DISTANCE'); L(nt, absv.outputs[0], d.inputs[0]); L(nt, c.outputs[0], d.inputs[1])
        return smooth(nt, d.outputs['Value'], r, r * .45)
    region = math_(nt, 'MAXIMUM', blobm(.27, -.2, .58, .46), blobm(.25, .4, .56, .44))
    region = math_(nt, 'MAXIMUM', region, blobm(.1, -.38, .68, .3))
    region = math_(nt, 'MAXIMUM', region, blobm(.1, -.56, .5, .13))    # reaching onto the cheek
    region = math_(nt, 'MAXIMUM', region, spine)
    region = math_(nt, 'MULTIPLY', region, smooth(nt, z, .22, .32))
    halo = math_(nt, 'MULTIPLY', ridge(4.6, .87, .97), .17)   # the ink's bleed around the main strands
    veins = math_(nt, 'MAXIMUM', math_(nt, 'MAXIMUM', v1, v2), halo)
    r_ = math_(nt, 'MULTIPLY', veins, region)
    # Bristles stain first: the spine strip always carries a little.
    r_ = math_(nt, 'MAXIMUM', r_, math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', spine, mixf(nt, smooth(nt, mid, .35, .6), .55, 1.0)), .95))
    cm = N(nt, 'ShaderNodeCombineColor'); L(nt, r_, cm.inputs[0])
    rough = mixf(nt, nose, mixf(nt, mud_mask, .84, .92), .32)
    height = math_(nt, 'ADD', math_(nt, 'MULTIPLY', streak, .7), math_(nt, 'MULTIPLY', mud_mask, .6))
    pores = noise(nt, P, 240.0, 2.0, .5)
    height = math_(nt, 'ADD', height, math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', pores, snout), .55))
    return K.finish(m, nt, b, base, rough, height=height, bump=.004, bump_strength=.75, mask=cm.outputs[0])


def m_plain(name, c1, c2, rough, scale=40.0, mask=None):
    m, nt, b = K.new_mat(name)
    P = world_pos(nt)
    n = noise(nt, P, scale, 3.0, .55)
    return K.finish(m, nt, b, mix(nt, smooth(nt, n, .36, .66), c1, c2), rough, mask=mask)


def m_eye():
    m, nt, b = K.new_mat('BoarEye')
    rgb = N(nt, 'ShaderNodeRGB'); rgb.outputs[0].default_value = (0, 1, 0, 1)
    return K.finish(m, nt, b, (.028, .016, .011), .16, mask=rgb.outputs[0])


def m_ear():
    m, nt, b = K.new_mat('BoarEar')
    P = world_pos(nt)
    inner = N(nt, 'ShaderNodeAttribute', attribute_name='qa_inner', attribute_type='GEOMETRY').outputs['Fac']
    outer = mix(nt, smooth(nt, noise(nt, P, 70.0, 3.0, .6), .35, .65), (.07, .04, .022), (.2, .115, .056))
    hair = mix(nt, smooth(nt, noise(nt, P, 60.0, 3.0, .6), .3, .7), (.06, .03, .024), (.15, .068, .05))
    return K.finish(m, nt, b, mix(nt, inner, outer, hair), .8)


# ----------------------------------------------------------------------------- the body
def build_skin(fur):
    # Front-heavy like a real boar: deep chest and high shoulder, then the back falls and the belly tucks up to a narrow rump.
    y_sections = [
        (.735, .615, .045, .045, .055),
        (.70, .60, .118, .09, .12),
        (.62, .585, .188, .155, .2),
        (.46, .575, .222, .185, .225),
        (.26, .58, .238, .21, .245),
        (.06, .585, .25, .25, .27),
        (-.12, .59, .258, .285, .29),
        (-.26, .585, .248, .275, .29),
        (-.38, .57, .22, .24, .265),
        (-.48, .545, .18, .2, .235),
        (-.57, .505, .146, .165, .185),
        (-.64, .455, .106, .115, .125),
        (-.70, .415, .07, .07, .08),
        (-.75, .395, .052, .048, .054),
        (-.785, .39, .043, .04, .043),
        (-.80, .39, .032, .03, .032),
    ]
    parts = [loft_y('Torso', y_sections, fur)]
    for side in (1, -1):
        s = side
        parts += [
            loft_path(f'FrontLeg{s}', [(s * .15, -.21, .58, .10), (s * .155, -.165, .38, .08), (s * .146, -.195, .25, .044), (s * .14, -.213, .15, .029), (s * .14, -.215, .095, .027), (s * .14, -.222, .05, .036), (s * .14, -.224, .03, .036)], fur),
            loft_path(f'HindLeg{s}', [(s * .14, .46, .59, .11), (s * .145, .41, .44, .095), (s * .145, .46, .33, .06), (s * .15, .54, .215, .033), (s * .15, .525, .13, .028), (s * .15, .516, .07, .028), (s * .15, .51, .03, .036)], fur),
            blob(f'ShoulderMass{s}', (s * .175, -.2, .62), (.08, .17, .2), fur),
            blob(f'HaunchMass{s}', (s * .15, .44, .59), (.075, .16, .16), fur),
            blob(f'Cheek{s}', (s * .085, -.585, .455), (.062, .082, .075), fur, rot=(.3, 0, 0)),
            blob(f'Brow{s}', (s * .082, -.595, .588), (.05, .066, .022), fur, rot=(.5, s * -.2, 0)),
            blob(f'Lip{s}', (s * .046, -.715, .372), (.03, .07, .024), fur, rot=(.12, 0, 0)),
        ]
    parts += [
        blob('Hump', (0, -.16, .79), (.14, .22, .09), fur),
        blob('NeckCrest', (0, -.42, .735), (.09, .15, .06), fur, rot=(.32, 0, 0)),
        blob('Jowl', (0, -.56, .385), (.095, .13, .055), fur, rot=(-.12, 0, 0)),
        blob('Brisket', (0, -.33, .33), (.115, .14, .06), fur),
        blob('NoseDisc', (0, -.788, .39), (.039, .013, .035), fur),
    ]
    skin = join(parts, 'Skin')
    K.select_only([skin], skin)
    r = skin.modifiers.new('Remesh', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = .0078; r.use_smooth_shade = True
    K.apply_mods(skin)
    bm = bmesh.new(); bm.from_mesh(skin.data)
    for _ in range(2): bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(skin.data); bm.free()

    # Sculpt: creases, sockets, nostrils, ribs and a shaggy, muddy surface.
    p = coords_of(skin); n = normals_of(skin)
    for s in (1, -1):
        p = dent(p, n, (s * .05, -.79, .372), (s * .082, -.655, .395), .014, .012)        # mouth line
        p = dent(p, n, (s * .076, -.63, .545), (s * .122, -.565, .545), .03, .017)        # eye socket, long towards the temple
        p = dent(p, n, (s * .05, -.685, .44), (s * .095, -.61, .47), .014, .006)          # the crease from snout to cheek
        p = dent(p, n, (s * .1, -.565, .49), (s * .118, -.49, .44), .018, .007)           # under the eye, down the jowl
        for y_ in (-.75, -.72, -.69):
            p = dent(p, n, (s * .012, y_, .432 - (y_ + .75) * .25), (s * .05, y_ + .006, .41 - (y_ + .75) * .2), .007, .0034)   # snout folds, side
        p = dent(p, n, (s * .037, -.79, .39), (s * .037, -.79, .39), .012, .007)          # the nose disc's rim
        p = dent(p, n, (s * .019, -.803, .392), (s * .019, -.803, .392), .012, .016)      # nostril
        p = dent(p, n, (s * .155, -.05, .40), (s * .15, -.09, .72), .10, .009)            # behind the shoulder
        p = dent(p, n, (s * .175, .27, .40), (s * .17, .24, .72), .09, .008)              # before the haunch
        p = dent(p, n, (s * .13, -.47, .69), (s * .13, -.47, .69), .045, .008)            # ear root
    for y_ in (-.745, -.718, -.692, -.665):
        p = dent(p, n, (-.055, y_, .44 + (y_ + .745) * .3), (.055, y_ - .004, .44 + (y_ + .745) * .3), .008, .0045)   # snout wrinkles
    p = dent(p, n, (0, -.8, .425), (0, -.8, .425), .009, .004)                        # the groove above the nose
    n = n * 1.0
    shag = np.zeros(len(p))
    for i, co in enumerate(p):
        c = Vector(co)
        v = mnoise.noise(Vector((c.x * 22, c.y * 7, c.z * 16))) * .0075 + mnoise.noise(c * 55) * .0022
        if co[2] < .3:
            v += (mnoise.noise(c * 42) * .011 + mnoise.noise(c * 90) * .004) * min(1, (.3 - co[2]) / .09) * (co[2] > .045)
        if co[1] < -.68: v *= .22
        shag[i] = v
    p = p + n * shag[:, None]
    p[:, 2] = np.maximum(p[:, 2], 0)
    set_coords(skin, p)

    d = skin.modifiers.new('Decimate', 'DECIMATE'); d.ratio = 36000 / K.tri_count(skin); d.use_collapse_triangulate = True
    K.apply_mods(skin)
    tag(skin, PART_BODY)
    for poly in skin.data.polygons: poly.use_smooth = True
    return skin


def surface_point(bvh, origin, target):
    origin, target = Vector(origin), Vector(target)
    hit, normal, _, _ = bvh.ray_cast(origin, (target - origin).normalized())
    return hit, normal


def build_ear(side, part_id, torn, mat):
    """A cupped leaf with thickness; one is torn at the rim."""
    H, W = .178, .086
    rows, cols = 9, 7
    front, back = [], []
    for i in range(rows):
        t = i / (rows - 1)
        half = W * min(1, .62 + t * 2.2) * (1 - t) ** .62 + .0015
        for j in range(cols):
            u = j / (cols - 1) * 2 - 1
            x = u * half
            bite = 1.0
            if torn and .46 < t < .74 and u > .1:
                bite = 1 - .55 * math.sin((t - .46) / .28 * math.pi) * (u - .1) / .9
                x *= bite
            cup = (1 - u * u) * .022 * math.sin(math.pi * t)
            z = t * H
            front.append(Vector((x, -cup, z)))
            back.append(Vector((x, -cup + .007 * (1 - t * .6), z)))
    verts = front + back
    faces = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            a, b, c, e = i * cols + j, i * cols + j + 1, (i + 1) * cols + j + 1, (i + 1) * cols + j
            faces.append((a, e, c, b))
            o = rows * cols
            faces.append((o + a, o + b, o + c, o + e))
    o_ = rows * cols
    for i in range(rows - 1):
        l1, l2 = i * cols, (i + 1) * cols
        faces.append((l1, o_ + l1, o_ + l2, l2))
        r1, r2 = l1 + cols - 1, l2 + cols - 1
        faces.append((r1, r2, o_ + r2, o_ + r1))
    for j in range(cols - 1):
        t1, t2 = (rows - 1) * cols + j, (rows - 1) * cols + j + 1
        faces.append((t1, o_ + t1, o_ + t2, t2))
        faces.append((j, j + 1, o_ + j + 1, o_ + j))
    ob = part(f'Ear{side}', verts, faces, mat, part_id)
    a = ob.data.attributes.new('qa_inner', 'FLOAT', 'POINT')
    a.data.foreach_set('value', [1.0] * (rows * cols) + [0.0] * (rows * cols))
    # Stands up and out from the crest, opening forward and to the side.
    rot = Euler((.1, side * .42, side * -.5)).to_matrix().to_4x4()
    ob.data.transform(Matrix.Translation((side * .112, -.468, .695)) @ rot)
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    for poly in ob.data.polygons: poly.use_smooth = True
    return ob


def build_details(bvh, ivory, hoof, deco, needle):
    parts = []
    eye = m_eye()
    for side, (x, ear_id, hooves) in ((1, (.14, PART_EAR_L, (PART_HOOF_FL, PART_HOOF_HL))), (-1, (.14, PART_EAR_R, (PART_HOOF_FR, PART_HOOF_HR)))):
        # Eyes sit in the sockets the sculpt left, found by ray so they stay on the skin.
        hit, nrm = surface_point(bvh, (side * .3, -.655, .595), (side * .05, -.57, .535))
        centre = hit - nrm * .002
        EYES.append(centre.copy())
        parts.append(blob(f'Eye{side}', centre, (.0145, .0145, .0145), eye, part_id=PART_HEAD, subd=3))
        parts.append(blob(f'Lid{side}', centre + Vector((0, 0, .012)) + nrm * .004, (.018, .017, .0075), None, rot=(.2, side * -.25, 0), part_id=PART_HEAD))
        parts[-1].data.materials.append(bpy.data.materials['BoarFur'])
        # Short curved tusks from the upper lip, tips turning out and up.
        t = [(side * .054, -.70, .372, .0135), (side * .068, -.71, .405, .0115), (side * .08, -.715, .44, .008), (side * .086, -.706, .468, .0035), (side * .087, -.702, .474, .0012)]
        parts.append(loft_path(f'Tusk{side}', t, ivory, PART_HEAD, per=4, segs=12))
        for (fx, fy), pid in zip(((side * .14, -.232), (side * .15, .505)), hooves):
            for toe in (1, -1):
                bm_o = blob(f'Hoof{side}{toe}{pid}', (fx + toe * .02, fy - .008, .026), (.0195, .04, .032), hoof, rot=(.3, 0, 0), part_id=pid)
                c = coords_of(bm_o); c[:, 2] = np.maximum(c[:, 2], 0); set_coords(bm_o, c)
                parts.append(bm_o)
    parts += [build_ear(1, PART_EAR_L, False, bpy.data.materials['BoarEar']), build_ear(-1, PART_EAR_R, True, bpy.data.materials['BoarEar'])]
    # The tail hangs from the rump; its long hair is added with the fur.
    parts.append(loft_path('Tail', [(0, .695, .665, .03), (0, .735, .61, .024), (.004, .75, .53, .018), (-.004, .752, .45, .012), (0, .75, .39, .007)], bpy.data.materials['BoarFur'], PART_TAIL, per=4, segs=10))
    # Burrs and pine needles caught in the fur (three-view: on the shoulder, the flank, the haunch).
    for i, (x, y, z) in enumerate([(.27, -.15, .70), (-.27, -.05, .62), (.26, .28, .74), (-.24, .44, .70), (.2, -.32, .78)]):
        hit, nrm = surface_point(bvh, (math.copysign(.6, x), y, z + .1), (0, y, z - .05))
        if hit is None: continue
        b = burr(f'Burr{i}', hit + nrm * .012, deco)
        parts.append(b)
    for i in range(26):
        y = rnd.uniform(-.4, .52); s = rnd.choice((1, -1)); z = rnd.uniform(.62, .84)
        hit, nrm = surface_point(bvh, (s * .6, y, z + .25), (0, y, z - .12))
        if hit is None: continue
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-.4, .4))).normalized()
        d = (d - nrm * d.dot(nrm)).normalized()
        a, m_, e = hit + nrm * .006, hit + nrm * .012 + d * .035, hit + nrm * .006 + d * .07
        parts.append(loft_path(f'Needle{i}', [(*a, .0016), (*m_, .0014), (*e, .0006)], needle, PART_FUR, per=2, segs=4))
    return parts


def burr(name, centre, mat):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=.013)
    for f in list(bm.faces):
        c = f.calc_center_median(); r = bmesh.ops.poke(bm, faces=[f])
        r['verts'][0].co = c * 1.9
    bmesh.ops.translate(bm, vec=centre, verts=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); K.link(o); me.materials.append(mat)
    tag(o, PART_FUR)
    return o


# ----------------------------------------------------------------------------- fur
def blade_mesh(name, roots, segments):
    """Tapered three-sided blades. roots: (root, direction, length, width, droop, tint)."""
    verts, faces, shade = [], [], []
    for root, d, length, width, droop, tint in roots:
        d = Vector(d).normalized()
        u = d.cross(Vector((0, 0, 1)))
        if u.length < 1e-3: u = Vector((1, 0, 0))
        u.normalize(); v = d.cross(u)
        base = len(verts)
        for s in range(segments):
            t = s / segments
            c = Vector(root) + d * (length * t) + Vector((0, 0, -droop)) * (t * t)
            w = width * (1 - t * .78)
            for a in (0, 2.094, 4.189):
                verts.append(c + (u * math.cos(a) + v * math.sin(a) * .6) * w)
                shade.append((*[min(1, tint[i] * (.62 + .46 * t)) for i in range(3)], 1))
        verts.append(Vector(root) + d * length + Vector((0, 0, -droop)))
        shade.append((min(1, tint[0] * 1.25), min(1, tint[1] * 1.12), min(1, tint[2] * .95), 1))
        for s in range(segments - 1):
            for k in range(3):
                j = (k + 1) % 3
                a, b = base + s * 3 + k, base + s * 3 + j
                faces.append((a, b, b + 3, a + 3))
        tip = base + segments * 3
        top = base + (segments - 1) * 3
        for k in range(3):
            faces.append((top + k, top + (k + 1) % 3, tip))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(name, me); K.link(o)
    for p in me.polygons: p.use_smooth = True
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT')
    col.data.foreach_set('color', np.array([min(1, c) for rgba in shade for c in rgba], np.float32))
    return o


TUFT_CELLS = 3


def make_tuft_map(path):
    """The fur tufts' alpha: three cells of tapering strands fanning from a root at the bottom centre to the top edge, and
    an opaque last column for everything that is not a tuft. R shades each strand, A cuts it out."""
    S = 1024
    cell = S // 4
    tone, alpha = np.zeros((S, S), np.float32), np.zeros((S, S), np.float32)
    r = random.Random(4)
    for c in range(TUFT_CELLS):
        for _ in range(64):
            start_x = c * cell + cell / 2 + r.uniform(-.06, .06) * cell
            spread = r.uniform(-1, 1)
            end_x = c * cell + cell / 2 + spread * cell * .41
            end_y = r.uniform(.62, .985) * S
            bend = r.uniform(-.1, .1) * cell
            thick = r.uniform(5.5, 10.5)
            shade = r.uniform(.68, 1.0)
            for k in range(420):
                t = k / 419
                x = start_x + (end_x - start_x) * t + bend * math.sin(t * math.pi)
                y = t * end_y
                # Widest low down, then a long taper to a point: reads as hair, not a leaf.
                rad = thick * min(1, .55 + t * 3) * (1 - t) ** .7 + .7
                x0, x1 = int(max(c * cell + 2, x - rad - 1)), int(min((c + 1) * cell - 2, x + rad + 2))
                y0, y1 = int(max(0, y - rad - 1)), int(min(S, y + rad + 2))
                if x1 <= x0 or y1 <= y0: continue
                yy, xx = np.mgrid[y0:y1, x0:x1]
                d = np.hypot(xx - x, yy - y)
                a = np.clip(rad + .5 - d, 0, 1)
                region = alpha[y0:y1, x0:x1]
                take = a > region
                tone[y0:y1, x0:x1][take] = shade * (.82 + .18 * t)
                alpha[y0:y1, x0:x1] = np.maximum(region, a)
    alpha[:, cell * TUFT_CELLS:] = 1
    tone[:, cell * TUFT_CELLS:] = 1
    # Colour bleeds past the strands so mip levels do not pick up black fringes.
    rgb = np.where(alpha > 0, tone, .85)
    return K._np_img('T_Fur', np.dstack([rgb, rgb, rgb, alpha]), 'Non-Color', path)


def card_mesh(name, cards, seed=3):
    """Fans of hair on the skin: a root and four outline corners, three triangles, cut out by the tuft map through the second UV.
    Lit with the skin's normal, so the coat reads as one soft mass."""
    r = random.Random(seed)
    verts, faces, shade, skin_normals, uv2 = [], [], [], [], []
    corners = ((.5, 0), (0, .5), (.19, 1), (.81, 1), (1, .5))
    for root, d, n, length, width, tint in cards:
        side = d.cross(n).normalized() * width * .5
        lift = n * length * .13
        base = len(verts)
        cell = r.randrange(TUFT_CELLS)
        verts += [root, root + d * length * .5 - side + lift, root + d * length - side * .62 + lift * .6, root + d * length + side * .62 + lift * .6, root + d * length * .5 + side + lift]
        skin_normals += [n] * 5
        dark = (tint[0] * .62, tint[1] * .6, tint[2] * .58, 1)
        mid = (tint[0] * .86, tint[1] * .84, tint[2] * .8, 1)
        tip = (min(1, tint[0] * 1.1), min(1, tint[1] * 1.0), min(1, tint[2] * .86), 1)
        shade += [dark, mid, tip, tip, mid]
        uv2 += [((cell + u) / 4, v) for u, v in corners]
        a, b_, c, e, f = range(base, base + 5)
        if (Vector(verts[b_]) - Vector(verts[a])).cross(Vector(verts[c]) - Vector(verts[a])).dot(n) > 0: faces += [(a, b_, c), (a, c, e), (a, e, f)]
        else: faces += [(a, c, b_), (a, e, c), (a, f, e)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(name, me); K.link(o)
    for p in me.polygons: p.use_smooth = True
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT')
    col.data.foreach_set('color', np.array([min(1, c) for rgba in shade for c in rgba], np.float32))
    set_uv2(me, np.array(uv2, np.float32))
    me.normals_split_custom_set_from_vertices([tuple(n) for n in skin_normals])
    return o


OPAQUE_UV2 = (.875, .5)


def set_uv2(me, per_vertex=None):
    """UV2 reads the tuft map. Anything that is not a tuft sits in the map's opaque column."""
    layer = me.uv_layers.get('UV2') or me.uv_layers.new(name='UV2', do_init=False)
    if per_vertex is None:
        layer.data.foreach_set('uv', np.tile(np.array(OPAQUE_UV2, np.float32), len(me.loops)))
        return
    loop_v = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', loop_v)
    layer.data.foreach_set('uv', per_vertex[loop_v].ravel())


def coat_cards(body, count, size_k=1.0, seed=5):
    """Shingled tufts over the whole skin, following the coat."""
    me = body.data; me.calc_loop_triangles()
    r = random.Random(seed)
    tris = me.loop_triangles; v = me.vertices
    part_attr = me.attributes['qa_part'].data
    weights = []
    for t in tris:
        if part_attr[t.vertices[0]].value > .5: weights.append(0.0); continue
        c = (v[t.vertices[0]].co + v[t.vertices[1]].co + v[t.vertices[2]].co) / 3
        near_eye = any((c - e).length < .03 for e in EYES)
        weights.append(0.0 if c.y < -.74 or c.z < .05 or near_eye else t.area * (4.0 if c.y < -.5 else 1))
    out = []
    for i in r.choices(range(len(tris)), weights=weights, k=count):
        t = tris[i]
        a, b = r.random(), r.random()
        if a + b > 1: a, b = 1 - a, 1 - b
        p = v[t.vertices[0]].co * a + v[t.vertices[1]].co * b + v[t.vertices[2]].co * (1 - a - b)
        n = t.normal.copy()
        flow = Vector((0, 1, -.5))
        length = .082
        if p.z < .36: flow = Vector((math.copysign(.12, p.x), .18, -1)); length = .068
        if p.z < .2: length = .05
        if p.y < -.48 and p.z > .5: flow = Vector((math.copysign(.3, p.x), .9, .05)); length = .058
        if p.y < -.56: length = .032
        if p.y < -.66: length = .02
        flow = flow - n * flow.dot(n)
        if flow.length < 1e-3: continue
        d = (flow.normalized() + Vector((r.uniform(-.28, .28), r.uniform(-.28, .28), r.uniform(-.28, .28)))).normalized()
        d = (d - n * d.dot(n)).normalized()
        g = r.uniform(.82, 1.0)
        out.append((p + n * .0015, d, n, length * r.uniform(.85, 1.25) * size_k, length * r.uniform(.5, .72) * size_k, (g, g * r.uniform(.96, 1.0), g * r.uniform(.9, 1.0))))
    return out


def fur_roots(body, count, length_k=1.0, width_k=1.0, seed=7):
    """Area-weighted sample of the body skin, thinned where the head is bare and the legs short, with the flow of the coat."""
    me = body.data; me.calc_loop_triangles()
    r = random.Random(seed)
    tris = me.loop_triangles
    v = me.vertices
    part_attr = me.attributes['qa_part'].data
    areas = []
    for t in tris:
        if part_attr[t.vertices[0]].value > .5: areas.append(0.0); continue
        c = (v[t.vertices[0]].co + v[t.vertices[1]].co + v[t.vertices[2]].co) / 3
        k = 1.0
        if c.y < -.62 or c.z < .05 or any((c - e).length < .05 for e in EYES): k = 0
        elif c.z > .4 and not (-.62 < c.y < -.44): k = .06            # keep spikes to the belly, the ruff and the legs' backs
        areas.append(t.area * k)
    picks = r.choices(range(len(tris)), weights=areas, k=count)
    out = []
    for i in picks:
        t = tris[i]
        a, b = r.random(), r.random()
        if a + b > 1: a, b = 1 - a, 1 - b
        p = v[t.vertices[0]].co * a + v[t.vertices[1]].co * b + v[t.vertices[2]].co * (1 - a - b)
        n = t.normal
        length = .058
        if p.z < .34 and p.y > -.35 and p.y < .35: length = .072          # the belly fringe
        elif p.z < .22: length = .03                                     # the legs
        elif p.z < .34: length = .05
        if -.62 < p.y < -.44 and p.z < .56: length = .092                # the cheek ruff
        if p.y < -.6: length = .03
        flow = Vector((0, 1, -.55))
        if p.z < .36: flow = Vector((math.copysign(.15, p.x), .22, -1))
        if p.y < -.5 and p.z > .5: flow = Vector((math.copysign(.25, p.x), .9, .1))
        flow = flow - n * flow.dot(n)
        d = (flow.normalized() + n * r.uniform(.12, .28) + Vector((r.uniform(-.2, .2), r.uniform(-.2, .2), r.uniform(-.2, .2)))).normalized()
        g = r.uniform(.84, 1.12)
        out.append((p - n * .004, d, length * r.uniform(.72, 1.25) * length_k, r.uniform(.011, .017) * width_k, length * .16, (g, g * r.uniform(.96, 1.02), g * r.uniform(.9, 1.0))))
    return out


def bristle_roots(count, length_k, width_k, bvh, seed=9):
    """The ridge along the spine: tallest over the shoulder and neck, as in the three-view."""
    r = random.Random(seed)
    out = []
    for _ in range(count):
        y = r.uniform(-.56, .62)
        x = r.gauss(0, .03)
        hit, nrm = surface_point(bvh, (x, y, 1.4), (x, y, 0))
        if hit is None: continue
        crest = math.exp(-((y + .2) / .36) ** 2)
        length = (.05 + .078 * crest) * r.uniform(.72, 1.1) * length_k
        lean = Vector((x * 2.4, .85 - .1 * crest, 1.05)).normalized()
        d = (lean + Vector((r.uniform(-.14, .14), r.uniform(-.2, .2), r.uniform(-.1, .1)))).normalized()
        g = r.uniform(.72, 1.05)
        out.append((hit - nrm * .006, d, length, r.uniform(.015, .022) * width_k, length * .12, (g, g * .9, g * .72)))
    return out


def tail_roots(count, length_k, width_k, seed=11):
    r = random.Random(seed)
    out = []
    for _ in range(count):
        t = r.random()
        z = .56 - t * .19
        p = Vector((r.gauss(0, .006), .745 + r.gauss(0, .004), z))
        d = Vector((r.gauss(0, .16), r.gauss(.02, .08), -1)).normalized()
        g = r.uniform(.5, .95)
        out.append((p, d, r.uniform(.08, .15) * length_k, r.uniform(.006, .009) * width_k, .012, (g * .8, g * .78, g * .85)))
    return out


def clip_height(roots, limit=.99):
    out = []
    for root, d, length, width, droop, tint in roots:
        v = Vector(d).normalized()
        if root[2] + v.z * length > limit: length = max(.02, (limit - root[2]) / max(v.z, .05))
        out.append((root, d, length, width, droop, tint))
    return out


def clip_width(roots, limit=.295):
    """Keeps blade tips inside the width limit by shortening the ones that would stick out."""
    kept = []
    for root, d, length, width, droop, tint in roots:
        x_end = root[0] + Vector(d).normalized().x * length
        if abs(x_end) > limit:
            room = limit - abs(root[0])
            if room < .012: continue
            length = room / max(abs(Vector(d).normalized().x), .05)
        kept.append((root, d, length, width, droop, tint))
    return kept


def attach_to_atlas(fur, body_bvh, body):
    part_of = body.data.attributes['qa_part'].data
    """Every blade samples the body atlas at its root, nudged so tangents stay valid. Needs no atlas space of its own."""
    me = fur.data
    uv = me.uv_layers.new(name='UVMap')
    bu = body.data.uv_layers['UVMap'].data
    body.data.calc_loop_triangles()
    tris = body.data.loop_triangles
    vs = body.data.vertices
    per_vertex = np.zeros(len(me.vertices) * 2, np.float32)
    groups = {}
    colv = me.vertices
    for poly in me.polygons:
        pass
    # Blades are vertex islands: walk them via edges.
    seen = np.zeros(len(me.vertices), bool)
    adj = [[] for _ in me.vertices]
    for e in me.edges:
        adj[e.vertices[0]].append(e.vertices[1]); adj[e.vertices[1]].append(e.vertices[0])
    for start in range(len(me.vertices)):
        if seen[start]: continue
        stack = [start]; island = []
        seen[start] = True
        while stack:
            i = stack.pop(); island.append(i)
            for j in adj[i]:
                if not seen[j]: seen[j] = True; stack.append(j)
        root = colv[island[0]].co
        loc, _, idx, _ = body_bvh.find_nearest(root)
        t = tris[idx]
        w = _bary(loc, vs[t.vertices[0]].co, vs[t.vertices[1]].co, vs[t.vertices[2]].co)
        u = bu[t.loops[0]].uv * w[0] + bu[t.loops[1]].uv * w[1] + bu[t.loops[2]].uv * w[2]
        for k, i in enumerate(island):
            uu = None
            if len(island) == 5:   # a card: each corner reads the skin under it, so the veins and streaks run on across the coat
                loc2, _, idx2, _ = body_bvh.find_nearest(colv[i].co)
                t2 = tris[idx2]
                w2 = _bary(loc2, vs[t2.vertices[0]].co, vs[t2.vertices[1]].co, vs[t2.vertices[2]].co)
                cand = bu[t2.loops[0]].uv * w2[0] + bu[t2.loops[1]].uv * w2[1] + bu[t2.loops[2]].uv * w2[2]
                if (cand - u).length < .06 and part_of[t2.vertices[0]].value < .5: uu = cand   # else it crosses a seam or leaves the skin: stay with the root
            if uu is None: uu = Vector((u.x + (k % 3) * 2e-4, u.y + ((k // 3) % 4) * 2e-4))
            per_vertex[i * 2] = uu.x
            per_vertex[i * 2 + 1] = uu.y
    loop_v = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', loop_v)
    uvs = per_vertex.reshape(-1, 2)[loop_v]
    uv.data.foreach_set('uv', uvs.ravel())


def _bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = max(d00 * d11 - d01 * d01, 1e-12)
    v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
    return (1 - v - w, v, w)


# ----------------------------------------------------------------------------- rig
BONES = [
    # name, head, tail, parent, roll target (the bone's local Z)
    ('Root', (0, 0, 0), (0, 0, .1), None, (0, 1, 0)),
    ('Pelvis', (0, .52, .62), (0, .30, .62), 'Root', (0, 0, 1)),
    ('Spine', (0, .30, .62), (0, .08, .62), 'Pelvis', (0, 0, 1)),
    ('Spine2', (0, .08, .62), (0, -.12, .62), 'Spine', (0, 0, 1)),
    ('Chest', (0, -.12, .62), (0, -.32, .62), 'Spine2', (0, 0, 1)),
    ('Neck', (0, -.32, .62), (0, -.43, .60), 'Chest', (0, 0, 1)),
    ('Neck2', (0, -.43, .60), (0, -.52, .57), 'Neck', (0, 0, 1)),
    ('Head', (0, -.52, .57), (0, -.76, .42), 'Neck2', (0, 0, 1)),
    ('Jaw', (0, -.56, .43), (0, -.77, .35), 'Head', (0, 0, 1)),
    ('Ear_L', (.112, -.468, .695), (.16, -.468, .835), 'Head', (0, -1, 0)),
    ('Ear_R', (-.112, -.468, .695), (-.16, -.468, .835), 'Head', (0, -1, 0)),
    ('Tail', (0, .695, .665), (0, .745, .54), 'Pelvis', (0, 1, 0)),
    ('Tail2', (0, .745, .54), (0, .75, .37), 'Tail', (0, 1, 0)),
]
for _s, _x in (('L', 1), ('R', -1)):
    BONES += [
        (f'FrontUpper_{_s}', (_x * .15, -.21, .54), (_x * .157, -.16, .33), 'Chest', (0, -1, 0)),
        (f'FrontLower_{_s}', (_x * .157, -.16, .33), (_x * .142, -.213, .13), f'FrontUpper_{_s}', (0, -1, 0)),
        (f'FrontPaw_{_s}', (_x * .142, -.213, .13), (_x * .14, -.24, .012), f'FrontLower_{_s}', (0, -1, 0)),
        (f'HindUpper_{_s}', (_x * .14, .46, .56), (_x * .145, .40, .36), 'Pelvis', (0, -1, 0)),
        (f'HindLower_{_s}', (_x * .145, .40, .36), (_x * .15, .55, .20), f'HindUpper_{_s}', (0, -1, 0)),
        (f'HindPaw_{_s}', (_x * .15, .55, .20), (_x * .15, .50, .012), f'HindLower_{_s}', (0, -1, 0)),
    ]
LEGS = {'FL': ('FrontLower_L', 'FrontPaw_L'), 'FR': ('FrontLower_R', 'FrontPaw_R'), 'HL': ('HindLower_L', 'HindPaw_L'), 'HR': ('HindLower_R', 'HindPaw_R')}


def build_rig():
    data = bpy.data.armatures.new('BR01_ZhuoBoar_Skeleton')
    arm = bpy.data.objects.new('RIG_BR01_ZhuoBoar', data)
    K.link(arm)
    K.select_only([arm], arm)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, head, tail, parent, roll in BONES:
        b = data.edit_bones.new(name)
        b.head, b.tail = head, tail
        b.align_roll(Vector(roll))
        if parent: b.parent = data.edit_bones[parent]
    # Foot targets for authoring only, not deforming, dropped from the exports.
    for key, (lower, paw) in LEGS.items():
        wrist = data.edit_bones[paw].head.copy()
        t = data.edit_bones.new('IK_' + key)
        t.head = wrist; t.tail = wrist + Vector((0, 0, .08)); t.parent = data.edit_bones['Root']; t.align_roll(Vector((0, 1, 0))); t.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')
    data['qa_deform'] = json.dumps([b[0] for b in BONES])
    return arm


def add_ik(arm):
    K.select_only([arm], arm)
    bpy.ops.object.mode_set(mode='POSE')
    for key, (lower, paw) in LEGS.items():
        pb = arm.pose.bones[lower]
        c = pb.constraints.new('IK'); c.name = 'FootIK'
        c.target = arm; c.subtarget = 'IK_' + key; c.chain_count = 2
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    bpy.ops.object.mode_set(mode='OBJECT')


def skin_to_rig(mesh, arm):
    """Distance-based weights with anatomical limits (left legs never move right skin), up to four bones per vertex.
    Fur takes the weights of the nearest body vertex."""
    me = mesh.data
    co = coords_of(mesh)
    part_ids = np.zeros(len(me.vertices), np.float32)
    me.attributes['qa_part'].data.foreach_get('value', part_ids)
    part_ids = np.rint(part_ids).astype(int)
    names = [b[0] for b in BONES]
    weights = np.zeros((len(co), len(names)), np.float32)
    idx = {n: i for i, n in enumerate(names)}
    is_body = part_ids == PART_BODY
    p = co[is_body]
    D = np.full((len(p), len(names)), np.inf, np.float32)
    for name, head, tail, parent, roll in BONES:
        if name in ('Root', 'Ear_L', 'Ear_R', 'Tail', 'Tail2'): continue
        d = seg_dist(p, head, tail)
        allow = np.ones(len(p), bool)
        if name.endswith('_L'): allow &= p[:, 0] > .015
        if name.endswith('_R'): allow &= p[:, 0] < -.015
        if name.startswith('FrontLower') or name.startswith('HindLower'): allow &= p[:, 2] < .42
        if name.startswith('FrontPaw') or name.startswith('HindPaw'): allow &= p[:, 2] < .22
        if name.startswith('FrontUpper') or name.startswith('HindUpper'):
            allow &= p[:, 2] < .6
            d = d * (1 + np.clip((p[:, 2] - .36) / .2, 0, 1) * 1.6)      # fades into the torso bones going up the flank
        D[:, idx[name]] = np.where(allow, d, np.inf)
    # The lower jaw below the mouth line goes wholly to Jaw; the rest of the snout never does.
    mouth = .372 + np.clip((p[:, 1] + .79) / .135, 0, 1) * .03
    jaw = (p[:, 1] < -.585) & (p[:, 2] < mouth - (np.clip(-p[:, 1] - .585, 0, .2) * 0))
    D[:, idx['Jaw']] = np.inf
    w = 1 / (D + .022) ** 4
    w[~np.isfinite(D)] = 0
    w = np.nan_to_num(w, posinf=0)
    order = np.argsort(-w, axis=1)[:, :4]
    top = np.zeros_like(w)
    np.put_along_axis(top, order, np.take_along_axis(w, order, axis=1), axis=1)
    top /= top.sum(axis=1, keepdims=True).clip(1e-9)
    top[jaw] = 0; top[jaw, idx['Jaw']] = 1
    weights[is_body] = top
    rigid = {PART_EAR_L: 'Ear_L', PART_EAR_R: 'Ear_R', PART_HEAD: 'Head', PART_JAW: 'Jaw', PART_HOOF_FL: 'FrontPaw_L', PART_HOOF_FR: 'FrontPaw_R', PART_HOOF_HL: 'HindPaw_L', PART_HOOF_HR: 'HindPaw_R'}
    for pid, bone in rigid.items():
        weights[part_ids == pid, idx[bone]] = 1
    tail = part_ids == PART_TAIL
    if tail.any():
        k = np.clip((.61 - co[tail, 2]) / .09, 0, 1)
        weights[tail, idx['Tail']] = 1 - k
        weights[tail, idx['Tail2']] = k
    fur = part_ids == PART_FUR
    if fur.any():
        src = np.where(is_body | tail)[0]
        tree = kdtree.KDTree(len(src))
        for n_, i in enumerate(src): tree.insert(co[i], n_)
        tree.balance()
        for i in np.where(fur)[0]:
            if co[i, 1] > .72 and co[i, 2] < .6 and abs(co[i, 0]) < .08:   # the tail's own hair
                k = float(np.clip((.61 - co[i, 2]) / .09, 0, 1))
                weights[i, idx['Tail']] = 1 - k; weights[i, idx['Tail2']] = k
                continue
            _, n_, _ = tree.find(co[i])
            weights[i] = weights[src[n_]]
    groups = [mesh.vertex_groups.new(name=n) for n in names]
    for b, g in enumerate(groups):
        where = np.nonzero(weights[:, b] > .004)[0]
        for i in where: g.add([int(i)], float(weights[i, b]), 'REPLACE')
    m = mesh.modifiers.new('Skin', 'ARMATURE'); m.object = arm
    mesh.parent = arm
    return int(np.count_nonzero(weights.sum(axis=1) < .5))


# ----------------------------------------------------------------------------- animation
FPS = 30


def set_rot(arm, frame, poses):
    for name, (x, y, z) in poses.items():
        pb = arm.pose.bones[name]
        pb.rotation_quaternion = Euler((x, y, z), 'XYZ').to_quaternion()
        pb.keyframe_insert('rotation_quaternion', frame=frame, group=name)


def set_world_move(arm, frame, bone, delta):
    """Moves a bone by a world-space offset from its rest position, whichever way its local axes point."""
    pb = arm.pose.bones[bone]
    pb.location = pb.bone.matrix_local.to_3x3().inverted() @ Vector(delta)
    pb.keyframe_insert('location', frame=frame, group=bone)


def foot(arm, frame, key, dy=0, dz=0, dx=0):
    set_world_move(arm, frame, 'IK_' + key, (dx, dy, dz))


def body(arm, frame, dy=0, dz=0, dx=0):
    set_world_move(arm, frame, 'Pelvis', (dx, dy, dz))


ALL_ROT = [b[0] for b in BONES if b[0] != 'Root']


def neutral(arm, frame):
    set_rot(arm, frame, {n: (0, 0, 0) for n in ALL_ROT})
    body(arm, frame)
    for k in LEGS: foot(arm, frame, k)


def loop_close(arm, first, last):
    """Copies the first frame's keys to the last, so a loop has no pop."""
    act = arm.animation_data.action
    from bpy_extras import anim_utils
    cb = anim_utils.action_get_channelbag_for_slot(act, arm.animation_data.action_slot)
    for fc in cb.fcurves:
        fc.keyframe_points.insert(last, fc.evaluate(first), options={'FAST'})
        fc.update()


def clip_idle(arm):
    n = 60
    for f, b, h in ((1, 0, 0), (31, 1, .5)):
        set_rot(arm, f, {'Chest': (.016 * b, 0, 0), 'Spine': (-.008 * b, 0, 0), 'Neck': (-.02 + .018 * b, 0, 0), 'Head': (-.03 - .018 * b, 0, .012 * b), 'Jaw': (-.012 - .01 * b, 0, 0),
                         'Tail': (.05 * b, 0, .1 - .2 * b), 'Tail2': (.03 * b, 0, .08 - .22 * b)})
        body(arm, f, dz=.006 * b)
    for k in LEGS: foot(arm, 1, k)
    # Ears flick: one at 18, the other twice around 42.
    set_rot(arm, 1, {'Ear_L': (0, 0, 0), 'Ear_R': (0, 0, 0)})
    for f, l, r in ((14, 0, 0), (17, .42, 0), (20, -.08, 0), (24, 0, 0), (38, 0, 0), (41, 0, .4), (44, 0, -.05), (47, 0, .3), (51, 0, 0), (n, 0, 0)):
        set_rot(arm, f, {'Ear_L': (l, 0, l * .4), 'Ear_R': (r, 0, -r * .4)})
    set_rot(arm, n, {'Chest': (0, 0, 0), 'Spine': (0, 0, 0), 'Neck': (-.02, 0, 0), 'Head': (-.03, 0, 0), 'Jaw': (-.012, 0, 0), 'Tail': (0, 0, .1), 'Tail2': (0, 0, .08)})
    body(arm, n)
    return n, True


def clip_paw(arm):
    """Head low, weight back, one forefoot scraping twice. 1.2 s."""
    n = 36
    low = {'Pelvis': (-.04, 0, 0), 'Spine': (.02, 0, 0), 'Chest': (-.07, 0, 0), 'Neck': (-.3, 0, 0), 'Neck2': (-.2, 0, 0), 'Head': (-.14, 0, 0), 'Ear_L': (-.38, 0, 0), 'Ear_R': (-.38, 0, 0), 'Tail': (.1, 0, .12), 'Tail2': (.05, 0, .1)}
    set_rot(arm, 1, {k: (0, 0, 0) for k in low})
    set_rot(arm, 7, low)
    set_rot(arm, n, low)
    body(arm, 1)
    body(arm, 7, dy=.03, dz=-.035)
    body(arm, n, dy=.035, dz=-.04)
    for k in ('FL', 'HL', 'HR'):
        foot(arm, 1, k); foot(arm, n, k)
    # FR: lift forward, drag back through the ground line, twice.
    for f, dy, dz, paw in ((1, 0, 0, 0), (6, -.10, .10, .45), (11, -.14, .05, .2), (15, .08, .005, -.5), (19, .10, .05, -.3), (23, -.13, .10, .45), (27, -.14, .05, .2), (31, .08, .005, -.5), (n, .03, .01, -.1)):
        foot(arm, f, 'FR', dy=dy, dz=dz)
        set_rot(arm, f, {'FrontPaw_R': (paw, 0, 0)})
    for f, k in ((14, .05), (16, -.04), (30, .05), (32, -.04)):
        set_rot(arm, f, {'Head': (-.14 + k, 0, k * .4)})
    return n, False


def gallop(arm, n, lift, stride, pitch, head, ears, tail, bob):
    """A running cycle: legs in pairs slightly apart, back flexing, head steady."""
    phase = {'HL': 0, 'HR': .1, 'FL': .46, 'FR': .56}
    for f in range(1, n + 1, 2):
        t = (f - 1) / (n - 1)
        a = math.tau * t
        flex = math.sin(a)
        for key, ph in phase.items():
            u = (t + ph) % 1
            if u < .42:     # on the ground, sweeping back
                k = u / .42
                dy = stride * (-1 + 2 * k); dz = 0
                paw = -.25 + .7 * k
            else:           # in the air, swinging forward
                k = (u - .42) / .58
                dy = stride * (1 - 2 * (k * k * (3 - 2 * k))); dz = lift * math.sin(math.pi * k)
                paw = .45 - .9 * math.sin(math.pi * k)
            foot(arm, f, key, dy=dy, dz=dz)
            set_rot(arm, f, {LEGS[key][1]: (paw, 0, 0)})
        body(arm, f, dz=bob * math.sin(a + 1.0) + bob * .3, dy=stride * .08 * flex)
        set_rot(arm, f, {
            'Pelvis': (-pitch * flex, 0, 0), 'Spine': (pitch * .35 * flex, 0, 0), 'Spine2': (pitch * .35 * flex, 0, 0), 'Chest': (pitch * .7 * flex, 0, 0),
            'Neck': (head - pitch * .55 * flex, 0, 0), 'Neck2': (head * .5, 0, 0), 'Head': (head * .3 - pitch * .25 * flex, 0, 0), 'Jaw': (-.06, 0, 0),
            'Ear_L': (ears, 0, .05 * flex), 'Ear_R': (ears, 0, -.05 * flex), 'Tail': (tail + .2 * flex, 0, 0), 'Tail2': (tail * .6 - .3 * flex, 0, 0)})
    return n, True


def clip_charge(arm):
    return gallop(arm, 17, lift=.15, stride=.27, pitch=.16, head=-.3, ears=-.65, tail=.65, bob=.04)


def clip_flee(arm):
    return gallop(arm, 21, lift=.13, stride=.23, pitch=.1, head=-.04, ears=-.2, tail=.95, bob=.03)


def clip_daze(arm):
    """Stunned, head swaying, legs unsteady. 2.5 s loop."""
    n = 75
    for f, sway, nod, roll, dip in ((1, -.12, -.2, .05, -.05), (12, .2, -.3, -.07, -.075), (24, -.26, -.17, .08, -.04), (38, .28, -.33, -.06, -.085), (52, -.2, -.2, .08, -.05), (64, .16, -.28, -.05, -.07), (n, -.12, -.2, .05, -.05)):
        set_rot(arm, f, {'Pelvis': (-.03, 0, roll * .7), 'Spine': (0, .02, -roll * .4), 'Chest': (-.06, -.03, roll),
                         'Neck': (nod, 0, sway * .7), 'Neck2': (nod * .4, 0, sway * .5), 'Head': (nod * .25, sway * .5, sway * .8),
                         'Jaw': (-.09, 0, sway * .12),
                         'Ear_L': (-.55 + sway * .4, 0, .25), 'Ear_R': (-.6 - sway * .4, 0, -.25), 'Tail': (-.05, 0, sway), 'Tail2': (0, 0, sway * .8)})
        body(arm, f, dz=dip, dx=roll * .25)
    # Quick head shakes on top of the sway.
    for f, k in ((30, .1), (32, -.12), (34, .1), (36, -.05)):
        set_rot(arm, f, {'Head': (-.07, .28 * k / .1, .1 + k)})
    # A front foot stumbles out and catches; the hind feet shuffle.
    for k, steps in (('FL', ((1, 0, 0, 0), (22, 0, 0, 0), (27, -.03, .05, .04), (32, -.05, 0, .07), (55, -.05, 0, .07), (60, -.02, .04, .03), (66, 0, 0, 0), (n, 0, 0, 0))),
                     ('FR', ((1, 0, 0, 0), (n, 0, 0, 0))),
                     ('HL', ((1, 0, 0, 0), (n, 0, 0, 0))),
                     ('HR', ((1, 0, 0, 0), (40, 0, 0, 0), (45, .02, .035, -.03), (50, .03, 0, -.05), (63, .03, 0, -.05), (68, .01, .03, -.02), (72, 0, 0, 0), (n, 0, 0, 0)))):
        for f, dy, dz, dx in steps: foot(arm, f, k, dy=dy, dz=dz, dx=dx)
    return n, True


def clip_cleanse(arm):
    """The dark qi lifts: hunched and unsure, then upright, a big head shake, ears up, still. 2 s."""
    n = 60
    hunched = {'Pelvis': (-.03, 0, 0), 'Chest': (-.06, 0, 0), 'Neck': (-.25, 0, 0), 'Neck2': (-.1, 0, 0), 'Head': (-.08, 0, 0), 'Ear_L': (-.5, 0, .2), 'Ear_R': (-.5, 0, -.2), 'Tail': (0, 0, 0), 'Tail2': (0, 0, 0)}
    up = {'Pelvis': (.0, 0, 0), 'Chest': (.05, 0, 0), 'Neck': (.2, 0, 0), 'Neck2': (.08, 0, 0), 'Head': (.03, 0, 0), 'Ear_L': (.25, 0, 0), 'Ear_R': (.25, 0, 0), 'Tail': (.2, 0, 0), 'Tail2': (.1, 0, 0)}
    rest = {k: (0, 0, 0) for k in up}
    rest['Ear_L'] = rest['Ear_R'] = (.08, 0, 0)
    set_rot(arm, 1, hunched); set_rot(arm, 10, hunched); set_rot(arm, 24, up); set_rot(arm, 44, up); set_rot(arm, n, rest)
    body(arm, 1, dz=-.05, dy=.02); body(arm, 10, dz=-.05, dy=.02); body(arm, 24, dz=.012); body(arm, 44, dz=.012); body(arm, n)
    for f, k in ((27, 1), (30, -1), (33, 1), (36, -.8), (39, .5), (42, -.2)):
        set_rot(arm, f, {'Head': (.03, k * .55, k * .22), 'Neck2': (.08, 0, k * .24), 'Neck': (.2, 0, k * .1), 'Ear_L': (.25, 0, -k * .5), 'Ear_R': (.25, 0, -k * .5)})
    for key in LEGS:
        foot(arm, 1, key); foot(arm, n, key)
    return n, False


CLIPS = [('Idle', clip_idle), ('Paw', clip_paw), ('Charge', clip_charge), ('Daze', clip_daze), ('Cleanse', clip_cleanse), ('Flee', clip_flee)]


def build_animations(arm):
    s = bpy.context.scene
    s.render.fps = FPS
    arm.animation_data_create()
    info = {}
    K.select_only([arm], arm)
    bpy.ops.object.mode_set(mode='POSE')
    for name, fn in CLIPS:
        for pb in arm.pose.bones:
            pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0)
        src = bpy.data.actions.new(name + '_src')
        arm.animation_data.action = src
        neutral(arm, 1)
        end, looped = fn(arm)
        if looped: loop_close(arm, 1, end)
        s.frame_start, s.frame_end = 1, end
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.nla.bake(frame_start=1, frame_end=end, step=1, only_selected=True, visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=False, clean_curves=False, bake_types={'POSE'})
        baked = arm.animation_data.action
        baked.name = name
        baked.use_fake_user = True
        baked['loop'] = looped
        baked['frames'] = end
        baked['root_motion'] = 'in_place'
        info[name] = {'frames': end, 'seconds': round((end - 1) / FPS, 3), 'loop': looped}
        bpy.data.actions.remove(src)
    bpy.ops.object.mode_set(mode='OBJECT')
    # The keys are FK now; the constraints would fight them.
    for key, (lower, paw) in LEGS.items():
        arm.pose.bones[lower].constraints['FootIK'].mute = True
    arm.animation_data.action = bpy.data.actions['Idle']
    return info


# ----------------------------------------------------------------------------- the whole asset
def main():
    s = K.reset()
    K.gpu(s, 1)
    src = K.coll('Source')
    K.ACTIVE['coll'] = src
    fur_mat = m_fur()
    m_ear()
    ivory = m_plain('BoarTusk', (.42, .32, .17), (.66, .56, .38), .42, scale=60)
    hoof = m_plain('BoarHoof', (.018, .014, .014), (.07, .052, .042), .52, scale=70)
    deco = m_plain('BoarBurr', (.09, .068, .025), (.27, .2, .08), .9, scale=120)
    needle = m_plain('BoarNeedle', (.19, .2, .05), (.42, .36, .1), .8, scale=60)

    skin = build_skin(fur_mat)
    skin_bvh = K.bvh_of(skin)
    parts = [skin] + build_details(skin_bvh, ivory, hoof, deco, needle)
    # Colour attribute on everything first, so the joined meshes keep it.
    for o in parts:
        col = o.data.color_attributes.new('Col', 'BYTE_COLOR', 'POINT')
        col.data.foreach_set('color', np.ones(len(o.data.vertices) * 4, np.float32))
    # Ear inner mask survives only if every part has it.
    for o in parts:
        if not o.data.attributes.get('qa_inner'):
            a = o.data.attributes.new('qa_inner', 'FLOAT', 'POINT')
            a.data.foreach_set('value', [0.0] * len(o.data.vertices))
    for node in EYE_NODES:
        node.inputs[0].default_value = abs(EYES[0].x); node.inputs[1].default_value = EYES[0].y; node.inputs[2].default_value = EYES[0].z
    K.finalize_parts(parts)
    gcoll = K.coll('Game')
    G, _ = K.game_mesh(KEY, parts, gcoll)
    K.ACTIVE['coll'] = gcoll
    for o in parts: o.hide_render = True
    src.hide_viewport = True

    tdir = OUT / 'textures'
    imgs, _ = K.bake_asset(G, KEY, tdir, res=2048, ao_samples=64)
    mat = K.game_material(KEY, imgs)
    G.data.materials.clear(); G.data.materials.append(mat)

    make_tuft_map(tdir / f'T_{KEY}_Fur.png')
    set_uv2(G.data)
    G.data.uv_layers.active_index = 0

    # LOD levels: decimate the baked skin and details, then grow each level's own fur on it.
    body_bvh = K.bvh_of(G)
    lods = [G] + K.make_lods(G, ratios=(.5, .16), gcoll=gcoll)
    body_parts = np.zeros(len(G.data.vertices), np.float32)

    specs = [
        # blades on the coat, segments, length, width; bristles; tail
        # cards, card size; spikes, segments, length, width; bristles; tail
        (9000, 1.0, 620, 2, 1.0, 1.0, 460, 1.0, 1.0, 60),
        (4200, 1.32, 300, 2, 1.1, 1.3, 260, 1.05, 1.25, 30),
        (800, 2.5, 70, 1, 1.3, 2.3, 110, 1.1, 2.2, 8),
    ]
    finals = []
    G.data.calc_loop_triangles()
    for level, (lod, spec) in enumerate(zip(lods, specs)):
        card_n, card_k, coat_n, segs, lk, wk, ridge_n, rl, rw, tail_n = spec
        roots = clip_width(fur_roots(G, coat_n, lk, wk, seed=7))
        ridge = clip_height(bristle_roots(ridge_n, rl, rw, body_bvh))
        tail = tail_roots(tail_n, 1.0, 1.0 + level * .7)
        spikes = blade_mesh(f'Fur_L{level}', roots + ridge + tail, segs)
        set_uv2(spikes.data)
        fur = join([spikes, card_mesh(f'Cards_L{level}', coat_cards(G, card_n, card_k))], f'Fur_L{level}')
        attach_to_atlas(fur, body_bvh, G)
        tips = coords_of(fur)
        tips[:, 0] = np.clip(tips[:, 0], -.298, .298); tips[:, 2] = np.clip(tips[:, 2], .002, .995); tips[:, 1] = np.clip(tips[:, 1], -.8, .795)
        set_coords(fur, tips)
        tag(fur, PART_FUR)
        a = fur.data.attributes.new('qa_inner', 'FLOAT', 'POINT')
        fur.data.materials.append(mat)
        name = f'{KEY}_LOD{level}' if level else KEY
        keep = lod.copy(); keep.data = lod.data.copy(); gcoll.objects.link(keep)
        joined = join([keep, fur], name)
        for attr_name in ('qa_inner', 'qa_lc', 'qa_seed', 'qa_node'):
            at = joined.data.attributes.get(attr_name)
            if at: joined.data.attributes.remove(at)
        for p in joined.data.polygons: p.use_smooth = True
        joined.data.uv_layers.active_index = 0
        finals.append(joined)
    for o in lods:
        bpy.data.objects.remove(o)
    for level, o in enumerate(finals):
        o.name = o.data.name = f'{KEY}_LOD{level}' if level else KEY
        ids_ = np.zeros(len(o.data.vertices), np.float32); o.data.attributes['qa_part'].data.foreach_get('value', ids_)
        c_ = coords_of(o)
        print('EXTENT', o.name, {int(p): [round(float(v), 3) for v in (np.abs(c_[np.rint(ids_) == p, 0]).max(), c_[np.rint(ids_) == p, 2].max(), c_[np.rint(ids_) == p, 1].min(), c_[np.rint(ids_) == p, 1].max())] for p in np.unique(np.rint(ids_))}, flush=True)

    # Collision: one convex hull of the torso, off the ground and clear of the feet.
    coll_verts = coords_of(finals[0])
    ids = np.zeros(len(coll_verts), np.float32); finals[0].data.attributes['qa_part'].data.foreach_get('value', ids)
    torso = coll_verts[(np.rint(ids) == PART_BODY) & (coll_verts[:, 2] > .3)]
    bm = bmesh.new()
    for v in torso[::4]: bm.verts.new(v)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    keep_v = {v for f in bm.faces for v in f.verts}
    for v in [v for v in bm.verts if v not in keep_v]: bm.verts.remove(v)
    col_me = bpy.data.meshes.new(KEY + '_Collision'); bm.to_mesh(col_me); bm.free()
    col = bpy.data.objects.new(KEY + '_Collision', col_me); gcoll.objects.link(col)
    col.hide_render = True
    bad = 0
    arm = build_rig()
    for o in finals: bad += skin_to_rig(o, arm)
    assert bad == 0, f'{bad} vertices without weights'
    add_ik(arm)
    clip_info = build_animations(arm)

    # Save, then export from the saved scene.
    BLEND.mkdir(parents=True, exist_ok=True)
    (K.REPO / 'art/source/zhuo-boar-a/blend').mkdir(parents=True, exist_ok=True)
    arm.animation_data.action = bpy.data.actions['Idle']
    OUT.mkdir(parents=True, exist_ok=True)
    glb = OUT / f'{KEY}_{VER}.glb'; fbx = OUT / f'{KEY}_{VER}.fbx'
    # Only the deform skeleton goes out: the foot targets are for authoring.
    for b in arm.data.bones: b.use_deform = b.name in json.loads(arm.data['qa_deform'])
    K.select_only([arm] + finals + [col], arm)
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_apply=False, export_yup=True, export_image_format='AUTO', export_materials='EXPORT',
                              export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True, export_def_bones=True, export_skins=True,
                              export_vertex_color='ACTIVE', export_extras=False)
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'ARMATURE', 'MESH'}, axis_forward='-Z', axis_up='Y', apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                             bake_space_transform=False, add_leaf_bones=False, use_armature_deform_only=True, mesh_smooth_type='FACE', use_tspace=True, colors_type='LINEAR',
                             bake_anim=True, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='RELATIVE', embed_textures=False)

    c0 = coords_of(finals[0]); mn, mx = c0.min(axis=0), c0.max(axis=0)
    info = {
        'id': 'BR01', 'name': KEY, 'version': VER, 'unit': 'metre, 1 unit = 1 m', 'front': '-Y (Blender); see Unity note in README',
        'origin': 'footprint centre, lowest vertex at z = 0, no ground plate',
        'sizeM': {'length': round(float(mx[1] - mn[1]), 3), 'width': round(float(mx[0] - mn[0]), 3), 'height': round(float(mx[2] - mn[2]), 3)},
        'limitM': {'length': 1.6, 'width': .6, 'height': 1.0},
        'tris': {f'LOD{i}': K.tri_count(o) for i, o in enumerate(finals)},
        'collision': {'name': col.name, 'kind': 'convex hull of the torso, above z = 0.3', 'tris': K.tri_count(col)},
        'material': {'name': mat.name, 'textures': [f'textures/T_{KEY}_{n}.png' for n in ('BaseColor', 'ORM', 'Normal', 'Mask', 'Fur')], 'atlas': 2048, 'uv2': 'fur tufts: A of T_Fur cuts them out; needs alpha clip, as the Unity shader does', 'unityShader': 'YunJing/QingxiZhuoBoar', 'vertexColour': 'fur root-to-tip shade, multiplied onto the base colour'},
        'state': {'_Zhuo': {'range': [0, 1], 'meaning': '1 = dark qi veins and dull red eyes, 0 = healthy warm brown', 'mask': 'Mask R (veins), G (eyes)'}},
        'skeleton': {'bones': [b[0] for b in BONES], 'count': len(BONES), 'deformExceptRoot': len(BONES) - 1},
        'animations': clip_info, 'fps': FPS,
        'lodNote': 'LOD2 keeps the tusks, the ears and a coarse bristle ridge in its silhouette.',
    }
    (OUT / f'{KEY}_model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND / f'{KEY}_{VER}.blend'), compress=True)
    print('BOAR_BUILD_PASS', json.dumps(info['tris']), info['sizeM'], flush=True)


if __name__ == '__main__':
    main()
