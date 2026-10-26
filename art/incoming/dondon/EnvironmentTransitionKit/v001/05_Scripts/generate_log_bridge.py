"""D01 single-log footbridge 獨木橋 (extra asset requested after the 29-module kit; not one of the 29).

  blender -b --python-exit-code 1 --python 05_Scripts/generate_log_bridge.py

SM_Bridge_Log_A is one hewn tree trunk, 10 m long, tapering from 0.46 m to 0.40 m with a slight natural bow.
The walking surface is an adzed flat strip at local Z = 0 (about 0.3-0.4 m wide); the pivot is the centre of
that strip at the entry end; travel +X.  Placed at (2, 0, +0.15) in the bridgehead frame it is flush with the
C01 ramp exit, and its underside is notched flat at local Z = -0.20 over the first and last 1.25 m, so it
rests on the C05 stone bases (top -0.05) of two bridgeheads whose frames are 14 m apart (the far one turned
180 degrees, as in the showcase).

Writes (never overwrites): 01_Blender/log_bridge_v01.blend (+ .build.json), 02_Exports/Bridge/SM_Bridge_Log_A.fbx,
04_Previews/Individual/D01_SM_Bridge_Log_A/ (10 orthographic views fitted per view, 11_persp_45, 12_detail, views.json,
model_info.json, validation.json).  Validation: walking strip flatness and width, seat contact and no
penetration into C05, clearance above C08/C02 terrain, triangle counts, and a Blender re-import of the FBX.
"""
import sys, json, math, random, hashlib
from pathlib import Path
import bpy
from mathutils import Vector, Matrix, noise
from mathutils.kdtree import KDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K
import kit_blender as KB
import export_fbx as EX

MID, CODE, NAME_ZH = 'SM_Bridge_Log_A', 'D01', '獨木橋'
L = 10.0; R0, R1 = 0.23, 0.20; AXIS_Z = -0.12; SEAT_Z = -0.20
SEAT_L = K.BASE_FACE_X - K.RAMP_L                  # 1.25 m bearing on each C05 base
SHOULDER = 0.18                                    # notch shoulder length
BARK_UV = 2.2                                      # bark repeats 2.2x denser than the 2 m terrain tiles (finer plates on a 0.4 m trunk)
PLACE = Matrix.Translation((K.RAMP_L, 0.0, K.DECK_Z))   # into the bridgehead frame
OUT_BLEND = '01_Blender/log_bridge_v01.blend'; OUT_FBX = '02_Exports/Bridge/%s.fbx' % MID
PREV = '04_Previews/Individual/%s_%s' % (CODE, MID)


def S(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)


def radius(s, th, fine=True):
    R = R0 + (R1 - R0) * s / L
    k = 1 + 0.035 * noise.noise(Vector((s * 0.9, math.cos(th) * 1.3, math.sin(th) * 1.3)))
    if fine: k += 0.012 * noise.noise(Vector((s * 6.0, math.cos(th) * 4.0, math.sin(th) * 4.0 + 7.0)))
    return R * k


def axis_y(s): return 0.05 * math.sin(math.pi * s / L)


def floor_z(s):
    """Lowest allowed Z at s: the seat plane under the bearings, rising out over the notch shoulder."""
    d = min(s, L - s)
    if d <= SEAT_L: return SEAT_Z
    return SEAT_Z - 0.4 * S((d - SEAT_L) / SHOULDER) if d < SEAT_L + SHOULDER else -9.0


def ring_positions(step):
    s = [L * i / round(L / step) for i in range(round(L / step) + 1)]
    for d in (SEAT_L, SEAT_L + SHOULDER * 0.5, SEAT_L + SHOULDER):
        s += [d, L - d]
    return sorted(set(round(v, 6) for v in s))


def ring_angles(s, n1, nf):
    """Angles of one ring, starting at the underside: round right side, the two edges of the adzed strip with nf
    points between them, round left side.  The strip edges sit exactly where the round surface meets Z = 0."""
    r_top = radius(s, math.pi / 2, False); ta = math.asin(max(-1.0, min(1.0, -AXIS_Z / r_top))); tb = math.pi - ta
    right = [-math.pi / 2 + (ta + math.pi / 2) * k / n1 for k in range(n1)]
    left = [tb + (1.5 * math.pi - tb) * k / n1 for k in range(1, n1)]
    return right + [ta] + [ta + (tb - ta) * k / (nf + 1) for k in range(1, nf + 1)] + [tb] + left, n1, nf


def log_mesh(name, step, n1, nf, fine, mats, coll, parent, stubs=False):
    """Rings around the trunk; the top is an exact flat strip at Z = 0, the bottom is clamped to the seat near both ends."""
    ss = ring_positions(step); P = KB.Parts(); rings = []; angs = []
    for s in ss:
        ths, _, _ = ring_angles(s, n1, nf); ring = []
        ia, ib = n1, n1 + nf + 1
        for j, th in enumerate(ths):
            r = radius(s, th, fine); y = axis_y(s) + r * math.cos(th); z = AXIS_Z + r * math.sin(th)
            ring.append([s, y, max(min(z, 0.0), floor_z(s))])
        ring[ia][2] = ring[ib][2] = 0.0
        for k in range(1, nf + 1):
            t = k / (nf + 1); ring[ia + k] = [s, ring[ia][1] + (ring[ib][1] - ring[ia][1]) * t, 0.0]
        rings.append([tuple(v) for v in ring]); angs.append(ths)
    nr = len(rings[0]); ths = angs[0]
    verts = [p for ring in rings for p in ring]; base = len(P.v); P.v += verts
    Rm = (R0 + R1) / 2
    for i in range(len(ss) - 1):
        for j in range(nr):
            jn = (j + 1) % nr
            idx = [base + i * nr + j, base + (i + 1) * nr + j, base + (i + 1) * nr + jn, base + i * nr + jn]
            pts = [Vector(P.v[k]) for k in idx]
            top = all(p.z >= -1e-7 for p in pts); seat = all(p.z <= SEAT_Z + 1e-7 for p in pts)
            if top or seat:
                mat = 1; uv = [(p.x / K.UV_TILE_M, p.y / K.UV_TILE_M) for p in pts]
            else:
                a0 = angs[i][j] + math.pi / 2; a1 = (angs[i][jn] if jn else angs[i][0] + math.tau) + math.pi / 2
                c = (pts[0] + pts[2]) / 2; up = Vector((0, 0, 1)); n = (pts[1] - pts[0]).cross(pts[3] - pts[0])
                mat = 3 if (min(ss[i], L - ss[i + 1]) < 1.8 and n.length > 0 and n.normalized().z > 0.25 and noise.noise(c * 2.7) > 0.32) else 0
                k = BARK_UV / K.UV_TILE_M
                uv = [(a0 * Rm * k, ss[i] * k), (a0 * Rm * k, ss[i + 1] * k), (a1 * Rm * k, ss[i + 1] * k), (a1 * Rm * k, ss[i] * k)]
            P.f.append(tuple(idx)); P.m.append(mat); P.uv.append(uv); P.sm.append(None)
    for i, flip in ((0, True), (len(ss) - 1, False)):            # sawn ends: a fan around the axis point
        ring = rings[i]; cy = axis_y(ss[i]); cz = sum(p[2] for p in ring) / nr; c = len(P.v); P.v.append((ss[i], cy, cz))
        rc = max(math.hypot(p[1] - cy, p[2] - cz) for p in ring) * 1.12
        def cuv(p): return (0.5 + (p[1] - cy) / (2 * rc), 0.5 + (p[2] - cz) / (2 * rc))
        for j in range(nr):
            a, b = base + i * nr + j, base + i * nr + (j + 1) % nr
            tri = (c, b, a) if flip else (c, a, b)
            P.f.append(tri); P.m.append(2); P.uv.append([cuv(P.v[k]) for k in tri]); P.sm.append(False)
    if stubs:
        rng = random.Random(5)
        for s, th, rr, ln in ((2.55, -0.45, 0.05, 0.15), (5.85, math.pi + 0.35, 0.06, 0.18), (7.7, -0.75, 0.04, 0.11), (4.1, math.pi + 0.9, 0.035, 0.09)):
            d = Vector((0.18, math.cos(th), math.sin(th))).normalized(); r0 = radius(s, th) - 0.04
            o = Vector((s, axis_y(s) + r0 * math.cos(th), AXIS_Z + r0 * math.sin(th)))
            u = d.cross(Vector((1, 0, 0))).normalized(); w = d.cross(u)
            ring0 = [o + (u * math.cos(k * math.tau / 8) + w * math.sin(k * math.tau / 8)) * rr for k in range(8)]
            ring1 = [o + d * ln + (u * math.cos(k * math.tau / 8) + w * math.sin(k * math.tau / 8)) * rr * 0.8 for k in range(8)]
            b0 = len(P.v); P.v += [tuple(p) for p in ring0 + ring1]
            for k in range(8):
                kn = (k + 1) % 8
                P.f.append((b0 + k, b0 + kn, b0 + 8 + kn, b0 + 8 + k)); P.m.append(0); P.sm.append(None)
                P.uv.append([(k / 8 * 0.2, 0), ((k + 1) / 8 * 0.2, 0), ((k + 1) / 8 * 0.2, 0.1), (k / 8 * 0.2, 0.1)])
            P.f.append(tuple(b0 + 8 + k for k in range(8))); P.m.append(2); P.sm.append(False)
            P.uv.append([(0.5 + 0.4 * math.cos(k * math.tau / 8), 0.5 + 0.4 * math.sin(k * math.tau / 8)) for k in range(8)])
    ob = P.build(name, mats, coll, parent, smooth=True, uv_mode='given')
    ob.data.set_sharp_from_angle(angle=math.radians(38))
    return ob


def build(scene):
    mats = [KB.pbr_material('Bark'), KB.pbr_material('Wood'), KB.pbr_material('EndGrain'), KB.pbr_material('Moss')]
    extras = bpy.data.collections.new('KIT_Extras'); scene.collection.children.link(extras)
    coll = bpy.data.collections.new(MID); extras.children.link(coll)
    root = bpy.data.objects.new(MID, None); coll.objects.link(root); root.empty_display_type = 'ARROWS'; root.empty_display_size = 0.6
    cons = [dict(name='EntryConnector', role='entry', type='LOG_WALK', location=(0.0, 0.0, 0.0), heading_deg=0.0),
            dict(name='ExitConnector', role='exit', type='LOG_WALK', location=(L, 0.0, 0.0), heading_deg=0.0),
            dict(name='Seat_Entry', role='seat', type='BRIDGE_SEAT', location=(SEAT_L / 2, 0.0, SEAT_Z), heading_deg=0.0, partner='SM_Bridgehead_Base_A'),
            dict(name='Seat_Exit', role='seat', type='BRIDGE_SEAT', location=(L - SEAT_L / 2, 0.0, SEAT_Z), heading_deg=0.0, partner='SM_Bridgehead_Base_A (far bank, turned 180)')]
    root['kit_module_id'] = MID; root['kit_code'] = CODE; root['kit_version'] = K.KIT_VERSION; root['kit_connectors'] = json.dumps(cons)
    root['kit_pivot'] = 'centre of the walking strip at the entry end; bridgehead frame placement = translate (2, 0, +0.15)'
    made = [log_mesh(MID + '_Log_LOD0', 0.2, 8, 2, True, mats, coll, root, stubs=True),
            log_mesh(MID + '_Log_LOD1', 0.4, 5, 1, True, mats, coll, root),
            log_mesh(MID + '_Log_LOD2', 1.25, 3, 0, False, mats, coll, root)]
    box = KB.Parts(); KB.block(box, (L / 2, 0.0, SEAT_Z / 2), (L, 0.36, -SEAT_Z))
    col = box.build(MID + '_COL', [], coll, root); col.display_type = 'WIRE'; made.append(col)
    for o in made[1:]: o.hide_render = True; o.hide_set(True)
    return coll, root, made, cons


def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)


def validate(made):
    lod0 = made[0]; vs = [v.co.copy() for v in lod0.data.vertices]
    log_vs = vs[:len(ring_positions(0.2)) * len(ring_angles(0.0, 8, 2)[0])]
    top = [v for v in log_vs if v.z >= -1e-7]
    widths = {}
    for v in top: widths.setdefault(round(v.x, 4), []).append(v.y)
    inner = [max(ys) - min(ys) for x, ys in widths.items() if 0.0 < x < L]
    seat_vs = [v for v in vs if min(v.x, L - v.x) <= SEAT_L + 1e-6]
    seat_min = min(v.z for v in seat_vs); seat_contact = sum(1 for v in seat_vs if abs(v.z - SEAT_Z) < 1e-6)
    clear = []
    for v in vs:                                   # clearance above the bridgehead terrain (C08 / C02) in the bridgehead frame
        w = PLACE @ v
        if K.BASE_FACE_X < w.x < K.BH_RIVER_X: clear.append(w.z - K.c_H(w.x, w.y))
    R = {'walk_strip_max_abs_z_m': max(abs(v.z) for v in top), 'walk_strip_min_width_m': min(inner), 'walk_strip_max_width_m': max(inner),
         'seat_lowest_z_m': seat_min, 'seat_expected_z_m': SEAT_Z, 'seat_contact_vertices': seat_contact,
         'seat_in_bridgehead_frame_z_m': (PLACE @ Vector((0, 0, SEAT_Z))).z, 'c05_top_z_m': K.DECK_BOTTOM,
         'entry_top_in_bridgehead_frame_z_m': (PLACE @ Vector((0, 0, 0))).z, 'c01_exit_z_m': K.DECK_Z,
         'min_clearance_above_c08_c02_m': min(clear) if clear else None,
         'tris': {o.name: tris(o) for o in made}, 'lod0_tris': tris(lod0), 'budget': [800, 4000]}
    R['pass'] = (R['walk_strip_max_abs_z_m'] <= K.TOL and R['walk_strip_min_width_m'] >= 0.28 and R['seat_lowest_z_m'] >= SEAT_Z - K.TOL
                 and R['seat_contact_vertices'] > 20 and abs(R['seat_in_bridgehead_frame_z_m'] - K.DECK_BOTTOM) <= K.TOL
                 and abs(R['entry_top_in_bridgehead_frame_z_m'] - K.DECK_Z) <= K.TOL and (R['min_clearance_above_c08_c02_m'] or 1) > 0.02
                 and R['lod0_tris'] <= 4000)
    return R


def fit_ortho(cam, objs, d):
    """Orthographic scale that fits this view (a 10 m log seen end-on would otherwise be a dot)."""
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]; d = Vector(d).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.99 else Vector((0, 1, 0)); right = up.cross(d).normalized(); up = d.cross(right).normalized()
    w = max(p.dot(right) for p in pts) - min(p.dot(right) for p in pts); h = max(p.dot(up) for p in pts) - min(p.dot(up) for p in pts)
    cam.data.ortho_scale = max(w, h) * 1.12


def previews(scene, coll, made):
    view = bpy.data.scenes.new('LOG_Preview'); stu = bpy.data.collections.new('LOG_Studio'); view.collection.children.link(stu)
    KB.studio(view, stu, samples=12, transparent=False); view.collection.children.link(coll)
    cam = bpy.data.objects.new('LOG_Camera', bpy.data.cameras.new('LOG_Camera')); stu.objects.link(cam); view.camera = cam; cam.data.clip_end = 200
    view.view_layers[0].update()
    objs = [made[0]]; pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)]); centre = (lo + hi) / 2
    records = []
    for name, d in KB.VIEWS + [('11_persp_45', (-0.75, -1.0, 0.55)), ('12_detail', (-0.9, -1.0, 0.65))]:
        p = KB.new_output(PREV + '/' + name + '.png')
        if name.startswith('11'):
            view.cycles.samples = 32; cam.data.type = 'PERSP'; cam.data.lens = 38
            KB.look_at(cam, centre, d, (hi - lo).length / 2 / math.sin(math.atan(18 / 38)) * 1.03)
        elif name.startswith('12'):     # close look at the entry end: bark, adzed top, sawn end, seat notch, branch stub
            view.cycles.samples = 32; cam.data.type = 'PERSP'; cam.data.lens = 35
            KB.look_at(cam, Vector((1.1, 0.0, -0.12)), d, 2.9)
        else:
            view.cycles.samples = 12; cam.data.type = 'ORTHO'; fit_ortho(cam, objs, d); KB.look_at(cam, centre, d, 40)
        view.render.filepath = str(p); bpy.ops.render.render(write_still=True, scene=view.name)
        persp = name.startswith(('11', '12'))
        records.append({'file': name + '.png', 'direction': list(d), 'projection': 'perspective' if persp else 'orthographic',
                        'camera_location': list(cam.location), 'ortho_scale': None if persp else cam.data.ortho_scale})
    KB.kit_path(PREV, 'views.json').write_text(json.dumps({'module': MID, 'code': CODE, 'source': OUT_BLEND, 'same_geometry': True,
                                                           'note': 'Library view convention: 01_front looks from -Y. Orthographic scale fitted per view.',
                                                           'lod_rendered': 'LOD0', 'views': records}, indent=2))
    view.collection.children.unlink(coll)


def reimport_check(made, fbx):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(fbx), use_custom_normals=True)
    new = [o for o in bpy.data.objects if o not in before]; names = {EX.base_name(o.name): o for o in new}
    issues = []
    want = {o.name: tris(o) for o in made}
    if set(want) - set(names): issues.append('missing %s' % sorted(set(want) - set(names)))
    for n, t in want.items():
        if n in names and tris(names[n]) != t: issues.append('tris changed %s' % n)
    lo, hi = EX.world_bounds([o for o in made]); lo2, hi2 = EX.world_bounds([names[n] for n in want if n in names])
    err = max(max(abs(a - b) for a, b in zip(lo, lo2)), max(abs(a - b) for a, b in zip(hi, hi2)))
    if err > K.TOL: issues.append('bounds differ %.4f' % err)
    if any(n.startswith('TEST_') for n in names): issues.append('TEST object in FBX')
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    return {'objects': len(names), 'max_bounds_error_m': err, 'issues': issues, 'pass': not issues}


def sha(p):
    h = hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()


def main():
    scene = KB.start_session()
    out_blend = KB.new_output(OUT_BLEND); out_fbx = KB.new_output(OUT_FBX)
    for p in (PREV + '/views.json', PREV + '/model_info.json', PREV + '/validation.json'): KB.new_output(p)
    coll, root, made, cons = build(scene)
    bpy.context.view_layer.update()
    V = validate(made); print('VALIDATION', 'PASS' if V['pass'] else 'FAIL', json.dumps({k: v for k, v in V.items() if k != 'tris'}), flush=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend)); bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_mainfile()
    for o in made: o.hide_set(False)
    EX.select_only([root] + made); bpy.ops.export_scene.fbx(filepath=str(out_fbx), **EX.FBX_EXPORT)
    for o in made[1:]: o.hide_set(True)
    previews(scene, coll, made)
    RI = reimport_check(made, out_fbx); print('REIMPORT', 'PASS' if RI['pass'] else 'FAIL', RI, flush=True)
    lo, hi = EX.world_bounds(made[:1])
    info = {'id': MID, 'code': CODE, 'name_zh': NAME_ZH, 'group': 'D (extra, requested after the 29-module kit)', 'version': K.KIT_VERSION,
            'purpose': '一根削平頂面的原木獨木橋，長 10 m；行走面與 C01 坡道頂齊平，兩端底部削平擱在兩岸 C05 石基上。',
            'units': 'metre', 'up': '+Z', 'forward': '+X', 'pivot': root['kit_pivot'], 'bounds_min_m': lo, 'bounds_max_m': hi,
            'triangles': V['tris'], 'materials': ['M_Bark', 'M_Wood', 'M_EndGrain', 'M_Moss'], 'connectors': cons,
            'files': {'blend': OUT_BLEND, 'blend_sha256': sha(out_blend), 'fbx': OUT_FBX, 'fbx_sha256': sha(out_fbx), 'previews': PREV},
            'fits': 'two bridgeheads whose frames are 14 m apart, the far one turned 180 degrees (10 m between the C01 exits)'}
    KB.kit_path(PREV, 'model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2))
    KB.kit_path(PREV, 'validation.json').write_text(json.dumps({'module': MID, 'code': CODE, 'tolerance_m': K.TOL, 'geometry': V, 'fbx_blender_reimport': RI,
                                                                 'overall_pass': V['pass'] and RI['pass'],
                                                                 'not_verified': ['Unity / Unreal import', 'in-engine walking on the log', 'performance']},
                                                                ensure_ascii=False, indent=2, default=float))
    Path(str(out_blend).replace('.blend', '.build.json')).write_text(json.dumps({'modules': {MID: {'tris': V['tris'], 'lod0_tris': V['lod0_tris']}}}, indent=2))
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
