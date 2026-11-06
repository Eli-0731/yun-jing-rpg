"""BaseColor only, no light: shows what the atlas really holds on the delivered mesh. Reads only.
Renders the FBX's LOD0 with its BaseColor as plain emission from fixed angles, and samples the whole surface of every triangle (corners, edge middles, centre), not only UV centres.
blender --background --python qa_basecolor.py -- <asset.fbx> <BaseColor.png> <out_prefix> [centre_x centre_y centre_z radius]"""
import bpy, bmesh, json, sys, math
from pathlib import Path
from mathutils import Vector
import numpy as np

BLACK = .03   # linear luminance a painted surface never reaches here; only an unbaked texel does


def surface(objs, tex):
    w, h = tex.size; px = np.empty(w * h * 4, np.float32); tex.pixels.foreach_get(px); px = px.reshape(h, w, 4)
    lum = px[..., :3] @ np.array([.2126, .7152, .0722], np.float32)
    n = dark = 0; dark_area = area = 0.; faces = dark_faces = 0
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); uv = bm.loops.layers.uv.active
        for f in bm.faces:
            q = np.array([l[uv].uv[:] for l in f.loops], np.float64)
            s = np.vstack((q, (q[0] + q[1]) / 2, (q[1] + q[2]) / 2, (q[2] + q[0]) / 2, q.mean(0)))
            xy = np.clip((s * (w, h)).astype(int), 0, (w - 1, h - 1)); v = lum[xy[:, 1], xy[:, 0]]
            bad = int((v < BLACK).sum()); a = f.calc_area(); n += len(v); dark += bad; area += a; faces += 1
            if bad: dark_faces += 1; dark_area += a * bad / len(v)
        bm.free()
    return dict(samples=n, dark_samples=dark, dark_ratio=round(dark / max(n, 1), 6), faces=faces, faces_with_dark=dark_faces, dark_area_cm2=round(dark_area * 1e4, 2), area_m2=round(area, 3))


def main():
    a = sys.argv[sys.argv.index('--') + 1:]; fbx, png, out = a[0], str(Path(a[1]).resolve()), a[2]; close = [float(x) for x in a[3:7]] if len(a) >= 7 else None
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=str(fbx))
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or 'LOD1' in o.name or 'LOD2' in o.name or '_Collision' in o.name or o.name.lower().endswith('_water_lod0'): bpy.data.objects.remove(o)
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    tex = bpy.data.images.load(png); tex.colorspace_settings.name = 'Non-Color'
    rep = surface(objs, tex)
    m = bpy.data.materials.new('base'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = tex; t.interpolation = 'Closest'; e = nt.nodes.new('ShaderNodeEmission'); r = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(t.outputs[0], e.inputs[0]); nt.links.new(e.outputs[0], r.inputs[0])
    for o in objs: o.data.materials.clear(); o.data.materials.append(m)
    bpy.context.view_layer.update()
    co = np.array([tuple(o.matrix_world @ Vector(c)) for o in objs for c in o.bound_box])
    lo, hi = co.min(0), co.max(0); c = Vector((lo + hi) / 2); rad = float(np.linalg.norm(hi - lo)) / 2
    if close: c, rad = Vector(close[:3]), close[3]
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.device = 'CPU'; sc.render.resolution_x = sc.render.resolution_y = 1400; sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.render.image_settings.file_format = 'PNG'
    cam = bpy.data.cameras.new('c'); cam.type = 'PERSP'; cam.lens = 70; co = bpy.data.objects.new('c', cam); bpy.context.collection.objects.link(co); sc.camera = co; cam.clip_start = rad * .02; cam.clip_end = rad * 30
    angles = dict(front=(.8, -1, .55), rear=(-.8, 1, .55)) if not close else dict(close=(a[7:10] and tuple(float(x) for x in a[7:10])) or (.8, -1, .55))
    rep['renders'] = {}
    for name, d in angles.items():
        co.location = c + Vector(d).normalized() * rad * 2.9
        co.rotation_euler = (c - co.location).to_track_quat('-Z', 'Y').to_euler()
        p = f'{out}_{name}.png'; sc.render.filepath = str(Path(p).resolve()); bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(sc.render.filepath); w, h = im.size; px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(-1, 4)
        cov = px[:, 3] > .5; L = px[cov, :3] @ np.array([.2126, .7152, .0722]); rep['renders'][name] = dict(asset_pixels=int(cov.sum()), near_black_pixels=int((L < BLACK).sum()), near_black_ratio=round(float((L < BLACK).mean()) if len(L) else 0, 6))
    print('QABASE', Path(fbx).stem, json.dumps(rep))
    json.dump(rep, open(f'{out}.json', 'w'), indent=1)


main()
