# 《雲境》素材交接清單

日期：2026-10-24  
提供方專案：[joshsu54/dondon2.0](https://github.com/joshsu54/dondon2.0)  
接收方：[z1nnz/yun-jing-rpg](https://github.com/z1nnz/yun-jing-rpg)。  
用途：將現有美術資源交付給《雲境》的 Unity 專案，逐項驗收與整合。

請依下面的清單提供最新有效素材，不需要搬移整個 Unreal 專案。以下版本是本次檢視時的版本；如果已有更新，請提供更新版，並註明差異與已知問題。

## 一、第一批：入世、採集、修煉與入宗

以下路徑皆相對於來源儲存庫根目錄。請交付每個資料夾對應的完整素材及依賴，不能只有預覽圖。

| 用途 | 來源資料夾 |
| --- | --- |
| 男女玩家 | `Models/QPlayerMale/v006`、`Models/QPlayerFemale/v006` |
| 關鍵 NPC | `Models/QSectElder/v006`、`Models/QHerbalist/v006`、`Models/QShopkeeper/v006`、`Models/QBlacksmith/v006`、`Models/QInnkeeper/v006` |
| 修煉與測資 | `Models/QQiManual/v002`、`Models/QAptitudeCrystal/v002`、`Models/QSpiritStone/v002`、`Models/QPillBottle/v002` |
| 採集與狩獵 | `Models/QMountainRabbit/v002`、`Models/QMountainBoar/v002`、`Models/BasicSword01/v001` |
| 靈草生長階段 | `Models/SpiritHerbSeedling/v001`、`Models/SpiritHerbYoung/v001`、`Models/SpiritHerbMature/v001` |
| 初期生活場景 | `Models/StarterHouse/v004`、`Models/SpawnTown/v001`、`Models/SpawnAltar/v002`、`Models/NoticeBoard/v002`、`Models/HerbalStall/v001`、`Models/MaterialShop/v001`、`Models/Blacksmith/v001` |
| 入宗洞府 | `Models/QCaveResidence/v002`、`Models/QCaveEntrance/v003`、`Models/QCaveFloor/v002`、`Models/QCaveWall/v002`、`Models/QCaveDoor/v002` |
| 洞府家具與修煉 | `Models/DiscipleBed/v001`、`Models/StorageChest/v001`、`Models/MeditationCushion/v001`、`Models/CultivationPlatform/v001` |
| 種植與煉丹 | `Models/SpiritHerbGarden/v001`、`Models/HerbPlanter/v001`、`Models/AlchemyFurnace/v001`、`Models/DryingRack/v001`、`Models/MortarPestle/v001` |

## 二、第二批：宗門、製作與野外

以下列出 `Models/` 底下的素材名稱，請挑選最新有效版本，避免連同所有歷史版本上傳。

| 用途 | 素材資料夾名稱 |
| --- | --- |
| 宗門建築與設施 | `SectGate`、`SectGrandHall`、`ScriptureLibrary`、`SectStorehouse`、`AlchemyHall`、`TrainingGround`、`TrainingDummy` |
| 弟子角色 | `QDiscipleSword`、`QDiscipleAlchemy`、`QDiscipleFarmer` |
| 煉器工具與材料 | `SmithAnvil`、`SmithWorkbench`、`SmithHammer`、`SmithTongs`、`QuenchBarrel`、`IronIngot01`、`JadeOre01` |
| 自然環境 | `CommonPine`、`BambooClump`、`WildShrub`、`MossBoulderSet`、`LayeredCliff` |
| 探索道路與水景 | `MountainStonePath`、`MountainStoneStairs`、`CliffBoardwalk`、`StoneArchBridge`、`MountainStreamBend` |
| 場景配置參考 | `TownLayout`、`SectLayout`，包含模型依賴與擺放資料 |

## 三、每個素材要一起交付什麼

- [ ] **可編輯原檔**：`.blend`，保留必要物件、修改器、骨架與動作。
- [ ] **引擎交換檔**：`.fbx`；若已有 `.glb` 可以附上，但不能取代可編輯原檔。
- [ ] **貼圖與材質**：所有引用貼圖及材質說明。外部貼圖須隨附，避免只留下提供方電腦上的絕對路徑；程序材質尚未烘焙時請明示。
- [ ] **角色骨架與動畫**：骨架、蒙皮權重、動作名稱、影格範圍、FPS、是否循環、是否包含根運動；若分檔，附全部相依檔案。
- [ ] **模型資料**：已有的 `model_info.json`、`validation.json`；未做的驗證請標示未做。
- [ ] **設計參考**：原始概念圖；若有 AI 三視圖，附原圖與提示詞。請區分建模前的 AI 參考與建模後的渲染圖。
- [ ] **製作工具**：對應生成、修改、綁骨架或匯出的腳本，以及必要依賴和使用方式。
- [ ] **規格與狀態**：單位、比例、朝向、原點、三角面數、材質數，以及 UV、LOD、碰撞、動畫的完成情況。
- [ ] **來源資訊**：作者、素材來源、外部素材的使用授權及需要保留的標示。

人物製作腳本請特別附上：

- `ArtLibrary/ExpansionBatches/QCharacters17/BlenderSource/qchar17_v004.py`
- `ArtLibrary/ExpansionBatches/QCharacters17/BlenderSource/rig_qchar17.py`
- 上述腳本引用的必要檔案；不用為了兩支腳本搬入整個歷史素材批次。

場景配置請提供 Blender 組合場景，或每個物件的素材識別、位置、旋轉、縮放與父子關係，並說明座標系與單位。單一 `.umap` 不能直接作為 Unity 場景使用。

## 四、已知待補項目

以下是本次資料檢視結果，並非實際完成 Unity 匯入測試的結論。

| 項目 | 已知狀態與交付要求 |
| --- | --- |
| 玩家人物 | `v006` 資料包含骨架、待機與走路。請確認奔跑、攻擊、受擊、死亡、採集、打坐是否另有檔案；沒有就標示待製作。 |
| 山兔 | `v002` 資料標示未綁骨架、動畫未就緒；目前不能直接當成可狩獵敵人。 |
| 山豬及其他生物 | 請各自附實際綁定與動畫狀態，不能以人物已有動畫推定生物也已完成。 |
| UV、LOD、碰撞 | 多項素材仍是外觀原型。已有成果請附上，未完成項目請列明。 |
| 引擎相容性 | Blender 可開啟、FBX 可往返匯入或曾經進入 UE，都不代表已完成 Unity、URP 與手機效能驗證。 |
| 三視圖來源 | 若原模型沒有建模前的 AI 三視圖，請如實說明；不要把事後渲染圖標成原始 AI 設計參考。 |

現有素材可先按真實完成程度交付，缺項另外列出，不必把未完成的內容寫成已完成。後續在《雲境》自行製作模型時，仍須遵守「先生成、檢視並保存 AI 三視圖，再建模」的製作條件。

## 五、上傳方式與目錄

接收儲存庫為 `https://github.com/z1nnz/yun-jing-rpg`；等 z1nnz 提供協作權限後，再上傳。建議另開分支：

`assets/dondon-import`

素材先放在交接目錄，避免直接覆蓋遊戲現有檔案：

```text
art/incoming/dondon/
  QPlayerMale/
    v006/
      QPlayerMale_v006.blend
      QPlayerMale_v006.fbx
      textures/
      references/
      model_info.json
      validation.json        # 有實際驗證結果才附
      README.md              # 來源、動作表、依賴、已知缺項
  ...
  tools/                     # 多個素材共用的製作腳本及依賴
```

此為建議結構；若變更原始相對路徑會破壞依賴，可保留必要原結構並在 README 說明。素材驗收後，再由《雲境》開發端整理進 Unity 的資源目錄。

- 使用 Git LFS 管理 `.blend`、`.fbx`、`.glb`、圖片等大型檔案，依接收儲存庫的 `.gitattributes` 設定。
- 確認 LFS 實際物件已上傳，不能只有指標檔。
- 建議以 Pull Request 交付，附本次素材、來源版本、缺項與驗證結果。
- 保留接收專案既有程式、設定、文件與模型，不覆蓋或整批取代。

## 六、這次不用上傳的內容

- Unreal 專案整包、`.uasset`、`.umap` 與 UE 專用執行程式碼。
- `Binaries`、`Intermediate`、`Saved`、`DerivedDataCache` 等產物或快取。
- `ArtLibrary/History`、重複的 `Current` 副本、全部舊版模型與重複交付 ZIP。
- 與所選素材無關的腳本或外部資源。
- 帳號憑證、金鑰、私鑰及個人環境設定。

如果某個所選素材依賴上述目錄中的必要原始資源，請抽出該依賴並說明，不要直接搬入整個目錄。

## 七、交付檢查

- [ ] 第一批／第二批各自列出已交付與未交付項目。
- [ ] `.blend` 能重新開啟，貼圖及依賴沒有遺失。
- [ ] `.fbx` 能重新匯入，比例與朝向合理；記錄驗證使用的軟體版本。
- [ ] 人物動畫能對應到正確骨架，列出實際存在的動作。
- [ ] LFS 檔案可由乾淨 checkout 下載並開啟。
- [ ] 已註明原始來源版本、已知缺項與外部素材授權。
- [ ] 沒有覆蓋《雲境》的既有檔案。

## 參考來源

- [素材索引](https://github.com/joshsu54/dondon2.0/blob/main/ArtLibrary/asset_catalog.json)
- [男玩家模型與動畫資料](https://github.com/joshsu54/dondon2.0/blob/main/Models/QPlayerMale/v006/model_info.json)
- [山兔模型資料](https://github.com/joshsu54/dondon2.0/blob/main/Models/QMountainRabbit/v002/model_info.json)

本次清單依來源版本 `4644558afb5d7d2dce59614768f8dabaca16e1c5` 檢視結果整理；上述 `main` 連結可能隨朋友後續開發更新。
