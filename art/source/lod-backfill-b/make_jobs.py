"""Writes jobs.json for lod_backfill.py (run from this folder): one entry per asset in the 11/07 LOD backfill list."""
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
HOUSE_KEEP = ["Door", "Window", "Wall", "Roof", "Ridge", "Eave", "Post", "Beam", "Step", "Plinth", "Floor"]
d = {
 "StarterHouse": {"src": "art/incoming/dondon/StarterHouse/v004/StarterHouse_v004.blend", "root": None, "detail_max_m": .35,
                  "min_tier": "standard", "keep": HOUSE_KEEP, "detail_collections": ["07_Porch_Props"], "recentre": False,
                  "note": "Dondon StarterHouse v004 原檔不動；只加 LOD1／LOD2 與 Detail_Small"},
 "Blacksmith": {"src": "art/incoming/dondon/Blacksmith/v001/Blacksmith_v001.blend", "root": None, "detail_max_m": .35,
                "min_tier": "standard", "keep": HOUSE_KEEP, "recentre": False,
                "note": "Dondon Blacksmith v001 原檔不動；只加 LOD1／LOD2 與 Detail_Small"},
 "TownInn": {"src": "art/incoming/dondon/TownLayout/v004/TownLayout_v004.blend", "root": "TownInn_01_ROOT", "detail_max_m": .35,
             "min_tier": "standard", "keep": HOUSE_KEEP, "recentre": True,
             "note": "從 TownLayout v004 取出客棧（TownInn_01_ROOT），原檔不動；原點改到腳印中心、底部 0，位移寫在 recentre_offset_m"},
}
ALCH = {"B01_BronzeFurnace_cold": .05, "B01_BronzeFurnace_heating": .05, "B02_FurnaceLid": .04, "B02_FurnaceLid_heating": .04,
        "B03_StoneMortar": .04, "B04_BambooSortingTrays": .04, "B05_HerbDrawerCabinet": .04, "B06_CeramicWaterJar": .04,
        "B07_WoodenFuelBox": .04, "B08_VentilatedDryingBasket": .04, "B09_ClothFilterFrame": .04, "B10_WaxSealedBottle_empty": .015,
        "B10_WaxSealedBottle_filled": .015, "B11_BambooRecipeStand": .04, "B12_WorkshopChimney": .05}
for k, t in ALCH.items():
    f = glob.glob(os.path.join(REPO, 'art', 'exports', 'qingxi-alchemy-b', '*', 'v001', k + '.fbx'))[0]
    d[k] = {"src": os.path.relpath(f, REPO).replace('\\', '/'), "root": None, "only_lod0": True, "split_loose": True, "detail_max_m": t,
            "min_tier": "standard", "recentre": False,
            "note": "qingxi-alchemy-b v001 原檔不動；LOD0 照原 LOD0，重做 LOD1／LOD2（原 LOD2 約 22%，改為約 15%），拆出 Detail_Small"}
for k in ("C03", "C04", "C06", "C07"):
    d[k] = {"src": f"art/exports/creek-repair-b-props/{k}/{k}.fbx", "root": None, "detail_max_m": .08, "min_tier": "standard", "recentre": False,
            "note": "creek-repair-b-props 原檔不動；原本沒有 LOD，零件合併為本體＋Detail_Small 並補 LOD1／LOD2"}
d["A04_SiltBar"] = {"src": "art/exports/creek-repair-b-props/A04_SiltBar/A04_SiltBar.fbx", "root": None, "only_lod0": True, "split_loose": True,
                    "detail_max_m": .15, "min_tier": "standard", "recentre": False,
                    "note": "原檔已有 LOD0/1/2；LOD0 不動，重做 LOD1／LOD2 並拆出 Detail_Small；A04_SiltBar_Water 一併留在本體"}
# LOD2 review (11/08): one joined collapse bent small parts (B06 lid, B10 cork, C03 bucket rims, A04 bank patches);
# these decimate every loose part by the same share instead.  A04 bank patches are open sheets covering the mound: kept in the body.
for k in ("B06_CeramicWaterJar", "B07_WoodenFuelBox", "B08_VentilatedDryingBasket", "B10_WaxSealedBottle_empty",
          "B10_WaxSealedBottle_filled", "B12_WorkshopChimney", "C03", "A04_SiltBar", "TownInn"):
    d[k]["lod_per_island"] = True
    d[k]["protect_borders"] = True
d["A04_SiltBar"]["detail_closed_only"] = True
# round double-walled shells (staves, jar necks, corks) cannot close below about 30 % of their own faces: LOD2 keeps that share per part
for k in ("C03", "B06_CeramicWaterJar", "B10_WaxSealedBottle_empty", "B10_WaxSealedBottle_filled", "B08_VentilatedDryingBasket"):
    d[k]["island_min_ratio"] = .3
d["A04_SiltBar"]["island_floor"] = 4        # 550 small bank patches: a high floor alone would hold LOD2 near 35 %
d["A04_SiltBar"]["protect_borders"] = False   # every bank patch is all border: protecting them stops the reduction
d["TownInn"]["protect_borders"] = False       # protected roof creases pushed the attic fill through the tiles
for k in ("B10_WaxSealedBottle_empty", "B10_WaxSealedBottle_filled"): d[k]["island_min_ratio"] = .5   # cork and liquid turned into wedges at 30 %
d["B12_WorkshopChimney"]["recompute_normals"] = True   # its LOD0 custom normals no longer fit the reduced faces: stones went dark
json.dump(d, open(os.path.join(HERE, 'jobs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(d), ' '.join(d))
