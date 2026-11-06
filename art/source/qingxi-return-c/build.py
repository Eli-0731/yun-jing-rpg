"""Original Qingxi return corner, Eli-0731 / Codex; Blender 4.5.3 LTS.
Requires saved imagegen reference review before any geometry is built.
Run with -- --batch 1 for C01-C04; --batch 2 for C01-C08.
"""
import bpy, math, json, hashlib, sys, argparse
from pathlib import Path
from mathutils import Vector
args=argparse.ArgumentParser();args.add_argument('--batch',type=int,choices=[1,2],default=1)
opt=args.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=Path(__file__).resolve().parents[3]
REF=ROOT/'art/references/qingxi-return-c'; OUT=ROOT/'art/exports/qingxi-return-c'; PRE=ROOT/'tools/qingxi-return-c/previews'
COUNT=4 if opt.batch==1 else 8
assert (REF/'review.json').is_file()
assert all((REF/f'C{i:02}-three-view.png').stat().st_size>10000 for i in range(1,COUNT+1))
for p in [OUT,PRE]:p.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=1000;scene.render.resolution_y=750;scene.render.resolution_percentage=100
scene.world.color=(.35,.35,.35);scene.view_settings.view_transform='AgX'

def mat(name,color,pattern=None):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.82
    if pattern:
        im=bpy.data.images.new(name+'_packed',width=128,height=128);px=[]
        for y in range(128):
            for x in range(128):
                if pattern=='wood':v=.91+.06*math.sin(x*.45+math.sin(y*.08))+.03*math.sin(x*2.2+y*.02)
                else:v=.84+.08*(math.sin(x*math.pi/4)**2+math.sin(y*math.pi/4)**2)
                px.extend([min(1,c*v) for c in color]+[1])
        im.pixels.foreach_set(px);im.pack();tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return m
WOOD=mat('old_warm_wood',(.30,.18,.09),'wood');DARK=mat('wood_endgrain',(.16,.09,.045),'wood')
BAMBOO=mat('bamboo_weave',(.46,.36,.17),'weave');RIM=mat('bamboo_rim',(.35,.25,.11),'wood')
HEMP=mat('hemp_rope',(.62,.52,.34),'weave');CLOTH=mat('sage_hemp',(.29,.35,.20),'weave')
PAPER=mat('warm_paper',(.81,.69,.43));BRONZE=mat('aged_bronze',(.25,.22,.10));LEATHER=mat('brown_leather',(.21,.10,.05),'weave')
LAMP=mat('warm_lamp_paper',(.81,.69,.43))
lamp_bs=LAMP.node_tree.nodes.get('Principled BSDF');lamp_bs.inputs['Emission Color'].default_value=(.9,.55,.15,1);lamp_bs.inputs['Emission Strength'].default_value=.45

def box(name,loc,size,material,bevel=.007):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
    if bevel:
        m=o.modifiers.new('worn_edges','BEVEL');m.width=min(bevel,min(size)*.22);m.segments=2;bpy.ops.object.modifier_apply(modifier=m.name)
    return o
def rod(name,a,b,r,material,n=10):
    a,b=Vector(a),Vector(b);v=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(material)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o
def torus(name,loc,r,t,material,scale=(1,1,1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=t,major_segments=32,minor_segments=6,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o
def line(name,points,r,material):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=r;cu.bevel_resolution=1
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,v in zip(sp.points,points):p.co=(*v,1)
    o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.data.materials.append(material)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return o
def panel(name,verts,material,thick=.006):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[tuple(range(len(verts)))]);mesh.update();o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.data.materials.append(material)
    bpy.context.view_layer.objects.active=o;o.select_set(True);m=o.modifiers.new('cloth_thickness','SOLIDIFY');m.thickness=thick;bpy.ops.object.modifier_apply(modifier=m.name);o.select_set(False);return o
groups={}
def begin():return set(bpy.data.objects)
def bounds(obs):
    bpy.context.view_layer.update();p=[o.matrix_world@Vector(v) for o in obs for v in o.bound_box]
    return [max(v[i] for v in p)-min(v[i] for v in p) for i in range(3)]
def end(id,before):
    obs=[o for o in bpy.data.objects if o not in before];bpy.context.view_layer.update()
    floor=min((o.matrix_world@Vector(v)).z for o in obs for v in o.bound_box)
    for o in obs:o.location.z-=floor
    col=bpy.data.collections.new(id);scene.collection.children.link(col)
    for o in obs:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    groups[id]=obs

# C01: open oval basket. Closed shell has an inner wall and a woven bottom.
s=begin();n=32;verts=[]
for rx,ry,z in [(.19,.115,0),(.23,.14,.60),(.217,.127,.60),(.177,.102,.025)]:
    verts.extend([(rx*math.cos(i*math.tau/n),ry*math.sin(i*math.tau/n),z) for i in range(n)])
faces=[]
for a,b in [(0,1),(1,2),(2,3)]:
    for i in range(n):j=(i+1)%n;faces.append((a*n+i,a*n+j,b*n+j,b*n+i))
faces.extend([tuple(range(n-1,-1,-1)),tuple(range(3*n,4*n))])
me=bpy.data.meshes.new('basket_shell');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('basket_shell',me);scene.collection.objects.link(o);o.data.materials.append(BAMBOO)
for z in [.05,.30,.59]:
    rx=.19+.04*z/.60;ry=.115+.025*z/.60
    torus('bamboo_binding',(0,0,z),rx+.002,.009,RIM,(1,ry/rx,1))
for i in range(24):
    a=i*math.tau/24;rod('vertical_weave',(.19*math.cos(a),.115*math.sin(a),.02),(.23*math.cos(a),.14*math.sin(a),.59),.0045,RIM,6)
for x in [-.11,.11]:
    line('hemp_shoulder_strap',[(x,.13,.54),(x,.21,.47),(x,.23,.28),(x,.16,.08)],.018,HEMP)
end('C01',s)

s=begin()
for i in range(4):box('table_plank',(0,-.24+i*.16,.635),(1.15,.155,.05),WOOD)
for x in [-.49,.49]:
    for y in [-.245,.245]:box('table_leg',(x,y,.31),(.075,.075,.62),DARK)
    box('side_stretcher',(x,0,.18),(.045,.52,.045),WOOD)
for y in [-.245,.245]:
    box('apron',(0,y,.565),(1.02,.045,.09),WOOD)
    box('long_stretcher',(0,y,.18),(1.02,.045,.045),WOOD)
end('C02',s)

s=begin()
box('casket_body',(0,0,.112),(.47,.29,.224),BAMBOO)
box('casket_lid',(0,0,.255),(.48,.30,.05),BAMBOO)
for z in [.025,.213,.272]:
    for y in [-.145,.145]:box('horizontal_rim',(0,y,z),(.48,.018,.018),RIM)
    for x in [-.23,.23]:box('side_rim',(x,0,z),(.018,.29,.018),RIM)
for x in [-.228,.228]:
    for y in [-.142,.142]:box('corner_post',(x,y,.12),(.025,.025,.22),RIM)
for x in [-.15,.15]:rod('rear_hinge',(x-.026,.151,.232),(x+.026,.151,.232),.010,BRONZE,10)
o=torus('front_clasp',(0,-.16,.215),.018,.005,HEMP);o.rotation_euler.x=math.pi/2
end('C03',s)

s=begin()
body=box('folded_herb_packet',(0,0,.072),(.34,.26,.144),CLOTH,.028)
panel('front_fold',[(-.17,-.127,.12),(.17,-.127,.12),(0,-.142,.045)],CLOTH)
panel('rear_fold',[(-.17,.127,.12),(0,.142,.045),(.17,.127,.12)],CLOTH)
line('crossed_twine_x',[(-.172,0,.045),(-.17,0,.145),(0,0,.152),(.17,0,.145),(.172,0,.045)],.004,HEMP)
line('crossed_twine_y',[(0,-.132,.04),(0,-.132,.14),(0,0,.155),(0,.132,.14),(0,.132,.04)],.004,HEMP)
torus('twine_knot',(0,0,.158),.013,.005,HEMP)
tag=box('plain_herb_tag',(.035,-.133,.093),(.045,.008,.065),WOOD,.003);tag.rotation_euler.y=-.2
end('C04',s)

# Second batch definitions require C05-C08 reviewed references.
if opt.batch==2:
    s=begin()
    box('commission_box',(0,0,.105),(.38,.27,.21),WOOD)
    box('commission_lid',(0,0,.23),(.40,.29,.04),DARK)
    box('paper_seal_front',(0,-.139,.17),(.055,.006,.15),PAPER,.001)
    box('paper_seal_top',(0,-.02,.252),(.055,.25,.004),PAPER,.0005)
    o=torus('bronze_seal',(0,-.144,.15),.018,.005,BRONZE);o.rotation_euler.x=math.pi/2
    end('C05',s)
    s=begin()
    for i in range(2):box('bench_seat',(0,-.085+i*.17,.425),(.80,.165,.05),WOOD)
    for x in [-.31,.31]:
        for y in [-.11,.11]:box('bench_leg',(x,y,.20),(.065,.065,.40),DARK)
        box('bench_stretcher',(x,0,.12),(.045,.28,.04),WOOD)
    box('bench_long_stretcher',(0,0,.17),(.65,.04,.045),WOOD)
    end('C06',s)
    s=begin()
    box('lamp_foot',(0,0,.025),(.27,.27,.05),WOOD)
    box('paper_lamp',(0,0,.245),(.23,.23,.36),LAMP)
    for x in [-.123,.123]:
        for y in [-.123,.123]:rod('lamp_corner',(x,y,.055),(x,y,.46),.010,RIM,8)
    for z in [.065,.445]:
        for x in [-.123,.123]:rod('lamp_frame_x',(x,-.123,z),(x,.123,z),.01,RIM,8)
        for y in [-.123,.123]:rod('lamp_frame_y',(-.123,y,z),(.123,y,z),.01,RIM,8)
    box('lamp_cap',(0,0,.47),(.28,.28,.025),DARK)
    o=torus('carry_handle',(0,0,.53),.05,.007,BRONZE);o.rotation_euler.x=math.pi/2
    end('C07',s)
    s=begin()
    box('journal_wood_tray',(0,0,.018),(.38,.29,.036),WOOD)
    for x in [-.185,.185]:box('tray_edge',(x,0,.045),(.012,.29,.05),DARK)
    box('journal_pages',(0,0,.057),(.30,.22,.04),PAPER)
    for z in [.034,.080]:box('journal_cover',(0,0,z),(.32,.24,.008),LEATHER,.002)
    box('closure_strap',(0,0,.088),(.045,.27,.008),LEATHER,.001)
    for x in [-.024,.024]:box('buckle_side',(x,-.07,.097),(.006,.045,.008),BRONZE,.001)
    for y in [-.09,-.05]:box('buckle_cross',(0,y,.097),(.05,.006,.008),BRONZE,.001)
    end('C08',s)

report={'author':'Eli-0731 / Codex','batch':opt.batch,'blender':bpy.app.version_string,'units':'meters','axes':'Blender Z-up / front -Y; GLB Y-up / front +Z','reference_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in REF.glob('C*-three-view.png')},'assets':[]}
for id,obs in groups.items():
    errs=[]
    for o in obs:
        if not o.data.uv_layers:errs.append(o.name+': missing UV')
        if any(p.area<1e-10 for p in o.data.polygons):errs.append(o.name+': degenerate face')
        if any(not math.isfinite(c) for v in o.data.vertices for c in v.co):errs.append(o.name+': nonfinite coordinate')
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/f'{id}.glb'),export_format='GLB',use_selection=True,export_apply=True)
    report['assets'].append({'id':id,'dimensions_xyz':bounds(obs),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in obs),'meshes':len(obs),'errors':errs,'lod_plan':'one prototype LOD; future 50% simplification of bindings at 8m, cull small props at 20m; not yet implemented','collision':'simple box main silhouette; basket capsule; no collisions on cords or paper'})
assert not any(a['errors'] for a in report['assets']),report

ground=box('preview_floor',(0,0,-.035),(3,4,.07),mat('warm_gray_floor',(.30,.33,.29)),0)
bpy.ops.object.light_add(type='AREA',location=(3,-4,5));bpy.context.object.data.energy=600;bpy.context.object.data.size=4
bpy.ops.object.light_add(type='AREA',location=(-3,1,3));bpy.context.object.data.energy=300;bpy.context.object.data.size=3
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';scene.camera=camera
def shot(name,target,eye,scale):
    camera.location=eye;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(PRE/name);bpy.ops.render.render(write_still=True)
for id,obs in groups.items():
    for key,objs in groups.items():
        for o in objs:o.hide_render=key!=id
    size=bounds(obs);h=size[2];shot(f'{id}-close.png',(0,0,h*.48),(2,-3,2),max(size)*2.2)
placements={'C01':(-.91,.48,0),'C02':(0,.46,0),'C03':(-.31,.45,.66),'C04':(.30,.40,.66),'C05':(.85,.52,0),'C06':(-.43,-.89,0),'C07':(.84,-.53,0),'C08':(-.43,-.89,.45)}
for id,obs in groups.items():
    for o in obs:o.hide_render=False;o.location+=Vector(placements[id])
shot('return-corner.png',(0,0,.35),(4,-6,4.2),4.8)
# A scale guide rendered as a neutral ruler, not an additional asset or a character.
scaleObjects=begin()
scaleMat=mat('scale_guide',(.68,.60,.39))
rod('1.7m_scale',(-1.30,1.36,0),(-1.30,1.36,1.7),.012,scaleMat)
for z in [0,.5,1,1.5,1.7]:rod('scale_tick',(-1.35,1.36,z),(-1.25,1.36,z),.007,scaleMat)
shot('scale-3x4m.png',(0,0,.5),(4,-6,4.2),5.3)
for o in set(bpy.data.objects)-scaleObjects:o.hide_render=True
if opt.batch==2:
    lights=[o for o in scene.objects if o.type=='LIGHT'];energies=[o.data.energy for o in lights]
    for light in lights:light.data.energy*=.20
    bpy.ops.object.light_add(type='POINT',location=(.84,-.53,.35));glow=bpy.context.object;glow.name='preview_lantern_glow';glow.data.energy=12;glow.data.color=(1,.58,.22);glow.data.shadow_soft_size=.20
    shot('return-corner-dusk.png',(0,0,.35),(4,-6,4.2),4.8)
    bpy.data.objects.remove(glow,do_unlink=True)
    for light,energy in zip(lights,energies):light.data.energy=energy
# Preserve the reviewable 3x4m assembly in the editable mother file.
# GLBs above were exported at local ground origins before this placement.
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).parent/f'Qingxi_Return_C_batch{opt.batch}.blend'))
report['corner_footprint_m']=[3,4];report['placements_xyz']=placements
for a in report['assets']:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(OUT/f"{a['id']}.glb"));obs=[o for o in scene.objects if o.type=='MESH'];a['roundtrip_dimensions_xyz']=bounds(obs)
    a['roundtrip_pass']=all(abs(x-y)<.002 for x,y in zip(a['dimensions_xyz'],a['roundtrip_dimensions_xyz'])) and all(o.data.uv_layers for o in obs)
    assert a['roundtrip_pass'],a
(OUT/f'batch{opt.batch}-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('RETURN_C_QA_PASS',COUNT,'independent assets and clean roundtrips')
