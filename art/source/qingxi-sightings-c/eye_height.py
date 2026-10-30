"""1.7 m eye-height check for a sighting prop, staged in Blender (no engine). Eli-0731, Blender 4.5.3 LTS.
The prop sits on a grass/dirt patch the way it is found (A2/A3 roadside, HOME interior floor), camera at player eye height.
blender -b --factory-startup -P eye_height.py -- --glb <abs .glb> --out <abs .png> --ground grass|dirt|floor
"""
import bpy,math,sys,argparse
from mathutils import Vector
a=argparse.ArgumentParser();a.add_argument('--glb');a.add_argument('--out');a.add_argument('--ground',default='grass');a.add_argument('--dist',type=float,default=.9)
args=a.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.render.resolution_x=960;sc.render.resolution_y=540;sc.view_settings.view_transform='AgX'
bpy.ops.import_scene.gltf(filepath=args.glb)
obs=[o for o in sc.objects if o.type=='MESH'];pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
ctr=sum(pts,Vector())/len(pts)
cols={'grass':((.20,.28,.12),(.30,.36,.18)),'dirt':((.30,.24,.16),(.40,.33,.23)),'floor':((.32,.24,.16),(.42,.32,.21))}[args.ground]
gm=bpy.data.materials.new('ground');gm.use_nodes=True;nt=gm.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.95
n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=18;r=nt.nodes.new('ShaderNodeValToRGB')
r.color_ramp.elements[0].color=(*cols[0],1);r.color_ramp.elements[1].color=(*cols[1],1);nt.links.new(n.outputs['Fac'],r.inputs['Fac']);nt.links.new(r.outputs['Color'],bs.inputs['Base Color'])
bpy.ops.mesh.primitive_plane_add(size=8);g=bpy.context.object;g.data.materials.append(gm)
if args.ground=='floor':   # interior: plank floor seams
    w=nt.nodes.new('ShaderNodeTexWave');w.inputs['Scale'].default_value=3;w.bands_direction='Y';m=nt.nodes.new('ShaderNodeMix');m.data_type='RGBA';m.blend_type='MULTIPLY';m.inputs['Factor'].default_value=.25
    nt.links.new(r.outputs['Color'],m.inputs[6]);nt.links.new(w.outputs['Color'],m.inputs[7]);nt.links.new(m.outputs[2],bs.inputs['Base Color'])
world=bpy.data.worlds.new('w');sc.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.55,.66,.78,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
sun=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN'));sun.data.energy=3.2;sun.data.color=(1,.88,.72);sun.data.angle=.1;sun.rotation_euler=(math.radians(52),0,math.radians(-35));sc.collection.objects.link(sun)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));cam.data.lens=60;sc.collection.objects.link(cam);sc.camera=cam
cam.location=Vector((ctr.x-args.dist*.45,ctr.y-args.dist,1.70));cam.rotation_euler=(Vector((ctr.x,ctr.y,ctr.z))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=args.out;bpy.ops.render.render(write_still=True);print('EYE_DONE')
