"""F01_Field's look for Blender review sheets: base texture times vertex colour, as the game's ww materials draw it.

The FBX carries the normal maps only, so in Blender the field otherwise renders plain white. Materials in the open file change; nothing is saved.

blender --background --factory-startup <blend> --python field_look.py --python ruler_views.py -- <ID> <repo>/art
"""
import bpy, sys
from pathlib import Path


def apply(art):
    textures = Path(art) / 'source' / 'qingxi-waterworks-b' / 'textures'
    for m in bpy.data.materials:
        key = m.name.split('.')[0]
        if not key.startswith('ww_') or not m.use_nodes: continue
        nodes, links = m.node_tree.nodes, m.node_tree.links
        bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None or bsdf.inputs['Base Color'].is_linked: continue
        col = nodes.new('ShaderNodeVertexColor'); col.layer_name = 'Col'
        png = textures / f'{key}.png'
        if not png.exists():
            links.new(col.outputs['Color'], bsdf.inputs['Base Color']); continue
        tex = nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(png), check_existing=True)
        mix = nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1
        links.new(tex.outputs['Color'], mix.inputs['A']); links.new(col.outputs['Color'], mix.inputs['B']); links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])


if __name__ == '__main__': apply(sys.argv[-1])
