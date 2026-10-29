"""青溪水工 B：預覽渲染（中性／風格化、正側背頂、3/4、clay、線框、1.7 m 眼高）。

用法：
  blender -b <母稿.blend> --python art/source/qingxi-waterworks-b/render.py -- [件號 ...] [--out 目錄] [--quick]
輸出到 art/previews/qingxi-waterworks-b/<件號>/。比對板由 compose.py（Pillow）組成。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import kit_lib as K  # noqa: E402

VIEWS_ORTHO = {
    "front": ((0, -1, 0), "從入口（-Y）看"),
    "right": ((1, 0, 0), "右側（+X）"),
    "back": ((0, 1, 0), "背面（+Y）"),
    "top": ((0, 0, 1), "頂視"),
}


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ids, out, quick = [], K.PREVIEW_DIR, False
    i = 0
    while i < len(argv):
        if argv[i] == "--out":
            out = argv[i + 1]
            i += 2
            continue
        if argv[i] == "--quick":
            quick = True
        else:
            ids.append(argv[i])
        i += 1
    return ids, out, quick


def piece_objects(pid):
    coll = bpy.data.collections.get(pid)
    if coll is None:
        raise SystemExit(f"母稿中沒有 {pid}")
    solid = [o for o in coll.objects if o.type == "MESH" and not o.name.startswith("WATER_")]
    water = [o for o in coll.objects if o.name.startswith("WATER_")]
    return coll, solid, water


def isolate(pid):
    """只顯示指定件，並移回原點（母稿中各件排成一列）。"""
    root = bpy.data.collections[K.SET]
    for c in root.children:
        c.hide_render = c.name != pid
        for sub in c.children:
            sub.hide_render = True
    coll, solid, water = piece_objects(pid)
    body = bpy.data.objects[pid]
    shift = body.location.copy()
    for o in coll.objects:
        if o.parent is None:
            o.location -= Vector((shift.x, shift.y, 0))
    bpy.context.view_layer.update()
    return solid, water, coll, shift


def attach_wheel(pid):
    """B05 預覽時把 B06 掛到閘輪座（B06 仍是獨立交付件）。"""
    if pid != "B05" or "B06" not in bpy.data.collections:
        return None
    sock = bpy.data.objects.get("SOCKET_wheel_mount")
    wheel = bpy.data.objects["B06"]
    old = wheel.location.copy()
    bpy.data.collections["B06"].hide_render = False
    for sub in bpy.data.collections["B06"].children:
        sub.hide_render = True
    wheel.location = sock.matrix_world.translation
    bpy.context.view_layer.update()
    return wheel, old


def bbox(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def setup_render(quick, w=1100, h=820):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.film_transparent = False
    sc.eevee.taa_render_samples = 16 if quick else 64
    try:
        sc.eevee.use_shadows = True
        sc.eevee.use_raytracing = not quick
    except AttributeError:
        pass
    sc.view_settings.view_transform = "AgX"
    sc.render.image_settings.file_format = "PNG"


def world(color, strength):
    w = bpy.data.worlds.get("ww_world") or bpy.data.worlds.new("ww_world")
    bpy.context.scene.world = w
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength


def light(name, kind, loc, rot, energy, color=(1, 1, 1), size=None, angle=None):
    ob = bpy.data.objects.get(name)
    if ob is None:
        data = bpy.data.lights.new(name, kind)
        ob = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    ob.data.energy = energy
    ob.data.color = color
    if size is not None and kind == "AREA":
        ob.data.size = size
    if angle is not None and kind == "SUN":
        ob.data.angle = math.radians(angle)
    return ob


def look(mode):
    """neutral：中性灰棚；stylized：暖主光＋冷天光＋輪廓光（遊戲畫面方向）。"""
    for n in ("key", "fill", "rim"):
        if bpy.data.objects.get(n):
            bpy.data.objects[n].hide_render = False
    sc = bpy.context.scene
    if mode == "neutral":
        world((0.86, 0.85, 0.82), 0.75)
        light("key", "SUN", (0, 0, 5), (50, 0, -35), 2.6, angle=8)
        light("fill", "AREA", (-3, -3, 3), (55, 0, -45), 120, size=4)
        light("rim", "AREA", (2, 3, 2.5), (-60, 0, 150), 40, size=2)
        sc.view_settings.look = "AgX - Base Contrast"
    else:
        world((0.62, 0.72, 0.80), 0.7)
        light("key", "SUN", (0, 0, 5), (48, 0, -40), 2.1, color=(1.0, 0.94, 0.85), angle=4)
        light("fill", "AREA", (-3, -3, 3), (55, 0, -45), 70, color=(0.8, 0.9, 1.0), size=5)
        light("rim", "AREA", (2.2, 3.2, 2.2), (-62, 0, 150), 90, color=(0.85, 0.95, 1.0), size=1.6)
        sc.view_settings.look = "AgX - Medium High Contrast"


def ground(z=0.0, visible=True):
    g = bpy.data.objects.get("ww_ground")
    if g is None:
        me = bpy.data.meshes.new("ww_ground")
        s = 30
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new()
        for i, l in enumerate(me.loops):
            co = me.vertices[l.vertex_index].co
            uv.data[i].uv = (co.x * 0.7, co.y * 0.7)
        mat = bpy.data.materials.new("ww_ground")
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (0.30, 0.29, 0.22, 1)
        bsdf.inputs["Roughness"].default_value = 0.95
        me.materials.append(mat)
        g = bpy.data.objects.new("ww_ground", me)
        bpy.context.scene.collection.objects.link(g)
    g.location.z = z - 0.0005
    g.hide_render = not visible
    return g


def mannequin():
    """1.75 m 灰色比例人形（簡化），只作尺度參考。"""
    if bpy.data.objects.get("ww_scale_175"):
        return bpy.data.objects["ww_scale_175"]
    import bmesh
    bm = bmesh.new()

    def capsule(x, y, z0, z1, r):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r, radius2=r, depth=z1 - z0,
                              matrix=__import__("mathutils").Matrix.Translation((x, y, (z0 + z1) / 2)))
    capsule(-0.09, 0, 0.0, 0.84, 0.065)       # 腿
    capsule(0.09, 0, 0.0, 0.84, 0.065)
    capsule(0, 0, 0.84, 1.46, 0.16)            # 軀幹
    capsule(-0.22, 0, 0.82, 1.42, 0.045)       # 手臂
    capsule(0.22, 0, 0.82, 1.42, 0.045)
    capsule(0, 0, 1.46, 1.52, 0.05)            # 頸
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.11,
                              matrix=__import__("mathutils").Matrix.Translation((0, 0, 1.64)))
    me = bpy.data.meshes.new("ww_scale_175")
    bm.to_mesh(me)
    bm.free()
    mat = bpy.data.materials.new("ww_mannequin")
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.56, 0.58, 1)
    me.materials.append(mat)
    ob = bpy.data.objects.new("ww_scale_175", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def camera():
    cam = bpy.data.objects.get("ww_cam")
    if cam is None:
        cam = bpy.data.objects.new("ww_cam", bpy.data.cameras.new("ww_cam"))
        bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def aim(cam, target):
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def shoot(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def clay_material():
    m = bpy.data.materials.get("ww_clay") or bpy.data.materials.new("ww_clay")
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.30, 0.29, 0.27, 1)
    b.inputs["Roughness"].default_value = 0.7
    return m


def wire_overlay(objs, on):
    mat = bpy.data.materials.get("ww_wire") or bpy.data.materials.new("ww_wire")
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.04, 0.05, 1)
    out = []
    for o in objs:
        name = f"{o.name}__wire"
        w = bpy.data.objects.get(name)
        if on and w is None:
            w = o.copy()
            w.name = name
            w.data = o.data.copy()
            w.data.materials.clear()
            w.data.materials.append(mat)
            mod = w.modifiers.new("wire", "WIREFRAME")
            mod.thickness = 0.0022
            mod.use_replace = True
            bpy.context.scene.collection.objects.link(w)
        if w is not None:
            w.hide_render = not on
            out.append(w)
    return out


def render_piece(pid, out_root, quick):
    solid, water, coll, shift = isolate(pid)
    attached = attach_wheel(pid)
    out = os.path.join(out_root, pid)
    os.makedirs(out, exist_ok=True)
    lo, hi = bbox(solid)
    ctr = (lo + hi) / 2
    size = hi - lo
    span = max(size.x, size.y, size.z)
    cam = camera()
    body = bpy.data.objects.get(pid)
    gz = body.get("preview_ground_z") if body is not None else None
    # 入土件（木樁、尖樁）地面在 z = 0、埋入部分被地面遮住；剖面式展示件（B02-V03 土塊）地面落到最低點
    g = ground(gz if gz is not None else (lo.z if lo.z < -0.01 else 0.0))
    man = mannequin()
    man.hide_render = True
    vl = bpy.context.view_layer

    # 1) 中性棚：正交四視圖（無地面、無水）＋ 3/4
    look("neutral")
    g.hide_render = True
    for w in water:
        w.hide_render = True
    cam.data.type = "ORTHO"
    for name, (d, _) in VIEWS_ORTHO.items():
        d = Vector(d)
        if name == "top":
            cam.data.ortho_scale = max(size.x, size.y) * 1.25
        else:
            horiz = size.y if abs(d.x) > 0.5 else size.x
            cam.data.ortho_scale = max(horiz, size.z * 1.5) * 1.25
        cam.location = ctr + d * (span * 3 + 2)
        cam.rotation_euler = (d * -1).to_track_quat("-Z", "Y" if name != "top" else "Y").to_euler()
        if name == "top":
            cam.rotation_euler = (0, 0, 0)
        shoot(os.path.join(out, f"{pid}_ortho_{name}.png"))

    cam.data.type = "PERSP"
    cam.data.lens = 50
    dist = span * 2.4 + 0.8
    shots = {"front34": (-0.75, -1.0, 0.65), "back34": (0.8, 1.0, 0.7)}
    for name, (dx, dy, dz) in shots.items():
        cam.location = ctr + Vector((dx, dy, dz)).normalized() * dist
        aim(cam, ctr)
        shoot(os.path.join(out, f"{pid}_neutral_{name}.png"))

    # clay 與線框：暫時換材質（不用 view layer 覆寫，線框才保有深色）
    clay = clay_material()
    saved = {o.name: list(o.data.materials) for o in solid}
    for o in solid:
        for i in range(len(o.data.materials)):
            o.data.materials[i] = clay
    cam.location = ctr + Vector((-0.75, -1.0, 0.65)).normalized() * dist
    aim(cam, ctr)
    shoot(os.path.join(out, f"{pid}_clay.png"))
    wire_overlay(solid, True)
    shoot(os.path.join(out, f"{pid}_wire.png"))
    wire_overlay(solid, False)
    for o in solid:
        for i, m in enumerate(saved[o.name]):
            o.data.materials[i] = m

    # 2) 風格化：英雄鏡頭（有地面、有水）、1.7 m 眼高、頂視流向
    look("stylized")
    g.hide_render = False
    cam.location = ctr + Vector((-0.9, -1.0, 0.55)).normalized() * dist
    aim(cam, ctr + Vector((0, 0, -0.05)))
    shoot(os.path.join(out, f"{pid}_hero.png"))

    man.hide_render = False
    man.location = (hi.x + 0.45, ctr.y + 0.1, 0)
    cam.data.lens = 35
    cam.location = Vector((ctr.x - 0.6, lo.y - 2.2, 1.70))
    aim(cam, Vector((ctr.x + 0.2, ctr.y, 0.45)))
    shoot(os.path.join(out, f"{pid}_eye170.png"))
    man.hide_render = True
    for o in coll.objects:
        if o.parent is None:
            o.location += Vector((shift.x, shift.y, 0))
    if attached:
        attached[0].location = attached[1]
        bpy.data.collections["B06"].hide_render = True
    bpy.context.view_layer.update()


def main():
    ids, out, quick = args()
    setup_render(quick)
    root = bpy.data.collections[K.SET]
    ids = ids or [c.name for c in root.children]
    for pid in ids:
        print(f"[render] {pid}")
        render_piece(pid, out, quick)


if __name__ == "__main__":
    main()
