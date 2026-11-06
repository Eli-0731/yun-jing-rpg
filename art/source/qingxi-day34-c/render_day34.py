"""Fixed review rig for the C day 3-4 models. Eli-0731, Blender 4.5.3 LTS.
Imports the exported GLB or FBX (what the engine receives); a .blend only for the state checks glTF cannot carry (_Warmth).
blender -b -P render_day34.py -- --glb <path> --out <dir> --tag <name> [--views front,side,back,threequarter] [--light day|night|neutral|afternoon|dusk]
      [--glow <emission strength>] [--hide <name substring>] [--no-ruler] [--wire] [--eye <x,y,z,tx,ty,tz>] [--res 1280x960] [--state warmth=1] [--move name:dx,dy,dz] [--clay] [--wire-mm 0.6] [--mark x,y,z,radius;...]
Every view carries a 1.75 m figure (review spec), unless --no-ruler.
"""
import bpy,math,sys,argparse
from pathlib import Path
from mathutils import Vector
a=argparse.ArgumentParser()
for k,d in (('--glb',None),('--out',None),('--tag','view'),('--views','front,side,back,threequarter'),('--light','day'),('--hide',''),('--eye',''),('--res','1280x960'),('--ruler-x',''),('--at',''),('--cam',''),('--state',''),('--move','')):a.add_argument(k,default=d)
a.add_argument('--glow',type=float,default=None);a.add_argument('--wire-mm',type=float,default=None);a.add_argument('--mark',default='');a.add_argument('--samples',type=int,default=64);a.add_argument('--no-ruler',action='store_true');a.add_argument('--wire',action='store_true');a.add_argument('--clay',action='store_true')
args=a.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=args.samples;sc.cycles.use_denoising=True
try:
    pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices()
    for d in pr.devices:d.use=d.type=='OPTIX'
    sc.cycles.device='GPU'
except Exception:sc.cycles.device='CPU'
w,h=map(int,args.res.split('x'));sc.render.resolution_x=w;sc.render.resolution_y=h;sc.view_settings.view_transform='AgX';sc.view_settings.look='None'
ats=[[float(v) for v in a_.split(',')] for a_ in args.at.split(';')] if args.at else []
for i,g in enumerate(args.glb.split(',')):   # --at "x,y,yawdeg[,z];..." places each file (glb or fbx)
    before=set(sc.objects)
    if g.lower().endswith('.fbx'):bpy.ops.import_scene.fbx(filepath=g)
    elif g.lower().endswith('.blend'):   # the working file keeps the state drivers (_Warmth, _Lit) that glTF cannot carry
        with bpy.data.libraries.load(str(Path(g).resolve())) as (src,dst):dst.objects=list(src.objects)
        for o in dst.objects:
            if o and not any(c.name.endswith('_SourceParts') for c in o.users_collection):sc.collection.objects.link(o)
        for kv in [x for x in args.state.split(',') if x]:
            k,v=kv.split('=');[o.__setitem__(k,float(v)) for o in sc.objects if o.name.endswith('_GroundOrigin')]
    else:bpy.ops.import_scene.gltf(filepath=g)
    new=[o for o in sc.objects if o not in before]
    for o in new:
        if any(s in o.name for s in ('Collision','_LOD1','_LOD2','_COL')):o.hide_render=True
    if i<len(ats):
        x,y,yaw,z=(ats[i]+[0])[:4];rootish=[o for o in new if o.parent is None or o.parent not in new]
        for o in rootish:o.location=(o.location.x+x,o.location.y+y,o.location.z+z);o.rotation_mode='XYZ';o.rotation_euler.z+=math.radians(yaw)   # glTF roots import as quaternions
for mv in [x for x in args.move.split(';') if x]:   # --move "UP01_Gate:0,0,1.2" shifts a pivot (and its children)
    n,v=mv.split(':');d=Vector([float(c) for c in v.split(',')])
    for o in sc.objects:
        if o.name.split('.')[0].startswith(n):o.location+=d
bpy.context.view_layer.update()
for o in list(sc.objects):
    if args.hide and any(s and s in o.name for s in args.hide.split(',')):bpy.data.objects.remove(o)
obs=[o for o in sc.objects if o.type=='MESH' and not o.hide_render]
if args.clay:   # grey model: one flat grey, no colour, no normal map; alpha cut-outs (leaf cards, decals) keep their alpha
    for m in bpy.data.materials:
        bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
        if not bs:continue
        for k in ('Base Color','Normal','Roughness','Metallic','Emission Color'):
            for l in list(bs.inputs[k].links):m.node_tree.links.remove(l)
        bs.inputs['Base Color'].default_value=(.40,.40,.39,1);bs.inputs['Roughness'].default_value=.75;bs.inputs['Metallic'].default_value=0;bs.inputs['Emission Strength'].default_value=0
if args.glow is not None:
    for m in bpy.data.materials:
        bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
        if bs and bs.inputs['Emission Color'].is_linked:bs.inputs['Emission Strength'].default_value=args.glow   # only the lamp materials (emission texture)
pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
if not args.no_ruler:   # 1.75 m figure beside the asset
    fm=bpy.data.materials.new('ruler');fm.use_nodes=True;fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.30,.42,.55,1)
    x0=float(args.ruler_x) if args.ruler_x else hi.x+.45
    for loc,size in [((x0,0,.45),(.30,.18,.90)),((x0,0,1.18),(.40,.22,.58)),((x0,0,1.62),(.22,.22,.26))]:
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc);c=bpy.context.object;c.dimensions=size;c.data.materials.append(fm)
    for z in (0.5,1.0,1.5,1.75):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x0+.24,0,z));t_=bpy.context.object;t_.dimensions=(.10,.01,.006);t_.data.materials.append(fm)
    lo.x=min(lo.x,x0-.2);hi.x=max(hi.x,x0+.3);hi.z=max(hi.z,1.75)
ctr=(lo+hi)/2;rad=(hi-lo).length/2
bpy.ops.mesh.primitive_plane_add(size=60,location=(0,0,0));g=bpy.context.object
gm=bpy.data.materials.new('ground');gm.use_nodes=True;gb=gm.node_tree.nodes['Principled BSDF'];gb.inputs['Base Color'].default_value=(.40,.38,.33,1);gb.inputs['Roughness'].default_value=.95;g.data.materials.append(gm)
world=bpy.data.worlds.new('w');sc.world=world;world.use_nodes=True;bg=world.node_tree.nodes['Background']
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.lens=70;cam.data.clip_end=500
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def sun(name,rot,energy,color,angle=.05):
    l=bpy.data.objects.new(name,bpy.data.lights.new(name,'SUN'));l.data.energy=energy;l.data.color=color;l.data.angle=angle;l.rotation_euler=rot;sc.collection.objects.link(l);return l
if args.light=='neutral':
    bg.inputs['Color'].default_value=(.62,.62,.62,1);bg.inputs['Strength'].default_value=.9;sun('key',(math.radians(50),0,math.radians(-35)),2.2,(1,1,1),.3)
elif args.light=='night':   # moonlit blue night: the lamp is the only warm light
    bg.inputs['Color'].default_value=(.05,.07,.13,1);bg.inputs['Strength'].default_value=.6;sun('moon',(math.radians(40),0,math.radians(150)),.25,(.65,.75,1),.02)
elif args.light=='afternoon':   # warm-stone check: bright high sun, the warmth should almost vanish
    bg.inputs['Color'].default_value=(.50,.60,.75,1);bg.inputs['Strength'].default_value=.8;sun('key',(math.radians(35),0,math.radians(-30)),5.0,(1,.95,.86),.05)
elif args.light=='dusk':   # warm-stone check: sun just down, dim blue sky, the warmth becomes visible
    bg.inputs['Color'].default_value=(.16,.20,.32,1);bg.inputs['Strength'].default_value=.55;sun('key',(math.radians(84),0,math.radians(-60)),.35,(1,.6,.4),.1)
else:   # style guide: low warm morning sun, blue-violet sky fill, rim from behind
    bg.inputs['Color'].default_value=(.42,.52,.68,1);bg.inputs['Strength'].default_value=.55
    sun('key',(math.radians(62),0,math.radians(-40)),3.6,(1,.84,.62),.06);sun('rim',(math.radians(-62),0,math.radians(160)),2.0,(1,.86,.66),.1)
views={'front':(0,-1,.12),'side':(1,0,.12),'back':(0,1,.12),'threequarter':(-.72,-.72,.50)}
def shoot(v,d):
    dist=max(rad*3.9,(hi.z-lo.z)*3.0,(hi.x-lo.x)*2.4);cam.location=ctr+Vector(d).normalized()*dist;aim(cam,ctr)
    sc.render.filepath=str(out/f'{args.tag}-{v}.png');bpy.ops.render.render(write_still=True)
if args.eye:
    e=[float(x) for x in args.eye.split(',')];cam.location=Vector(e[:3]);aim(cam,Vector(e[3:]));cam.data.lens=28
    sc.render.filepath=str(out/f'{args.tag}.png');bpy.ops.render.render(write_still=True)
elif args.views:
    for v in args.views.split(','):shoot(v,views[v])
if args.wire:
    wm=bpy.data.materials.new('wire');wm.use_nodes=True;n=wm.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(.02,.05,.09,1);o2=n.new('ShaderNodeOutputMaterial');wm.node_tree.links.new(e.outputs[0],o2.inputs[0])
    flat=bpy.data.materials.new('flat');flat.use_nodes=True;flat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.8,.8,.78,1)
    for o in obs:
        d=o.copy();d.data=o.data.copy();sc.collection.objects.link(d);d.data.materials.clear();d.data.materials.append(wm)
        m=d.modifiers.new('w','WIREFRAME');m.thickness=args.wire_mm/1000 if args.wire_mm else max(.0004,min(.004,rad*.0008));m.use_replace=True
        for i in range(len(o.material_slots)):o.material_slots[i].material=flat
    for l in [o for o in sc.objects if o.type=='LIGHT']:bpy.data.objects.remove(l)
    bg.inputs['Color'].default_value=(.62,.62,.62,1);bg.inputs['Strength'].default_value=.9;sun('key',(math.radians(50),0,math.radians(-35)),2.2,(1,1,1),.3)
    if not args.cam:shoot('wire',views['threequarter'])   # with --cam the wire close-up below replaces the overview
if args.mark:   # --mark "x,y,z,r;...": small red dots at QA coordinates (qa-lod0.json), hidden where the asset hides them
    rm=bpy.data.materials.new('mark');rm.use_nodes=True;nn=rm.node_tree.nodes;nn.clear();em=nn.new('ShaderNodeEmission');em.inputs['Color'].default_value=(1,.05,.02,1);em.inputs['Strength'].default_value=4
    rm.node_tree.links.new(em.outputs[0],nn.new('ShaderNodeOutputMaterial').inputs[0])
    for mk in args.mark.split(';'):
        x,y,z,rr=[float(c) for c in mk.split(',')];bpy.ops.mesh.primitive_uv_sphere_add(radius=rr,location=(x,y,z));bpy.context.object.data.materials.append(rm)
if args.cam:   # explicit camera: x,y,z,tx,ty,tz,lens
    e=[float(x) for x in args.cam.split(',')];cam.location=Vector(e[:3]);aim(cam,Vector(e[3:6]));cam.data.lens=e[6]
    sc.render.filepath=str(out/f'{args.tag}-cam.png');bpy.ops.render.render(write_still=True)
print('RIG_DONE',len(obs),'meshes')
