"""TX02 大鐘與鐘亭；鐘與撞木各有獨立可旋轉樞軸。"""
from pathlib import Path
import bpy
import json
import math
from mathutils import Vector

ROOT=Path.cwd()
OUT=ROOT/'art/exports/mountain-city-v1/TX02'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1
meshes=[]

def mat(name,color,rough=.85,tex=None):
    m=bpy.data.materials.new(name)
    b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Roughness'].default_value=rough
    if tex:
        node=m.node_tree.nodes.new('ShaderNodeTexImage')
        node.image=bpy.data.images.load(str(OUT/tex),check_existing=True)
        node.image.pack()
        m.node_tree.links.new(node.outputs['Color'],b.inputs['Base Color'])
    return m

stone=mat('TX02_WornStone',(.45,.45,.42),tex='TX02_Stone_Albedo.png')
wood=mat('TX02_AgedWood',(.22,.17,.13),tex='TX02_Wood_Albedo.png')
rope=mat('TX02_OldRope',(.34,.28,.19))
bronze=mat('TX02_PatinaBronze',(.23,.27,.20),.68,tex='TX02_Bronze_Albedo.png')
bronze_dark=mat('TX02_BronzeEdge',(.16,.19,.16),.62)
tile=mat('TX02_DarkTile',(.25,.27,.28),tex='TX02_Tile_Albedo.png')

def register(ob,name,material,projection=True):
    ob.name=name
    ob.data.materials.clear()
    ob.data.materials.append(material)
    if projection and not ob.data.uv_layers:
        uv=ob.data.uv_layers.new(name='UV0')
        coords=[v.co for v in ob.data.vertices]
        for face in ob.data.polygons:
            axis=max(range(3),key=lambda k:abs(face.normal[k]))
            axes=[k for k in range(3) if k!=axis]
            bounds=[(min(v[k] for v in coords),max(v[k] for v in coords)) for k in axes]
            for li in face.loop_indices:
                p=coords[ob.data.loops[li].vertex_index]
                uv.data[li].uv=tuple((p[k]-lo)/max(hi-lo,.001) for k,(lo,hi) in zip(axes,bounds))
    meshes.append(ob)
    return ob

def block(name,location,size,material,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    ob=bpy.context.object
    ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=ob.modifiers.new('WornEdge','BEVEL')
    mod.width=bevel
    mod.segments=1
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return register(ob,name,material)

def beam(name,a,b,r,material,segments=10):
    a,b=Vector(a),Vector(b)
    d=b-a
    mid=(a+b)/2
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=d.length,location=mid)
    ob=bpy.context.object
    ob.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return register(ob,name,material)

# 石基分塊與兩級台階，避免一塊無磨損的整體方柱。
block('Plinth_Base',(0,0,.12),(4.85,4.85,.24),stone,.055)
block('Plinth_Upper',(0,.25,.42),(4.55,4.35,.36),stone,.045)
block('Step_Outer',(0,-2.31,.15),(4.55,.40,.28),stone,.035)
block('Step_Inner',(0,-2.00,.35),(4.55,.28,.27),stone,.03)
for x in (-1.95,1.95):
    for y in (-1.95,1.95):
        block(f'PostFoot_{x}_{y}',(x,y,.72),(.43,.43,.30),stone,.035)
        beam(f'Column_{x}_{y}',(x,y,.86),(x,y,5.18),.17,wood,12)
for y in (-1.95,1.95):
    block(f'BeamX_{y}',(0,y,5.11),(4.28,.23,.25),wood,.025)
for x in (-1.95,1.95):
    block(f'BeamY_{x}',(x,0,5.11),(.23,4.28,.25),wood,.025)
block('BellCrossbeam',(0,0,4.83),(3.25,.20,.24),wood,.025)

# 四片攢尖瓦坡，檐角微翹；UV 僅用 TX02 的瓦圖。
corners=[(-2.5,-2.5),(2.5,-2.5),(2.5,2.5),(-2.5,2.5)]
for side in range(4):
    a=Vector((*corners[side],0))
    b=Vector((*corners[(side+1)%4],0))
    verts=[]
    uvs=[]
    for k in range(8):
        t=k/8
        for j in range(13):
            u=j/12
            p=(a*(1-u)+b*u)*(1-t)
            edge_z=5.22+.21*abs(2*u-1)**5
            p.z=edge_z*(1-t)+6.08*t
            verts.append(tuple(p))
            uvs.append((u,t))
    center=len(verts)
    verts.append((0,0,6.08))
    uvs.append((.5,1))
    faces=[]
    for k in range(7):
        for j in range(12):
            q=k*13+j
            faces.extend(((q,q+1,q+14),(q,q+14,q+13)))
    for j in range(12):
        faces.append((7*13+j,7*13+j+1,center))
    mesh=bpy.data.meshes.new('TX02_RoofMesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    uv=mesh.uv_layers.new(name='TX02_Tile_UV')
    for face in mesh.polygons:
        for li in face.loop_indices:
            uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
    ob=bpy.data.objects.new(f'Roof_{side}',mesh)
    scene.collection.objects.link(ob)
    register(ob,ob.name,tile,projection=False)
    beam(f'Eave_{side}',(a.x,a.y,5.43),(b.x,b.y,5.43),.07,wood,8)
for side in range(4):
    x,y=corners[side]
    beam(f'HipRidge_{side}',(0,0,6.09),(x,y,5.44),.08,wood,8)
block('RoofFinialBase',(0,0,6.14),(.34,.34,.12),bronze_dark,.025)
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.16,location=(0,0,6.32))
register(bpy.context.object,'RoofFinial',bronze_dark)

# 鐘身的外表與內壁連續，底部敞口；鐘本體原點就是上方吊環。
pivot_z=4.44
profile=[(4.29,.10),(4.18,.34),(3.97,.51),(3.63,.63),(3.18,.71),
         (2.64,.83),(2.27,.90),(2.23,.89),(2.23,.76),
         (2.65,.70),(3.25,.59),(3.88,.43),(4.18,.14)]
segments=40
verts=[]
uvs=[]
for k,(z,r) in enumerate(profile):
    for j in range(segments):
        ang=2*math.pi*j/segments
        relief=.012*math.sin(8*ang+k*.55)
        verts.append(((r+relief)*math.cos(ang),(r+relief)*math.sin(ang),z-pivot_z))
        uvs.append((j/segments,k/(len(profile)-1)))
faces=[]
for k in range(len(profile)-1):
    for j in range(segments):
        n=(j+1)%segments
        faces.append((k*segments+j,k*segments+n,(k+1)*segments+n,(k+1)*segments+j))
mesh=bpy.data.meshes.new('TX02_BellMesh')
mesh.from_pydata(verts,[],faces)
mesh.update()
uv=mesh.uv_layers.new(name='Bell_UV')
for face in mesh.polygons:
    for li in face.loop_indices:
        vi=mesh.loops[li].vertex_index
        u=uvs[vi][0]
        if vi%segments==0 and any(mesh.loops[t].vertex_index%segments==segments-1 for t in face.loop_indices):
            u=1
        uv.data[li].uv=(u,uvs[vi][1])
bell=bpy.data.objects.new('Bell',mesh)
scene.collection.objects.link(bell)
bell.location.z=pivot_z
register(bell,'Bell',bronze,projection=False)
for z,r in ((2.29,.895),(3.13,.72),(3.93,.52)):
    bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=6,
        location=(0,0,z),major_radius=r,minor_radius=.018)
    ring=register(bpy.context.object,f'BellReliefBand_{z}',bronze_dark)
    ring.parent=bell
    ring.matrix_parent_inverse=bell.matrix_world.inverted()
bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,
    location=(0,0,4.45),major_radius=.14,minor_radius=.045)
ring=register(bpy.context.object,'BellSuspensionRing',bronze_dark)
ring.parent=bell
ring.matrix_parent_inverse=bell.matrix_world.inverted()
socket=bpy.data.objects.new('Socket_Ring',None)
scene.collection.objects.link(socket)
socket.parent=bell
socket.location=(0,0,0)

# 撞木和兩根舊繩共用一個空物件樞軸，核心組可直接旋轉 Striker。
striker=bpy.data.objects.new('Striker',None)
scene.collection.objects.link(striker)
striker.location=(1.52,0,4.65)
log=beam('Striker_Log',(1.02,0,2.96),(2.15,0,2.96),.13,wood,12)
log.parent=striker
log.matrix_parent_inverse=striker.matrix_world.inverted()
for x in (1.20,1.90):
    cord=beam(f'Striker_Rope_{x}',(x,0,3.05),(x,0,4.65),.019,rope,6)
    cord.parent=striker
    cord.matrix_parent_inverse=striker.matrix_world.inverted()

OUT.mkdir(parents=True,exist_ok=True)
gray=bpy.data.materials.new('TX02_Gray')
gray.diffuse_color=(.5,.5,.5,1)
original=[(o,list(o.data.materials)) for o in meshes]
for o,_ in original:
    o.data.materials.clear()
    o.data.materials.append(gray)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'TX02_gray.blend'))
for o,mats in original:
    o.data.materials.clear()
    for m in mats: o.data.materials.append(m)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'TX02.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[striker,socket]: o.select_set(True)
bpy.context.view_layer.objects.active=bell
bpy.ops.export_scene.gltf(filepath=str(OUT/'TX02.glb'),export_format='GLB',use_selection=True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'TX02.fbx'),use_selection=True,axis_forward='-Z',axis_up='Y',use_triangles=True,add_leaf_bones=False,bake_anim=False)
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
info={'id':'TX02','name_zh':'大鐘與鐘亭','units':'m',
      'reference':'art/references/mountain-city-v1/TX02/three-view.png',
      'dimensions_m':[5,5,6.48],'bell_diameter_m':1.8,
      'pivots':{'Bell':'上方吊環 z=4.44 m','Striker':'兩根吊繩頂端 x=1.52,z=4.65 m','Socket_Ring':'Bell 子物件，局部原點'},
      'lods':[{'name':'LOD0','triangles':tris,'materials':6,
               'textures':[{'name':'TX02_Bronze_Albedo.png','resolution':[1024,1024]},
                           {'name':'TX02_Tile_Albedo.png','resolution':[1024,1024]},
                           {'name':'TX02_Wood_Albedo.png','resolution':[1024,1024]},
                           {'name':'TX02_Stone_Albedo.png','resolution':[1024,1024]}]}],
      'unity_import':'未驗證'}
(OUT/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print('TX02_DONE',len(meshes),tris)
