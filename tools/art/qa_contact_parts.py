"""Per-kind contact table for the loose pieces of C's props (debris, weed, tufts, gravel), read from the working .blend
where every piece is still its own named object in <ID>_SourceParts with its group in the 'grp' property.

For every piece of a loose group: the largest gap on the best chain of pieces that leads to the ground or to a fixed
part (weir, gate, stone). 0 means it touches or sinks into its support, directly or through pieces that do;
a twig that touches its branch counts as resting on whatever the branch rests on. Pieces are grouped by kind
(the name without numbers: Branch, Twig, Weed, JointTuft ...).

  blender -b --factory-startup -P tools/art/qa_contact_parts.py -- <out.json> <a.blend>:<LooseGroup,LooseGroup> [...]
"""
import bpy,re,json,sys,collections,heapq
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=.06   # gaps are measured up to 6 cm
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]);rep={}
for spec in args[1:]:
    blend,groups=spec.rsplit(':',1);loose=set(groups.split(','))
    bpy.ops.wm.open_mainfile(filepath=blend)
    col=[c for c in bpy.data.collections if c.name.endswith('_SourceParts')][0];pid=col.name[:-len('_SourceParts')]
    src=[o for o in col.objects if o.type=='MESH' and not o.get('nobounds')]
    V=[];F=[];own=[]
    for k,o in enumerate(src):
        b=len(V);mw=o.matrix_world;V+=[mw@v.co for v in o.data.vertices]
        for p in o.data.polygons:F.append([b+i for i in p.vertices]);own.append(k)
    tree=BVHTree.FromPolygons(V,F)
    fixed={k for k,o in enumerate(src) if o.get('grp') not in loose}
    ground=min((src[k].matrix_world@v.co).z for k in fixed for v in src[k].data.vertices)
    G='GROUND';adj=collections.defaultdict(dict);lo=[k for k in range(len(src)) if k not in fixed]
    for k in lo:
        o=src[k];mw=o.matrix_world;vs=[mw@v.co for v in o.data.vertices];zmin=min(v.z for v in vs)-ground
        if zmin<R:adj[k][G]=max(zmin,0)
        for v in vs:
            for (co,n,fi,d) in tree.find_nearest_range(v,R):
                j=own[fi]
                if j==k:continue
                j=G if j in fixed else j
                if d<adj[k].get(j,9):adj[k][j]=d
    for k in list(adj):
        for j,d in list(adj[k].items()):adj[j][k]=min(d,adj[j].get(k,9))
    best={G:0};pq=[(0,G)]
    while pq:   # minimax path from the ground
        d,u=heapq.heappop(pq)
        if d>best.get(u,9):continue
        for w,dd in adj[u].items():
            nd=max(d,dd)
            if nd<best.get(w,9):best[w]=nd;heapq.heappush(pq,(nd,w))
    kinds=collections.defaultdict(list)
    for k in lo:
        o=src[k];m=re.match(re.escape(pid)+r'_([A-Za-z]+?)(\d|_|-|$)',o.name);t=m.group(1) if m else o.name
        kinds[(o.get('grp'),t)].append((round(best.get(k,9),4),o.name))
    r_={}
    for (g,t),L in sorted(kinds.items()):
        L.sort(reverse=True);ds=[x[0] for x in L]
        r_[f'{g}/{t}']=dict(pieces=len(L),within_1mm=sum(d<=.001 for d in ds),gap_1_3mm=sum(.001<d<=.003 for d in ds),gap_3_10mm=sum(.003<d<=.01 for d in ds),
                            gap_over_10mm=sum(d>.01 for d in ds),largest_mm=(round(L[0][0]*1000,1) if L[0][0]<R else f'>{int(R*1000)}'),largest_at=L[0][1])
        print('@@CONTACT@@',pid,g,t,r_[f'{g}/{t}'])
    rep[pid]=r_
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,ensure_ascii=False,indent=1),encoding='utf-8')
