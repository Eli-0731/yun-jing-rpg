# 在開著的 Blender（MCP）裡重建＋渲染：exec 這個檔之後呼叫 go('r02', ['V2','tq'])
import bpy, os, time
D = 'D:/yun-jing-d2-roots/art/source/d2-roots-b/'
WORK = os.environ.get('DR_WORK', 'D:/yun-jing-cache/dr01-work/')


def load(n):
    p = D + n
    g = {'__file__': p, '__name__': n[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def go(tag, views=('V2', 'tq'), quick=True, samples=48, res=(1280, 720), rebuild=True, plants=True):
    t = time.time()
    b = load('build_dr01.py')
    pv = load('preview_dr.py')
    if rebuild:
        objs = b['build'](quick=quick)
        if plants:
            b['dress'](objs, quick=quick)
    pv['setup'](samples=samples)
    os.makedirs(WORK, exist_ok=True)
    for n in views:
        loc, tgt, lens = pv['VIEWS'][n]
        pv['shot'](f'{WORK}{tag}_{n}.png', loc, tgt, lens, res=res)
    print('done', tag, round(time.time() - t, 1), 's')
