"""Mesh clean-up shared by build_basics.py, build_bm08.py and build_bm09_bm10.py (#69 review).

separate_overlaps: two separate pieces (twigs on a stem, leaf cards, grass blades, fallen leaves) whose triangles face the same
way within 10 degrees, lie within 2 mm of each other's plane and overlap: the smaller piece is lifted 2.5 mm along that face's
normal, in passes until none are left (found at 12 degrees / 3 mm, a margin over the QA tolerance). This is the reviewer's "same-facing coplanar" tolerance, as reproduced by
tools/art/qa_lod0_basic.py --loose. Pairs inside one connected piece are not touched here (they need a fix in the shape itself).

drop_ground_bottoms: faces at the ground (all corners under 2 cm) that face straight down are never seen; where pieces stand
side by side their bottoms overlap in one plane. They are deleted.
"""
import math
import bmesh
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

ANG=math.cos(math.radians(12));PLANE=.003;PEN=.0001   # a margin over the QA's 10 degrees / 2 mm: builders scale the mesh afterwards

def islands(bm):
    """connected pieces; corners at one position count as joined (a tube's end cap has its own corners for its UV)"""
    bm.verts.ensure_lookup_table();m=len(bm.verts);par=list(range(m))
    def fd(x):
        while par[x]!=x:par[x]=par[par[x]];x=par[x]
        return x
    for e in bm.edges:par[fd(e.verts[0].index)]=fd(e.verts[1].index)
    seen={}
    for v in bm.verts:
        k=(round(v.co.x/1e-5),round(v.co.y/1e-5),round(v.co.z/1e-5))
        if k in seen:par[fd(v.index)]=fd(seen[k])
        else:seen[k]=v.index
    roots={};isl=[roots.setdefault(fd(i),len(roots)) for i in range(m)]
    return isl,len(roots)

def overlap(a,b,n):
    """in-plane overlap depth of two triangles (separating axes), 0 when they only touch"""
    u_=(a[1]-a[0]).normalized();w_=n.cross(u_)
    P=[Vector((p.dot(u_),p.dot(w_))) for p in a];Q=[Vector((p.dot(u_),p.dot(w_))) for p in b];pen=1e9
    for poly in (P,Q):
        for t in range(3):
            e_=poly[(t+1)%3]-poly[t];ax=Vector((-e_.y,e_.x))
            if ax.length<1e-12:return 0
            ax.normalize();pa=[p.dot(ax) for p in P];pb=[p.dot(ax) for p in Q];pen=min(pen,min(max(pa),max(pb))-max(min(pa),min(pb)))
    return max(pen,0)

def pairs(bm,isl):
    """same-facing coplanar overlapping triangle pairs between different pieces: [(face a, face b)]"""
    bm.faces.ensure_lookup_table();bm.normal_update();out=[]
    tree=BVHTree.FromBMesh(bm,epsilon=PLANE)
    for i,j in tree.overlap(tree):
        if i>=j:continue
        a,b=bm.faces[i],bm.faces[j]
        if len(a.verts)!=3 or len(b.verts)!=3:continue
        if isl[a.verts[0].index]==isl[b.verts[0].index]:continue
        if a.normal.length<1e-9 or b.normal.length<1e-9 or a.normal.dot(b.normal)<ANG:continue
        A=[v.co for v in a.verts];B=[v.co for v in b.verts]
        if max(abs((p-A[0]).dot(a.normal)) for p in B)>PLANE:continue
        if overlap(A,B,a.normal)<PEN:continue
        out.append((a,b))
    return out

def separate_overlaps(bm,lift=.0025,passes=6,keep=None,mode='lift',tilt=12,big=None):
    """returns (pieces moved, pairs left). keep(island_vertices) -> True leaves that piece where it is (e.g. the trunk).
    mode 'lift': the smaller piece moves `lift` along the shared face normal.
    mode 'tilt': the smaller piece turns `tilt` degrees about its first-built vertex, which the builders make the base (a
    pinna's root on the rachis, a blade's root in the soil, a leaf's stalk on the twig), so it stays attached and only its
    free end swings out of the shared plane.
    big: pieces with more corners than this never move (a whole frond's rachis would swing away from its pinnae); a pair
    of two such pieces is left and counted."""
    if big is not None:keep=lambda vs,k0=keep:len(vs)>big or (k0 is not None and k0(vs))
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
    isl,n=islands(bm);size=[0]*n
    for v in bm.verts:size[isl[v.index]]+=1
    members={}
    for v in bm.verts:members.setdefault(isl[v.index],[]).append(v)
    moved=set();left=0
    for _ in range(passes):
        P=pairs(bm,isl);left=len(P)
        if not P:break
        done=set()
        for a,b in P:
            ia,ib=isl[a.verts[0].index],isl[b.verts[0].index]
            if ia in done or ib in done:continue
            fa,ka=(a,ia) if size[ia]<=size[ib] else (b,ib)
            if keep and keep(members[ka]):fa,ka=(b,ib) if ka==ia else (a,ia)
            if keep and keep(members[ka]):continue
            vs=members[ka];moved_ok=False
            if mode=='tilt':
                pv=min(vs,key=lambda v:v.index).co.copy();c=sum((v.co for v in vs),Vector())/len(vs);ax=(c-pv).cross(fa.normal)
                if ax.length>1e-6:
                    R=Matrix.Rotation(math.radians(tilt),3,ax.normalized())
                    for v in vs:v.co=pv+R@(v.co-pv)
                    moved_ok=True
            if not moved_ok:
                d=fa.normal*lift
                for v in vs:v.co+=d
            done.add(ka);moved.add(ka)
    else:left=len(pairs(bm,isl))
    return len(moved),left

def drop_ground_bottoms(bm,z=.02,keep_verts=False):
    """keep_verts: delete the faces only, so a builder that checks its bounds on vertices sees the same footprint"""
    bm.normal_update()
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.normal.z<-.95 and max(v.co.z for v in f.verts)<z],context='FACES_ONLY' if keep_verts else 'FACES')

def separate_meshes(meshes,**kw):
    """separate_overlaps over several meshes at once (pieces of different objects can overlap too, e.g. a frond on its rachis).
    Only vertex positions change, so custom normals and UVs stay as they were. Returns (pieces moved, pairs left)."""
    bm=bmesh.new();ranges=[]
    for me in meshes:
        base=len(bm.verts);tmp=bmesh.new();tmp.from_mesh(me)
        vmap=[bm.verts.new(v.co) for v in tmp.verts]
        for f in tmp.faces:
            try:bm.faces.new([vmap[v.index] for v in f.verts])
            except ValueError:pass   # a duplicate face: its vertices still move with the piece
        tmp.free();ranges.append((me,base,len(vmap)))
    bm.verts.index_update();r=separate_overlaps(bm,**kw);bm.verts.ensure_lookup_table()
    for me,base,n in ranges:
        for i in range(n):me.vertices[i].co=bm.verts[base+i].co
        me.update()
    bm.free();return r
