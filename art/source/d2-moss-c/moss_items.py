# DP06 moss clumps (D2 V2, V3, V6) — exec'd by build_moss.py; every item is filled in after its three-view is picked.
import random as _rnd

def _outline(seed,noise,lobes=(2,3,5,7,13,19)):
    """irregular lobed outline: radius factor round the clump"""
    r_=_rnd.Random(seed);ph=[r_.uniform(0,6.3) for _ in lobes];am=[noise*w for w in (.50,.30,.16,.10,.07,.05)[:len(lobes)]]   # 13 and 19: the ragged small-scale edge (no separate strands)
    return lambda th:1+sum(a*math.sin(n*th+p) for a,n,p in zip(am,lobes,ph))

def _field(pts,cent,amp,rad,sharp=.6):
    """sum of soft domes: pts (N,2), cent (M,2), amp (M), rad (M) → (N)"""
    if not len(cent):return np.zeros(len(pts))
    d=np.linalg.norm(pts[:,None,:]-np.asarray(cent)[None,:,:],axis=2)/np.asarray(rad)[None,:]
    return (np.asarray(amp)[None,:]*np.clip(1-d*d,0,1)**sharp).max(1)   # max, not sum: overlapping humps never stack into a spike

def _poisson(r_,n,inside,rmin,tries=4000):
    out=[]
    for _ in range(tries):
        if len(out)>=n:break
        p=inside(r_)
        if p is None:continue
        if all((p[0]-q[0])**2+(p[1]-q[1])**2>=rmin*rmin for q in out):out.append(p)
    return out

def _mound(name,c,rx,ry,H,M,grp,seed,nr=16,nth=56,noise=.18,lobes=(),bumps=96,bump_r=(0.020,0.048),bump_h=.35,
           prof=(2.0,.55),bend=0.,depth=.015,fringe=0,fringe_len=(0.012,0.028),mat='moss',flank='moss_old',skirt='soil',flank_h=0.,
           hollow=None,lobe_floor=.3,bump_sharp=.9):
    """a moss cushion: lobed outline, a few big lobes (lobes: (x, y, height factor, radius) in units of rx/ry),
    many small tuft humps on top, the rim lands on z = 0, a soil skirt runs on below, loose strands spill over the rim.
    The top keeps a flat top-down 'Tiled' UV; the underside of a boulder cap (and a lower flank, if flank_h > 0) is the older brown-olive moss.
    fringe: loose strands over the rim (off for DP06: they read as thorns at game distance and lay on the moss; the ragged outline does it)."""
    r_=_rnd.Random(seed);c=Vector(c);rr=_outline(seed,noise)
    th=np.array([math.tau*k/nth for k in range(nth)])
    def xy(f,t):
        s=rr(t)*f;x=math.cos(t)*rx*s;y=math.sin(t)*ry*s+bend*(x/rx)**2*ry;return x,y
    # even triangles (no polar fan, which pinched the top into radial creases): the rim ring + a jittered hex grid inside,
    # Delaunay-triangulated inside the rim; about 2·nr·nth top triangles, as the old ring layout
    rim=[xy(1.,t) for t in th];N=nr*nth
    area=math.pi*rx*ry*float(np.mean([rr(t)**2 for t in th]));sp=math.sqrt(area/(N*math.sqrt(3)/2))
    inner=[];Fi=[];j=0;yy=-ry*1.6
    while yy<ry*1.6:
        xx=-rx*1.6+(sp/2 if j%2 else 0.)
        while xx<rx*1.6:
            x=xx+r_.uniform(-.22,.22)*sp;y=yy+r_.uniform(-.22,.22)*sp
            t=math.atan2(y/ry,x/rx);e=math.hypot(x/rx,y/ry);f=e/rr(t);R=math.hypot(rx*math.cos(t),ry*math.sin(t))*rr(t)
            if f<1 and (1-f)*R>.55*sp:inner.append((x,y+bend*(x/rx)**2*ry));Fi.append(f)
            xx+=sp
        yy+=sp*math.sqrt(3)/2;j+=1
    pts=np.array(rim+inner);F=np.array([1.]*nth+Fi)
    base=(1-np.clip(F,0,1)**prof[0])**prof[1]
    if lobes:   # big lobes: the height follows the highest lobe under each point (merged rounded humps)
        L=np.array([[lx*rx,ly*ry+bend*lx*lx*ry] for lx,ly,_,_ in lobes]);la=np.array([a for _,_,a,_ in lobes]);lr=np.array([q*max(rx,ry) for *_,q in lobes])
        d=np.linalg.norm(pts[:,None,:]-L[None],axis=2)/lr[None];lob=(la[None]*np.clip(1-d*d,0,1)**.5).max(1)   # round-topped lobes
        base=base*(lobe_floor+(1-lobe_floor)*np.clip(lob,0,1))
    # small tuft humps over the whole top, smaller toward the rim
    def inside(rg):
        t=rg.uniform(0,math.tau);f=math.sqrt(rg.random())*.97;return xy(f,t)
    cen=_poisson(r_,bumps,inside,bump_r[0]*1.3)
    rad=[r_.uniform(*bump_r) for _ in cen];amp=[r_.uniform(.5,1.)*bump_h*H for _ in cen]
    z=H*base+_field(pts,cen,amp,rad,bump_sharp)*np.clip(base*3,0,1)
    z[F>=.999]=0.   # rim on the ground
    from mathutils.geometry import delaunay_2d_cdt
    cv,_,cf,_,_,_=delaunay_2d_cdt([Vector(p) for p in pts],[],[list(range(nth))],2,1e-7)
    assert len(cv)==len(pts),'the triangulation added or merged points'
    bm=bmesh.new();V=[bm.verts.new(c+Vector((p[0],p[1],zz))) for p,zz in zip(pts,z)];n=nth
    for f_ in cf:
        try:bm.faces.new([V[i] for i in f_])
        except ValueError:pass
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f_ in bm.faces:
        if f_.normal.z<0:f_.normal_flip()
    under=set()
    if hollow:   # boulder cap: no skirt; a hollow underside (the rock's dome) closes the shell, the lip sits on z = 0
        fi,Hr=hollow;U=[]
        for f in [fi*(1-j/(nr//2)) for j in range(nr//2)]:
            U.append([bm.verts.new(c+Vector((*xy(f,t),Hr*max(0.,1-(f/fi)**2)**.5))) for t in th])
        uc=bm.verts.new(c+Vector((0,0,Hr)));rimv=V[:n]
        for k in range(n):
            k1=(k+1)%n;under.add(bm.faces.new((rimv[k],rimv[k1],U[0][k1],U[0][k])))
            for i in range(len(U)-1):under.add(bm.faces.new((U[i][k],U[i][k1],U[i+1][k1],U[i+1][k])))
            under.add(bm.faces.new((U[-1][k],U[-1][k1],uc)))
    bm.normal_update();uv=bm.loops.layers.uv.new('Tiled');du,dv=r_.random(),r_.random()
    Rm=(rx+ry)/2
    for fc in bm.faces:   # top-down on the gentle top; round the clump on the steep sides, so the tufts never stretch into streaks
        fc.smooth=True;steep=abs(fc.normal.z)<.6;cx=fc.calc_center_median()-c;a0=math.atan2(cx.y,cx.x)
        for l in fc.loops:
            q=l.vert.co-c
            if steep:
                a=math.atan2(q.y,q.x);a+=math.tau*round((a0-a)/math.tau)   # no wrap inside one face
                l[uv].uv=(a*Rm/K.TILE+du,q.z/K.TILE+dv+.37)
            else:l[uv].uv=(q.x/K.TILE+du,q.y/K.TILE+dv)
    idx=[i for i,fc in enumerate(bm.faces) if fc in under or (flank_h>0 and fc.calc_center_median().z-c.z<flank_h*H)]
    o=finish(name,bm,M[mat],grp,keep_uv=True)
    if flank:   # the lower flank: older brown-olive moss (a second slot, the atlas bake keeps it)
        o.data.materials.append(M[flank])
        for i in idx:o.data.polygons[i].material_index=1
    # soil skirt under the rim (not under a boulder cap: that one sits on the rock)
    if not hollow:
        bm=bmesh.new();rim=[c+Vector((*pts[k],0)) for k in range(n)]
        a=[bm.verts.new(p) for p in rim];b=[bm.verts.new(c+(p-c)*.93+Vector((0,0,-depth))) for p in rim];bot=bm.verts.new(c+Vector((0,0,-depth)))
        for k in range(n):
            k1=(k+1)%n;bm.faces.new((a[k1],a[k],b[k],b[k1]));bm.faces.new((b[k1],b[k],bot))
        finish(name+'_skirt',bm,M[skirt],grp)
    assert not fringe,'rim strands were dropped for DP06 (read as thorns, lay on the moss)'
    return o

def _moss_paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
    """D2 moss: muted yellow-green on the tops of the tufts that face the sky, darker and cooler in the hollows"""
    up=np.clip((onrm[...,2]-.35)/.6,0,1)*ao;lit=up*(.8+.2*noise)   # follows the sky-facing tops, not a low-frequency blotch
    tip=np.array([.40,.38,.10])   # D2 V6: muted yellow-green tips
    lum=col.mean(2,keepdims=True)/max(float(col.mean()),1e-4)   # keep the tuft pattern of the source: tint, do not paint over
    col=col*(1-.30*lit[...,None])+tip[None,None,:]*.30*lit[...,None]*np.clip(lum,.4,1.6)
    col=col*(1-.35*cav[...,None])
    return np.clip(col,0,1),np.clip(rough+.03,0,1)

def dp06_01(M):   # A small round cushion (cand-3): one low rounded cushion, 0.25 m, 0.10 m tall
    _rnd.seed(6001)
    _mound('DP06_01_Moss',(0,0,0),.125,.12,.075,M,'Body',6001,nr=16,nth=76,noise=.10,bumps=73,bump_r=(0.018,0.032),bump_h=.26,prof=(1.8,.85),fringe=0,fringe_len=(0.006,0.014))
    return {'paint':_moss_paint,'grime':.6,'wear':0}
def dp06_02(M):   # B lumpy mound (cand-1): three or four merged lobes, 0.45 × 0.38 × 0.16
    _rnd.seed(6002)
    _mound('DP06_02_Moss',(0,0,0),.225,.19,.15,M,'Body',6002,nr=18,nth=84,noise=.14,
           lobes=((-.45,.05,.78,.62),(.18,-.22,1.0,.66),(.0,.52,.66,.52),(.62,.24,.55,.44)),bumps=96,bump_r=(0.018,0.036),bump_h=.15,prof=(4.0,.6),lobe_floor=.18,fringe=0,fringe_len=(0.006,0.017))
    return {'paint':_moss_paint,'grime':.6,'wear':0}
def dp06_03(M):   # C large low spreading patch (cand-3): flat blanket with gentle humps, ragged lobed outline, 0.80 × 0.60 × 0.10
    _rnd.seed(6003)
    _mound('DP06_03_Moss',(0,0,0),.40,.30,.085,M,'Body',6003,nr=20,nth=92,noise=.24,
           lobes=((-.45,.10,.85,.40),(.10,-.25,1.0,.45),(.45,.25,.80,.38),(-.05,.45,.70,.35),(.65,-.30,.55,.28)),bumps=192,bump_r=(0.022,0.044),bump_h=.32,prof=(1.6,.7),lobe_floor=.25,fringe=0,fringe_len=(0.007,0.017))
    return {'paint':_moss_paint,'grime':.6,'wear':0}
def dp06_04(M):   # D root-foot strip (cand-1): a chain of soft humps tapering at both ends, 0.60 × 0.22 × 0.12, a slight curve to follow a root
    _rnd.seed(6004)
    _mound('DP06_04_Moss',(0,0,0),.30,.105,.11,M,'Body',6004,nr=16,nth=88,noise=.10,bend=.35,
           lobes=((-.62,0,.55,.30),(-.22,0,.95,.40),(.22,0,1.0,.40),(.60,0,.60,.32)),bumps=96,bump_r=(0.016,0.032),bump_h=.28,prof=(2.0,.75),lobe_floor=.2,fringe=0,fringe_len=(0.006,0.015))
    return {'paint':_moss_paint,'grime':.6,'wear':0}
def dp06_05(M):   # E boulder cap (cand-1): domed shell, edges drape to the ground line, hollow underneath where the rock sits
    _rnd.seed(6005)
    _mound('DP06_05_Moss',(0,0,0),.225,.21,.14,M,'Body',6005,nr=16,nth=80,noise=.10,bumps=102,bump_r=(0.020,0.036),bump_h=.22,prof=(2.0,.75),
           fringe=0,fringe_len=(0.009,0.019),hollow=(.90,.095))
    return {'paint':_moss_paint,'grime':.6,'wear':0}
def dp06_06(M):   # F scattered tufts (cand-4): one larger tuft and six small separate ones over 0.50 × 0.40
    _rnd.seed(6006);r=_rnd.Random(606)
    _mound('DP06_06_Big',(-.04,.02,0),.10,.09,.075,M,'Body',6061,nr=12,nth=52,noise=.12,bumps=48,bump_r=(0.013,0.024),bump_h=.28,prof=(1.8,.8),fringe=0,fringe_len=(0.005,0.011))
    small=((.17,.10,.045,.040),(.19,-.09,.035,.030),(-.20,.13,.038,.032),(-.21,-.10,.050,.042),(.02,-.16,.032,.028),(.06,.17,.028,.025))
    for i,(x,y,rad,h) in enumerate(small):
        _mound(f'DP06_06_Tuft{i+1}',(x,y,0),rad*r.uniform(.9,1.1),rad*r.uniform(.85,1.0),h,M,'Body',6070+i,nr=7,nth=26,noise=.12,bumps=16,bump_r=(0.007,0.013),bump_h=.28,prof=(1.8,.8),fringe=0,fringe_len=(0.004,0.008),depth=.01)
    return {'paint':_moss_paint,'grime':.6,'wear':0}

PROPS.update({'DP06_01':dp06_01,'DP06_02':dp06_02,'DP06_03':dp06_03,'DP06_04':dp06_04,'DP06_05':dp06_05,'DP06_06':dp06_06})
