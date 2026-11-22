# d2-floor-c shared part helpers (from d2-mushrooms-c/dp_items.py: stems, caps, moss pads, wood chips), exec'd by build_floor.py (names from there: K, M, Vector, Matrix, np, math, bmesh, bpy, finish, PROPS, link …)
import random as _rnd
TL=K.TILE

def _frame(ax):
    ax=Vector(ax).normalized();u=ax.orthogonal().normalized();v=ax.cross(u);return ax,u,v

def _stem(name,base,top,r0,r1,M,grp,sides=8,bulb=1.25,bend=None,rings=6):
    """tapered stem from base (in the pad) to top (under the cap): a soft bend, a small bulb at the foot,
    own 'Tiled' UV (u round, v along the length) so the fibres run up the stem; the lowest ring takes the foot colour"""
    base=Vector(base);top=Vector(top);bend=Vector(bend) if bend is not None else Vector((0,0,0))
    pts=[base.lerp(top,t)+bend*math.sin(math.pi*t) for t in (i/(rings-1) for i in range(rings))]
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');R=[];prev=None;s=[0.];roll=_rnd.uniform(0,math.tau)   # every stem's facets turned differently (no coplanar neighbours)
    for a,b in zip(pts,pts[1:]):s.append(s[-1]+(b-a).length)
    for i,p in enumerate(pts):
        t=(pts[min(i+1,rings-1)]-pts[max(i-1,0)]).normalized()
        u=(prev-t*prev.dot(t)).normalized() if prev is not None else (Matrix.Rotation(roll,3,t)@t.orthogonal()).normalized();prev=u;v=t.cross(u)
        f=i/(rings-1);r=r0+(r1-r0)*f;r*=1+(bulb-1)*max(0,1-f*3.5)**2
        R.append([bm.verts.new(p+(u*math.cos(math.tau*k/sides)+v*math.sin(math.tau*k/sides))*r) for k in range(sides)])
    circ=math.tau*(r0+r1)/2;du=_rnd.random()
    for i in range(rings-1):
        for k in range(sides):
            fc=bm.faces.new((R[i][k],R[i][(k+1)%sides],R[i+1][(k+1)%sides],R[i+1][k]))
            for l,(kk,ii) in zip(fc.loops,((k,i),(k+1,i),(k+1,i+1),(k,i+1))):l[lay].uv=(du+kk/sides*circ/TL*3,s[ii]/TL*1.5)
    bm.faces.new(list(reversed(R[0])))   # closed foot (buried in the pad)
    for fc in bm.faces:fc.smooth=True
    return finish(name,bm,M['stem'],grp,keep_uv=True)

def _cap(name,apex,ax,R,M,grp,seed,segs=24,thick=.22,umbo=.06,droop=.04,wave=.05,under=.10,gill=.035,young=0.,arch=1.6):
    """mushroom cap round the axis `ax`, its underside centre at `apex` (the stem top).
    Top (material 'cap'): pole → 3 rings → rim, flat-convex with a low central bump; the rim turns a little down and under.
    Underside (material 'gill'): 2 corrugated rings (gill ridges in the mesh, fine gill lines in the texture) → a fan at the stem.
    young (0–1) closes the cap into a bell (buttons). Both pieces keep a polar 'Tiled' UV: u round the cap, v centre → rim."""
    r_=_rnd.Random(seed);ax,U,V=_frame(ax);apex=Vector(apex);ph=[r_.uniform(0,6.3) for _ in range(4)]
    rot=Matrix.Rotation(r_.uniform(0,math.tau),3,ax);U=rot@U;V=rot@V   # each cap's segments start at a different angle
    # Broad asymmetry plus small scallops and a chipped sector on mature caps.
    def rad(th):
        nick=max(0.,math.cos(th-ph[3]))**45
        return R*(1+wave*math.sin(3*th+ph[0])+wave*.6*math.sin(5*th+ph[1])
                  +(1-young)*(.024*math.sin(9*th+ph[2])-.055*nick))
    def edge_lift(th):
        return R*(1-young)*(.023*math.sin(5*th+ph[1])+.016*math.sin(11*th+ph[2]))
    def P(th,rho,h):return apex+(U*math.cos(th)+V*math.sin(th))*rho+ax*h
    bell=young
    def htop(f):   # f: 0 centre … 1 rim, in units of R
        return R*(thick*(1-f**arch)*(1+bell*.5)+umbo*math.exp(-(f/.29)**2)-droop*f**3-bell*.55*f**2)+R*under   # flat-convex: a low dome with a small central bump (D2 V2/V4/V6), the rim turned down
    top_f=(.14,.32,.60,.85,1.0) if R>.028 else (.30,.60,.85,1.0);bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled')
    pole=bm.verts.new(apex+ax*htop(0));ring=[]
    for f in top_f:
        row=[]
        for k in range(segs):
            th=math.tau*k/segs;rr=rad(th)*f*(1-.18*bell*f);row.append(bm.verts.new(P(th,rr,htop(f)+R*.012*math.sin(2*th+ph[2])*f+edge_lift(th)*f**3)))
        ring.append(row)
    rim=[]   # rolled-under edge
    for k in range(segs):
        th=math.tau*k/segs;rr=rad(th)*(.96-.2*bell);rim.append(bm.verts.new(P(th,rr,htop(1)-R*(.06+.25*bell)+edge_lift(th))))
    ring.append(rim);fv=list(top_f)+[1.0]
    for k in range(segs):
        k1=(k+1)%segs;u0,u1=k/segs,(k+1)/segs
        fc=bm.faces.new((pole,ring[0][k],ring[0][k1]))
        for l,uv in zip(fc.loops,(((u0+u1)/2,0),(u0,fv[0]),(u1,fv[0]))):l[lay].uv=uv
        for i in range(len(ring)-1):
            fc=bm.faces.new((ring[i][k],ring[i+1][k],ring[i+1][k1],ring[i][k1]))
            for l,uv in zip(fc.loops,((u0,fv[i]),(u0,fv[i+1]),(u1,fv[i+1]),(u1,fv[i]))):l[lay].uv=uv
    for fc in bm.faces:fc.smooth=True
    top=finish(name+'_top',bm,M['cap'],grp,keep_uv=True)
    # underside: from the rolled rim inward over the gills to the stem
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');rows=[]
    for j,f in enumerate((.96,.72,.38)):
        row=[]
        for k in range(segs):
            th=math.tau*k/segs;rr=rad(th)*f*(1-.2*bell);g=(gill*R if j>0 else 0)*(1 if k%2 else -1)
            hh=(htop(1)-R*(.06+.25*bell)+edge_lift(th)) if j==0 else R*under*(.55+.45*(1-f))-R*.032+g
            row.append(bm.verts.new(P(th,rr,hh)))
        rows.append(row)
    ctr=bm.verts.new(apex+ax*R*under*.9);vf=(1.,.72,.38)
    for k in range(segs):
        k1=(k+1)%segs;u0,u1=k/segs,(k+1)/segs
        for i in range(2):
            fc=bm.faces.new((rows[i][k],rows[i][k1],rows[i+1][k1],rows[i+1][k]))
            for l,uv in zip(fc.loops,((u0,vf[i]),(u1,vf[i]),(u1,vf[i+1]),(u0,vf[i+1]))):l[lay].uv=uv
        fc=bm.faces.new((rows[2][k],rows[2][k1],ctr))
        for l,uv in zip(fc.loops,((u0,vf[2]),(u1,vf[2]),((u0+u1)/2,.05))):l[lay].uv=uv
    for fc in bm.faces:fc.smooth=True
    und=finish(name+'_gills',bm,M['gill'],grp,keep_uv=True)
    return top,und

def _shroom(name,base,lean,H,R,M,grp,seed,segs=24,stem_r=None,bend=.25,bend_dir=None,**cap):
    """one mushroom: stem from `base` (in the pad, z a little below its surface) leaning by `lean` (x, y), height H to the cap top"""
    r_=_rnd.Random(seed+7);base=Vector(base);ax=Vector((lean[0],lean[1],1)).normalized()
    sr=stem_r or R*.16;und=R*cap.get('under',.10)
    apex=base+ax*(H-R*(cap.get('thick',.22)+cap.get('umbo',.06)+cap.get('under',.10)))
    side=ax.orthogonal().normalized();side.rotate(Matrix.Rotation(r_.uniform(0,6.3),3,ax))
    if bend_dir is not None:side=Vector(bend_dir).normalized()   # the tuft: the stems bow outwards
    sides=10 if R>.045 else (8 if R>.03 else 6)
    _stem(name+'_stem',base,apex+ax*und*.55,sr*1.15,sr*.85,M,grp,sides=sides,bend=side*H*bend*.12)
    # The stem can lean away from the cluster while its mature cap stays nearly level.
    cap_lean = .38 if cap.get('young',0) < .25 else .64
    capax=Vector((ax.x*cap_lean+r_.uniform(-.11,.11),ax.y*cap_lean+r_.uniform(-.10,.10),1)).normalized()
    _cap(name+'_cap',apex,capax,R,M,grp,seed,segs=segs,**cap)

def _pad(name,c,rx,ry,h,M,grp,seed,segs=18,mat='moss',skirt='soil',depth=.012,rings=(.35,.7,1.0),noise=.25):
    """moss pad on wet soil: a low irregular cushion whose rim lands on z = 0 and runs on 1.2 cm under the ground"""
    r_=_rnd.Random(seed);c=Vector(c);ph=[r_.uniform(0,6.3) for _ in range(6)]
    def rr(th):return 1+noise*(.55*math.sin(2*th+ph[0])+.3*math.sin(3*th+ph[1])+.15*math.sin(5*th+ph[2]))
    bm=bmesh.new();top=bm.verts.new(c+Vector((0,0,h)));R=[]
    for f in rings:
        row=[]
        for k in range(segs):
            th=math.tau*k/segs;s=rr(th)*f;z=h*(1-f**2)**.8*(1+.25*math.sin(4*th+ph[3])*f) if f<1 else 0.
            row.append(bm.verts.new(c+Vector((math.cos(th)*rx*s,math.sin(th)*ry*s,z))))
        R.append(row)
    for k in range(segs):
        k1=(k+1)%segs;bm.faces.new((top,R[0][k],R[0][k1]))
        for i in range(len(R)-1):bm.faces.new((R[i][k],R[i+1][k],R[i+1][k1],R[i][k1]))
    for fc in bm.faces:fc.smooth=True
    o=finish(name,bm,M[mat],grp)
    bm=bmesh.new()
    rim=[c+Vector((math.cos(math.tau*k/segs)*rx*rr(math.tau*k/segs),math.sin(math.tau*k/segs)*ry*rr(math.tau*k/segs),0)) for k in range(segs)]
    a=[bm.verts.new(p) for p in rim];b=[bm.verts.new(c+(p-c)*.9+Vector((0,0,-depth))) for p in rim];bot=bm.verts.new(c+Vector((0,0,-depth)))
    for k in range(segs):
        k1=(k+1)%segs;bm.faces.new((a[k1],a[k],b[k],b[k1]));bm.faces.new((b[k1],b[k],bot))
    finish(name+'_under',bm,M[skirt],grp)
    return o

def _chip(name,c,rx,ry,h,M,grp,seed,segs=20):
    """a flake of rotten bark-wood lying half in the soil: irregular outline, thick in the middle and thin, broken edges;
    top at c.z + h, rim on z = c.z, bottom 1.5 cm below"""
    r_=_rnd.Random(seed);c=Vector(c);ph=[r_.uniform(0,6.3) for _ in range(6)]
    def rr(th):return 1+.22*math.sin(2*th+ph[0])+.12*math.sin(3*th+ph[1])+.08*math.sin(7*th+ph[2])+r_.uniform(-.05,.05)
    bm=bmesh.new();top=bm.verts.new(c+Vector((0,0,h)));R=[];rs=[rr(math.tau*k/segs) for k in range(segs)]
    for f,z in ((.45,.92),(.8,.65),(1.0,.18),(1.0,0.)):
        R.append([bm.verts.new(c+Vector((math.cos(math.tau*k/segs)*rx*rs[k]*f,math.sin(math.tau*k/segs)*ry*rs[k]*f,h*z*(1+.15*math.sin(5*k/segs*math.tau+ph[3]))))) for k in range(segs)])
    bot=[bm.verts.new(c+Vector((math.cos(math.tau*k/segs)*rx*rs[k]*.85,math.sin(math.tau*k/segs)*ry*rs[k]*.85,-.015))) for k in range(segs)];R.append(bot)
    cb=bm.verts.new(c+Vector((0,0,-.015)))
    for k in range(segs):
        k1=(k+1)%segs;bm.faces.new((top,R[0][k],R[0][k1]))
        for i in range(len(R)-1):bm.faces.new((R[i][k],R[i+1][k],R[i+1][k1],R[i][k1]))
        bm.faces.new((bot[k1],bot[k],cb))
    o=finish(name,bm,M['rotwood'],grp,scale=.12);jitter(o,.003,seed,freq=90);return o

