"""F01 出水口疊板閘特寫：板頂 0.30（卡滿）／0.19／0.10 m（全降）三個位置（只移動 weir 部件，水面一律隱藏）。

用法（repo 根目錄）：
  blender -b art/source/qingxi-waterworks-b/qingxi-waterworks-b.blend --python art/source/qingxi-waterworks-b/render_detail.py -- --out <絕對路徑>
輸出 <out>/F01/F01_weir_full.png、_half.png、_drain.png。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import kit_lib as K  # noqa: E402
import render as R  # noqa: E402

STATES = {"full": 0.30, "half": 0.19, "drain": 0.10}      # 疊板頂高度 crest_z（m）：卡滿／半降／全降


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = argv[argv.index("--out") + 1] if "--out" in argv else K.PREVIEW_DIR
    solid, water, coll, _ = R.isolate("F01")
    for o in water:
        o.hide_render = True
    R.setup_render(False, w=1100, h=820)
    R.ground(0.0).hide_render = False
    R.look("stylized")
    cam = R.camera()
    cam.data.type = "PERSP"
    cam.data.lens = 40
    target = Vector((0.0, 3.62, 0.24))
    cam.location = Vector((-0.55, 2.75, 0.95))                  # 從田內畦溝上方往出水口看（上游側）
    R.aim(cam, target)
    os.makedirs(os.path.join(out, "F01"), exist_ok=True)
    weir = bpy.data.objects["F01_weir"]
    z0 = weir.location.z
    for state, crest in STATES.items():
        weir.location.z = z0 + crest - K.WATER_Z
        R.shoot(os.path.join(out, "F01", f"F01_weir_{state}.png"))
        print(f"[detail] F01 {state}")


if __name__ == "__main__":
    main()
