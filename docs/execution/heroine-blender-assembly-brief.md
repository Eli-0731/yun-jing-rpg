# 女主角 Heroine-01｜Blender 拼接作業說明（給 Codex 或 Claude Code）

2026-10-29，z1nnz 指定。z1nnz 會用外部網站生成女主角的身體、頭髮、衣服等 3D 件，再請 Codex 或 Claude Code **用 computer use 操作本機 Blender 5.2**，把各件拼成一個可進遊戲的角色。本文件是作業手冊；執行者遇到下列任何一步做不到，就停下來回報，不要用其他模型代替。

## 0. 開工前

- 讀 `art/references/heroine-01/character-spec.md` 與 `art/references/heroine-01/components/`（身體衣裝、無髮頭部、髮型髮飾三張正側背參考）。這些三視圖是**造型基準**：黑長直髮、青玉銀飾、淡藍白漢服、半透明外紗袖、腰帶與流蘇。
- 角色只屬於 z1nnz／核心組；協作者不改。
- 從最新 main 開分支 `feature/heroine-01-assembly-vNNN`，工作樹放在 `D:\yun-jing-rpg-workspace\`，並登記到 `D:\yun-jing-rpg-workspace\README.md`。
- 提交與 PR 一律用 z1nnz 名義（`202040543+z1nnz@users.noreply.github.com`），**不加** Co-Authored-By 或「Generated with」等署名行。

## 1. 輸入

z1nnz 會把外部生成檔放在 `art/incoming/heroine-01/<日期>/`。開工前先記下：

| 檔案 | 檢查 |
|---|---|
| 身體（含頭） | 格式、是否有骨架、面數、是否 T／A pose |
| 頭髮 | 是否和頭分開；髮片或實體網格；面數 |
| 衣服（內襯、外裙、外紗袖、腰帶、鞋） | 是否分件；有無厚度；是否穿插身體 |
| 飾品（髮釵、耳墜、流蘇） | 數量、是否浮空 |
| 來源網站與授權 | 寫進 README；授權不明的檔案不進 Git，只留本機 |

## 2. 拼接步驟（Blender 5.2）

1. **新檔與單位**：公尺制。人物身高 1.75 m（頭頂到腳底，不含髮飾）。原點在兩腳之間的地面，正面朝 -Y。
2. **匯入並對齊**：每件匯入後套用縮放與旋轉（Apply Scale／Rotation），以身體為基準對齊。旁邊放正、側、背三視圖當參考平面，並用 1.75 m 人形尺比對比例。
3. **頭與髮**：頭髮跟頭顱貼合，不能浮空；髮根和頭皮之間不露縫。髮型要符合參考：長直及腰、前側兩縷、後腦髮飾位置。髮片數量要控制，手機預算見第 4 步。
4. **衣服貼合**：先用 Shrinkwrap（offset 2–5 mm）或 Surface Deform 讓衣服貼合身體，再刪掉被衣服完全蓋住、看不到的身體面，避免穿模。外紗袖保留厚度；半透明材質只用在紗，不要整件衣服都半透明。
5. **骨架與權重**：沒有骨架就用 Rigify 或 Unity Humanoid 相容的骨架（命名照 Unity Humanoid）。衣服權重從身體轉移（Data Transfer），長裙、袖、髮需要另加幾根擺動骨，或標註「之後由 Unity 物理處理」。
6. **姿勢測試**：抬手 90°、彎膝 120°、跑步姿勢各一張，檢查衣服是否被拉破、身體是否穿出衣服。
7. **材質**：每件最多 1–2 個材質；貼圖 2048（臉、髮）／1024（其他）。紗用 Alpha Blend 或 dither，在報告中寫明。
8. **QA**：每件跑 blender-asset-qa（`profile=game`）：重疊面、浮件、反法線、未套用縮放、UV。錯誤要全部修好，警告逐條寫明接受理由。
9. **匯出**：
   - 母稿：`art/source/heroine-01/heroine-01_vNNN.blend`（版本號遞增，不覆蓋舊版）
   - Unity：`apps/game/Assets/YunJing/Models/Heroine01/heroine-01_vNNN.fbx`，Humanoid 可用
   - Web：`art/exports/heroine-01/heroine-01_vNNN.glb`
   - 匯出後在空白場景重新匯入，比對身高、面數、材質與骨架。

## 3. 交付檢查表

- [ ] 正、側、背、3/4 預覽，各附 1.75 m 人形尺；與三視圖並排
- [ ] 三個姿勢測試圖
- [ ] QA 報告（0 錯誤）與面數表（身體、髮、衣服、飾品分列）
- [ ] FBX／GLB 回匯紀錄
- [ ] README：來源網站與授權、做了哪些修改、**哪些還沒驗證**（Unity 動畫重定向、手機效能、布料擺動）

## 4. 預算（手機優先，先當上限）

| 部分 | 三角面上限 |
|---|---:|
| 身體＋頭 | 15,000 |
| 頭髮 | 12,000 |
| 衣服全部 | 15,000 |
| 飾品 | 3,000 |
| 合計 | 45,000（LOD1 約一半） |

## 5. 用 computer use 時注意

- 只操作 Blender 視窗；用 Blender 內建 Python 主控台或腳本時，把腳本存成 `tools/art/assemble_heroine_01_vNNN.py`，之後才能重跑。
- 不登入任何網站、不下載未經 z1nnz 指定的檔案。
- 每做完一步存一次新版本檔（`_step2`、`_step3`），不要覆蓋外部原檔。
