# DR08 v002 的苔：v001 共用的苔貼圖（DR08_Moss_Albedo）偏暗偏橄欖（平均約 64,59,33），參考圖的苔毯是亮黃綠（約 111,104,60）。
# 同一張手繪圖重新調色、調亮另存 DR08_Moss_v002_Albedo.png（筆觸不變；法線沿用 DR08_Moss_Normal）。v001 的貼圖不動。
# 用法：uv run --no-project --offline --with pillow --with numpy python tex_dr08v2.py
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, '..', '..', 'exports', 'd2-logs-b', 'DR08_Shared', 'Textures')
a = np.asarray(Image.open(os.path.join(TEX, 'DR08_Moss_Albedo.png')).convert('RGB'), np.float64) / 255.0
target = np.array((108, 101, 57)) / 255.0
lin = a ** 2.2
gain = (target ** 2.2) / lin.reshape(-1, 3).mean(0)
b = np.clip(lin * gain, 0, 1) ** (1 / 2.2)
g = (b * np.array((.30, .59, .11))).sum(-1, keepdims=True)
b = np.clip(g + (b - g) * 1.05, 0, 1)
Image.fromarray(np.round(b * 255).astype(np.uint8)).save(os.path.join(TEX, 'DR08_Moss_v002_Albedo.png'))
print('moss v002 mean', (b.reshape(-1, 3).mean(0) * 255).round())

# 撕裂纖維／年輪：v001 的 DR08_Fibre_Albedo 偏暗（約 100,76,64），參考圖 B 右端的木纖維是淡暖米色（約 165,135,105）。同樣只調色另存 v002。
f = np.asarray(Image.open(os.path.join(TEX, 'DR08_Fibre_Albedo.png')).convert('RGB'), np.float64) / 255.0
tf = np.array((160, 130, 100)) / 255.0
lf = f ** 2.2
fb = np.clip(lf * ((tf ** 2.2) / lf.reshape(-1, 3).mean(0)), 0, 1) ** (1 / 2.2)
Image.fromarray(np.round(fb * 255).astype(np.uint8)).save(os.path.join(TEX, 'DR08_Fibre_v002_Albedo.png'))
print('fibre v002 mean', (fb.reshape(-1, 3).mean(0) * 255).round())

# 樹皮：v001 的 DR08_Bark_Albedo 偏灰紫（約 99,83,77），參考圖側面樹皮是暖紅褐（約 102,76,60）。同樣只調色另存 v002。
k = np.asarray(Image.open(os.path.join(TEX, 'DR08_Bark_Albedo.png')).convert('RGB'), np.float64) / 255.0
tk = np.array((104, 76, 58)) / 255.0
lk = k ** 2.2
kb = np.clip(lk * ((tk ** 2.2) / lk.reshape(-1, 3).mean(0)), 0, 1) ** (1 / 2.2)
Image.fromarray(np.round(kb * 255).astype(np.uint8)).save(os.path.join(TEX, 'DR08_Bark_v002_Albedo.png'))
print('bark v002 mean', (kb.reshape(-1, 3).mean(0) * 255).round())
