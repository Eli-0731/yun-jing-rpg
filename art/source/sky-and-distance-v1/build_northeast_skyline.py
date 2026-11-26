"""以既有四象限環景接圖流程組合東北高山群。"""
from __future__ import annotations
from build_valley_skyline import make_ring
import numpy as np

for name, offset in (("SK04", 30), ("SK05", 60), ("SK06", 0)):
    image = make_ring(name, offset)
    pixels = np.asarray(image, dtype=np.int16)
    seam = np.abs(pixels[:, 0, :] - pixels[:, -1, :])
    print(name, image.size, "首尾最大色差", seam.max())
