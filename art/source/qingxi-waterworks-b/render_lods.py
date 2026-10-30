"""青溪水工 B：LOD0／LOD1／LOD2 並排預覽（讀匯出的 GLB，驗證同一檔案內三層都在、外形可用）。

用法（在 repo 根目錄）：
  blender -b --factory-startup --python art/source/qingxi-waterworks-b/render_lods.py -- [件號 ...]
輸出 art/previews/qingxi-waterworks-b/<件號>/<件號>_lods.png（左到右 LOD0、LOD1、LOD2，同一鏡頭）。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import kit_lib as K  # noqa: E402


def lod_of(o):
    n = o.name.rsplit(".", 1)[0] if o.name[-4:-3] == "." else o.name
    return 1 if n.endswith("_LOD1") else 2 if n.endswith("_LOD2") else 0


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ids = argv or sorted(d for d in os.listdir(K.EXPORT_DIR) if os.path.isfile(os.path.join(K.EXPORT_DIR, d, f"{d}.glb")))
    for pid in ids:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = 32
        sc.render.resolution_x, sc.render.resolution_y = 1500, 560
        w = bpy.data.worlds.new("w")
        w.color = (0.75, 0.74, 0.70)
        sc.world = w
        bpy.ops.import_scene.gltf(filepath=os.path.join(K.EXPORT_DIR, pid, f"{pid}.glb"))
        meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        bpy.context.view_layer.update()
        lo = Vector((1e9,) * 3)
        hi = Vector((-1e9,) * 3)
        for o in meshes:
            if lod_of(o) == 0:
                for c in o.bound_box:
                    p = o.matrix_world @ Vector(c)
                    lo = Vector(map(min, lo, p))
                    hi = Vector(map(max, hi, p))
        size = hi - lo
        gap = max(size.x, size.y) * 1.25
        # 三份複本左右排開：每份只留一層 LOD
        roots = [o for o in bpy.data.objects if o.parent is None]
        groups = []
        for k in range(3):
            if k == 0:
                objs = list(bpy.data.objects)
            else:
                objs = []
                mapping = {}
                for o in bpy.data.objects:
                    if o in groups[0]:
                        c = o.copy()
                        sc.collection.objects.link(c)
                        mapping[o] = c
                        objs.append(c)
                for o, c in mapping.items():
                    if o.parent in mapping:
                        c.parent = mapping[o.parent]
                for r in roots:
                    mapping[r].location.x += gap * k
            groups.append(objs)
        for k, objs in enumerate(groups):
            for o in objs:
                if o.type == "MESH":
                    o.hide_render = lod_of(o) != k
        tris = []
        for k, objs in enumerate(groups):
            n = 0
            for o in objs:
                if o.type == "MESH" and lod_of(o) == k:
                    o.data.calc_loop_triangles()
                    n += len(o.data.loop_triangles)
            tris.append(n)
        sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
        sun.data.energy = 3.0
        sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
        sc.collection.objects.link(sun)
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = gap * 3.1
        centre = (lo + hi) / 2 + Vector((gap, 0, 0))
        d = Vector((0.55, -1.0, 0.75)).normalized()
        cam.location = centre + d * 30
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(cam)
        sc.camera = cam
        out = os.path.join(K.PREVIEW_DIR, pid)
        os.makedirs(out, exist_ok=True)
        sc.render.filepath = os.path.join(out, f"{pid}_lods.png")
        bpy.ops.render.render(write_still=True)
        print(f"[lods] {pid}: LOD0 {tris[0]} / LOD1 {tris[1]} / LOD2 {tris[2]}")


if __name__ == "__main__":
    main()
