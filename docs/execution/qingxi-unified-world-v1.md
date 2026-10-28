# 青溪統一世界底圖 v1

更新：2026-10-27。z1nnz 指導，Codex 負責場景接線；城鎮原模型與 151 筆配置、狩獵區原件各保留原作者署名。此版是可行走的世界底圖，尚非精修新手村。

## 已接入

- `QingxiWorld.Editor.QingxiWorldBuilder` 重建較大城鎮與西南側狩獵灰盒，保留其玩家、兔子替身和既有路線測試。
- `YunJing.Editor.QingxiUnifiedWorldBuilder` 在同一場景加入核心組原創聽風台 FBX，依城鎮地形落地，石基／鋪面／入口階加碰撞，並生成獨立 `QingxiUnifiedWorld.unity`。
- `tools/unity.ps1 -Target UnifiedWorldWindows` 分兩次 Unity 程序生成場景與建置橫向 1280×720 Windows 本機版本；不覆蓋舊小入口試走場景。
- 無圖形裝置的批次驗證略過舊生成器的 RenderTexture 截圖，避免 Editor 在存檔前崩潰；有圖形裝置時仍執行原截圖流程。
- 玩家導航網格可從城鎮廣場抵達聽風台周邊入口，增加第九個本機除錯定位點與到達提示；它不取代實際步行驗收。
- 聽風台入口到坊市現有 MaterialShop 外側也加入導航網格路線檢查與到達標記；HUD 以「聽風台入口」「坊市入口」顯示地名。

## 實際驗證

固定 Unity `6000.0.82f1`、`-batchmode -nographics`：舊城鎮與狩獵路線報告 `passed`、`failures=0`，統一場景生成成功，城鎮廣場至聽風台周邊有完整 NavMesh 路徑約 53.4 m，Windows build 成功。曾啟動 `YunJingUnifiedWorld.exe`，實際畫面可見第三人稱角色、城鎮廣場、河與通往狩獵區的方向。這只證明 Windows 版本可啟動和顯示；聽風台至坊市尚未完成連續人工走位，手機、網路及服務端採獵亦未驗收。

後續批次生成再次以固定 Unity `6000.0.82f1` 驗證：舊城鎮路線 `passed`、`failures=0`；聽風台入口至坊市外側取得完整 NavMesh 路徑約 192.2 m。這段路線目前只通過導航網格檢查，尚未完成人工連續步行與沿途視覺指引驗收。

本機重建命令：

```powershell
./tools/unity.ps1 -Target UnifiedWorldWindows
```

產物在未追蹤的 `artifacts/windows-unified-world/`；路線報告在 `artifacts/qingxi-world/route_test.json`。生成場景與建置檔不提交 Git。

## 仍要完成的遊玩路線

1. 已接起廣場、聽風台入口、坊市的導航網格路線；接下來須讓玩家實際走完整程，修正碰撞、高差與沿途可辨認的路標。村口地塊尚待精修。
2. 分段替換路旁最顯眼的平面草地、簡單樹形與方盒屋；優先挑選已交接的房屋、道路、河岸、橋頭模組，不覆蓋協作者母檔。
3. 在這條路上接第一株可採靈草：靠近、採集、服務端入帳、背包、重登；再把山兔動畫與合法命中、掉落、出售接進狩獵路線。

現有較大城鎮的 151 筆配置不是 `TownLayout v004` 整包，31 件環境轉接模組亦未全部匯入。這兩類素材將逐段選用，先確認比例、材質、LOD 和碰撞。
