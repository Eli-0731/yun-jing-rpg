# DR03 根牆收頭與交叉件的遊戲用模型：流程和 game_dr02.py 完全一樣（低模 → 拆 UV → 烘焙 → 植物 → LOD1／LOD2 → 碰撞 → FBX／GLB），
# 只換名稱、建模檔（build_dr03.py）和接口。configure('E'); run_all()  ／  configure('X'); run_all()
#   E 收頭：Socket_Wall 對到 DR02 的 Socket_Head（位置、方向都對齊）→ 收頭件往牆的反方向攤出去。
#   X 交叉件：Socket_Joint 在交叉點正下方，+X 是下面那條根的方向；對到 DR02 接頭（Socket_Tail）就蓋住接縫。
import os

_HERE = 'D:/yun-jing-d2-roots/art/source/d2-roots-b'
_src = _HERE + '/game_dr02.py'
exec(compile(open(_src, encoding='utf-8').read(), _src, 'exec'), globals())

NAMES = {'E': 'DR03_RootEnd', 'X': 'DR03_RootCross'}
DET = 'Detail_DR03_Plants'


def configure(v):
    global VARIANT, ASSET, EXP, TEX, WORKTEX
    VARIANT = v
    ASSET = NAMES[v]
    EXP = f'{ROOT}/art/exports/d2-roots-b/{ASSET}'
    TEX = EXP + '/Textures'
    WORKTEX = os.environ.get('DR_WORK3', 'D:/yun-jing-cache/dr03-work/') + f'bake_{v}'     # 烘焙中間檔，不進版本庫


def _build():
    b = _load('build_dr03.py')
    b['set_variant'](VARIANT)
    return b


def sockets(b):
    if VARIANT == 'E':
        # build_dr03 的 s = 0 是牆的粗頭露出土的地方；收頭件往 +X 攤開，所以接口的 +X（牆的方向）朝 -X
        return [('Socket_Wall', (b['X0'], 0.0, 0.0), 180.0)]
    return [('Socket_Joint', (0.0, 0.0, 0.0), 0.0)]
