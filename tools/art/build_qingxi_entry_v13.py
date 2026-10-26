"""Original Qingxi novice, gate, basket and road dressing.

Three-view source images are checked before any new mesh is constructed.
Blender preview only: no Unity or gameplay claim is made by this script.
"""
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / 'art/references'
for name in ('qingxi-novice-cultivator-v1', 'qingxi-village-gate-v1', 'qingxi-herb-basket-v1'):
    path = REF / name / 'three-view.png'
    if not path.is_file():
        raise FileNotFoundError(f'AI three-view required before modeling: {path}')

SOURCE = ROOT / 'art/source/qingxi-entry-assets-v13.blend'
EXPORT = ROOT / 'art/exports/qingxi-entry-assets-v13'
PREVIEW = ROOT / 'art/previews/qingxi-entry-assets-v13'
for p in (EXPORT, PREVIEW): p.mkdir(parents=True, exist_ok=True)
random.seed(131026)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

def material(name, rgb, rough=.78, metallic=0):
    m=bpy.data.materials.new('M_QX13_'+name)
    m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metallic
    return m

M={
 'robe':material('RobeDeepTeal',(.058,.17,.175)), 'robe_light':material('RobeLightTeal',(.19,.38,.35)),
 'ivory':material('Ivory',(.82,.75,.61)), 'skin':material('Skin',(.72,.52,.41),.65),
 'hair':material('Hair',(.034,.029,.027),.46), 'hair_high':material('HairHighlight',(.075,.061,.052),.43),
 'jade':material('Jade',(.16,.62,.52),.24), 'bronze':material('Bronze',(.44,.28,.11),.42,.62),
 'wood':material('DarkTimber',(.19,.105,.055)), 'wood_edge':material('TimberEdge',(.34,.18,.085)),
 'tile':material('RoofTeal',(.12,.27,.27)), 'tile_edge':material('RoofEdge',(.075,.15,.15)),
 'stone':material('Limestone',(.42,.40,.35)), 'stone_dark':material('StoneJoint',(.26,.25,.22)),
 'straw':material('BambooStraw',(.52,.36,.17)), 'straw_light':material('BambooHighlight',(.72,.53,.28)),
 'herb':material('HarvestHerb',(.20,.34,.14)), 'flower':material('Wildflower',(.84,.67,.39)),
 'earth':material('Earth',(.37,.25,.15)), 'moss':material('Moss',(.20,.28,.10)),
}

def group(name):
    c=bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c
CHAR=group('ASSET_QX13_NoviceCultivator')
GATE=group('ASSET_QX13_VillageGate')
BASKET=group('ASSET_QX13_HerbBasket')
DRESS=group('ASSET_QX13_RoadDressing')

def link(ob,c,name,mat):
    ob.name=name
    for old in list(ob.users_collection): old.objects.unlink(ob)
    c.objects.link(ob)
    ob.data.materials.clear()
    ob.data.materials.append(M[mat])
    return ob

def cube(c,name,loc,dim,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=link(bpy.context.object,c,name,mat)
    o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('SoftEdges','BEVEL'); mod.width=bevel; mod.segments=2
        o.modifiers.new('WeightedNormals','WEIGHTED_NORMAL')
    return o

def uvball(c,name,loc,dim,mat,segments=16,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    o=link(bpy.context.object,c,name,mat); o.scale=dim
    return o

def beam(c,name,p0,p1,radius,mat,vertices=10):
    a,b=Vector(p0),Vector(p1); d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=d.length,location=(a+b)/2)
    o=link(bpy.context.object,c,name,mat)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    return o

def tube(c,name,points,radius,mat,bevel_resolution=2):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=12
    data.bevel_depth=radius;data.bevel_resolution=bevel_resolution
    sp=data.splines.new('POLY');sp.points.add(len(points)-1)
    for q,p in zip(sp.points,points):q.co=(*p,1)
    o=bpy.data.objects.new(name,data);c.objects.link(o);o.data.materials.append(M[mat]);return o

def mesh(c,name,verts,faces,mat):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);c.objects.link(o);me.materials.append(M[mat]);return o

# Character: 1.75 m reference pose. The silhouette and costume are an original
# interpretation of the saved sheet, not a copy of a supplied short-drama face.
uvball(CHAR,'SK_QX13_Face',(0,-.01,1.57),(.105,.082,.14),'skin',24,16)
uvball(CHAR,'SK_QX13_HairCap',(0,.032,1.665),(.115,.092,.095),'hair',24,12)
for side in (-1,1):
    uvball(CHAR,f'SK_QX13_Eye_{side}',(.045*side,-.082,1.585),(.017,.005,.011),'hair',12,6)
    tube(CHAR,f'SK_QX13_TempleHair_{side}',[(.088*side,.014,1.66),(.105*side,.023,1.48),(.091*side,.030,1.24)],.018,'hair')
    tube(CHAR,f'SK_QX13_HairPin_{side}',[(.07*side,-.005,1.73),(.12*side,.0,1.69)],.006,'jade')
for i in range(14):
    x=(i-6.5)*.012
    tube(CHAR,f'SK_QX13_BackHair_{i:02}',[(x,.085,1.68),(x*1.6,.094,1.38),(x*1.9,.10,1.06)],.009,'hair' if i%3 else 'hair_high',1)

uvball(CHAR,'SK_QX13_Torso',(0,.015,1.25),(.17,.10,.25),'robe',20,10)
cube(CHAR,'SK_QX13_InnerCollar',(0,-.08,1.41),(.145,.025,.16),'ivory',.004)
for side in (-1,1):
    beam(CHAR,f'SK_QX13_CollarLap_{side}',(.018*side,-.113,1.49),(.13*side,-.105,1.31),.013,'robe_light')
    for j in range(1):
        z=1.37-j*.045
        beam(CHAR,f'SK_QX13_BeltCord_{side}_{j}',(.10*side,-.112,z),(.015*side,-.122,z-.01),.006,'ivory')
    beam(CHAR,f'SK_QX13_UpperArm_{side}',(.14*side,.0,1.38),(.31*side,.0,1.21),.055,'robe',12)
    beam(CHAR,f'SK_QX13_Forearm_{side}',(.31*side,.0,1.21),(.43*side,-.015,1.07),.045,'robe_light',12)
    uvball(CHAR,f'SK_QX13_Hand_{side}',(.44*side,-.017,1.045),(.027,.023,.06),'skin',12,8)
    # Wide sleeve is a tapered cloth mesh, kept separate for later cloth/skin work.
    s=side
    mesh(CHAR,f'SK_QX13_Sleeve_{side}',[(s*.27,-.065,1.24),(s*.34,.06,1.24),(s*.47,.11,1.01),(s*.49,-.11,1.01)],[(0,1,2,3)],'robe')
    beam(CHAR,f'SK_QX13_Leg_{side}',(.075*side,.01,.88),(.085*side,.0,.18),.054,'robe',12)
    cube(CHAR,f'SK_QX13_Shoe_{side}',(.085*side,-.04,.075),(.11,.23,.09),'hair',.02)

# Layered skirt panels with different hem heights and modest asymmetry.
for k,(top,bot,mat) in enumerate(((.17,.38,'robe'),(.13,.32,'robe_light'),(.10,.24,'ivory'))):
    ztop=1.13-k*.018; zbot=.14+k*.02
    yoff=.025-k*.012
    mesh(CHAR,f'SK_QX13_SkirtLayer_{k}',[(-top,-.05-k*.008,ztop),(top,-.05-k*.008,ztop),(-bot,-.13-k*.01,zbot),(bot,-.13-k*.01,zbot),(-top,.10+yoff,ztop),(top,.10+yoff,ztop),(-bot,.18+yoff,zbot),(bot,.18+yoff,zbot)],[(0,2,3,1),(4,5,7,6),(0,4,6,2),(1,3,7,5)],mat)
cube(CHAR,'SK_QX13_WaistSash',(0,-.01,1.115),(.33,.23,.052),'ivory',.01)
uvball(CHAR,'SK_QX13_JadeBuckle',(0,-.135,1.115),(.034,.011,.032),'jade',12,8)
for side in (-1,1):
    tube(CHAR,f'SK_QX13_WaistTassel_{side}',[(.038*side,-.121,1.1),(.042*side,-.145,.91),(.049*side,-.15,.74)],.006,'bronze')

# Gate: 4 m clear span, 3.5 m tall; detailed tiled roof and bracket rhythm.
for side in (-1,1):
    x=2.13*side
    cube(GATE,f'SM_QX13_GateFoundation_{side}',(x,0,.18),(.60,.67,.36),'stone',.045)
    cube(GATE,f'SM_QX13_GatePost_{side}',(x,0,1.72),(.30,.31,2.82),'wood',.018)
    for z in (.48,1.12,1.90,2.72):
        cube(GATE,f'SM_QX13_PostBand_{side}_{z:.2f}',(x,0,z),(.34,.34,.045),'wood_edge',.006)
    for j in range(4):
        y=(j-1.5)*.12
        beam(GATE,f'SM_QX13_Bracket_{side}_{j}',(x,y,3.05),(x-side*.38,y,3.29),.052,'wood_edge',8)
cube(GATE,'SM_QX13_Header',(0,0,3.08),(4.76,.40,.27),'wood',.023)
cube(GATE,'SM_QX13_Signboard',(0,-.24,2.84),(1.68,.13,.30),'wood_edge',.02)
for side in (-1,1):
    for j in range(5):
        y=(j-2)*.075
        cube(GATE,f'SM_QX13_SignCarving_{side}_{j}',(side*(.26+j*.105),-.313,2.84),(.075,.008,.016),'bronze',.003)
# Roof shape as two pitched, slightly raised eaves and actual tile rows.
for side in (-1,1):
    s=side
    mesh(GATE,f'SM_QX13_RoofPlane_{side}',[(-2.60,0,3.61),(2.60,0,3.61),(-2.83,s*.70,3.31),(2.83,s*.70,3.31)],[(0,1,3,2)],'tile_edge')
    for row in range(5):
        y=s*(.085+row*.135);z=3.61-row*.067
        for col in range(28):
            x=-2.68+col*.198
            o=cube(GATE,f'SM_QX13_RoofTile_{side}_{row:02}_{col:02}',(x,y,z-.015),(.17,.155,.035),'tile' if (col+row)%4 else 'tile_edge',.008)
            o.rotation_euler[0]=s*.38
    for x in (-2.76,2.76):
        tube(GATE,f'SM_QX13_EaveTip_{side}_{x:+.1f}',[(x,s*.63,3.32),(x*1.03,s*.72,3.39),(x*1.04,s*.75,3.49)],.037,'tile_edge')
tube(GATE,'SM_QX13_Ridge',[(-2.65,0,3.64),(2.65,0,3.64)],.055,'tile_edge')

# Basket: interlaced ribs/rings, open interior and hand grip.
for level in range(13):
    z=.075+level*.022
    rx=.245-level*.0034; ry=.175-level*.0021
    pts=[(rx*math.cos(t*2*math.pi/64),ry*math.sin(t*2*math.pi/64),z+.004*math.sin(t*.8+level)) for t in range(65)]
    tube(BASKET,f'SM_QX13_WovenRing_{level:02}',pts,.006,'straw_light' if level%2 else 'straw',1)
for j in range(32):
    a=j*2*math.pi/32
    pts=[]
    for level in range(13):
        z=.075+level*.022;rx=.245-level*.0034;ry=.175-level*.0021
        aa=a+.018*math.sin(level*math.pi)
        pts.append((rx*math.cos(aa),ry*math.sin(aa),z))
    tube(BASKET,f'SM_QX13_WeaveRib_{j:02}',pts,.0045,'straw' if j%2 else 'straw_light',1)
cube(BASKET,'SM_QX13_BasketBottom',(0,0,.067),(.45,.31,.025),'straw',.01)
for side in (1,):
    tube(BASKET,f'SM_QX13_Handle_{side}',[(side*.205,0,.22),(side*.26,0,.37),(side*.21,0,.47),(0,0,.51),(-side*.21,0,.47),(-side*.26,0,.37),(-side*.205,0,.22)],.012,'straw_light')
for j in range(9):
    a=j*2.399; r=.045+.016*(j%3);x=r*math.cos(a);y=r*math.sin(a)
    beam(BASKET,f'SM_QX13_HerbStem_{j}',(x,y,.17),(x+math.sin(a)*.02,y,.34+.01*(j%3)),.0035,'herb',6)
    for k in range(2):uvball(BASKET,f'SM_QX13_HerbLeaf_{j}_{k}',(x+(-1)**k*.012,y,.28+k*.03),(.028,.011,.007),'herb',10,6)

# Road dressing is a reusable scatter set. The v12 path mesh itself is left
# intact so collaborators can work on seams independently.
for j in range(34):
    x=(j%9)*.29-1.15;y=(j//9)*.42-.55
    rr=.035+.025*((j*7)%5)/4
    uvball(DRESS,f'SM_QX13_Gravel_{j:02}',(x,y,rr*.32),(rr,rr*.7,rr*.38),'stone' if j%3 else 'stone_dark',10,6)
for j in range(20):
    x=(j%5)*.28-.55;y=(j//5)*.31-.42
    h=.12+.09*((j*3)%5)/4
    for k in range(4):
        a=k*math.pi/2+j*.7
        mesh(DRESS,f'SM_QX13_Reed_{j:02}_{k}',[(x,y,.03),(x+.017*math.cos(a),y+.017*math.sin(a),h*.45),(x+.05*math.cos(a),y+.05*math.sin(a),h)],[(0,1,2)],'herb')
    if j%3==0:
        beam(DRESS,f'SM_QX13_FlowerStem_{j}',(x,y,.03),(x+.02,y,h+.05),.002,'herb',5)
        uvball(DRESS,f'SM_QX13_Flower_{j}',(x+.02,y,h+.05),(.013,.013,.008),'flower',8,5)

# Apply export transforms and seed UVs before QA. Texture artists can re-unwrap.
for c in (CHAR,GATE,BASKET,DRESS):
    for o in list(c.objects):
        if o.type=='CURVE':
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True)
            bpy.context.view_layer.objects.active=o
            bpy.ops.object.convert(target='MESH')
for c in (CHAR,GATE,BASKET,DRESS):
    for o in c.objects:
        if o.type!='MESH':continue
        sx,sy,sz=o.scale
        if any(abs(v-1)>1e-6 for v in (sx,sy,sz)):
            o.data.transform(Matrix.Diagonal((sx,sy,sz,1)))
            o.scale=(1,1,1)
        if not o.data.uv_layers:
            uv=o.data.uv_layers.new(name='UVMap')
            for poly in o.data.polygons:
                axes=sorted(range(3),key=lambda axis:abs(poly.normal[axis]))[:2]
                for li in poly.loop_indices:
                    co=o.data.vertices[o.data.loops[li].vertex_index].co
                    uv.data[li].uv=(co[axes[0]],co[axes[1]])

# Simple art-review renders (not gameplay screenshots).
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
world=bpy.data.worlds.new('Qingxi_Studio') if not bpy.data.worlds else bpy.data.worlds[0]
scene.world=world; world.use_nodes=True
world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.58,.68,.72,1)
world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.8
bpy.ops.object.light_add(type='AREA',location=(2,-3,6));key=bpy.context.object;key.name='RENDER_Key';key.data.energy=700;key.data.shape='DISK';key.data.size=5
bpy.ops.object.camera_add(location=(4,-7,3));camera=bpy.context.object;camera.name='RENDER_Camera';scene.camera=camera
def render(name,visible,loc,target,ortho):
    for c in (CHAR,GATE,BASKET,DRESS):
        for o in c.objects:o.hide_render=c!=visible
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=ortho
    scene.render.filepath=str(PREVIEW/(name+'.png'));bpy.ops.render.render(write_still=True)

for name,c,loc,target,scale in (
 ('novice-front',CHAR,(0,-5,1.7),(0,0,.9),2.8),
 ('novice-side',CHAR,(5,0,1.6),(0,0,.9),2.8),
 ('village-gate',GATE,(4,-8,4),(0,0,1.7),6.8),
 ('herb-basket',BASKET,(1,-1.7,1.25),(0,0,.23),.95),
 ('road-dressing',DRESS,(2,-2.4,2),(.0,0,.05),3.0)):
    render(name,c,loc,target,scale)
for c in (CHAR,GATE,BASKET,DRESS):
    for o in c.objects:o.hide_render=False

def select_group(c):
    bpy.ops.object.select_all(action='DESELECT')
    for o in c.objects:o.select_set(True)
    bpy.context.view_layer.objects.active=next(iter(c.objects))

stats={}
for slug,c in (('novice-cultivator',CHAR),('village-gate',GATE),('herb-basket',BASKET),('road-dressing',DRESS)):
    select_group(c)
    bpy.ops.export_scene.gltf(filepath=str(EXPORT/(slug+'-v13.glb')),export_format='GLB',use_selection=True,export_apply=True)
    tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in c.objects if o.type=='MESH')
    stats[slug]={'objects':len(c.objects),'triangles':tris,'glb':str((EXPORT/(slug+'-v13.glb')).relative_to(ROOT))}

SOURCE.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
(EXPORT/'build-report.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
print(json.dumps(stats,indent=2))
