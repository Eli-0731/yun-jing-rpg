"""青溪水工 B：重建母稿、匯出 GLB／FBX／LOD，並寫 model_info 與 QA。

用法（在 repo 根目錄）：
  blender -b --python art/source/qingxi-waterworks-b/build.py -- [件號 ...] [--blend 路徑] [--no-export]

不給件號時建全部；預設存 art/source/qingxi-waterworks-b/qingxi-waterworks-b.blend。
只寫入 art/source|exports/qingxi-waterworks-b/，不碰其他套件。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import kit_lib as K  # noqa: E402
import pieces_b1  # noqa: E402

try:
    import pieces_b2  # noqa: E402
except ImportError:
    pieces_b2 = None
try:
    import pieces_field  # noqa: E402
except ImportError:
    pieces_field = None
try:
    import pieces_stream  # noqa: E402
except ImportError:
    pieces_stream = None

PIECES = {}
for mod in (pieces_b1, pieces_b2, pieces_field, pieces_stream):
    if mod is None:
        continue
    for name in dir(mod):
        if name[:1] in ("B", "F", "S") and name[1:3].isdigit() and callable(getattr(mod, name)):
            PIECES[name.replace("_", "-")] = getattr(mod, name)

LOD_RATIOS = {"LOD1": 0.45, "LOD2": 0.18}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ids, blend, export = [], os.path.join(K.HERE, f"{K.SET}.blend"), True
    i = 0
    while i < len(argv):
        if argv[i] == "--blend":
            blend = argv[i + 1]
            i += 2
            continue
        if argv[i] == "--no-export":
            export = False
        else:
            ids.append(argv[i])
        i += 1
    return ids or sorted(PIECES), blend, export


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    return scene


def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def make_lod(obj, ratio, coll, suffix):
    dup = obj.copy()
    dup.data = obj.data.copy()
    dup.name = f"{obj.name}_{suffix}"
    coll.objects.link(dup)
    mod = dup.modifiers.new("decimate", "DECIMATE")
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = dup
    dup.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return dup


def export_glb(objs, path):
    select_only(objs)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format="GLB",
                              export_image_format="JPEG", export_image_quality=88,
                              export_vertex_color="ACTIVE", export_extras=True, export_yup=True,
                              export_apply=True, export_animations=False)


def export_fbx(objs, path):
    # 先在 Blender 端三角化再輸出：凹多邊形交給 Unity 三角化會掉面（B04-V02 曾少 33 面）
    mods = []
    for o in objs:
        if o.type == "MESH":
            m = o.modifiers.new("fbx_tri", "TRIANGULATE")
            m.quad_method, m.ngon_method = "BEAUTY", "BEAUTY"
            mods.append((o, m))
    select_only(objs)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Z", axis_up="Y",
                             object_types={"MESH", "EMPTY"}, mesh_smooth_type="FACE",
                             use_mesh_modifiers=True, path_mode="COPY", embed_textures=False, bake_anim=False)
    for o, m in mods:
        o.modifiers.remove(m)


def reimport_check(path, expect):
    """匯出後在空白場景重新匯入，比較尺寸、三角面與材質。"""
    before = set(bpy.data.objects)
    before_mats = set(bpy.data.materials)
    before_imgs = set(bpy.data.images)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    bpy.context.view_layer.update()
    st = K.mesh_stats(meshes) if meshes else dict(tris=0, size=[0, 0, 0], materials=[])
    empties = sorted(o.name for o in new if o.type == "EMPTY")
    # glTF 為 Y 向上；匯入器轉回 Z 向上，尺寸可直接比
    size_err = max(abs(a - b) for a, b in zip(st["size"], expect["size"]))
    res = dict(file=os.path.relpath(path, K.ROOT).replace("\\", "/"), tris=st["tris"],
               size=st["size"], materials=st["materials"], empties=empties,
               size_error_m=round(size_err, 5), tris_match=st["tris"] == expect["tris"])
    res["textures_embedded"] = len([i for i in bpy.data.images if i not in before_imgs])
    for o in new:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)
    for m in [m for m in bpy.data.materials if m not in before_mats]:
        bpy.data.materials.remove(m)
    for i in [i for i in bpy.data.images if i not in before_imgs]:
        bpy.data.images.remove(i)
    return res


def snap_to_ports(b, objs, reach=0.02):
    """圓角沿弦線偏移、弧形水面等會讓頂點略超出接口平面；把 2 cm 內的越界頂點壓回平面，確保拼接不重疊。"""
    ports = [p for p in b.ports if p["kind"] in ("in", "out")]
    for o in objs:
        mw, inv = o.matrix_world, o.matrix_world.inverted()
        for v in o.data.vertices:
            w = mw @ v.co
            for p in ports:
                dx, dy = w.x - p["pos"][0], w.y - p["pos"][1]
                d = dx * p["dir"][0] + dy * p["dir"][1]
                if 0 < d < reach and abs(dx * p["dir"][1] - dy * p["dir"][0]) < 0.6:
                    w.x -= p["dir"][0] * d
                    w.y -= p["dir"][1] * d
            v.co = inv @ w
        o.data.update()
    # 反方向：弧牆端塊的弦線偏移會讓牆端退到接口平面內幾 mm，相接時露縫。
    # 分左右牆／底板三區量最遠頂點；若整區都沒到平面（差 0.3–8 mm），把接口 5 cm 內的頂點漸進推齊。
    regions = ((0.19, 0.33, 0.10, 0.40), (-0.33, -0.19, 0.10, 0.40), (-0.199, 0.199, -0.01, 0.11))
    fixed = []
    solids = [o for o in objs if not o.name.startswith("WATER_")]   # 水面已貼齊平面，會掩蓋牆端的縫
    for p in ports:
        d = Vector((p["dir"][0], p["dir"][1], 0))
        side = Vector((-d.y, d.x, 0))
        base = Vector((p["pos"][0], p["pos"][1], 0))
        for a0, a1, z0, z1 in [r for r in regions for _ in range(3)]:   # 每區最多推三次，收斂到 0.3 mm 內
            hits, best = [], None
            for o in solids:
                mw = o.matrix_world
                for v in o.data.vertices:
                    w = mw @ v.co
                    rel = w - base
                    s, lat = rel.dot(d), rel.dot(side)
                    if s > -0.05 and a0 <= lat <= a1:
                        hits.append((o, v, w, s))
                        if z0 <= w.z <= z1:
                            best = s if best is None else max(best, s)
            if best is None or not (-0.008 < best < -0.0003):
                continue
            for o, v, w, s in hits:
                k = max(0.0, min(1.0, (s + 0.05) / (0.05 + best)))
                push = min(-best * k, max(0.0, -s))          # 已在平面上的頂點（他區、銅件）不推過平面
                v.co = o.matrix_world.inverted() @ (w + d * push)
            fixed.append(f"{p['name']}:{round(-best * 1000, 2)}mm")
            for o in objs:
                o.data.update()
    if fixed:
        print(f"[snap] {b.id} 推齊接口：{', '.join(fixed)}")


def build_piece(pid, fn, root_coll, export):
    coll = bpy.data.collections.new(pid)
    root_coll.children.link(coll)
    b = K.Builder(pid)
    meta = fn(b)
    objs = K.build_objects(b, coll)
    body = objs["body"]
    if "preview_ground" in meta:
        body["preview_ground_z"] = meta["preview_ground"]
    for part, o in objs.items():
        if part != "body":
            o.parent = body
    waters = K.water_objects(b, coll)
    snap_to_ports(b, list(objs.values()) + waters)
    sockets = K.socket_empties(b, coll, body)
    solid = list(objs.values())
    stats = K.mesh_stats(solid)
    qa = {name: K.qa_mesh(o) for name, o in objs.items()}
    cells = K.footprint_cells(solid)
    # 接口面越界：任何頂點超出接口平面（沿接口外法線）即會和相鄰件重疊
    over = 0.0
    for o in solid:
        mw = o.matrix_world
        for v in o.data.vertices:
            w = mw @ v.co
            for p in b.ports:
                if p["kind"] in ("intake", "discharge"):   # 接地形的終端口不與套件相鄰
                    continue
                d = (w.x - p["pos"][0]) * p["dir"][0] + (w.y - p["pos"][1]) * p["dir"][1]
                if d > over and abs((w.x - p["pos"][0]) * p["dir"][1] - (w.y - p["pos"][1]) * p["dir"][0]) < 0.6:
                    over = d
    for q in qa.values():
        q["port_overreach_mm"] = round(over * 1000, 2)
    info = dict(id=pid, name=meta["name"], family=meta["family"], variant=meta["variant"],
                author=K.AUTHOR, status=meta.get("status", "建模完成（程序化母稿），待人工精修審核"),
                reference=f"art/references/{K.SET}/{meta['ref']}",
                units="m", up="Blender +Z / glTF +Y", flow_axis="入口在原點，水流朝 +Y",
                standard=dict(outer_w=K.OUTER_W, clear_w=K.CLEAR_W, total_h=K.TOTAL_H,
                              floor_t=K.FLOOR_T, water_z=K.WATER_Z, grid=K.GRID),
                ports=b.ports, flows=b.flows, water_polys=b.water_polys, sockets=b.sockets,
                parts=sorted(objs), footprint_cells=cells, stats=stats, qa=qa,
                notes=meta.get("notes", []), states=meta.get("states", {}),
                collision=meta.get("collision", "以 footprint 盒＋各牆盒組成；水面不碰撞"),
                lod=dict(LOD0=stats["tris"]), extra=meta.get("extra", {}))
    if export:
        out = os.path.join(K.EXPORT_DIR, pid)
        K.ensure_dirs(out)
        main = os.path.join(out, f"{pid}.glb")
        export_glb(solid + sockets, main)
        info["exports"] = {"glb": f"{pid}.glb"}
        info["reimport"] = reimport_check(main, stats)
        if waters:
            export_glb(waters, os.path.join(out, f"{pid}_water.glb"))
            info["exports"]["water_glb"] = f"{pid}_water.glb"
            export_fbx(waters, os.path.join(out, f"{pid}_water.fbx"))   # Unity 半透明流動水面（與本體同原點）
            info["exports"]["water_fbx"] = f"{pid}_water.fbx"
        export_fbx(solid + sockets, os.path.join(out, f"{pid}.fbx"))
        info["exports"]["fbx"] = f"{pid}.fbx"
        lod_coll = bpy.data.collections.new(f"{pid}_LOD")
        coll.children.link(lod_coll)
        for suffix, ratio in LOD_RATIOS.items():
            lods = [make_lod(o, ratio, lod_coll, suffix) for o in solid]
            info["lod"][suffix] = K.mesh_stats(lods)["tris"]
            export_glb(lods, os.path.join(out, f"{pid}_{suffix}.glb"))
            info["exports"][suffix.lower()] = f"{pid}_{suffix}.glb"
        lod_coll.hide_render = True
        lod_coll.hide_viewport = True
        K.write_json(os.path.join(out, "model_info.json"), info)
    return info


def main():
    ids, blend, export = parse_args()
    reset_scene()
    K.make_textures()
    root = bpy.data.collections.new(K.SET)
    bpy.context.scene.collection.children.link(root)
    infos = []
    for pid in ids:
        if pid not in PIECES:
            raise SystemExit(f"未知件號 {pid}；可用：{', '.join(sorted(PIECES))}")
        print(f"[build] {pid}")
        infos.append(build_piece(pid, PIECES[pid], root, export))
    # 母稿：各件分 Collection，排成一列方便檢視（匯出時已在原點完成）
    x = 0.0
    for coll in root.children:
        w = max([o.dimensions.x for o in coll.all_objects if o.type == "MESH"] + [1.7])
        x += max(0.0, w / 2 - 1.25)                    # 田地等大件多留間距，不與鄰件重疊
        for o in coll.all_objects:
            if o.parent is None:
                o.location.x += x
        x += 2.5 + max(0.0, w / 2 - 1.25)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    for i in infos:
        print(f"[done] {i['id']}: {i['stats']['tris']} tris, size {i['stats']['size']}, qa {i['qa']}")


if __name__ == "__main__":
    main()
