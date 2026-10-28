# 青溪可操作修行者試模

更新：2026-10-28。這是讓玩家在場景裡**看得見自己移動**的原創低精度替身，不是 Heroine-01 或最終人物品質。

- 先行參考：`art/references/qingxi-novice-cultivator-v1/three-view.png`，已保存並在 v13 建模前檢視。
- 原始模型：`art/source/qingxi-entry-assets-v13.blend`；遊戲交換檔：`art/exports/qingxi-entry-assets-v13/novice-cultivator-v13.glb`。
- Unity 轉檔：`tools/art/import_novice_avatar_to_unity.py`，輸出 `apps/game/Assets/QingxiWorld/Models/ArtV001/NoviceCultivatorV1.fbx`。Blender 往返檢查為 47 件網格、3,716 面，無網格或面數遺失。
- PWA `tools/qingxi-trial/main.js`：第三人稱鏡頭下會轉向、步行擺動、閒置呼吸與出招抬手。
- Unity `QingxiWorldBuilder.AddPlayer`：原本的 QPlayerMale 可操作替身改為此角色；`QingxiNoviceMotion` 依角色位移擺動腿、袖及髮束。仍由本機 `QingxiFirstPerson` 控制，預設第三人稱。
- 來源與負責：z1nnz 指導／Codex 依原創三視圖建模與接線；未使用使用者下載的外來角色檔作此版本的基底。

**待精修：** 此模型比例、臉、髮與衣裝不足以代表使用者選定的 AI 漫劇女主角。小紅帽來源模型目前另有本機頭部改造研究，但其頭部 QA 未通過、沒有完成身體和動畫，未匯入此可玩角色。下一版先依 Heroine-01 正、側、背圖修臉與髮冠，再做完整骨架和經過實際相機驗證的步行／戰鬥動畫。不可把目前的程序擺動當成已完成角色動畫。
