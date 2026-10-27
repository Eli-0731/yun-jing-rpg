"""D02 timber beam footbridge 木造梁橋 (extra asset requested after the 29-module kit; not one of the 29).

  blender -b --python-exit-code 1 --python 05_Scripts/generate_timber_bridge.py

SM_Bridge_Timber_A: 10 m long, 3 m wide plank deck on four sawn stringers, timber railings on both sides and
one timber trestle (three bark piles, cap beam, cross braces) at mid-span.  The deck top is local Z = 0 and the
pivot is the centre of the deck at the entry end; travel +X.  Placed at (2, 0, +0.15) in the bridgehead frame
the deck is flush with the C01 ramp exit, and the stringer ends are notched to rest at local Z = -0.20 on the
C05 stone bases (top -0.05) of two bridgeheads whose frames are 14 m apart (far one turned 180 degrees).
Nothing reaches beyond |Y| = 1.5 over the 1.25 m bearings, so the C07 corner stones stay clear.

Writes (never overwrites): 01_Blender/timber_bridge_v01.blend (+ .build.json), 02_Exports/Bridge/SM_Bridge_Timber_A.fbx,
04_Previews/Individual/D02_SM_Bridge_Timber_A/ (10 orthographic views fitted per view, 11_persp_45, 12_detail,
13_pier, views.json, model_info.json, validation.json).
"""
import sys, json, math, random
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K
import kit_blender as KB
import export_fbx as EX
import generate_log_bridge as LB

MID, CODE, NAME_ZH = 'SM_Bridge_Timber_A', 'D02', '木造梁橋'
L = 10.0; HALF_W = K.DECK_HALF; PLANK_T = 0.05; SEAT_Z = -0.20; SPAN_BOTTOM = -0.30
SEAT_L = K.BASE_FACE_X - K.RAMP_L; SHOULDER = 0.18
STRINGERS_Y = (-1.2, -0.4, 0.4, 1.2); STRINGER_W = 0.2
POSTS_X = (1.45, 2.65, 3.85, 5.0, 6.15, 7.35, 8.55); POST_Y = 1.40; POST_H = 0.90
PIER_X = L / 2; PILES_Y = (-1.15, 0.0, 1.15); PILE_BOTTOM = -1.95
PLACE = Matrix.Translation((K.RAMP_L, 0.0, K.DECK_Z))
OUT_BLEND = '01_Blender/timber_bridge_v01.blend'; OUT_FBX = '02_Exports/Bridge/%s.fbx' % MID
PREV = '04_Previews/Individual/%s_%s' % (CODE, MID)
TIMBER, BARK, END = 0, 1, 2
T = K.UV_TILE_M


def add_poly(P, pts, mat, uvs, smooth=False):
    o = len(P.v); P.v += [tuple(p) for p in pts]
    P.f.append(tuple(range(o, o + len(pts)))); P.m.append(mat); P.uv.append(uvs); P.sm.append(smooth)


def beam(P, p0, p1, w, h, up=(0, 0, 1), rng=None, mat=TIMBER):
    """Sawn timber from p0 to p1 (centre line), w x h section; grain (U) runs along the piece, ends are end grain."""
    p0, p1 = Vector(p0), Vector(p1); a = (p1 - p0); ln = a.length; a.normalize()
    u = Vector(up); b = u.cross(a); b = b.normalized() if b.length > 1e-6 else Vector((0, 1, 0)); c = a.cross(b)
    o = Vector((rng.uniform(0, 4), rng.uniform(0, 4))) if rng else Vector((0, 0))
    cs = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    ring0 = [p0 + b * x + c * y for x, y in cs]; ring1 = [p1 + b * x + c * y for x, y in cs]
    perim = [0.0, w, w + h, 2 * w + h, 2 * w + 2 * h]
    for k in range(4):
        kn = (k + 1) % 4
        add_poly(P, [ring0[k], ring1[k], ring1[kn], ring0[kn]], mat,
                 [(o.x, o.y + perim[k] / T), (o.x + ln / T, o.y + perim[k] / T), (o.x + ln / T, o.y + perim[k + 1] / T), (o.x, o.y + perim[k + 1] / T)])
    euv = [(0.5 + x / max(w, h), 0.5 + y / max(w, h)) for x, y in cs]
    add_poly(P, list(reversed(ring0)), END, list(reversed(euv))); add_poly(P, ring1, END, euv)


def pile(P, x, y, z0, z1, r, sides=10, mat=BARK):
    ring0 = [Vector((x + r * math.cos(k * math.tau / sides), y + r * math.sin(k * math.tau / sides), z0)) for k in range(sides)]
    ring1 = [Vector((p.x, p.y, z1)) for p in ring0]
    for k in range(sides):
        kn = (k + 1) % sides; u0, u1 = k / sides * math.tau * r / T * 2.2, (k + 1) / sides * math.tau * r / T * 2.2
        add_poly(P, [ring0[k], ring0[kn], ring1[kn], ring1[k]], mat, [(u0, z0 / T * 2.2), (u1, z0 / T * 2.2), (u1, z1 / T * 2.2), (u0, z1 / T * 2.2)], smooth=True)
    add_poly(P, ring1, END, [(0.5 + 0.42 * math.cos(k * math.tau / sides), 0.5 + 0.42 * math.sin(k * math.tau / sides)) for k in range(sides)])


def stringer(P, y, deep=True):
    """Side profile extruded across Y: deck seat on top, notched ends resting on C05, deeper over the span."""
    zb = SPAN_BOTTOM if deep else SEAT_Z
    prof = [(0.0, -PLANK_T), (L, -PLANK_T), (L, SEAT_Z), (L - SEAT_L, SEAT_Z), (L - SEAT_L - SHOULDER, zb), (SEAT_L + SHOULDER, zb), (SEAT_L, SEAT_Z), (0.0, SEAT_Z)]
    y0, y1 = y - STRINGER_W / 2, y + STRINGER_W / 2
    side0 = [Vector((x, y0, z)) for x, z in prof]; side1 = [Vector((x, y1, z)) for x, z in prof]
    add_poly(P, list(reversed(side0)), TIMBER, [(x / T, z / T) for x, z in reversed(prof)])
    add_poly(P, side1, TIMBER, [(x / T, z / T) for x, z in prof])
    n = len(prof)
    for k in range(n):
        kn = (k + 1) % n; a, b = prof[k], prof[kn]
        seg = math.hypot(b[0] - a[0], b[1] - a[1]); mat = END if abs(a[0] - b[0]) < 1e-9 and a[0] in (0.0, L) else TIMBER
        uv = [(0.5, 0.2), (0.5, 0.8), (0.9, 0.8), (0.9, 0.2)] if mat == END else [(0, 0), (0, STRINGER_W / T), (seg / T, STRINGER_W / T), (seg / T, 0)]
        add_poly(P, [side0[k], side1[k], side1[kn], side0[kn]], mat, uv)


def deck_planks(P, rng):
    x = 0.0; i = 0
    while x < L - 1e-6:
        w = min(rng.uniform(0.19, 0.23), L - x)
        if L - (x + w) < 0.12: w = L - x                          # no sliver at the far end
        bearing = x < SEAT_L + 0.05 or x + w > L - SEAT_L - 0.05
        half = HALF_W if bearing else HALF_W + rng.uniform(-0.03, 0.0)
        dz = 0.0 if (bearing or i < 2) else rng.uniform(-0.003, 0.0)
        gap = 0.012 if x + w < L - 1e-6 else 0.0
        x0, x1 = x + (0.006 if x > 0 else 0.0), x + w - (gap / 2 if gap else 0.0)
        beam(P, (x0 + (x1 - x0) / 2, -half, dz - PLANK_T / 2), (x0 + (x1 - x0) / 2, half, dz - PLANK_T / 2), PLANK_T, x1 - x0, up=(1, 0, 0), rng=rng)
        x += w; i += 1
    return i


def railings(P, rng, simple=False):
    for sg in (1, -1):
        y = sg * POST_Y
        for k, px in enumerate(POSTS_X if not simple else POSTS_X[::3] + (POSTS_X[-1],)):
            end = px in (POSTS_X[0], POSTS_X[-1]); s = 0.14 if end else 0.11; top = POST_H + (0.06 if end else 0.0)
            beam(P, (px, y, 0.0), (px, y, top), s, s, up=(1, 0, 0), rng=rng)
            if end and not simple:                               # pyramid cap on the end posts
                c = Vector((px, y, top + 0.07)); q = [Vector((px - s / 2, y - s / 2, top)), Vector((px + s / 2, y - s / 2, top)), Vector((px + s / 2, y + s / 2, top)), Vector((px - s / 2, y + s / 2, top))]
                for j in range(4): add_poly(P, [q[j], q[(j + 1) % 4], c], TIMBER, [(0, 0), (0.1, 0), (0.05, 0.06)])
        beam(P, (POSTS_X[0] - 0.05, y, POST_H + 0.035), (POSTS_X[-1] + 0.05, y, POST_H + 0.035), 0.08, 0.07, rng=rng)       # handrail
        if not simple: beam(P, (POSTS_X[0], y, 0.45), (POSTS_X[-1], y, 0.45), 0.05, 0.08, rng=rng)                         # mid rail


def pier(P, rng, simple=False):
    beam(P, (PIER_X, -1.6, SPAN_BOTTOM - 0.125), (PIER_X, 1.6, SPAN_BOTTOM - 0.125), 0.3, 0.25, rng=rng)                 # cap beam
    for y in PILES_Y: pile(P, PIER_X, y, PILE_BOTTOM, SPAN_BOTTOM - 0.25, 0.11, 10 if not simple else 6)
    if simple: return
    for face in (-1, 1):                                                                                                    # cross braces on both faces
        x = PIER_X + face * 0.15; x2 = PIER_X + face * 0.215   # the second brace of each X sits one brace thickness further out (no coplanar overlap)
        for (ya, yb) in ((PILES_Y[0], PILES_Y[1]), (PILES_Y[1], PILES_Y[2])):
            beam(P, (x, ya, -0.62), (x, yb, -1.45), 0.13, 0.06, up=(1, 0, 0), rng=rng)
            beam(P, (x2, ya, -1.45), (x2, yb, -0.62), 0.13, 0.06, up=(1, 0, 0), rng=rng)


def build(scene):
    mats = [KB.pbr_material('Timber'), KB.pbr_material('Bark'), KB.pbr_material('EndGrain')]
    extras = bpy.data.collections.new('KIT_Extras'); scene.collection.children.link(extras)
    coll = bpy.data.collections.new(MID); extras.children.link(coll)
    root = bpy.data.objects.new(MID, None); coll.objects.link(root); root.empty_display_type = 'ARROWS'; root.empty_display_size = 0.6
    cons = [dict(name='EntryConnector', role='entry', type='BRIDGE_3M', location=(0.0, 0.0, 0.0), heading_deg=0.0, partner='SM_Bridgehead_RoadTransition_A exit'),
            dict(name='ExitConnector', role='exit', type='BRIDGE_3M', location=(L, 0.0, 0.0), heading_deg=0.0, partner='far SM_Bridgehead_RoadTransition_A exit (turned 180)'),
            dict(name='Seat_Entry', role='seat', type='BRIDGE_SEAT', location=(SEAT_L / 2, 0.0, SEAT_Z), heading_deg=0.0, partner='SM_Bridgehead_Base_A'),
            dict(name='Seat_Exit', role='seat', type='BRIDGE_SEAT', location=(L - SEAT_L / 2, 0.0, SEAT_Z), heading_deg=0.0, partner='SM_Bridgehead_Base_A (far bank)')]
    root['kit_module_id'] = MID; root['kit_code'] = CODE; root['kit_version'] = K.KIT_VERSION; root['kit_connectors'] = json.dumps(cons)
    root['kit_pivot'] = 'centre of the deck top at the entry end; bridgehead frame placement = translate (2, 0, +0.15)'
    rng = random.Random(31)
    P0 = KB.Parts(); n_planks = deck_planks(P0, rng)
    for y in STRINGERS_Y: stringer(P0, y)
    railings(P0, rng); pier(P0, rng)
    lod0 = P0.build(MID + '_LOD0', mats, coll, root, uv_mode='given')
    P1 = KB.Parts(); beam(P1, (0.0, 0.0, -PLANK_T / 2), (L, 0.0, -PLANK_T / 2), 2 * HALF_W, PLANK_T, rng=rng)
    for y in STRINGERS_Y[::3]: stringer(P1, y)
    railings(P1, rng, simple=True); pier(P1, rng, simple=True)
    lod1 = P1.build(MID + '_LOD1', mats, coll, root, uv_mode='given')
    P2 = KB.Parts(); beam(P2, (0.0, 0.0, (SPAN_BOTTOM) / 2), (L, 0.0, SPAN_BOTTOM / 2), 2 * HALF_W, -SPAN_BOTTOM, rng=rng)
    for sg in (1, -1): beam(P2, (POSTS_X[0], sg * POST_Y, POST_H / 2), (POSTS_X[-1], sg * POST_Y, POST_H / 2), 0.08, POST_H, rng=rng)
    beam(P2, (PIER_X, 0.0, SPAN_BOTTOM - 0.3), (PIER_X, 0.0, PILE_BOTTOM), 3.2, 0.25, up=(1, 0, 0), rng=rng)
    lod2 = P2.build(MID + '_LOD2', mats, coll, root, uv_mode='given')
    C = KB.Parts(); KB.block(C, (L / 2, 0.0, -PLANK_T / 2), (L, 2 * HALF_W, PLANK_T))
    for sg in (1, -1): KB.block(C, ((POSTS_X[0] + POSTS_X[-1]) / 2, sg * POST_Y, POST_H / 2 + 0.02), (POSTS_X[-1] - POSTS_X[0] + 0.14, 0.1, POST_H + 0.04))
    col = C.build(MID + '_COL', [], coll, root); col.display_type = 'WIRE'
    made = [lod0, lod1, lod2, col]
    for o in made: o.data.shade_flat() if o is not lod0 else None
    lod0.data.set_sharp_from_angle(angle=math.radians(35))
    for o in made[1:]: o.hide_render = True; o.hide_set(True)
    return coll, root, made, cons, n_planks


def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)


def validate(made, n_planks):
    vs = [v.co.copy() for v in made[0].data.vertices]
    deck_top = [v for v in vs if abs(v.z) < 0.004 and abs(v.y) <= HALF_W + 1e-6 and v.z <= 1e-7]
    entry = [v for v in vs if v.x < 0.25 and abs(v.z) < 0.004 and abs(v.y) <= HALF_W]
    bearing = [v for v in vs if min(v.x, L - v.x) <= SEAT_L + 1e-6]
    clear = [(PLACE @ v).z - K.c_H((PLACE @ v).x, (PLACE @ v).y) for v in vs if K.BASE_FACE_X + 0.01 < (PLACE @ v).x < K.BH_RIVER_X and v.z < -0.1]
    R = {'planks': n_planks, 'deck_top_highest_z_m': max(v.z for v in vs if abs(v.y) <= HALF_W + 0.05 and v.z < 0.05),
         'entry_plank_top_z_m': max(v.z for v in entry), 'deck_top_min_z_m': min(v.z for v in deck_top),
         'bearing_lowest_z_m': min(v.z for v in bearing), 'bearing_max_abs_y_m': max(abs(v.y) for v in bearing),
         'seat_contact_vertices': sum(1 for v in bearing if abs(v.z - SEAT_Z) < 1e-6),
         'seat_in_bridgehead_frame_z_m': (PLACE @ Vector((0, 0, SEAT_Z))).z, 'c05_top_z_m': K.DECK_BOTTOM,
         'entry_top_in_bridgehead_frame_z_m': (PLACE @ Vector((0, 0, max(v.z for v in entry)))).z, 'c01_exit_z_m': K.DECK_Z,
         'min_clearance_above_c08_c02_m': min(clear) if clear else None, 'railing_height_m': POST_H + 0.07, 'clear_walk_width_m': 2 * POST_Y - 0.11,
         'tris': {o.name: tris(o) for o in made}, 'lod0_tris': tris(made[0]), 'budget': [800, 4000]}
    R['pass'] = (abs(R['entry_plank_top_z_m']) <= K.TOL and R['deck_top_min_z_m'] >= -0.004 and R['bearing_lowest_z_m'] >= SEAT_Z - K.TOL
                 and R['bearing_max_abs_y_m'] <= HALF_W + K.TOL and R['seat_contact_vertices'] >= 16
                 and abs(R['seat_in_bridgehead_frame_z_m'] - K.DECK_BOTTOM) <= K.TOL and abs(R['entry_top_in_bridgehead_frame_z_m'] - K.DECK_Z) <= K.TOL
                 and (R['min_clearance_above_c08_c02_m'] or 1) > 0.02 and R['lod0_tris'] <= 4000)
    return R


def previews(scene, coll, made):
    view = bpy.data.scenes.new('TB_Preview'); stu = bpy.data.collections.new('TB_Studio'); view.collection.children.link(stu)
    KB.studio(view, stu, samples=12, transparent=False); view.collection.children.link(coll)
    cam = bpy.data.objects.new('TB_Camera', bpy.data.cameras.new('TB_Camera')); stu.objects.link(cam); view.camera = cam; cam.data.clip_end = 200
    view.view_layers[0].update()
    objs = [made[0]]; pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)]); centre = (lo + hi) / 2
    extra = [('11_persp_45', (-0.75, -1.0, 0.55), None, None), ('12_detail', (-0.85, -1.0, 0.55), (1.6, -0.7, 0.35), 3.6),
             ('13_pier', (0.55, -1.0, -0.05), (PIER_X, 0.0, -0.9), 4.6)]
    records = []
    for name, d in KB.VIEWS + [(e[0], e[1]) for e in extra]:
        p = KB.new_output(PREV + '/' + name + '.png'); persp = name[:2] in ('11', '12', '13')
        if persp:
            view.cycles.samples = 32; cam.data.type = 'PERSP'; cam.data.lens = 38 if name.startswith('11') else 32
            e = next(e for e in extra if e[0] == name)
            if e[2] is None: KB.look_at(cam, centre, d, (hi - lo).length / 2 / math.sin(math.atan(18 / 38)) * 1.03)
            else: KB.look_at(cam, Vector(e[2]), d, e[3])
        else:
            view.cycles.samples = 12; cam.data.type = 'ORTHO'; LB.fit_ortho(cam, objs, d); KB.look_at(cam, centre, d, 40)
        view.render.filepath = str(p); bpy.ops.render.render(write_still=True, scene=view.name)
        records.append({'file': name + '.png', 'direction': list(d), 'projection': 'perspective' if persp else 'orthographic',
                        'camera_location': list(cam.location), 'ortho_scale': None if persp else cam.data.ortho_scale})
    KB.kit_path(PREV, 'views.json').write_text(json.dumps({'module': MID, 'code': CODE, 'source': OUT_BLEND, 'same_geometry': True,
                                                           'note': 'Library view convention: 01_front looks from -Y. Orthographic scale fitted per view.',
                                                           'lod_rendered': 'LOD0', 'views': records}, indent=2))
    view.collection.children.unlink(coll)


def main():
    scene = KB.start_session()
    out_blend = KB.new_output(OUT_BLEND); out_fbx = KB.new_output(OUT_FBX)
    for p in (PREV + '/views.json', PREV + '/model_info.json', PREV + '/validation.json'): KB.new_output(p)
    coll, root, made, cons, n_planks = build(scene)
    bpy.context.view_layer.update()
    V = validate(made, n_planks); print('VALIDATION', 'PASS' if V['pass'] else 'FAIL', json.dumps({k: v for k, v in V.items() if k != 'tris'}), flush=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend)); bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_mainfile()
    for o in made: o.hide_set(False)
    EX.select_only([root] + made); bpy.ops.export_scene.fbx(filepath=str(out_fbx), **EX.FBX_EXPORT)
    for o in made[1:]: o.hide_set(True)
    previews(scene, coll, made)
    RI = LB.reimport_check(made, out_fbx); print('REIMPORT', 'PASS' if RI['pass'] else 'FAIL', RI, flush=True)
    lo, hi = EX.world_bounds(made[:1])
    info = {'id': MID, 'code': CODE, 'name_zh': NAME_ZH, 'group': 'D (extra, requested after the 29-module kit)', 'version': K.KIT_VERSION,
            'purpose': '木造梁橋：3 m 寬木板橋面、4 根主梁、兩側木欄杆、河中央一座木排架（3 根圓木樁＋帽梁＋交叉斜撐）；跨距 10 m，橋面與 C01 坡道頂齊平，主梁兩端削口擱在兩岸 C05 石基上。',
            'units': 'metre', 'up': '+Z', 'forward': '+X', 'pivot': root['kit_pivot'], 'bounds_min_m': lo, 'bounds_max_m': hi,
            'triangles': V['tris'], 'materials': ['M_Timber', 'M_Bark', 'M_EndGrain'], 'connectors': cons,
            'files': {'blend': OUT_BLEND, 'blend_sha256': LB.sha(out_blend), 'fbx': OUT_FBX, 'fbx_sha256': LB.sha(out_fbx), 'previews': PREV},
            'fits': 'two bridgeheads whose frames are 14 m apart, the far one turned 180 degrees (10 m between the C01 exits); pier piles reach local Z %.2f' % PILE_BOTTOM}
    KB.kit_path(PREV, 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2))
    KB.kit_path(PREV, 'validation.json').write_text(json.dumps({'module': MID, 'code': CODE, 'tolerance_m': K.TOL, 'geometry': V, 'fbx_blender_reimport': RI,
                                                                 'overall_pass': V['pass'] and RI['pass'],
                                                                 'not_verified': ['Unity / Unreal import', 'in-engine walking and railing collision', 'performance']},
                                                                ensure_ascii=False, indent=2, default=float))
    Path(str(out_blend).replace('.blend', '.build.json')).write_text(json.dumps({'modules': {MID: {'tris': V['tris'], 'lod0_tris': V['lod0_tris']}}}, indent=2))
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
