"""承天 · 11/03 A 包的地面件（Johnnnny0823）：TY05 練功地面（兩種石板排法）、TY10 碎石小徑（直段兩種、收尾一種）。
The picked AI texture (art/references/<ID>/, see prompt.txt) is made seamless (half-offset copy cross-faded under a soft mask:
both axes for TY05, along the path for TY10), a height field is taken from its luminance (blurred, joints low), and from it come a
normal map, a cavity AO and a gently displaced ground mesh that never rises more than 1.5 cm above z = 0. LOD1 / LOD2 are coarser
grids. No collision (it is ground). Exports FBX (all LODs) + GLB (LOD0) + model_info entries next to the props.
blender -b --factory-startup -P build_ground_a.py -- TY05A TY05B TY10A TY10B TY10C
"""
import bpy, bmesh, json, math, sys
from pathlib import Path
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PKG = 'world-props-a'
REF = ROOT / 'art/references'; TEX = ROOT / 'art/textures' / PKG; OUT = ROOT / 'art/exports' / PKG
TEX.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
N = 2048
MAXH = .015

SPEC = {   # source pick, mesh size (x, y) m, texture metres per tile (u, v), variant transform, kind
    'TY05A': ('TY05/TY05_option2.png', (2.0, 2.0), (2.0, 2.0), dict(rot=0, shift=(0, 0)), 'slab'),
    'TY05B': ('TY05/TY05_option2.png', (2.0, 2.0), (2.0, 2.0), dict(rot=1, shift=(.37, .61)), 'slab'),
    'TY10A': ('TY10/TY10_option1.png', (1.0, 2.0), (1.0, 1.0), dict(rot=0, shift=(0, 0)), 'path'),
    'TY10B': ('TY10/TY10_option1.png', (1.0, 2.0), (1.0, 1.0), dict(rot=0, shift=(0, .5), flip=True), 'path'),
    'TY10C': ('TY10/TY10_option1.png', (1.0, 1.0), (1.0, 1.0), dict(rot=0, shift=(0, .25)), 'end'),
}


def load(path):
    im = bpy.data.images.load(str(path)); im.scale(N, N)
    a = np.array(im.pixels[:], np.float32).reshape(N, N, 4)[::-1, :, :3].copy(); bpy.data.images.remove(im); return a


def blur(a, r):
    k = np.exp(-np.linspace(-2, 2, 2 * r + 1) ** 2); k /= k.sum(); out = a
    for ax in (0, 1):
        out = sum(np.roll(out, i - r, axis=ax) * k[i] for i in range(2 * r + 1))
    return out


def seamless(a, both):
    """half-offset copy cross-faded under a soft mask: the original's wrap seam sits where the mask is 0"""
    y = np.linspace(-1, 1, N)[:, None]; x = np.linspace(-1, 1, N)[None, :]
    my = np.clip((1 - np.abs(y)) / .35, 0, 1); mx = np.clip((1 - np.abs(x)) / .35, 0, 1) if both else np.ones_like(x)
    m = (my * mx)[..., None]; m = m * m * (3 - 2 * m)
    rolled = np.roll(a, (N // 2, N // 2 if both else 0), axis=(0, 1))
    return a * m + rolled * (1 - m)


def save(name, rgb, data=False):
    im = bpy.data.images.new(name, N, N, alpha=True)
    if data: im.colorspace_settings.name = 'Non-Color'
    px = np.ones((N, N, 4), np.float32); px[..., :3] = np.clip(rgb, 0, 1)
    im.pixels.foreach_set(px[::-1].ravel()); im.filepath_raw = str(TEX / f'{name}.png'); im.file_format = 'PNG'; im.save(); return im


def run(pid):
    src, size, tile, var, kind = SPEC[pid]
    rid = src.split('/')[0]
    assert '選用：' in (REF / rid / 'prompt.txt').read_text(encoding='utf-8'), f'{pid}: pick a saved AI image first'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    a = load(REF / src)
    a = seamless(a, both=(kind == 'slab'))
    if var.get('rot'): a = np.rot90(a, var['rot']).copy()
    sx, sy = var.get('shift', (0, 0)); a = np.roll(a, (int(sy * N), int(sx * N)), axis=(0, 1))
    if var.get('flip'): a = a[:, ::-1].copy()
    lum = a @ np.array([.3, .59, .11], np.float32)
    h = blur(lum, 6); h = (h - h.min()) / max(1e-6, h.max() - h.min())
    hp = np.clip((h - blur(h, 24)) * 3 + .5, 0, 1)                 # local relief: stone tops vs joints
    ao = np.clip(.55 + .9 * blur(hp, 3) - .2, 0, 1)
    dx = (np.roll(hp, -1, 1) - np.roll(hp, 1, 1)) * 6; dy = (np.roll(hp, -1, 0) - np.roll(hp, 1, 0)) * 6
    n = np.dstack([-dx, dy, np.ones_like(hp)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    # gently grade the painted albedo toward the style guide: cool shade in joints, warm on tops
    alb = np.clip(a * (.88 + .12 * hp[..., None]) + (1 - hp[..., None]) * np.array([-.02, -.01, .02]) * .6, 0, 1)
    T = {'alb': save(f'T_{pid}_Albedo', alb), 'nrm': save(f'T_{pid}_Normal', n * .5 + .5, True),
         'orm': save(f'T_{pid}_ORM', np.dstack([ao, np.full_like(ao, .86), np.zeros_like(ao)]), True)}
    save(f'T_{pid}_MaskURP', np.dstack([np.zeros_like(ao), ao, np.zeros_like(ao)]), True)   # A (smoothness) written below
    im = bpy.data.images.load(str(TEX / f'T_{pid}_MaskURP.png')); px = np.array(im.pixels[:], np.float32).reshape(N, N, 4); px[..., 3] = .14
    im.pixels.foreach_set(px.ravel()); im.save()
    # material
    mat = bpy.data.materials.new(f'{pid}_Ground'); mat.use_nodes = True; nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
    def tn(img): t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; return t
    nt.links.new(tn(T['alb']).outputs['Color'], bs.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn(T['nrm']).outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
    sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tn(T['orm']).outputs['Color'], sp.inputs['Color']); nt.links.new(sp.outputs['Green'], bs.inputs['Roughness'])
    # meshes: displaced grids, edges held at z = 0 so they meet the terrain; the end piece narrows into grass
    W, L = size; root = bpy.data.objects.new(f'{pid}_GroundOrigin', None); bpy.context.scene.collection.objects.link(root)
    lods = []
    for lod, (nx, ny) in enumerate(((int(W * 64), int(L * 64)), (int(W * 32), int(L * 32)), (int(W * 10), int(L * 10)))):
        bm = bmesh.new(); V = []; uvs = []
        for j in range(ny + 1):
            row = []
            for i in range(nx + 1):
                u, v = i / nx, j / ny; x, y = (u - .5) * W, (v - .5) * L
                if kind == 'end':   # path end: the outline rounds off toward +y
                    half = .5 * W * math.sqrt(max(.04, 1 - max(0, (v - .35) / .65) ** 2)); x = (u - .5) * 2 * half
                tu, tv = (x / tile[0] + .5) % 1.0, (y / tile[1] + .5) % 1.0
                hh = float(hp[min(N - 1, int(tv * N)), min(N - 1, int(tu * N))])
                edge = min(u, 1 - u, v, 1 - v); fade = min(1, edge / .04)
                z = MAXH * hh * fade if lod < 2 else 0.0
                row.append(bm.verts.new((x, y, z))); uvs.append((x / tile[0] + .5, y / tile[1] + .5))
            V.append(row)
        for j in range(ny):
            for i in range(nx): bm.faces.new((V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]))
        me = bpy.data.meshes.new(f'{pid}_LOD{lod}'); bm.to_mesh(me); bm.free()
        uvl = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices: uvl.data[li].uv = uvs[me.loops[li].vertex_index]
        for poly in me.polygons: poly.use_smooth = True
        o = bpy.data.objects.new(f'{pid}_LOD{lod}', me); bpy.context.scene.collection.objects.link(o); me.materials.append(mat); o.parent = root
        o.hide_render = lod > 0; lods.append(o)
    tri = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / f'{pid}.blend'), compress=True)
    def sel(objs):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
    # FBX only (PR #68 review 11/07: one export format per item; Unity computes MikkTSpace tangents on import)
    sel([root] + lods); bpy.ops.export_scene.fbx(filepath=str(OUT / f'{pid}.fbx'), use_selection=True, object_types={'MESH', 'EMPTY'}, apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=True, axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False, bake_anim=False, path_mode='RELATIVE')
    zmax = max(v.co.z for v in lods[0].data.vertices)
    info = {'id': pid, 'kind': 'ground (embedded mesh + tiling texture)', 'dimensions_xyz_m': [W, L, round(zmax, 4)], 'max_height_above_ground_m': round(zmax, 4),
            'triangles_total': [tri(o) for o in lods], 'texture_px': N, 'texture_tile_m': list(tile),
            'textures': f'T_{pid}_Albedo / Normal / ORM / MaskURP (art/textures/{PKG})', 'reference': f'art/references/{rid}/prompt.txt',
            'origin': 'centre, ground plane z = 0', 'collision': None, 'minTier': 'standard', 'detailObjects': [],
            'note': {'TY05A': 'slab layout A', 'TY05B': 'slab layout B (same set, rotated and offset)', 'TY10A': 'straight 2 m', 'TY10B': 'straight 2 m, mirrored layout',
                     'TY10C': 'end piece: path rounds off into the grass at +Y'}[pid]}
    print('GROUND_DONE', json.dumps(info, ensure_ascii=False)); return info


ids = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(SPEC)
infos = [run(i) for i in ids]
mf = OUT / 'model_info.json'; old = json.loads(mf.read_text(encoding='utf-8')) if mf.exists() else {}
old.update({i['id']: i for i in infos}); mf.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding='utf-8')
