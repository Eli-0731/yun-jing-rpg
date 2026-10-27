"""Render per-module previews from a kit .blend (PHASE 6): 10 orthographic views + 1 perspective 45° view.

  blender -b --python-exit-code 1 --python 05_Scripts/render_previews.py -- --file 01_Blender/road_edge_modules_v01.blend [--ids A01,A03] [--out 04_Previews/Individual] [--views 11_persp_45]

Opens the kit file read-only (never saved).  Each module is rendered alone, centred on its own bounds,
with the same 10 directions as the art library (front = -Y ... top, high front) plus 11_persp_45.png.
Only LOD0 parts are visible.  Writes <out>/<code>_<id>/NN_view.png and views.json; refuses to overwrite.
"""
import sys, json, math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_spec as K
import kit_blender as KB


HERO_DIR = {'C05': (1.0, -0.8, 0.35)}   # stone base: look at the river face (its top is hidden under the deck in use)


def cli():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def get(k, d=None): return a[a.index(k) + 1] if k in a else d
    return get('--file'), get('--ids'), get('--out', '04_Previews/Individual'), int(get('--samples', '32')), get('--views'), int(get('--ortho-samples', '12'))


def lod0_meshes(coll):
    return [o for o in coll.objects if o.type == 'MESH' and o.name.endswith('_LOD0')]


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def main():
    path, ids, out, samples, only_views, ortho_samples = cli()
    KB.start_session()
    KB.open_kit_file(KB.kit_path(path))
    src = bpy.context.scene
    scene = bpy.data.scenes.new('KIT_Preview')
    stu = bpy.data.collections.new('KIT_Studio'); scene.collection.children.link(stu)
    KB.studio(scene, stu, samples=samples, transparent=False)
    cam = bpy.data.objects.new('KIT_Camera', bpy.data.cameras.new('KIT_Camera')); stu.objects.link(cam); scene.camera = cam
    cam.data.clip_end = 500
    kit = bpy.data.collections['KIT_Modules']
    want = set(ids.split(',')) if ids else None
    done = []
    for coll in kit.children:
        mod = K.BY_ID.get(coll.name)
        if not mod or (want and mod['code'] not in want): continue
        scene.collection.children.link(coll)
        for o in coll.objects:
            if o.type == 'MESH': o.hide_render = not o.name.endswith('_LOD0')
        scene.view_layers[0].update()
        objs = lod0_meshes(coll); lo, hi = bounds(objs); centre = (lo + hi) / 2; ext = hi - lo
        folder = KB.kit_path(out, '%s_%s' % (mod['code'], mod['id']))
        records = []
        # 3/4 hero view looks at the side the terrain faces (banks face the water, C08 faces the river)
        terr = [o for o in objs if '_Terrain_' in o.name] or objs
        nsum = Vector((0, 0, 0))
        for o in terr:
            for poly in o.data.polygons: nsum += (o.matrix_world.to_3x3() @ poly.normal) * poly.area
        hz = Vector((nsum.x, nsum.y)); hz = hz / nsum.length if nsum.length else hz
        if mod['code'] in HERO_DIR:
            hero = HERO_DIR[mod['code']]
        elif hz.length > 0.12:
            az = math.atan2(hz.y, hz.x) - math.radians(35)
            hero = (math.cos(az), math.sin(az), 0.85)
        else:
            hero = (-1.0, -1.15, 0.85)
        radius = ext.length / 2
        views = [(n, d) for n, d in KB.VIEWS + [('11_persp_45', hero)] if not only_views or n in only_views.split(',')]
        for name, d in views:
            p = KB.new_output(str(Path(out) / ('%s_%s' % (mod['code'], mod['id'])) / (name + '.png')))
            scene.cycles.samples = samples if name.startswith('11') else ortho_samples   # denoised; the hero view gets more samples
            if name.startswith('11'):
                cam.data.type = 'PERSP'; cam.data.lens = 38
                KB.look_at(cam, centre, d, radius / math.sin(math.atan(18 / 38)) * 1.03)   # whole bounding sphere in frame: nothing cropped
            else:
                cam.data.type = 'ORTHO'; cam.data.ortho_scale = ext.length * 1.08
                KB.look_at(cam, centre, d, cam.data.ortho_scale * 2.3 + 5)
            scene.render.filepath = str(p); bpy.ops.render.render(write_still=True, scene=scene.name)
            records.append({'file': name + '.png', 'direction': list(d), 'projection': 'perspective' if name.startswith('11') else 'orthographic',
                            'camera_location': list(cam.location)})
        if only_views and (folder / 'views.json').exists():   # re-rendered views replace their records
            old = json.loads((folder / 'views.json').read_text()); keep = {r['file'] for r in records}
            records = [r for r in old['views'] if r['file'] not in keep] + records; records.sort(key=lambda r: r['file'])
        if not only_views or (folder / 'views.json').exists(): (folder / 'views.json').unlink(missing_ok=True); (folder / 'views.json').write_text(json.dumps({'module': mod['id'], 'code': mod['code'], 'source': path, 'same_geometry': True,
                                                       'note': 'Library view convention: 01_front looks from -Y. Kit modules travel along +X.',
                                                       'lod_rendered': 'LOD0 (terrain + details)', 'views': records}, indent=2))
        scene.collection.children.unlink(coll)
        done.append(mod['code']); print('PREVIEWED', mod['code'], flush=True)
    print('DONE', done, flush=True)


if __name__ == '__main__':
    main()
