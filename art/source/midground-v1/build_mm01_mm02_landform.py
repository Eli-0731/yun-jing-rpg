"""依 AI 三視圖重建中景喀斯特峰：平面高度場，不使用旋轉石柱。"""
from pathlib import Path
import bpy
import json
import math
from mathutils import Vector

ROOT = Path.cwd()
OUT = ROOT / "art/exports/midground-v1"
N = 76
R = 39.0


def wave(x, y, seed):
    return (math.sin(.41*x + .19*y + seed) * math.sin(.23*y - .13*x)
            + .45*math.sin(.91*x - .38*y + seed*.4)
            + .24*math.sin(1.7*x + .63*y + seed))


def peak_height(x, y, px, py, height, wx, wy, angle, seed):
    dx, dy = x-px, y-py
    c, s = math.cos(angle), math.sin(angle)
    u, v = c*dx+s*dy, -s*dx+c*dy
    d = math.sqrt((u/wx)**2+(v/wy)**2)
    # 陡直主壁與數段不對稱的岩脊；噪聲只在岩面，不形成方形塊體。
    main = height / (1+d**7.0)
    shoulder = height*.09*math.exp(-((u-8)/16)**2-((v+4)/12)**2)
    ribs = (1+.07*math.sin(math.atan2(v,u)*5+seed+.25*d)
            +.04*math.sin(math.atan2(v,u)*9-.7*d))
    return (main+shoulder)*ribs


def make(name, peaks):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    vertices = []
    faces = []
    uv_coords = []
    for iy in range(N+1):
        gy = -R+2*R*iy/N
        for ix in range(N+1):
            gx = -R+2*R*ix/N
            x = gx*math.sqrt(1-gy*gy/(2*R*R))
            y = gy*math.sqrt(1-gx*gx/(2*R*R))
            h = max(peak_height(x,y,*p) for p in peaks)
            falloff = max(0.0, 1-(math.hypot(x,y)/R)**5)
            z = max(0, (h+wave(x,y,3.7)*min(1.8,h*.11))*falloff)
            vertices.append((x,y,z))
            uv_coords.append((ix/N,iy/N))
    for iy in range(N):
        for ix in range(N):
            a=iy*(N+1)+ix
            faces.extend(((a,a+1,a+N+2),(a,a+N+2,a+N+1)))
    # 邊界與底面封口；地形埋入場景時不露出邊界。
    boundary = (list(range(N+1))
                +[iy*(N+1)+N for iy in range(1,N+1)]
                +[N*(N+1)+ix for ix in range(N-1,-1,-1)]
                +[iy*(N+1) for iy in range(N-1,0,-1)])
    base_start=len(vertices)
    for idx in boundary:
        x,y,_=vertices[idx]
        vertices.append((x,y,-1.0))
        uv_coords.append((.5+x/(2*R),.5+y/(2*R)))
    center=len(vertices)
    vertices.append((0,0,-1.0))
    uv_coords.append((.5,.5))
    for j,idx in enumerate(boundary):
        nxt=boundary[(j+1)%len(boundary)]
        b=base_start+j
        bn=base_start+(j+1)%len(boundary)
        faces.extend(((idx,b,bn),(idx,bn,nxt),(center,bn,b)))
    mesh=bpy.data.meshes.new(name+'_LandformMesh')
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    uv=mesh.uv_layers.new(name='UV0')
    top_face_count=2*N*N
    for face in mesh.polygons:
        for li in face.loop_indices:
            vi=mesh.loops[li].vertex_index
            if face.index>=top_face_count and (face.index-top_face_count)%3<2:
                j=(face.index-top_face_count)//3
                u=j/len(boundary) if vi in (boundary[j],base_start+j) else (j+1)/len(boundary)
                uv.data[li].uv=(u,1 if vi<base_start else 0)
            else:
                uv.data[li].uv=uv_coords[vi]
    obj=bpy.data.objects.new(name+'_LOD0',mesh)
    scene.collection.objects.link(obj)
    folder=OUT/name
    folder.mkdir(parents=True,exist_ok=True)
    gray=bpy.data.materials.new(name+'_Gray')
    gray.diffuse_color=(.46,.50,.52,1)
    mesh.materials.append(gray)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'_gray.blend')))
    mat=bpy.data.materials.new('M_KarstRock')
    bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bsdf.inputs['Roughness'].default_value=.92
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(OUT/'T_KarstRock.png'))
    tex.image.pack()
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    mesh.materials.clear()
    mesh.materials.append(mat)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')))
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True)
    bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,axis_forward='-Z',axis_up='Y',use_triangles=True,add_leaf_bones=False,bake_anim=False)
    zs=[v[2] for v in vertices]
    info={'id':name,'name_zh':'喀斯特中景石峰','units':'m',
          'reference':f'art/references/midground-v1/{name}/three-view.png',
          'method':'不規則雙軸高度場與岩脊置換，單一連續山體',
          'pivot':'圓角山腳中央','dimensions_m':[2*R,2*R,round(max(zs),2)],
          'lods':[{'name':'LOD0','triangles':len(faces),'materials':1,
                   'textures':[{'name':'T_KarstRock.png','resolution':[1024,1024]}]}],
          'unity_import':'未驗證'}
    (folder/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print('DONE',name,len(faces),round(max(zs),2))


make('MM01',[(-8,1,96,18,20,.36,.3),(11,7,70,13,16,-.25,2.0),(-18,-9,48,12,14,.2,1.4)])
make('MM02',[(-14,-4,82,20,20,.48,1.1),(12,7,65,18,18,-.2,2.4),(20,-11,39,12,15,.1,3.1)])
