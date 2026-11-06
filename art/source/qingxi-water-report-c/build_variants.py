"""Seven reviewed shape variants and two interchangeable 3x5m village layouts.
Blender 4.5.3 LTS; Eli-0731 / Codex. Run in a separate background process.
"""
from pathlib import Path
import sys,json,hashlib,math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
review=json.loads((ROOT/'art/references/qingxi-water-report-c/variant-review.json').read_text(encoding='utf-8'))
for entry in review['assets']:
    assert entry['status'].startswith('accepted')
    assert (ROOT/'art/references/qingxi-water-report-c'/entry['reference']).stat().st_size>10000
# Reuse our original modeling primitives, not the old family meshes.
helper=HERE/'build.py'
exec(compile(helper.read_text(encoding='utf-8').split('# C01 is a new')[0],str(helper),'exec'))
for p in [OUT/'variants',PRE/'variants']:p.mkdir(exist_ok=True)
wetKeys={};cloths={};patterns={};patches={};interfaces={};details={}

def anchor(name,loc,**props):
    o=empty(name,loc)
    for k,v in props.items():o[k]=v
    return o

def prism(name,outline,depth,mat,y=0):
    n=len(outline)
    verts=[(x,y+dy,z) for dy in [-depth/2,depth/2] for x,z in outline]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,verts,faces,mat)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    return o

def shell(name,profile,n,thickness=.014):
    inner=[(r-thickness,z) for r,z in profile[:0:-1]]+[(profile[0][0]-thickness,profile[0][1]+.025)]
    rings=profile+inner
    vs=[(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for r,z in rings for i in range(n)]
    fs=[]
    for k in range(len(rings)-1):
        for i in range(n):j=(i+1)%n;fs.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    fs.extend([tuple(range(n-1,-1,-1)),tuple(range((len(rings)-1)*n,len(rings)*n))])
    return mesh(name,vs,fs,WOOD)

def water(id,n,height,radii):
    zs=[.012,(.025+height)/2,height-.028]
    vs=[(radii[0]*math.cos(i*math.tau/n),radii[0]*math.sin(i*math.tau/n),zs[0]) for i in range(n)]
    o=mesh('WaterSurface_'+id,vs,[tuple(range(n))],WATER);o.shape_key_add(name='Empty')
    keys=[]
    for name,r,z in [('HalfFull',radii[1],zs[1]),('Filled',radii[2],zs[2])]:
        key=o.shape_key_add(name=name)
        for i,v in enumerate(key.data):v.co=(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z)
        keys.append(key)
    wetKeys[id]=keys

bucketSpecs=[('C03_tall_01',[(.147,.02),(.158,.06),(.158,.40),(.164,.42)],16,'Straight 16-stave cylinder; cleats; inset foot',.42,(.125,.141,.146)),('C03_low_02',[(.187,.02),(.207,.06),(.213,.22)],8,'Eight broad flat panels; wide octagonal basin; raised square ears',.22,(.16,.181,.191)),('C03_bail_03',[(.127,.04),(.168,.09),(.18,.17),(.165,.25),(.14,.32),(.149,.34)],24,'Bowed belly, narrow mouth, two foot rails and rigid bamboo bail',.34,(.108,.163,.12))]
for id,profile,n,desc,h,radii in bucketSpecs:
    s=start();shell('HollowBody_'+id,profile,n)
    for r,z in [profile[1],profile[-1]]:
        pts=[((r+.002)*math.cos(i*math.tau/n),(r+.002)*math.sin(i*math.tau/n),z-.012) for i in range(n+1)]
        line('ReinforcementBand_'+id,pts,.005,BRONZE if n!=8 else BAMBOO)
    for i in range(n):
        a=i*math.tau/n
        line('StaveSeam_'+id,[((r+.001)*math.cos(a),(r+.001)*math.sin(a),z) for r,z in profile],.0015,DARK)
    for side in [-1,1]:
        ring('CarryEye_'+id,(side*.16,0,.30),.019,.004,BRONZE,(0,math.pi/2,0))
        anchor(id+'__Lift_'+('L' if side<0 else 'R'),(side*.16,0,.30))
    if id=='C03_tall_01':
        rod('InsetFoot',(0,0,0),(0,0,.026),.145,DARK,32)
        for side in [-1,1]:box('SideGripCleat',(side*.166,0,.235),(.04,.095,.028),WOOD)
    elif id=='C03_low_02':
        rod('OctagonalFoot',(0,0,0),(0,0,.026),.188,DARK,8)
        for side in [-1,1]:
            box('RaisedEar',(side*.20,0,.248),(.05,.065,.146),DARK)
            rod('EyeMountPin',(side*.16,0,.30),(side*.21,0,.30),.006,BRONZE,10)
    else:
        for x in [-.10,.10]:box('SeparateFootRail',(x,0,.02),(.075,.18,.04),DARK)
        line('RigidBambooBail',[(.16*math.cos(i*math.pi/24),0,.30+.26*math.sin(i*math.pi/24)) for i in range(25)],.009,BAMBOO)
    water(id,n,h,radii)
    interfaces[id]={'Lift_L':[-.16,0,.30],'Lift_R':[.16,0,.30]}
    details[id]=desc;finish(id,s)

for id in ['C05_notch_01','C05_fork_02']:
    s=start();box('SquareTongue',(0,0,.195),(.04,.04,.63),DARK)
    box('StoneSocketCollar',(0,0,.03),(.16,.14,.06),STONE,.012 if 'notch' in id else .025)
    if 'notch' in id:
        outline=[(-.15,.28),(.15,.28),(.15,.64),(.075,.64),(.065,.70),(-.15,.69),(-.15,.49),(-.11,.47),(-.11,.43),(-.15,.42)]
        prism('NotchedTimberEdge',outline,.040,WOOD,y=-.006)
        for z in [.34,.60]:box('BackBatten',(0,.032,z),(.27,.024,.025),DARK)
        dots=[(0,z) for z in [.40,.49,.58]];patchZ=.33
        details[id]='Tall asymmetric broken/notched wood edge, straight square post and rectangular stone collar'
    else:
        prism('LowerChamferedBoard',[(-.18,.385),(-.14,.34),(.14,.34),(.18,.385),(.18,.477),(-.18,.477)],.040,WOOD,y=-.006)
        prism('UpperSteppedBoard',[(-.165,.48),(.165,.48),(.165,.62),(-.015,.62),(-.03,.59),(-.165,.59)],.040,WOOD,y=-.006)
        for side in [-1,1]:rod('ForkBrace',(0,.040,.135),(side*.125,.040,.375),.022,DARK,4)
        for z in [.37,.55]:box('BackBatten',(0,.038,z),(.29,.024,.024),DARK)
        dots=[(x,.525) for x in [-.105,0,.105]];patchZ=.405
        details[id]='Two offset boards, stepped/chamfered silhouette, visible Y-braces and chamfered socket'
    for (x,z),mat in zip(dots,[MARK_WET,MARK_DAMP,MARK_DRY]):rod('SoilSampleDisc',(x,-.02,z),(x,-.030,z),.024,mat,16)
    patches[id]=box('SoilMoisturePatch_'+id,(0,-.028,patchZ),(.09,.012,.030),MARK_DRY,.003)
    anchor(id+'__GroundSocket',(0,0,0),tongueWidth=.04,burialDepth=.12);anchor(id+'__PanelMount',(0,0,.46))
    interfaces[id]={'GroundSocket':[0,0,0],'PanelMount':[0,0,.46]};finish(id,s)

for id in ['C06_fork_01','C06_slant_02']:
    s=start();box('SharedStoneFoot',(0,0,.045),(.24,.22,.09),STONE,.02)
    rod('SharedMast',(0,.015,.07),(0,.015,.85),.018,BAMBOO)
    rod('SharedCrossbeam',(-.23,0,.79),(.23,0,.79),.014,BAMBOO)
    if 'fork' in id:
        outline=[(-.18,.75),(-.18,.30),(0,.46),(.18,.30),(.18,.75)]
        details[id]='Deep V notch with two pointed swallowtail ends; central mast'
    else:
        outline=[(-.18,.75),(-.18,.38),(-.045,.30),(.125,.30),(.18,.355),(.18,.75)]
        details[id]='Asymmetric diagonal hem with short bottom and clipped right corner; central mast'
    cloths[id]=prism('WorkCloth_'+id,outline,.004,FLAG_WIP,y=-.02)
    for x in [-.16,0,.16]:
        line('HempTie',[(x,-.023,.75),(x,-.023,.80),(x,.018,.80),(x,.018,.75)],.004,HEMP)
        anchor(id+'__ClothTie_'+('Left' if x<0 else 'Right' if x>0 else 'Center'),(x,0,.79))
    a=start()
    line('WorkOpenCircle',[(.045*math.cos(.25+i*5.1/24),-.028,.635+.045*math.sin(.25+i*5.1/24)) for i in range(25)],.004,OCHRE)
    for z in [.535,.51]:box('WorkProgressStrip',(0,-.027,z),(.09,.006,.007),OCHRE,.001)
    work=[o for o in bpy.data.objects if o not in a]
    a=start();ring('CompleteClosedCircle',(0,-.028,.635),.045,.004,TEAL,(math.pi/2,0,0));wave('CompleteFlowMark',-.028,.535,TEAL,.008,.11)
    done=[o for o in bpy.data.objects if o not in a];patterns[id]=(work,done)
    interfaces[id]={'ClothTie_Left':[-.16,0,.79],'ClothTie_Center':[0,0,.79],'ClothTie_Right':[.16,0,.79]};finish(id,s)

def state(name):
    for keys in wetKeys.values():
        keys[0].value=1 if name=='partial' else 0;keys[1].value=1 if name=='restored' else 0
    for id,cloth in cloths.items():
        cloth.data.materials[0]=FLAG_DONE if name=='restored' else FLAG_WIP
        for o in patterns[id][0]:o.hide_render=name=='restored'
        for o in patterns[id][1]:o.hide_render=name!='restored'
    for o in patches.values():o.data.materials[0]=MARK_WET if name=='restored' else MARK_DAMP if name=='partial' else MARK_DRY
    for o in scene.objects:
        if o.name.startswith('StatusPivot'):o.rotation_euler.x=math.pi if name=='restored' else 0
    bpy.context.view_layer.update()

def export(path,obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        if not o.hide_render:o.select_set(True)
    bpy.context.view_layer.objects.active=next(o for o in obs if o.select_get())
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)

report={'author':'Eli-0731 / Codex','blender':bpy.app.version_string,'units':'m','review_sha256':hashlib.sha256((REF/'variant-review.json').read_bytes()).hexdigest(),'variants':[],'layouts':{}}
state('dry')
for id,obs in groups.items():
    meshes=[o for o in obs if o.type=='MESH'];errors=[];b=bounds(obs)
    for o in meshes:
        if not o.data.uv_layers:errors.append(o.name+': missing UV')
        if any(p.area<1e-10 for p in o.data.polygons):errors.append(o.name+': degenerate face')
        bm=bmesh.new();bm.from_mesh(o.data)
        if any(len(e.link_faces)>2 or not e.link_faces for e in bm.edges):errors.append(o.name+': nonmanifold')
        if not o.name.startswith('WaterSurface') and any(e.is_boundary for e in bm.edges):errors.append(o.name+': open boundary')
        bm.free()
    assert not errors,(id,errors)
    export(OUT/'variants'/f'{id}.glb',obs)
    if id.startswith('C06'):
        state('restored');export(OUT/'variants'/f'{id}-complete.glb',obs);state('dry')
    meshSignature=[tuple(round((v.co[i]-o.bound_box[0][i])/(max(c[i] for c in o.bound_box)-min(c[i] for c in o.bound_box) or 1),5) for i in range(3)) for o in meshes for v in o.data.vertices]
    report['variants'].append({'id':id,'dimensions_xyz':[p[1]-p[0] for p in b],'bounds_xyz':b,'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),'materials':len({m.name for o in meshes for m in o.data.materials}),'morphs':sum(len(o.data.shape_keys.key_blocks)-1 for o in meshes if o.data.shape_keys),'interface':interfaces[id],'construction':details[id],'normalized_geometry_sha256':hashlib.sha256(str(meshSignature).encode()).hexdigest(),'reference_sha256':hashlib.sha256((REF/'variants'/f'{id}-three-view.png').read_bytes()).hexdigest(),'errors':errors,'collision':'prototype scene uses conservative whole-prop XZ AABBs; water and icons have no independent collider; not Unity collision','lod':'single prototype LOD; no measured mobile budget'})
assert len({a['normalized_geometry_sha256'] for a in report['variants']})==7

floor=box('layout_proxy_3x5m',(0,0,-.035),(3,5,.07),material('plot_ground',(.34,.38,.29)),0)
bpy.ops.object.light_add(type='AREA',location=(3,-4,6));bpy.context.object.data.energy=750;bpy.context.object.data.size=5
bpy.ops.object.light_add(type='AREA',location=(-4,2,4));bpy.context.object.data.energy=480;bpy.context.object.data.size=4
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam
def shot(path,target,eye,scale=2,perspective=False):
    cam.data.type='PERSP' if perspective else 'ORTHO';cam.data.lens=36;cam.data.ortho_scale=scale
    cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(PRE/path);bpy.ops.render.render(write_still=True)
for id,obs in groups.items():
    for key,objects in groups.items():
        for o in objects:o.hide_render=key!=id
    state('dry')
    for key,objects in groups.items():
        if key!=id:
            for o in objects:o.hide_render=True
    b=bounds(obs);target=[sum(p)/2 for p in b];extent=max(p[1]-p[0] for p in b)
    shot(f'variants/{id}-close.png',target,(1.8,-3.2,2.4),extent*1.8)
    if id.startswith(('C03','C06')):
        for label,mode in [('empty','dry'),('half','partial'),('full','restored')] if id.startswith('C03') else [('work','dry'),('complete','restored')]:
            state(mode)
            for key,objects in groups.items():
                if key!=id:
                    for o in objects:o.hide_render=True
            shot(f'variants/{id}-{label}.png',target,(1.8,-3.2,2.4),extent*1.8)

# Reuse only our five single-refinement families from the original mother file.
with bpy.data.libraries.load(str(HERE/'WaterReportC_batch2.blend'),link=False) as (src,dst):dst.collections=['C01','C02','C04','C07','C08']
for col in dst.collections:
    scene.collection.children.link(col);groups[col.name]=list(col.objects);roots[col.name]=next(o for o in col.objects if o.name.startswith(col.name+'_GroundOrigin'))
    for o in col.objects:
        if o.name.startswith('StatusPivot'):o.animation_data_clear()

layouts={
 'a':{'C01':[-.68,0,0],'C02':[-.98,1.43,0],'C04':[-.55,-2.10,0],'C07':[-.68,.16,.631],'C08':[.12,2.05,0],'C03_tall_01':[-1.12,-1.10,0],'C03_low_02':[-.51,-1.55,0],'C03_bail_03':[-.35,-.94,0],'C05_notch_01':[.13,1.08,0],'C05_fork_02':[-.53,2.12,0],'C06_fork_01':[.15,-.61,0],'C06_slant_02':[-.98,.69,0]},
 'b':{'C01':[-.68,.12,0],'C02':[-.98,1.55,0],'C04':[-.55,-2.10,0],'C07':[-.68,.28,.631],'C08':[.12,2.05,0],'C03_tall_01':[-.52,-1.52,0],'C03_low_02':[-1.12,-1.02,0],'C03_bail_03':[-.05,-1.18,0],'C05_notch_01':[-.54,2.12,0],'C05_fork_02':[.14,1.11,0],'C06_fork_01':[-1.03,.80,0],'C06_slant_02':[.13,-.54,0]}}
def arrange(key):
    for id,loc in layouts[key].items():
        roots[id].location=loc
        for o in groups[id]:o.hide_render=False
        if id=='C04':roots[id].rotation_euler.x=math.pi/2;roots[id].location.z-=bounds(groups[id])[2][0]
    state('dry')

for key in layouts:
    arrange(key)
    measurements=[]
    for id,obs in groups.items():
        b=bounds(obs)
        assert b[0][0]>=-1.5 and b[0][1]<.52 and b[1][0]>=-2.5 and b[1][1]<=2.5,(key,id,b)
        if id not in ['C07'] and not id.startswith('C05'):assert abs(b[2][0])<.002,(id,b)
        measurements.append({'id':id,'position':list(roots[id].location),'bounds_xyz':b})
    report['layouts'][key]={'instances':measurements,'route_x':[.52,1.50],'character_reference_m':1.75,'eye_height_m':1.7}
    for mode in ['dry','partial','restored']:
        state(mode);shot(f'corner-{mode}.png' if key=='a' else f'corner-b-{mode}.png',(-.15,0,.4),(5,-7,5),6.3)
    state('dry')
    shot(f'variants/eye-{key}-south-1p7m.png',(-.50,.4,.55),(1.25,-2.7,1.7),perspective=True)
    shot(f'variants/eye-{key}-north-1p7m.png',(-.5,-.25,.50),(1.25,2.7,1.7),perspective=True)
    scene.render.resolution_x=1000;scene.render.resolution_y=1400
    shot(f'variants/plan-{key}.png',(0,0,0),(0,0,7),5.6)
    scene.render.resolution_x=1100;scene.render.resolution_y=825
    state('dry');export(OUT/'variants'/f'VillageCorner-{key}.glb',[o for obs in groups.values() for o in obs]+[floor])
arrange('a');state('dry');bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'WaterReportC_variants.blend'))

for a in report['variants']:
    for suffix in ['', '-complete'] if a['id'].startswith('C06') else ['']:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.gltf(filepath=str(OUT/'variants'/f"{a['id']}{suffix}.glb"))
        obs=list(scene.objects);meshes=[o for o in obs if o.type=='MESH'];b=bounds(meshes)
        dims=[p[1]-p[0] for p in b]
        assert all(abs(x-y)<.002 for x,y in zip(dims,a['dimensions_xyz'])),a
        assert all(o.data.uv_layers for o in meshes),a
        morphs=sum(len(o.data.shape_keys.key_blocks)-1 for o in meshes if o.data.shape_keys)
        assert morphs==a['morphs'],a
        for name,pos in a['interface'].items():
            found=next((o for o in obs if o.name.startswith(a['id']+'__'+name)),None);assert found is not None,(a,name)
            assert (found.matrix_world.translation-Vector(pos)).length<.002,(a,name)
        a['roundtrip_pass']=True
        if suffix:a['complete_state_roundtrip_pass']=any(m.name.startswith('complete_sage_hemp') for o in meshes for m in o.data.materials);assert a['complete_state_roundtrip_pass']
(OUT/'variants/manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('WATER_REPORT_VARIANTS_PASS',len(report['variants']))
