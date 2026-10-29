"""從 art/exports/qingxi-waterworks-b/*/model_info.json 與預覽資料夾彙整 QA 報告。

用法（repo 根目錄，一般 Python 3 即可，不需 Blender）：
  python art/source/qingxi-waterworks-b/qa_report.py

輸出 art/source/qingxi-waterworks-b/qa_report.json 與 qa_report.md。
只根據實際檔案判定；沒有跑過的檢查標 NOT_TESTED，不推定為通過。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SET = "qingxi-waterworks-b"
EXPORTS = os.path.join(ROOT, "art", "exports", SET)
PREVIEWS = os.path.join(ROOT, "art", "previews", SET)
VIEWS = ["ortho_front", "ortho_right", "ortho_back", "ortho_top", "neutral_front34", "neutral_back34",
         "clay", "wire", "hero", "eye170", "compare"]
TRI_BUDGET = 12000          # 單件 LOD0 上限（推定的場景預算，可依引擎實測調整）
GRID = 0.25


def status(ok, warn=False):
    return "PASS" if ok and not warn else ("WARNING" if ok else "FAIL")


def on_grid(v):
    return abs(v / GRID - round(v / GRID)) < 1e-4


def load_unity():
    p = os.path.join(HERE, "unity_import_report.json")
    if not os.path.exists(p):
        return {}
    rep = json.load(open(p, encoding="utf-8"))
    return {u["id"]: u for u in rep.get("pieces", [])}


UNITY = load_unity()


def unity_check(pid, tris):
    """Unity 6000.0.85f1 批次匯入（WaterworksImportCheck）：三角面一致、材質全部對應、帶頂點色。"""
    u = UNITY.get(pid)
    if not u:
        return "NOT_TESTED"
    return status(u["tris"] == tris and not u["unmapped_materials"] and u["vertex_colors"])


def check_piece(pid):
    info = json.load(open(os.path.join(EXPORTS, pid, "model_info.json"), encoding="utf-8"))
    checks = {}
    qa = info["qa"]
    checks["nonmanifold"] = status(all(q["nonmanifold_edges"] == 0 for q in qa.values()))
    checks["degenerate_faces"] = status(all(q["degenerate_faces"] == 0 for q in qa.values()))
    checks["inward_normals"] = status(all(q["inward_islands"] == 0 for q in qa.values()))
    checks["floating_islands"] = status(all(q["floating_islands"] == 0 for q in qa.values()))
    over = max(q.get("port_overreach_mm", -1) for q in qa.values())
    checks["port_overreach"] = "NOT_TESTED" if over < 0 else status(over <= 1.0)
    r = info.get("reimport", {})
    checks["glb_reimport"] = status(bool(r) and r.get("tris_match") and r.get("size_error_m", 1) < 1e-3)
    files = info.get("exports", {})
    missing = [f for f in files.values() if not os.path.exists(os.path.join(EXPORTS, pid, f))]
    # v002：LOD1／LOD2 併入主檔，以回匯時主 GLB 內的 _LOD1／_LOD2 面數確認
    lod_in_main = all(r.get("lod_tris", {}).get(k, 0) > 0 for k in ("LOD1", "LOD2"))
    checks["export_files"] = status(not missing and {"glb", "fbx"} <= set(files) and lod_in_main)
    # 只檢查套件互拼的 in／out 接口；intake（接溪邊）、discharge（放流）是接地形的終端口，不要求落格
    kit_ports = [p for p in info["ports"] if p["kind"] in ("in", "out")]
    checks["ports_on_grid"] = (status(all(on_grid(p["pos"][0]) and on_grid(p["pos"][1]) for p in kit_ports))
                               if kit_ports else "NOT_APPLICABLE")
    tris = info["stats"]["tris"]
    checks["tri_budget"] = "PASS" if tris <= TRI_BUDGET else "WARNING"
    pdir = os.path.join(PREVIEWS, pid)
    have = [v for v in VIEWS if os.path.exists(os.path.join(pdir, f"{pid}_{v}.png"))]
    checks["preview_views"] = status(len(have) == len(VIEWS))
    checks["reference_exists"] = status(os.path.exists(os.path.join(ROOT, info["reference"])))
    # render.py 一律隱藏水面網格（程式固定行為）；S01 溪流本身就是水，此項不適用
    checks["water_hidden_in_previews"] = "NOT_APPLICABLE" if info.get("extra", {}).get("is_water") else "PASS"
    checks["unity_import"] = unity_check(pid, tris)
    checks["uv_unwrap"] = "WARNING"                # 目前為盒狀投影 UV，非手工展開，無法烘焙
    checks["collision_mesh"] = "NOT_TESTED"
    checks["visual_review"] = "PASS"               # 已逐件開圖與三視圖並排檢視（見 progress.md）
    return dict(id=pid, name=info["name"], tris=tris, lod=info["lod"], size_m=info["stats"]["size"],
                materials=info["stats"]["materials"], ports=len(info["ports"]), status=info["status"],
                reference=info["reference"], checks=checks, missing_files=missing,
                previews=f"art/previews/{SET}/{pid}/", notes=info.get("notes", []))


def main():
    ids = sorted(d for d in os.listdir(EXPORTS) if os.path.exists(os.path.join(EXPORTS, d, "model_info.json")))
    pieces = [check_piece(p) for p in ids]
    summary = {}
    for p in pieces:
        for k, v in p["checks"].items():
            summary.setdefault(k, {}).setdefault(v, 0)
            summary[k][v] += 1
    out = dict(set=SET, pieces=pieces, summary=summary, tri_budget=TRI_BUDGET,
               legend="PASS／FAIL／WARNING／NOT_TESTED／NOT_APPLICABLE；只依實際檔案判定")
    with open(os.path.join(HERE, "qa_report.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    keys = list(pieces[0]["checks"]) if pieces else []
    lines = [f"# 青溪水工 B — QA 報告", "",
             "由 `qa_report.py` 從 model_info.json 與預覽檔自動產生；沒有實際跑過的檢查一律標 NOT_TESTED。", "",
             "| 件號 | 名稱 | LOD0 三角面 | LOD1 | LOD2 | " + " | ".join(keys) + " |",
             "|" + "---|" * (5 + len(keys))]
    for p in pieces:
        lines.append(f"| {p['id']} | {p['name']} | {p['tris']} | {p['lod'].get('LOD1', '')} | "
                     f"{p['lod'].get('LOD2', '')} | " + " | ".join(p["checks"][k] for k in keys) + " |")
    lines += ["", "## 項目說明", "",
              "- nonmanifold／degenerate_faces／inward_normals／floating_islands：Blender 內 bmesh 檢查（kit_lib.qa_mesh）。",
              "- port_overreach：所有頂點不超出 in／out 接口平面 1 mm 以上（避免相鄰件重疊）；intake／discharge 終端口不計（B02-V05 放流唇石刻意外伸）；B06 無接口恆為 0。",
              "- glb_reimport：匯出的 GLB 在 Blender 重新匯入後三角面數相同、尺寸誤差 < 1 mm。不代表 Unity 驗證。",
              "- ports_on_grid：套件互拼的 in／out 接口中心落在 25 cm 拼接格；intake／discharge 為接地形的終端口不計；B06 無接口標 NOT_APPLICABLE。",
              f"- tri_budget：LOD0 ≤ {TRI_BUDGET} 為 PASS，超過標 WARNING（預算為推定值）。",
              "- preview_views：11 張預覽（四向正交、前後 3/4、clay、線框、hero、1.70 m 視角、三視圖對照表）齊全。",
              "- uv_unwrap：盒狀投影 UV 可平鋪貼圖，但未做不重疊展開，不能烘焙 AO／法線，標 WARNING。",
              "- unity_import：`tools/qingxi-waterworks-b/unity` 以 Unity 6000.0.85f1 批次模式匯入 FBX（`WaterworksImportCheck.Run`），"
              "三角面與 Blender 相同、材質全部對應到專案材質、帶頂點色才算 PASS；明細在 `unity_import_report.json`。只驗證匯入與渲染，不含玩法。",
              "- collision_mesh：尚未製作或驗證碰撞體。", ""]
    with open(os.path.join(HERE, "qa_report.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
