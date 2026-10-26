"""Render the material previews used by REF_F_Materials.png (PHASE 4/6).

  blender -b --python-exit-code 1 --python 05_Scripts/render_material_sheet.py

Fresh session; nothing is opened or saved.  Each shared material M_DrySoil, M_WetSoil, M_Grass, M_Moss, M_Rock,
M_PathGravel is shown on one 2 m x 2 m texture tile (= one texture repeat) under the preview lighting, plus a
demo of M_TerrainBlend: four 4 m strips whose Mask channel ramps 0 -> 1 left to right (R wet soil, G grass,
B path gravel, A moss over the dry-soil base), seen from above.  Writes 04_Previews/Materials/*.png.
make_ref_f.py lays them out with the texture maps.  Never overwrites.
"""
import sys, math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K
import kit_blender as KB


def plane(name, w, h, nx, ny, mat, uv_scale=None, mask=None):
    verts = [(-w / 2 + w * i / nx, -h / 2 + h * j / ny, 0.0) for i in range(nx + 1) for j in range(ny + 1)]
    faces = [(i * (ny + 1) + j, (i + 1) * (ny + 1) + j, (i + 1) * (ny + 1) + j + 1, i * (ny + 1) + j + 1) for i in range(nx) for j in range(ny)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.x + w / 2) / (uv_scale or w), (co.y + h / 2) / (uv_scale or h))
    if mask:
        ca = me.color_attributes.new('Mask', 'FLOAT_COLOR', 'POINT')
        for d, v in zip(ca.data, me.vertices): d.color = mask(v.co.x, v.co.y)
    me.materials.append(mat); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def main():
    scene = KB.start_session()
    stu = bpy.data.collections.new('MAT_Studio'); scene.collection.children.link(stu)
    KB.studio(scene, stu, samples=48, transparent=False)
    cam = bpy.data.objects.new('MAT_Camera', bpy.data.cameras.new('MAT_Camera')); stu.objects.link(cam); scene.camera = cam
    scene.render.resolution_x = scene.render.resolution_y = 640
    for layer in KB.LAYERS:
        ob = plane('MAT_' + layer, 2.0, 2.0, 1, 1, KB.pbr_material(layer))
        cam.data.type = 'PERSP'; cam.data.lens = 50; KB.look_at(cam, (0, 0, 0), (-0.55, -1.0, 1.25), 4.2)
        p = KB.new_output('04_Previews/Materials/M_%s.png' % layer); scene.render.filepath = str(p)
        bpy.ops.render.render(write_still=True, scene=scene.name); print('RENDERED', p.name, flush=True)
        bpy.data.objects.remove(ob, do_unlink=True)
    rows = 4; w, h = 4.0, 2.0
    def mask(x, y):
        r = min(rows - 1, int((y + h / 2) / (h / rows))); t = max(0.0, min(1.0, (x + w / 2 - 0.4) / (w - 0.8)))
        c = [0.0, 0.0, 0.0, 0.0]; c[[0, 1, 2, 3][rows - 1 - r]] = t; return tuple(c)
    plane('MAT_TerrainBlend', w, h, 64, 32, KB.terrain_material(), uv_scale=K.UV_TILE_M, mask=mask)
    scene.render.resolution_x, scene.render.resolution_y = 1280, 640
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 4.0; KB.look_at(cam, (0, 0, 0), (0, 0, 1), 10)
    p = KB.new_output('04_Previews/Materials/M_TerrainBlend_demo.png'); scene.render.filepath = str(p)
    bpy.ops.render.render(write_still=True, scene=scene.name); print('RENDERED', p.name, flush=True)


if __name__ == '__main__':
    main()
