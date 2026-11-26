# DR03 根牆收頭與交叉件：量尺寸、FBX 回匯、十視圖、LOD 比較、model_info.json／validation.json（和 report_dr02.py 同一套，只換名稱與說明）。
# 在做完 game_dr03 的 Blender 裡：r = 載入此檔; r['report']('E')
_src = 'D:/yun-jing-d2-roots/art/source/d2-roots-b/report_dr02.py'
exec(compile(open(_src, encoding='utf-8').read(), _src, 'exec'), globals())

_NAMES = {'E': 'DR03_RootEnd', 'X': 'DR03_RootCross'}


class _Fmt(str):
    def format(self, v):
        return _NAMES[v]


ASSET_FMT = _Fmt('DR03_{v}')
BUILD = 'build_dr03.py'
DET_NAME = 'Detail_DR03_Plants'
SLOT = '根牆在路邊斷開的地方（收頭）、兩條根交叉或 DR02 接頭處（交叉件）'
NOTE_HEAD = '和 DR02 板根牆同一套做法：一塊內芯加上一股股慢慢扭轉的根絞成一束，斷面底寬頂尖。'
NAME_ZH = {'E': '根牆收頭', 'X': '根牆交叉件'}
NOTE = {
    'E': ('從 DR02 粗頭底下鑽出來，約 1.7 m 高，往外斜下去分成五根粗細不一的根指，攤開約 4.6 m 寬鑽進土裡。'
          'Socket_Wall 對到 DR02 的 Socket_Head（位置、方向都對齊）就接上，牆的粗頭不再是一面陡的切面。'),
    'X': ('兩條根約 55° 交叉：下面一條順著 X 貼地，上面一條細一點，拱起來壓在它上面，四個端都鑽進土裡。'
          'Socket_Joint 在交叉點正下方、+X 是下面那條根的方向；對到 DR02 的接頭就蓋住接縫，也可以單獨放在兩條根交叉的地方。'),
}
FRONT_TXT = '-Y (Blender)；收頭：根指往 +X 攤開，接牆的一端在 -X；交叉件：下面那條沿 X、上面那條和 X 夾 55°'
ORIGIN_TXT = '收頭：整件（含鑽土的部分）沿 X 的中點正下方的地面；交叉件：交叉點正下方的地面。z = 0 是地面，鑽土的部分在 z < 0'
TURN_DIST = 16
SHOTS_X = {
    'front': ((0.0, -10.0, 1.4), (0.0, 0.0, .7), 30),
    # 斜角、人眼高都從兩條根夾鈍角的那一側看（約 -62°）：v001 第一輪從 -133° 看，剛好順著上面那條根，X 疊成一團
    'tq': ((4.4, -8.4, 3.0), (-.2, .2, .6), 28),
    'end': ((-9.0, -.6, 1.3), (0.0, 0.0, .7), 35),
    'eye': ((2.2, -4.2, 1.65), (-.3, .3, .6), 22),
    'back': ((1.2, 9.5, 1.8), (0.0, 0.0, .7), 30),
    'bark': ((-.8, -2.6, 1.3), (-.6, -.2, .7), 50),
}
# 收頭：接牆的一端（-X）在遊戲裡藏在 DR02 粗頭裡，看的是根指那一側（+X）
SHOTS_E = {
    'front': ((0.0, -10.0, 1.4), (0.0, 0.0, .7), 30),
    'tq': ((7.5, -7.0, 2.6), (-.3, 0.0, .6), 28),
    'end': ((10.0, .6, 1.3), (0.0, 0.0, .8), 35),
    'eye': ((4.2, -3.6, 1.65), (.2, .2, .5), 22),
    'back': ((-1.2, 9.5, 1.8), (0.0, 0.0, .7), 30),
    'bark': ((2.6, -2.4, 1.3), (1.4, -.2, .5), 50),
}
SHOTS = SHOTS_X
_report = report


def report(v, **kw):
    global SHOTS
    SHOTS = SHOTS_E if v == 'E' else SHOTS_X
    return _report(v, **kw)
