"""青溪水工 B：總覽板（Pillow）。

  uv run --no-project --with pillow python art/source/qingxi-waterworks-b/sheets.py
輸出：
  art/previews/qingxi-waterworks-b/batch1_hero_sheet.png、batch2_hero_sheet.png（各件 hero 圖）
  art/previews/qingxi-waterworks-b/routes/<路線>_sheet.png（頂視＋3/4，疊件號標籤；標籤座標來自 routes.py）
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PREV = os.path.join(ROOT, "art", "previews", "qingxi-waterworks-b")
FONT = "C:/Windows/Fonts/msjh.ttc"
BATCH1 = ["B01", "B02", "B02-V02", "B02-V03", "B02-V04", "B02-V05", "B03", "B03-V02", "B03-V03", "B03-V04", "B04",
          "B05", "B06"]
BATCH2 = ["B04-V02", "B07", "B07-V02", "B07-V03", "B08", "B09", "B10", "B10-V02", "B10-V03", "B11", "B12"]


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def hero_sheet(ids, out, cols=4, tw=550, th=410):
    rows = (len(ids) + cols - 1) // cols
    img = Image.new("RGB", (cols * tw, rows * th), (240, 238, 232))
    g = ImageDraw.Draw(img)
    f = font(26)
    for i, p in enumerate(ids):
        fp = os.path.join(PREV, p, f"{p}_hero.png")
        x, y = (i % cols) * tw, (i // cols) * th
        if os.path.exists(fp):
            img.paste(Image.open(fp).convert("RGB").resize((tw, th)), (x, y))
        g.text((x + 10, y + 6), p, font=f, fill=(20, 20, 20))
    img.save(out)


def tag(g, x, y, text, f, zone=False):
    w = g.textlength(text, font=f)
    fill, ink = ((70, 96, 52), (255, 255, 255)) if zone else ((250, 248, 240), (25, 25, 25))
    g.rounded_rectangle((x - w / 2 - 8, y - 18, x + w / 2 + 8, y + 16), radius=8, fill=fill, outline=(60, 60, 60))
    g.text((x - w / 2, y - 16), text, font=f, fill=ink)


def route_sheet(key):
    meta = json.load(open(os.path.join(PREV, "routes", f"{key}_labels.json"), encoding="utf-8"))
    tiles = []
    for view in ("top", "hero"):
        im = Image.open(os.path.join(PREV, "routes", f"{key}_{view}.png")).convert("RGB")
        g = ImageDraw.Draw(im)
        f = font(24)
        for lb in meta["labels"][view]:
            tag(g, lb["x"] * im.width, lb["y"] * im.height, lb["text"], f, lb.get("kind") == "zone")
        tiles.append(im)
    W = sum(t.width for t in tiles)
    H = tiles[0].height + 70
    sheet = Image.new("RGB", (W, H), (244, 242, 236))
    g = ImageDraw.Draw(sheet)
    plan = {"restore_channel": "restore_channel", "protect_nursery": "protect_nursery", "clear_silt": "clear_silt"}
    water = "石槽水面隱藏、S01 溪流＋S02 河床河岸顯示" if meta["plan"] == "stream_test" else "水面隱藏"
    g.text((20, 14), f"{meta['title']}　|　方案 {plan.get(meta['plan'], meta['plan'])}　|　左：頂視　右：3/4（{water}）",
           font=font(32), fill=(20, 20, 20))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 70))
        x += t.width
    sheet.save(os.path.join(PREV, "routes", f"{key}_sheet.png"))


def main():
    hero_sheet(BATCH1, os.path.join(PREV, "batch1_hero_sheet.png"))
    hero_sheet(BATCH2, os.path.join(PREV, "batch2_hero_sheet.png"))
    for fn in sorted(os.listdir(os.path.join(PREV, "routes"))):
        if fn.endswith("_labels.json"):
            route_sheet(fn[:-len("_labels.json")])
    print("sheets done")


if __name__ == "__main__":
    main()
