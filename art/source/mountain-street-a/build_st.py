"""承天 · 11/08 A 包第二部分 ST01–ST06 山城街道小件（Johnnnny0823）。Exports go to art/exports/mountain-street-a.

Same hand as MC01 (#80) / TX04 (#90) / MC02 (#98): geometry helpers from the MC01 builder, stone, timber, iron-dark bronze and
lantern paper from the shared 2048 MC01 trim sheet (M_MountainStreet_Trim / M_MountainStreet_Glow), so the pieces batch with
the street houses. Colours the trim sheet does not have (three banner cloths, red lantern paper, polished bench granite, iron,
hemp rope, red silk) live on one small 1024 sheet made here: M_StreetFurniture (+ M_StreetFurniture_Glow for the red paper),
art/textures/mountain-street-a/T_StreetFurniture_*.png, 256 px/m like the trim sheet.

Modules (each modelled after its picked three-view in art/references/ST0x/):
  ST01            square granite lantern post with a framed cloud-scroll panel and a small tiled lamp house (Glow)
  ST02 / _6M / _4M  five (four, three) paper lanterns on a hemp rope between two iron hooks; 8 m is the package size,
                  6 m and 4 m are the same design for narrower streets (python build_st.py ... ST02 --span 7.2 builds any length)
  ST03_S / _C / _D  drainage channel: 4 m straight, corner, 4 m stepped cascade matching the MC01 SB04 stair (11 x 0.182 m)
  ST04            stone bench, polished slab on two carved blocks
  ST05_A / _B / _C  blank cloth banner on a rod, indigo / ochre / stone grey, tasselled hem, no writing
  ST06_S / _C / _E  cliff-edge railing: 2 m timber panel (post centre to post centre), corner / line post, end post

Origins: footprint centre, -Y = street front, bottom z = 0, except the hanging pieces and the channel:
  ST02  midpoint between the two hook tips (z = 0 = hook tips, the string hangs below), runs along X
  ST03  stands on the street (bottom z = 0, rim 0.3 m) as in the picked three-view; +Y edge (y = +0.25) goes against the
        MC01 stone-base front face; the cascade stands on the lower street and its rims step down 2.0 m from -X to +X
  ST05  bottom of the tassels at z = 0, hang point (Socket_Hang) at the top of the cord loop
LOD0 is the modelled detail; LOD1 <= 50 %, LOD2 <= 15 %. Groups: main mesh, Glow (emissive), Detail_Moss (removable).

    blender -b --factory-startup -P art/source/mountain-street-a/build_st.py -- sheet ST01 ST02 ...
"""
import bpy, bmesh, json, math, sys, random
from contextlib import contextmanager
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'art/source/mountain-street-houses-a'))
import build_mc01 as mc
from build_mc01 import box, beam, lathe, tube, prism_xz, rotz, chisel, bevel, apply, moss_tuft, tile_cap

PKG = 'mountain-street-a'; OUT = ROOT / 'art/exports' / PKG; TEX = ROOT / 'art/textures' / PKG
for p in (OUT, TEX): p.mkdir(parents=True, exist_ok=True)
PACKAGE = 'docs/execution/2026-11-08/A-80h-mountain-city.md'

# ------------------------------------------------------------------ the small street-furniture sheet
STRIPS = [('cloth_indigo', 128), ('cloth_ochre', 128), ('cloth_grey', 128), ('paper_red', 64), ('paper_red_faded', 64),
          ('paper_cream', 64), ('paper_soot', 64), ('granite_polish', 128), ('iron', 64), ('rope', 64), ('silk_red', 64), ('wood_dark', 64)]
SHEET = 1024; V0 = {}; _v = 0
for _n, _h in STRIPS: V0[_n] = (_v, _h); _v += _h
assert _v == SHEET, _v
MST = {}

def sources():
    R = mc.R; fbm = mc.fbm; lerp = mc.lerp; X, Y = mc.X, mc.Y; S = {}
    soft = fbm(2, 3); weave = .5 + .25 * np.sin(X * math.tau * 160) + .25 * np.sin(Y * math.tau * 160)   # coarse cotton
    slub = np.clip((fbm(40, 2, aniso=8) - .6) * 3, 0, 1)
    fade = np.clip(Y * 1.4 - .35, 0, 1) ** 1.2                     # V = up the banner: sun-bleached upper part
    dirt = np.clip(.35 - Y, 0, 1) * 2 * (.5 + .5 * fbm(5, 2))     # grime along the hem
    for nm, lo, hi in (('cloth_indigo', (.11, .16, .30), (.20, .28, .46)), ('cloth_ochre', (.40, .17, .07), (.58, .28, .12)),
                       ('cloth_grey', (.34, .34, .33), (.50, .49, .46))):
        a = lerp(lo, hi, np.clip(soft * .8 + .2 * slub, 0, 1)) * (.92 + .08 * weave[..., None])
        a = a * (1 - .6 * fade[..., None]) + fade[..., None] * np.array([.58, .55, .48]) * .6
        a = a * (1 - .35 * dirt[..., None])
        S[nm] = (a, .6 * weave + .4 * slub, .9, .95, 0, 0)
    ribs = (np.abs(((X * 24) % 1) - .5) < .06).astype(float)     # bamboo hoops: U runs up the lantern (lathe axis)
    blot = np.clip((fbm(10, 2) - .62) * 4, 0, 1)
    for nm, lo, hi, gl in (('paper_red', (.62, .10, .05), (.80, .20, .09), 1), ('paper_red_faded', (.66, .30, .20), (.80, .44, .30), 1),
                           ('paper_cream', (.84, .74, .55), (.95, .87, .68), 1), ('paper_soot', (.20, .10, .06), (.32, .18, .11), 1)):
        a = lerp(lo, hi, fbm(4, 3)) * (1 - .12 * blot[..., None]) * (1 - .45 * ribs[..., None])
        S[nm] = (a, .3 * fbm(8, 2) + ribs, .7, .85, 0, gl)
    S['granite_polish'] = (lerp((.50, .48, .45), (.70, .67, .62), np.clip(fbm(3, 4) * .8 + .2 * soft, 0, 1)), .3 * fbm(12, 2), .8, .45, 0, 0)
    S['iron'] = (lerp((.07, .07, .075), (.16, .15, .14), fbm(6, 3)) + np.clip((fbm(8, 3) - .62) * 2.5, 0, 1)[..., None] * np.array([.12, .05, .01]),
                 fbm(14, 3), 1.2, .6, .6, 0)
    tw = .5 + .5 * np.sin(math.tau * (X * 60 + Y * 2))            # twisted hemp
    S['rope'] = (lerp((.30, .25, .17), (.50, .43, .30), np.clip(tw * .6 + .4 * soft, 0, 1)), tw, 1.0, .9, 0, 0)
    S['silk_red'] = (lerp((.42, .05, .04), (.62, .12, .07), np.clip(soft + .3 * np.sin(Y * 300), 0, 1)), .5 + .5 * np.sin(Y * 300), .5, .7, 0, 0)
    S['wood_dark'] = (lerp((.10, .07, .05), (.20, .14, .10), fbm(3, 3, aniso=1 / 8)), fbm(20, 2, aniso=1 / 8), 1.0, .7, 0, 0)
    return S

def make_sheet():
    S = sources(); R = mc.R
    A = np.zeros((SHEET, SHEET, 3), np.float32); N = np.zeros((SHEET, SHEET, 3), np.float32)
    MS = np.zeros((SHEET, SHEET, 4), np.float32); EM = np.zeros((SHEET, SHEET, 3), np.float32)
    for name, h in STRIPS:
        alb, hgt, s, r, m, glow = S[name]; k = R // h
        alb = np.broadcast_to(alb, (R, R, 3)); hgt = np.broadcast_to(hgt, (R, R))
        a = alb.reshape(h, k, h, k, 3).mean((1, 3)); hh = hgt.reshape(h, k, h, k).mean((1, 3))
        dx = (np.roll(hh, -1, 1) - np.roll(hh, 1, 1)) * s; dy = (np.roll(hh, -1, 0) - np.roll(hh, 1, 0)) * s
        n = np.dstack([-dx, -dy, np.ones_like(hh)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
        reps = SHEET // h; v0 = V0[name][0]
        A[v0:v0 + h] = np.tile(a, (1, reps, 1)); N[v0:v0 + h] = np.tile(n * .5 + .5, (1, reps, 1))
        MS[v0:v0 + h, :, 0] = m; MS[v0:v0 + h, :, 3] = 1 - r
        if glow: EM[v0:v0 + h] = np.tile(a, (1, reps, 1))
    for nm, arr, data in (('Albedo', A, False), ('Normal', N, True), ('MetallicSmoothness', MS, True), ('Emission', EM, False)):
        im = bpy.data.images.new(f'T_StreetFurniture_{nm}', SHEET, SHEET, alpha=arr.shape[2] == 4)
        if data: im.colorspace_settings.name = 'Non-Color'
        px = np.ones((SHEET, SHEET, 4), np.float32); px[..., :arr.shape[2]] = np.clip(arr, 0, 1); im.pixels.foreach_set(px.ravel())
        im.filepath_raw = str(TEX / f'T_StreetFurniture_{nm}.png'); im.file_format = 'PNG'; im.save()

def load_sheet():
    ims = {k: bpy.data.images.load(str(TEX / f'T_StreetFurniture_{n}.png')) for k, n in
           (('alb', 'Albedo'), ('nrm', 'Normal'), ('ms', 'MetallicSmoothness'), ('em', 'Emission'))}
    for k in ('nrm', 'ms'): ims[k].colorspace_settings.name = 'Non-Color'
    for nm, glow in (('M_StreetFurniture', 0), ('M_StreetFurniture_Glow', 1)):
        mat = bpy.data.materials.new(nm); mat.use_nodes = True; nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
        def tex(im): t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; return t
        nt.links.new(tex(ims['alb']).outputs['Color'], bs.inputs['Base Color'])
        ms = tex(ims['ms']); sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(ms.outputs['Color'], sep.inputs['Color'])
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
        nt.links.new(ms.outputs['Alpha'], inv.inputs[1]); nt.links.new(inv.outputs[0], bs.inputs['Roughness']); nt.links.new(sep.outputs['Red'], bs.inputs['Metallic'])
        nm_ = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(ims['nrm']).outputs['Color'], nm_.inputs['Color']); nt.links.new(nm_.outputs['Normal'], bs.inputs['Normal'])
        if glow:
            nt.links.new(tex(ims['em']).outputs['Color'], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = 4.0
        MST[glow] = mat

@contextmanager
def st():
    """inside this block the MC01 helpers project onto the street-furniture sheet and use its materials"""
    sv = (mc.V0, mc.SHEET, mc.MAT[0], mc.MAT[1]); mc.V0, mc.SHEET, mc.MAT[0], mc.MAT[1] = V0, SHEET, MST[0], MST[1]
    try: yield
    finally: mc.V0, mc.SHEET, mc.MAT[0], mc.MAT[1] = sv

def mesh_obj(name, bm, mat, grp, uv, smooth=False):
    """object from a bmesh with explicit UVs: uv(co) -> (u, v) in sheet units"""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    lay = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        f.smooth = smooth
        for l in f.loops: l[lay].uv = uv(l.vert.co)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); me.materials.append(mat)
    return mc.link(o, grp)

def rim_uv(o, strip):
    """solidify copies the sheet UVs onto its thin rim faces, which leaves them zero-area: give each rim face a sliver of
    the same strip from its own edge length (u) and thickness (v)"""
    me = o.data; uv = me.uv_layers.active.data
    for p in me.polygons:
        us = [uv[li].uv for li in p.loop_indices]
        if abs(sum(us[i].x * us[i - 1].y - us[i - 1].x * us[i].y for i in range(len(us)))) > 1e-10: continue
        cs = [me.vertices[me.loops[li].vertex_index].co for li in p.loop_indices]; c0 = cs[0]
        for li, co in zip(p.loop_indices, cs):
            d = co - c0; uv[li].uv = ((co.x + co.z) * mc.PXM / SHEET, strip_v(strip, .5) + (d.y * 40 + d.z * .2) / SHEET)

def strip_v(strip, t):
    """V for a 0..1 position across a street-furniture strip (pads kept)"""
    v0, h = V0[strip]; return (v0 + mc.PAD + t * (h - 2 * mc.PAD)) / SHEET

def chip(o, point, normal, strip, sheet='trim'):
    """knock a corner off a stone: bisect, drop the outer part, cap the hole, re-project"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=point, plane_no=Vector(normal).normalized(), clear_outer=True)
    cut = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    if cut: bmesh.ops.holes_fill(bm, edges=cut, sides=0)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)
    bm.to_mesh(o.data); bm.free()
    if sheet == 'st':
        with st(): mc.reuv(o, strip)
    else: mc.reuv(o, strip)

SOCKETS = []
def socket(name, loc, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = .2
    e.location = loc; e.rotation_euler = rot; bpy.context.scene.collection.objects.link(e); SOCKETS.append(e); return e

def stone(name, size, center, strip='granite', amt=.006, bev=.015, seed=0, cuts=None):
    o = box(name, size, center, strip, 'Main', bev=0, cuts=(1 if max(size) > .5 else 0) if cuts is None else cuts)
    chisel(o, amt, 3.0, seed=seed, keep_bed=True); bevel(o, bev, 2, 30); return o

def tuft(name, rg, at, scale=1.0):
    o = moss_tuft(name, rg); o.data.transform(Matrix.Translation(at) @ Matrix.Scale(scale, 4)); return o

LIMITS = {}; INFO = {}

# ------------------------------------------------------------------ ST01 lantern post (three-view option 2)
LIMITS['ST01'] = (.6, .6, 2.4)
def cloud_scroll(cx, cz, s, flip=1):
    """one ruyi cloud head (three lobes) in XZ, for relief panels"""
    pts = []
    for a in np.linspace(0, math.tau, 28, endpoint=False):
        r = s * (1 + .26 * math.cos(3 * a + .4) ** 2 * (1 if math.sin(a) > -.3 else .3))
        pts.append((cx + flip * r * math.cos(a), cz + .72 * r * math.sin(a)))
    return pts
def cloud_tail(cx, cz, s, flip=1, n=14, up=1):
    """a tapering wisp trailing from a cloud head: a thick wavy line as a polygon"""
    top, bot = [], []
    for i in range(n + 1):
        t = i / n; x = cx - flip * s * (.6 + 2.2 * t); z = cz - up * s * (.1 + .9 * t) + s * .35 * math.sin(t * math.pi * 1.6)
        w = s * .22 * (1 - t) + s * .03; top.append((x, z + w)); bot.append((x, z - w))
    return top + bot[::-1]

def ST01():
    """square granite lantern post 0.6 x 0.6 x 2.4 m: a two-step plinth (one chipped corner, lichen), a die with raised frames,
    a square shaft carrying a framed panel of cloud scrolls on all four faces, cloud corbels under a projecting shelf, a small
    lamp house of four stone posts with lattice-framed openings around a paper lamp box (Glow, the lamp wick light), soot-dark
    lintels, a hipped stone roof with tile ribs and upturned corners, a jewel finial."""
    rg = random.Random(6101)
    o = stone('ST01_plinth', (.6, .6, .14), (0, 0, .07), 'granite_moss', amt=.008, bev=.02, seed=9101, cuts=1)
    chip(o, (.3 - .07, -.3 + .07, .14), (1, -1, 1.4), 'granite_moss')
    stone('ST01_step', (.5, .5, .12), (0, 0, .132 + .06), 'granite_moss', amt=.006, bev=.015, seed=9102)   # stacked stones overlap 8 mm (chisel sinks tops)
    stone('ST01_die', (.40, .40, .30), (0, 0, .244 + .15), 'granite', amt=.006, bev=.012, seed=9103)
    for k in range(4):   # raised frame on each die face
        for nm, sz, c in (('t', (.29, .016, .025), (0, -.2 - .006, .51)), ('b', (.29, .016, .025), (0, -.2 - .006, .29)),
                          ('l', (.025, .013, .22), (-.1375, -.2 - .0055, .40)), ('r', (.025, .013, .22), (.1375, -.2 - .0055, .40))):
            b = box(f'ST01_dieframe{k}{nm}', sz, c, 'granite', 'Main', bev=.004); rotz(b, k * math.pi / 2)
    stone('ST01_dietop', (.44, .44, .06), (0, 0, .536 + .03), 'granite_top', amt=.004, bev=.012, seed=9104)
    # shaft 1.55 m with chamfered arrises
    z0, z1 = .588, 1.60; sw = .30
    o = box('ST01_shaft', (sw, sw, z1 - z0), (0, 0, (z0 + z1) / 2), 'granite', 'Main', bev=0, cuts=1); chisel(o, .005, 3, 9105); bevel(o, .022, 1, 30)
    # framed panel with cloud scrolls on each face
    for k in range(4):
        y = -sw / 2 - .007; fz0, fz1 = z0 + .12, z1 - .10; fw = sw - .07
        for nm, sz, c in (('t', (fw - .01, .016, .022), (0, y, fz1)), ('b', (fw - .01, .016, .022), (0, y, fz0)),
                          ('l', (.022, .013, fz1 - fz0), (-fw / 2 + .011, y + .0005, (fz0 + fz1) / 2)), ('r', (.022, .013, fz1 - fz0), (fw / 2 - .011, y + .0005, (fz0 + fz1) / 2))):
            b = box(f'ST01_frame{k}{nm}', sz, c, 'granite', 'Main', bev=.004); rotz(b, k * math.pi / 2)
        flip = 1 if k % 2 == 0 else -1
        for j, cz in enumerate(np.linspace(fz1 - .10, fz0 + .10, 5)):   # a rising column of five cloud heads, wisps trailing across
            sd = flip * (1 if j % 2 == 0 else -1); cx = .036 * sd; s_ = .040
            h = prism_xz(f'ST01_cloud{k}{j}', cloud_scroll(cx, float(cz), s_, sd), .018, -sw / 2 - .016, 'granite', 'Main', bev=0); rotz(h, k * math.pi / 2)
            t = prism_xz(f'ST01_wisp{k}{j}', cloud_tail(cx, float(cz) - .01, s_ * .85, sd, up=1), .0155, -sw / 2 - .0105, 'granite', 'Main', bev=0); rotz(t, k * math.pi / 2)
    # cloud corbels under the shelf (two per face) and the shelf
    for k in range(4):
        for sx in (-1, 1):
            poly = [(sx * .06, z1 - .005), (sx * .15, z1 - .005), (sx * .17, z1 - .03), (sx * .155, z1 - .06), (sx * .12, z1 - .065),
                    (sx * .10, z1 - .045), (sx * .085, z1 - .06), (sx * .06, z1 - .07)]
            if sx < 0: poly = poly[::-1]
            c = prism_xz(f'ST01_corbel{k}{sx}', poly, .05, -sw / 2 - .05, 'granite', 'Main', bev=.003); rotz(c, k * math.pi / 2)
    stone('ST01_shelf', (.48, .48, .07), (0, 0, z1 - .008 + .035), 'granite_top', amt=.004, bev=.014, seed=9106)
    zl0 = z1 + .062; zl1 = zl0 + .36
    stone('ST01_sill', (.40, .40, .04), (0, 0, zl0 - .008 + .02), 'granite', amt=.003, bev=.008, seed=9107)
    zs = zl0 + .032
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):   # lamp-house corner posts
        box(f'ST01_lpost{i}', (.07, .07, zl1 - zs - .034), (sx * .155, sy * .155, (zs - .006 + zl1 - .04) / 2), 'granite', 'Main', bev=.008)
    for k in range(4):   # soot-dark lintels (odd sides fit between the even ones) and a lattice frame in each opening
        b = box(f'ST01_lintel{k}', (.40 if k % 2 == 0 else .26, .07, .05), (0, -.155, zl1 - .025 - .001), 'granite_moss', 'Main', bev=.008); rotz(b, k * math.pi / 2)
        y = -.155 + .012; hz = zl1 - .051 - zs
        for nm, sz, c in (('b', (.244, .02, .02), (0, y, zs + .01)), ('t', (.244, .02, .02), (0, y, zl1 - .051 - .01)),
                          ('l', (.02, .014, hz - .008), (-.085, y, zs + hz / 2)), ('r', (.02, .014, hz - .008), (.085, y, zs + hz / 2))):
            b = box(f'ST01_lat{k}{nm}', sz, c, 'beam', 'Main', bev=.003); rotz(b, k * math.pi / 2)
    lathe('ST01_lamp', [(.004, zs - .004), (.16, zs - .004), (.16, zl1 - .062), (.004, zl1 - .062)], 'paper', 'Glow', seg=4, glow=True); rotz(mc.parts[-1], math.pi / 4)
    # hipped stone roof with tile ribs (tile_cap, re-projected onto the granite strips)
    n0 = len(mc.parts); tile_cap('ST01_roof', .28, zl1 - .002, 2.27, eave_lift=.045)
    for p_ in mc.parts[n0:]: mc.reuv(p_, 'granite_top')
    z0r, z1r, r0 = zl1 - .002, 2.27, .28 * math.sqrt(2)
    ts = np.linspace(.08, 1, 8); rs = [.004] + [r0 * t for t in ts]; zz_ = [z1r] + [z1r - (z1r - z0r) * t ** .7 + .045 * t ** 6 for t in ts]
    def roof_z(d): return float(np.interp(d * math.sqrt(2), rs, zz_))
    for k in range(4):   # carved tile ribs following each slope
        for j, x in enumerate(np.linspace(-.15, .15, 7)):
            ys = np.linspace(-.255, -(abs(x) + .03), 6)
            t = tube(f'ST01_rib{k}{j}', [(float(x), float(y), roof_z(-y) + .005) for y in ys], .009, 'granite_top', 'Main', sides=5); rotz(t, k * math.pi / 2)
    lathe('ST01_finial', [(.004, 2.24), (.05, 2.255), (.055, 2.28), (.035, 2.30), (.045, 2.33), (.04, 2.36), (.022, 2.385), (.004, 2.40)], 'granite_top', 'Main', seg=12)
    for i, at in enumerate(((-.21, -.25, .138), (.18, .25, .138), (.22, .04, .138), (-.21, .1, .256))):
        tuft(f'Detail_Moss_ST01_{i}', rg, at)
    return {'collision': [('box', (0, 0, .29), (.6, .6, .58)), ('box', (0, 0, 1.1), (.3, .3, 1.05)), ('box', (0, 0, 1.95), (.48, .48, .7))],
            'glow': 'ST01_lamp paper box inside the lamp house (M_MountainStreet_Glow)', 'mount': 'free-standing on the street, bottom z = 0'}

# ------------------------------------------------------------------ ST02 lantern string
SPAN = {'ST02': 8.0, 'ST02_6M': 6.0, 'ST02_4M': 4.0}
for _k, _L in SPAN.items(): LIMITS[_k] = (_L, .4, 1.2)
def lantern_string(mid, L, n):
    """hemp rope between two iron S-hooks (hook tips at z = 0, x = +-(L/2 - .02)), sagging ~3 % of the span; n oval paper
    lanterns hang on short cords: dark wooden caps, bamboo hoops in the paper, a sooty band under the top cap, red silk tassel."""
    rg = random.Random(6200 + int(L * 10)); xh = L / 2 - .045; zr = -.10; sag = .03 * L
    def rope_z(x): return zr - sag * (1 - (x / (xh - .02)) ** 2)
    with st():
        for sx in (-1, 1):   # S-hook: open hook on top (over the eave ring), shank, closed eye holding the rope
            cx = sx * xh
            hook = [(cx + sx * .035 * math.cos(a), 0, -.035 + .035 * math.sin(a)) for a in np.linspace(-.3, math.pi, 10)]
            hook += [(cx - sx * .035, 0, zr + .04)]
            tube(f'ST02_hook{sx}', hook, .007, 'iron', 'Main', sides=6)
            ex = cx - sx * .035
            eye = [(ex, .022 * math.sin(a), zr + .022 - .022 * math.cos(a)) for a in np.linspace(0, math.tau, 13)]   # eye turned 90 deg to the hook
            tube(f'ST02_eye{sx}', eye, .006, 'iron', 'Main', sides=6, caps=False)
            tube(f'ST02_wrap{sx}', [(ex + .016 * math.cos(a), .016 * math.sin(a), zr - .004 - .006 * a / math.tau) for a in np.linspace(0, math.tau * 1.5, 16)],
                 .007, 'rope', 'Main', sides=5)
        xs = np.linspace(-(xh - .05), xh - .05, 72)
        tube('ST02_rope', [(x, 0, rope_z(x) + (.004 * math.sin(x * 9))) for x in xs], .011, 'rope', 'Main', sides=6)
        papers = ['paper_red', 'paper_cream', 'paper_red_faded', 'paper_cream', 'paper_red_faded'][:n] if n == 5 else \
                 (['paper_red', 'paper_cream', 'paper_red_faded', 'paper_red'][:n] if n == 4 else ['paper_red', 'paper_red_faded', 'paper_cream'])
        lx = np.linspace(-(xh - .05) * .75, (xh - .05) * .75, n)
        R, H = .17, .30
        for k, xb in enumerate((-(xh - .05) * .45, (xh - .05) * .2)):   # red silk bindings on the rope
            xb = float(xb); zb = rope_z(xb)
            lathe(f'ST02_bind{k}', [(.004, -.03), (.015, -.03), (.016, -.02), (.016, .02), (.015, .03), (.004, .03)], 'silk_red', 'Main', seg=8)
            mc.parts[-1].data.transform(Matrix.Translation((xb, 0, zb)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
        for i, (x, pap) in enumerate(zip(lx, papers)):
            x = float(x); z0 = rope_z(x) - .006; zc = z0 - .07 - rg.uniform(0, .02)
            tube(f'ST02_cord{i}', [(x, 0, z0 + .012), (x, 0, zc - .008)], .004, 'rope', 'Main', sides=5)
            tube(f'ST02_loop{i}', [(x + .014 * math.cos(a), .014 * math.sin(a) * .2, z0 + .002 + .012 * math.sin(a)) for a in np.linspace(0, math.tau, 11)], .004, 'rope', 'Main', sides=4, caps=False)
            lathe(f'ST02_top{i}', [(.004, zc), (.06, zc), (.075, zc - .012), (.075, zc - .028), (.004, zc - .028)], 'wood_dark', 'Main', seg=12)
            zp0 = zc - .028; zp1 = zp0 - H; prof = []
            for t in np.linspace(0, 1, 13):
                r = .07 + (R - .07) * math.sin(math.pi * t) ** .7; prof.append((r, zp0 - t * H))
            soot = [p for p in prof if p[1] >= zp0 - .045] + [(.07 + (R - .07) * math.sin(math.pi * .13) ** .7, zp0 - .045)]
            body = [soot[-1]] + [p for p in prof if p[1] < zp0 - .045]
            lathe(f'ST02_soot{i}', [(.004, zp0)] + soot + [(.004, zp0 - .045)], 'paper_soot', 'Glow', seg=16, glow=True)
            lathe(f'ST02_paper{i}', [(.004, zp0 - .045)] + body + [(.004, zp1)], pap, 'Glow', seg=16, glow=True)
            lathe(f'ST02_bot{i}', [(.004, zp1 + .002), (.075, zp1 + .002), (.075, zp1 - .018), (.05, zp1 - .03), (.004, zp1 - .03)], 'wood_dark', 'Main', seg=12)
            zt = zp1 - .03; Lt = .15 + rg.uniform(-.01, .02)
            lathe(f'ST02_knot{i}', [(.004, zt + .002), (.016, zt), (.02, zt - .02), (.004, zt - .028)], 'silk_red', 'Main', seg=8, center=(x, 0, 0))
            tube(f'ST02_tassel{i}', [(x, 0, zt - .02), (x + rg.uniform(-.01, .01), 0, zt - .02 - Lt)], .012, 'silk_red', 'Main', sides=8, radii=[.008, .022])
            for p_ in mc.parts[-6:-2]: p_.data.transform(Matrix.Translation((x, 0, 0)))
    socket('Socket_HookA', (-xh, 0, 0)); socket('Socket_HookB', (xh, 0, 0))
    return {'collision': [], 'hanging': True, 'span_m': L, 'lanterns': n,
            'mount': 'hang the two hook tips (Socket_HookA / Socket_HookB, z = 0) on eave rings or nails at the same height; '
                     'the string hangs below to about -0.95 m. Other spans: build_st.py ST02 --span <metres>',
            'glow': 'lantern paper (M_StreetFurniture_Glow)', 'noWriting': True}
def ST02(): return lantern_string('ST02', 8.0, 5)
def ST02_6M(): return lantern_string('ST02_6M', 6.0, 4)
def ST02_4M(): return lantern_string('ST02_4M', 4.0, 3)

# ------------------------------------------------------------------ ST03 drainage channel
CH_W, CH_IN, CH_D, CH_FLOOR = .5, .22, .3, .18      # outer width, inner width, block depth, channel depth below the rim
LIMITS['ST03_S'] = (4.0, .5, .3); LIMITS['ST03_C'] = (.5, .5, .3); LIMITS['ST03_D'] = (4.0, .5, 2.3)
WALL = (CH_W - CH_IN) / 2

def channel_run(pre, x0, x1, ztop, rg, seed, bottom=0.0, lip=False, cramp=False, base=True):
    """a run of U blocks from x0 to x1 with the rim at ztop and the base at `bottom`: base slab (its top is the wet, darker
    channel floor) + two side walls with worn coping, joints every 0.6-1.0 m, weeds in the joints, algae on the floor"""
    xs = [x0]
    while x1 - xs[-1] > 1.1: xs.append(xs[-1] + rg.uniform(.6, 1.0))
    xs.append(x1); g = .003; zb = bottom
    for k, (a, b) in enumerate(zip(xs, xs[1:])):
        a_, b_ = a + (g if a > x0 else 0), b - (g if b < x1 else 0); L = b_ - a_; cx = (a_ + b_) / 2
        if base:
            o = box(f'{pre}_floor{k}', (L, CH_W, ztop - CH_FLOOR - zb), (cx, 0, (zb + ztop - CH_FLOOR) / 2), 'granite', 'Main', bev=0, cuts=1 if L > .5 else 0)
            chisel(o, .005, 3, seed + k, keep_bed=True); bevel(o, .01, 1, 30)
        box(f'{pre}_wet{k}', (L - .004, CH_IN + .004, .008), (cx, 0, ztop - CH_FLOOR + .002), 'granite_moss', 'Main', bev=0)
        for sy in (-1, 1):
            o = box(f'{pre}_wall{k}{sy}', (L, WALL, CH_FLOOR + .004), (cx, sy * (CH_W / 2 - WALL / 2), ztop - .002 - (CH_FLOOR + .004) / 2), 'granite', 'Main', bev=0, cuts=1 if L > .5 else 0)
            chisel(o, .006, 3, seed + 40 + k * 2 + (sy > 0), keep_bed=True); bevel(o, .02 if sy < 0 else .012, 2, 30)   # street-side rim worn rounder
        if rg.random() < .7 and b < x1 - .01:
            tuft(f'Detail_Moss_{pre}_j{k}', rg, (b, -CH_W / 2 + .04, zb), .8)
        if rg.random() < .8:
            tuft(f'Detail_Moss_{pre}_a{k}', rg, (cx + rg.uniform(-L / 3, L / 3), rg.choice((-1, 1)) * (CH_IN / 2 - .01), ztop - CH_FLOOR - .002), .45)
        if zb < .01 and rg.random() < .6:   # weeds at the foot of the street-side face
            tuft(f'Detail_Moss_{pre}_f{k}', rg, (cx + rg.uniform(-L / 3, L / 3), -CH_W / 2 + .04, 0), .8)
        if cramp and k == 1:   # one dark iron cramp across a coping joint (street side), as in the picked three-view
            with st(): box(f'{pre}_cramp', (.10, .045, .008), (a_ - g, -CH_W / 2 + WALL / 2, ztop - .004), 'iron', 'Main', bev=.002)
    if lip and x1 < 1.99:   # spout lip over the drop at the +X end
        box(f'{pre}_lip', (.06, CH_IN - .02, .032), (x1 + .02, 0, ztop - CH_FLOOR + .004), 'granite_moss', 'Main', bev=.006)

def ch_cols(cx, L, ztop, zb=0.0):
    return [('box', (cx, 0, (zb + ztop - CH_FLOOR) / 2), (L, CH_W, ztop - CH_FLOOR - zb)),
            ('box', (cx, -CH_W / 2 + WALL / 2, ztop - CH_FLOOR / 2), (L, WALL, CH_FLOOR)), ('box', (cx, CH_W / 2 - WALL / 2, ztop - CH_FLOOR / 2), (L, WALL, CH_FLOOR))]

def ST03_S():
    """4 m straight street gutter (picked three-view option 3): a 0.3 m high granite trough standing on the street, U blocks
    of different lengths with worn coping, a darker wet floor, algae and small weeds in the joints, one iron cramp."""
    channel_run('ST03_S', -2.0, 2.0, CH_D, random.Random(6301), 9300, cramp=True)
    return {'collision': ch_cols(0, 4.0, CH_D),
            'mount': 'stands on the street, bottom z = 0, rim 0.3 m; +Y side (y = +0.25) against the MC01 stone-base front face; runs along X; ends at x = -2 / +2'}

def ST03_C():
    """0.5 x 0.5 m corner block: the channel comes in from -X and leaves toward +Y (wrapping an outside building corner that
    sits in the -X/+Y quadrant); outer walls on -Y and +X, a small inner corner stone, wet floor."""
    rg = random.Random(6302); h = CH_W / 2; zf = CH_D - CH_FLOOR; zt = CH_D
    o = box('ST03_C_floor', (CH_W, CH_W, zf), (0, 0, zf / 2), 'granite', 'Main', bev=0); chisel(o, .004, 3, 9350); bevel(o, .01, 1, 30)
    box('ST03_C_wet', (CH_W - WALL - .004, CH_W - WALL - .004, .008), (-WALL / 2, WALL / 2, zf + .002), 'granite_moss', 'Main', bev=0)
    o = box('ST03_C_wallS', (CH_W, WALL, CH_FLOOR + .004), (0, -h + WALL / 2, zt - .002 - (CH_FLOOR + .004) / 2), 'granite', 'Main', bev=0); chisel(o, .006, 3, 9351); bevel(o, .02, 2, 30)
    o = box('ST03_C_wallE', (WALL, CH_W - WALL - .003, CH_FLOOR + .004), (h - WALL / 2, WALL / 2 + .0015, zt - .002 - (CH_FLOOR + .004) / 2), 'granite', 'Main', bev=0); chisel(o, .006, 3, 9352); bevel(o, .016, 2, 30)
    o = box('ST03_C_post', (WALL, WALL, CH_FLOOR + .004), (-h + WALL / 2, h - WALL / 2, zt - .002 - (CH_FLOOR + .004) / 2), 'granite', 'Main', bev=0); chisel(o, .006, 3, 9353); bevel(o, .012, 2, 30)
    tuft('Detail_Moss_ST03_C0', rg, (h - WALL - .01, -h + WALL + .01, zf - .002), .45)
    tuft('Detail_Moss_ST03_C1', rg, (h - .04, .05, 0), .8)
    tuft('Detail_Moss_ST03_C2', rg, (.1, -h + .04, 0), .8)
    return {'collision': [('box', (0, 0, zf / 2), (CH_W, CH_W, zf)), ('box', (0, -h + WALL / 2, zt - CH_FLOOR / 2), (CH_W, WALL, CH_FLOOR)),
                          ('box', (h - WALL / 2, 0, zt - CH_FLOOR / 2), (WALL, CH_W, CH_FLOOR)), ('box', (-h + WALL / 2, h - WALL / 2, zt - CH_FLOOR / 2), (WALL, WALL, CH_FLOOR))],
            'mount': 'bottom z = 0, rim 0.3 m; channel enters at the -X face and leaves at the +Y face (centre lines y = 0 and x = 0)'}

def ST03_D():
    """4 m stepped cascade beside a stair (picked three-view option 3): 11 solid blocks of 0.364 m standing on the lower street,
    each rim 0.182 m lower than the last (the MC01 SB04 stair: 11 risers of 0.182, treads of 0.364), a spout lip at every
    drop. -X end: rim 2.3 m (= an ST03_S on the upper street at +2.0 m); +X end: rim 0.482 m, the last drop lands on an
    ST03_S on the lower street."""
    rg = random.Random(6304); n, run, rise = 11, 4.0 / 11, 2.0 / 11; cols = []
    for k in range(n):
        x0 = -2.0 + k * run; zt = CH_D + (n - k) * rise
        channel_run(f'ST03_D{k}', x0 + (.002 if k else 0), x0 + run - (.002 if k < n - 1 else 0), zt, rg, 9400 + k * 10, lip=True, base=False)
        cols += ch_cols(x0 + run / 2, run, zt)
    # the base under the channel floor as a coursed wall with a stepped top (picked view): courses ~0.3 m, staggered joints;
    # a step whose floor ends inside a course gets its own short block, runs of full-height steps share long blocks
    F = [CH_D + (n - k) * rise - CH_FLOOR for k in range(n)]; X0 = [-2.0 + k * run for k in range(n)]
    ch = .30; zc = 0.0; j = 0
    while zc < max(F) - .01:
        zt_ = zc + ch; k = 0
        while k < n:
            if F[k] <= zc + .01: k += 1; continue
            if F[k] < zt_ + .01:   # partial course under this step (its top is the step floor)
                spans = [(X0[k], X0[k] + run, F[k])]; k += 1
            else:
                k1 = k
                while k1 < n and F[k1] >= zt_ + .01: k1 += 1
                xa, xb = X0[k], X0[k1 - 1] + run; cut = [xa]
                off = rg.uniform(.15, .45) if j % 2 else 0
                while xb - cut[-1] > .95 + off: cut.append(cut[-1] + rg.uniform(.5, .9) + off); off = 0
                cut.append(xb); spans = [(a, b, zt_) for a, b in zip(cut, cut[1:])]; k = k1
            for a, b, top in spans:
                g0 = .002 if a > -2.0 + 1e-6 else 0; g1 = .002 if b < 2.0 - 1e-6 else 0
                o = box(f'ST03_D_c{j}_{a:.2f}', (b - a - g0 - g1, CH_W, top - zc + (.006 if zc > 0 else 0)), ((a + g0 + b - g1) / 2, 0, (zc - (.006 if zc > 0 else 0) + top) / 2),
                        'granite_moss' if j == 0 else 'granite', 'Main', bev=0, cuts=1 if b - a > .5 else 0)
                chisel(o, .006, 3, 9500 + j * 31 + int(a * 100), keep_bed=True); bevel(o, .014, 2, 30)
        zc = zt_; j += 1
    return {'collision': cols, 'drop_m': 2.0, 'steps': n, 'rise_m': round(rise, 4), 'tread_m': round(run, 4),
            'mount': 'stands on the lower street (bottom z = 0) beside an MC01 SB04 stair; -X end meets an ST03_S at +2.0 m, +X end drops onto an ST03_S at z = 0'}

# ------------------------------------------------------------------ ST04 bench
LIMITS['ST04'] = (1.8, .5, .5)
def ST04():
    """stone bench 1.8 x 0.5 x 0.5 m: one thick slab of polished warm granite (seat dished and glossier where people sit, a
    chipped front edge) on two carved blocks with cusped feet and a raised panel, moss at the feet."""
    rg = random.Random(6401); zt = .48; T = .14
    with st():
        o = box('ST04_seat', (1.8, .48, T), (0, 0, zt - T / 2), 'granite_polish', 'Main', bev=0, cuts=4); chisel(o, .003, 3, 9401, keep_bed=True)
        me = o.data
        for v in me.vertices:   # a faint dish worn into the seat, deeper at the two usual sitting places
            if v.co.z > zt - .01:
                d = sum(math.exp(-((v.co.x - c) / .32) ** 2) for c in (-.42, .42)) * math.exp(-((v.co.y + .02) / .2) ** 2)
                v.co.z -= .006 * d
        bevel(o, .028, 3, 30); mc.reuv(o, 'granite_polish', (1, 0, 0))
    chip(o, (.55, -.24 + .03, zt - .012), (.15, -1, 1), 'granite_polish', sheet='st')
    for i, sx in enumerate((-1, 1)):   # picked view option 4: a block on a small plinth, a raised panel with notched corners
        cx = sx * .6; w, d, h = .30, .38, zt - T + .002
        stone(f'ST04_foot{i}', (w + .05, d + .05, .06), (cx, 0, .03), 'granite_moss', amt=.004, bev=.012, seed=9410 + i)
        o = box(f'ST04_block{i}', (w, d, zt - T + .008 - .052), (cx, 0, (.052 + zt - T + .008) / 2), 'granite', 'Main', bev=0, cuts=1)
        chisel(o, .005, 3, 9420 + i); bevel(o, .012, 2, 30)
        for f, (ax, half) in enumerate((('y', d / 2), ('x', w / 2))):   # front + back panels and the two end panels
            for sgn in (-1, 1):
                pw, ph, z0 = (w - .08 if ax == 'y' else d - .08), h - .06 - .1, .06 + .05
                for nm, sz, c in (('t', (pw, .012, .018), (0, 0, z0 + ph)), ('b', (pw, .012, .018), (0, 0, z0)),
                                  ('l', (.018, .012, ph - .05), (-pw / 2 + .009, 0, z0 + ph / 2)), ('r', (.018, .012, ph - .05), (pw / 2 - .009, 0, z0 + ph / 2))):
                    sz_ = sz; c_ = (c[0], sgn * (half + .004), c[2])
                    if nm == 't' or nm == 'b': sz_ = (pw - .05, sz[1], sz[2])
                    b = box(f'ST04_panel{i}{f}{sgn}{nm}', sz_, c_, 'granite', 'Main', bev=.003)
                    if ax == 'x': b.data.transform(Matrix.Translation((cx, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'Z'))
                    else: b.data.transform(Matrix.Translation((cx, 0, 0)))
                for q, (qx, qz) in enumerate(((-1, 0), (1, 0), (-1, 1), (1, 1))):   # notched corners: small diagonal bars
                    b = box(f'ST04_notch{i}{f}{sgn}{q}', (.04, .012, .016), (qx * (pw / 2 - .03), sgn * (half + .004), z0 + qz * ph + (.012 if qz == 0 else -.012)),
                            'granite', 'Main', bev=.003, rot=Matrix.Rotation(qx * (1 if qz == 0 else -1) * math.pi / 4, 4, 'Y'))
                    if ax == 'x': b.data.transform(Matrix.Translation((cx, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'Z'))
                    else: b.data.transform(Matrix.Translation((cx, 0, 0)))
        tuft(f'Detail_Moss_ST04_{i}a', rg, (cx - .14, -.18, 0)); tuft(f'Detail_Moss_ST04_{i}b', rg, (cx + .14, .18, 0))
    return {'collision': [('box', (0, 0, zt - T / 2), (1.8, .48, T)), ('box', (-.6, 0, (zt - T) / 2), (.35, .43, zt - T)), ('box', (.6, 0, (zt - T) / 2), (.35, .43, zt - T))],
            'seatHeight_m': zt, 'mount': 'free-standing, seat faces -Y'}

# ------------------------------------------------------------------ ST05 banners
BANNERS = {'ST05_A': 'cloth_indigo', 'ST05_B': 'cloth_ochre', 'ST05_C': 'cloth_grey'}
for _k in BANNERS: LIMITS[_k] = (.6, .1, 1.8)
def banner(mid, strip, seed):
    """blank cloth banner on a short rod: hanging cord loop (Socket_Hang at the top), turned rod with knob ends, cotton cloth
    0.5 m wide with gentle vertical folds, sun-bleached upper part, a sewn hem and a fringe of frayed tassels. No writing."""
    rg = random.Random(seed); zr = 1.70; W = .5; ztop = zr + .004; zbot = .25
    tube(f'{mid}_rod', [(-.255, 0, zr), (.255, 0, zr)], .016, 'beam', 'Main', sides=8)
    for sx in (-1, 1):
        lathe(f'{mid}_knob{sx}', [(.004, 0), (.022, .004), (.028, .02), (.02, .038), (.004, .042)], 'beam', 'Main', seg=8)
        mc.parts[-1].data.transform(Matrix.Translation((sx * .253, 0, zr)) @ Matrix.Rotation(sx * math.pi / 2, 4, 'Y'))
    with st():
        tube(f'{mid}_cord', [(-.2, 0, zr + .01), (-.1, 0, 1.75), (0, 0, 1.788), (.1, 0, 1.75), (.2, 0, zr + .01)], .005, 'rope', 'Main', sides=5)
        tube(f'{mid}_loop', [(.009 * math.sin(a), 0, 1.788 + .009 - .009 * math.cos(a)) for a in np.linspace(0, math.tau, 9)], .003, 'rope', 'Main', sides=4, caps=False)
    ph = rg.uniform(0, math.tau)
    def fold(u, v): return .022 * math.sin(u * math.tau * 1.5 + ph) * (.25 + .75 * v) + .006 * math.sin(u * math.tau * 4 + ph * 2) * v
    bm = bmesh.new(); nx, nz = 14, 22; vs = []
    for j in range(nz + 1):
        v = j / nz; z = ztop - v * (ztop - zbot)
        vs.append([bm.verts.new((-W / 2 + i / nx * W, fold(i / nx, v), z)) for i in range(nx + 1)])
    for j in range(nz):
        for i in range(nx): bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    uoff = rg.random()
    o = mesh_obj(f'{mid}_cloth', bm, MST[0], 'Main', lambda co: (co.x * mc.PXM / SHEET + uoff, strip_v(strip, (co.z - zbot) / (ztop - zbot))))
    m = o.modifiers.new('t', 'SOLIDIFY'); m.thickness = .005; m.offset = 0; apply(o, m); rim_uv(o, strip)
    pal = {'cloth_indigo': 'cloth_grey', 'cloth_ochre': 'cloth_grey', 'cloth_grey': 'cloth_indigo'}
    for q in range(2):   # two sewn patches (picked view option 2), a different faded cloth, following the folds just in front
        pw_, ph_ = rg.uniform(.07, .10), rg.uniform(.08, .11); u0 = rg.uniform(.08, .9 - pw_ / W); v0_ = rg.uniform(.45, .85) if q == 0 else rg.uniform(.15, .4)
        bm = bmesh.new(); g_ = []
        for jj in range(4):
            row = []
            for ii in range(4):
                u = u0 + ii / 3 * pw_ / W; v = v0_ + jj / 3 * ph_ / (ztop - zbot)
                row.append(bm.verts.new((-W / 2 + u * W, fold(u, v) - .0045, ztop - v * (ztop - zbot))))
            g_.append(row)
        for jj in range(3):
            for ii in range(3): bm.faces.new((g_[jj][ii], g_[jj][ii + 1], g_[jj + 1][ii + 1], g_[jj + 1][ii]))
        ps = pal[strip]; mesh_obj(f'{mid}_patch{q}', bm, MST[0], 'Main', lambda co, ps=ps: (co.x * mc.PXM / SHEET + .37 * q, strip_v(ps, .35 + (co.z - zbot) / (ztop - zbot) * .3)))
        m = mc.parts[-1].modifiers.new('t', 'SOLIDIFY'); m.thickness = .002; m.offset = 0; apply(mc.parts[-1], m); rim_uv(mc.parts[-1], ps)
    hem = [(x, fold((x + W / 2) / W, 1.0), zbot + .012) for x in np.linspace(-W / 2 + .004, W / 2 - .004, 15)]
    with st():
        tube(f'{mid}_hem', hem, .009, strip, 'Main', sides=6)
        for i, x in enumerate(np.linspace(-W / 2 + .02, W / 2 - .02, 17)):   # a dense fringe of frayed strands with knots
            x = float(x) + rg.uniform(-.004, .004); y = fold((x + W / 2) / W, 1.0); L = rg.uniform(.15, .22) * (.75 if rg.random() < .25 else 1)
            sway = rg.uniform(-.01, .01)
            tube(f'{mid}_tassel{i}', [(x, y, zbot + .005), (x + sway * .3, y, zbot - .04), (x + sway, y + .002, zbot - L)], .006, strip, 'Main', sides=5, radii=[.0055, .0075, .0035])
            lathe(f'{mid}_knot{i}', [(.002, zbot - .045), (.009, zbot - .042), (.009, zbot - .03), (.002, zbot - .027)], strip, 'Main', seg=6, center=(x + sway * .3, y, 0))
    # keep the lowest tassel tip on z = 0
    mn = min(v.co.z for p_ in mc.parts for v in p_.data.vertices)
    for p_ in mc.parts: p_.data.transform(Matrix.Translation((0, 0, -mn)))
    socket('Socket_Hang', (0, 0, 1.797 - mn))
    return {'collision': [], 'hanging': True, 'mount': 'hang the cord loop (Socket_Hang) on a nail, hook or the MC01 DT02 arm; tassel tips at z = 0',
            'cloth': strip, 'noWriting': True}
def ST05_A(): return banner('ST05_A', 'cloth_indigo', 6501)
def ST05_B(): return banner('ST05_B', 'cloth_ochre', 6502)
def ST05_C(): return banner('ST05_C', 'cloth_grey', 6503)

# ------------------------------------------------------------------ ST06 cliff railing
LIMITS['ST06_S'] = (2.0, .2, 1.1); LIMITS['ST06_C'] = (.2, .2, 1.1); LIMITS['ST06_E'] = (.5, .2, 1.1)
POST_S = .17    # post shaft width; posts stand on the 2 m grid, the panel spans post centre to post centre
def ST06_S():
    """2 m railing panel between two stone posts (posts are separate: ST06_C / ST06_E): dark cedar bottom rail lifted 0.1 m for
    drainage, square balusters, a mid rail, a broad hand-polished top rail, dark iron L-brackets with nail heads at both ends."""
    rg = random.Random(6601); xe = 1.0 - POST_S / 2 + .012
    beam('ST06_S_top', (-xe, 0, 1.0), (xe, 0, 1.0), .10, .075, 'oldwood', 'Main', bev=.018)
    beam('ST06_S_bot', (-xe, 0, .15), (xe, 0, .15), .065, .07, 'beam', 'Main', bev=.008)
    with st():   # hemp lashing round the top rail near one end (picked view option 1)
        for q in range(4):
            tube(f'ST06_S_lash{q}', [(-.62 + q * .022 + .003 * a / math.tau, .052 * math.cos(a), 1.0 + .04 * math.sin(a)) for a in np.linspace(0, math.tau, 13)], .006, 'rope', 'Main', sides=5, caps=False)
    for i, x in enumerate(np.linspace(-.76, .76, 9)):
        lean = rg.uniform(-.004, .004)
        beam(f'ST06_S_bal{i}', (float(x), 0, .18), (float(x) + lean, 0, .967), .04, .04, 'beam', 'Main', bev=.005)
    with st():   # dark iron L-brackets: one leg along the rail side, one on the post face, a nail head
        for sx in (-1, 1):
            xf = sx * (1.0 - POST_S / 2)
            for zz, rw in ((1.0, .10), (.15, .065)):
                for sy in (-1, 1):
                    box(f'ST06_S_brkA{sx}{zz}{sy}', (.10, .005, .035), (xf - sx * .05, sy * (rw / 2 + .0015), zz), 'iron', 'Main', bev=.0015)
                    box(f'ST06_S_brkB{sx}{zz}{sy}', (.005, .045, .046), (xf - sx * .0015, sy * (rw / 2 + .024), zz), 'iron', 'Main', bev=.0015)
                    lathe(f'ST06_S_nail{sx}{zz}{sy}', [(.002, 0), (.008, 0), (.006, .005), (.002, .006)], 'iron', 'Main', seg=6)
                    mc.parts[-1].data.transform(Matrix.Translation((xf - sx * .07, sy * (rw / 2 + .003), zz)) @ Vector((0, sy, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
    return {'collision': [('box', (0, 0, .55), (2.0 - POST_S, .1, 1.1))],
            'mount': 'post centre to post centre 2.0 m along X; stand a ST06_C or ST06_E post on each end (x = -1 and x = +1); on an MC01 CP01 edge'}

def rail_post(pre, rg, seed, end=False):
    zc = 1.02
    stone(f'{pre}_base', (.2, .2, .12), (0, 0, .06), 'granite_moss', amt=.005, bev=.014, seed=seed)
    o = box(f'{pre}_shaft', (POST_S, POST_S, zc - .112), (0, 0, (zc + .112) / 2), 'granite', 'Main', bev=0, cuts=1)
    chisel(o, .004, 3, seed + 1); bevel(o, .016, 1, 30)
    stone(f'{pre}_cap', (.2, .2, .05), (0, 0, zc - .008 + .025), 'granite_top', amt=.003, bev=.01, seed=seed + 2)
    if end:   # end post: lotus-bud finial and a small scroll buttress outside the run (+X)
        lathe(f'{pre}_bud', [(.004, zc + .036), (.07, zc + .038), (.075, zc + .062), (.05, zc + .072), (.045, 1.08), (.025, 1.095), (.004, 1.1)], 'granite_top', 'Main', seg=12)
        poly = [(POST_S / 2 - .004, .105), (POST_S / 2 + .26, .105), (POST_S / 2 + .26, .17), (POST_S / 2 + .2, .2), (POST_S / 2 + .12, .26),
                (POST_S / 2 + .07, .36), (POST_S / 2 + .05, .46), (POST_S / 2 - .004, .52)]
        prism_xz(f'{pre}_buttress', poly, .1, -.05, 'granite', 'Main', bev=.008)
        stone(f'{pre}_bfoot', (.3, .14, .11), (POST_S / 2 + .14, 0, .055), 'granite_moss', amt=.004, bev=.012, seed=seed + 3)
    else:
        lathe(f'{pre}_top', [(.004, zc + .036), (.075, zc + .038), (.04, 1.085), (.004, 1.095)], 'granite_top', 'Main', seg=4); rotz(mc.parts[-1], math.pi / 4)
    for i in range(2): tuft(f'Detail_Moss_{pre}_{i}', rg, ((-1) ** i * .03, (-1) ** (i + 1) * .06, 0), .6)

def ST06_C():
    """corner / line post 0.2 x 0.2 x 1.1 m: granite base with lichen, a square shaft, a cap with a low pyramid top"""
    rail_post('ST06_C', random.Random(6602), 9600)
    return {'collision': [('box', (0, 0, .55), (.2, .2, 1.1))], 'mount': 'at a panel end or a corner of the run (panels meet it on any face)'}
def ST06_E():
    """end post: the corner post with a lotus-bud finial and a small scroll buttress on the outside (+X) to close a run"""
    rail_post('ST06_E', random.Random(6603), 9610, end=True)
    return {'collision': [('box', (0, 0, .55), (.2, .2, 1.1)), ('box', (POST_S / 2 + .14, 0, .26), (.28, .1, .52))],
            'mount': 'closes a run: the last panel comes in from -X; the buttress faces outward (+X)', 'footprintNote': 'buttress reaches +0.385 m along X'}

# ------------------------------------------------------------------ build / LOD / export / info
ORDER = ['ST01', 'ST02', 'ST02_6M', 'ST02_4M', 'ST03_S', 'ST03_C', 'ST03_D', 'ST04', 'ST05_A', 'ST05_B', 'ST05_C', 'ST06_S', 'ST06_C', 'ST06_E']

def build(mid, fn=None):
    mc.clear(); mc.load_trim(); load_sheet(); SOCKETS.clear()
    meta = (fn or globals()[mid])() or {}; parts = mc.parts; tag = f'ST_{mid}'; lim = LIMITS.get(mid)
    groups = {}
    for o in parts: groups.setdefault(o['grp'], []).append(o)
    lod0 = {}
    for g, objs in groups.items():
        nm = tag if g == 'Main' else f'{tag}_{g}'
        lod0[g] = mc.join(objs, f'{nm}_LOD0'); bpy.ops.object.select_all(action='DESELECT')
    T = {g: mc.tris(o) for g, o in lod0.items()}; tot = sum(T.values()); out = {}
    for lv, frac, cap in ((1, .5, 100_000), (2, .15, 25_000)):
        budget = min(tot * frac, cap); w = {g: math.sqrt(t) for g, t in T.items()}; tw = sum(w.values())
        for g, o in lod0.items():
            tgt = max(min(T[g] * (.5 if lv == 1 else .15), budget * w[g] / tw), 12)
            c = o.copy(); c.data = o.data.copy(); c.name = o.name.replace('_LOD0', f'_LOD{lv}'); bpy.context.scene.collection.objects.link(c)
            m = c.modifiers.new('d', 'DECIMATE'); m.ratio = min(1.0, tgt / max(T[g], 1)); m.use_collapse_triangulate = True; mc.apply(c, m)
            out.setdefault(lv, {})[g] = c
    cols = []
    for i, (kind, c, s) in enumerate(meta.get('collision', [])):
        bm = mc.box_bm(s, c); me = bpy.data.meshes.new(f'{tag}_Collision{i}'); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(o); cols.append(o)
    if cols: mc.join(cols, f'{tag}_Collision')
    vs = np.array([v.co[:] for o in lod0.values() for v in o.data.vertices]); mn, mx = vs.min(0), vs.max(0); dims = mx - mn
    if lim: assert all(dims[i] <= lim[i] + .005 for i in range(3)), f'{mid} over limit {tuple(round(float(d), 3) for d in dims)} > {lim}'
    if not meta.get('hanging') and not meta.get('below_ground'): assert mn[2] > -.005, f'{mid} bottom below 0: {mn[2]}'
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / f'{tag}.blend'))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(filepath=str(OUT / f'{tag}.fbx'), use_selection=True, object_types={'MESH', 'EMPTY'}, global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', use_tspace=False, add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    lods = [{'lod': lv, 'triangles': sum(mc.tris(o) for o in d.values()), 'objects': len(d), 'materials': len({m.name for o in d.values() for m in o.data.materials})}
            for lv, d in ((0, lod0), (1, out[1]), (2, out[2]))]
    mats = sorted({m.name for o in lod0.values() for m in o.data.materials}); tex = {}
    if any(m.startswith('M_MountainStreet') for m in mats):
        tex.update({n: '2048x2048' for n in ('T_MountainStreet_Albedo', 'T_MountainStreet_Normal', 'T_MountainStreet_MetallicSmoothness', 'T_MountainStreet_Emission')})
    if any(m.startswith('M_StreetFurniture') for m in mats):
        tex.update({n: '1024x1024' for n in ('T_StreetFurniture_Albedo', 'T_StreetFurniture_Normal', 'T_StreetFurniture_MetallicSmoothness', 'T_StreetFurniture_Emission')})
    info = {'id': mid.replace('_', '-'), 'package': PACKAGE, 'author': 'A (Johnnnny0823)', 'version': 'v001',
            'status': 'Exported; Imported: see README (Unity 6000.3.28f1 check); In-game Verified: 未驗',
            'dimensions_m': [round(float(d), 3) for d in dims], 'bounds_min_m': [round(float(v), 3) for v in mn], 'bounds_max_m': [round(float(v), 3) for v in mx],
            'limit_m': list(lim) if lim else None, 'origin': meta.get('mount', ''), 'minTier': 'low', 'lods': lods,
            'objectsLOD0': [o.name for o in lod0.values()], 'detailObjects': [o.name for g, o in lod0.items() if g.startswith('Detail_')],
            'glowObjects': [o.name for g, o in lod0.items() if g == 'Glow'], 'materials': mats, 'textures': tex,
            'textureNote': 'M_MountainStreet_*: shared MC01 trim sheet (art/textures/mountain-street-houses-a); M_StreetFurniture_*: art/textures/mountain-street-a (256 px/m)',
            'sockets': [{'name': e.name, 'location_m': [round(x, 3) for x in e.location]} for e in SOCKETS],
            'collision': f'{tag}_Collision ({len(cols)} boxes)' if cols else 'none (hanging piece)',
            'extra': {k: v for k, v in meta.items() if k not in ('collision', 'mount')},
            'fbx': f'art/exports/{PKG}/{tag}.fbx', 'fps': '不寫（手機未實測）'}
    (OUT / f'{tag}.model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
    print(mid, 'LOD tris', [l['triangles'] for l in lods], 'objects', [l['objects'] for l in lods], 'mats', mats, 'dims', info['dimensions_m'],
          'min', info['bounds_min_m'], flush=True)

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if '--span' in args:
        i = args.index('--span'); L = float(args[i + 1]); del args[i:i + 2]; mid = f'ST02_{int(round(L * 10))}DM'
        LIMITS[mid] = (L, .4, 1.2); build(mid, lambda: lantern_string(mid, L, 5 if L >= 7 else 4 if L >= 5 else 3)); args = [a for a in args if a != 'ST02']
    if 'all' in args: args = ['sheet'] + ORDER
    for a in args:
        if a == 'sheet': mc.clear(); make_sheet(); print('street-furniture sheet saved', flush=True)
        else: build(a)
