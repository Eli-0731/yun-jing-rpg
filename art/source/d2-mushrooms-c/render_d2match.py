"""D2 look-match shots for the 11/15 standard (00-300h-共同標準.md §三/§四): render the asset under the
D2 concept light (overcast morning, low ground mist, dark wet soil) from the concept's camera heights,
so it can sit next to the matching crop of art/references/blocks/D2/V*.png (Eli-0731, Blender 4.5.3 LTS).
  eye     1.6 m eye height, ~3.5 m away, slightly down (V2/V5 foreground); --small 1: 0.30 m high, about 0.45 m away (mushrooms, moss)
  crouch  0.6 m, ~2 m away, looking north-west (V6 close-up); --small 1: 0.12 m high, 0.45 m away
blender -b --factory-startup -P render_d2match.py -- --glb <path> --out <dir> --tag <ID> [--samples 96]
"""
import bpy,math,sys,argparse
from pathlib import Path
from mathutils import Vector
a=argparse.ArgumentParser();a.add_argument('--glb');a.add_argument('--out');a.add_argument('--tag');a.add_argument('--samples',type=int,default=96)
a.add_argument('--fig',type=int,default=1);a.add_argument('--small',type=int,default=0)
A=a.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(A.out).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
(bpy.ops.import_scene.fbx if A.glb.lower().endswith('.fbx') else bpy.ops.import_scene.gltf)(filepath=A.glb)
for o in list(sc.objects):
    if any(s in o.name for s in ('Collision','_LOD1','_LOD2')):bpy.data.objects.remove(o)
obs=[o for o in sc.objects if o.type=='MESH'];bpy.context.view_layer.update()
pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
lo.z=max(lo.z,0.);ctr=(lo+hi)/2;H=hi.z;D=max(hi.x-lo.x,hi.y-lo.y,H)
sc.render.engine='CYCLES';sc.cycles.samples=A.samples;sc.cycles.use_denoising=True
try:
    pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices()
    for d in pr.devices:d.use=d.type=='OPTIX'
    sc.cycles.device='GPU'
except Exception:sc.cycles.device='CPU'
sc.render.resolution_x,sc.render.resolution_y=1280,960;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Base Contrast'
# overcast sky: grey-blue, low saturation, no hard sun
world=bpy.data.worlds.new('w');sc.world=world;world.use_nodes=True;nt=world.node_tree;bg=nt.nodes['Background']
bg.inputs['Color'].default_value=(.50,.54,.58,1);bg.inputs['Strength'].default_value=1.15
# mist in a finite box (an infinite world volume swallows the sky and sun)
bpy.ops.mesh.primitive_cube_add(size=1,location=(ctr.x,ctr.y,5));fog=bpy.context.object;fog.scale=(90,90,12)
fm_=bpy.data.materials.new('mist');fm_.use_nodes=True;fn=fm_.node_tree;fn.nodes.remove(fn.nodes['Principled BSDF'])
vol=fn.nodes.new('ShaderNodeVolumePrincipled');vol.inputs['Color'].default_value=(.80,.82,.84,1);vol.inputs['Density'].default_value=.012
fn.links.new(vol.outputs[0],fn.nodes['Material Output'].inputs['Volume']);fog.data.materials.append(fm_)
l=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN'));l.data.energy=.9;l.data.color=(.92,.94,1.);l.data.angle=math.radians(25)
l.rotation_euler=(math.radians(40),0,math.radians(-30));sc.collection.objects.link(l)
# dark wet forest soil, a little sheen
bpy.ops.mesh.primitive_plane_add(size=400);g=bpy.context.object;m=bpy.data.materials.new('soil');m.use_nodes=True;g.data.materials.append(m)
p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.075,.058,.042,1);p.inputs['Roughness'].default_value=.85
if A.fig:
    bpy.ops.mesh.primitive_cylinder_add(radius=.18,depth=1.75,location=(hi.x+.55,ctr.y+.3,.875));fig=bpy.context.object
    fm=bpy.data.materials.new('fig');fm.use_nodes=True;fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.30,.42,.55,1);fig.data.materials.append(fm)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.clip_end=300
def aim(p,t,lens):cam.location=Vector(p);cam.rotation_euler=(Vector(t)-Vector(p)).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
def shot(name):sc.render.filepath=str(out/f'{A.tag}-d2-{name}.png');bpy.ops.render.render(write_still=True)
t=Vector((ctr.x,ctr.y,H*.45))
dist=max(.45 if A.small else 3.5,D*2.6)
aim((ctr.x+dist*.30,ctr.y-dist*.95,(.30 if A.small else 1.6)),t,40);shot('eye')
dc=max(.45 if A.small else 2.0,D*1.5)
aim((ctr.x+dc*.6,ctr.y-dc*.8,(.12 if A.small else .6)),(ctr.x,ctr.y,H*.5),35);shot('crouch')
print('D2MATCH_DONE',A.tag)
