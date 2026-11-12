# MC-S 山城剪影卡

- 視角：A4 觀景亭（122, 22）向東北遠望；畫面僅留霧中的山城與崖壁，觀景亭不在卡上。
- `MC-S.png`：2048 × 1024 RGBA。左右、上、下以 alpha 漸退，作為單張遠景卡；不用環繞平鋪。
- `MC-S-source.png`：選定的生成來源。由 `art/source/sky-and-distance-v1/build_mountain_city_card.py` 重建尺寸、色調與漸退。
- `MC-S_sky-preview.png`：合成到 SK05 東北山景的預覽；`MC-S_seam-check.png`：四張卡並排確認透明邊界不留硬接縫。正式配置只放一張。
- 山城的屋脊、樓閣與少量舊金色燈點在中距霧層仍可辨認；燈點沒有自發光材質。Unity 弧面方向、深度遮擋與實機畫面尚未驗證。
