"""Contact table read from an exported GLB (no named source parts needed): every connected piece of LOD0 (corners at one
position count as joined), the largest gap on its best chain of pieces down to the ground (the plane z=0 the asset stands on;
parts sunk below it count as touching).
0 means the piece touches or cuts into something that reaches the ground (vertex distances alone would count a root buried 4 mm deep as a 4 mm gap). Grouped per object, with the worst pieces' positions,
so each kind (fallen leaves, shards, stones, leaf cards) can be shown with a close-up and a reason.

  blender -b --factory-startup -P tools/art/qa_contact_glb.py -- <out.json> <a.glb> [<b.glb> ...]
"""
import bpy,bmesh,sys,json,heapq,collections
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=.06;GROUND=.001
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]);rep={}
for f in args[1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=f)
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and not any(s in o.name for s in ('Collision','_COL','_LOD1','_LOD2'))]
    V=[];F=[];own=[]
    for o in obs:
        bm=bmesh.new();bm.from_mesh(o.data);bm.transform(o.matrix_world);bmesh.ops.triangulate(bm,faces=bm.faces[:]);base=len(V)
        V+=[v.co.copy() for v in bm.verts]
        for t in bm.faces:F.append(tuple(base+v.index for v in t.verts));own.append(o.name)
        bm.free()
    par=list(range(len(V)))
    def fd(x):
        while par[x]!=x:par[x]=par[par[x]];x=par[x]
        return x
    seen={}
    for i,v in enumerate(V):
        k=(round(v.x/1e-5),round(v.y/1e-5),round(v.z/1e-5))
        if k in seen:par[fd(i)]=fd(seen[k])
        else:seen[k]=i
    for t in F:
        for k in t[1:]:par[fd(k)]=fd(t[0])
    isl=[fd(t[0]) for t in F];ground=0.;tree=BVHTree.FromPolygons(V,F,all_triangles=True)   # ground: the plane z=0 every asset stands on (trunks and stakes go below it)
    verts=collections.defaultdict(set);obj={}
    for n,t in enumerate(F):verts[isl[n]].update(t);obj.setdefault(isl[n],own[n])
    G='GROUND';adj=collections.defaultdict(dict)
    for r,vs in verts.items():
        z=min(V[k].z for k in vs)-ground
        if z<R:adj[r][G]=max(z,0.)
        for k in vs:
            for (co,nn,fi,d) in tree.find_nearest_range(V[k],R):
                q=isl[fi]
                if q!=r and d<adj[r].get(q,9):adj[r][q]=d
    for i,j in tree.overlap(tree):   # triangles that cut through each other touch, however deep one sits in the other (a root in the soil)
        if isl[i]!=isl[j]:adj[isl[i]][isl[j]]=0.
    for r in list(adj):
        for q,d in list(adj[r].items()):adj[q][r]=min(d,adj[q].get(r,9))
    best={G:0.};pq=[(0.,G)]
    while pq:
        d,u=heapq.heappop(pq)
        if d>best.get(u,9):continue
        for w,dd in adj[u].items():
            nd=max(d,dd)
            if nd<best.get(w,9):best[w]=nd;heapq.heappush(pq,(nd,w))
    per=collections.defaultdict(list)
    for r,vs in verts.items():
        c=sum((V[k] for k in vs),V[0]*0)/len(vs);per[obj[r]].append((best.get(r,9),[round(x,3) for x in c]))
    res={}
    for o,L in sorted(per.items()):
        L.sort(key=lambda x:-x[0]);ds=[x[0] for x in L]
        res[o]=dict(pieces=len(L),within_1mm=sum(d<=GROUND for d in ds),gap_1_3mm=sum(GROUND<d<=.003 for d in ds),gap_3_10mm=sum(.003<d<=.01 for d in ds),
                    gap_over_10mm=sum(d>.01 for d in ds),largest_mm=(round(L[0][0]*1000,1) if L[0][0]<R else f'>{int(R*1000)}'),worst_at=[x[1] for x in L[:4] if x[0]>.003])
        print('@@CONTACT@@',Path(f).stem,o,{k:v for k,v in res[o].items() if k!='worst_at'})
    rep[Path(f).stem]=res
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,ensure_ascii=False,indent=1),encoding='utf-8')
