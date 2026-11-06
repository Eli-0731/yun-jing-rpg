# UP05_Burner — Codex 獨立製作紀錄

> **併入後的說明（Eli，2026-11-05）**：這份是 Codex 獨立製作時的原始紀錄，路徑和物件名照當時寫。併入正式包時，建模腳本改名為 `art/source/qingxi-day34-c/build_up05_burner.py`，物件改為 `UP05_Burner_Burner_LOD0/1/2`，匯出到 `art/exports/qingxi-day34-c/UP05_Burner.glb/.fbx`，另加 URP 用的 MaskURP 貼圖；當時的獨立匯出資料夾、`.blend`、驗證腳本和多數審圖已刪除，只留 `art/previews/qingxi-day34-c/codex-burner/` 的 LOD 對照、近拍和 QA 報告。

本件以 Blender 4.5.3 LTS 的 Python 腳本從零建立。工作根目錄為 `E:\yun-jing-rpg-main\workspaces\eli-0731-day34`。只在本次指定的三個資料夾內寫入檔案；沒有執行 git、開啟 Unity、讀取原版 build_day34.py 或原版香爐匯出檔。

## 參考與解讀

建模之前已檢視使用者指定且已保存的 `UP05-v2-cand-4.png`、`UP05-v2-details.png`、`UP05-v2-turnaround.png` 與 `pick.md`。使用既有 AI 三視圖，不重新生成參考。尺寸以工作包為準，沒有照整張桌椅圖的像素比例縮放。

保留矮圓腹、厚外翻口沿、三個短足、兩個方形鏤空耳、腹部低浮雕框紋。八組雙層圓角框均為無文字幾何裝飾。耳孔位於側向平面，耳身略向外傾，對應主圖正面細窄、斜視能看到開孔的解讀。內部為灰層、22 個嵌入灰面的簡化灰塊、三支燒短且頂端深褐的香枝；沒有發光火頭。

## 最終數值

| 項目 | 結果 |
| --- | --- |
| id / 版本 | UP05_Burner / Codex |
| LOD0 XYZ 外框 | 0.149584 × 0.134958 × 0.120000 m |
| 單位 / 正面 | 1 Blender unit = 1 m / Blender -Y |
| 原點 / 最低點 | (0, 0, 0) / z = 0 |
| LOD0 | 11,268 三角形，100% |
| LOD1 | 5,634 三角形，50.00% |
| LOD2 | 1,696 三角形，15.05% |
| 材質 | 1 個，風格化舊銅與灰、香枝共用 atlas |
| 貼圖 | Albedo、Normal、ORM 各 1024 × 1024 PNG |
| Normal | 切線空間、+Y／OpenGL |
| ORM | R = AO、G = roughness、B = metallic |
| Socket_Smoke | Empty，Blender local (0, 0, 0.094) m，在灰面上方約 3.7 mm |
| minTier | standard |
| 碰撞、地板、底座、煙幾何 | 均無 |

GLB 只有 LOD0 與場景根節點、Socket_Smoke。FBX 同檔含 LOD0、LOD1、LOD2 與插槽。LOD 名稱為 `UP05_Burner_codex_LOD0/1/2`；沒有宣稱已建立引擎端的自動 LODGroup。

## 貼圖與 LOD 製作

貼圖由腳本在 UV atlas 上依物件座標光柵繪製：大範圍柔和色差、有限數量的不規則銅綠筆觸、凹部淺綠灰、口沿及凸框暖銅磨邊。沒有照片素材、全表面隨機噪聲或純黑。AO 為繪製的凹部遮蔽近似，不是實測環境光或完整光照烘焙。貼圖島含 8 px 延展；爐身使用連續圓柱展開，以提高主要可見面的解析度。

第一版銅色過於均勻，之後補上局部氧化與斷續磨亮，調整雙耳方向，並改善灰面與 UV 分配。整體強制減面曾使最低階口沿不整齊，因此最終 LOD2 改為規則 32 邊旋轉體，保留實體口沿、內壁、雙耳、三足與三支短香。腹部框紋在 LOD2 轉由 Albedo / Normal 承接，並非完整保留浮雕幾何。遠距離減面是刻意的視覺取捨。

FBX 的通用材質交換無法保證 packed ORM 自動接線，匯入目標引擎時應依上述 R/G/B 通道設定。GLB 的 Albedo、Normal、AO、roughness、metallic 連線已直接檢查。`lod-textured.png` 是把來源材質明確接回「重新匯入的 FBX 網格」後的 UV／LOD 對照，不冒稱是 FBX 自動轉譯的完整材質。

## 驗證與目視審查

- 未修改的 `tools/art/qa_lod0_basic.py` 對最終 GLB 執行：1 個網格、11,268 三角形、**0 findings**。沒有零面積 UV、共面重疊三角形、游離件或未套用縮放。
- `verify_burner.py` 重新匯入 FBX：三個 LOD 三角形數與 model_info 一致，各有三足、兩個鏤空耳，縮放均為 1，各 LOD 零面積 UV 均為 0，Socket_Smoke 的世界座標正確。
- LOD1 回匯外框為 0.149584 × 0.134899 × 0.120000 m；LOD2 為 0.149322 × 0.134000 × 0.119703 m。接地 z 的約 -5.4e-9 m 差異為 FBX 軸轉換浮點誤差。
- LOD0 頂點至 LOD1 表面的距離 P95 / 最大值為 0.1510 / 0.6042 mm；至 LOD2 為 1.8777 / 3.1394 mm。後者包含已轉成貼圖的浮雕與簡化內壁，不能當成純輪廓誤差。
- 使用未修改的 `render_day34.py` 產生前、側、背、斜視及線框，附 1.75 m 人物比例尺。為避免側視被人物遮住，僅在審圖場景以 `--at 0,-0.35,0` 移動道具，匯出檔的原點不變。比例圖為 1280 × 1120，完整保留人物。
- 另提供無人物的四方向近景及線框，讓小物件細節可讀。指定近景鏡頭距注視點約 0.412 m、60 mm 鏡頭、1280 × 960。
- 已目視檢查四方向、近景、線框、比例圖與三級 LOD 對照。

## 最終自評：90 / 100

| 面向 | 分數 | 理由及扣分 |
| --- | --- | --- |
| 比例與輪廓 | 28 / 30 | 真實尺度、矮圓腹、三短足、厚口沿、雙耳完整；耳身外傾與腳端曲線仍是對非正投影參考的解讀，較規則。 |
| 參考細節 | 26 / 30 | 三足、雙耳、八組框紋、灰與短香均可辨識；框紋採規則雙圓角環，沒有逐筆重現參考的變形渦紋；灰堆也較平整。 |
| 材質與貼圖乾淨度 | 21 / 25 | 凹部銅綠、暖色磨邊、柔和大色差與少量筆觸成立；表面比參考更簡潔，細碎剝蝕與手繪碎筆密度較低，耳頂有較規律的色帶。 |
| 技術 | 15 / 15 | 指定 QA 零問題；三級 LOD、貼圖尺寸、原點、尺寸、插槽與 FBX 回匯均驗證；最低階保留主要實體輪廓。 |

這是本次製作者自評，不代表核心組或外部美術驗收。達到 90 分後停止造型修改。仍未匹配的主要特徵為更自然的局部鑄造不規則、參考較密的細碎磨耗與更蓬鬆的灰堆。參考中的煙和桌上散灰依題意不做成此道具幾何。沒有 Unity 編譯、引擎接線或手機效能實測宣稱。

## 檔案清單

`art/source/qingxi-day34-c/codex-burner/`

- `build_burner.py`：可重建全部模型與貼圖的獨立建模腳本。
- `verify_burner.py`：FBX 回匯、LOD／UV／插槽驗證及 LOD 對照圖腳本。
- `UP05_Burner_codex.blend`：含三級 LOD、插槽及打包貼圖的來源檔；預設只顯示 LOD0。
- `NOTES.md`：本紀錄；`build.log`：最終建置日誌。

`art/exports/qingxi-day34-c-codex/`

- `UP05_Burner_codex.glb`
- `UP05_Burner_codex.fbx`
- `model_info.json`
- `textures/UP05_Burner_codex_Albedo.png`
- `textures/UP05_Burner_codex_Normal.png`
- `textures/UP05_Burner_codex_ORM.png`

`art/previews/qingxi-day34-c/codex-burner/`

- `scale-front.png`、`scale-side.png`、`scale-back.png`、`scale-threequarter.png`、`scale-wire.png`：附人物比例尺。
- `detail-front.png`、`detail-side.png`、`detail-back.png`、`detail-threequarter.png`、`detail-wire.png`：細節審圖。
- `review-close-cam.png`：約 0.4 m 的最終近景。
- `lod-comparison.png`、`lod-textured.png`：由左至右 LOD0、LOD1、LOD2。
- `mesh_qa.json`、`roundtrip_qa.json`、`QA_REPORT.md`、`artifact_checksums.json`：最終驗證及檔案校驗資料。
- `initial-close-cam.png`、`revised-close-cam.png`：保留的過程對照，並非最終成品。
- `mesh_qa.log`、`roundtrip_qa.log`、`scale_render.log`、`detail_render.log`、`close_render.log`、`initial_render.log`、`revised_render.log`：對應日誌。

## 重建與驗證

在儲存庫根目錄，以指定 Blender 執行：

```powershell
$blender = 'E:\yun-jing-rpg-main\workspaces\tooling\blender-4.5.3-windows-x64\blender.exe'
& $blender -b --factory-startup -P art/source/qingxi-day34-c/codex-burner/build_burner.py --
& $blender -b --factory-startup -P tools/art/qa_lod0_basic.py -- art/previews/qingxi-day34-c/codex-burner/mesh_qa.json art/exports/qingxi-day34-c-codex/UP05_Burner_codex.glb
& $blender -b --factory-startup -P art/source/qingxi-day34-c/codex-burner/verify_burner.py --
& $blender -b --factory-startup -P art/source/qingxi-day34-c/render_day34.py -- --glb art/exports/qingxi-day34-c-codex/UP05_Burner_codex.glb --out art/previews/qingxi-day34-c/codex-burner --tag scale --at '0,-0.35,0' --res 1280x1120 --views front,side,back,threequarter --wire
& $blender -b --factory-startup -P art/source/qingxi-day34-c/render_day34.py -- --glb art/exports/qingxi-day34-c-codex/UP05_Burner_codex.glb --out art/previews/qingxi-day34-c/codex-burner --tag detail --no-ruler --views front,side,back,threequarter --wire
& $blender -b --factory-startup -P art/source/qingxi-day34-c/render_day34.py -- --glb art/exports/qingxi-day34-c-codex/UP05_Burner_codex.glb --out art/previews/qingxi-day34-c/codex-burner --tag review-close --no-ruler --views '""' --cam=0.24,-0.30,0.21,0,0,0.06,60
```
