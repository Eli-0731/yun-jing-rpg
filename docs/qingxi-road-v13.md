# 青溪彎曲土路近景 v13

製作：z1nnz 指導／Codex 在既有 v12 道路母檔上精修。原始三視圖為 [青溪彎曲道路](../art/references/qingxi-winding-road-v1/three-view.png)，已在 v12 建模前保存；v13 先檢視該圖與 v12 斜視畫面，再修改道路，不覆蓋舊版。石材貼圖取自本專案現有河岸素材。

- [Blender 可編輯母檔](../art/source/qingxi-road-props-v13.blend)、[獨立 GLB](../art/exports/qingxi-road-props-v13/qingxi-road-v13.glb)、[可重建腳本](../tools/art/refine_qingxi_road_v13.py)。
- [斜視](../art/previews/qingxi-road-props-v13/road-oblique.png)與[俯視](../art/previews/qingxi-road-props-v13/road-top.png)。
- 道路兩端仍保持可拼接的截面；中段橫向偏移最多 0.58 m。沿路緣重用 20 個碎石與 12 個低矮葉叢實例；灰石改用既有石材貼圖。
- 模型 147 個網格、12,960 三角面。Blender 5.2 game profile QA 為 0 錯誤；[報告](../art/exports/qingxi-road-props-v13/qa-report.json)仍記錄 3 組既有草片 UV 重疊及花片重複頂點等 4 項警告。這些警告在未重新烘焙貼圖前接受，量產前需整理。
- GLB 已重新匯入 Blender；扣除空場景預設方塊，回匯為 147 網格、12,960 三角面。

**未完成：** 這仍是近景資產樣片，植被、岩石質感與三視圖的密度有明顯差距；尚未匯入 Unity 統一場景、配置 LOD／碰撞或量測手機效能。下一步先挑入口一段試擺，與人物尺度、路面高度和既有協作者道路模組比較，再決定哪些細節值得繼續雕刻與烘焙。
