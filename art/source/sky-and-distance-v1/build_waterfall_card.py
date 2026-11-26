"""從選定水流來源製作可循環的瀑布卡貼圖與檢查圖。"""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

root = Path("art/exports/sky-and-distance-v1/FA")
root.mkdir(parents=True, exist_ok=True)
source = root / "FA01-source.png"
im = Image.open(source).convert("RGBA")
body = im.crop((130, 330, 757, 1444)).resize((1024, 1024), Image.Resampling.LANCZOS)
arr = np.asarray(body, dtype=np.float32).copy()
grey = arr[:,:,:3].mean(axis=2)
arr[:,:,0] = grey * 0.96
arr[:,:,1] = grey * 0.99
arr[:,:,2] = grey * 1.02
# 兩端各 96 像素朝同一接縫色過渡，首尾一致。
edge = (arr[0] + arr[-1]) * 0.5
for i in range(96):
    t = i / 95.0
    t = t * t * (3 - 2 * t)
    arr[i] = edge * (1 - t) + arr[i] * t
    arr[-1-i] = edge * (1 - t) + arr[-1-i] * t
arr[0] = edge
arr[-1] = edge
flow = Image.fromarray(np.clip(arr,0,255).astype(np.uint8), "RGBA")
flow.save(root / "FA01.png")

sky = Image.open("art/exports/sky-and-distance-v1/SK/SK01_sky-preview.png").convert("RGB").resize((1920,1080), Image.Resampling.LANCZOS)
cascade = flow.resize((64, 340), Image.Resampling.LANCZOS)
sky.paste(cascade, (935, 690), cascade)
sky.save(root / "FA01_sky-preview.png")

panel = Image.new("RGB", (2048, 512), "#A9B8C4")
d = ImageDraw.Draw(panel)
for j in range(4):
    sample = flow.resize((100, 400), Image.Resampling.LANCZOS)
    panel.paste(sample, (j*512+210, 55), sample)
    d.line((j*512,0,j*512,511), fill="#8495A5", width=1)
panel.save(root / "FA01_four-panel-check.png")

loop = Image.new("RGBA", (1024, 4096))
for j in range(4):
    loop.paste(flow, (0, j*1024))
loop.resize((256,1024),Image.Resampling.LANCZOS).save(root / "FA01_flow-loop-check.png")
print("FA01", flow.size, flow.mode, "上下最大差", int(np.abs(np.asarray(flow,dtype=np.int16)[0]-np.asarray(flow,dtype=np.int16)[-1]).max()))

