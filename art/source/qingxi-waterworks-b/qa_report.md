# 青溪水工 B — QA 報告

由 `qa_report.py` 從 model_info.json 與預覽檔自動產生；沒有實際跑過的檢查一律標 NOT_TESTED。

| 件號 | 名稱 | LOD0 三角面 | LOD1 | LOD2 | nonmanifold | degenerate_faces | inward_normals | floating_islands | port_overreach | glb_reimport | export_files | ports_on_grid | tri_budget | preview_views | reference_exists | water_hidden_in_previews | unity_import | uv_unwrap | collision_mesh | visual_review |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B01 | 舊水路方形基座 | 8904 | 4452 | 1334 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B02 | 完整短直槽 | 3996 | 1998 | 598 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B02-V02 | 磨損階梯牆直槽 | 3768 | 1884 | 564 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B02-V03 | 半埋基腳直槽 | 5864 | 2932 | 878 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B02-V04 | 鍵槽短接頭 | 5508 | 2754 | 826 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B02-V05 | 終止放流坡 | 5304 | 2652 | 794 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B03 | 直角彎槽（右） | 4008 | 2004 | 600 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B03-V02 | 寬弧彎槽（右） | 7672 | 3836 | 1150 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B03-V03 | 斜角扶壁彎槽（左） | 4276 | 2138 | 640 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B03-V04 | 掃弧階台彎槽（左） | 8328 | 4164 | 1248 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B04 | 分流三通 | 4380 | 2190 | 656 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B04-V02 | 圓缽分流三通 | 8220 | 4110 | 1232 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B05 | 木製手動閘板 | 5832 | 2916 | 872 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B06 | 青銅水位閘輪 | 1072 | 536 | 158 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B07 | 修補石鞍 | 1364 | 682 | 204 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B07-V02 | 轉角L形修補鍵 | 772 | 386 | 114 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B07-V03 | 階梯底板修補塞 | 1428 | 714 | 214 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B08 | 河床清淤篩 | 2568 | 1284 | 384 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B09 | 流速指示浮標 | 2010 | 1004 | 300 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B10 | 石槽支架（排架） | 772 | 386 | 114 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B10-V02 | 低矮楔固枕木支架 | 2156 | 1078 | 322 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B10-V03 | 高四樁棧架 | 1472 | 736 | 220 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B11 | 兩輪手推車 | 6780 | 3390 | 1016 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| B12 | 完工紀錄碑座 | 2612 | 1306 | 388 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| F01 | 灌溉田地 | 12860 | 6430 | 1926 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | WARNING | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |
| S01 | 溪流 | 10872 | 5436 | 1630 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | NOT_APPLICABLE | PASS | WARNING | NOT_TESTED | PASS |
| S02 | 河床與河岸 | 9056 | 4528 | 1358 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | NOT_APPLICABLE | PASS | PASS | PASS | PASS | PASS | WARNING | NOT_TESTED | PASS |

## 項目說明

- nonmanifold／degenerate_faces／inward_normals／floating_islands：Blender 內 bmesh 檢查（kit_lib.qa_mesh）。
- port_overreach：所有頂點不超出 in／out 接口平面 1 mm 以上（避免相鄰件重疊）；intake／discharge 終端口不計（B02-V05 放流唇石刻意外伸）；B06 無接口恆為 0。
- glb_reimport：匯出的 GLB 在 Blender 重新匯入後三角面數相同、尺寸誤差 < 1 mm。不代表 Unity 驗證。
- ports_on_grid：套件互拼的 in／out 接口中心落在 25 cm 拼接格；intake／discharge 為接地形的終端口不計；B06 無接口標 NOT_APPLICABLE。
- tri_budget：LOD0 ≤ 12000 為 PASS，超過標 WARNING（預算為推定值）。
- preview_views：11 張預覽（四向正交、前後 3/4、clay、線框、hero、1.70 m 視角、三視圖對照表）齊全。
- uv_unwrap：盒狀投影 UV 可平鋪貼圖，但未做不重疊展開，不能烘焙 AO／法線，標 WARNING。
- unity_import：`tools/qingxi-waterworks-b/unity` 以 Unity 6000.0.85f1 批次模式匯入 FBX（`WaterworksImportCheck.Run`），三角面與 Blender 相同、材質全部對應到專案材質、帶頂點色才算 PASS；明細在 `unity_import_report.json`。只驗證匯入與渲染，不含玩法。
- collision_mesh：尚未製作或驗證碰撞體。
