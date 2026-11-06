"""R1（修回舊渠、直送村田）放進青溪村新手村地圖的擺放提案。

讀：
  art/source/qingxi-waterworks-b/routes.json 的 route_a_direct（套件內各件矩陣，接縫已實測 0 mm）
  novice-village.json（核心組 tools/qingxi-terrain/，以 --village 指定；取自 feature/qingxi-main-scene-abc-v1）
寫：
  tools/qingxi-waterworks-b/village/r1_village_layout.json   每件村圖座標（Unity x／z、yaw、件底高度）
  tools/qingxi-waterworks-b/village/r1_village_top.png       頂視示意（溪、田區、蓄水池、R1 各件）

用法：uv run --no-project --with pillow python tools/qingxi-waterworks-b/village/r1_village_layout.py --village <novice-village.json>
座標換算：套件 Blender (x, y) → Unity (x, z)；R1 整條轉 180°（水流朝村圖 −z，也就是往南流向田區）。
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ROUTES = os.path.join(ROOT, "art", "source", "qingxi-waterworks-b", "routes.json")
EXPORTS = os.path.join(ROOT, "art", "exports", "qingxi-waterworks-b")
FONT = "C:/Windows/Fonts/msjh.ttc"

WATER_Z = 0.28            # 套件水面離件底的高度
INTAKE_IN_WATER = 0.10    # B01 取水口伸進溪水的距離（與 stream_test 相同）


def creek_edge_z(creek, x):
    """沿 x 垂直往南，找溪流南岸水邊（中心線往外半寬）的 z。"""
    pts = list(zip(creek["points"][0::2], creek["points"][1::2]))
    half = creek["width"] / 2
    best = None
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        if x0 != x1 and min(x0, x1) <= x <= max(x0, x1):
            t = (x - x0) / (x1 - x0)
            zc = z0 + (z1 - z0) * t
            nz = abs((x1 - x0) / math.hypot(x1 - x0, z1 - z0))   # 法線的 z 分量
            edge = zc - half / nz
            best = edge if best is None else max(best, edge)
    return best


def main():
    village = sys.argv[sys.argv.index("--village") + 1]
    V = json.load(open(village, encoding="utf-8"))
    R = json.load(open(ROUTES, encoding="utf-8"))
    route = next(r for r in R["routes"] if r["key"] == "route_a_direct")
    fields = {p["id"]: p for p in V["placements"] if p.get("zone") == "fields"}
    cistern = fields["Fields_Cistern"]
    creek = V["creek"]
    pad = next(p for p in V["pads"] if p["id"] == "fields")
    x_line = cistern["x"]                                   # 渠道中心線對準蓄水池中心
    edge = creek_edge_z(creek, x_line)
    intake_z = edge - INTAKE_IN_WATER
    origin_z = intake_z - 1.8                               # B01 出口（套件原點）
    base_y = creek["waterLevel"] - WATER_Z                  # 讓 B01 水面與溪面同高

    def to_village(m):
        x, y = m[0][3], m[1][3]
        yaw_kit = math.degrees(math.atan2(m[1][0], m[0][0]))
        yaw = (180.0 - yaw_kit) % 360.0                     # Blender 繞 Z 正轉 → Unity 繞 Y 反轉，再整條轉 180°
        return round(x_line - x, 3), round(origin_z - y, 3), round(yaw, 1), round(base_y + m[2][3], 3)

    pieces = []
    length = 0.0
    for p in route["pieces"]:
        info = json.load(open(os.path.join(EXPORTS, p["id"], "model_info.json"), encoding="utf-8"))
        X, Z, yaw, Y = to_village(p["matrix"])
        ports = {pt["kind"]: pt["pos"] for pt in info["ports"]}
        a = ports.get("in") or ports.get("intake")
        b = ports.get("out") or ports.get("discharge")
        seg = abs(b[1] - a[1]) if a and b else 0.0           # 只計水路上的件（B06 閘輪、B07 補石、B12 碑不計）
        length += seg
        pieces.append(dict(id=p["id"], label=p["label"], name=info["name"], x=X, z=Z, yaw=yaw, base_y=Y,
                           channel_length_m=round(seg, 3),
                           tris=dict(LOD0=info["lod"]["LOD0"], LOD1=info["lod"]["LOD1"], LOD2=info["lod"]["LOD2"])))
    discharge_z = intake_z - length
    out = dict(
        route="R1（route_a_direct：修回舊渠、直送村田）",
        village_source="novice-village.json（feature/qingxi-main-scene-abc-v1，tools/qingxi-terrain/）",
        units="m，Unity 座標（x 東、z 北、y 上）；yaw 為 Unity 繞 Y（度）；x／z 是各件原點（入口接口），base_y 為件底高度",
        intake=dict(creek_segment="溪流折線 (−27, −8)→(−31, −10) 的南岸，溪彎轉向西南之前",
                    creek_south_edge_z=round(edge, 3), intake_port=[x_line, round(intake_z, 3)],
                    note="B01 取水口伸進溪水 0.10 m；件底 = 溪水面 0.6 − 0.28 = 0.32 m，基座水面與溪面同高"),
        discharge=dict(port=[x_line, round(discharge_z, 3)], target="Fields_Cistern（−30.5, −19.5）北緣",
                       distance_to_cistern_centre_m=round(discharge_z - cistern["z"], 3)),
        total_channel_length_m=round(length, 3),
        straight_line_creek_edge_to_cistern_centre_m=round(edge - cistern["z"], 3),
        water_drop_creek_to_fields_pad_m=round(creek["waterLevel"] - pad["height"], 3),
        pieces=pieces,
        open_questions=[
            "蓄水池 cistern.fbx 的實際尺寸未知；放流坡 B02-V05 出口在池中心北方約 0.8 m；池的南北半長若小於 0.8 m，要往南補一段 B02-V04（0.5 m）。",
            "溪岸 bank 3 m 為斜坡；B01 與第一段 B02 落在岸坡上，渠道下方地形需整平到 base_y。",
            "B 組工作點 waterline-B 標在 (−31, −6)，在溪北岸；R1 從南岸取水，建議把互動點移到 B05 閘門旁（約 −30.9, −15.4）。",
        ])
    with open(os.path.join(HERE, "r1_village_layout.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    # 頂視示意：1 m = 40 px，範圍 x −40…−18、z −24…−4
    S, x0, z1 = 40, -40.0, -4.0
    im = Image.new("RGB", (22 * S, 21 * S), (214, 206, 180))
    d = ImageDraw.Draw(im)

    def P(x, z):
        return ((x - x0) * S, (z1 - z) * S)

    f = ImageFont.truetype(FONT, 18)
    fs = ImageFont.truetype(FONT, 14)
    pts = list(zip(creek["points"][0::2], creek["points"][1::2]))
    d.line([P(x, z) for x, z in pts], fill=(170, 158, 124), width=int((creek["width"] + 2 * creek["bank"]) * S))
    d.line([P(x, z) for x, z in pts], fill=(70, 140, 160), width=int(creek["width"] * S))
    d.rectangle([P(pad["x"] - pad["halfX"], pad["z"] + pad["halfZ"]), P(pad["x"] + pad["halfX"], pad["z"] - pad["halfZ"])],
                outline=(120, 90, 50), width=3)
    d.text(P(pad["x"] - pad["halfX"] + 0.3, pad["z"] + pad["halfZ"] - 0.2), "田區 fields（A1）", fill=(90, 60, 30), font=f)
    for p in fields.values():
        if p["id"] == "Fields_Herbalist":
            continue
        r = 1.0 if p["id"] == "Fields_Cistern" else 1.4
        c = (40, 100, 150) if p["id"] == "Fields_Cistern" else (100, 130, 50)
        d.rectangle([P(p["x"] - r, p["z"] + r), P(p["x"] + r, p["z"] - r)], outline=c, width=3)
        d.text(P(p["x"] - r + 0.1, p["z"] + r - 0.1), p["id"].replace("Fields_", ""), fill=c, font=fs)
    d.rectangle([P(x_line - 0.3, intake_z), P(x_line + 0.3, discharge_z)], fill=(150, 146, 136), outline=(40, 40, 40))
    for p in pieces:
        if p["channel_length_m"] > 0:
            d.line([P(x_line - 0.5, p["z"] + (1.8 if p["id"] == "B01" else 0)),
                    P(x_line + 0.5, p["z"] + (1.8 if p["id"] == "B01" else 0))], fill=(30, 30, 30), width=2)
        d.text(P(p["x"] + 1.0, p["z"] + (1.0 if p["id"] == "B01" else 0.25)), p["label"], fill=(20, 20, 20), font=fs)
    d.text((10, 8), f"R1 放進青溪村：取水 ({x_line}, {intake_z:.2f}) → 放流 ({x_line}, {discharge_z:.2f})，渠長 {length:.2f} m",
           fill=(20, 20, 20), font=f)
    d.text(P(-39.5, -10.5), "溪流（creek）", fill=(30, 80, 110), font=f)
    im.save(os.path.join(HERE, "r1_village_top.png"))
    print(json.dumps({k: out[k] for k in ("total_channel_length_m", "straight_line_creek_edge_to_cistern_centre_m",
                                          "intake", "discharge")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
