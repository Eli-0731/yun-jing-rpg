# UP05_Burner Codex — 最終 QA

- 工具：Blender 4.5.3 LTS。
- 指定 GLB mesh QA：**0 findings**，1 mesh，11,268 triangles。
- 檢查項目：UV 存在、零面積 UV、共面重疊、游離件、套用縮放；原始結果見 `mesh_qa.json`。
- FBX 重新匯入：LOD0 = 11,268、LOD1 = 5,634（50.00%）、LOD2 = 1,696（15.05%）。每級三足、雙耳、零面積 UV = 0；插槽座標 (0,0,0.094) m。完整數據見 `roundtrip_qa.json`。
- LOD0 外框 XYZ：0.149584 × 0.134958 × 0.120000 m。原點為底部中心，來源最低 z = 0；FBX 軸轉換接地誤差小於 6e-9 m。
- 三張 PNG 均 1024 × 1024；Normal 為 tangent +Y；ORM 為 AO / roughness / metallic。
- GLB 內有三張貼圖，AO 與 metallic-roughness 共用 ORM，所有通道連線已驗證。
- LOD2 為規則低面數爐身，浮雕圖案由色彩與法線承接；三足、方耳、口沿及內部短香保留幾何。
- 已使用指定且未修改的 review rig 產生四方向人物比例圖、線框與約 0.412 m 近景；另加四方向細節圖及兩張 LOD 對照。
- 比例圖以場景平移避免人物遮蔽香爐；此平移沒有寫入模型。地面與人物只存在於審圖場景。
- FBX packed ORM 需在目標材質依通道接線；`lod-textured.png` 使用明確重接的來源材質檢查 FBX UV。
- 自評 **90/100**：比例 28/30、參考細節 26/30、材質 21/25、技術 15/15。理由、差異與重建方式見來源資料夾 `NOTES.md`。
- 範圍：僅 Blender 及交換檔驗證，未開啟 Unity，沒有手機效能實測。
