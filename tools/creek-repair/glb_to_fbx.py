"""Unity in this project has no glTF importer, so the water-report-c props and the A04 silt bar the site reuses are converted to FBX unchanged.
The textures come out beside the FBX with materials.txt (name|base|normal|r|g|b|roughness); the scene builder makes URP materials from them.
blender --background --factory-startup --python tools/creek-repair/glb_to_fbx.py -- <in.glb> <out_dir> <id>"""
import sys
from pathlib import Path
import bpy

src, out, aid = sys.argv[sys.argv.index('--') + 1:][:3]
out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)


def save(img, stem):
    if img is None: return ''
    path = out / f'{stem}.png'; img.filepath_raw = str(path); img.file_format = 'PNG'; img.save()
    return path.name


def linked_image(socket):
    stack = [socket]
    while stack:
        for link in stack.pop().links:
            node = link.from_node
            if node.type == 'TEX_IMAGE': return node.image
            stack += [i for i in node.inputs if i.is_linked]
    return None


lines = []
for m in bpy.data.materials:
    if not m.use_nodes: continue
    b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is None: continue
    c = b.inputs['Base Color'].default_value
    lines.append('|'.join([m.name, save(linked_image(b.inputs['Base Color']), m.name + '_base'), save(linked_image(b.inputs['Normal']), m.name + '_normal'),
                           f'{c[0]:.4f}', f'{c[1]:.4f}', f'{c[2]:.4f}', f"{b.inputs['Roughness'].default_value:.3f}"]))
(out / 'materials.txt').write_text('\n'.join(lines), encoding='utf8')
bpy.ops.export_scene.fbx(filepath=str(out / f'{aid}.fbx'), path_mode='STRIP', embed_textures=False, axis_forward='-Z', axis_up='Y', bake_anim=False, add_leaf_bones=False)
