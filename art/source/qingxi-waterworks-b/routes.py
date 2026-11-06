"""青溪水工 B：三條路線組合＋支架／修補展示，依接口自動拼接並實測接縫。

用法（repo 根目錄）：
  blender -b art/source/qingxi-waterworks-b/qingxi-waterworks-b.blend --python art/source/qingxi-waterworks-b/routes.py
輸出：
  art/source/qingxi-waterworks-b/routes.json            各件擺放、接縫實測（mm）
  art/previews/qingxi-waterworks-b/routes/<路線>_top.png、_hero.png、_labels.json
標籤由 sheets.py（Pillow）疊到圖上。

接縫實測：在各件自己的座標內，把接口截面分成左牆、右牆、底板三區，各量最遠頂點到接口平面的距離：
超出平面 = 重疊，未到平面 = 縫隙；兩件相加即該區的重疊／縫隙，接縫取三區最大值。
石塊圓角讓接口面外緣內縮約 2 cm，兩件相接會形成刻意的 V 形石縫，不計為縫隙。
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import kit_lib as K  # noqa: E402
import render as R  # noqa: E402

OUT = os.path.join(K.PREVIEW_DIR, "routes")


def info(pid):
    return json.load(open(os.path.join(K.EXPORT_DIR, pid, "model_info.json"), encoding="utf-8"))


def port(pid, name):
    p = next(q for q in info(pid)["ports"] if q["name"] == name)
    return Vector((p["pos"][0], p["pos"][1], 0.0)), Vector((p["dir"][0], p["dir"][1], 0.0))


def rot(theta):
    return Matrix.Rotation(theta, 4, "Z")


def heading(v):
    return math.atan2(v.y, v.x)


class Route:
    def __init__(self, key, title, plan):
        self.key, self.title, self.plan = key, title, plan
        self.items = []          # dict(id, M（4x4 本件→世界）, label)
        self.joints = []

    def place(self, pid, M, label=None):
        self.items.append(dict(id=pid, M=M, label=label or pid))
        return len(self.items) - 1

    def first(self, pid):
        return self.place(pid, Matrix.Identity(4))

    def world_port(self, idx, name):
        it = self.items[idx]
        p, d = port(it["id"], name)
        M = it["M"]
        return M @ p, (M.to_3x3() @ d).normalized()

    def attach(self, idx, out_name, pid, in_name="in", label=None):
        P, D = self.world_port(idx, out_name)
        p, d = port(pid, in_name)
        theta = heading(-D) - heading(d)
        Rm = rot(theta)
        t = P - Rm @ p
        M = Matrix.Translation(t) @ Rm
        j = self.place(pid, M, label)
        self.joints.append(dict(a=self.items[idx]["id"], a_port=out_name, b=pid, b_port=in_name, a_idx=idx, b_idx=j,
                                pos=[round(P.x, 4), round(P.y, 4)]))
        return j

    def prop(self, pid, xy, deg=0.0, z=0.0, label=None):
        M = Matrix.Translation((xy[0], xy[1], z)) @ rot(math.radians(deg))
        return self.place(pid, M, label)

    def on_socket(self, idx, socket, pid, label=None):
        it = self.items[idx]
        s = next(q for q in info(it["id"])["sockets"] if q["name"] == socket)
        M = it["M"] @ Matrix.Translation(s["pos"]) @ rot(s.get("rot", (0, 0, 0))[2])
        return self.place(pid, M, label)


# ------------------------------------------------------------------ 路線定義

def build_routes():
    routes = []
    # A 直通村田（restore_channel）：修好裂槽、開閘直送村田
    r = Route("route_a_direct", "A 直通村田", "restore_channel")
    i = r.first("B01")
    i = r.attach(i, "out", "B02")
    g = r.attach(i, "out", "B05")
    r.on_socket(g, "wheel_mount", "B06")
    c = r.attach(g, "out", "B02-V02", label="B02-V02＋B07")
    # B07 修補石鞍貼在 B02-V02 -X 牆裂縫（y≈0.62）外側，接觸面朝 +X
    M = r.items[c]["M"] @ Matrix.Translation((-0.30 - 0.0315, 0.62, 0.06)) @ rot(-math.pi / 2)
    r.place("B07", M, label="")
    i = r.attach(c, "out", "B02")
    r.attach(i, "out", "B02-V05")
    r.prop("B12", (1.3, 4.2), deg=90)
    r.field = (-1.2, 4.75, 1.2, 6.2)
    routes.append(r)

    # B 繞過育幼區（protect_nursery）：向左繞出育幼區再回到村田
    r = Route("route_b_bypass", "B 繞過育幼區", "protect_nursery")
    i = r.first("B01")
    i = r.attach(i, "out", "B02")
    i = r.attach(i, "out", "B03-V04")
    i = r.attach(i, "out", "B02")
    i = r.attach(i, "out", "B03")
    i = r.attach(i, "out", "B02-V03")
    i = r.attach(i, "out", "B02")
    i = r.attach(i, "out", "B03-V02")
    i = r.attach(i, "out", "B02")
    i = r.attach(i, "out", "B03-V03")
    i = r.attach(i, "out", "B02-V04")
    r.attach(i, "out", "B02-V05")
    r.prop("B12", (1.3, 6.9), deg=90)
    r.field = (-1.2, 7.25, 1.2, 8.7)
    routes.append(r)

    # C 先清淤再暫時導流（clear_silt）：入口段清淤，左支暫時放流、右支關閘後送村田
    r = Route("route_c_desilt", "C 先清淤再暫時導流", "clear_silt")
    i = r.first("B01")
    i = r.attach(i, "out", "B02", label="B02（清淤段）")
    t = r.attach(i, "out", "B04-V02")
    a = r.attach(t, "out_left", "B02", label="B02＋B09")
    fl = r.items[a]["M"] @ Matrix.Translation((0.0, 0.55, 0.10)) @ rot(math.pi / 2)
    r.place("B09", fl, label="")
    a = r.attach(a, "out", "B02-V04")
    r.attach(a, "out", "B02-V05", label="B02-V05（暫時放流）")
    g = r.attach(t, "out_right", "B05", label="B05（關閘）")
    r.on_socket(g, "wheel_mount", "B06")
    i = r.attach(g, "out", "B03-V03")
    i = r.attach(i, "out", "B02")
    r.attach(i, "out", "B02-V05")
    r.prop("B08", (0.75, 0.35), deg=-90)
    r.prop("B11", (-1.7, -0.6), deg=90)
    r.prop("B07-V02", (-1.1, 0.3), deg=20)
    r.prop("B07-V03", (-1.15, -0.05), deg=-10)
    r.prop("B12", (-1.3, 3.0), deg=90)
    r.field = (1.0, 4.05, 3.5, 5.4)
    routes.append(r)

    # D 支架與修補件展示：1 m 直槽坐在三種支架上
    r = Route("showcase_supports", "支架展示（B10 家族）", "showcase")
    for x, sid in ((-1.6, "B10"), (0.0, "B10-V02"), (1.6, "B10-V03")):
        s = r.prop(sid, (x, 0.0))
        r.on_socket(s, "trough", "B02", label="")
    r.field = None
    r.nursery = False
    routes.append(r)

    # E 灌溉田地拼接測試：石槽經閘門送進 F01；上游田的水口板保水，溢流再送進下游田，最後才放流
    r = Route("field_test", "E 石槽接兩塊灌溉田地（F01 測試）", "field_test")
    i = r.first("B01")
    i = r.attach(i, "out", "B02")
    g = r.attach(i, "out", "B05")
    r.on_socket(g, "wheel_mount", "B06")
    i = r.attach(g, "out", "B02")
    f = r.attach(i, "out", "F01", label="F01 上游田")
    i = r.attach(f, "out", "B02", label="B02（溢流）")
    f = r.attach(i, "out", "F01", label="F01 下游田")
    r.attach(f, "out", "B02-V05")
    r.field = None
    r.nursery = False
    routes.append(r)

    # F 溪流取水測試：S01 水面在 z = 0.28（＝石槽水位），B01 坐在右岸掛點、入水口伸入水面，一路送進 F01
    r = Route("stream_test", "F 溪流取水 → 石槽 → 灌溉田地", "stream_test")
    sidx = r.place("S01", Matrix.Translation((0, 0, K.WATER_Z)), label="S01 溪流")
    r.place("S02", Matrix.Translation((0, 0, K.WATER_Z)), label="S02 河床與河岸")   # 與 S01 同原點、同變換
    i = r.on_socket(sidx, "kit_B01", "B01", label="B01 取水")
    i = r.attach(i, "out", "B02")
    g = r.attach(i, "out", "B05")
    r.on_socket(g, "wheel_mount", "B06")
    i = r.attach(g, "out", "B02")
    f = r.attach(i, "out", "F01", label="F01 灌溉田地")
    r.attach(f, "out", "B02-V05")
    r.field = None
    r.nursery = False
    r.stream = sidx
    routes.append(r)
    return routes


def intake_check(r):
    """B01 入水口是否在溪流水面內：入水口中心沿溪流左法線量到右岸線的距離（正＝在水裡）。"""
    st, b01 = r.items[r.stream], next(it for it in r.items if it["id"] == "B01")
    p, _ = port("B01", "intake")
    w = st["M"].inverted() @ (b01["M"] @ p)
    prof = info("S01")["extra"]["profile"]
    q = min(prof, key=lambda e: (e[0] - w.x) ** 2 + (e[1] - w.y) ** 2)
    o = (w.x - q[0]) * q[2] + (w.y - q[1]) * q[3]
    inside = o + q[5]                                   # 右岸在 o = −half_w_right
    depth = K.WATER_Z - K.FLOOR_T
    return dict(intake_inside_water_m=round(inside, 3), intake_floor_z=K.FLOOR_T, water_surface_z=K.WATER_Z,
                intake_water_depth_m=round(depth, 3), ok=bool(0.0 < inside < 0.5))


# ------------------------------------------------------------------ 接縫實測

_VERTS = {}


def local_verts(pid):
    if pid in _VERTS:
        return _VERTS[pid]
    coll = bpy.data.collections[pid]
    body = bpy.data.objects[pid]
    shift = Matrix.Translation((-body.location.x, -body.location.y, 0))
    vs = []
    for o in coll.objects:
        if o.type != "MESH" or o.name.startswith("WATER_"):
            continue
        mw = shift @ o.matrix_world
        vs += [mw @ v.co for v in o.data.vertices]
    _VERTS[pid] = vs
    return vs


REGIONS = {"wall_L": (0.19, 0.33, 0.10, 0.40), "wall_R": (-0.33, -0.19, 0.10, 0.40),
           "floor": (-0.199, 0.199, -0.01, 0.11)}


def face_measure(pid, name):
    """接口面分三區（左牆、右牆、底板）各量最遠頂點到接口平面的距離（正＝超出、負＝未到）。"""
    p, d = port(pid, name)
    side = Vector((-d.y, d.x, 0))
    reach = {k: None for k in REGIONS}
    for v in local_verts(pid):
        rel = v - p
        lat = rel.dot(side)
        s = rel.dot(d)
        if s < -0.05:
            continue
        for k, (a0, a1, z0, z1) in REGIONS.items():
            if a0 <= lat <= a1 and z0 <= v.z <= z1:
                reach[k] = s if reach[k] is None else max(reach[k], s)
    return {k: (None if v is None else round(v * 1000, 2)) for k, v in reach.items()}


def measure_joints(r):
    for j in r.joints:
        fa, fb = face_measure(j["a"], j["a_port"]), face_measure(j["b"], j["b_port"])
        # b 件轉了 180°（接口相對），左右牆互換
        fb_sw = dict(wall_L=fb["wall_R"], wall_R=fb["wall_L"], floor=fb["floor"])
        gaps, overs = {}, {}
        for k in REGIONS:
            if fa[k] is None or fb_sw[k] is None:
                gaps[k] = None
                continue
            gaps[k] = round(max(-fa[k], 0) + max(-fb_sw[k], 0), 2) + 0.0
            overs[k] = round(max(fa[k], 0) + max(fb_sw[k], 0), 2) + 0.0
        j["gap_mm"] = max((v for v in gaps.values() if v is not None), default=None)
        j["overlap_mm"] = max(overs.values(), default=None)
        j["gap_by_region_mm"] = gaps
        j["a_reach_mm"], j["b_reach_mm"] = fa, fb


# ------------------------------------------------------------------ 場景與渲染

def flat_box(name, x0, y0, x1, y1, h, color, coll):
    me = bpy.data.meshes.new(name)
    vs = [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0), (x0, y0, h), (x1, y0, h), (x1, y1, h), (x0, y1, h)]
    me.from_pydata(vs, [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.95
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def instantiate(r, coll):
    objs = []
    for it in r.items:
        pid = it["id"]
        src = bpy.data.collections[pid]
        body = bpy.data.objects[pid]
        base = it["M"] @ Matrix.Translation((-body.location.x, -body.location.y, 0))
        for o in src.objects:
            if o.type != "MESH" or o.name.startswith("WATER_"):
                continue
            n = o.copy()
            n.parent = None
            n.matrix_world = base @ o.matrix_world
            coll.objects.link(n)
            objs.append(n)
        it["objs"] = [o.name for o in objs[-len([x for x in src.objects if x.type == "MESH"
                                                   and not x.name.startswith("WATER_")]):]]
    return objs


def render_route(r):
    root = bpy.data.collections[K.SET]
    for c in root.children:
        c.hide_render = True
    coll = bpy.data.collections.new(r.key)
    bpy.context.scene.collection.children.link(coll)
    objs = instantiate(r, coll)
    extra = []
    if getattr(r, "nursery", True):
        extra.append(flat_box("nursery_zone", -1.0, 2.3, 1.0, 4.9, 0.004, (0.42, 0.52, 0.30), coll))
    if r.field:
        x0, y0, x1, y1 = r.field
        extra.append(flat_box("field", x0, y0, x1, y1, 0.02, (0.24, 0.17, 0.10), coll))
        for k in range(5):
            xx = x0 + (x1 - x0) * (k + 0.5) / 5
            extra.append(flat_box(f"ridge{k}", xx - 0.08, y0 + 0.1, xx + 0.08, y1 - 0.1, 0.07, (0.30, 0.22, 0.13),
                                  coll))
    lo, hi = R.bbox(objs + extra)
    ctr = (lo + hi) / 2
    size = hi - lo
    R.setup_render(False, w=1600, h=1200)
    g = R.ground(0.0)
    g.hide_render = False
    R.look("stylized")
    cam = R.camera()
    os.makedirs(OUT, exist_ok=True)
    shots = {}
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(size.x * 1.15, size.y * 1.15 * 1600 / 1200) + 0.4
    cam.location = Vector((ctr.x, ctr.y, 20))
    cam.rotation_euler = (0, 0, 0)
    R.shoot(os.path.join(OUT, f"{r.key}_top.png"))
    shots["top"] = label_positions(r, cam)
    cam.data.type = "PERSP"
    cam.data.lens = 35
    span = max(size.x, size.y)
    cam.location = ctr + Vector((-0.55, -1.0, 0.8)).normalized() * (span * 0.95 + 1.0)
    R.aim(cam, ctr + Vector((0, 0, 0.1)))
    R.shoot(os.path.join(OUT, f"{r.key}_hero.png"))
    shots["hero"] = label_positions(r, cam)
    json.dump(dict(title=r.title, plan=r.plan, labels=shots), open(os.path.join(OUT, f"{r.key}_labels.json"), "w",
                                                                   encoding="utf-8"), ensure_ascii=False, indent=1)
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(coll)


def label_positions(r, cam):
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    out = []
    for it in r.items:
        if not it["label"]:
            continue
        obs = [bpy.data.objects[n] for n in it.get("objs", []) if n in bpy.data.objects]
        if not obs:
            continue
        lo, hi = R.bbox(obs)
        p = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z + 0.05))
        c = world_to_camera_view(sc, cam, p)
        out.append(dict(text=it["label"], x=round(c.x, 4), y=round(1 - c.y, 4)))
    for text, xy in getattr(r, "zones", []):
        if xy is None:                                  # 河床佔位標在溪流上游端旁
            st = r.items[r.stream]["M"]
            p = st @ Vector((-1.4, 1.5, 0.0))
            xy = (p.x, p.y)
        c = world_to_camera_view(sc, cam, Vector((xy[0], xy[1], 0.3)))
        out.append(dict(text=text, x=round(c.x, 4), y=round(1 - c.y, 4), kind="zone"))
    for text, xy in (("育幼區 nursery_tracks", (0.0, 3.5)), ("村田", None)):
        if not getattr(r, "nursery", True):
            break
        if xy is None:
            if not r.field:
                continue
            xy = ((r.field[0] + r.field[2]) / 2, (r.field[1] + r.field[3]) / 2)
        c = world_to_camera_view(sc, cam, Vector((xy[0], xy[1], 0.1)))
        out.append(dict(text=text, x=round(c.x, 4), y=round(1 - c.y, 4), kind="zone"))
    return out


def main():
    routes = build_routes()
    report = []
    for r in routes:
        measure_joints(r)
        render_route(r)
        report.append(dict(key=r.key, title=r.title, plan=r.plan,
                           pieces=[dict(id=it["id"], label=it["label"],
                                        matrix=[[round(v, 4) for v in row] for row in it["M"]]) for it in r.items],
                           joints=[{k: v for k, v in j.items() if k not in ("a_idx", "b_idx")} for j in r.joints],
                           max_overlap_mm=max((j["overlap_mm"] or 0 for j in r.joints), default=0),
                           max_gap_mm=max((j["gap_mm"] or 0 for j in r.joints), default=0)))
        if getattr(r, "stream", None) is not None:
            report[-1]["intake_check"] = intake_check(r)
            print(f"[route] {r.key} intake: {report[-1]['intake_check']}")
        print(f"[route] {r.key}: {len(r.items)} pieces, {len(r.joints)} joints, "
              f"overlap ≤ {report[-1]['max_overlap_mm']} mm, gap ≤ {report[-1]['max_gap_mm']} mm")
    with open(os.path.join(K.HERE, "routes.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(dict(set=K.SET, note="接縫由 routes.py 依各件頂點實測；不是由座標推算。", routes=report), f,
                  ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
