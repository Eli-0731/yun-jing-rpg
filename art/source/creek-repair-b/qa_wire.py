"""One spot of a saved asset .blend, isolated: its baked material, then the raw topology over it. Reads only; nothing is saved to the .blend.
blender --background <asset>.blend --python qa_wire.py -- <x y z radius> <view_x view_y view_z> <out_prefix>
Coordinates are the .blend's own world space (same as the delivered FBX after import)."""
import bpy, bmesh, sys
from pathlib import Path
from mathutils import Vector


def main():
    a = sys.argv[sys.argv.index('--') + 1:]; c = Vector(tuple(float(x) for x in a[:3])); rad = float(a[3]); view = Vector(tuple(float(x) for x in a[4:7])); out = a[7]
    lod0 = [o for o in bpy.data.objects if o.type == 'MESH' and '_LOD0' in o.name and not o.name.lower().endswith('_water_lod0')]
    for o in bpy.context.scene.objects: o.hide_render = True
    sc = bpy.context.scene; keep = []
    for o in lod0:
        bm = bmesh.new(); bm.from_mesh(o.data); m = o.matrix_world
        dead = [f for f in bm.faces if ((m @ f.calc_center_median()) - c).length > rad * 1.6]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        if not bm.faces: bm.free(); continue
        me = bpy.data.meshes.new(o.name + '_crop'); bm.to_mesh(me); bm.free()
        for s in o.data.materials: me.materials.append(s)
        n = bpy.data.objects.new(o.name + '_crop', me); n.matrix_world = m; sc.collection.objects.link(n); keep.append(n)
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.device = 'CPU'; sc.render.resolution_x = sc.render.resolution_y = 900; sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 1.2; sc.render.image_settings.file_format = 'PNG'
    w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.75, .75, .75, 1); sc.world = w
    cam = bpy.data.cameras.new('c'); cam.lens = 70; cam.clip_start = rad * .05; cam.clip_end = rad * 60; co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
    co.location = c + view.normalized() * rad * 2.9; co.rotation_euler = (c - co.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(Path(out + '_material.png').resolve()); bpy.ops.render.render(write_still=True)
    ink = bpy.data.materials.new('ink'); ink.use_nodes = True; nt = ink.node_tree; nt.nodes.clear(); e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (.02, .02, .02, 1); r = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], r.inputs[0])
    for n in keep:
        w2 = bpy.data.objects.new(n.name + '_wire', n.data.copy()); w2.matrix_world = n.matrix_world; sc.collection.objects.link(w2); w2.data.materials.clear(); w2.data.materials.append(ink)
        mod = w2.modifiers.new('w', 'WIREFRAME'); mod.thickness = rad / 500; mod.use_replace = True; mod.use_even_offset = False
    sc.render.filepath = str(Path(out + '_wire.png').resolve()); bpy.ops.render.render(write_still=True)
    print('QAWIRE', out, 'objects', len(keep))


main()
