"""比對板：上方原始 AI 三視圖，下方模型正交正／右／背與 3/4、clay、線框。

用法：uv run --no-project --with pillow python art/source/qingxi-waterworks-b/compose.py <件號> [預覽根目錄]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SET = "qingxi-waterworks-b"
FONT = "C:/Windows/Fonts/msjh.ttc"


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def main():
    pid = sys.argv[1]
    prev_root = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "art", "previews", SET)
    info = json.load(open(os.path.join(ROOT, "art", "exports", SET, pid, "model_info.json"), encoding="utf-8"))
    ref = Image.open(os.path.join(ROOT, info["reference"])).convert("RGB")
    W = 1800
    ref = ref.resize((W, int(ref.height * W / ref.width)))
    d = os.path.join(prev_root, pid)
    row1 = [("正交 正面（入口 -Y）", "ortho_front"), ("正交 右側（+X）", "ortho_right"), ("正交 背面（+Y）", "ortho_back")]
    row2 = [("中性光 3/4", "neutral_front34"), ("Clay", "clay"), ("線框", "wire")]
    tw = W // 3
    th = int(tw * 820 / 1100)
    head = 70
    sheet = Image.new("RGB", (W, head + ref.height + 2 * (th + 40) + 20), (246, 243, 236))
    g = ImageDraw.Draw(sheet)
    st = info["stats"]
    g.text((20, 14), f"{pid} {info['name']}｜上：AI 三視圖參考　下：Blender 模型渲染", font=font(30), fill=(30, 30, 30))
    g.text((20, 48 - 4), f"尺寸 {st['size'][0]:.2f}×{st['size'][1]:.2f}×{st['size'][2]:.2f} m　LOD0 {st['tris']} tris　材質 {len(st['materials'])}",
           font=font(18), fill=(80, 80, 80))
    sheet.paste(ref, (0, head))
    y = head + ref.height + 10
    for row in (row1, row2):
        for i, (label, key) in enumerate(row):
            p = os.path.join(d, f"{pid}_{key}.png")
            if os.path.exists(p):
                sheet.paste(Image.open(p).convert("RGB").resize((tw, th)), (i * tw, y + 30))
            g.text((i * tw + 12, y + 2), label, font=font(20), fill=(40, 40, 40))
        y += th + 40
    out = os.path.join(d, f"{pid}_compare.png")
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
