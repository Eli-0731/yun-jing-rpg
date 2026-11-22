"""DP05 蕈叢擺放示範 (11/15 300h pack, batch A): DP01–DP04 set on and around a stretch of a fallen log, for the integration
to copy. The work pack names Josh's DR08 rotten log "or any fallen log"; DR08 is not made yet, so this uses DR06_FallenTrunk_A
(art/exports/d2-logs-b on main). No new model: the log is NOT copied into this package — the script loads it from wherever
it is checked out and writes
  art/exports/d2-mushrooms-c/DP05_placement.json   every piece: GLB, position (m), rotation (XYZ Euler degrees and quaternion
                                                    w x y z) in DR06_FallenTrunk_A's own asset coordinates (its origin, z up, Blender axes)
  art/previews/d2-mushrooms-c/DP05/                 renders: overview, three-quarter, crouched close-up, top-down plan
Placement: every piece is put on the log by a ray (straight down for the top, sideways for the brackets) and tilted to the
surface it lands on, so nothing floats; the brackets (DP03) put their flat back on the bark.
blender -b --factory-startup -P art/source/d2-mushrooms-c/place_dp05.py -- --log <DR06_FallenTrunk_A_v001.glb> [--samples 96]
"""
import bpy,json,math,sys,argparse
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
a=argparse.ArgumentParser();a.add_argument('--log',required=True);a.add_argument('--samples',type=int,default=96)
A=a.parse_args(sys.argv[sys.argv.index('--')+1:])
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];E=ROOT/'art/exports/d2-mushrooms-c';OUT=ROOT/'art/previews/d2-mushrooms-c/DP05';OUT.mkdir(parents=True,exist_ok=True)
info=json.loads((E/'model_info.json').read_text(encoding='utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
def imp(path):
    before=set(sc.objects);bpy.ops.import_scene.gltf(filepath=str(path));new=[o for o in sc.objects if o not in before]
    for o in [o for o in new if any(s in o.name for s in ('_LOD1','_LOD2','Collision'))]:bpy.data.objects.remove(o)
    return [o for o in new if o.name in sc.objects]
log=imp(A.log);trunk=next(o for o in log if o.type=='MESH' and 'Trunk' in o.name and 'Detail' not in o.name)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
detail=next((o for o in log if o.type=='MESH' and o.name.startswith('Detail_')),None)
def cast(ob,o,d):
    mw=ob.matrix_world;mi=mw.inverted();ok,loc,n,_=ob.ray_cast(mi@Vector(o),(mi.to_3x3()@Vector(d)).normalized())
    return (ok,mw@loc if ok else None,(mi.transposed().to_3x3()@n).normalized() if ok else None)
def hit(o,d):   # the trunk, or the log's own moss shell (in its Detail_ object) when that lies within 6 cm over the bark;
    ok,loc,n=cast(trunk,o,d)   # anything higher in Detail_ (ferns, the sapling, its mushrooms) is ignored
    if not ok:raise RuntimeError(f'ray from {o} missed the trunk')
    if detail:
        ok2,l2,n2=cast(detail,o,d)
        if ok2 and 0<(loc-l2).length<.06 and (l2-Vector(o)).length<(loc-Vector(o)).length:return l2,n2
    return loc,n
# id, how, where (x along the trunk; top: y offset; side: z height), turn about the surface normal (deg), note
PLAN=[
 ('DP01_03','foot',(1.70,0.),0,'a row of brown mushrooms along the foot of the log (front side)'),
 ('DP01_01','foot',(2.55,-.10),25,'slender brown cluster at the foot'),
 ('DP01_02','foot',(3.35,-.05),-30,'stout trio at the foot'),
 ('DP02_02','foot',(2.15,-.06),10,'pale aqua-white trio tucked in at the foot'),
 ('DP02_03','ground',(2.95,-.75),-15,'white mushrooms on a broken chunk lying in front of the log'),
 ('DP04_02','foot',(3.75,-.04),0,'slime mould where the log meets the ground'),
 ('DP01_04','top',(2.20,.06),40,'brown tuft on the top of the log'),
 ('DP02_01','top',(3.05,.04),-20,'white cluster on the moss on top'),
 ('DP04_01','top',(1.75,-.05),15,'tiny bonnets on top'),
 ('DP04_03','top',(3.55,-.02),70,'mossy twig with tiny bells lying on top'),
 ('DP03_01','side',(2.60,.55),0,'thin shelves on the front side'),
 ('DP03_02','side',(3.30,.45),0,'hoof polypores on the front side'),
 ('DP03_03','side',(1.95,.40),0,'lingzhi on the front side'),
]
placed=[];rec=[]
for pid,how,(x,v),turn,note in PLAN:
    d=info[pid];glb=ROOT/d['files']['glb'];obs=imp(glb);root=next((o for o in obs if o.name.endswith('GroundOrigin')),None) or obs[0]
    if how=='top':   # the surface tilt from nine rays 6 cm apart (one ray's normal follows a single bark ridge)
        loc,_=hit((x,v,8.),(0,0,-1));ps=[hit((x+dx,v+dy,8.),(0,0,-1))[0] for dx in (-.06,0,.06) for dy in (-.06,0,.06)]
        n=(ps[8]-ps[0]).cross(ps[6]-ps[2]).normalized();n=n if n.z>0 else -n
    elif how=='side':   # brackets: a ray from the front (−Y) at height v; the slab's back goes on the bark, its front out along the normal
        loc,_=hit((x,-6.,v),(0,1,0));ps=[hit((x+dx,-6.,v+dz),(0,1,0))[0] for dx in (-.08,0,.08) for dz in (-.08,0,.08)]
        n=(ps[6]-ps[2]).cross(ps[8]-ps[0]).normalized();n=n if n.y<0 else -n
    else:   # foot / ground: on the ground (z = 0) in front of the log's surface at this x (v: extra offset to the front)
        lz,_=hit((x,-6.,.12),(0,1,0));loc=Vector((x,lz.y-.06+v,0.));n=Vector((0,0,1))
    if how=='side':
        fwd=-n;up=Vector((0,0,1));up=(up-fwd*up.dot(fwd)).normalized();right=fwd.cross(up)   # local +Y (the back) into the bark, local −Y out along the normal, local Z up
        R=Matrix((right,fwd,up)).transposed()
        rot=R.to_quaternion();loc=loc-n*.008   # back plane 8 mm into the bark: the flat slab's edges sink into the round trunk
    else:
        z=Vector((0,0,1));rot=z.rotation_difference(n) if how=='top' else Quaternion()
        rot=rot@Quaternion((0,0,1),math.radians(turn))
        if how=='top':loc=loc-n*.006   # the moss skirt / chip sinks 6 mm into the bark
    root.rotation_mode='QUATERNION';root.rotation_quaternion=rot;root.location=loc
    e=rot.to_euler('XYZ');placed+=obs
    rec.append({'id':pid,'glb':d['files']['glb'],'fbx':d['files']['fbx'],'location_m':[round(c,4) for c in loc],
                'rotation_euler_xyz_deg':[round(math.degrees(c),2) for c in e],'rotation_quaternion_wxyz':[round(c,5) for c in rot],
                'placed':how,'note':note})
doc={'what':'DP05 擺放示範：DP01–DP04 在一段倒木上的一組擺法，給整合時照抄',
     'log':{'id':'DR06_FallenTrunk_A','file':'art/exports/d2-logs-b/DR06_FallenTrunk_A/DR06_FallenTrunk_A_v001.glb','why':'the work pack names DR08 (not made yet) or any fallen log'},
     'coordinates':'DR06_FallenTrunk_A asset coordinates: its origin, metres, Blender axes (z up, -Y front). To use in Unity, parent the pieces under the placed log and convert like the FBX export (Blender -Y forward -> Unity -Z, z up -> y up).',
     'stretch_x_m':[1.6,3.9],'pieces':rec}
(E/'DP05_placement.json').write_text(json.dumps(doc,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
# ---------------- renders: D2 look (overcast, misty, wet brown soil) ----------------
bpy.ops.mesh.primitive_plane_add(size=40,location=(0,0,-.003));g=bpy.context.object
gm=bpy.data.materials.new('soil');gm.use_nodes=True;nt=gm.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.85
nz=nt.nodes.new('ShaderNodeTexNoise');nz.inputs['Scale'].default_value=30;rp=nt.nodes.new('ShaderNodeValToRGB')
rp.color_ramp.elements[0].color=(.025,.017,.010,1);rp.color_ramp.elements[1].color=(.085,.055,.032,1);nt.links.new(nz.outputs['Fac'],rp.inputs['Fac']);nt.links.new(rp.outputs['Color'],bs.inputs['Base Color']);g.data.materials.append(gm)
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(.46,.52,.59,1);bg.inputs['Strength'].default_value=.55
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(55),0,math.radians(-30)));sun=bpy.context.object;sun.data.energy=1.6;sun.data.angle=math.radians(25);sun.data.color=(.93,.95,1.)
sc.render.engine='CYCLES';sc.cycles.samples=A.samples;sc.cycles.use_denoising=True;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Base Contrast'
try:
    pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices()
    for dv in pr.devices:dv.use=dv.type=='OPTIX'
    sc.cycles.device='GPU'
except Exception:pass
sc.render.resolution_x,sc.render.resolution_y=1600,1000
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.clip_start=.02
def shot(name,p,t,lens):
    cam.location=Vector(p);cam.rotation_euler=(Vector(t)-Vector(p)).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    sc.render.filepath=str(OUT/f'DP05-{name}.png');bpy.ops.render.render(write_still=True)
shot('overview',(2.9,-5.2,1.75),(2.75,-.3,.45),32)
shot('threequarter',(4.6,-2.6,1.25),(2.7,-.55,.45),35)
shot('crouch',(3.0,-2.3,.30),(2.75,-.80,.28),38)
shot('top',(2.65,-2.3,2.05),(2.65,0.,.95),24)
shot('plan',(2.75,-.6,6.),(2.75,-.6,0),40)
print('DP05_DONE',len(rec),'pieces')
