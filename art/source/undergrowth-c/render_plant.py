"""Plant review shots asked for by 樹木重做-v2-分工.md §3 (Eli-0731, Blender 4.5.3 LTS):
  silhouette  three black silhouettes on white (front, side, 35°): weight, asymmetry, holes of different sizes
  under       from under the crown looking up: the twigs run into the leaves
  far20/far60 at 20 m and 60 m with EEVEE (mipmapped texture filtering, as in the game): no flicker, no mush
  front, left35, right35   the comparison set: same light, front and 35° to each side, 1.75 m figure
blender -b --factory-startup -P render_plant.py -- --glb <path> --out <dir> --tag <ID> [--lod N (FBX)] [--sets silhouette,under,far,turn]
"""
import bpy,math,sys,argparse
from pathlib import Path
from mathutils import Vector
a=argparse.ArgumentParser();a.add_argument('--glb');a.add_argument('--out');a.add_argument('--tag');a.add_argument('--lod',type=int,default=0)
a.add_argument('--sets',default='silhouette,under,far,turn');a.add_argument('--samples',type=int,default=64)
A=a.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(A.out).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
(bpy.ops.import_scene.fbx if A.glb.lower().endswith('.fbx') else bpy.ops.import_scene.gltf)(filepath=A.glb)
for o in list(sc.objects):
    if any(s in o.name for s in ('Collision',)+tuple(f'_LOD{k}' for k in range(3) if k!=A.lod)):bpy.data.objects.remove(o)
obs=[o for o in sc.objects if o.type=='MESH'];bpy.context.view_layer.update()
pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
lo.z=max(lo.z,0.);ctr=(lo+hi)/2;H=hi.z
def engine(e):
    if e=='eevee':sc.render.engine='BLENDER_EEVEE_NEXT';sc.eevee.taa_render_samples=32
    else:
        sc.render.engine='CYCLES';sc.cycles.samples=A.samples;sc.cycles.use_denoising=True
        try:
            pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices()
            for d in pr.devices:d.use=d.type=='OPTIX'
            sc.cycles.device='GPU'
        except Exception:sc.cycles.device='CPU'
sc.render.resolution_x,sc.render.resolution_y=1280,960;sc.view_settings.view_transform='AgX'
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.clip_end=500
def aim(p,t,lens):cam.location=Vector(p);cam.rotation_euler=(Vector(t)-Vector(p)).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
def shot(name):sc.render.filepath=str(out/f'{A.tag}-{name}.png');bpy.ops.render.render(write_still=True)
world=bpy.data.worlds.new('w');sc.world=world;world.use_nodes=True;bg=world.node_tree.nodes['Background']
gnd=None
def ground(col):
    global gnd
    if gnd is None:
        bpy.ops.mesh.primitive_plane_add(size=400);gnd=bpy.context.object;m=bpy.data.materials.new('g');m.use_nodes=True;gnd.data.materials.append(m)
    gnd.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*col,1);gnd.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.95
def sun(rot,e,c):l=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN'));l.data.energy=e;l.data.color=c;l.data.angle=.06;l.rotation_euler=rot;sc.collection.objects.link(l);return l
sets=A.sets.split(',')
D=max(hi.x-lo.x,hi.y-lo.y,H)
if 'silhouette' in sets:   # black on white, no light: the shape alone
    engine('eevee');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=1;sc.view_settings.view_transform='Standard'
    blk=bpy.data.materials.new('blk');blk.use_nodes=True;nt=blk.node_tree;nt.nodes.clear();e=nt.nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=(0,0,0,1);nt.links.new(e.outputs[0],nt.nodes.new('ShaderNodeOutputMaterial').inputs[0])
    keep={o.name:[s.material for s in o.material_slots] for o in obs}
    for o in obs:
        for s_ in o.material_slots:s_.material=blk
    t=Vector((ctr.x,ctr.y,H*.5))
    for v,d in (('front',(0,-1,0)),('side',(1,0,0)),('35',(math.sin(math.radians(35)),-math.cos(math.radians(35)),0))):
        aim(t+Vector(d)*D*3.2,t,50);shot(f'silhouette-{v}')
    for o in obs:
        for s_,m in zip(o.material_slots,keep[o.name]):s_.material=m
    sc.view_settings.view_transform='AgX'
bg.inputs['Color'].default_value=(.42,.52,.68,1);bg.inputs['Strength'].default_value=.55
sun((math.radians(55),0,math.radians(-35)),3.4,(1,.86,.66));sun((math.radians(-60),0,math.radians(160)),1.6,(1,.88,.70))
ground((.36,.33,.27))
if 'under' in sets:   # lying under the crown, looking up through it
    engine('cycles');aim((ctr.x+.25,ctr.y-.35,.12),(ctr.x-.05,ctr.y+.10,H*.85),18);shot('under')
if 'far' in sets:   # game distances: EEVEE filters the textures with mipmaps as the engine does
    engine('eevee');sc.render.resolution_x,sc.render.resolution_y=960,540
    for d in (20,60):aim((ctr.x+d*.34,ctr.y-d*.94,1.6),(ctr.x,ctr.y,H*.45),50);shot(f'far{d}m')
    sc.render.resolution_x,sc.render.resolution_y=1280,960
if 'turn' in sets:   # front and 35° each side, the same light: the comparison with the standard image
    engine('cycles');bpy.ops.mesh.primitive_cylinder_add(radius=.18,depth=1.75,location=(hi.x+.45,ctr.y,.875));fig=bpy.context.object
    fm=bpy.data.materials.new('fig');fm.use_nodes=True;fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.30,.42,.55,1);fig.data.materials.append(fm)
    t=Vector((ctr.x+.2,ctr.y,H*.48))
    for v,ang in (('front',0),('left35',-35),('right35',35)):
        r=math.radians(ang);aim(t+Vector((math.sin(r),-math.cos(r),.10))*D*3.0,t,50);shot(v)
print('PLANT_DONE',A.tag)
