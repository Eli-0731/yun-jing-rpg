# 丹房工作桌 v1｜AI 三視圖

2026-10-29，z1nnz 指導、Claude Code 製作。用途：取代新手村丹房角的灰盒工作桌。joshsu54 的 B03 研缽、B08 晾藥籃、B10 藥瓶、B11 食譜架原本就放在 0.78 m 高的桌面上，所以桌面高度、長寬都沿用他灰盒的規格（2.0 × 0.72 m，桌面 0.78 m）。

## 圖像

- `three-view-thumbnail.png`：Canva 圖像生成的結果（媒體 `MAHZU4Vva18`，原圖 1680 × 944）。**目前只存得到 200 × 112 縮圖**；工具拿不到原圖。原圖在 z1nnz 的 Canva 素材庫，下載後請存成 `three-view.png` 放在這裡。
- 縮圖可辨認：正面、右側、背面三欄；平板桌面、四隻直腿、離地約 15 cm 的下層竹條架；三面輪廓一致，並標了 2.0 m、0.72 m、0.78 m。

## 提示詞

> Orthographic three-view reference sheet of ONE game prop: an old wooden alchemy work table for a riverside Chinese xianxia village herb workshop (original design). Three clearly separated panels on one board, left to right labeled FRONT, RIGHT SIDE, BACK. Same object, identical proportions and details in all three views, true orthographic projection, no perspective, no scene, plain light grey background, ground line drawn under each view. Dimensions: 2.0 m long, 0.72 m deep, tabletop surface 0.78 m high; one thick slab top 6 cm thick made of aged warm brown elm planks with worn rounded edges and small knife marks; four square legs with simple splayed stance and mortise-and-tenon joints visible; a low stretcher frame 15 cm above ground with a slatted bamboo shelf between the legs; small oxidized bronze corner caps on the top. Materials: old wood, bamboo, a little oxidized bronze. No objects on the table. Annotate overall length, depth and height with simple dimension lines. Clean concept-art style, flat even lighting, readable silhouette.

## 檢視與推定設計

- 三面輪廓一致，沒有矛盾。
- 縮圖太小，看不出榫卯和銅包角。建模時依提示詞做，列為**推定設計**：
  - 腿：8 × 8 cm 方料，垂直不外撇；圖上看起來是直腿，以圖為準。
  - 牙條：前後各一條，高 5 cm。
  - 下層：前後兩根橫撐，上面放 9 根竹條。
  - 包角：四角各一個 7 cm 的銅包角。
- 背面和正面相同，沒有抽屜；不另外推測背面結構。
