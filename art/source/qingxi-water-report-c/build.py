"""Original water-report props: Eli-0731 / Codex, Blender 4.5.3 LTS.
Run in a separate Blender process, never in the user's working scene.
-- --batch 1 builds four props; --batch 2 builds all eight.
"""
import bpy,bmesh,math,json,hashlib,sys,argparse
from pathlib import Path
from mathutils import Vector
parser=argparse.ArgumentParser();parser.add_argument('--batch',type=int,choices=[1,2],default=1)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=Path(__file__).resolve().parents[3];REF=ROOT/'art/references/qingxi-water-report-c';OUT=ROOT/'art/exports/qingxi-water-report-c';PRE=ROOT/'art/previews/qingxi-water-report-c'
N=4 if args.batch==1 else 8
assert (REF/'review.json').is_file()
assert all((REF/f'C{i:02}-three-view.png').stat().st_size>10000 for i in range(1,N+1))
for p in [OUT,PRE]:p.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.engine='CYCLES';scene.cycles.samples=20
scene.render.resolution_x=1100;scene.render.resolution_y=825;scene.render.resolution_percentage=100;scene.world.color=(.43,.43,.43)
scene.view_settings.view_transform='AgX'

def material(name,color,pattern=None):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.78
    if pattern:
        im=bpy.data.images.new(name+'_packed',width=128,height=128);px=[]
        for y in range(128):
            for x in range(128):
                if pattern=='wood':v=.92+.035*math.sin(x*.8+math.sin(y*.03)*2)+.025*math.sin(x*2.1+y*.08)+.015*math.sin(x*8+y*6)
                else:v=.90+.04*math.sin(x*5)*math.sin(y*5)+.03*math.sin(x*.9+y*.7)
                px.extend([c*v for c in color]+[1])
        im.pixels.foreach_set(px);im.pack();tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return m
WOOD=material('warm_weathered_wood',(.40,.265,.145),'wood');DARK=material('old_joinery',(.245,.145,.075),'wood')
BAMBOO=material('aged_bamboo',(.43,.385,.19),'wood');HEMP=material('natural_hemp',(.58,.48,.30),'cloth')
STONE=material('warm_gray_stone',(.40,.43,.385),'stone');INSET=material('stone_recess',(.245,.285,.25),'stone')
BRONZE=material('aged_bronze',(.30,.30,.18));OCHRE=material('dry_ochre',(.61,.37,.13));TEAL=material('restored_teal',(.12,.39,.37));WATER=material('opaque_water_sample',(.19,.48,.53));next(n for n in WATER.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Roughness'].default_value=.25
FLAG_WIP=material('work_in_progress_hemp',(.64,.48,.23),'cloth');FLAG_DONE=material('complete_sage_hemp',(.32,.45,.34),'cloth')
MARK_DRY=material('soil_dry',(.45,.29,.16));MARK_WET=material('soil_moist',(.17,.20,.12));GOLD=material('record_choice',(.62,.49,.19))

def box(name,loc,size,mat,bevel=.006):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
    if bevel:
        m=o.modifiers.new('hand_worn_edges','BEVEL');m.width=min(bevel,min(size)*.22);m.segments=2;bpy.ops.object.modifier_apply(modifier=m.name)
    return o
def rod(name,a,b,r,mat,n=12):
    a,b=Vector(a),Vector(b);d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=d.length,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o
def mesh(name,verts,faces,mat):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.data.materials.append(mat);return o
def line(name,pts,r,mat):
    clean=[]
    for p in pts:
        if not clean or (Vector(p)-Vector(clean[-1])).length>1e-7:clean.append(p)
    cyclic=len(clean)>2 and (Vector(clean[0])-Vector(clean[-1])).length<1e-7
    if cyclic:clean.pop()
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1;cu.use_fill_caps=True
    sp=cu.splines.new('POLY');sp.points.add(len(clean)-1);sp.use_cyclic_u=cyclic
    for p,v in zip(sp.points,clean):p.co=(*v,1)
    o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.data.materials.append(mat);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update();return o
def ring(name,loc,r,t,mat,rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=t,major_segments=32,minor_segments=6,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(mat)
    if rotation:o.rotation_euler=rotation
    return o
def wave(name,y,z,mat,amplitude=.024,width=.39):
    return line(name,[(width*(i/24-.5),y,z+amplitude*math.sin(i/24*math.tau)) for i in range(25)],.007,mat)
def leaf(name,center,size,mat,axis='Y'):
    x,y,z=center
    if axis=='Y':pts=[(x+size*.32*math.sin(i*math.pi/12),y,z+size*(i/12-.5)) for i in range(13)]+[(x-size*.32*math.sin(i*math.pi/12),y,z+size*(i/12-.5)) for i in range(12,-1,-1)]
    else:pts=[(x+size*.32*math.sin(i*math.pi/12),y+size*(i/12-.5),z) for i in range(13)]+[(x-size*.32*math.sin(i*math.pi/12),y+size*(i/12-.5),z) for i in range(12,-1,-1)]
    return line(name,pts,.004,mat)
def empty(name,loc):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.location=loc;return o
def parent_keep(o,parent):
    bpy.context.view_layer.update();mw=o.matrix_world.copy();o.parent=parent;o.matrix_world=mw
def bounds(obs):
    bpy.context.view_layer.update();points=[o.matrix_world@Vector(v) for o in obs if o.type=='MESH' for v in o.bound_box]
    return [[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]
groups={};roots={};waterKeys=[];pivot=None;flag=None;soil=None
def start():return set(bpy.data.objects)
def finish(id,before):
    obs=[o for o in bpy.data.objects if o not in before];col=bpy.data.collections.new(id);scene.collection.children.link(col)
    root=empty(id+'_GroundOrigin',(0,0,0));obs.append(root)
    for o in obs:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
        if o!=root and o.parent is None:parent_keep(o,root)
        if o.type=='MESH':
            bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
            if not o.data.uv_layers:
                bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    groups[id]=obs;roots[id]=root

# C01 is a new radial council table, not the earlier rectangular sorting table.
s=start()
for k in range(6):
    a0=k*math.tau/6+.006;a1=(k+1)*math.tau/6-.006
    outline=[(.105*math.cos(a0),.105*math.sin(a0))]+[(.55*math.cos(a0+(a1-a0)*i/7),.55*math.sin(a0+(a1-a0)*i/7)) for i in range(8)]+[(.105*math.cos(a1),.105*math.sin(a1))]
    n=len(outline);v=[(x,y,z) for z in [.57,.62] for x,y in outline];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh('radial_top_segment',v,f,WOOD)
rod('table_center',(0,0,.57),(0,0,.62),.106,DARK,32)
legpoints=[]
for i in range(3):
    a=i*math.tau/3+math.pi/6;foot=(.43*math.cos(a),.43*math.sin(a),.045);top=(.32*math.cos(a),.32*math.sin(a),.58)
    rod('splayed_table_leg',foot,top,.038,DARK,10);box('stone_foot',(*foot[:2],.025),(.12,.12,.05),STONE,.012);legpoints.append((.40*math.cos(a),.40*math.sin(a),.19))
for i in range(3):rod('triangle_stretcher',legpoints[i],legpoints[(i+1)%3],.018,WOOD,8)
for i in range(3):
    x=(i-1)*.24;y=-.28
    rod('choice_inlay',(x,y,.619),(x,y,.623),.065,BRONZE,24)
    if i==0:ring('water_option',(x,y,.625),.028,.004,TEAL)
    if i==1:
        box('repair_option',(x,y,.627),(.058,.014,.006),OCHRE,.001);box('repair_option_stem',(x,y,.627),(.014,.045,.006),OCHRE,.001)
    if i==2:leaf('nursery_option',(x,y,.627),.065,TEAL,'Z')
finish('C01',s)

s=start()
box('stone_plinth',(0,0,.06),(.72,.36,.12),STONE,.018)
for x in [-.30,.30]:
    box('pivot_support',(x,0,.615),(.055,.07,.99),DARK)
    for y in [-.12,.12]:rod('support_brace',(x,y,.13),(x,0,.40),.015,WOOD,8)
rod('horizontal_axle',(-.34,0,.90),(.34,0,.90),.020,BRONZE,12)
beforePanel=set(bpy.data.objects)
for i in range(5):box('reversible_panel_slat',(0,0,.70+i*.08),(.52,.052,.078),WOOD)
rod('front_dry_circle',(0,-.030,.985),(0,-.040,.985),.043,OCHRE,24);wave('dry_line',-.037,.825,OCHRE)
rod('back_recovered_circle',(0,.030,.815),(0,.040,.815),.043,TEAL,24)
wave('flow_line_back_1',.037,.935,TEAL);wave('flow_line_back_2',.037,.875,TEAL)
panel=[o for o in bpy.data.objects if o not in beforePanel];pivot=empty('StatusPivot',(0,0,.90))
for o in panel:parent_keep(o,pivot)
pivot.rotation_euler.x=0;pivot.keyframe_insert(data_path='rotation_euler',frame=1);pivot.rotation_euler.x=math.pi;pivot.keyframe_insert(data_path='rotation_euler',frame=24);pivot.animation_data.action.name='WaterBoardFlip';scene.frame_set(1)
finish('C02',s)

def pail(cx,r,h):
    n=24;verts=[]
    for rad,z in [(r*.84,0),(r,h),(r-.014,h),(r*.84-.014,.022)]:verts.extend([(cx+rad*math.cos(i*math.tau/n),rad*math.sin(i*math.tau/n),z) for i in range(n)])
    faces=[]
    for a,b in [(0,1),(1,2),(2,3)]:
        for i in range(n):j=(i+1)%n;faces.append((a*n+i,a*n+j,b*n+j,b*n+i))
    faces += [tuple(range(n-1,-1,-1)),tuple(range(n*3,n*4))]
    mesh('pail_staves_hollow',verts,faces,WOOD)
    for z in [.055,h-.055]:ring('bronze_pail_band',(cx,0,z),r*(.84+.16*z/h)+.002,.006,BRONZE)
    for i in range(18):
        a=i*math.tau/18;rod('stave_join',(cx+r*.84*math.cos(a),r*.84*math.sin(a),.01),(cx+r*math.cos(a),r*math.sin(a),h-.008),.002,DARK,5)
    pts=[(cx+r*math.cos(i*math.pi/20),0,h+.17*math.sin(i*math.pi/20)) for i in range(21)];line('bamboo_pail_handle',pts,.009,BAMBOO)
    for x in [cx-r,cx+r]:rod('handle_pivot',(x,-.014,h-.008),(x,.014,h-.008),.012,BRONZE,10)
    rr=r-.023;wv=[(cx+rr*math.cos(i*math.tau/24),rr*math.sin(i*math.tau/24),.038) for i in range(24)];w=mesh('WaterSurface',wv,[tuple(range(24))],WATER)
    w.shape_key_add(name='Low');key=w.shape_key_add(name='Filled')
    for v in key.data:v.co.z += h*.72
    waterKeys.append(key)
s=start();pail(-.185,.155,.38);pail(.185,.125,.30);finish('C03',s)

s=start()
polepts=[(1.25*(i/32-.5),0,.225+.055*math.cos((i/32-.5)*math.pi)) for i in range(33)]
line('curved_bamboo_shoulder_beam',polepts,.025,BAMBOO)
for x in [-.56,-.36,0,.36,.56]:
    z=.225+.055*math.cos(x/1.25*math.pi);o=ring('bamboo_node',(x,0,z),.027,.004,DARK,(0,math.pi/2,0))
for x in [-.56,.56]:
    line('attachment_loop',[(x-.015,0,.24),(x-.018,0,.03),(x,0,.006),(x+.018,0,.03),(x+.015,0,.24)],.006,HEMP)
finish('C04',s)

if args.batch==2:
    s=start()
    rod('moisture_stake',(0,0,-.12),(0,0,.60),.019,DARK,8)
    box('installed_stone_collar',(0,0,.025),(.11,.09,.05),STONE)
    profile=[(-.14*math.sin(i*math.pi/12),.25+.40*i/12) for i in range(13)]+[(.14*math.sin(i*math.pi/12),.25+.40*i/12) for i in range(12,-1,-1)]
    # Drop coincident leaf tips before creating a closed prism.
    profile=[p for i,p in enumerate(profile) if i==0 or p!=profile[i-1]]
    if profile[-1]==profile[0]:profile.pop()
    n=len(profile);v=[(x,y,z) for y in [-.022,.022] for x,z in profile];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];mesh('leaf_moisture_face',v,f,WOOD)
    line('leaf_vein',[(0,-.027,.27),(0,-.027,.62)],.004,DARK)
    for z in [.37,.44,.51]:
        for sign in [-1,1]:line('leaf_side_vein',[(0,-.027,z),(sign*.08,-.027,z+.06)],.003,DARK)
    for x in [-.065,0,.065]:rod('soil_dots',(x,-.027,.36),(x,-.035,.36),.014,MARK_DRY,12)
    soil=box('SoilMoisturePatch',(0,-.026,.29),(.115,.008,.035),MARK_DRY,.002)
    for z in [.34,.53]:box('back_crossbrace',(0,.03,z),(.21,.025,.028),DARK)
    finish('C05',s)
    s=start()
    box('banner_stone_base',(0,0,.045),(.24,.22,.09),STONE,.02);rod('bamboo_banner_mast',(0,0,.07),(0,0,.85),.018,BAMBOO)
    rod('banner_crossbeam',(-.23,0,.79),(.23,0,.79),.014,BAMBOO)
    verts=[(-.18+.36*i/6,-.014+.008*math.sin(i*.6+j*.8),.75-.45*j/8) for j in range(9) for i in range(7)]
    faces=[(j*7+i,j*7+i+1,(j+1)*7+i+1,(j+1)*7+i) for j in range(8) for i in range(6)]
    flag=mesh('WorkCloth',verts,faces,FLAG_WIP)
    uv=flag.data.uv_layers.new(name='ClothUV')
    for poly in flag.data.polygons:
        for li,vi in zip(poly.loop_indices,poly.vertices):uv.data[li].uv=(vi%7/6,vi//7/8)
    bpy.context.view_layer.objects.active=flag;m=flag.modifiers.new('cloth_thickness','SOLIDIFY');m.thickness=.003;bpy.ops.object.modifier_apply(modifier=m.name)
    ring('banner_work_circle',(0,-.03,.56),.065,.008,OCHRE,(math.pi/2,0,0));wave('banner_flow_mark',-.032,.40,OCHRE,.012,.21)
    for x in [-.16,0,.16]:line('banner_tie',[(x,-.02,.76),(x,-.02,.80),(x,.015,.80),(x,.015,.76)],.005,HEMP)
    finish('C06',s)
    s=start()
    box('carrier_bottom',(0,0,.018),(.48,.28,.036),WOOD)
    for y in [-.13,.13]:box('carrier_side',(0,y,.08),(.48,.02,.13),WOOD)
    for x in [-.23,.23]:box('carrier_end',(x,0,.08),(.02,.25,.13),DARK)
    line('arched_carry_handle',[(-.23,0,.13),(-.20,0,.24),(0,0,.32),(.20,0,.24),(.23,0,.13)],.015,DARK)
    box('wood_mallet_head',(-.13,.055,.085),(.09,.07,.09),WOOD,.01);rod('wood_mallet_handle',(-.13,.055,.08),(.12,.055,.08),.012,DARK,10)
    box('chisel_bronze_tip',(-.14,-.07,.054),(.095,.034,.012),BRONZE,.002);rod('chisel_wood_handle',(-.095,-.07,.06),(.07,-.07,.06),.014,DARK,10)
    for i in range(4):ring('coiled_hemp_cord',(.145,-.01,.043+i*.009),.043,.005,HEMP)
    finish('C07',s)
    s=start()
    box('record_plinth',(0,0,.045),(.60,.26,.09),STONE,.015)
    profile=[(-.255,.085),(-.265,.68),(-.19,.83),(-.03,.92),(.15,.87),(.26,.73),(.25,.085)];n=len(profile)
    verts=[(x,y,z) for y in [-.087,.087] for x,z in profile];faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    tablet=mesh('record_tablet',verts,faces,STONE)
    box('recessed_record_face',(0,-.090,.47),(.37,.010,.62),INSET,.009)
    for z in [.69,.64]:wave('record_water_symbol',-.101,z,STONE,.015,.20)
    line('record_joint_symbol',[(-.10,-.101,.46),(-.04,-.101,.46),(-.04,-.101,.50),(.04,-.101,.50),(.04,-.101,.46),(.10,-.101,.46)],.008,STONE)
    leaf('record_nursery_symbol',(0,-.101,.29),.15,STONE)
    box('back_support_peg',(0,.102,.14),(.07,.04,.15),DARK)
    finish('C08',s)

def visual(state):
    pivot.animation_data_clear();pivot.rotation_euler.x=math.pi if state=='restored' else 0
    for key in waterKeys:key.value={'dry':0,'partial':.48,'restored':1}.get(state,0)
    if flag:
        flag.data.materials[0]=FLAG_DONE if state=='restored' else FLAG_WIP
        for o in groups['C06']:
            if o.type=='MESH' and ('banner_work_circle' in o.name or 'banner_flow_mark' in o.name):o.data.materials[0]=TEAL if state=='restored' else OCHRE
    if soil:soil.data.materials[0]=MARK_WET if state=='restored' else MARK_DRY
    bpy.context.view_layer.update()
visual('dry')
report={'author':'Eli-0731 / Codex','batch':args.batch,'blender':bpy.app.version_string,'units':'m','axes':'Z-up, front -Y in Blender; glTF Y-up','reference_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in REF.glob('C*-three-view.png')},'assets':[]}
for id,obs in groups.items():
    errors=[];warnings=[];meshes=[o for o in obs if o.type=='MESH'];bound=bounds(obs)
    for o in meshes:
        if not o.data.uv_layers:errors.append(o.name+': no UV')
        if any(p.area<1e-10 for p in o.data.polygons):errors.append(o.name+': degenerate face')
        if any(not math.isfinite(c) for v in o.data.vertices for c in v.co):errors.append(o.name+': invalid coordinate')
        bm=bmesh.new();bm.from_mesh(o.data);boundary=sum(1 for e in bm.edges if e.is_boundary);bad=sum(1 for e in bm.edges if len(e.link_faces)>2 or not e.link_faces)
        if bad:errors.append(o.name+': nonmanifold/loose edges')
        if boundary:
            if o.name.startswith('WaterSurface'):warnings.append(o.name+': intentional single water surface')
            else:errors.append(o.name+': unexpected boundary')
        bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=roots[id]
    bpy.ops.export_scene.gltf(filepath=str(OUT/f'{id}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
    report['assets'].append({'id':id,'dimensions_xyz':[p[1]-p[0] for p in bound],'local_bounds_xyz':bound,'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),'meshes':len(meshes),'materials':len({m.name for o in meshes for m in o.data.materials}),'errors':errors,'warnings':warnings,'morphs':sum(len(o.data.shape_keys.key_blocks)-1 for o in meshes if o.data.shape_keys),'lod_plan':'single prototype LOD; future remove small ties at 10m, cull small props at 25m; not measured','collision':'simple hull/boxes for structural parts; no collision for water, cloth, cord or icons'})
assert not any(a['errors'] for a in report['assets']),report
# C06 second material variant is the same item with a different cloth state.
if args.batch==2:
    visual('restored');bpy.ops.object.select_all(action='DESELECT')
    for o in groups['C06']:o.select_set(True)
    bpy.context.view_layer.objects.active=roots['C06'];bpy.ops.export_scene.gltf(filepath=str(OUT/'C06-complete.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False);visual('dry')

# Proxy plot only: objects remain in the left 2m; the right 1m is reserved clear.
floor=box('layout_proxy_3x5m',(0,0,-.035),(3,5,.07),material('plot_ground',(.34,.38,.29)),0)
bpy.ops.object.light_add(type='AREA',location=(3,-4,6));bpy.context.object.data.energy=750;bpy.context.object.data.size=5
bpy.ops.object.light_add(type='AREA',location=(-4,2,4));bpy.context.object.data.energy=480;bpy.context.object.data.size=4
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
def shot(name,target,eye,scale):
    cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(PRE/name);bpy.ops.render.render(write_still=True)
for id,obs in groups.items():
    for key,objects in groups.items():
        for o in objects:o.hide_render=key!=id
    b=bounds(obs);size=[p[1]-p[0] for p in b];target=[sum(p)/2 for p in b]
    shot(f'{id}-close.png',target,(2,-4,2.0),max(size)*2.15)
placements={'C01':[-.65,0,0],'C02':[-.90,1.4,0],'C03':[-.78,-1.30,0],'C04':[-.55,-2.0,0],'C05':[.18,1.25,.12],'C06':[.18,-.60,0],'C07':[-.65,.16,.62],'C08':[.15,2.05,0]}
for id,obs in groups.items():
    for o in obs:o.hide_render=False
    roots[id].location=placements[id]
    if id=='C04':
        roots[id].rotation_euler.x=math.pi/2;b=bounds(obs);roots[id].location.z-=b[2][0]
for state in ['dry','partial','restored']:
    visual(state);shot(f'corner-{state}.png',(-.15,0,.40),(5,-7,5),6.3)
visual('dry');cam.data.type='PERSP';cam.data.lens=36
cam.location=(1.35,-3.3,1.7);cam.rotation_euler=(Vector((-.45,.25,.62))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(PRE/'eye-height-1p7m.png');bpy.ops.render.render(write_still=True)
cam.data.type='ORTHO';shot('plan-3x5m.png',(0,0,0),(0,-.01,7),5.7)
report['plot_m']=[3,5];report['placements_xyz']=placements;report['character_reference_m']=1.75
report['clearance']={'reserved_route_x':[.52,1.50],'actual_prop_max_x':max(bounds(obs)[0][1] for obs in groups.values()),'main_road':'outside the 3x5m proxy; no main-scene edits'}
assert report['clearance']['actual_prop_max_x']<.52
visual('dry');bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).parent/f'WaterReportC_batch{args.batch}.blend'))
for a in report['assets']:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(OUT/f"{a['id']}.glb"))
    imported=[o for o in scene.objects if o.type=='MESH'];b=bounds(imported);a['roundtrip_dimensions_xyz']=[p[1]-p[0] for p in b]
    a['roundtrip_pass']=all(abs(x-y)<.002 for x,y in zip(a['dimensions_xyz'],a['roundtrip_dimensions_xyz'])) and all(o.data.uv_layers for o in imported)
    assert a['roundtrip_pass'],a
(OUT/f'batch{args.batch}-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('WATER_REPORT_MODELS_PASS',N)
