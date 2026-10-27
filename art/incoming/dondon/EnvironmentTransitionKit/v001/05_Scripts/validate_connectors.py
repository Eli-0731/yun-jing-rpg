"""Automatic connector and assembly QA (PHASE 2 / 5).

  blender -b --python-exit-code 1 --python 05_Scripts/validate_connectors.py -- \
      --files 01_Blender/Blockout/blockout_representatives_v01.blend --name blockout_representatives [--render]

Runs in a fresh session.  The kit files are LINKED (read-only), never saved.  Writes
06_Reports/qa/<name>.json, assembly renders to 04_Previews/AssemblyTests/<name>_*.png and an assembly
scene 04_Previews/AssemblyTests/<name>_assembly.blend that links the kit files.  Refuses to overwrite.

Checks (tolerance kit_spec.TOL = 1 mm):
  1. every connector of every built module: mesh vertices vs the spec vertex sequence, no extra vertices on
     the connector line, Mask colours vs the spec masks, mesh normals vs the analytic surface normals;
  2. chains: each module placed on the previous module's exit transform, exit vs entry vertices, masks
     and normals compared in world space;
  3. pairs: A01 + TEST_RoadCore_3m + A02, C01 exit on the test deck, B01 on both C02 bank connectors,
     bridgehead internal seams;
  4. per module: triangle count, UVs, Mask attribute, object naming, identity child transforms;
  5. details (stones, grass, sod, masonry) never cross an entry/exit connector plane.
"""
import sys, math, json
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K
import kit_blender as KB

DEG = math.degrees


def cli():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def get(k, d=None): return a[a.index(k) + 1] if k in a else d
    return get('--files').split(','), get('--name'), '--render' in a


# ---- module data -------------------------------------------------------------------------------------
class Mod:
    def __init__(self, coll):
        self.coll = coll; self.id = coll.name; self.spec = K.BY_ID[self.id]
        self.root = next(o for o in coll.objects if o.type == 'EMPTY' and o.name == self.id)
        self.objs = [o for o in coll.objects if o.type == 'MESH']
        self.terrain = next((o for o in self.objs if o.name == self.id + '_Terrain_LOD0'), None)
        self.slot = Vector(self.root.location)
        if self.terrain:
            me = self.terrain.data
            self.verts = [v.co.copy() for v in me.vertices]
            self.kd = KDTree(len(self.verts))
            for i, p in enumerate(self.verts): self.kd.insert(p, i)
            self.kd.balance()
            ca = me.color_attributes.get('Mask')
            self.mask = [tuple(d.color) for d in ca.data] if ca else None
            loop_of = {}
            for li, lp in enumerate(me.loops): loop_of.setdefault(lp.vertex_index, li)
            cn = me.corner_normals
            self.normal = {vi: Vector(cn[li].vector) for vi, li in loop_of.items()}
        else:
            self.verts = []

    def surfaces(self):
        m = self.spec
        if m['kind'] == 'c_base': return []
        return [K.Surface(m, i) for i in range(len(m['parts']))] if m['kind'] == 'c_grid' else [K.Surface(m)]


def spec_normal(sf, u, v, h=1e-4):
    def P(uu, vv):
        x, y = sf.xy(uu, vv); return Vector((x, y, sf.z(uu, vv)))
    return (P(u + h, v) - P(u - h, v)).cross(P(u, v + h) - P(u, v - h)).normalized()


def param_of(mod, p):
    """(surface, u, v) of a module-local point on its lattice (exact lattice positions)."""
    best = None
    for sf in mod.surfaces():
        for u in sf.us:
            for v in sf.vs:
                x, y = sf.xy(u, v); d = (x - p.x) ** 2 + (y - p.y) ** 2
                if best is None or d < best[0]: best = (d, sf, u, v)
    return best[1], best[2], best[3]


def seg_dist2(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]; dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    qx, qy = ax + t * dx, ay + t * dy
    return (p[0] - qx) ** 2 + (p[1] - qy) ** 2


def check_connector(mod, con):
    exp = [Vector(p) for p in con['vertices']]
    if not mod.terrain or con['type'] == 'BRIDGE_SEAT':
        return None
    pos_err = 0.0; mask_err = 0.0; nrm_err = 0.0; matched = []
    for e in exp:
        co, idx, d = mod.kd.find(e); pos_err = max(pos_err, d); matched.append(idx)
        sf, u, v = param_of(mod, e)
        if mod.mask:
            mk = sf.mask(u, v); mask_err = max(mask_err, max(abs(a - min(1.0, max(0.0, b))) for a, b in zip(mod.mask[idx], mk)))
        n = mod.normal.get(idx)
        if n is not None:
            nrm_err = max(nrm_err, DEG(n.angle(spec_normal(sf, u, v), 0.0)))
    on_line = 0
    if len(exp) > 1:
        # a connector may consist of separate runs (e.g. the two corner pieces); never bridge a gap
        segs = [(a, b) for a, b in zip(exp, exp[1:]) if (a - b).length < 0.3]
        for p in mod.verts:
            if min(seg_dist2(p, a, b) for a, b in segs) < 1e-10: on_line += 1
    return {'connector': con['name'], 'type': con['type'], 'expected_vertices': len(exp), 'vertices_on_line': on_line,
            'max_position_error_m': pos_err, 'max_mask_error': mask_err, 'max_normal_error_deg': nrm_err,
            'pass': pos_err <= K.TOL and (on_line == len(exp) or len(exp) == 1) and mask_err <= 0.01 and nrm_err <= 0.5}


def placed(mod, T):
    """World matrix that puts the module pivot at T (the root sits at its layout slot inside the kit file)."""
    return T


def exit_matrix(mod, T):
    tf = K.exit_transform(mod.spec)
    (x, y, z), hd = tf
    return T @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(hd), 4, 'Z')


def compare_sets(ma, Ta, ca, mb, Tb, cb, use_mask=True):
    """Compare connector ca of module a (world Ta) with connector cb of module b (world Tb)."""
    va = [Ta @ Vector(p) for p in ca['vertices']]; vb = [Tb @ Vector(p) for p in cb['vertices']]
    kd = KDTree(len(vb))
    for i, p in enumerate(vb): kd.insert(p, i)
    kd.balance()
    pos = 0.0; mask = 0.0; nrm = 0.0
    ra = Ta.to_3x3(); rb = Tb.to_3x3()
    for i, p in enumerate(va):
        q, j, d = kd.find(p); pos = max(pos, d)
        ia = ma.kd.find(Vector(ca['vertices'][i]))[1] if ma.terrain else None
        ib = mb.kd.find(Vector(cb['vertices'][j]))[1] if mb.terrain else None
        if ia is not None and ib is not None:
            if use_mask and ma.mask and mb.mask:
                mask = max(mask, max(abs(x - y) for x, y in zip(ma.mask[ia], mb.mask[ib])))
            na, nb = ma.normal.get(ia), mb.normal.get(ib)
            if na is not None and nb is not None:
                nrm = max(nrm, DEG((ra @ na).angle(rb @ nb, 0.0)))
    return {'max_position_error_m': pos, 'max_mask_error': mask if use_mask else None, 'max_normal_error_deg': nrm,
            'count_a': len(va), 'count_b': len(vb),
            'pass': pos <= K.TOL and len(va) == len(vb) and (not use_mask or mask <= 0.01) and nrm <= 0.5}


def con_by_name(mod, name):
    """'Name', 'Name[a:b]' or 'A+B' (concatenated)."""
    out = []
    for part in name.split('+'):
        nm = part.split('[')[0]
        c = next(c for c in K.connectors(mod.spec) if c['name'] == nm)
        vs = c['vertices']
        if '[' in part:
            a, b = part[part.index('[') + 1:-1].split(':'); vs = vs[int(a) if a else None:int(b) if b else None]
        out += vs
    return {'name': name, 'vertices': out, 'type': 'BRIDGEHEAD_FIELD'}


def module_stats(mod):
    tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in mod.objs}
    lod0 = sum(t for n, t in tris.items() if n.endswith('_LOD0'))
    issues = []
    for o in mod.objs:
        if not o.data.uv_layers: issues.append('no UV: ' + o.name)
        if o.parent != mod.root: issues.append('not parented to root: ' + o.name)
        if max(abs(o.matrix_local[i][j] - (1.0 if i == j else 0.0)) for i in range(4) for j in range(4)) > 1e-9: issues.append('non-identity transform: ' + o.name)
        if not o.name.startswith(mod.id + '_'): issues.append('naming: ' + o.name)
        if o.name.startswith('TEST_'): issues.append('test object inside module: ' + o.name)
    if mod.terrain and 'Mask' not in mod.terrain.data.color_attributes: issues.append('terrain has no Mask attribute')
    lo, hi = K.tri_budget(mod.spec)
    return {'objects': len(mod.objs), 'lod0_tris': lod0, 'budget': [lo, hi], 'within_budget_max': lod0 <= hi,
            'tris_by_object': tris, 'issues': issues}


DETAIL_TAGS = ('_DET_', '_Rocks_LOD0', '_SodLip_LOD0', '_Masonry_LOD0')


def detail_containment(mod):
    """Details (stones, grass cards, sod lips, masonry) must stay behind every entry/exit connector plane,
    so a neighbouring module's terrain and details are never intruded upon.  Returns the worst protrusion (m)."""
    out = []
    planes = [(c['name'], Vector(c['location']), Vector((math.cos(math.radians(c['heading_deg'])), math.sin(math.radians(c['heading_deg'])), 0.0)),
               1.0 if c['role'] == 'exit' else -1.0) for c in K.connectors(mod.spec) if c['role'] in ('entry', 'exit')]
    for o in mod.objs:
        if not any(t in o.name for t in DETAIL_TAGS): continue
        for name, loc, d, sgn in planes:
            worst = max(sgn * (v.co - loc).dot(d) for v in o.data.vertices)
            out.append({'object': o.name, 'connector': name, 'protrusion_m': max(0.0, worst)})
    worst = max([r['protrusion_m'] for r in out] or [0.0])
    return {'max_protrusion_m': worst, 'pass': worst <= K.TOL, 'worst': sorted(out, key=lambda r: -r['protrusion_m'])[:3]}


# ---- assembly scenes (rendered) ------------------------------------------------------------------------
def instance(scene, coll, mod, T, name):
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = mod.coll
    e.matrix_world = T @ Matrix.Translation(-mod.slot); scene.collection.objects.link(e); return e


def flat(scene, name, verts, faces, mat):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return ob


def road_core(scene, T, mat, name):
    us = K.steps(0.0, 4.0, 0.25); vs = K.CORE_V; nv = len(vs)
    verts = [tuple(T @ Vector((u, v, 0.0))) for u in us for v in vs]
    faces = [(i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1) for i in range(len(us) - 1) for j in range(nv - 1)]
    return flat(scene, name, verts, faces, mat)


def render_views(scene, name, bounds, out_dir, views):
    lo, hi = bounds; centre = (lo + hi) / 2; ext = hi - lo; files = []
    cam = bpy.data.objects.new('QA_Camera', bpy.data.cameras.new('QA_Camera')); scene.collection.objects.link(cam); scene.camera = cam
    scene.render.resolution_x = 1600; scene.render.resolution_y = 1000
    for tag, d, persp in views:
        if persp:
            cam.data.type = 'PERSP'; cam.data.lens = 30; dist = max(ext.x, ext.y) * 1.25 + 4
            KB.look_at(cam, centre, d, dist)
        else:
            cam.data.type = 'ORTHO'; KB.look_at(cam, centre, d, 60)
            span_h = ext.x if abs(d[0]) < 0.5 else ext.y
            cam.data.ortho_scale = max(span_h, (ext.y if d[2] > 0.9 else ext.z * 3) * 1.6) * 1.12
        cam.data.clip_end = 500
        path = KB.new_output(str(Path(out_dir) / ('%s_%s.png' % (name, tag)))); scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True, scene=scene.name); files.append(str(path.relative_to(KB.KIT_DIR)))
    return files


def main():
    files, name, render = cli()
    scene = KB.start_session()
    out_json = KB.new_output('06_Reports/qa/%s.json' % name)
    mods = {}
    for f in files:
        path = KB.kit_path(f)
        with bpy.data.libraries.load(str(path), link=True) as (src, dst):
            dst.collections = [c for c in src.collections if c.startswith('SM_')]
        for c in dst.collections:
            mods[c.name] = Mod(c)
    print('LINKED', sorted(m.spec['code'] for m in mods.values()), flush=True)
    R = {'name': name, 'files': files, 'blender': bpy.app.version_string, 'tolerance_m': K.TOL, 'modules': {}, 'chains': [], 'pairs': []}
    # 1. connectors per module
    for mid, mod in sorted(mods.items(), key=lambda kv: kv[1].spec['code']):
        cons = [check_connector(mod, c) for c in K.connectors(mod.spec)]
        R['modules'][mid] = {'code': mod.spec['code'], 'connectors': [c for c in cons if c], 'stats': module_stats(mod), 'details': detail_containment(mod)}
        ok = all(c['pass'] for c in cons if c) and not R['modules'][mid]['stats']['issues'] and R['modules'][mid]['details']['pass']
        R['modules'][mid]['pass'] = ok
        print('MODULE', mod.spec['code'], 'PASS' if ok else 'FAIL', max([c['max_position_error_m'] for c in cons if c] or [0]), 'details', '%.4f' % R['modules'][mid]['details']['max_protrusion_m'], R['modules'][mid]['stats']['lod0_tris'], flush=True)
    # 2. chains
    for title, chain in K.CHAIN_TESTS:
        if not all(c in mods for c in chain): continue
        T = Matrix.Identity(4); steps = []
        for a, b in zip(chain, chain[1:]):
            ma, mb = mods[a], mods[b]; Te = exit_matrix(ma, T)
            ea = next(c for c in K.connectors(ma.spec) if c['name'] == 'ExitConnector')
            eb = next(c for c in K.connectors(mb.spec) if c['name'] == 'EntryConnector')
            same_variant = ea.get('surface_variant') is None
            res = compare_sets(ma, T, ea, mb, Te, eb, use_mask=same_variant); res.update(a=ma.spec['code'], b=mb.spec['code'])
            steps.append(res); T = Te
        R['chains'].append({'chain': title, 'steps': steps, 'pass': all(s['pass'] for s in steps)})
        print('CHAIN', title, 'PASS' if R['chains'][-1]['pass'] else 'FAIL', flush=True)
    # 3. pairs
    I = Matrix.Identity(4)
    if 'SM_RoadEdge_Straight_L_A' in mods or 'SM_RoadEdge_Straight_R_A' in mods:
        for mid in ('SM_RoadEdge_Straight_L_A', 'SM_RoadEdge_Straight_R_A'):
            if mid not in mods: continue
            m = mods[mid]; c = next(c for c in K.connectors(m.spec) if c['name'] == 'CoreSeam'); v = c['vertices'][0][1]
            core = [(u, v, 0.0) for u in K.steps(0.0, 4.0, 0.25)]
            err = max((Vector(p) - Vector(q)).length for p, q in zip(sorted(c['vertices']), sorted(core)))
            mesh_err = max(m.kd.find(Vector(p))[2] for p in core)
            R['pairs'].append({'pair': '%s CoreSeam + TEST_RoadCore_3m' % m.spec['code'], 'max_position_error_m': max(err, mesh_err), 'pass': max(err, mesh_err) <= K.TOL})
    if 'SM_Bridgehead_RoadTransition_A' in mods:
        m = mods['SM_Bridgehead_RoadTransition_A']; c = next(c for c in K.connectors(m.spec) if c['name'] == 'ExitConnector')
        dz = max(abs(m.kd.find(Vector(p))[0].z - K.DECK_Z) for p in c['vertices'])
        R['pairs'].append({'pair': 'C01 exit on TEST_BridgeDeck_3m top (+0.15)', 'max_position_error_m': dz, 'pass': dz <= K.TOL})
    if 'SM_Bridgehead_BankTransition_A' in mods and 'SM_Riverbank_Straight_A' in mods:
        c2, b1 = mods['SM_Bridgehead_BankTransition_A'], mods['SM_Riverbank_Straight_A']
        ent = next(c for c in K.connectors(c2.spec) if c['name'] == 'EntryConnector'); ex = next(c for c in K.connectors(c2.spec) if c['name'] == 'ExitConnector')
        bex = next(c for c in K.connectors(b1.spec) if c['name'] == 'ExitConnector'); ben = next(c for c in K.connectors(b1.spec) if c['name'] == 'EntryConnector')
        R90 = Matrix.Rotation(math.radians(90), 4, 'Z')
        Tin = Matrix.Translation((K.BANK_LINE_X, -K.BH_BANK_A, 0)) @ R90 @ Matrix.Translation((-4.0, 0, 0))
        Tout = Matrix.Translation((K.BANK_LINE_X, K.BH_BANK_A, 0)) @ R90
        r1 = compare_sets(b1, Tin, bex, c2, I, ent); r1['pair'] = 'B01 exit -> C02 entry (3, -4) heading 90'
        r2 = compare_sets(c2, I, ex, b1, Tout, ben); r2['pair'] = 'C02 exit (3, +4) -> B01 entry'
        R['pairs'] += [r1, r2]
    for a, ca, b, cb in K.FIELD_SEAMS:
        if a in mods and b in mods:
            r = compare_sets(mods[a], I, con_by_name(mods[a], ca), mods[b], I, con_by_name(mods[b], cb)); r['pair'] = '%s.%s = %s.%s' % (K.BY_ID[a]['code'], ca, K.BY_ID[b]['code'], cb)
            R['pairs'].append(r)
    for p in R['pairs']: print('PAIR', p['pair'], 'PASS' if p['pass'] else 'FAIL', '%.6f' % p['max_position_error_m'], flush=True)
    R['pass'] = all(m['pass'] for m in R['modules'].values()) and all(c['pass'] for c in R['chains']) and all(p['pass'] for p in R['pairs'])
    # 4. assembly renders: one scene per layout, three views each
    if render:
        R['renders'] = {}
        mt = KB.test_material(); water = KB.flat_material('M_TEST_Water', (0.10, 0.22, 0.24), 0.08); deck = KB.test_material('M_TEST_Deck', (0.42, 0.40, 0.50))
        R90 = Matrix.Rotation(math.radians(90), 4, 'Z')
        def chain_place(chain, T0, scn, pts):
            T = T0
            for i, mid in enumerate(chain):
                if mid not in mods: return
                instance(scn, None, mods[mid], T, 'QA_%s_%d' % (mid, i)); pts += [T @ p for p in mods[mid].verts[::5]]
                if i < len(chain) - 1: T = exit_matrix(mods[mid], T)
        layouts = []
        if all(m in mods for m in ('SM_RoadEdge_Straight_L_A', 'SM_RoadEdge_Straight_R_A', 'SM_Bridgehead_RoadTransition_A')):
            layouts.append('road_bridgehead')
        if 'SM_RoadEdge_Curve_L_A' in mods: layouts.append('road_chain')
        if 'SM_Riverbank_InnerCorner_A' in mods: layouts.append('bank_chain')
        for lay in layouts:
            scn = bpy.data.scenes.new('QA_' + lay)
            KB.studio(scn, scn.collection, samples=24, transparent=False); pts = []
            if lay == 'road_bridgehead':
                for i in range(3):
                    T = Matrix.Translation((-12.0 + 4.0 * i, 0, 0))
                    for mid in ('SM_RoadEdge_Straight_L_A', 'SM_RoadEdge_Straight_R_A'):
                        instance(scn, None, mods[mid], T, 'QA_%s_%d' % (mid, i)); pts += [T @ p for p in mods[mid].verts[::5]]
                    road_core(scn, T, mt, 'QA_TEST_RoadCore_%d' % i)
                for mid, mod in mods.items():
                    if mod.spec['group'] == 'C' and mod.spec['kind'] != 'c06':
                        instance(scn, None, mod, I, 'QA_' + mid); pts += [p for p in mod.verts[::5]]
                flat(scn, 'QA_TEST_BridgeDeck_3m', [(2, -1.5, K.DECK_Z), (8, -1.5, K.DECK_Z), (8, 1.5, K.DECK_Z), (2, 1.5, K.DECK_Z)], [(0, 1, 2, 3)], deck)
                if 'SM_Riverbank_Straight_A' in mods:
                    b1 = mods['SM_Riverbank_Straight_A']
                    for i, T in enumerate((Matrix.Translation((3, -4, 0)) @ R90 @ Matrix.Translation((-4.0, 0, 0)), Matrix.Translation((3, 4, 0)) @ R90)):
                        instance(scn, None, b1, T, 'QA_B01_%d' % i); pts += [T @ p for p in b1.verts[::5]]
                if 'SM_Bridgehead_SlopeFix_A' in mods:
                    T = Matrix.Translation((-4.0, -7.0, 0))
                    flat(scn, 'QA_TEST_DeckEnd', [(-7.5, -8.5, K.DECK_Z), (-4.0, -8.5, K.DECK_Z), (-4.0, -5.5, K.DECK_Z), (-7.5, -5.5, K.DECK_Z)], [(0, 1, 2, 3)], deck)
                    instance(scn, None, mods['SM_Bridgehead_SlopeFix_A'], T, 'QA_C06'); pts += [T @ p for p in mods['SM_Bridgehead_SlopeFix_A'].verts[::3]]
                flat(scn, 'QA_TEST_Water_-0.8', [(3.0, -8.5, K.WATER_Z), (9.0, -8.5, K.WATER_Z), (9.0, 8.5, K.WATER_Z), (3.0, 8.5, K.WATER_Z)], [(0, 1, 2, 3)], water)
            elif lay == 'road_chain':
                chain = ['SM_RoadEdge_Slope_A', 'SM_RoadEdge_Curve_L_A', 'SM_RoadEdge_Curve_R_A', 'SM_RoadEdge_WideCurve_L_A', 'SM_RoadEdge_WideCurve_R_A',
                         'SM_RoadEdge_Damaged_A', 'SM_RoadEdge_StoneTransition_A']
                chain_place(chain, I, scn, pts)
                chain_place(['SM_RoadEdge_Curve_R_A', 'SM_RoadEdge_GrassTransition_A'], Matrix.Translation((0, -9, 0)), scn, pts)
                chain_place(['SM_RoadEdge_Curve_L_A', 'SM_RoadEdge_End_A'], Matrix.Translation((14, -9, 0)), scn, pts)
            elif lay == 'bank_chain':
                chain = ['SM_Riverbank_Straight_A', 'SM_Riverbank_InnerCorner_A', 'SM_Riverbank_Straight_B', 'SM_Riverbank_OuterCorner_A', 'SM_Riverbank_Slope_A',
                         'SM_Riverbank_Steep_A', 'SM_Riverbank_RockReinforced_A', 'SM_Riverbank_GrassHeavy_A', 'SM_Riverbank_Eroded_A', 'SM_Riverbank_End_A']
                chain_place(chain, I, scn, pts)
                lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
                flat(scn, 'QA_TEST_Water_-0.8', [(lo.x - 1, lo.y - 1, K.WATER_Z), (hi.x + 1, lo.y - 1, K.WATER_Z), (hi.x + 1, hi.y + 1, K.WATER_Z), (lo.x - 1, hi.y + 1, K.WATER_Z)], [(0, 1, 2, 3)], water)
            lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
            R['renders'][lay] = render_views(scn, '%s_%s' % (name, lay), (lo, hi), '04_Previews/AssemblyTests',
                                             [('45deg', (-1.0, -1.25, 1.0), True), ('top', (0, 0, 1), False), ('side', (0, -1, 0.0), False)])
        if layouts:
            asm = KB.new_output('04_Previews/AssemblyTests/%s_assembly.blend' % name)
            bpy.ops.wm.save_as_mainfile(filepath=str(asm), relative_remap=True)
            R['renders']['assembly_blend'] = str(asm.relative_to(KB.KIT_DIR))
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(R, indent=2, default=float))
    print('RESULT', 'PASS' if R['pass'] else 'FAIL', out_json, flush=True)


if __name__ == '__main__':
    main()
