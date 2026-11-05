"""LOD0 mesh QA for C's exported props, run on a fresh GLB import (what the engine and the reviewer receive).
Same kinds of findings as the core group's Blender asset QA: no UV map, zero-area UV faces, coplanar overlapping
triangles (z-fighting), floating/detached islands, unapplied scale. One finding per object and kind, with a count.

  blender -b --factory-startup -P tools/art/qa_lod0_basic.py -- <out.json> <a.glb> [<b.glb> ...]

Coplanar pairs: two triangles of LOD0 (same object or not) that share no vertex, face the same or the opposite way
within 1.5 degrees, lie within 0.5 mm of each other's plane and overlap by more than 1 mm inside that plane.
Floating island: a connected piece whose lowest point is above 2.5 cm and which comes no closer than 2.5 cm
to any other piece. Alpha-cut cards are checked like any other mesh.
"""
import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

TOL=.025;PLANE=.0005;ANG=math.cos(math.radians(1.5));PEN=.001;UVEPS=1e-10
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]);files=args[1:]

def tris_world(o):
    bm=bmesh.new();bm.from_mesh(o.data);bm.transform(o.matrix_world);bmesh.ops.triangulate(bm,faces=bm.faces[:])
    bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
    return bm

def sat_overlap(a,b,n):   # two coplanar triangles: smallest penetration along the in-plane edge normals (SAT)
    u=(a[1]-a[0]).normalized();w=n.cross(u)
    P=[Vector((p.dot(u),p.dot(w))) for p in a];Q=[Vector((p.dot(u),p.dot(w))) for p in b];best=1e9
    for poly in (P,Q):
        for i in range(3):
            e=poly[(i+1)%3]-poly[i];ax=Vector((-e.y,e.x))
            if ax.length<1e-12:return 0
            ax.normalize();pa=[p.dot(ax) for p in P];pb=[p.dot(ax) for p in Q]
            d=min(max(pa),max(pb))-max(min(pa),min(pb))
            if d<=0:return 0
            best=min(best,d)
    return best

def check(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and not any(s in o.name for s in ('Collision','_COL','_LOD1','_LOD2'))]
    findings=[];allv=[];alltri=[];owner=[]
    for o in obs:
        s=o.matrix_world.to_scale()
        if any(abs(c-1)>1e-4 for c in o.scale):findings.append(('unapplied scale',o.name,1,f'scale {tuple(round(c,4) for c in o.scale)}'))
        me=o.data
        if not me.uv_layers:findings.append(('no UV map',o.name,1,''))
        else:
            uv=me.uv_layers.active.data;z=0
            for p in me.polygons:
                pts=[uv[i].uv for i in p.loop_indices];a=0
                for i in range(1,len(pts)-1):a+=abs((pts[i]-pts[0]).cross(pts[i+1]-pts[0]))/2
                if a<UVEPS:z+=1
            if z:findings.append(('zero-area UV',o.name,z,f'{z} of {len(me.polygons)} faces'))
        bm=tris_world(o);base=len(allv)
        allv+= [v.co.copy() for v in bm.verts]
        for f in bm.faces:alltri.append(tuple(base+v.index for v in f.verts));owner.append(o.name)
        bm.free()
    if not alltri:return {'file':str(path),'objects':0,'findings':[]}
    # islands: union-find over shared vertices (positions welded at 0.01 mm, as glTF splits verts on UV seams)
    key=lambda v:(round(v.x/1e-5),round(v.y/1e-5),round(v.z/1e-5));weld={};par=list(range(len(allv)))
    def fd(x):
        while par[x]!=x:par[x]=par[par[x]];x=par[x]
        return x
    for i,v in enumerate(allv):
        k=key(v)
        if k in weld:par[fd(i)]=fd(weld[k])
        else:weld[k]=i
    for t in alltri:
        r=fd(t[0])
        for k in t[1:]:par[fd(k)]=r
    tree=BVHTree.FromPolygons(allv,alltri,all_triangles=True,epsilon=PLANE)
    pairs={};where={};nkey={}
    for i,j in tree.overlap(tree):
        if i>=j or set(alltri[i])&set(alltri[j]):continue
        A=[allv[k] for k in alltri[i]];B=[allv[k] for k in alltri[j]]
        na=(A[1]-A[0]).cross(A[2]-A[0]);nb=(B[1]-B[0]).cross(B[2]-B[0])
        if na.length<1e-12 or nb.length<1e-12:continue
        na.normalize();nb.normalize()
        if abs(na.dot(nb))<ANG:continue
        if max(abs((p-A[0]).dot(na)) for p in B)>PLANE:continue
        if sat_overlap(A,B,na)<PEN:continue
        key=tuple(sorted((owner[i],owner[j])));pairs[key]=pairs.get(key,0)+1
        if len(where.setdefault(key,[]))<6:where[key].append([round(c,3) for c in (A[0]+A[1]+A[2])/3]+['n'+''.join('%+.0f'%c for c in na)])
        nkey.setdefault(key,{});nk=('down' if na.z<-.95 else 'up' if na.z>.95 else 'side')+(' z<0.02' if max(p.z for p in A)<.02 else '')+(' one piece' if fd(alltri[i][0])==fd(alltri[j][0]) else ' two pieces');nkey[key][nk]=nkey[key].get(nk,0)+1
    for (a,b),c in sorted(pairs.items()):
        findings.append(('coplanar overlap',a if a==b else f'{a} x {b}',c,f'{c} triangle pairs {nkey[(a,b)]}, e.g. at {where[(a,b)]}'))
    isl={};[isl.setdefault(fd(t[0]),[]).append(n) for n,t in enumerate(alltri)]
    if len(isl)>1:
        kd=KDTree(sum(3+max(0,int(((allv[t[1]]-allv[t[0]]).length+(allv[t[2]]-allv[t[0]]).length)/TOL))**2 for t in alltri));pid=[];samp={}
        for n,t in enumerate(alltri):   # vertices plus a grid of points on larger triangles
            A,B,C=(allv[k] for k in t);m=max(1,int(max((B-A).length,(C-A).length,(C-B).length)/TOL))
            for a in range(m+1):
                for b in range(m+1-a):
                    q=A+(B-A)*(a/m)+(C-A)*(b/m);kd.insert(q,len(pid));pid.append(fd(t[0]));samp.setdefault(fd(t[0]),[]).append(q)
        kd.balance()
        for r,ts in isl.items():   # every sample point of the island (not only its vertices), so a long beam on two caps counts as touching
            vs={k for n in ts for k in alltri[n]}
            if min(allv[k].z for k in vs)<=TOL:continue
            if any(pid[j]!=r for q in samp[r] for (_,j,_) in kd.find_range(q,TOL)):continue
            ob=owner[ts[0]];c_=sum((allv[k] for k in vs),Vector())/len(vs);findings.append(('floating/detached',ob,1,f'island of {len(ts)} triangles at {[round(x,3) for x in c_]}'))
    merged={}
    for kind,ob,c,note in findings:
        if kind=='floating/detached':
            k=(kind,ob);n=merged.get(k,(0,0));merged[k]=(n[0]+1,n[1]+int(note.split()[2]))
    at={};[at.setdefault(ob,[]).append(note.split(' at ')[1]) for kind,ob,c,note in findings if kind=='floating/detached']
    out_f=[f for f in findings if f[0]!='floating/detached']+[('floating/detached',ob,n,f'{n} islands, {t} triangles, at {"; ".join(at[ob][:6])}') for (kind,ob),(n,t) in merged.items()]
    return {'file':str(path),'objects':len(obs),'triangles':len(alltri),'findings':[dict(kind=k,object=o,count=c,note=n) for k,o,c,n in out_f]}

rep=[check(Path(f)) for f in files]
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,ensure_ascii=False,indent=1),encoding='utf-8')
for r in rep:
    print('@@QA@@',Path(r['file']).stem,len(r['findings']),'findings',r.get('triangles'),'tris')
    for f in r['findings']:print('   ',f['kind'],'|',f['object'],'|',f['note'])
