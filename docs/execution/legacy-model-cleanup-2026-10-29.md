# 舊模型清理｜2026-10-29

z1nnz 決定刪除四項不再使用的早期模型，從場景生成器和 repo 一起移除；Claude Code 依指示執行。Git 歷史仍保留全部原檔，需要時可以找回。

| 刪除項目 | 原本是什麼 | 原本在哪裡用 | 改成什麼 |
|---|---|---|---|
| 方塊小平房等佔位物 | 開發測試場景 `ProjectBuilder.cs` 用方塊拼的兩間小屋（House／Roof／Door）、Broken array、Lotus bed、Beast sanctuary、圓柱丹爐；不是建模 | 開發場景，以及疊在它上面的入口預覽 `QingxiWorldPreview` | 不放東西。開發場景只留地面、牆、溪、灌溉樣件和網路角色 |
| 低多邊形古樹 v1（`qingxi-sacred-tree-v1`） | 10/26 青溪世界雛形的古樹 | 入口預覽的古樹與其碰撞 | 移除；之後的古樹以樹伴原樹移植版或新做的古樹為準 |
| 木橋 v1（`qingxi-timber-bridge-v1`） | 10/26 青溪世界雛形的木橋 | 入口預覽的主橋 | 改用 joshsu54 的石拱橋 `StoneArchBridge_v001`；兩側坡道改為看不見的碰撞，不再壓在橋上 |
| 河邊客舍 v1（`qingxi-riverside-house-v1`） | 10/27 細化樣片的客舍 | PWA 入口 `tools/qingxi-trial/main.js` | 從 PWA 移除；旁邊的商販標示改名「路邊商販」。房屋改用 joshsu54 的 StarterHouse v004 |

## 刪除的檔案

- `art/exports/qingxi-world-v1/`、`art/exports/qingxi-riverside-house-v1/`
- `art/references/qingxi-world-v1/`、`art/references/qingxi-riverside-house-v1/`
- `art/previews/qingxi-riverside-house-v1/`
- `art/source/qingxi-sacred-tree-v1.blend`、`qingxi-timber-bridge-v1.blend`、`qingxi-riverside-house-v1.blend`
- `apps/game/Assets/YunJing/Models/QingxiWorldV1/`（兩件 FBX）
- 專用腳本：`tools/art/build_qingxi_landmarks.py`、`qa_qingxi_landmarks.py`、`build_qingxi_riverside_house.py`、`qa_qingxi_riverside_house.py`、`verify_qingxi_exports.py`、`render_qingxi_world_preview.py`

## 找回方式

刪除前的版本是 main 的 `4476c37`。例如找回木橋母稿：

```powershell
git checkout 4476c37 -- art/source/qingxi-timber-bridge-v1.blend
```

## 保留但已無法重跑的舊紀錄

下列是當時產生樣片的一次性腳本與報告，引用了已刪除的模型；保留作為歷史紀錄，不再重跑：

- `tools/art/assemble_qingxi_world_v2.py`、`assemble_qingxi_entry_v13.py`、`assemble_qingxi_entry_v14.py`、`integrate_qingxi_detail_v4.py`
- `art/previews/qingxi-world-v2/placements.json`、`art/previews/qingxi-entry-v13|v14/assembly-report.json`
- `art/previews/qingxi-world-v1/` 的兩張世界雛形俯視圖，以及 `docs/qingxi-world-foundation.md`、`docs/qingxi-world-detail-v4.md`；文件開頭已加註

## 順手修正：協作者模型被縮成 1/100

入口預覽的 `CollaboratorModel` 會把 FBX 根節點的旋轉和縮放直接覆寫。Blender 匯出的根節點帶 Z 軸向上的旋轉和 ×100 縮放（公分單位），被覆寫後，CollaboratorWorldV1 的房屋、橋、崖壁、宗門、松竹都倒下並縮成 1/100，所以在預覽裡一直看不見。現在改成保留根節點的旋轉和縮放，再乘上擺放倍率。修正後石拱橋實測 9.75 × 3.28 × 3.94 m，見 `art/previews/legacy-cleanup-2026-10-29/`。

**已知問題：** 石拱橋拱頂約 3.3 m，但行走用的碰撞仍是舊木橋那塊 1.45 m 的看不見平板，角色會穿過拱面。要依石拱橋形狀重做碰撞，和 PR #48 的橋頭工作一起處理。崖壁仍浮在離地約 2 m 的地方。

## 與其他分支的關係

- Codex 的 PR #48（入口地形試點）也改了 `apps/game/Assets/YunJing/Editor/QingxiWorldBuilder.cs`。兩邊合併時，這個檔案要手動整合：保留 #48 的地形，並套用這裡「古樹移除、木橋改石拱橋」的改動。
- 新手村（PR #49）沒有用到這四項，不受影響。
