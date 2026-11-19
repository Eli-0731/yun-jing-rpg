# DR04 根間的樹洞的遊戲用模型：流程和 game_dr02.py 一樣（低模 → 拆 UV → 烘焙 → 植物 → LOD1／LOD2 → 碰撞 → FBX／GLB），
# 只換名稱、建模檔（build_dr04.py）、接口，另外：
#   - 洞裡的朽木（物件名有 Rot）烘焙時放在同一組：同一種材質，射線打到隔壁那條也沒關係（不然十幾條纖維要分十幾次烘）；
#   - 遊戲植物多了洞口和洞裡的落葉（三種褐色，畫在葉子那一條的 0.5–0.875）。
# configure('H'); run_all()
import os

_HERE = 'D:/yun-jing-d2-roots/art/source/d2-roots-b'
_src = _HERE + '/game_dr02.py'
exec(compile(open(_src, encoding='utf-8').read(), _src, 'exec'), globals())

NAMES = {'H': 'DR04_RootHollow'}
DET = 'Detail_DR04_Plants'
# 落葉：三條褐色（暗、亮 sRGB），每片葉子整片對到其中一條
LEAF = dict(LEAF, Litter0=(.50, .625, (.13, .09, .06), (.28, .19, .11)), Litter1=(.625, .75, (.11, .085, .06), (.23, .17, .11)),
            Litter2=(.75, .875, (.16, .12, .075), (.33, .25, .15)))
LEAF_X = .875
COL_BIG = .28          # 兩條板根的內芯半徑約 0.30 m（0.40 × 0.76），0.32 會把板根整條排除在碰撞殼外，人會從板根中間穿過去


def configure(v):
    global VARIANT, ASSET, EXP, TEX, WORKTEX
    VARIANT = v
    ASSET = NAMES[v]
    EXP = f'{ROOT}/art/exports/d2-roots-b/{ASSET}'
    TEX = EXP + '/Textures'
    WORKTEX = os.environ.get('DR_WORK4', 'D:/yun-jing-cache/dr04-work/') + f'bake_{v}'     # 烘焙中間檔，不進版本庫


def _build():
    b = _load('build_dr04.py')
    b['set_variant'](VARIANT)
    return b


def sockets(b):
    # Socket_Back：背面正中的地面，+X 朝後（神木或根牆那邊）。擺的時候把它對到神木根部或 DR02 牆的側面
    return [('Socket_Back', (0.0, b['BACK_Y'], 0.0), 90.0)]


_colour0 = _colour


def _colour(objs, near=.75):
    """朽木（Rot）全部放同一組，其餘照 DR02 的規則分組。"""
    rot = [i for i, o in enumerate(objs) if '_Rot' in o.name]
    rest = [i for i in range(len(objs)) if i not in rot]
    groups = [[rest[k] for k in g] for g in _colour0([objs[i] for i in rest], near)] if rest else []
    if rot:
        groups.append(rot)
    return groups


_finish_textures0 = finish_textures


def finish_textures():
    """照 DR02 做完四張圖之後，洞裡再壓暗：用烘焙的 AO（含全部高模和地面）當遮罩，AO 越低底色越暗。
    設定圖的樹洞是黑的；只靠引擎即時光，洞裡兩側和後壁會被天光照亮。開闊的面 AO 接近 1，不受影響。"""
    _finish_textures0()
    for S in SETS:
        im, ao = _px(f'{WORKTEX}/{ASSET}_{S}_AO.png')
        ao = _dilate(ao, fill=1.0)[..., 0]
        bpy.data.images.remove(im)
        p = f'{TEX}/{ASSET}_{S}_Albedo.png'
        im, base = _px(p)
        bpy.data.images.remove(im)
        f = np.clip((ao - .15) / .55, 0, 1)
        h0 = int(STRIP * SIZE)
        f[:h0, :int(LEAF_X * SIZE)] = 1           # 葉子那一條不動
        base[..., :3] *= (.16 + .84 * f)[..., None]
        _save(base, p, True)
