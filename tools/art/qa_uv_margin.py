"""UV margin check for C's exported props, on a fresh GLB import (what the engine receives).
For every LOD0 mesh: rasterise its UV islands at the resolution of the texture the material actually uses, then report
  - UVs outside 0..1,
  - pixels painted by two islands (UV overlap: the bake would mix them),
  - the narrowest gap between two islands in texture pixels, and how many island pairs are closer than 2 / 4 / 8 px.
Islands are faces joined by shared corners with the same position and the same UV (glTF splits vertices on seams
and on hard edges, so mesh pieces alone would over-count). A pixel belongs to an island when its centre lies within
half a pixel of one of its triangles.

  blender -b --factory-startup -P tools/art/qa_uv_margin.py -- <out.json> <a.glb> [<b.glb> ...]
"""
import bpy,sys,json
import numpy as np
from pathlib import Path

R=8   # gaps are measured up to this many pixels
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]);files=args[1:]

def tex_res(o):
    for m in o.data.materials:
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type=='TEX_IMAGE' and n.image and n.image.size[0]:return n.image.size[0],n.image.size[1]
    return None

def islands(me,uv):
    nl=len(me.loops);vi=np.zeros(nl,np.int64);me.loops.foreach_get('vertex_index',vi)
    co=np.zeros(len(me.vertices)*3);me.vertices.foreach_get('co',co);co=co.reshape(-1,3)
    k=np.hstack([np.round(co[vi]/1e-5),np.round(uv/1e-6)]).astype(np.int64)
    _,key=np.unique(k,axis=0,return_inverse=True);key=key.ravel()
    nf=len(me.polygons);ls=np.zeros(nf,np.int64);me.polygons.foreach_get('loop_start',ls);lt=np.zeros(nf,np.int64);me.polygons.foreach_get('loop_total',lt)
    par=np.arange(key.max()+1)
    def fd(x):
        r=x
        while par[r]!=r:r=par[r]
        while par[x]!=r:par[x],x=r,par[x]
        return r
    for s,t in zip(ls,lt):
        r=fd(key[s])
        for j in range(s+1,s+t):
            q=fd(key[j])
            if q!=r:par[q]=r
    root=np.array([fd(x) for x in range(len(par))])
    face_isl=root[key[ls]];_,lab=np.unique(face_isl,return_inverse=True)
    return lab.ravel()+1,ls,lt

def check_obj(o):
    me=o.data;res=tex_res(o)
    if not me.uv_layers or not res:return None
    W,H=res;nl=len(me.loops);uv=np.zeros(nl*2);me.uv_layers.active.data.foreach_get('uv',uv);uv=uv.reshape(-1,2)
    oob=int(((uv<-1e-4)|(uv>1+1e-4)).any(1).sum())
    lab,ls,lt=islands(me,uv)
    img=np.zeros((H,W),np.int32);overlap=0;ovl_pairs=set()
    P=uv*np.array([W,H])
    for f,(s,t) in enumerate(zip(ls,lt)):
        for j in range(1,t-1):   # fan triangles
            A,B,C=P[s],P[s+j],P[s+j+1]
            x0=max(int(np.floor(min(A[0],B[0],C[0])-1)),0);x1=min(int(np.ceil(max(A[0],B[0],C[0])+1)),W)
            y0=max(int(np.floor(min(A[1],B[1],C[1])-1)),0);y1=min(int(np.ceil(max(A[1],B[1],C[1])+1)),H)
            if x1<=x0 or y1<=y0:continue
            xs,ys=np.meshgrid(np.arange(x0,x1)+.5,np.arange(y0,y1)+.5)
            area=(B[0]-A[0])*(C[1]-A[1])-(B[1]-A[1])*(C[0]-A[0]);sg=1 if area>=0 else -1;inside=np.ones(xs.shape,bool)
            for p,q in ((A,B),(B,C),(C,A)):   # signed distance to each edge, half a pixel of slack
                e=q-p;L=np.hypot(*e)
                if L<1e-9:continue
                inside&=sg*(e[0]*(ys-p[1])-e[1]*(xs-p[0]))/L>=-.5
            sub=img[y0:y1,x0:x1];clash=inside&(sub>0)&(sub!=lab[f])
            if clash.any():
                overlap+=int(clash.sum());ovl_pairs|={tuple(sorted((int(a),int(lab[f])))) for a in np.unique(sub[clash])}
            sub[inside&(sub==0)]=lab[f]
    best={}
    ys_,xs_=np.nonzero(img);
    if len(ys_):
        y0,y1,x0,x1=ys_.min(),ys_.max()+1,xs_.min(),xs_.max()+1;im=img[y0:y1,x0:x1]
        offs=sorted({(dy,dx) for dy in range(0,R+1) for dx in range(-R,R+1) if (dy>0 or dx>0) and dy*dy+dx*dx<=R*R},key=lambda d:d[0]**2+d[1]**2)
        for dy,dx in offs:
            d=(dy*dy+dx*dx)**.5;h,w=im.shape
            a=im[0:h-dy,max(0,-dx):w-max(0,dx)];b=im[dy:h,max(0,dx):w-max(0,-dx)]   # b is a shifted by (dy,dx)
            m=(a>0)&(b>0)&(a!=b)
            if not m.any():continue
            pr=np.unique(np.sort(np.stack([a[m],b[m]],1),1),axis=0)
            for p in map(tuple,pr):
                if p in ovl_pairs:continue
                best.setdefault(p,d-1)   # pixel centres d apart with both filled: the empty gap between them is d-1 px
    gaps=sorted(best.values())
    return dict(object=o.name,res=f'{W}x{H}',faces=len(me.polygons),islands=int(lab.max()),uv_outside=oob,
                overlap_px=overlap,overlap_pairs=len(ovl_pairs),min_gap_px=(round(gaps[0],2) if gaps else f'>{R}'),
                pairs_under_2px=sum(g<2 for g in gaps),pairs_under_4px=sum(g<4 for g in gaps),pairs_under_8px=len(gaps))

rep=[]
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=f)
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and not any(s in o.name for s in ('Collision','_COL','_LOD1','_LOD2'))]
    r=[x for x in (check_obj(o) for o in sorted(obs,key=lambda o:o.name)) if x]
    rep.append({'file':str(f),'objects':r})
    for x in r:print('@@UV@@',Path(f).stem,x)
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,ensure_ascii=False,indent=1),encoding='utf-8')
