# DR04 根間的樹洞：量尺寸、FBX 回匯、十視圖、LOD 比較、model_info.json／validation.json（和 report_dr02.py 同一套，只換名稱與說明），
# 另外量洞口：寬（0.3／0.6／1.0 m 高）、高、往裡多深，以及碰撞殼擋不擋得住人鑽進去。
# 在做完 game_dr04 的 Blender 裡：r = 載入此檔; r['report']('H')
import json
_src = 'D:/yun-jing-d2-roots/art/source/d2-roots-b/report_dr02.py'
exec(compile(open(_src, encoding='utf-8').read(), _src, 'exec'), globals())


class _Fmt(str):
    def format(self, v):
        return 'DR04_RootHollow'


ASSET_FMT = _Fmt('DR04_{v}')
BUILD = 'build_dr04.py'
DET_NAME = 'Detail_DR04_Plants'
COL_BIG = .28                # 和 game_dr04.COL_BIG 一樣
SLOT = '板根之間 2 處（神木根部、或靠在 DR02 板根牆的側面）'
NOTE_HEAD = '和 DR02 板根牆同一套做法：一塊內芯加上一股股慢慢扭轉的根絞成一束，斷面底寬頂尖。'
NAME_ZH = {'H': '根間的樹洞'}
NOTE = {'H': ('洞口本身是一道粗根拱，後面再一道更高的拱當洞頂，最後面是封住的心材牆（背面靠在神木或根牆上）；兩側各一條板根從後面高處斜下來、'
              '往前往外攤開鑽進土裡。洞口寬約 1.5 m、高約 1.5 m，往裡約 1.4 m；洞裡兩側內壁和後壁貼著紅褐色的朽心材，洞底後面一堆朽木，'
              '拱的內緣垂著一圈朽木纖維。Socket_Back 在背面正中的地面，+X 朝後。')}
FRONT_TXT = '-Y (Blender)：看進洞口；背面（+Y）靠在神木或根牆上'
ORIGIN_TXT = '洞口正下方的地面（洞口那道根拱的中線）；z = 0 是地面，鑽土的部分在 z < 0'
TURN_DIST = 14
SHOTS = {
    'front': ((0.0, -8.0, 1.3), (0.0, .5, .9), 32),
    'tq': ((-5.0, -5.5, 3.0), (0.0, .6, .8), 30),
    'end': ((7.5, -.3, 1.4), (0.0, .6, .9), 32),          # 側面
    'eye': ((.7, -3.0, 1.6), (-.1, 1.0, .6), 26),         # 人眼高、從洞口斜前方看進去（人形尺在 (-1, -3)，別放進柱子裡）
    'back': ((1.5, 8.0, 2.2), (0.0, .5, .9), 32),
    'bark': ((-1.6, -1.6, 1.3), (-.7, .4, .9), 50),       # 洞口左側：樹皮轉朽心材、垂下來的纖維
}


def hollow(o):
    """洞口量測（o 是 LOD0 本體或碰撞殼）。"""
    t = bvh_of(o)
    y0 = .22
    out = {}
    for z in (.3, .6, 1.0):
        l = t.ray_cast(Vector((0, y0, z)), Vector((-1, 0, 0)), 5)[0]
        r = t.ray_cast(Vector((0, y0, z)), Vector((1, 0, 0)), 5)[0]
        out[f'width_at_{z}m'] = round(r.x - l.x, 3) if (l is not None and r is not None) else None
    h = t.ray_cast(Vector((0, y0, .05)), Vector((0, 0, 1)), 5)[0]
    out['height_at_centre_m'] = round(h.z, 3) if h is not None else None
    lip = t.ray_cast(Vector((0, -5, 1.9)), Vector((0, 1, 0)), 10)[0]       # 根拱正面（拱頂的前緣）
    out['lip_front_y_m'] = round(lip.y, 3) if lip is not None else None
    for z in (.5, 1.0):
        d = t.ray_cast(Vector((0, -5, z)), Vector((0, 1, 0)), 10)[0]
        out[f'depth_hit_y_at_{z}m'] = round(d.y, 3) if d is not None else None
    # 1.75 m 的人（膠囊半徑 0.3）沿洞口中線往裡走：在 0.3–1.7 m 每 0.2 m 往 +Y 打，最先被擋到的地方就是人走得到的最深處
    first = [t.ray_cast(Vector((dx, -5, z)), Vector((0, 1, 0)), 10)[0] for z in [.3 + .2 * k for k in range(8)] for dx in (-.3, 0, .3)]
    ys = [p.y for p in first if p is not None]
    out['walker_stops_at_y_m'] = round(min(ys), 3) if ys else None
    return out


_report = report


def report(v='H', **kw):
    val = _report(v, **kw)
    asset = 'DR04_RootHollow'
    EXP = f'{ROOT}/art/exports/d2-roots-b/{asset}'
    val['hollow_lod0'] = hollow(bpy.data.objects[f'{asset}_LOD0'])
    val['hollow_collision'] = hollow(bpy.data.objects[f'{asset}_Collision'])
    json.dump(val, open(f'{EXP}/validation.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print('hollow', val['hollow_lod0'], val['hollow_collision'])
    return val
