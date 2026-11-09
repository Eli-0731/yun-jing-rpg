"""承天 · 11/05 A 包 MC02 索橋（Johnnnny0823）。Exports go to art/exports/mc02-rope-bridge.

Two walkable chain bridges, 24 m and 12 m long, 1.6 m deck, 1.5 m sag, both ends at the same height. Same hand and the same
shared 2048 trim sheet as MC01 / TX04 (M_MountainStreet_Trim), so the bridges batch with the street and the academy; geometry
helpers from the MC01 builder and stone_block from the TX04 builder (both merged).

Layout (picked three-views: 24 m option 2, 12 m option 1): a granite bridgehead at each end (1.4 m deep, its top is the walking
surface), two square stone posts per bridgehead anchoring two dark iron hand chains, iron hangers every ~1.2 m down to two deck
chains, weathered cedar planks resting on the deck chains with hemp lashings at intervals, a few loose decorative edge boards
outside the walking width (the walking surface itself is continuous).
Origin: the centre of end A's outer edge at deck level (z = 0 is the walking surface at both ends); the bridge runs along +Y to
end B at y = L. Put the origin on a CliffBoardwalk connector (its deck is at +1.2 m, running along Y) and both ends meet the
boardwalk deck height. LOD0 keeps the modelled links; LOD1 <= 50 %, LOD2 <= 15 %. Collision: a smooth deck ribbon with 1.1 m
guard walls on both sides plus the bridgehead tops (no step at either joint).

    blender -b --factory-startup -P art/source/mc02-rope-bridge/build_mc02.py -- B24 B12
"""
import bpy, bmesh, json, math, sys, random
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'art/source/mountain-street-houses-a')); sys.path.insert(0, str(ROOT / 'art/source/tx04-branch-court'))
import build_mc01 as mc
import build_tx04 as tx

PKG = 'mc02-rope-bridge'; OUT = ROOT / 'art/exports' / PKG; PRE = ROOT / 'art/previews' / PKG
for p in (OUT, PRE): p.mkdir(parents=True, exist_ok=True)
SPEC = {'B24': 24.0, 'B12': 12.0}
W, SAG, HEAD = 1.6, 1.5, 1.4          # deck width, sag, bridgehead depth
PX = .78                               # deck chain x (under the plank ends)
POST_X, POST_H = 1.02, 1.45            # stone post centre x, height above the walking surface
HAND_Z = 1.05                          # hand chain anchor height above the walking surface

def deck_z(y, L):
    """walking-surface height: 0 on the bridgeheads, a parabola sagging SAG at mid span between them"""
    a, b = HEAD, L - HEAD
    if y <= a or y >= b: return 0.0
    t = (y - a) / (b - a); return -SAG * 4 * t * (1 - t)

def hand_z(y, L):
    """hand chain: anchored at HAND_Z on the inner faces of the posts, sagging with the deck so it stays ~1.05 m above it"""
    a, b = HEAD - .2, L - HEAD + .2
    t = min(1.0, max(0.0, (y - a) / (b - a))); return HAND_Z - SAG * 4 * t * (1 - t) * .98

def chain(name, path_fn, y0, y1, seed, link=.13, r_link=.045, wire=.011):
    """a chain of alternating torus links along a curve x(y), z(y) from y0 to y1, link length `link` measured along the curve"""
    pts = [path_fn(y) for y in np.linspace(y0, y1, 400)]
    seg = [0.0]
    for i in range(1, len(pts)): seg.append(seg[-1] + (Vector(pts[i]) - Vector(pts[i - 1])).length)
    total = seg[-1]; n = int(total / link)
    bm = bmesh.new()
    for k in range(n):
        s = (k + .5) * total / n; i = int(np.searchsorted(seg, s)); i = min(max(i, 1), len(pts) - 1)
        f = (s - seg[i - 1]) / max(seg[i] - seg[i - 1], 1e-9); P = Vector(pts[i - 1]).lerp(Vector(pts[i]), f)
        T = (Vector(pts[i]) - Vector(pts[i - 1])).normalized()
        up = Vector((0, 0, 1)); side = T.cross(up).normalized(); up = side.cross(T).normalized()
        if k % 2: side, up = up, -side   # every other link turned 90 degrees
        # an oval link: 8 x 4 ring of rings
        ring = []
        for a_ in np.linspace(0, math.tau, 8, endpoint=False):
            c = P + T * (link * .5 * .9 * math.cos(a_)) + side * (r_link * math.sin(a_))
            d = (T * math.cos(a_) * (link * .5 * .9) + side * math.sin(a_) * r_link).normalized()
            ring.append([bm.verts.new(c + (d * math.cos(b_) + up * math.sin(b_)) * wire) for b_ in np.linspace(0, math.tau, 4, endpoint=False)])
        for a_ in range(8):
            for b_ in range(4):
                bm.faces.new((ring[a_][b_], ring[(a_ + 1) % 8][b_], ring[(a_ + 1) % 8][(b_ + 1) % 4], ring[a_][(b_ + 1) % 4]))
    return mc.finish(name, bm, 'bronze', 'Main', axis=(0, 1, 0), smooth=True)

def bridgehead(pre, y0, flip, L, seed):
    """granite bridgehead y0..y0+HEAD (flip mirrors it to end B): coursed body down to -1.2 m, a paved top flush with the deck,
    two square posts with caps and chain eyes, kerb stones along both sides"""
    rg = random.Random(seed); sgn = -1 if flip else 1; yc = y0 + sgn * HEAD / 2
    for ci, (z0, z1) in enumerate(((-1.2, -.78), (-.78, -.36), (-.36, -.1))):
        x = -1.3 - (0 if ci % 2 == 0 else .3); k = 0   # staggered joints; every course still starts at the -X face
        while x < 1.3 - 1e-3:
            a = max(x, -1.3); l = rg.uniform(.6, 1.0); b = min(x + l, 1.3)
            if 1.3 - b < .3: b = 1.3
            tx.stone_block(f'{pre}_course{ci}_{k}', (b - a - .014, HEAD - .02 * ci, z1 - z0 - .012), ((a + b) / 2, yc, (z0 + z1) / 2),
                           'granite_moss' if ci == 0 else 'granite', amt=.01, bev=.025, seed=seed + ci * 20 + k)
            x = b; k += 1
    mc.box(f'{pre}_core', (2.5, HEAD - .1, 1.12), (0, yc, -.64), 'dark', 'Main', bev=0)
    for i, x in enumerate((-.4, .4)):   # paving between the kerbs, top = walking surface
        o = mc.box(f'{pre}_pave{i}', (.79, HEAD - .03, .1), (x, yc, -.05 - .002 * i), 'granite_top', 'Main', bev=0); mc.bevel(o, .01, 2, 30)
    for sx in (-1, 1):
        tx.stone_block(f'{pre}_kerb{sx:+d}', (.44, HEAD - .02, .16), (sx * 1.04, yc, -.02), 'granite_top', amt=.008, bev=.02, seed=seed + 60 + sx)
        yp = y0 + sgn * (HEAD - .26)
        tx.stone_block(f'{pre}_post{sx:+d}', (.4, .4, POST_H), (sx * POST_X, yp, POST_H / 2 + .06), 'granite', amt=.008, bev=.025, seed=seed + 70 + sx)
        bm = bmesh.new()   # pyramidal cap
        h = .16; v = [bm.verts.new((sx * POST_X + dx, yp + dy, POST_H + .035)) for dx, dy in ((-.24, -.24), (.24, -.24), (.24, .24), (-.24, .24))]
        top = [bm.verts.new((sx * POST_X + dx, yp + dy, POST_H + .06 + .07)) for dx, dy in ((-.24, -.24), (.24, -.24), (.24, .24), (-.24, .24))]
        apex = bm.verts.new((sx * POST_X, yp, POST_H + .06 + .07 + h))
        bm.faces.new(list(reversed(v)))
        for i in range(4):
            bm.faces.new((v[i], v[(i + 1) % 4], top[(i + 1) % 4], top[i])); bm.faces.new((top[i], top[(i + 1) % 4], apex))
        o = mc.finish(f'{pre}_cap{sx:+d}', bm, 'granite_top', 'Main'); mc.bevel(o, .012, 2, 30)
        mc.tube(f'{pre}_eye{sx:+d}', [(sx * POST_X - sx * .05 + .06 * 0, yp + sgn * .2 + .05 * math.cos(a), HAND_Z + .05 * math.sin(a)) for a in np.linspace(0, math.tau, 13)],
                .016, 'bronze', 'Main', sides=6, caps=False)
        mc.box(f'{pre}_plate{sx:+d}', (.22, .02, .22), (sx * POST_X, yp + sgn * .209, HAND_Z), 'bronze', 'Main', bev=.004, axis=(1, 0, 0))
        mc.box(f'{pre}_deckanchor{sx:+d}', (.16, .05, .12), (sx * PX, y0 + sgn * HEAD, -.07), 'bronze', 'Main', bev=.004, axis=(1, 0, 0))

def BRIDGE(mid):
    L = SPEC[mid]; rg = random.Random(9000 + int(L)); pre = mid
    bridgehead(f'{pre}_headA', 0.0, False, L, 9100 + int(L))
    bridgehead(f'{pre}_headB', L, True, L, 9200 + int(L))
    a, b = HEAD, L - HEAD
    # planks along the curve (arc-length spacing), resting on the deck chains; a lashing every third plank
    ys = np.linspace(a, b, 2000); zs = np.array([deck_z(y, L) for y in ys]); arc = np.concatenate([[0], np.cumsum(np.hypot(np.diff(ys), np.diff(zs)))])
    pitch = .235; n = int(arc[-1] / pitch); k = 0
    for i in range(n):
        s = (i + .5) * arc[-1] / n; y = float(np.interp(s, arc, ys)); z = deck_z(y, L)
        dz = (deck_z(y + .01, L) - deck_z(y - .01, L)) / .02; ang = math.atan(dz)
        wdt = W - (rg.uniform(.0, .12) if rg.random() < .15 else 0.0); xo = rg.uniform(-.02, .02)
        o = mc.box(f'{pre}_plank{i}', (wdt, pitch - .016, .05), (xo, 0, -.025), 'oldwood' if rg.random() < .35 else 'plank', 'Main', bev=.006, axis=(1, 0, 0))
        o.data.transform(Matrix.Translation((0, y, z)) @ Matrix.Rotation(ang, 4, 'X')); k += 1
        if i % 3 == 1:
            for sx in (-1, 1):
                ring = [(sx * PX + .05 * math.cos(t), y + (.0), z - .055 + .055 * math.sin(t)) for t in np.linspace(0, math.tau, 11)]
                lash = mc.tube(f'{pre}_lash{i}{sx:+d}', ring, .012, 'oldwood', 'Main', sides=5, caps=False)
                lash.data.transform(Matrix.Translation((0, y, z)) @ Matrix.Rotation(ang, 4, 'X') @ Matrix.Translation((0, -y, -z)))
    # a few loose decorative edge boards outside the walking width (review rule: never in the walking path)
    for j, t in enumerate((.18, .41, .66, .83)):
        y = a + (b - a) * t; z = deck_z(y, L); sx = 1 if j % 2 else -1
        dz = (deck_z(y + .01, L) - deck_z(y - .01, L)) / .02
        o = mc.box(f'{pre}_edgeboard{j}', (.18, .34, .035), (0, 0, 0), 'oldwood', 'Main', bev=.005, axis=(0, 1, 0))
        o.data.transform(Matrix.Translation((sx * (W / 2 + .08), y, z - .085)) @ Matrix.Rotation(math.atan(dz), 4, 'X') @ Matrix.Rotation(sx * .25, 4, 'Y'))
    # deck chains under the plank ends, hand chains between the posts, hangers between them
    for sx in (-1, 1):
        chain(f'{pre}_deckchain{sx:+d}', lambda y, sx=sx: (sx * PX, y, deck_z(y, L) - .058), a + .01, b - .01, 9300 + sx)
        hx = sx * (POST_X - .06)
        chain(f'{pre}_handchain{sx:+d}', lambda y, hx=hx: (hx, y, hand_z(y, L)), HEAD - .19, L - HEAD + .19, 9400 + sx)
        nh = max(3, int((b - a) / 1.2));
        for j, y in enumerate(np.linspace(a + .6, b - .6, nh)):
            top = Vector((hx, y, hand_z(y, L) - .047)); bot = Vector((sx * (PX + .02), y, deck_z(y, L) - .07))
            mc.tube(f'{pre}_hanger{sx:+d}{j}', [top, top.lerp(bot, .5) + Vector((sx * .01, 0, 0)), bot], .011, 'bronze', 'Main', sides=6)
            mc.tube(f'{pre}_clip{sx:+d}{j}', [(bot.x + .03 * math.cos(t), y + .017, bot.z - .02 + .03 * math.sin(t)) for t in np.linspace(0, math.tau, 9)], .009, 'bronze', 'Main', sides=5, caps=False)
    return {'L': L}

def collision(tag, L):
    """smooth walkable deck ribbon (no step at the joints) + 1.1 m guard walls both sides + bridgehead tops; one mesh"""
    bm = bmesh.new()
    def slab(ys, zfn, x0, x1, top_off, bot_off):
        rows = []
        for y in ys:
            z = zfn(y); rows.append([bm.verts.new((x0, y, z + bot_off)), bm.verts.new((x1, y, z + bot_off)), bm.verts.new((x1, y, z + top_off)), bm.verts.new((x0, y, z + top_off))])
        for i in range(len(rows) - 1):
            r0, r1 = rows[i], rows[i + 1]
            for q in range(4): bm.faces.new((r0[q], r1[q], r1[(q + 1) % 4], r0[(q + 1) % 4]))
        bm.faces.new(list(reversed(rows[0]))); bm.faces.new(rows[-1])
    ys = np.linspace(0, L, 61)
    slab(ys, lambda y: deck_z(y, L), -W / 2 - .05, W / 2 + .05, 0.0, -.12)
    for sx in (-1, 1): slab(ys, lambda y: deck_z(y, L), sx * (W / 2 + .05) - .05, sx * (W / 2 + .05) + .05, 1.1, -.1)
    me = bpy.data.meshes.new(f'{tag}_Collision'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(o); return o

def build(mid):
    mc.clear(); mc.load_trim(); tx.roof_material()   # (the roof material is unused here; created so tx helpers stay consistent)
    meta = BRIDGE(mid); L = meta['L']; parts = mc.parts; tag = f'MC02_{mid}'
    lod0 = mc.join(parts, f'{tag}_LOD0'); bpy.ops.object.select_all(action='DESELECT')
    T0 = mc.tris(lod0); out = {}
    for lv, frac, cap in ((1, .5, 100_000), (2, .15, 25_000)):
        tgt = max(min(T0 * frac, cap), 12)
        c = lod0.copy(); c.data = lod0.data.copy(); c.name = f'{tag}_LOD{lv}'; bpy.context.scene.collection.objects.link(c)
        m = c.modifiers.new('d', 'DECIMATE'); m.ratio = min(1.0, tgt / T0); m.use_collapse_triangulate = True; mc.apply(c, m); out[lv] = c
    col = collision(tag, L)
    vs = np.array([v.co[:] for v in lod0.data.vertices]); mn, mx = vs.min(0), vs.max(0); dims = mx - mn
    assert abs(mx[1] - L) < .01 and abs(mn[1]) < .01, f'{mid} length {mn[1]:.3f}..{mx[1]:.3f} != 0..{L}'
    assert dims[0] <= 2.62, f'{mid} width {dims[0]:.3f}'
    endz = [deck_z(0, L), deck_z(L, L)]
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / f'{tag}.blend'))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(filepath=str(OUT / f'{tag}.fbx'), use_selection=True, object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', use_tspace=False, add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    lods = [{'lod': lv, 'triangles': mc.tris(o), 'objects': 1, 'materials': len({m.name for m in o.data.materials})}
            for lv, o in ((0, lod0), (1, out[1]), (2, out[2]))]
    info = {'id': f'MC02-{int(L)}M', 'package': 'docs/execution/2026-11-05/A-48h-mountain-city-architecture.md', 'author': 'A (Johnnnny0823)',
            'version': 'v001', 'status': 'Exported; Imported/In-game Verified: 未驗',
            'dimensions_m': [round(float(d), 3) for d in dims], 'bounds_min_m': [round(float(v), 3) for v in mn], 'bounds_max_m': [round(float(v), 3) for v in mx],
            'length_m': L, 'deckWidth_m': W, 'sag_m': SAG, 'bridgehead_m': HEAD, 'endDeckHeights_m': endz,
            'origin': 'centre of end A outer edge at walking-surface height (z = 0 at both ends); runs along +Y to end B at y = length',
            'cliffBoardwalk': 'place the origin on a CliffBoardwalk v001 connector (its deck is at +1.2 m, running along Y): both ends meet the boardwalk deck height',
            'minTier': 'low', 'lods': lods, 'objectsLOD0': [lod0.name], 'detailObjects': [], 'glowObjects': [],
            'materials': sorted({m.name for m in lod0.data.materials}),
            'textures': {n: '2048x2048' for n in ('T_MountainStreet_Albedo', 'T_MountainStreet_Normal', 'T_MountainStreet_MetallicSmoothness', 'T_MountainStreet_Emission')},
            'textureNote': 'shared MC01 trim sheet (art/textures/mountain-street-houses-a)',
            'collision': f'{tag}_Collision (one mesh: smooth deck ribbon over the full length incl. bridgeheads, 1.1 m guard walls both sides)',
            'maxDeckSlope_deg': round(math.degrees(math.atan(SAG * 4 / (L - 2 * HEAD))), 1),
            'fbx': f'art/exports/{PKG}/{tag}.fbx', 'fps': '不寫（手機未實測）'}
    (OUT / f'{tag}.model_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
    print(mid, 'LOD tris', [l['triangles'] for l in lods], 'dims', info['dimensions_m'], 'min', info['bounds_min_m'], 'slope', info['maxDeckSlope_deg'], flush=True)

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for a in args: build(a)
