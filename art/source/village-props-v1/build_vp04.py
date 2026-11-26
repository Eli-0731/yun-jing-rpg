"""VP04 茶棚重建：獨立瓦圖與 UV、灰模、遊戲匯出。"""
from pathlib import Path
import bpy
import json
import math
from mathutils import Vector

ROOT=Path.cwd()
FOLDER=ROOT/'art/exports/village-props-v1/VP04'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
objects=[]

def material(name,color,rough=0.88,texture=None):
    m=bpy.data.materials.new(name)
    b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Roughness'].default_value=rough
    if texture:
        t=m.node_tree.nodes.new('ShaderNodeTexImage')
        t.image=bpy.data.images.load(str(FOLDER/texture))
        t.image.pack()
        m.node_tree.links.new(t.outputs['Color'],b.inputs['Base Color'])
    return m

wood=material('VP04_OldWood',(.19,.135,.089),texture='VP04_Wood_Albedo.png')
wood_light=material('VP04_WornWood',(.29,.215,.15),texture='VP04_WoodLight_Albedo.png')
wood_dark=material('VP04_WetWood',(.105,.095,.08))
stone=material('VP04_ClayStone',(.32,.31,.28))
clay=material('VP04_ClayPot',(.22,.195,.16))
cloth=material('VP04_OldCloth',(.52,.49,.42))
rope_mat=material('VP04_OldRope',(.31,.27,.20))
tile=material('VP04_OwnTile',(.27,.31,.33),texture='VP04_Tile_Albedo.png')

def collect(o,name,mat):
    o.name=name
    if o.type=='MESH' and len(o.data.uv_layers)==0:
        uv=o.data.uv_layers.new(name='UV0')
        coords=[v.co for v in o.data.vertices]
        for poly in o.data.polygons:
            normal=poly.normal
            axis=max(range(3),key=lambda k:abs(normal[k]))
            axes=[k for k in range(3) if k!=axis]
            bounds=[(min(v[k] for v in coords),max(v[k] for v in coords)) for k in axes]
            for li in poly.loop_indices:
                p=coords[o.data.loops[li].vertex_index]
                uv.data[li].uv=tuple((p[k]-lo)/max(hi-lo,.001) for k,(lo,hi) in zip(axes,bounds))
    o.data.materials.clear()
    o.data.materials.append(mat)
    objects.append(o)
    return o

def log(name,a,b,r,mat,segments=8,seed=0):
    a,b=Vector(a),Vector(b)
    axis=(b-a).normalized()
    side=axis.cross(Vector((0,1,0)))
    if side.length<.05: side=axis.cross(Vector((1,0,0)))
    side.normalize()
    other=axis.cross(side).normalized()
    verts=[]
    for k in range(4):
        t=k/3
        p=a.lerp(b,t)+side*(.015*math.sin(seed+t*4))
        for j in range(segments):
            theta=2*math.pi*j/segments
            rad=r*(1+.09*math.sin(j*2.7+seed+k*1.3))
            if k==0 and p.z<.5: rad*=1.04
            verts.append(tuple(p+rad*(side*math.cos(theta)+other*math.sin(theta))))
    faces=[]
    for k in range(3):
        for j in range(segments):
            n=(j+1)%segments
            faces.append((k*segments+j,k*segments+n,(k+1)*segments+n,(k+1)*segments+j))
    faces.extend((tuple(range(segments-1,-1,-1)),tuple(3*segments+j for j in range(segments))))
    mesh=bpy.data.meshes.new(name+'_Mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    scene.collection.objects.link(ob)
    return collect(ob,name,mat)

def plank(name,p,s,mat,bevel=.02):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p)
    o=bpy.context.object
    o.dimensions=s
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    modifier=o.modifiers.new('Worn_edges','BEVEL')
    modifier.width=bevel
    modifier.segments=1
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return collect(o,name,mat)

# 四根舊柱；底段水痕為獨立材質。
for xi,x in enumerate((-1.55,1.55)):
    for yi,y in enumerate((-1.22,1.22)):
        post=log(f'Post_{xi}_{yi}',(x,y,0),(x,y,2.48),.105,wood,seed=xi*5+yi*3)
        post.data.materials.append(wood_dark)
        for face in post.data.polygons:
            if face.center.z<.83: face.material_index=1
        for ring_z in (1.98,2.28):
            bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=4,
                location=(x,y,ring_z),major_radius=.116,minor_radius=.016)
            collect(bpy.context.object,f'RopeJoint_{xi}_{yi}_{ring_z}',rope_mat)
for y in (-1.22,1.22):
    log('EaveBeam_'+str(y),(-1.7,y,2.40),(1.7,y,2.40),.105,wood_light)
for x in (-1.55,1.55):
    log('CrossBeam_'+str(x),(x,-1.42,2.43),(x,1.42,2.43),.09,wood)
    for y in (-1.22,1.22):
        log('KneeBrace_'+str(x)+'_'+str(y),(x,y,1.75),(x*.72,y,2.42),.06,wood)
log('RidgeBeam',(0,-1.50,3.0),(0,1.50,3.0),.095,wood_dark)

# 自己的瓦面 UV，兩片坡面各自使用整張 VP04_Tile_Albedo；沒有 RK03 UV。
def roof(side):
    verts=[]
    uv=[]
    for ky in range(9):
        y=-1.50+3.00*ky/8
        for kx in range(17):
            t=kx/16
            x=side*(.01+1.77*t)
            z=3.0-.70*t+.08*t**8
            verts.append((x,y,z))
            uv.append((ky/8,t))
    faces=[]
    for ky in range(8):
        for kx in range(16):
            a=ky*17+kx
            faces.extend(((a,a+17,a+18),(a,a+18,a+1)) if side<0 else ((a,a+18,a+17),(a,a+1,a+18)))
    mesh=bpy.data.meshes.new('VP04_RoofMesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    layer=mesh.uv_layers.new(name='VP04_Tile_UV')
    for p in mesh.polygons:
        for li in p.loop_indices:
            layer.data[li].uv=uv[mesh.loops[li].vertex_index]
    ob=bpy.data.objects.new('Roof_'+('L' if side<0 else 'R'),mesh)
    scene.collection.objects.link(ob)
    collect(ob,ob.name,tile)
roof(-1)
roof(1)
for y in (-1.50,1.50):
    log('RoofEdge_'+str(y),(-1.80,y,2.34),(0,y,3.01),.075,wood_dark)
    log('RoofEdgeR_'+str(y),(0,y,3.01),(1.80,y,2.34),.075,wood_dark)

# 桌與兩條凳：板材有分縫，桌緣受手磨亮。
for i,x in enumerate((-.58,-.19,.20,.59)):
    plank(f'TablePlank_{i}',(x,0,.80),(.38,1.08,.07),wood_light)
for x in (-.57,.57):
    for y in (-.42,.42):
        log(f'TableLeg_{x}_{y}',(x,y,.08),(x,y,.76),.045,wood)
for si,x in enumerate((-1.05,1.05)):
    for i,y in enumerate((-.40,-.12,.16,.44)):
        plank(f'Bench_{si}_Plank_{i}',(x,y,.43),(.32,.27,.055),wood_light)
    for y in (-.38,.38):
        log(f'Bench_{si}_Leg_{y}',(x,y,.06),(x,y,.42),.05,wood)

# 小爐、茶壺和空白舊布；不放字樣。
bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.27,depth=.58,location=(1.02,.37,.33))
collect(bpy.context.object,'ClayStove',stone)
bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.17,depth=.03,location=(1.02,.37,.63))
collect(bpy.context.object,'StoveAsh',wood_dark)
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=7,radius=.15,location=(.05,0,.95))
collect(bpy.context.object,'TeapotBody',clay)
log('TeapotSpout',(.16,0,.99),(.27,0,1.06),.032,clay,6)
bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=5,location=(-.10,0,1.02),major_radius=.075,minor_radius=.018)
collect(bpy.context.object,'TeapotHandle',clay)
verts=[(-.92,-1.43,2.26),(.45,-1.43,2.26),(.45,-1.43,1.53),(.08,-1.43,1.49),(-.46,-1.43,1.57),(-.92,-1.43,1.51)]
mesh=bpy.data.meshes.new('BlankClothMesh')
mesh.from_pydata(verts,[],[(0,1,2),(0,2,3),(0,3,4),(0,4,5)])
mesh.update()
ob=bpy.data.objects.new('BlankCloth',mesh)
scene.collection.objects.link(ob)
collect(ob,ob.name,cloth)
log('ClothRod',(-.98,-1.43,2.27),(.50,-1.43,2.27),.024,wood,6)

FOLDER.mkdir(parents=True,exist_ok=True)
gray=bpy.data.materials.new('VP04_Gray')
gray.diffuse_color=(.5,.5,.5,1)
original=[(o,list(o.data.materials)) for o in objects]
for o,_ in original:
    o.data.materials.clear()
    o.data.materials.append(gray)
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/'VP04_gray.blend'))
for o,mats in original:
    o.data.materials.clear()
    for m in mats: o.data.materials.append(m)
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/'VP04.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in objects: o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.gltf(filepath=str(FOLDER/'VP04.glb'),export_format='GLB',use_selection=True)
bpy.ops.export_scene.fbx(filepath=str(FOLDER/'VP04.fbx'),use_selection=True,axis_forward='-Z',axis_up='Y',use_triangles=True,add_leaf_bones=False,bake_anim=False)
tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects)
info={'id':'VP04','name_zh':'茶棚','units':'m',
      'reference':'art/references/village-props-v1/VP04/three-view.png',
      'source_note':'原規格提到的 v009 幾何未在目前工作樹或可見 Git 物件找到，故依三視圖重建',
      'tile_material':'VP04_Tile_Albedo.png，VP04_Tile_UV 獨立；無 RK03 貼圖或 UV',
      'lods':[{'name':'LOD0','triangles':tri,'materials':len(set(m.name for o in objects for m in o.data.materials)),
               'textures':[{'name':'VP04_Tile_Albedo.png','resolution':[1024,1024]},
                           {'name':'VP04_Wood_Albedo.png','resolution':[1024,1024]},
                           {'name':'VP04_WoodLight_Albedo.png','resolution':[1024,1024]}]}],
      'dimensions_m':[3.6,3.0,3.08],'unity_import':'未驗證'}
(FOLDER/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print('VP04_DONE',len(objects),tri)
