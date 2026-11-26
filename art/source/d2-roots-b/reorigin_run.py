# 舊版（DR01 v005、DR02–04 v001）的遊戲 blend → 原點移到底部中心的新版（DR01 v006、其餘 v002）：
# 平移（dr_pivot.to_bottom_centre）→ 匯出 FBX／GLB → 存新版遊戲 blend → 跑 report（model_info、validation、十方位、審圖）。
# 形狀、UV、貼圖都不動，所以不用重新烘焙。重建整件時 game_dr01／game_dr02 的 finish() 也會做同一個平移。
# 用法（Blender 背景模式，一件一次）：
#   blender -b art/source/d2-roots-b/blend/DR04_RootHollow_v001.blend --python art/source/d2-roots-b/reorigin_run.py -- DR04_H
#   代號：DR01、DR02_A、DR02_B、DR02_C、DR03_E、DR03_X、DR04_H
import bpy, sys, os, json, time

HERE = 'D:/yun-jing-d2-roots/art/source/d2-roots-b'
ROOT = os.path.abspath(HERE + '/../../..').replace('\\', '/')
JOBS = {   # 代號：(物件名, 遊戲腳本, 報告腳本, 變體, 新版號)
    'DR01': ('DR01_RootArch', 'game_dr01.py', 'report_dr01.py', None, 'v006'),
    'DR02_A': ('DR02_RootWall_A', 'game_dr02.py', 'report_dr02.py', 'A', 'v002'),
    'DR02_B': ('DR02_RootWall_B', 'game_dr02.py', 'report_dr02.py', 'B', 'v002'),
    'DR02_C': ('DR02_RootWall_C', 'game_dr02.py', 'report_dr02.py', 'C', 'v002'),
    'DR03_E': ('DR03_RootEnd', 'game_dr03.py', 'report_dr03.py', 'E', 'v002'),
    'DR03_X': ('DR03_RootCross', 'game_dr03.py', 'report_dr03.py', 'X', 'v002'),
    'DR04_H': ('DR04_RootHollow', 'game_dr04.py', 'report_dr04.py', 'H', 'v002'),
}


def _load(n):
    p = f'{HERE}/{n}'
    g = {'__file__': p, '__name__': n[:-3]}
    exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), g)
    return g


def _select(objs, active):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def export(asset, ver, lods, col, socks, root):
    """和 game_dr01／game_dr02 的匯出同一組設定。"""
    exp = f'{ROOT}/art/exports/d2-roots-b/{asset}'
    allm = [o for lst in lods for o in lst] + [col]
    col.hide_render = False
    _select(allm + socks + [root], root)
    bpy.ops.export_scene.fbx(filepath=f'{exp}/{asset}_{ver}.fbx', use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', embed_textures=False)
    _select(lods[0] + [root], root)
    bpy.ops.export_scene.gltf(filepath=f'{exp}/{asset}_{ver}.glb', use_selection=True, export_format='GLB', export_yup=True)
    col.hide_render = True


def run(job):
    asset, game, rep, v, ver = JOBS[job]
    t = time.time()
    root = bpy.data.objects[asset]
    det = next(o.name[:-5] for o in root.children if o.name.startswith('Detail_') and o.name.endswith('_LOD0'))
    lods = [[bpy.data.objects[f'{asset}_LOD{lv}'], bpy.data.objects[f'{det}_LOD{lv}']] for lv in (0, 1, 2)]
    col = bpy.data.objects[f'{asset}_Collision']
    socks = [o for o in root.children if o.name.startswith('Socket_')]
    c = _load('dr_pivot.py')['to_bottom_centre'](root, lods[0][0])
    print('PIVOT', asset, tuple(round(x, 4) for x in c))
    export(asset, ver, lods, col, socks, root)
    bpy.ops.wm.save_as_mainfile(filepath=f'{HERE}/blend/{asset}_{ver}.blend', copy=True)
    r = _load(rep)
    if v is None:
        val = r['report']()
    else:
        val = r['report'](v)
    print('REPORT_DONE', asset, round(time.time() - t), json.dumps(val.get('origin_at_bottom_centre')), val.get('fbx_dims_match'))


if __name__ == '__main__':
    run(sys.argv[sys.argv.index('--') + 1])
