"""VL roof (work pack B-104h part 2): the StarterHouse v004 curved gable roof rebuilt as pan and roll tiles.

StarterHouse roof (build_starter_house.py, kept as is): roof_z(x, t) = 3.40 + 1.60 (1 - t)^1.35 + .18 t^8 + .25 (|x| / 4.3)^8,
t = 0 at the ridge, 1 at the eave; the front slope reaches y = -3.95 (over the porch), the back slope y = +3.45; x from -4.3 to 4.3.

Tiles (group 'Roof', not baked): pan rows with roll rows over the joints, 12 courses per slope, each course steps up 16 mm at its eave
end (the upper tile lies on the lower one). They read their own UVs on one shared 1024 tile texture of eight cells (VL_Shared/Textures):
  pans 0 old, 1 darker firing, 2 mossy, 3 new (paler, VL02) | rolls 4 old, 5 darker, 6 mossy, 7 new.
A cell is 1/8 wide and holds three courses top to bottom (a lip band at the foot of each), so a course's cell and slot are chosen per
tile and the course steps hide the texture seams. The cells are baked once from the cr_mats tile shader on the same course geometry.
LODs are built, not decimated (lod_mask bit per LOD): LOD0 pans 4 / rolls 4 segments across, LOD1 2 / 2, LOD2 three courses per strip,
flat pans, 2-segment rolls (the painted lips carry the courses).
Underlay boards (Wood atlas), barge boards, eave rafters, ridge (Main atlas) are ordinary baked parts.
"""
import bpy, bmesh, math, random
import numpy as np
from pathlib import Path
from mathutils import Vector
from ti_core import S, mesh
import ti_mats as tm
import cr_mats as cm

ART = Path(__file__).resolve().parents[2]
TILE_DIR = ART / 'exports' / 'village-houses-b' / 'VL_Shared' / 'Textures'
TILE_PX = 1024
DEPTH = {-1: 3.95, 1: 3.45}
N_COURSE = 12
PITCH = .2389
PAN_X0 = -4.30
N_PAN = 37                      # pan centres -4.30 .. +4.30
N_ROLL = 38                     # roll centres -4.4195 .. +4.4195 (over every pan joint, plus the two gable edges)
PAN_HW, PAN_SAG = .117, .018
ROLL_HW, ROLL_H, ROLL_BASE = .07, .055, -.008
LIFT = .016
LIP = .02                       # v band (in cell units) for the lip of each course
E_T = .0015                     # gap in t between a course's ridge end and the next course's raised eave end
UNDER_TOP, UNDER_T = -.035, .1


def roof_z(x, t): return 3.40 + 1.60 * max(0., 1 - t) ** 1.35 + .18 * t ** 8 + .25 * (abs(x) / 4.3) ** 8


def pan_x(j): return PAN_X0 + j * PITCH
def roll_x(i): return PAN_X0 - PITCH / 2 + i * PITCH


def course_t(k, n=N_COURSE):
    """(t at the raised eave end, t at the ridge end) of course k (0 = eave course)."""
    return 1 - k / n, 1 - (k + 1) / n + E_T


# ------------------------------------------------------------------ tile geometry (shared by the cell bake and the roof)
def _profile(kind, nu):
    """[(u in -1..1, dx, dz)] across one tile."""
    out = []
    for i in range(nu + 1):
        u = -1 + 2 * i / nu
        if kind == 'pan':
            out.append((u, u * PAN_HW, -PAN_SAG * (1 - u * u) if nu > 1 else -PAN_SAG * .45))
        else:
            a = math.pi * (1 - i / nu)
            out.append((u, ROLL_HW * math.cos(a), ROLL_BASE + ROLL_H * math.sin(a)))
    return out


def strip(V, F, UV, M, place, kind, nu, courses, cell_of, slot_of, mask, group=1, jit=None):
    """One column of tiles. place(dx, t, dz) -> xyz. courses: course indices from the eave. group: courses per strip (LOD2: 3).
    Appends faces with per-corner UVs and the lod mask."""
    prof = _profile(kind, nu)
    k = 0; ks = list(courses)
    runs, cur = [], []
    for c in ks:                                  # consecutive runs (holes split the column)
        if cur and c != cur[-1] + 1: runs.append(cur); cur = []
        cur.append(c)
    if cur: runs.append(cur)
    for run in runs:
        prev_ridge = None
        i = 0
        while i < len(run):
            grp = run[i:i + group] if group > 1 else [run[i]]
            if group > 1 and (len(grp) < group or grp[0] % group): grp = [run[i]]     # LOD2 strips start on a whole group
            k0, k1 = grp[0], grp[-1]
            ta, _ = course_t(k0); _, tb = course_t(k1)
            cell = cell_of(k0); U0, U1 = cell / 8 + 2. / TILE_PX, (cell + 1) / 8 - 2. / TILE_PX
            if len(grp) == 1:
                s = slot_of(k0); va, vb, vl = s / 3 + LIP, (s + 1) / 3, s / 3
            else:
                va, vb, vl = LIP, 1., 0.
            j = jit(k0) if jit else (0., 0.)
            A = [len(V) + q for q in range(nu + 1)]
            V.extend(place(dx + j[0], ta, dz + LIFT + j[1]) for _, dx, dz in prof)
            B = [len(V) + q for q in range(nu + 1)]
            V.extend(place(dx + j[0], tb, dz + j[1]) for _, dx, dz in prof)
            if prev_ridge is None:
                R = [len(V) + q for q in range(nu + 1)]   # the eave lip of the first course: straight down 20 mm
                V.extend(place(dx + j[0], ta + .0005, dz + LIFT + j[1] - .022) for _, dx, dz in prof)
            else:
                R = prev_ridge
            for q in range(nu):
                ua, ub = U0 + (prof[q][0] + 1) / 2 * (U1 - U0), U0 + (prof[q + 1][0] + 1) / 2 * (U1 - U0)
                F.append((A[q], A[q + 1], B[q + 1], B[q])); UV.append(((ua, va), (ub, va), (ub, vb), (ua, vb))); M.append(mask)
                F.append((R[q], R[q + 1], A[q + 1], A[q])); UV.append(((ua, vl), (ub, vl), (ub, va), (ua, va))); M.append(mask)
            prev_ridge = B
            i += len(grp)


def uv_part(name, V, F, UV, M, mat, group='Roof', **kw):
    o = mesh(name, V, F, mat, smooth=True, group=group, grain='y', **kw)
    me = o.data; uvl = me.uv_layers.active
    for poly in me.polygons:
        for c, li in enumerate(poly.loop_indices): uvl.data[li].uv = UV[poly.index][c]
    at = me.attributes.new('lod_mask', 'INT', 'FACE'); at.data.foreach_set('value', M)
    return o


# ------------------------------------------------------------------ the eight cells, baked once
def _bake_cells():
    """Course geometry of every cell laid flat, the cr_mats tile shader on it, baked into the cells (colour, roughness, normal)."""
    TILE_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
    col = bpy.data.collections.new('TileCellBake'); scene.collection.children.link(col)
    mats = [cm.tile('Cell_Old', base=(.061, .084, .078), light=(.111, .147, .144), moss=0., edge_amt=.55),
            cm.tile('Cell_Dark', base=(.045, .058, .062), light=(.085, .105, .11), moss=0., edge_amt=.45),
            cm.tile('Cell_Moss', base=(.061, .084, .078), light=(.111, .147, .144), moss=1.6, edge_amt=.4),
            cm.tile('Cell_New', base=(.105, .13, .13), light=(.2, .235, .225), moss=0., edge_amt=.6)]
    objs = []
    for cell in range(8):
        kind = 'pan' if cell < 4 else 'roll'
        V, F, UV, M = [], [], [], []
        x0 = cell * .6
        place = lambda dx, t, dz, x0=x0: (x0 + dx, (1 - t) * N_COURSE * .32, dz)
        strip(V, F, UV, M, place, kind, 8, range(3), lambda k, c=cell: c, lambda k: k, 1)
        me = bpy.data.meshes.new(f'cell{cell}'); me.from_pydata(V, [], F); me.update()
        uvl = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for c, li in enumerate(poly.loop_indices): uvl.data[li].uv = UV[poly.index][c]
        for p in me.polygons: p.use_smooth = True
        o = bpy.data.objects.new(f'cell{cell}', me); col.objects.link(o)
        n = len(me.vertices); rnd = random.Random(cell)
        for nm, vec in (('gA', (0, 1, 0)), ('gB', (1, 0, 0)), ('gC', (0, 0, 1))):
            a = me.attributes.new(nm, 'FLOAT_VECTOR', 'POINT'); a.data.foreach_set('vector', list(vec) * n)
        a = me.attributes.new('part_rand', 'FLOAT', 'POINT'); a.data.foreach_set('value', [rnd.random()] * n)
        me.materials.append(mats[cell % 4]); objs.append(o)
    imgs = {}
    for label, node_name, color in (('BaseColor', 'OUT_COLOR', True), ('Roughness', 'OUT_ROUGH', False), ('Normal', None, False)):
        img = bpy.data.images.new(f'VL_RoofTiles_{label}', TILE_PX, TILE_PX, alpha=False, float_buffer=not color)
        if not color: img.colorspace_settings.name = 'Non-Color'
        scene.cycles.samples = 16 if color else 4
        scene.render.bake.margin = 6; scene.render.bake.use_clear = True
        for m in mats:
            nt = m.node_tree; tn = nt.nodes.new('ShaderNodeTexImage'); tn.name = 'BAKE_TARGET'; tn.image = img; nt.nodes.active = tn
            if node_name:
                em = nt.nodes.new('ShaderNodeEmission'); em.name = 'BAKE_EMIT'; src = nt.nodes[node_name].outputs[0]
                if src.type == 'VALUE':
                    cmb = nt.nodes.new('ShaderNodeCombineColor'); cmb.name = 'BAKE_CMB'
                    for i in range(3): nt.links.new(src, cmb.inputs[i])
                    src = cmb.outputs[0]
                nt.links.new(src, em.inputs['Color']); nt.links.new(em.outputs[0], nt.nodes['OUTPUT'].inputs['Surface'])
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if node_name: bpy.ops.object.bake(type='EMIT')
        else: bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT')
        for m in mats:
            nt = m.node_tree
            for nm in ('BAKE_TARGET', 'BAKE_EMIT', 'BAKE_CMB'):
                if nm in nt.nodes: nt.nodes.remove(nt.nodes[nm])
            bs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
            nt.links.new(bs.outputs[0], nt.nodes['OUTPUT'].inputs['Surface'])
        img.filepath_raw = str(TILE_DIR / f'VL_RoofTiles_{label}.png'); img.file_format = 'PNG'; img.save(); imgs[label] = img
    rg = np.array(imgs['Roughness'].pixels[:], np.float32).reshape(TILE_PX, TILE_PX, 4)
    ms = np.zeros_like(rg); ms[..., 3] = 1 - rg[..., 0]
    im = bpy.data.images.new('VL_RoofTiles_MetallicSmoothness', TILE_PX, TILE_PX, alpha=True, float_buffer=True); im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(ms.ravel()); im.filepath_raw = str(TILE_DIR / 'VL_RoofTiles_MetallicSmoothness.png'); im.file_format = 'PNG'; im.save()
    for o in objs: bpy.data.objects.remove(o)
    bpy.data.collections.remove(col)
    for m in mats: MAT_DROP(m)
    print('TILE_CELLS_BAKED', TILE_DIR, flush=True)


def MAT_DROP(m):
    tm.MAT_INFO.pop(m.name, None); bpy.data.materials.remove(m)


def roof_material(force=False):
    if force or not (TILE_DIR / 'VL_RoofTiles_Normal.png').exists(): _bake_cells()
    m = bpy.data.materials.new('VL_RoofTiles'); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    def img(label, color):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(str(TILE_DIR / f'VL_RoofTiles_{label}.png'), check_existing=True)
        if not color: n.image.colorspace_settings.name = 'Non-Color'
        return n
    nt.links.new(img('BaseColor', True).outputs['Color'], bs.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(img('Normal', False).outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs[0], bs.inputs['Normal'])
    nt.links.new(img('Roughness', False).outputs['Color'], bs.inputs['Roughness'])
    bs.inputs['Specular IOR Level'].default_value = .3
    tm.MAT_INFO[m.name] = {'slot': 'RoofTiles', 'own_uv': True}
    return m


# ------------------------------------------------------------------ the tiled slopes
def tiles(P, side, hole=lambda side, x, k: False, cell=None):
    """Pans and rolls of one slope at the three LODs. hole(side, x, course) drops a tile; a roll goes when a pan beside it goes."""
    R = random.Random(f'tiles{side}'); D = DEPTH[side]
    def place(x0):
        return lambda dx, t, dz: (x0 + (dx if side < 0 else -dx), side * t * D, roof_z(x0 + (dx if side < 0 else -dx), t) + dz)
    if cell is None: cell = lambda kind, side, x, k, r: (0 if r < .55 else 1 if r < .85 else 2) + (4 if kind == 'roll' else 0)
    gone_pan = {(j, k) for j in range(N_PAN) for k in range(N_COURSE) if hole(side, pan_x(j), k)}
    jits = {}
    for lod, (nu_p, nu_r, grp, mask) in enumerate(((4, 4, 1, 1), (2, 2, 1, 2), (1, 2, 3, 4))):
        V, F, UV, M = [], [], [], []
        for j in range(N_PAN):
            x0 = pan_x(j); ks = [k for k in range(N_COURSE) if (j, k) not in gone_pan]
            if lod == 2: ks = [k for k in ks if all((j, kk) not in gone_pan for kk in range(k - k % 3, k - k % 3 + 3))]
            rs = {k: R.random() for k in range(N_COURSE)} if lod == 0 else jits[('p', j)][1]
            if lod == 0: jits[('p', j)] = (None, rs)
            strip(V, F, UV, M, place(x0), 'pan', nu_p, ks, lambda k, j=j, x0=x0, rs=rs: cell('pan', side, x0, k, rs[k]), lambda k: k % 3, mask, grp,
                  jit=lambda k, rs=rs: ((rs[k] - .5) * .006, (rs[(k + 5) % N_COURSE] - .5) * .003))
        for i in range(N_ROLL):
            x0 = roll_x(i); jl, jr = i - 1, i
            ks = [k for k in range(N_COURSE) if not any((jj, k) in gone_pan for jj in (jl, jr) if 0 <= jj < N_PAN)]
            if lod == 2: ks = [k for k in ks if all(not any((jj, kk) in gone_pan for jj in (jl, jr) if 0 <= jj < N_PAN) for kk in range(k - k % 3, k - k % 3 + 3))]
            rs = {k: R.random() for k in range(N_COURSE)} if lod == 0 else jits[('r', i)][1]
            if lod == 0: jits[('r', i)] = (None, rs)
            strip(V, F, UV, M, place(x0), 'roll', nu_r, ks, lambda k, x0=x0, rs=rs: cell('roll', side, x0, k, rs[k]), lambda k: (k + 1) % 3, mask, grp,
                  jit=lambda k, rs=rs: ((rs[k] - .5) * .004, .0))
        uv_part(f'Roof_Tiles_{side}_LOD{lod}', V, F, UV, M, P['roof'])


# ------------------------------------------------------------------ boards under the tiles, barge boards, eave rafters, ridge
def slab_grid(name, nx, nt, top, bottom, keep, mat, uvw_top=.03, uvw_bottom=.6, **kw):
    """Board slab over a (x, t) grid: top(i, j) / bottom(i, j) -> xyz; keep(i, j) per cell; rims on every open edge."""
    idx = {}; V = []
    def vid(layer, i, j):
        key = (layer, i, j)
        if key not in idx: idx[key] = len(V); V.append((top if layer == 0 else bottom)(i, j))
        return idx[key]
    F, W = [], []
    kept = {(i, j) for i in range(nx) for j in range(nt) if keep(i, j)}
    for (i, j) in kept:
        F.append((vid(0, i, j), vid(0, i + 1, j), vid(0, i + 1, j + 1), vid(0, i, j + 1))); W.append(uvw_top)
        F.append((vid(1, i, j), vid(1, i, j + 1), vid(1, i + 1, j + 1), vid(1, i + 1, j))); W.append(uvw_bottom)
        for (di, dj), (a, b) in (((0, -1), ((i, j), (i + 1, j))), ((1, 0), ((i + 1, j), (i + 1, j + 1))), ((0, 1), ((i + 1, j + 1), (i, j + 1))), ((-1, 0), ((i, j + 1), (i, j)))):
            if (i + di, j + dj) not in kept:
                F.append((vid(0, *b), vid(0, *a), vid(1, *a), vid(1, *b))); W.append(1.)
    o = mesh(name, V, F, mat, **kw)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    at = o.data.attributes.new('uvw', 'FLOAT', 'FACE'); at.data.foreach_set('value', W)
    return o


def underlay(P, side, cut=lambda side, x, t: False):
    D = DEPTH[side]; nx, nt = 22, 24; X = 4.40
    xs = lambda i: -X + 2 * X * i / nx
    ts = lambda j: j / nt * 1.004
    top = lambda i, j: (xs(i), side * ts(j) * D, roof_z(xs(i), ts(j)) + UNDER_TOP)
    bot = lambda i, j: (xs(i), side * ts(j) * D, roof_z(xs(i), ts(j)) + UNDER_TOP - UNDER_T)
    keep = lambda i, j: not cut(side, (xs(i) + xs(i + 1)) / 2, (ts(j) + ts(j + 1)) / 2)
    return slab_grid(f'Roof_Boards_{side}', nx, nt, top, bot, keep, P['timber'], group='Wood', grain='x')


def sweep_box(name, pts, w, h, mat, up=None, bevel=True, **kw):
    """Rectangular section w (sideways) x h (down from the path) along pts; ends capped."""
    pts = [Vector(p) for p in pts]; V, F = [], []
    for k, p in enumerate(pts):
        d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        u = Vector(up or (0, 0, 1)); s = d.cross(u).normalized(); u = s.cross(d).normalized()
        for a, b in ((-w / 2, 0), (w / 2, 0), (w / 2, -h), (-w / 2, -h)):
            V.append(tuple(p + s * a + u * b))
    n = len(pts)
    for k in range(n - 1):
        for q in range(4):
            a, b = k * 4 + q, k * 4 + (q + 1) % 4
            F.append((a, b, b + 4, a + 4))
    F.append((3, 2, 1, 0)); F.append(tuple((n - 1) * 4 + q for q in range(4)))
    o = mesh(name, V, F, mat, **kw)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    if bevel:
        m = o.modifiers.new('Soft_edges', 'BEVEL'); m.width = .006; m.segments = 1; m.limit_method = 'ANGLE'
    return o


def barge_boards(P, keep=lambda x, side, t: True):
    for sx in (-1, 1):
        x = sx * 4.45
        for side in (-1, 1):
            D = DEPTH[side]; pts = [(x, side * t * D, roof_z(x, t) + UNDER_TOP - .005) for t in np.linspace(0., .985, 17) if keep(x, side, t)]
            if len(pts) > 1: sweep_box(f'Barge_Board_{sx}_{side}', pts, .04, .17, P['timber'], up=(0, 0, 1), group='Wood', grain='y')


def eave_rafters(P, keep=lambda x, side: True):
    for side in (-1, 1):
        D = DEPTH[side]
        for i in range(17):
            x = -4.05 + i * .506
            if not keep(x, side): continue
            t0 = (D - .75) / D
            pts = [(x, side * t * D, roof_z(x, t) + UNDER_TOP - UNDER_T + .01) for t in np.linspace(t0, 1.0, 5)]     # under the boards, its top 1 cm into them
            sweep_box(f'Eave_Rafter_{side}_{i}', pts, .08, .1, P['timber'], bevel=False, group='Wood', grain='y', uvw=.6)


def ridge(P, x0=-4.34, x1=4.34, broken_end=None):
    """Stacked ridge body with a round cap tile along it; the ends curl up with the roof."""
    xs = np.linspace(x0, x1, 37)
    zr = lambda x: roof_z(x, 0.)
    body = [(x, 0., zr(x) + .19) for x in xs]
    sweep_box('Ridge_Body', body, .3, .22, P['tile'], up=(0, 0, 1), grain='x', group='Stone')
    V, F = [], []; seg = 8
    for x in xs:
        for q in range(seg + 1):
            a = math.pi * q / seg
            V.append((x, .085 * math.cos(a), zr(x) + .19 + .075 * math.sin(a)))
    for k in range(len(xs) - 1):
        for q in range(seg):
            a = k * (seg + 1) + q
            F.append((a, a + seg + 1, a + seg + 2, a + 1))
    mesh('Ridge_Cap', V, F, P['tile'], smooth=True, grain='x', solid=.012, group='Stone')
    for x in (x0, x1):
        from ti_core import cyl
        cyl('Ridge_End_Cap', (x + (.006 if x < 0 else -.006), 0., zr(x) + .19), .095, .02, P['tile'], axis='x', verts=14, group='Stone')


def eave_caps(P, side, keep=lambda x: True):
    """Round end tiles (wa dang) closing the rolls at the eave."""
    from ti_core import cyl
    D = DEPTH[side]
    for i in range(N_ROLL):
        x = roll_x(i)
        if not keep(x): continue
        t = 1.
        y = side * (t * D + .004); z = roof_z(x, t) + ROLL_BASE + LIFT + .02
        cyl('Eave_Cap', (x, y, z), .056, .016, P['tile'], axis='y', verts=8, bevel=0., detail=1, group='Stone')
