# 青溪公共演武區資產交接

此目錄是六件道具的可編輯 Blender 5.2.2 母檔與可重建程式。`Qingxi_Training_Yard_v1.blend` 保留六個獨立 Collection；每件包含可編輯的網格、倒角修改器、材質節點、UV、及已打包的 Base Color／Roughness／Normal 圖。原件是本輪依已保存 AI 三視圖製作的程序幾何，沒有取用第三方模型。作者標註為 Johnnnny0823 委託、Codex 建模與驗證；圖像來源詳見 `../../references/qingxi-training-yard-v1/README.md`。

`build_yard.py` 在**獨立背景 Blender 程序**中重建母檔，不應在使用者目前開啟的場景內執行。執行 `blender -b --python-exit-code 1 --python build_yard.py` 後以 `review_yard.py` 跑六件 QA 和近景渲染；`export_yard.py` 讀入母檔、套用修改器、逐件合併遊戲網格，產生六個獨立 GLB，並在全新空場景逐一回匯檢查網格三角面數、UV、材質及尺寸。所有輸出路徑限定在本組自己的 `art/exports/qingxi-training-yard-v1/` 與 `art/previews/qingxi-training-yard-v1/`。

尺度為公尺，母檔採 Blender Z-up、資產前方為 -Y；GLB 採 glTF Y-up、模型前方為 +Z。各件原點是地面中心，無場景組裝位移。示範擺放座標在 `../../previews/qingxi-training-yard-v1/assembly-placement.json`。棚體總外包尺寸約 6.82 × 5.40 × 3.90 m（含屋脊、坡道及飛檐）；石坡寬 3.40 m、平台高 0.12 m，四柱內的步行通道無中央柱。精確匯出面數和回匯尺寸在 `../../exports/qingxi-training-yard-v1/asset-manifest.json`。

`qa-report.json` 的六件 `pass` 為 Blender 網格檢查結果，實際回匯結果在匯出 manifest。警告中的重疊 UV 來自共享／平鋪材質貼圖，不適合作獨立光照貼圖或逐件烘焙；圓柱端蓋 n-gon 為平面封口，GLB 匯出時已三角化。棚內隱藏接合面尚可在正式整合前進一步精簡。手機 FPS、Unity 編譯、Unity 導入材質和碰撞、主線入口連接及正式練功 API 均未驗證。

`collision-proxies.json` 是給核心組的簡化碰撞建議，並非已寫入 Unity 的 Collider。
