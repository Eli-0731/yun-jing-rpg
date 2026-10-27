import bpy,sys,json,os,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parents[2];OUT=PROJECT/'art/previews/qingxi-training-yard-v1'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Qingxi_Training_Yard_v1.blend'))
sys.path.insert(0,str(Path(os.environ.get('BLENDER_ASSET_QA_SCRIPTS',str(Path.home()/'.codex/skills/blender-asset-qa/scripts')))))
import qa_check
names=['training-shelter','qi-striking-post','agility-post','weapon-rack','engraved-training-stone','training-banner']
results={}
if os.environ.get('YARD_QA','1')=='1':
    for name in names:
        full=qa_check.run(objects=[o.name for o in bpy.data.collections[name].objects],profile='game',eps=.00015,tol=.003,uv=True)
        parts=full['objects'].values()
        results[name]={'pass':full['pass'],'errors':full['errors'],
                       'warnings_count':len(full['warnings']),
                       'warnings_by_type':{
                           'stacked_uv':sum('UV overlap' in w for w in full['warnings']),
                           'flat_cap_ngons':sum('n-gons' in w for w in full['warnings']),
                           'hidden_contact_faces':sum('back-to-back' in w for w in full['warnings'])},
                       'mesh_parts':len(full['objects']),
                       'triangles':sum(o['tris'] for o in parts),
                       'boundary_edges':sum(o['boundary_edges'] for o in full['objects'].values()),
                       'nonmanifold_edges':sum(o['nonmanifold_edges'] for o in full['objects'].values()),
                       'degenerate_faces':sum(o['degenerate_faces'] for o in full['objects'].values()),
                       'floating_islands':len(full['floating'])}
        print('QA',name,json.dumps(results[name]),flush=True)
    (OUT/'qa-report.json').write_text(json.dumps(results,indent=2),encoding='utf8')
if os.environ.get('YARD_RENDER','1')=='1':
    scene=bpy.context.scene
    for name,loc,power,size in [('Key',(-4,-5,7),1700,5),('Fill',(4,-1,5),1100,4),('Rim',(0,5,6),2000,4)]:
        light=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,light);scene.collection.objects.link(ob);ob.location=loc;light.energy=power;light.shape='DISK';light.size=size;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',cd);scene.collection.objects.link(cam);scene.camera=cam
    for name in names:
        for n in names:
            for ob in bpy.data.collections[n].objects:ob.hide_render=n!=name
        cd.type='ORTHO';cd.ortho_scale=8.7 if name=='training-shelter' else 3.1
        center=Vector((0,0,1.7 if name=='training-shelter' else (1.3 if name=='training-banner' else .8)))
        cam.location=center+Vector((4,-6,3));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/(name+'-detail.png'));bpy.ops.render.render(write_still=True)
    # Independent assembly for integration evidence; not the core entry scene.
    placement={'training-shelter':(0,0,0),'qi-striking-post':(-1.55,.35,.12),'agility-post':(1.55,.35,.12),'weapon-rack':(2.0,1.55,.12),'engraved-training-stone':(-1.45,1.45,.12),'training-banner':(-3,-2.1,0)}
    for name in names:
        for ob in bpy.data.collections[name].objects:ob.hide_render=False;ob.location=placement[name]
    cd.type='PERSP';cd.lens=28;cam.location=(0,-8.5,1.70);cam.rotation_euler=(Vector((0,0,1.65))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/'eye-height-1.7m.png');bpy.ops.render.render(write_still=True)
    cd.lens=40;cam.location=(9,-12,8);cam.rotation_euler=(Vector((0,0,1.3))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/'yard-overview.png');bpy.ops.render.render(write_still=True)
    (OUT/'assembly-placement.json').write_text(json.dumps(placement,indent=2),encoding='utf8')
print('REVIEW_DONE',flush=True)
