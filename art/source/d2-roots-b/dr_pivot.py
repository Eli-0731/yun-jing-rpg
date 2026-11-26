# 原點移到底部中心：LOD0 本體外框的 XY 中心正下方的地面（z = 0 仍是地面，鑽土的部分在 z < 0）。
# 遊戲腳本（game_dr01／game_dr02）在 finish() 匯出前呼叫 to_bottom_centre()；舊版（DR01 v005、DR02–04 v001）的原點在功能位置
# （拱洞、根的中點、交叉點、洞口），新版只把整件平移，形狀、UV、貼圖都不變。
# 平移量寫進場景的 dr_pivot（舊原點座標系裡新原點的位置）：report_dr0X 量洞口、拍舊鏡位時把根物件搬回 dr_pivot，量法和鏡位不用改。
import bpy
from mathutils import Matrix, Vector


def footprint_centre(body):
    """LOD0 本體（世界座標）外框的 XY 中心。"""
    mw = body.matrix_world
    ps = [mw @ v.co for v in body.data.vertices]
    return Vector(((min(p.x for p in ps) + max(p.x for p in ps)) / 2, (min(p.y for p in ps) + max(p.y for p in ps)) / 2, 0.0))


def to_bottom_centre(root, body):
    """root 底下的網格（各級 LOD、植物、碰撞殼）和接口一起平移，讓底部中心落在原點。回傳平移量（舊座標裡新原點的位置）。"""
    assert tuple(root.location) == (0.0, 0.0, 0.0), 'root 要在原點'
    bpy.context.view_layer.update()
    c = footprint_centre(body)
    c = Vector((round(c.x, 4), round(c.y, 4), 0.0))
    for o in root.children:
        if o.type == 'MESH':
            o.data.transform(Matrix.Translation(-c))
            o.data.update()
        else:
            o.location -= c
    bpy.context.scene['dr_pivot'] = list(c)
    bpy.context.view_layer.update()
    return c


def pivot():
    return Vector(bpy.context.scene.get('dr_pivot', (0.0, 0.0, 0.0)))


def frame(root_name, old):
    """old=True：根物件搬回舊原點的位置（量洞口、拍舊鏡位用）；old=False：放回原點（量外框、接口、匯出用）。"""
    r = bpy.data.objects[root_name]
    r.location = pivot() if old else Vector((0, 0, 0))
    bpy.context.view_layer.update()
