"""Shared kit for build_bm09.py (ferns) and build_bm10.py (ground patches), rewritten for the #69 follow-up: a small mesh
builder, value noise, map writing (Albedo with alpha, Normal from height, ORM, MaskURP), colour bleed into the cut-out
margin, an alpha-clip material, the FBX / GLB export the Unity check expects, and the model_info merge.
Nothing here draws a plant or a patch; the shapes and the painting live in the two build scripts."""
import bpy,json,math,struct
from pathlib import Path
import numpy as np
from mathutils import Vector

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
TEX=ROOT/'art/textures/modelling-basics-c';OUT=ROOT/'art/exports/modelling-basics-c'

# ---------------------------------------------------------------- mesh
class Mesh:
    """vertices with one UV each (a seam is simply a second vertex), triangles and quads"""
    def __init__(s):s.v=[];s.uv=[];s.f=[]
    def add(s,co,uv):s.v.append(tuple(co));s.uv.append(tuple(uv));return len(s.v)-1
    def tri(s,a,b,c):s.f.append((a,b,c))
    def quad(s,a,b,c,d):s.f.append((a,b,c,d))
    def tris(s):return sum(len(f)-2 for f in s.f)
    def build(s,name,mat):
        me=bpy.data.meshes.new(name);me.from_pydata(s.v,[],s.f);me.update()
        uv=me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            for li in p.loop_indices:uv.data[li].uv=s.uv[me.loops[li].vertex_index]
        for p in me.polygons:p.use_smooth=True
        if mat:me.materials.append(mat)
        o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return o

def frame(tangent,up=Vector((0,0,1))):
    """side and normal for a direction: side is horizontal, normal leans up"""
    t=tangent.normalized();s=t.cross(up)
    if s.length<1e-6:s=t.cross(Vector((1,0,0)))
    s.normalize();n=s.cross(t).normalized();return s,n

def tube(mesh,pts,radii,sides,v_scale=1.,u0=0.,u1=1.):
    """open tube along pts (no end caps: the base sits in the soil, the tip is thinner than a pixel); UV u round, v along"""
    base=len(mesh.v);acc=0.;prev=None;n=len(pts)
    for i,p in enumerate(pts):
        t=(pts[min(i+1,n-1)]-pts[max(i-1,0)]).normalized()
        a=(prev-t*prev.dot(t)) if prev is not None else frame(t)[0]
        a.normalize();prev=a;b=t.cross(a).normalized()
        if i:acc+=(p-pts[i-1]).length
        for j in range(sides+1):
            ang=math.tau*j/sides;mesh.add(p+radii[i]*(a*math.cos(ang)+b*math.sin(ang)),(u0+(u1-u0)*j/sides,acc*v_scale))
    for i in range(n-1):
        for j in range(sides):
            k=base+i*(sides+1)+j;mesh.quad(k,k+1,k+sides+2,k+sides+1)

# ---------------------------------------------------------------- painting
def noise(h,w,cells,seed,octaves=4,wrap=False):
    """value noise in 0..1; wrap=True tiles on all four sides (the grids are periodic and resampled with wrap-around)"""
    rng=np.random.default_rng(seed);out=np.zeros((h,w),np.float32);amp=1.;tot=0.
    for o in range(octaves):
        c=max(2,int(cells*2**o));g=rng.random((c,c)).astype(np.float32)
        ys=(np.arange(h)+.5)/h*c-(0 if wrap else .5);xs=(np.arange(w)+.5)/w*c-(0 if wrap else .5)
        y0=np.floor(ys).astype(int);x0=np.floor(xs).astype(int);fy=(ys-y0)[:,None];fx=(xs-x0)[None,:]
        fy=fy*fy*(3-2*fy);fx=fx*fx*(3-2*fx)
        if wrap:y0%=c;x0%=c;y1=(y0+1)%c;x1=(x0+1)%c
        else:y1=np.clip(y0+1,0,c-1);x1=np.clip(x0+1,0,c-1);y0=np.clip(y0,0,c-1);x0=np.clip(x0,0,c-1)
        v=(g[y0][:,x0]*(1-fx)+g[y0][:,x1]*fx)*(1-fy)+(g[y1][:,x0]*(1-fx)+g[y1][:,x1]*fx)*fy
        out+=amp*v;tot+=amp;amp*=.5
    out/=tot;lo,hi=np.percentile(out,1),np.percentile(out,99);return np.clip((out-lo)/max(hi-lo,1e-6),0,1)

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def bleed(rgb,alpha,passes=40):
    """push opaque colour out into the transparent margin, so mip levels and filtering never pull in black"""
    rgb=rgb.copy();m=(alpha>.02).astype(np.float32)
    if m.all() or not m.any():return rgb
    rgb*=m[...,None]
    for _ in range(passes):
        acc=np.zeros_like(rgb);cnt=np.zeros_like(m)
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):acc+=np.roll(np.roll(rgb*m[...,None],dy,0),dx,1);cnt+=np.roll(np.roll(m,dy,0),dx,1)
        new=(m==0)&(cnt>0);rgb[new]=acc[new]/cnt[new][:,None];m=np.maximum(m,new.astype(np.float32))
        if m.all():break
    if not m.all():rgb[m==0]=rgb[m>0].mean(0)
    return rgb

def normal_from_height(h,strength,wrap=False):
    if wrap:dx=(np.roll(h,-1,1)-np.roll(h,1,1))*.5;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*.5
    else:dy,dx=np.gradient(h)
    n=np.dstack([-dx*strength,dy*strength,np.ones_like(h)]);n/=np.linalg.norm(n,axis=2,keepdims=True)
    return n*.5+.5   # tangent space, +Y up (image rows run down, hence the sign on dy)

def save_maps(name,rgb,alpha,height,rough,ao,strength=6.,wrap=False,bleed_px=40):
    """Albedo (RGBA, sRGB), Normal, ORM (AO / roughness / metal) and MaskURP (metal / AO / 0 / smoothness)"""
    TEX.mkdir(parents=True,exist_ok=True)
    rgb=np.clip(rgb,0,1)
    if alpha is not None and bleed_px:rgb=bleed(rgb,alpha,bleed_px)
    a=np.ones(rgb.shape[:2],np.float32) if alpha is None else np.clip(alpha,0,1)
    paths={}
    def put(key,arr,data):
        H,W=arr.shape[:2];arr=np.dstack([arr,np.ones((H,W),np.float32)]) if arr.shape[2]==3 else arr
        p=TEX/f'{name}_{key}.png';im=bpy.data.images.new(f'{name}_{key}',W,H,alpha=True)
        if data:im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(np.ascontiguousarray(np.clip(arr[::-1],0,1),dtype=np.float32).ravel())   # Blender rows run bottom-up
        im.filepath_raw=str(p);im.file_format='PNG'
        p.unlink(missing_ok=True);im.save();bpy.data.images.remove(im);paths[key]=str(p)
    put('Albedo',np.dstack([rgb,a]),False)
    put('Normal',normal_from_height(height,strength,wrap),True)
    z=np.zeros_like(rough);put('ORM',np.dstack([ao,rough,z]),True);put('MaskURP',np.dstack([z,ao,z,1-rough]),True)
    return paths

# ---------------------------------------------------------------- material and export
def material(name,paths,cutout):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=False
    nt=m.node_tree;n=nt.nodes;l=nt.links;bs=n['Principled BSDF']
    def img(key,linear):
        t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(paths[key]);t.image.colorspace_settings.name='Non-Color' if linear else 'sRGB';return t
    a=img('Albedo',False);l.new(a.outputs['Color'],bs.inputs['Base Color'])
    nm=n.new('ShaderNodeNormalMap');l.new(img('Normal',True).outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],bs.inputs['Normal'])
    sep=n.new('ShaderNodeSeparateColor');l.new(img('ORM',True).outputs['Color'],sep.inputs['Color'])
    l.new(sep.outputs['Green'],bs.inputs['Roughness']);l.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    bs.inputs['Specular IOR Level'].default_value=.3
    if cutout:
        l.new(a.outputs['Alpha'],bs.inputs['Alpha']);m['alphaCutoff']=.45   # read back by gltf_mask() below
        try:m.surface_render_method='DITHERED'
        except AttributeError:m.blend_method='CLIP'
    return m

def gltf_mask(path):
    """Blender writes alpha as BLEND; foliage needs glTF MASK with the 0.45 cutoff stored on the material"""
    data=Path(path).read_bytes();off=12;chunks=[]
    while off<len(data):
        ln,kind=struct.unpack_from('<II',data,off);chunks.append([kind,data[off+8:off+8+ln]]);off+=8+ln
    doc=json.loads(chunks[0][1])
    for m in doc.get('materials',[]):
        c=m.get('extras',{}).get('alphaCutoff')
        if c:m['alphaMode']='MASK';m['alphaCutoff']=float(c)
    js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);chunks[0][1]=js
    body=b''.join(struct.pack('<II',len(c),k)+c for k,c in chunks)
    Path(path).write_bytes(struct.pack('<III',0x46546c67,2,len(body)+12)+body)

def select(obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]

def export(pid,root,lod0,every):
    OUT.mkdir(parents=True,exist_ok=True);select([root]+lod0)
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/(pid+'.blend')),compress=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(pid+'.glb')),use_selection=True,export_format='GLB',export_apply=True,export_extras=True)
    gltf_mask(OUT/(pid+'.glb'))
    select([root]+every)
    bpy.ops.export_scene.fbx(filepath=str(OUT/(pid+'.fbx')),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)

def bounds(obs):
    p=np.array([tuple(o.matrix_world@v.co) for o in obs for v in o.data.vertices]);return p.min(0),p.max(0)

def tri_count(o):return sum(len(p.vertices)-2 for p in o.data.polygons)

def merge_model_info(info):
    """writes this item into model_info.json (1-space indent, as the file is kept) so the Unity check sees it straight away"""
    p=OUT/'model_info.json';d=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    d[info['id']]=info;p.write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

def rel(p):return str(Path(p).relative_to(ROOT)).replace('\\','/')
