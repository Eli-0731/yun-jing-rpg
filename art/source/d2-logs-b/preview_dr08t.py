# DR08 第二版（手繪平鋪＋分層）遊戲模型的快速預覽：開 blend/DR08_RottenLog_<v>_v001.blend，只留 LOD0（本體＋植物），
# 陰天天光＋斜上方太陽，拍幾個鏡位到 D:/yun-jing-cache/dr08-work/T_<v>_<鏡位>.png（不交付，只給自己看）。
#   blender -b art/source/d2-logs-b/blend/DR08_RottenLog_B_v001.blend --python art/source/d2-logs-b/preview_dr08t.py -- B tq,midc,leftc
import bpy, sys, math
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
v = a[0]
views = (a[1] if len(a) > 1 else 'tq,side,midc,leftc,rightc').split(',')
asset = f'DR08_RottenLog_{v}'
root = bpy.data.objects[asset]
root.location = Vector(bpy.context.scene.get('dr_pivot', (0, 0, 0)))          # 搬回建模座標（樹幹沿 +x，0..L）
for o in bpy.data.objects:
    keep = o.name in (f'{asset}_LOD0', f'Detail_DR08_Plants_LOD0', asset)
    o.hide_render = not keep
bpy.context.view_layer.update()
lo = Vector((1e9, 1e9, 1e9))
hi = -lo
for o in (bpy.data.objects[f'{asset}_LOD0'],):
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, p))
        hi = Vector(map(max, hi, p))
L = hi.x
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = 'Standard'
w = sc.world or bpy.data.worlds.new('W')
sc.world = w
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (.55, .60, .66, 1)
bg.inputs['Strength'].default_value = .9
sun = bpy.data.objects.new('PrevSun', bpy.data.lights.new('PrevSun', 'SUN'))
sun.data.energy = 2.6
sun.data.angle = math.radians(8)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
sc.collection.objects.link(sun)
gme = bpy.data.meshes.new('PrevGround')
gme.from_pydata([(-20, -20, 0), (20, -20, 0), (20, 20, 0), (-20, 20, 0)], [], [(0, 1, 2, 3)])
gm = bpy.data.materials.new('PrevGround')
gm.use_nodes = True
next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (.055, .045, .033, 1)
gme.materials.append(gm)
g = bpy.data.objects.new('PrevGround', gme)
g.location.z = -.003
sc.collection.objects.link(g)
cam = bpy.data.objects.new('PrevCam', bpy.data.cameras.new('PrevCam'))
sc.collection.objects.link(cam)
sc.camera = cam
CAMS = {'tq': ((L * .5 - 3.4, -4.2, 2.3), (L * .5, 0, .35), 40), 'side': ((L * .5, -6.5, .8), (L * .5, 0, .4), 40),
        'midc': ((L * .62, -1.6, .95), (L * .62, 0, .35), 40), 'leftc': ((-.9, -1.6, 1.0), (.5, 0, .35), 40),
        'rightc': ((L + .9, -1.6, 1.0), (L - .5, 0, .35), 40), 'top': ((L * .5, -1.2, 4.5), (L * .5, 0, 0), 40),
        'back': ((L * .5 + 2.5, 4.2, 2.0), (L * .5, 0, .35), 40)}
# 層狀菌近拍：本體裡用植物材質（第二槽）的面就是層狀菌；取 x 最小那一叢的中心，從斜側低處看根部有沒有貼住樹幹
body = bpy.data.objects[f'{asset}_LOD0']
bc = [body.matrix_world @ p.center for p in body.data.polygons if p.material_index == 1]
if bc:
    for nm, pick in (('brk', min), ('brk2', max)):
        x0 = pick(c.x for c in bc)
        cl = [c for c in bc if abs(c.x - x0) < .6]
        c = sum(cl, Vector()) / len(cl)
        sd = -1 if c.y < sum(bc, Vector()).y / len(bc) + 1e-6 else 1
        CAMS[nm] = (tuple(c + Vector((.75, sd * 1.0, .10))), tuple(c), 45)
        CAMS[nm + 'b'] = (tuple(c + Vector((-.75, sd * 1.0, -.02))), tuple(c), 45)
for vw in views:
    p, t, lens = CAMS[vw]
    cam.location = p
    cam.rotation_euler = (Vector(t) - Vector(p)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    sc.render.filepath = f'D:/yun-jing-cache/dr08-work/T_{v}_{vw}.png'
    bpy.ops.render.render(write_still=True)
    print('PREVIEW', sc.render.filepath)
