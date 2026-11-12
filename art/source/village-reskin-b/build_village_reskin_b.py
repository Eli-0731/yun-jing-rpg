"""village-reskin-b v001 (work pack 2026-11-09 B-112h, batch A): RS01 the Dondon town inn, RS02 the Dondon smithy and materials shop,
re-textured with the VL01-05 / VH material set (RS02 also takes the VH old-wood timber of vh_wood.py).

RS02_Blacksmith reads art/exports/lod-backfill-b/Blacksmith/Blacksmith_LOD_v001.blend the same way as the inn. RS02_MaterialShop has no
lod-backfill copy: it is read straight from art/incoming/dondon/MaterialShop/v001/MaterialShop_v001.blend (read only), every exported mesh
evaluated with its modifiers (what the source FBX holds), the origin kept (the StarterHouse / VL origin it was built from), small parts
to Detail_Small by the lod-backfill rule (bounding box under min(0.35 m, 12 % of the asset)). Run with the ID in place of RS01_TownInn.

The shape does not change. The source is the inn already taken out of TownLayout v004 by lod-backfill-b (#85):
  art/exports/lod-backfill-b/TownInn/TownInn_LOD_v001.blend   (opened read-only; nothing is saved over it)
Its LOD0 mesh (and the Detail_Small props) is split into its loose parts, each part keeps its vertices exactly; the 15 flat colour
materials of the source are swapped one for one for the VL procedural materials (vl_mats, kept-up 'diligent' palette: dark old timber,
lime plaster with cracks, valley blue-grey stone; dark fired tile #3A4048 in place of the jade/teal tile and the green glaze). Then the
village-houses-b pipeline runs unchanged: UV atlas per group, bake (Main, Stone, Wood and a fourth Tile atlas, 2048 each: the inn's own
tile geometry has no tile-cell UVs, so it cannot read the shared VL_RoofTiles cells), LOD1/LOD2 rebuilt from the new LOD0 (50 % / 15 %),
FBX/GLB, ten views. RS01: the source had no collision mesh and has none here (a re-texture; walking the inn is the TownLayout setup's).
RS02/RS03: their sources have none either; <ID>_Collision is made here, one fitted box per reachable part (rs_collision.py).

Run (from the repo root):
  blender --background --factory-startup --python art/source/village-reskin-b/build_village_reskin_b.py -- RS01_TownInn [--force]
  ... -- RS01_TownInn --preview <dir>        procedural look only
  ... -- RS01_TownInn --compare               original | re-textured, same light and camera (needs the export)
Writes art/exports/village-reskin-b/<ID>/, art/previews/village-reskin-b/<ID>/, art/source/village-reskin-b/blend/<ID>_v001.blend
"""
import bpy, bmesh, sys, json, math
from pathlib import Path
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
VHB = HERE.parent / 'village-houses-b'
sys.path.insert(0, str(VHB))
import build_village_houses_b as B          # registers VL/VH assets too; only RS01 is run from here
import ti_core, ti_mats as tm, vl_mats, cr_mats as cm
sys.path.insert(0, str(HERE))
import rs02_props, rs_collision, rs01_stair
from ti_core import S

ART = HERE.parents[1]
KIT = 'village-reskin-b'
LODB = ART / 'exports' / 'lod-backfill-b'
SRC = LODB / 'TownInn' / 'TownInn_LOD_v001.blend'
SRC_INFO = LODB / 'TownInn' / 'model_info.json'
SHOP_SRC = ART / 'incoming' / 'dondon' / 'MaterialShop' / 'v001' / 'MaterialShop_v001.blend'
GATE_SRC = ART / 'incoming' / 'dondon' / 'SectGate' / 'v001' / 'SectGate_v001.blend'

# source material -> (palette key, export group, grain rule)
INN_MAP = {
    'TL09_Timber': ('timber', 'Wood'), 'TL09_Board': ('plank', 'Wood'), 'TL09_Lacquer': ('door', 'Wood'),
    'TL09_Plaster': ('plaster', 'Main'), 'TL09_Paper': ('paper', 'Main'), 'TL09_Lantern': ('lantern', 'Main'),
    'TL09_Cloth': ('cloth', 'Main'), 'TL09_Rope': ('rope', 'Main'), 'TL09_Brass': ('brass', 'Main'), 'TL09_Iron': ('iron', 'Main'),
    'TL09_Clay': ('clay', 'Main'),
    'TL09_Stone': ('stone', 'Stone'), 'TL09_Pale': ('stone_pale', 'Stone'),
    'TL09_Tile': ('tile', 'Tile'), 'TL09_Glaze': ('tile_ridge', 'Tile'),
}
# the source's four or five shades of one material alternate between two VL materials, so the courses still read apart
SMITHY_MAP = {
    'Smithy_Aged_Timber': ('timber', 'Wood'), 'Smithy_Workbench_Wood': ('plank', 'Wood'),
    **{f'Smithy_Jade_Tile_{i}': ('tile_b' if i % 2 else 'tile', 'Tile') for i in range(4)},
    **{f'Smithy_Bluestone_{i}': ('stone_b' if i % 2 else 'stone', 'Stone') for i in range(4)},
    **{f'Forge_Firebrick_{i}': ('firebrick_b' if i % 2 else 'firebrick', 'Stone') for i in range(4)},
    'Smithy_Joints': ('mortar', 'Stone'),
    'Forged_Dark_Iron': ('forged_iron', 'Main'), 'Brushed_Sword_Steel': ('steel', 'Main'), 'Smithy_Old_Brass': ('brass', 'Main'),
    'Charcoal': ('charcoal', 'Main'), 'Quench_Water': ('water', 'Main'), 'Hot_Ember': ('ember', 'Main'),
}
# RS03 the sect gate: old wood, dark tile, bronze fittings, grey-white granite base (work pack: SG and RS03 granite #C9C6BD)
GATE_MAP = {
    'Dark_Chestnut': ('timber', 'Wood'), 'Warm_Timber': ('door', 'Wood'),
    'Blue_Green_Tiles': ('tile', 'Tile'), 'Tile_Roll_Highlight': ('tile_b', 'Tile'),
    'Aged_Brass': ('bronze', 'Main'), 'Recess_Shadow': ('recess', 'Main'), 'Celadon_Jade': ('jade', 'Main'),
    'Pale_Stone': ('granite', 'Stone'), 'Blue_Gray_Stone': ('granite_b', 'Stone'),
}
SHOP_MAP = {
    'Aged_Chestnut_Timber': ('timber', 'Wood'), 'Worn_Porch_Boards': ('plank', 'Wood'),
    **{f'Celadon_Grey_Tile_{i}': ('tile_b' if i % 2 else 'tile', 'Tile') for i in range(5)},
    **{f'Blue_Stone_{i}': ('stone_b' if i % 2 else 'stone', 'Stone') for i in range(4)}, 'Dark_Joint': ('mortar', 'Stone'),
    'Warm_Lime_Plaster': ('plaster', 'Main'), 'Warm_Window_Paper': ('paper', 'Main'), 'Dark_Brass': ('brass', 'Main'),
    'Shop_Glazed_Jar_0': ('jar_green', 'Main'), 'Shop_Glazed_Jar_1': ('jar_brown', 'Main'), 'Shop_Glazed_Jar_2': ('jar_buff', 'Main'),
    'Shop_Ochre_Canvas': ('awning', 'Main'), 'Shop_Linen_Sacks': ('sack', 'Main'), 'Shop_Dried_Herbs': ('herbs', 'Main'),
    'Shop_Jade_Ore': ('ore', 'Main'), 'Shop_Dark_Coin_Centre': ('coin_centre', 'Main'),
}


def _rs02_base():
    """Kept-up working buildings: the VL 'diligent' set, the VH old-wood timber (vh_wood, 'diligent'), dark fired tile in two shades."""
    import vh_wood as vw
    P = vl_mats.palette('diligent')
    P['stone'], P['stone_b'] = P['stone']
    vw.apply(P, 'diligent')
    P['tile'] = cm.tile('Shop_Roof_Tile', base=(.03, .038, .048), light=(.07, .08, .094), moss=.5)
    P['tile_b'] = cm.tile('Shop_Roof_Tile_B', base=(.034, .04, .048), light=(.078, .084, .094), moss=.4)
    return P


def palette_smithy():
    P = _rs02_base()
    # forge brick: dull fired clay darkened by soot (the source's warm tan read as new)
    P['firebrick'] = cm.stone('Forge_Brick', light=(.17, .115, .08), dark=(.06, .04, .03), ochre=(.15, .08, .045), moss=0., lichen=0., crack=.45)
    P['firebrick_b'] = cm.stone('Forge_Brick_B', light=(.14, .1, .075), dark=(.05, .036, .028), ochre=(.12, .07, .04), moss=0., lichen=0., crack=.5)
    mk = __import__('mk_mats')
    P['forged_iron'] = mk.cast_iron('Forged_Iron')
    P['steel'] = tm.metal('Blade_Steel', (.46, .47, .47), (.16, .15, .14), rough=.3, patina_amt=.2, patina_scale=30.)
    P['charcoal'] = tm.plain('Charcoal_Lump', (.016, .014, .012), rough=.95, noise=.5, bump=.3)
    P['water'] = tm.plain('Quench_Water', (.012, .017, .017), rough=.08, noise=.05, bump=0.)
    P['ember'] = tm.emissive('Forge_Ember', (.05, .02, .01), (1., .3, .05), 'Main')
    tm.set_emission(P['ember'], 3.)          # preview only: the bake reads the emission colour; the baked material starts at 0 (the game sets the glow)
    rs02_props.palette_extra_smithy(P)
    return P


def palette_shop():
    P = _rs02_base()
    P['plaster'] = vl_mats.plaster('Lime_Plaster_Shop', peel=.02, repair=.15, grime=.6, cracks=.35, seed=(2.1, 0., 0.))
    P['jar_green'] = tm.glaze('Jar_Glaze_Green', (.05, .075, .06), (.02, .03, .025))       # dull celadon, not bright teal
    P['jar_brown'] = tm.glaze('Jar_Glaze_Brown', (.1, .055, .028), (.04, .022, .012))
    P['jar_buff'] = tm.glaze('Jar_Glaze_Buff', (.34, .3, .21), (.16, .13, .08), rough=.3)
    P['awning'] = cm.canvas('Awning_Canvas', base=(.27, .18, .085), stain=(.1, .06, .025), faded=.5, dirt=.6)
    P['sack'] = cm.canvas('Sack_Linen', base=(.3, .25, .16), stain=(.12, .09, .05), faded=.3, dirt=.7)
    P['herbs'] = tm.plain('Dried_Herbs', (.06, .07, .03), rough=.9, noise=.5, bump=.3)
    P['ore'] = cm.stone('Jade_Ore', light=(.1, .16, .13), dark=(.03, .05, .04), ochre=(.09, .1, .08), moss=0., lichen=0., crack=.3)
    P['coin_centre'] = tm.plain('Coin_Centre', (.035, .03, .022), rough=.7)
    rs02_props.palette_extra_shop(P)
    return P


def palette_gate():
    """RS03: the bright teal and glossy finish of the source toned down. Old dark timber (vh_wood 'elderly'), dark fired tile, aged bronze
    with green in the recesses, grey-white granite (#C9C6BD in sRGB is linear .58 .56 .51) weathered with lichen, rain darkening low down."""
    import vh_wood as vw
    P = vl_mats.palette('diligent')
    vw.apply(P, 'elderly')
    P['tile'] = cm.tile('Gate_Roof_Tile', base=(.03, .037, .048), light=(.066, .076, .092), moss=.25)        # #3A4048 dark tile; moss .6 read olive (#34372F)
    P['tile_b'] = cm.tile('Gate_Roll_Tile', base=(.034, .041, .052), light=(.074, .083, .098), moss=.2)
    # dark aged bronze, not new brass: mk_mats.brass (rough .32) read as polished gold in the URP shots (ridge-end caps, plaque rim),
    # the sky caught in the smooth metal; rougher, darker, more patina pooled in the recesses
    # patina .85 still left the plain cylinder caps bare metal (the mask is crevice + noise x amount): 1.35 covers about half of a plain
    # surface with green-grey patina, so the caps read weathered, bronze showing through in patches
    P['bronze'] = tm.metal('Gate_Bronze', (.12, .075, .035), (.05, .085, .065), slot='Main', rough=.6, patina_amt=1.35, patina_scale=30.,
                           crevice=2.4)
    P['recess'] = tm.plain('Plaque_Recess', (.03, .028, .024), rough=.85, noise=.25)
    P['jade'] = cm.stone('Gate_Jade_Inlay', light=(.07, .09, .08), dark=(.025, .035, .03), ochre=(.08, .09, .07), moss=0., lichen=0., crack=.25)
    # granite white #C9C6BD (work pack): the first try (light .58, dark .30, moss .35) baked the visible top to #9D9A92, too dark
    P['granite'] = cm.stone('Gate_Granite', light=(.82, .80, .74), dark=(.6, .585, .53), ochre=(.52, .49, .42), moss=.15, lichen=.35, crack=.3,
                            wet_z=.25)
    P['granite_b'] = cm.stone('Gate_Granite_B', light=(.74, .725, .67), dark=(.52, .505, .46), ochre=(.46, .44, .37), moss=.2, lichen=.4, crack=.35,
                              wet_z=.25)
    return P


def palette():           # RS01 inn
    P = vl_mats.palette('diligent')
    P['stone'] = P['stone'][0]
    # an inn in use: the VL lime plaster with few repair patches (the 'diligent' patches read as blotches at the inn's 8 m wall height)
    P['plaster'] = vl_mats.plaster('Lime_Plaster_Inn', peel=.02, repair=.12, grime=.6, cracks=.35, seed=(0., 0., 0.))
    P['stone_pale'] = cm.stone('Edge_Stone', light=vl_mats.STONE[2], dark=vl_mats.STONE[0], ochre=(.2, .19, .15), moss=.35, lichen=.5, crack=.4)
    # dark fired tile, mean close to #3A4048 under the game's light (linear .042, .052, .065); ridge pieces a shade darker, no glaze
    P['tile'] = cm.tile('Inn_Roof_Tile', base=(.03, .038, .048), light=(.07, .08, .094), moss=.5)
    P['tile_ridge'] = cm.tile('Inn_Ridge_Tile', base=(.026, .032, .04), light=(.058, .066, .078), moss=.3)
    P['lantern'] = cm.paper('Lantern_Paper', base=(.62, .5, .3), edge=(.36, .25, .12), age=.35)
    P['cloth'] = cm.canvas('Banner_Cloth', base=(.1, .13, .12), stain=(.05, .05, .04), faded=.5, dirt=.5)
    P['rope'] = tm.plain('Hemp_Rope', (.24, .18, .1), rough=.9, noise=.3)
    return P


def grain_of(co):
    """Longest principal axis of a part's vertices: the wood grain runs along it."""
    c = co - co.mean(0)
    if len(c) < 3: return (1., 0., 0.)
    w, v = np.linalg.eigh(c.T @ c)
    a = v[:, int(np.argmax(w))]
    return tuple(float(x) for x in a)


def _not_exported(o):
    return any(k in c.name for c in o.users_collection for k in ('Not_Exported', 'Studio', 'Concept'))


def cap_open_tubes(objs, max_ring=32):
    """RS03 roof parts (tile rolls, tile overlaps, ridges, fascia and barge boards) are swept tubes left open at both ends. An open piece
    has no inside, so orient_faces cannot tell which way it faces and some came out inside-out (back-face check: 30 % red). Each open
    end ring is filled flat and triangulated: the piece is closed, faces outward, and the outline does not move."""
    before = after = parts = rings = 0
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bnd = [e for e in bm.edges if e.is_boundary]
        if not bnd: bm.free(); continue
        n0 = sum(len(f.verts) - 2 for f in bm.faces); old = set(bm.faces); mi = next(iter(old)).material_index
        res = bmesh.ops.holes_fill(bm, edges=bnd, sides=max_ring)
        left = [e for e in bm.edges if e.is_boundary]
        assert not left, (o.name, len(left), 'open edges left after capping')
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if f not in old])
        for f in bm.faces:
            if f not in old: f.material_index = mi
        n1 = sum(len(f.verts) - 2 for f in bm.faces); bm.to_mesh(o.data); bm.free(); o.data.update()
        before += n0; after += n1; parts += 1; rings += len(res['faces'])
    S['pre_edits'] = [{'part': f'{parts} open roof tubes capped ({rings} end rings)',
                       'why': 'back-face check: open swept tubes have no inside, so some came out facing inward (30 % red)',
                       'triangles_before': before, 'triangles_after': after}] if parts else []
    S['source_tris_added'] = after - before     # the counter below runs after this; model_info must keep the source's own count


def load_raw(cfg, aid):
    """A Dondon source with its parts as many objects and live modifiers: every exported mesh evaluated in world space (what its FBX
    holds), the origin kept; small parts to Detail_Small by the lod-backfill rule. Returns the body object and the detail object."""
    with bpy.data.libraries.load(str(cfg['src']), link=False) as (src, dst):
        dst.collections = [n for n in src.collections if n not in cfg['skip_collections']]
    tmp = bpy.data.collections.new('_SRC'); bpy.context.scene.collection.children.link(tmp)
    for c in dst.collections: tmp.children.link(c)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    pool = {o for c in dst.collections for o in c.all_objects if o.type == 'MESH' and not o.hide_render}
    out = []
    for o in sorted(pool, key=lambda o: o.name):
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg); me.transform(o.matrix_world)
        if len(me.polygons): out.append(bpy.data.objects.new('src_' + o.name, me))
        else: bpy.data.meshes.remove(me)
    for c in dst.collections:
        for o in list(c.objects): bpy.data.objects.remove(o, do_unlink=True)
    for c in dst.collections: bpy.data.collections.remove(c)
    bpy.data.collections.remove(tmp)
    for o in out: S['col'].objects.link(o)
    if cfg.get('cap_open'): cap_open_tubes(out)
    bpy.context.view_layer.update()
    co = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in out])
    size = co.max(0) - co.min(0)
    S['source_mesh_objects'] = len(out); S['source_dims'] = [round(float(v), 4) for v in size]
    dmax = min(.35, .12 * float(size.max()))
    def small(o):
        c = np.array([v.co[:] for v in o.data.vertices]); return float((c.max(0) - c.min(0)).max()) < dmax
    det = [o for o in out if small(o)]; body = [o for o in out if o not in det]
    S['source_detail_parts'] = len(det); S['source_body_parts'] = len(body)
    res = []
    for objs, name in ((body, f'{aid}_SRC_LOD0'), (det, f'{aid}_SRC_Detail_Small_LOD0')):
        if not objs: continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active; j.name = name; res.append(j)
    return res


def build_inn(P):
    cfg = SOURCES[S['asset']]
    if cfg.get('raw'):
        objs = load_raw(cfg, S['asset'])
    else:
        with bpy.data.libraries.load(str(cfg['src']), link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n in cfg['objects']]
        objs = dst.objects
        for o in objs: S['col'].objects.link(o)
    S['source_parts'] = {}
    for o in objs:
        detail = 'Detail_Small' in o.name
        bpy.context.view_layer.update()
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        me = o.data
        S['source_tris'] = S.get('source_tris', 0) + sum(len(p.vertices) - 2 for p in me.polygons)
        # the pipeline drops zero-area faces (orient_faces: they bake to zero-area UVs); count the source's own so the check can tell
        bm = bmesh.new(); bm.from_mesh(me); n_in = sum(len(f.verts) - 2 for f in bm.faces)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
        dead = [f for f in bm.faces if f.calc_area() < 1e-10]
        if dead: bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
        S['source_degenerate'] = S.get('source_degenerate', 0) + n_in - sum(len(f.verts) - 2 for f in bm.faces); bm.free()
        # one object per material, then per loose part
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
        by_mat = list(bpy.context.selected_objects)
        bpy.ops.object.select_all(action='DESELECT')
        for m_o in by_mat:
            if not m_o.data.polygons:                  # separate() leaves the emptied original behind
                bpy.data.objects.remove(m_o); continue
            src_mat = m_o.data.materials[m_o.data.polygons[0].material_index].name
            if src_mat not in cfg['map']: src_mat = src_mat.rsplit('.', 1)[0]
            m_o.select_set(True); bpy.context.view_layer.objects.active = m_o
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
            parts = list(bpy.context.selected_objects); bpy.ops.object.select_all(action='DESELECT')
            for q in [q for q in parts if not q.data.polygons]: parts.remove(q); bpy.data.objects.remove(q)
            key, group = cfg['map'][src_mat]
            S['source_parts'][src_mat] = S['source_parts'].get(src_mat, 0) + len(parts)
            for q in parts:
                me_q = q.data
                co = np.zeros(len(me_q.vertices) * 3, np.float32); me_q.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
                me_q.materials.clear(); me_q.materials.append(P[key])
                q.data.polygons.foreach_set('material_index', [0] * len(me_q.polygons))
                ti_core.finish(q, f'{src_mat[5:] if src_mat.startswith("TL09_") else src_mat}_Part', None, grain=grain_of(co) if group == 'Wood' else 'x',
                               detail=1 if detail else 0, group='Detail_Small' if detail else group)
    S['shape_edits'] = S.pop('pre_edits', [])
    if cfg.get('fix'): cfg['fix'](P)
    S['source_coplanar_nudged'] = part_coplanar_nudge([q for q in S['parts'] if q.type == 'MESH'], **cfg.get('nudge', {}))
    S['collision_mesh'] = None
    col = cfg.get('collide')
    if col is not None:                    # RS02/RS03: one box per part a walker can reach (rs_collision.py)
        V, F, n, names = rs_collision.boxes([q for q in S['parts'] if q.type == 'MESH'], col.get('skip', ()), zmax=col.get('zmax', 2.2))
        S['collision_mesh'] = (V, F)
        S['collision_boxes'] = {'boxes': n, 'triangles': 2 * len(F), 'skipped_parts': list(col.get('skip', ())),
                                'rule': f'one box per part with its lowest point under {col.get("zmax", 2.2)} m (roof tile and Detail_Small none): the smaller of its axis-aligned '
                                        'and principal-axes box, thin sides opened to 2 cm', 'by_part': dict(sorted(names.items()))}



def collision_probes(aid, check, cfg):
    """Rays straight down from 6 m onto <ID>_Collision at points read off the model: floor, step and platform tops where a walker stands,
    blocks (forge, counter) where it is stopped, open ground (no box) beside the building."""
    from mathutils.bvhtree import BVHTree
    o = S.get('collision_obj'); probes = (cfg.get('collide') or {}).get('probes')
    if not o or not probes: return None
    t = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get()); res = []
    for pr in probes:
        name, x, y, lo, hi = pr[:5]; z0 = pr[5] if len(pr) > 5 else 6.      # RS01: ground-floor probes start under the upper floor
        h = t.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), z0 + 1.)
        z = None if h[0] is None else round(h[0].z, 3)
        ok = (z is None) if lo is None else (z is not None and lo <= z <= hi)
        res.append({'probe': name, 'xy': [x, y], 'ray_from_z_m': z0, 'top_z_m': z, 'expected': None if lo is None else [lo, hi], 'ok': ok})
    check('collision_probe_tops', all(r['ok'] for r in res), res)
    return res


def part_coplanar_nudge(objs, push=.001, tol=.0005):
    """The source has faces of two different parts lying in one plane, facing the same way (partition panels over wall panels, plate tops
    under the roof). With one flat colour on both nothing showed; baked into an atlas each face reads its own texels and they z-fight.
    The face of the smaller of the two parts is pulled 1 mm back along its normal (its vertices only, so the part stays closed), repeated
    while any pair is left (stacks of three or four); triangle count and outside size do not change. Returns the counts and the largest shift."""
    import importlib
    near_pairs = importlib.import_module('qa_fbx').near_pairs
    def gather():
        V, T, owner, poly = [], [], [], []
        for k, o in enumerate(objs):
            me = o.data; me.calc_loop_triangles(); base = len(V); mw = o.matrix_world
            V += [tuple(mw @ v.co) for v in me.vertices]
            for lt in me.loop_triangles: T.append([base + i for i in lt.vertices]); owner.append(k); poly.append(lt.polygon_index)
        return np.array(V, np.float64), np.array(T, np.int64), owner, poly
    for o in objs: B.pl.orient_faces(o.data, flush=False)      # face each part outward first, as join_groups will: a pair that is two sides now can be one side then
    size = [sum(p.area for p in o.data.polygons) for o in objs]
    shift = {}; found = moved = 0; rounds = 0
    for rounds in range(1, 7):         # faces stacked three or four deep: a face pulled back can meet the next layer, so repeat
        V, T, owner, poly = gather()
        # pairs inside one part count too: the pipeline later parts such overlapping twins (part_twins) and they z-fight the same way
        pairs = [(a, b) for a, b, area, d in near_pairs(V, T, tol) if d > 0 and (owner[a], poly[a]) != (owner[b], poly[b])]
        if rounds == 1: found = len(pairs)
        if not pairs: break
        moves = {}
        for a, b in pairs:
            if owner[a] == owner[b]:      # within one part: the smaller face goes back
                pa, pb = (objs[owner[a]].data.polygons[poly[x]].area for x in (a, b)); t = a if (pa, poly[a]) <= (pb, poly[b]) else b
            else: t = a if (size[owner[a]], owner[a]) <= (size[owner[b]], owner[b]) else b
            moves.setdefault(owner[t], set()).add(poly[t])
        for k, polys in moves.items():
            me = objs[k].data; delta = {}
            for pi in polys:
                p = me.polygons[pi]
                for vi in p.vertices: delta[vi] = delta.get(vi, Vector()) - p.normal * push
            for vi, d in delta.items():
                if d.length > push: d = d.normalized() * push        # a corner shared by two moved faces moves 1 mm, not 1.4
                me.vertices[vi].co += d; shift[(k, vi)] = shift.get((k, vi), 0.) + d.length
            me.update()
        moved += sum(len(v) for v in moves.values())
    V, T, owner, poly = gather()
    left = [(a, b) for a, b, area, d in near_pairs(V, T, tol) if d > 0 and (owner[a], poly[a]) != (owner[b], poly[b])]
    return {'pairs_found': found, 'faces_moved': moved, 'rounds': rounds, 'pairs_left': len(left), 'push_m': push, 'tol_m': tol,
            'vertices_moved': len(shift), 'max_shift_m': round(max(shift.values(), default=0.), 4)}


def reskin_checks(aid, check, cfg):
    """Shape unchanged: LOD0 has the source's triangle count, size and bounds; the roof tile is dark and grey, not teal."""
    cfg = SOURCES[aid]
    if cfg.get('raw'):
        h = json.loads(cfg['info'].read_text(encoding='utf-8'))['blend']
        info = {'source_triangles': h['triangles'], 'dimensions_m': [round(v, 4) for v in h['size_m']]}
    else:
        info = json.loads(cfg['info'].read_text(encoding='utf-8'))
    lod0 = list(S['lods'][0].values()); lo, hi = B.pl.eval_bounds(lod0); dims = [round(v, 4) for v in hi - lo]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in lod0)
    deg = S.get('source_degenerate', 0)
    edits = S.get('shape_edits') or []; delta = sum(e['triangles_after'] - e['triangles_before'] for e in edits)
    st = S.get('stair_v002')          # RS01 v002: the stair parts taken out and the new ones (rs01_stair.rebuild) are the only change
    if st: delta += st['new_triangles'] - st['removed_v001_triangles']
    check('shape_unchanged_triangles', tris == info['source_triangles'] - deg + delta and deg <= info['source_triangles'] * .005,
          {'lod0_triangles': tris, 'source_triangles': info['source_triangles'], 'source_zero_area_dropped': deg,
           'reviewed_part_edits': edits, **({'stair_v002_removed_triangles': st['removed_v001_triangles'], 'stair_v002_new_triangles': st['new_triangles']} if st else {})})
    err = max(abs(a - b) for a, b in zip(dims, info['dimensions_m']))
    check('shape_unchanged_size', err < .002, {'dimensions_m': dims, 'source_dimensions_m': info['dimensions_m'], 'max_error_m': round(err, 5)})
    nud = S.get('source_coplanar_nudged') or {}
    check('source_coplanar_pulled_apart', nud.get('pairs_left') == 0 and nud.get('max_shift_m', 1) <= .0075, nud)     # no face moved more than 7.5 mm
    out = {'source_coplanar_nudged': nud}
    tex = S['tex_sets'].get(f'{aid}_Tile')
    if tex:
        im = bpy.data.images.load(str(tex['BaseColor']), check_existing=True); n = im.size[0]
        px = np.array(im.pixels[:], np.float32).reshape(-1, 4)[:, :3]; used = px[px.sum(1) > .02]
        mean = used.mean(0); srgb = [round(float(c), 3) for c in mean]        # an 8-bit sRGB PNG's .pixels are the stored sRGB values, not linear
        hexc = '#' + ''.join(f'{int(round(c * 255)):02X}' for c in srgb)
        sat = (max(srgb) - min(srgb)) / max(max(srgb), 1e-6)
        check('roof_tile_dark_not_teal', sat < .3 and max(srgb) < .4, {'tile_atlas_mean_srgb': srgb, 'hex': hexc, 'saturation': round(sat, 3),
              'target': '#3A4048', 'source_tile': cfg['source_tile']})
        out['tile_mean_hex'] = hexc
    out['source_parts_by_material'] = S.get('source_parts')
    if S.get('collision_boxes'):
        check('collision_boxes_made', S['collision_boxes']['boxes'] > 0 and bool(S.get('collision_obj')), {k: v for k, v in S['collision_boxes'].items() if k != 'by_part'})
        out['collision_probes'] = collision_probes(aid, check, cfg)
    return out


def tile_lod2_bands():
    """LOD2 of the inn's tile. 88 of its tile pieces are long closed bands (5.7 x 0.6 x 0.13 m tile courses lapped one over the next); a
    collapse decimate cannot take a band below ~50 triangles, so the Tile group stalls at 32 % instead of 15 %. At LOD2 each long band is
    rebuilt as a three-segment box that follows the band (slice extents at four stations along its length, 28 triangles), its UVs taken
    from the nearest point of the band it replaces, so it reads the same baked atlas; the remaining tile pieces are decimated as before."""
    from mathutils.bvhtree import BVHTree
    from mathutils.interpolate import poly_3d_calc
    tris = lambda me: sum(len(p.vertices) - 2 for p in me.polygons)
    src, old = S['lod0']['Tile'], S['lods'][2]['Tile']
    bm0 = bmesh.new(); bm0.from_mesh(src.data); bm0.faces.ensure_lookup_table(); bm0.verts.ensure_lookup_table()
    seen, bands, band_faces = set(), [], set()
    for f0 in bm0.faces:
        if f0.index in seen: continue
        isl, todo = [f0], [f0]; seen.add(f0.index)
        while todo:
            f = todo.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); todo.append(g); isl.append(g)
        P = np.array([v.co[:] for v in {v for f in isl for v in f.verts}]); c = P.mean(0)
        vt = np.linalg.svd(P - c, full_matrices=False)[2]; Q = (P - c) @ vt.T; ext = Q.max(0) - Q.min(0)
        if len(isl) >= 60 and ext[0] > 4 * ext[1] and ext[1] < 1. and ext[2] < .25:     # tile courses only; the 1.5 m wide pent board over the door stays a decimated mesh
            bands.append((isl, c, vt, Q)); band_faces.update(f.index for f in isl)
    # the rest: same decimate as the pipeline
    me = src.data.copy(); bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in band_faces], context='FACES'); bm.to_mesh(me); bm.free()
    o = src.copy(); o.data = me; S['lodcol'].objects.link(o)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    m = o.modifiers.new('LOD_decimate', 'DECIMATE'); m.use_collapse_triangulate = True; m.ratio = B.LOD_TARGET[2]
    bpy.ops.object.modifier_apply(modifier=m.name)
    B.pl.orient_faces(o.data, flush=False)
    # the band boxes
    bm = bmesh.new(); bm.from_mesh(o.data)
    uv0 = [bm0.loops.layers.uv[l.name] for l in src.data.uv_layers]; uv1 = [bm.loops.layers.uv[l.name] for l in src.data.uv_layers]
    new_faces = []
    for isl, c, vt, Q in bands:
        a0, a1, a2 = (Vector(v) for v in vt); c = Vector(c)
        vs = list({v for f in isl for v in f.verts}); q = np.array([(Vector(v.co) - c).dot(a0) for v in vs])
        lo, hi = q.min(), q.max(); st = np.linspace(lo, hi, 4); seg = (hi - lo) / 3
        rings = []
        for t in st:
            sel = [v for v, qq in zip(vs, q) if abs(qq - t) < seg * .3] or [vs[int(np.argmin(abs(q - t)))]]
            s1 = [(Vector(v.co) - c).dot(a1) for v in sel]; s2 = [(Vector(v.co) - c).dot(a2) for v in sel]
            ring = [c + a0 * float(t) + a1 * u + a2 * w for u, w in ((min(s1), min(s2)), (max(s1), min(s2)), (max(s1), max(s2)), (min(s1), max(s2)))]
            rings.append([bm.verts.new(p) for p in ring])
        fl = [bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k])) for r0, r1 in zip(rings, rings[1:]) for k in range(4)]
        fl += [bm.faces.new(rings[0][::-1]), bm.faces.new(rings[-1])]
        # UV (and material) from the band itself, sampled a little inside each new face so a corner reads its own side of the band
        tv, tf, owner = [], [], []
        for g in isl:
            b = len(tv); tv += [v.co.copy() for v in g.verts]
            for i in range(1, len(g.verts) - 1): tf.append((b, b + i, b + i + 1)); owner.append(g)
        tree = BVHTree.FromPolygons(tv, tf)
        for f in fl:
            fc = f.calc_center_median()
            for lp in f.loops:
                p = lp.vert.co.lerp(fc, .15); hit = tree.find_nearest(p)
                g = owner[hit[2]]; w = poly_3d_calc([v.co for v in g.verts], hit[0])
                for la, lb in zip(uv0, uv1):
                    lp[lb].uv = sum((gl[la].uv * wi for gl, wi in zip(g.loops, w)), Vector((0., 0.)))
            f.material_index = owner[tree.find_nearest(fc)[2]].material_index
        new_faces += fl
    bmesh.ops.triangulate(bm, faces=new_faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(o.data); bm.free(); bm0.free()
    B.pl.orient_faces(o.data, flush=False); B.pl.spread_zero_uv([o])
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except Exception: pass
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38))
    name = old.name; bpy.data.objects.remove(old); o.name = name; o.data.name = name
    S['lods'][2]['Tile'] = o
    S['tile_lod2_bands'] = len(bands)
    return tris(o.data)


_make_lods = B.make_lods
def make_lods():
    rep = _make_lods()
    if 'Tile' in S['lods'][2]:
        rep['Tile']['LOD2'] = tile_lod2_bands()
    return rep


def merge_per_lod():
    """As village-houses-b, with the Tile atlas joined in: one object per LOD with four material slots; Detail_Small apart."""
    a = S['asset']
    for lv, groups in S['lods'].items():
        parts = [groups[g] for g in ('Main', 'Stone', 'Wood', 'Tile') if g in groups]
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts: o.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active; j.name = f'{a}_LOD{lv}'; j.data.name = j.name
        S['lods'][lv] = {'Main': j, **{g: o for g, o in groups.items() if g not in ('Main', 'Stone', 'Wood', 'Tile')}}
    S['lod0'] = dict(S['lods'][0])


SOURCES = {
    'RS01_TownInn': dict(src=SRC, objects=('TownInn_LOD0', 'TownInn_Detail_Small_LOD0'), info=SRC_INFO, map=INN_MAP, fix=rs01_stair.rebuild,
                         # v002: two floors, so parts up to 6.15 m (upper floor 3.95 + 2.2) get boxes; the roof space over 6.7 m none
                         collide=dict(skip=('Lantern_Part', 'Rope_Part'), zmax=6.15,      # the door lanterns hang at 2.25-2.95 m outside, over head height
                                      probes=(('dining_floor', 2.0, -3.0, .47, .51, 3.5), ('ground_outside', 8.5, 0., None, None), ('entry_step', 5.9, 0., .2, .47, 2.0),
                                              ('flight1_tread_6', -2.65, -3.09, 1.5, 1.56), ('half_landing', -2.1, -5.2, 2.54, 2.6),
                                              ('flight2_tread_4', -1.55, -3.65, 3.23, 3.29), ('old_wall_end_gone', .51, -2.2, 3.93, 3.97), ('top_landing', -1.5, -2.0, 3.93, 3.97),
                                              ('upper_hall', 2.0, -3.0, 3.93, 3.97))),
                         source_tile='#486D6E (TL09_Tile), #507F75 glaze'),
    'RS02_Blacksmith': dict(src=LODB / 'Blacksmith' / 'Blacksmith_LOD_v001.blend', objects=('Blacksmith_LOD0', 'Blacksmith_Detail_Small_LOD0'),
                            info=LODB / 'Blacksmith' / 'model_info.json', map=SMITHY_MAP, fix=rs02_props.smithy_rework, nudge=dict(push=.0015, tol=.0011),      # RS02: pairs up to 1.1 mm apart, pulled 1.5 mm
                            # forge bricks, soot lining, coal bed and embers lie inside the forge core's box; the quench water inside the tub's
                            collide=dict(skip=('Forge_Brick', 'Forge_Soot_Lining', 'Forge_Coal_Bed', 'Forge_Burning', 'Charcoal', 'Hot_Ember', 'Coal_Lump', 'Quench_Water'),
                                         probes=(('floor', 0., -2.0, .12, .2), ('floor_by_anvil', 1.5, -.2, .16, .2), ('forge', -1.8, 1.0, 1.85, 6.),
                                                 ('anvil_stump', .25, -.75, .5, 1.2), ('ground_outside', 0., -3.6, None, None))),
                            source_tile='Smithy_Jade_Tile_0-3, linear (.07-.115, .14-.185, .15-.195)'),
    'RS02_MaterialShop': dict(src=SHOP_SRC, raw=True, info=SHOP_SRC.parent / 'handoff_check.json', map=SHOP_MAP, fix=rs02_props.shop_jars, nudge=dict(push=.0015, tol=.0011),
                              # the jars, ore and herb bundles are goods on the shelves (inside the shelf's reach), the window paper inside its frame
                              collide=dict(skip=('Jar_', 'Warm_Window_Paper', 'Shop_Jade_Ore', 'Shop_Dried_Herbs'),
                                           probes=(('step_1', 0., -4.5, .15, .21), ('porch', .2, -3.2, .52, .56), ('floor_inside', 0., 0., .52, .56),
                                                   ('ground_outside', 0., -5.2, None, None))),
                              skip_collections=('90_Studio_Not_Exported', 'Collection'),        # studio floor, lights, camera; 'Collection' is not in the scene
                              source_tile='Celadon_Grey_Tile_0-4, linear (.065-.105, .13-.178, .14-.188)'),
    'RS03_SectGate': dict(src=GATE_SRC, raw=True, info=GATE_SRC.parent / 'handoff_check.json', map=GATE_MAP, nudge=dict(push=.0015, tol=.0011), cap_open=True,
                          collide=dict(skip=(), probes=(('step_1', 0., -2.1, .14, .18), ('platform_gateway', 0., .4, .48, .52), ('platform_back', 0., 1.9, .48, .52),
                                                        ('ground_side', -4.8, 0., None, None))),
                          skip_collections=('90_Studio_Not_Exported',),
                          source_tile='Blue_Green_Tiles linear (.065, .15, .155), Tile_Roll_Highlight (.11, .22, .22)'),
}


def register_rs03():
    h = json.loads(SOURCES['RS03_SectGate']['info'].read_text(encoding='utf-8'))['blend']
    lo, hi = h['bounds_min_m'], h['bounds_max_m']
    B.ASSETS['RS03_SectGate'] = dict(kind='reskin', tex=2048, ver='v001', uv_detach_zero=True,
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood'], 'Tile': ['Tile']},
        zh='山門換材質（舊木、黛瓦、銅件、花崗石基）', palette=palette_gate, build=build_inn,
        limit=[h['size_m'][0] + .04, h['size_m'][1] + .04, h['size_m'][2] + .02],
        box=((lo[0] - .02, lo[1] - .02, 0.), (hi[0] + .02, hi[1] + .02, hi[2] + .02)),
        slot='B1_SectGate', ref='SectGate/(no three-view: a re-texture)',
        note='Dondon SectGate v001 的三開間山門，外形不動；鮮豔青綠加光滑的材質改成舊木、深瓦、銅件、灰白花崗石基，顏色收斂，有雨痕和磨損（11/09 工作包 RS03）；原檔不改，另存新檔',
        method='every exported mesh of the source evaluated with its modifiers (what the source FBX holds), origin kept (bottom centre); parts under min(0.35 m, 12 % of the size) '
               'to Detail_Small; then as RS01: loose parts, vertices unchanged except the 1.5 mm coplanar pull-back; the 9 flat source materials swapped for the VL / VH set, four 2048 atlases',
        based_on='art/incoming/dondon/SectGate/v001/SectGate_v001.blend (Dondon SectGate v001; read only, not changed)')


def register_rs02():
    common = dict(kind='reskin', tex=2048, ver='v001', uv_detach_zero=True,      # ti_pipeline.detach_zero_uv: no texel claimed twice
                  atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood'], 'Tile': ['Tile']})
    d = json.loads(SOURCES['RS02_Blacksmith']['info'].read_text(encoding='utf-8'))['dimensions_m']
    B.ASSETS['RS02_Blacksmith'] = dict(common, zh='鐵匠鋪換材質（VL 質感）', palette=palette_smithy, build=build_inn,
        # the anvil face is one UV piece with the hardy and pritchel holes in it: CONCAVE packing nested the hole walls into that hole and
        # they overlapped (316 texels, largest 39); CONVEX packs by outline
        uv_shape='CONVEX',
        # the source origin is centred in x only (lod-backfill kept it): y runs -3.023 .. 2.700 (the eave overhangs the front)
        limit=[d[0] + .04, d[1] + .04, d[2] + .02], box=((-d[0] / 2 - .02, 2.7 - d[1] - .02, 0.), (d[0] / 2 + .02, 2.72, d[2] + .02)),
        slot='TownLayout_Blacksmith', ref='Blacksmith/(no three-view: a re-texture)',
        note='Dondon Blacksmith v001 的鐵匠鋪，外形不動，瓦、木、石、爐磚、鐵件換成 VL／VH 那一套質感（11/09 工作包 RS02）；原檔不改，另存新檔',
        method='as RS01: the lod-backfill LOD0 split into its loose parts, vertices unchanged (except the 1 mm coplanar pull-back); the 21 flat source materials '
               'swapped for the VL / VH procedural set, baked to four 2048 atlases (Main, Stone, Wood, Tile; the forge embers also an emission map); LOD1/LOD2 rebuilt from the new LOD0',
        based_on='art/exports/lod-backfill-b/Blacksmith/Blacksmith_LOD_v001.blend (Dondon Blacksmith v001; the source files are not changed)')
    h = json.loads(SOURCES['RS02_MaterialShop']['info'].read_text(encoding='utf-8'))['blend']
    lo, hi = h['bounds_min_m'], h['bounds_max_m']
    B.ASSETS['RS02_MaterialShop'] = dict(common, zh='材料鋪換材質（VL 質感）', palette=palette_shop, build=build_inn,
        limit=[h['size_m'][0] + .04, h['size_m'][1] + .04, h['size_m'][2] + .02],
        box=((lo[0] - .02, lo[1] - .02, 0.), (hi[0] + .02, hi[1] + .02, hi[2] + .02)),
        slot='TownLayout_MaterialShop', ref='MaterialShop/(no three-view: a re-texture)',
        note='Dondon MaterialShop v001 的材料鋪，外形不動，瓦、牆、木、石、貨品換成 VL／VH 那一套質感（11/09 工作包 RS02）；原檔不改，另存新檔；原點照原檔（和 StarterHouse／VL 相同）',
        method='every exported mesh of the source evaluated with its modifiers (what the source FBX holds), origin kept; parts under min(0.35 m, 12 % of the size) '
               'to Detail_Small; then as RS01: loose parts, vertices unchanged except the 1 mm coplanar pull-back; the 23 flat source materials swapped for the VL / VH set, four 2048 atlases',
        based_on='art/incoming/dondon/MaterialShop/v001/MaterialShop_v001.blend (Dondon MaterialShop v001; read only, not changed)')


def register():
    src = json.loads(SRC_INFO.read_text(encoding='utf-8'))
    d = src['dimensions_m']
    B.ASSETS['RS01_TownInn'] = dict(
        kind='reskin', zh='客棧換材質（VL 質感）', palette=palette, build=build_inn, tex=2048, ver='v002', uv_detach_zero=True,
        atlases={'Main': ['Main', 'Detail_Small'], 'Stone': ['Stone'], 'Wood': ['Wood'], 'Tile': ['Tile']},
        limit=[d[0] + .04, d[1] + .04, d[2] + .02], box=((-d[0] / 2 - .02, -d[1] / 2 - .02, 0.), (d[0] / 2 + .02, d[1] / 2 + .02, d[2] + .02)),
        slot='TownLayout_TownInn', ref='TownInn/(no three-view: a re-texture)',
        note='Dondon TownLayout v004 的客棧，瓦、牆、木、石全部換成 VL01–05 那一套質感（11/09 工作包 RS01）；原檔不改，另存新檔。'
             'v002（2026-11-10，使用者決定）：原樓梯太陡（38.7°、踏面 25 cm、鏤空）、起步卡在牆角、頂端撞客房隔間，人上不了二樓，'
             '改成雙跑折返梯（20 階、每階 17.3 cm、踏面 28 cm、約 32°），頂平台向東接二樓走廊；加中牆、樓梯下封板、二樓樓梯井欄杆；其他不動',
        method='source mesh split into its loose parts with vertices unchanged (except: where two parts had faces in one plane facing the same way, the face of the smaller part is pulled back 1 mm so the baked atlas does not z-fight); the 15 flat source materials swapped for the VL procedural set '
               '(art/source/village-reskin-b/), baked to four 2048 atlases (Main, Stone, Wood, Tile); LOD1/LOD2 rebuilt from the new LOD0; at LOD2 the 88 long tile-course bands are three-segment boxes reading the same atlas (a collapse decimate stalls on them)',
        based_on='art/exports/lod-backfill-b/TownInn/TownInn_LOD_v001.blend (from TownLayout v004; the source files are not changed)')


register()
register_rs02()
register_rs03()
B.reskin_checks = reskin_checks
B.merge_per_lod = merge_per_lod
B.make_lods = make_lods
B.KIT = KIT


def compare(aid):
    """Original (lod-backfill-b LOD0, its flat colours) and the re-textured LOD0, same studio light and camera, side by side."""
    prev = ART / 'previews' / KIT / aid; tmp = prev / '_cmp'; tmp.mkdir(parents=True, exist_ok=True)
    views = (('three_quarter', (1, -1.25, .55)), ('front', (0, -1, .12)), ('back_left', (-1, 1.1, .45)))
    cfg = SOURCES[aid]
    for tag, path in (('original', cfg['src']), ('reskin', ART / 'source' / KIT / 'blend' / f'{aid}_v001.blend')):
        bpy.ops.wm.open_mainfile(filepath=str(path))
        raw = tag == 'original' and cfg.get('raw')
        if raw:            # the source's own studio floor, lights and camera out; the comparison uses the pipeline's studio for both
            for o in [o for o in bpy.data.objects if o.type in ('LIGHT', 'CAMERA') or (o.type == 'MESH' and _not_exported(o))]:
                bpy.data.objects.remove(o, do_unlink=True)
        if tag == 'reskin':
            for img in bpy.data.images:
                if img.source == 'FILE' and img.filepath:
                    p = ART / 'exports' / KIT / aid / 'Textures' / Path(bpy.path.abspath(img.filepath)).name
                    if p.exists(): img.filepath = str(p); img.reload()
        objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.split('.')[0].endswith('_LOD0') and 'Collision' not in o.name]
        if raw: objs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and o.users_scene]
        if tag == 'reskin':        # the forge embers glow in the original render: light the baked emission the same way for the comparison
            for m in bpy.data.materials:
                nd = m.node_tree.nodes.get('EMIT_STRENGTH') if m.node_tree else None
                if nd: nd.outputs[0].default_value = 3.
        for name, d in views:
            B.pl.persp_shot(objs, tmp / f'{tag}_{name}.png', direction=d, samples=64)
    for name, _ in views:
        B._strip([tmp / f'original_{name}.png', tmp / f'reskin_{name}.png'], prev / f'{aid}_compare_{name}_original_vs_reskin.png')
    for q in tmp.iterdir(): q.unlink()
    tmp.rmdir()


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ids = [a for a in argv if a in B.ASSETS and a.startswith('RS')] or ['RS01_TownInn']
    if '--compare' in argv:
        for aid in ids: compare(aid)
    elif '--preview' in argv:
        for aid in ids: B.preview(aid, Path(argv[argv.index('--preview') + 1]))
    else:
        for aid in ids:
            B.run(aid, '--force' in argv)
            mi = ART / 'exports' / KIT / aid / 'model_info.json'
            if mi.exists():          # the VL wording of these two fields does not fit a re-texture
                info = json.loads(mi.read_text(encoding='utf-8'))
                info['reference'] = 'no three-view (a re-texture, work pack: original and new side by side under the same light instead)'
                info['unity_import_verified'] = 'see artifacts/village-houses-unity/ (local Unity batch check VillageHousesModelCheck, not committed)'
                info['source_triangles'] = S.get('source_tris') - S.get('source_tris_added', 0)
                if S.get('uv_detached_zero_faces') is not None: info['uv_detached_zero_faces'] = S['uv_detached_zero_faces']     # ti_pipeline.detach_zero_uv
                if S.get('collision_boxes'): info['collision_boxes'] = S['collision_boxes']
                if S.get('stair_v002'): info['stair_v002'] = S['stair_v002']     # rs01_stair.rebuild
                mi.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
