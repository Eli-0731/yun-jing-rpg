"""BM09 / BM10 only. Blender 4.5.3, deterministic, restricted output paths.
blender -b --factory-startup -P build_bm09_bm10.py -- [BM09_01 ... BM10_03]
Saved and selected AI references are required before any modelling begins.
Foliage uses authored blade atlases, not automatic triangle collapse: LODs preserve
the curved rachis and pinna direction. Ground materials are periodic from inception.
"""
import sys
sys.dont_write_bytecode=True
import bpy, math, json, random, struct
from pathlib import Path
from mathutils import Vector
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
import bm10_textures as tx
TEX=ROOT/'art/textures/modelling-basics-c';OUT=ROOT/'art/exports/modelling-basics-c'
IDS=['BM09_01','BM09_02','BM10_01','BM10_02','BM10_03']

def select(obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]

class Mesh:
    def __init__(self):self.v=[];self.uv=[];self.f=[]
    def vertex(self,p,uv):self.v.append(tuple(p));self.uv.append(uv);return len(self.v)-1
    def quad(self,a,b,c,d):self.f.extend([(a,b,c),(a,c,d)])
    def object(self,name,material):
        me=bpy.data.meshes.new(name);me.from_pydata(self.v,[],self.f);me.update()
        uv=me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            p.use_smooth=True
            for li in p.loop_indices:uv.data[li].uv=self.uv[me.loops[li].vertex_index]
        o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);me.materials.append(material)
        return o

def tube(mesh,points,radius,sides=4,uvcell=False):
    points=[Vector(p) for p in points];base=len(mesh.v);n=len(points)
    for i,p in enumerate(points):
        tangent=(points[min(i+1,n-1)]-points[max(i-1,0)]).normalized()
        a=tangent.cross(Vector((0,1,0)))
        if a.length<.01:a=tangent.cross(Vector((1,0,0)))
        a.normalize();b=tangent.cross(a).normalized();t=i/(n-1)
        for j in range(sides):
            r=radius*(1-.88*t);ang=math.tau*j/sides
            uv=((j/sides),t)
            if uvcell:uv=((.06+.88*j/sides)/4,(.05+.90*t)/2)
            mesh.vertex(p+r*(a*math.cos(ang)+b*math.sin(ang)),uv)
    for i in range(n-1):
        for j in range(sides):
            a=base+i*sides+j;b=base+i*sides+(j+1)%sides
            mesh.quad(a,b,b+sides,a+sides)
    mesh.f.append(tuple(base+j for j in reversed(range(sides))))
    mesh.f.append(tuple(base+(n-1)*sides+j for j in range(sides)))

def material(name,paths,alpha=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=False
    if alpha:m.blend_method='CLIP';m.alpha_threshold=.45
    nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.8
    bs.inputs['Specular IOR Level'].default_value=.24
    images={}
    for kind,path in paths.items():
        im=bpy.data.images.load(path,check_existing=True)
        im.colorspace_settings.name='sRGB' if kind=='Albedo' else 'Non-Color';images[kind]=im
    def node(kind):
        n=nt.nodes.new('ShaderNodeTexImage');n.image=images[kind];n.extension='REPEAT';n.label=kind;return n
    alb=node('Albedo');nt.links.new(alb.outputs['Color'],bs.inputs['Base Color'])
    if alpha:nt.links.new(alb.outputs['Alpha'],bs.inputs['Alpha'])
    normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(node('Normal').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
    sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(node('ORM').outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    group=bpy.data.node_groups.get('glTF Material Output')
    if group is None:
        group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree');group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
    gn=nt.nodes.new('ShaderNodeGroup');gn.node_tree=group;nt.links.new(sep.outputs['Red'],gn.inputs['Occlusion'])
    m['doubleSided']=True;m['alphaCutoff']=.45 if alpha else 0
    return m

def frond_specs(small):
    rng=random.Random(902 if small else 901);out=[]
    rings=[(6,.29,.17,.045),(4,.21,.25,.16),(2,.10,.30,.27)] if small else [(8,.66,.56,.20),(6,.43,.78,.57),(4,.22,.86,.79)]
    k=0
    for ring,(count,rise,height,tip) in enumerate(rings):
        for j in range(count):
            angle=math.tau*j/count+ring*.71+rng.uniform(-.19,.19)
            out.append((angle,rise*rng.uniform(.88,1.10),height*rng.uniform(.89,1.05),tip*rng.uniform(.86,1.10),ring,k));k+=1
    return out

def curve(t,spec,small):
    ang,r,h,tip,ring,k=spec
    # Cubic radial profile: steep petiole, outward arch, drooping distal rachis.
    p0=np.array([.013,.008]);p1=np.array([r*.08,h*.75]);p2=np.array([r*.62,h*1.18]);p3=np.array([r,tip])
    p=(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3
    if small and t>.80:
        s=.80;anchor=(1-s)**3*p0+3*(1-s)**2*s*p1+3*(1-s)*s*s*p2+s**3*p3
        tangent=3*(1-s)**2*(p1-p0)+6*(1-s)*s*(p2-p1)+3*s*s*(p3-p2)
        tangent/=np.linalg.norm(tangent);normal=np.array([-tangent[1],tangent[0]])
        q=(t-.80)/.20;phi=q*math.pi*1.65;rad=.026*(1-.48*q)
        p=anchor+rad*(tangent*math.sin(phi)+normal*(1-math.cos(phi)))
    a=ang+.07*math.sin(t*math.pi)*(1 if k%2 else -1)
    return Vector((math.cos(a)*p[0],math.sin(a)*p[0],p[1]))

def pinna(mesh,base,direction,up,length,width,slot,segments,curl,phase):
    # Swept ribbon with biological taper in alpha, retaining direction/bend in every LOD.
    base=Vector(base);direction=Vector(direction).normalized();up=Vector(up).normalized()
    transverse=direction.cross(up).normalized();first=len(mesh.v)
    col,row=slot%4,slot//4
    for i in range(segments+1):
        t=i/segments
        p=base+direction*length*t+up*(length*curl*(math.sin(t*math.pi)*.35-t*t*.24))
        twist=.16*math.sin(t*math.pi+phase)
        edge=(transverse*math.cos(twist)+up*math.sin(twist))*(width/2)
        for side in [-1,1]:
            uv=((col+.06+.88*(side+1)/2)/4,(row+.05+.90*t)/2)
            mesh.vertex(p+edge*side,uv)
    for i in range(segments):mesh.quad(first+i*2,first+i*2+1,first+i*2+3,first+i*2+2)

def fern_meshes(pid,lod):
    small=pid=='BM09_02';leaf=Mesh();stem=Mesh();detail=Mesh()
    segments=([4,2,1] if small else [6,3,1])[lod];rings=([22,11,3] if small else [24,12,3])[lod]
    pairs=([13,13,7] if small else [22,22,21])[lod]
    specs=frond_specs(small)
    for spec in specs:
        ang,r,h,tip,layer,k=spec
        samples=np.linspace(0,1,rings+1)
        if small and lod<2:
            base_n=12 if lod==0 else 6;end_n=rings-base_n
            samples=np.concatenate([np.linspace(0,.8,base_n+1),np.linspace(.8,1,end_n+1)[1:]])
        points=[curve(t,spec,small) for t in samples]
        tube(stem,points,.0016 if small else .0032,4)
        ts=np.linspace(.17,.985,pairs)
        if small and lod<2:ts=np.concatenate([np.linspace(.17,.77,pairs-4),np.linspace(.82,.99,4)])
        for j,t in enumerate(ts):
            p=curve(t,spec,small)
            tangent=(curve(min(1,t+.006),spec,small)-curve(max(0,t-.006),spec,small)).normalized()
            side=Vector((-math.sin(ang),math.cos(ang),.10*math.sin(t*5+k))).normalized()
            up=side.cross(tangent).normalized()
            if up.z<0:up=-up
            profile=math.sin(math.pi*(t-.10)/.94)**.80
            length=(.045 if small else .118)*profile*(1-.12*layer)*(1+.08*math.sin(j*2.7+k))
            if small and t>.80:length=max(length,.012)
            for s in [-1,1]:
                b=p+tangent*(.0015*s if small else .003*s)
                d=side*s+tangent*(.30+.12*t)
                slot=(k+j%3)%4
                if layer==0 and t>.72 and k%3!=1:slot=4+(k%4)
                pinna(leaf,b,d,up,length,length*(.42 if small else .30),slot,segments,.42 if small else .28,k*.7+j)
    # Coiled new croziers. These are part of the recognisable plant body.
    for k in range(3 if small else 2):
        a=k*2.4+.5;H=(.27 if small else .45)*(1-.12*k);r=.014 if small else .023
        count=([24,12,4] if small else [30,15,4])[lod]
        pts=[]
        for t in np.linspace(0,1,count+1):
            if t<.68:x=.02*t;z=H*t/.68
            else:
                q=(t-.68)/.32*math.tau*1.18;rad=r*(1-.72*(t-.68)/.32)
                x=.0136+rad*(1-math.cos(q));z=H+rad*math.sin(q)
            pts.append((math.cos(a)*x,math.sin(a)*x,z))
        tube(stem,pts,.0021 if small else .0036,4)
    # Dried, broken fronds at the crown; hiding this group leaves no baked body shadow.
    for k in range(3):
        a=k*2.18+.4;L=(.09 if small else .22)*(1-.12*k)
        pts=[(math.cos(a)*L*t,math.sin(a)*L*t,.012+L*.24*math.sin(t*math.pi)) for t in np.linspace(0,1,[12,6,2][lod])]
        tube(detail,pts,.0012 if small else .0022,3,True)
        npairs=[6,6,4][lod]
        for j in range(npairs):
            t=.2+.7*j/max(1,npairs-1);p=Vector((math.cos(a)*L*t,math.sin(a)*L*t,.012+L*.24*math.sin(t*math.pi)))
            for s in [-1,1]:
                d=Vector((-math.sin(a)*s,math.cos(a)*s,.15));length=L*.18*(1-t*.65)
                pinna(detail,p,d,Vector((0,0,1)),length,length*.34,4+k,[4,2,1][lod],.6,j)
    return {'Fronds':leaf,'Rachis':stem,'Detail_DryFronds':detail}

def ground(lod):
    mesh=Mesh();nx,ny=[(8,8),(8,4),(3,3)][lod]
    for y in range(ny+1):
        for x in range(nx+1):
            u,v=x/nx,y/ny;z=.0015*(1-math.cos(math.tau*u))*(1-math.cos(math.tau*v))
            mesh.vertex((u-.5,v-.5,z),(u,v))
    for y in range(ny):
        for x in range(nx):
            i=y*(nx+1)+x;mesh.quad(i,i+1,i+nx+2,i+nx+1)
    return {'Ground':mesh}

def bounds(objects):
    pts=np.array([tuple(o.matrix_world@v.co) for o in objects for v in o.data.vertices]);return pts.min(0),pts.max(0)

def glb_cutout(path):
    # Blender 4.5's legacy CLIP flag is exported as BLEND. Specify portable glTF MASK.
    data=path.read_bytes();offset=12;chunks=[]
    while offset<len(data):
        length,kind=struct.unpack_from('<II',data,offset);chunks.append((kind,data[offset+8:offset+8+length]));offset+=8+length
    doc=json.loads(chunks[0][1])
    for m in doc['materials']:
        cutoff=m.get('extras',{}).get('alphaCutoff',0)
        if cutoff:m['alphaMode']='MASK';m['alphaCutoff']=float(cutoff)
    encoded=json.dumps(doc,separators=(',',':')).encode('utf-8');encoded+=b' '*((-len(encoded))%4);chunks[0]=(chunks[0][0],encoded)
    body=b''.join(struct.pack('<II',len(content),kind)+content for kind,content in chunks)
    path.write_bytes(struct.pack('<III',0x46546c67,2,len(body)+12)+body)

def run(pid):
    assert pid in IDS
    ref=ROOT/'art/references'/pid[:4]/'prompt.txt'
    assert ref.exists() and '\u9078\u7528\uff1a' in ref.read_text(encoding='utf-8'), 'Save and select AI references first'
    expected=8 if pid.startswith('BM09') else 18
    assert len(list(ref.parent.glob('*-cand-*.png')))>=expected
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    TEX.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    fern=pid.startswith('BM09');target=.3 if pid=='BM09_02' else .8 if fern else 1.
    min_tier='high' if pid=='BM09_02' else 'standard' if fern else 'ultra'
    root=bpy.data.objects.new(pid+'_GroundOrigin',None);sc.collection.objects.link(root);root['minTier']=min_tier
    textures={};res={};mats={}
    if fern:
        for g,size,kw in [('Fronds',2048,{}),('Rachis',512,{'stem':True}),('Detail_DryFronds',512,{'dry':True})]:
            paths=tx.fern_atlas(pid+'_'+g,size,TEX,**kw);textures[g]=paths;res[g]=size;mats[g]=material(pid+'_'+g,paths,g!='Rachis')
    else:
        paths=tx.moss(pid+'_Ground',TEX) if pid=='BM10_01' else tx.leaves(pid+'_Ground',TEX,'maple' if pid=='BM10_02' else 'ginkgo')
        textures['Ground']=paths;res['Ground']=2048;mats['Ground']=material(pid+'_Ground',paths,pid!='BM10_01')
    groups={};lod0=[]
    for lod in range(3):
        meshes=fern_meshes(pid,lod) if fern else ground(lod)
        for g,mesh in meshes.items():
            o=mesh.object(f'{pid}_{g}_LOD{lod}',mats[g]);o.parent=root;o.hide_render=lod!=0;groups.setdefault(g,[]).append(o)
            if not fern:
                normals=[]
                for u,v in mesh.uv:
                    dx=.0015*math.tau*math.sin(math.tau*u)*(1-math.cos(math.tau*v))
                    dy=.0015*math.tau*math.sin(math.tau*v)*(1-math.cos(math.tau*u))
                    normals.append(tuple(Vector((-dx,-dy,1)).normalized()))
                o.data.normals_split_custom_set_from_vertices(normals)
            if lod==0:lod0.append(o)
    # Normalise by body only, then apply the same transform to every detail and LOD.
    body=[o for o in lod0 if '_Detail_' not in o.name];lo,hi=bounds(body)
    factor=target/(hi[2]-lo[2]) if fern else 1.;offset=np.array([-(hi[0]+lo[0])/2,-(hi[1]+lo[1])/2,-lo[2]])
    for objects in groups.values():
        for o in objects:
            for v in o.data.vertices:
                v.co=(Vector(v.co)+Vector(offset))*factor
                if v.co.z<0:v.co.z=0
    bpy.context.view_layer.update()
    lo,hi=bounds(lod0);blo,bhi=bounds(body)
    tri=lambda o:sum(len(p.vertices)-2 for p in o.data.polygons)
    details=[g for g in groups if g.startswith('Detail_')]
    info={'id':pid,'dimensions_xyz_m':[round(float(v),6) for v in hi-lo],'body_dimensions_xyz_m':[round(float(v),6) for v in bhi-blo],
          'target_axis':'z' if fern else 'x','target_m':target,'minTier':min_tier,'detailObjects':details,
          'detailMeshes':[o.name for g in details for o in groups[g]],
          'groups':{g:{'material':pid+'_'+g,'texture_px':res[g],'triangles':[tri(o) for o in obs],'maps':['alb','nrm','maskurp','orm']} for g,obs in groups.items()},
          'triangles_total':[sum(tri(obs[l]) for obs in groups.values()) for l in range(3)],
          'triangles_without_detail':[sum(tri(obs[l]) for g,obs in groups.items() if not g.startswith('Detail_')) for l in range(3)],
          'reference':str(ref.relative_to(ROOT)).replace('\\','/'),'origin':'footprint centre, bottom z = 0, front = -Y (Blender) / -Z (FBX, Unity)',
          'textures':{g:{k:str(Path(v).relative_to(ROOT)).replace('\\','/') for k,v in maps.items()} for g,maps in textures.items()},'collision':{},
          'notes':{'build':'Curved rachis, paired bent alpha pinnae, older brown outer tips, coiled croziers; atlas groups preserve leaf silhouette at LOD1.' if fern else '1m square periodic ground surface; authored procedural texture, leaf alpha gaps; 8x8 / 8x4 / 3x3 grids.',
                   'detail':'Detail_DryFronds can be hidden; no baked detail shadows on body.' if fern else 'Whole patch is ultra dressing; no independent detail submeshes are necessary.',
                   'material':'Double-sided foliage; Albedo sRGB, Normal tangent +Y, ORM=AO/roughness/metal, MaskURP=metal/AO/0/smoothness. No photo sources.',
                   'validation':'Blender export/import only; Unity and mobile performance not tested.'}}
    if fern:assert info['triangles_total'][0]<(6000 if pid=='BM09_02' else 15000)
    assert abs(float(bhi[2]-blo[2])-target)<1e-5 if fern else abs(float(bhi[0]-blo[0])-1)<1e-5
    root['detailObjects']=json.dumps(details)
    select([root]+lod0)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/(pid+'.blend')),compress=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(pid+'.glb')),use_selection=True,export_format='GLB',export_apply=True,export_extras=True)
    glb_cutout(OUT/(pid+'.glb'))
    select([root]+[o for obs in groups.values() for o in obs])
    bpy.ops.export_scene.fbx(filepath=str(OUT/(pid+'.fbx')),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    print('BM_DONE',json.dumps(info));return info

if __name__=='__main__':
    assert bpy.app.version[:3]==(4,5,3), 'Pinned Blender 4.5.3 required'
    ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else IDS
    mf=OUT/'model_info_bm09_bm10.json';infos=json.loads(mf.read_text(encoding='utf-8')) if mf.exists() else {}
    for pid in ids:
        infos[pid]=run(pid);mf.write_text(json.dumps(infos,ensure_ascii=False,indent=2),encoding='utf-8')
