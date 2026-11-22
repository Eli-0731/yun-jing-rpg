# DP08 小蕨, DP09 林下地被, DP11 莎草 (small plants, every leaf and leaflet modelled, no cards) — exec'd by build_moss.py.
# Origin: base centre, z = 0 on the ground; a small soil disc under the plant runs 1 cm under the ground (no floating on uneven ground).

def _plant_sources(S):
    K.rng=np.random.default_rng(6801)   # leaf: muted forest green, a paler midrib along V (u across 0..1), soft veins, darker edge
    mid=np.exp(-((X-.5)/.05)**2);vein=np.clip(.5+.5*np.sin(math.tau*(Y*14+np.abs(X-.5)*6)),0,1)**6*(1-mid)
    edge=np.clip((np.abs(X-.5)-.38)*8,0,1);t=np.clip(.5+.6*(fbm(5,3)-.5),0,1)
    base=lerp((.10,.15,.07),(.20,.27,.12),t)
    S['leaf']=(base*(1-.25*edge[...,None])+mid[...,None]*np.array([.06,.07,.03])+vein[...,None]*np.array([.03,.035,.015]),.8*mid+.5*vein,1.6,.62,0,0)
    S['leaf_young']=(lerp((.22,.28,.10),(.36,.42,.16),t)+mid[...,None]*np.array([.05,.05,.02]),.8*mid+.4*vein,1.4,.6,0,0)
    S['leaf_dark']=(lerp((.07,.10,.05),(.15,.20,.09),t)*(1-.25*edge[...,None])+mid[...,None]*np.array([.04,.05,.02]),.8*mid+.5*vein,1.6,.6,0,0)
    K.rng=np.random.default_rng(6802)   # sedge blade: dark green along V with fine parallel lines, the tip (v → 1) dry brown
    ln=.5+.5*np.sin(math.tau*X*9);tip=np.clip((Y-.80)*5+.15*(fbm(8,2)-.5),0,1)
    g=lerp((.08,.12,.06),(.17,.23,.10),np.clip(.5+.5*(fbm(4,3,aniso=8)-.5)+.15*(ln-.5),0,1))
    S['sedge']=(g*(1-tip[...,None])+tip[...,None]*np.array([.36,.28,.17]),.6*ln,1.2,.6,0,0)
    S['sedge_dry']=(lerp((.26,.20,.12),(.42,.34,.21),np.clip(.5+.5*(fbm(4,3,aniso=8)-.5),0,1)),.6*ln,1.2,.75,0,0)
    K.rng=np.random.default_rng(6803)   # stems: dark brown-black (maidenhair, fern rachis), red-brown (seedlings, sorrel), seed spikes
    f=np.clip((fbm(50,2,aniso=30)-.5)*2+.5,0,1)
    S['stem_dark']=(lerp((.04,.03,.025),(.11,.08,.06),f),.5*f,1.,.45,0,0)
    S['stem_red']=(lerp((.20,.09,.06),(.36,.18,.12),f),.5*f,1.,.6,0,0)
    S['stem_green']=(lerp((.12,.16,.07),(.22,.27,.12),f),.5*f,1.,.6,0,0)
    S['spike']=(lerp((.18,.12,.07),(.34,.24,.14),np.clip(.5+.6*(fbm(30,2)-.5),0,1)),.9*fbm(60,2),1.6,.8,0,0)
SRC_HOOKS.append(_plant_sources)

def _base(name,rx,ry,h,M,grp,seed,mat='soil',depth=.010,segs=18):
    h=min(h,.007)   # a low disc: it reads as soil, not a plinth
    """a low soil disc under a plant: rim on z = 0, a skirt 1 cm under the ground"""
    r_=_rnd.Random(seed);ph=[r_.uniform(0,6.3) for _ in range(3)];bm=bmesh.new()
    rr=lambda t:1+.12*math.sin(2*t+ph[0])+.08*math.sin(3*t+ph[1])+.04*math.sin(7*t+ph[2])
    top=bm.verts.new((0,0,h));R=[]
    for f in (.5,1.):R.append([bm.verts.new((math.cos(math.tau*k/segs)*rx*rr(math.tau*k/segs)*f,math.sin(math.tau*k/segs)*ry*rr(math.tau*k/segs)*f,h*(1-f*f)**.6 if f<1 else 0.)) for k in range(segs)])
    bot=[bm.verts.new((v.co.x*.9,v.co.y*.9,-depth)) for v in R[-1]];cb=bm.verts.new((0,0,-depth))
    for k in range(segs):
        k1=(k+1)%segs;bm.faces.new((top,R[0][k],R[0][k1]));bm.faces.new((R[0][k],R[1][k],R[1][k1],R[0][k1]))
        bm.faces.new((R[1][k1],R[1][k],bot[k],bot[k1]));bm.faces.new((bot[k1],bot[k],cb))
    for f in bm.faces:f.smooth=True
    return finish(name,bm,M[mat],grp,scale=.2)

def _curve(p0,d0,L,droop=.0,side=None,bend=0.,n=6):
    """a gently arching path: start p0, start direction d0, length L; droop pulls it down by droop·L·t², bend sideways"""
    p0=Vector(p0);d0=Vector(d0).normalized();side=Vector(side) if side is not None else d0.orthogonal().normalized()
    return [p0+d0*L*t-Vector((0,0,1))*droop*L*t*t+side*bend*L*t*t for t in (i/n for i in range(n+1))]

def _strip(name,pts,widths,up,M,mat,grp,uv_len=None,fold=0.):
    """a flat strip along pts (blade, rachis band): width per point, its face turned toward `up` (a vector or a list); u across 0..1, v along"""
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');L=[];R=[];Mid=[];s=[0.]
    for a,b in zip(pts,pts[1:]):s.append(s[-1]+(b-a).length)
    tot=s[-1] or 1.
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized();u=Vector(up[i] if isinstance(up,list) else up)
        sd=t.cross(u).normalized();nn=sd.cross(t).normalized();w=widths[i]/2
        L.append(bm.verts.new(p-sd*w));R.append(bm.verts.new(p+sd*w));Mid.append(bm.verts.new(p+nn*w*fold))
    for i in range(len(pts)-1):
        v0,v1=s[i]/tot,s[i+1]/tot
        for (a,b,c_,d),(ua,ub) in (((L[i],Mid[i],Mid[i+1],L[i+1]),(0,.5)),((Mid[i],R[i],R[i+1],Mid[i+1]),(.5,1))):
            if (a.co-d.co).length<1e-7 or (b.co-c_.co).length<1e-7:
                vs=[x for x in (a,b,c_,d)];vs=list(dict.fromkeys(vs))
                if len(vs)<3:continue
                fc=bm.faces.new(vs)
            else:fc=bm.faces.new((a,b,c_,d))
            for l in fc.loops:
                q=l.vert;uu=ua if q in (L[i],L[i+1]) else (ub if q in (R[i],R[i+1]) else .5);vv=v0 if q in (L[i],R[i],Mid[i]) else v1
                l[lay].uv=(uu,vv)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,M[mat],grp,keep_uv=True)

def _leafp(name,base,d,n,L,W,M,mat,grp,shape='oval',seg=5,fold=.12,curl=.15,teeth=0):
    """one modelled leaf/leaflet: outline by `shape` (oval, heart, fan, round, lance, pinna), a midrib fold, a slight curl;
    u across, v from the base (0) to the tip (1)"""
    import zlib
    d=Vector(d).normalized();n=Vector(n);s=d.cross(n).normalized();n=s.cross(d).normalized();base=Vector(base)
    rl=_rnd.Random(zlib.crc32(name.encode())).uniform(-.45,.45);n.rotate(Matrix.Rotation(rl,3,d));s=d.cross(n).normalized()   # every leaf rolled a little: no two neighbours lie parallel
    def wid(t):
        if shape=='heart':return (math.sin(math.pi*min(1,t*1.15))**.7)*(1-.35*max(0,1-t*4))   # notched base
        if shape=='fan':return max(.05,t**.8)*(1-max(0,t-.85)*3)
        if shape=='round':return math.sin(math.pi*t)**.55
        if shape=='lance':return math.sin(math.pi*t**.8)**1.1
        return math.sin(math.pi*t)**.8
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');rows=[]
    for i in range(seg+1):
        t=i/seg;w=max(.0004,W*wid(t)/2*(1+(.18*math.sin(t*seg*math.pi*2) if teeth else 0)));c=base+d*L*t-n*curl*L*t*t
        rows.append((bm.verts.new(c-s*w-n*fold*w),bm.verts.new(c+n*fold*w*.2),bm.verts.new(c+s*w-n*fold*w)))
    for i in range(seg):
        a,b=rows[i],rows[i+1]
        for p,q in ((0,1),(1,2)):
            fc=bm.faces.new((a[p],a[q],b[q],b[p]))
            for l,(cc,rr) in zip(fc.loops,((p,i),(q,i),(q,i+1),(p,i+1))):l[lay].uv=((0,.5,1)[cc],rr/seg)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,M[mat],grp,keep_uv=True)

def _tube(name,pts,r0,r1,M,mat,grp,sides=4):
    pts=[Vector(p) for p in pts];bm=bmesh.new();rings=[];prev=None;n=len(pts)
    for i,p in enumerate(pts):
        t=(pts[min(i+1,n-1)]-pts[max(i-1,0)]).normalized();u=(prev-t*prev.dot(t)).normalized() if prev is not None else t.orthogonal().normalized();prev=u;v=t.cross(u)
        r=r0+(r1-r0)*i/(n-1);rings.append([bm.verts.new(p+(u*math.cos(math.tau*k/sides)+v*math.sin(math.tau*k/sides))*r) for k in range(sides)])
    for a,b in zip(rings,rings[1:]):
        for k in range(sides):bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
    for f in bm.faces:f.smooth=True
    return finish(name,bm,M[mat],grp,scale=.05)

def _plant_paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
    """plants under the D2 canopy: a little cooler and darker in the inner, occluded leaves"""
    col=col*(.78+.22*ao[...,None]);return np.clip(col,0,1),np.clip(rough,0,1)
PLANT={'paint':_plant_paint,'grime':.3,'wear':0,'ao_k':.35}

# ---------------- DP08 ferns (three-views: art/references/DP08/prompt.txt) ----------------
def dp08_01(M):
    """鐵線蕨型 (DP08A-cand-3): thin dark stems arching out, each forking into short side stalks with fans of small rounded leaflets"""
    r_=_rnd.Random(8101);_base('DP08_01_base',.06,.05,.012,M,'Body',8102)
    for f in range(10):
        a=math.tau*f/10+r_.uniform(-.25,.25);el=r_.uniform(.9,1.4);L=r_.uniform(.28,.40)
        d0=Vector((math.cos(a)*.55,math.sin(a)*.55,el));path=_curve((math.cos(a)*.01,math.sin(a)*.01,0),d0,L,droop=.35,n=8)
        _tube(f'DP08_01_st{f}',path,.0018,.0008,M,'stem_dark','Body')
        for b in range(7):   # side stalks with a fan of leaflets each
            i=2+b;i=min(i,8);p=path[i];t=(path[min(i+1,8)]-path[i-1]).normalized()
            sd=t.cross(Vector((0,0,1))).normalized()*(1 if b%2 else -1)
            nk=r_.randint(3,4)
            for k in range(nk):   # a fan: the leaflets spread evenly round the stalk end (random directions stacked them)
                fa=(k-(nk-1)/2)*.95;fan=(t*math.cos(fa)+sd*math.sin(fa)).normalized()
                dd=(fan*.8+sd*.45+Vector((0,0,.12+.1*k))).normalized()
                q=p+dd*.002   # the leaflet starts on its stalk
                _leafp(f'DP08_01_l{f}_{b}_{k}',q,dd,(0,0,1),r_.uniform(.014,.02),r_.uniform(.018,.024),M,'leaf','Body',shape='fan',seg=2,fold=.05,curl=.1)
    return dict(PLANT)
def dp08_02(M):
    """細裂蕨 (DP08B-cand-1): a rosette of six arching fronds, each with paired toothed pinnae, and one young fiddlehead"""
    r_=_rnd.Random(8201);_base('DP08_02_base',.06,.06,.014,M,'Body',8202)
    for f in range(6):
        a=math.tau*f/6+r_.uniform(-.2,.2);L=r_.uniform(.40,.48);d0=Vector((math.cos(a)*.45,math.sin(a)*.45,1.))
        path=_curve((math.cos(a)*.012,math.sin(a)*.012,0),d0,L,droop=.55,n=16)
        _tube(f'DP08_02_ra{f}',path,.0025,.001,M,'stem_green','Body')
        for i in range(2,16):
            p=path[i];t=(path[i+1]-path[i-1]).normalized();sd=t.cross(Vector((0,0,1))).normalized();up=sd.cross(t)
            pl=.085*math.sin(math.pi*(i-1)/15.5)**.7
            for sgn in (-1,1):   # the two sides staggered half a step (alternate pinnae do not stack)
                q=p if sgn<0 else p.lerp(path[i+1],.5);dd=(sd*sgn+t*(.4 if sgn<0 else .55)).normalized()
                _leafp(f'DP08_02_p{f}_{i}_{sgn}',q,dd,up,pl,pl*.25,M,'leaf','Body',shape='lance',seg=4,fold=.15,curl=.2,teeth=1)
    coil=[Vector((.0,.0,.0))]+[Vector((math.cos(t)*.012*(1-t/9)+.0,math.sin(t)*.003,.13+math.sin(t)*.012*(1-t/9))) for t in np.linspace(0,8,14)]
    _tube('DP08_02_fiddle',[Vector((0,0,0)),Vector((0,0,.07)),Vector((.002,0,.12))]+coil[1:],.0032,.0016,M,'stem_green','Body',sides=5)
    return dict(PLANT)
def dp08_03(M):
    """梯子蕨 (DP08C-cand-1): a vase of upright narrow fronds, a single row of short rounded leaflets either side"""
    r_=_rnd.Random(8301);_base('DP08_03_base',.05,.045,.014,M,'Body',8302)
    for f in range(10):
        a=math.tau*f/10+r_.uniform(-.2,.2);L=r_.uniform(.32,.46);d0=Vector((math.cos(a)*.22,math.sin(a)*.22,1.))
        path=_curve((math.cos(a)*.01,math.sin(a)*.01,0),d0,L,droop=.12,n=16)
        _tube(f'DP08_03_ra{f}',path,.0022,.0009,M,'stem_dark','Body')
        for i in range(2,17):
            p=path[i];t=(path[min(i+1,16)]-path[i-1]).normalized();sd=t.cross(Vector((math.cos(a),math.sin(a),0))).normalized()
            pl=.030*min(1,math.sin(math.pi*(i-.5)/16.5)**.5+.15)
            for sgn in (-1,1):
                dd=(sd*sgn+t*.25).normalized();_leafp(f'DP08_03_p{f}_{i}_{sgn}',p,dd,Vector((math.cos(a),math.sin(a),.2)),pl,pl*.6,M,'leaf_dark','Body',shape='oval',seg=2,fold=.1,curl=.1)
    return dict(PLANT)

# ---------------- DP09 groundcover (three-views: art/references/DP09/prompt.txt) ----------------
def dp09_01(M):
    """酢漿草 (DP09A-cand-1): thin stems with three folded heart-shaped leaflets each"""
    r_=_rnd.Random(9101);_base('DP09_01_base',.11,.09,.010,M,'Body',9102)
    for s in range(28):
        a=r_.uniform(0,math.tau);rr=math.sqrt(r_.random())*.09;x,y=math.cos(a)*rr,math.sin(a)*rr;h=r_.uniform(.035,.09)*(1-.4*rr/.09)
        top=Vector((x*1.15,y*1.15,h));_tube(f'DP09_01_s{s}',[(x,y,0),(x*1.05,y*1.05,h*.6),top],.0012,.0009,M,'stem_red','Body',sides=3)
        rot=r_.uniform(0,math.tau)
        for k in range(3):
            b=rot+math.tau*k/3;dd=Vector((math.cos(b),math.sin(b),-.25)).normalized()
            _leafp(f'DP09_01_l{s}_{k}',top+dd*.004,dd,(0,0,1),r_.uniform(.026,.036),r_.uniform(.028,.038),M,'leaf' if s%5 else 'leaf_dark','Body',shape='heart',seg=3,fold=.35,curl=.05)
    return dict(PLANT)
def dp09_02(M):
    """幼苗 (DP09B-cand-1): five young seedlings, red-brown stems, two to four small oval leaves"""
    r_=_rnd.Random(9201);_base('DP09_02_base',.12,.08,.012,M,'Body',9202)
    for s,(x,y,h) in enumerate(((-.08,.01,.13),(-.04,-.02,.10),(0,.01,.17),(.045,-.01,.12),(.085,.015,.14))):
        lean=(r_.uniform(-.1,.1),r_.uniform(-.1,.1));top=Vector((x+lean[0]*h,y+lean[1]*h,h))
        _tube(f'DP09_02_s{s}',[(x,y,0),(x+lean[0]*h*.4,y+lean[1]*h*.4,h*.5),top],.0022,.0013,M,'stem_red','Body',sides=5)
        nl=r_.randint(2,4)
        for k in range(nl):
            b=r_.uniform(0,math.tau) if k>1 else (math.pi*k+r_.uniform(-.3,.3));z=h*(1 if k<2 else .65)
            p=Vector((x+lean[0]*z,y+lean[1]*z,z));dd=Vector((math.cos(b),math.sin(b),.35)).normalized()
            _leafp(f'DP09_02_l{s}_{k}',p,dd,(0,0,1),r_.uniform(.05,.07),r_.uniform(.026,.034),M,'leaf_young' if k<2 else 'leaf','Body',shape='oval',seg=5,fold=.15,curl=.2)
    return dict(PLANT)
def dp09_03(M):
    """圓葉地被 (DP09C-cand-1): a low creeping mat of round coin-shaped leaves on short stems"""
    r_=_rnd.Random(9301);_base('DP09_03_base',.15,.12,.008,M,'Body',9302)
    pts=_poisson(r_,52,lambda rg:(lambda a,rr:(math.cos(a)*rr*.14,math.sin(a)*rr*.11))(rg.uniform(0,math.tau),math.sqrt(rg.random())),.018)
    for i,(x,y) in enumerate(pts):
        h=r_.uniform(.02,.045);top=Vector((x,y,h));_tube(f'DP09_03_s{i}',[(x*.9,y*.9,0),top],.0012,.001,M,'stem_green','Body',sides=3)
        b=r_.uniform(0,math.tau);dd=Vector((math.cos(b),math.sin(b),-.1)).normalized();sz=r_.uniform(.03,.042)
        _leafp(f'DP09_03_l{i}',top-dd*sz*.45,dd,(r_.uniform(-.2,.2),r_.uniform(-.2,.2),1),sz,sz*.95,M,'leaf' if i%3 else 'leaf_dark','Body',shape='round',seg=7,fold=.05,curl=-.05)
    return dict(PLANT)
def dp09_04(M):
    """混合地被 (DP09D-cand-2): heart-shaped leaves on thin stems with two tiny ferns and a few round leaves"""
    r_=_rnd.Random(9401);_base('DP09_04_base',.17,.13,.012,M,'Body',9402)
    for i in range(26):   # heart leaves
        a=r_.uniform(0,math.tau);rr=math.sqrt(r_.random())*.13;x,y=math.cos(a)*rr,math.sin(a)*rr*.8;h=r_.uniform(.04,.11)
        top=Vector((x*1.1,y*1.1,h));_tube(f'DP09_04_s{i}',[(x,y,0),(x*1.04,y*1.04,h*.6),top],.0013,.001,M,'stem_green','Body',sides=3)
        b=a+r_.uniform(-.6,.6);dd=Vector((math.cos(b),math.sin(b),.05)).normalized()
        _leafp(f'DP09_04_h{i}',top,dd,(0,0,1),r_.uniform(.035,.05),r_.uniform(.03,.042),M,'leaf' if i%4 else 'leaf_dark','Body',shape='heart',seg=5,fold=.15,curl=.15)
    for f,(x,y) in enumerate(((-.06,.03),(.07,-.02))):   # two tiny ferns
        for g in range(4):
            a=math.tau*g/4+f;path=_curve((x,y,0),(math.cos(a)*.6,math.sin(a)*.6,1),.10,droop=.6,n=6)
            _tube(f'DP09_04_fr{f}_{g}',path,.0012,.0006,M,'stem_green','Body',sides=3)
            for i in range(1,6):
                p=path[i];t=(path[i+1]-path[i-1]).normalized();sd=t.cross(Vector((0,0,1))).normalized()
                for sgn in (-1,1):_leafp(f'DP09_04_fp{f}_{g}_{i}_{sgn}',p,(sd*sgn+t*.4).normalized(),sd.cross(t),.016*(1-i/7),.006,M,'leaf_young','Body',shape='lance',seg=2,fold=.1,curl=.1)
    for i in range(6):   # round leaves low down
        a=r_.uniform(0,math.tau);rr=r_.uniform(.05,.12);x,y=math.cos(a)*rr,math.sin(a)*rr*.8;dd=Vector((math.cos(a),math.sin(a),0))
        _leafp(f'DP09_04_r{i}',(x,y,.003),dd,(0,0,1),.024,.022,M,'leaf_dark','Body',shape='round',seg=4,fold=.05,curl=-.05)
    return dict(PLANT)

# ---------------- DP11 sedges (three-views: art/references/DP11/prompt.txt) ----------------
def _blade(name,root,a,L,W,lean,M,mat,grp,droop=.55,seg=6,twist=0.):
    import zlib
    rl=_rnd.Random(zlib.crc32(name.encode())).uniform(-.5,.5)
    d0=Vector((math.cos(a)*lean,math.sin(a)*lean,1.));path=_curve(root,d0,L,droop=droop,n=seg)
    for i,p in enumerate(path[1:],1):p.z=max(p.z,.003+.002*i)   # a drooping blade lies on the ground, never under it
    up=[Vector((-math.sin(a+rl+twist*i/seg),math.cos(a+rl+twist*i/seg),0)).cross((path[min(i+1,seg)]-path[max(i-1,0)]).normalized()) for i in range(seg+1)]
    up=[u if u.length>1e-6 else Vector((0,0,1)) for u in up]
    widths=[W*(1-(i/seg)**2.2)*(1 if i else .9)+.0004 for i in range(seg+1)];widths[-1]=.0003
    return _strip(name,path,widths,up,M,mat,grp,fold=.25)
def dp11_01(M):
    """小莎草叢 (DP11A-cand-1): many narrow dark blades rising from a tight base and arching out, a few dry tips"""
    r_=_rnd.Random(11101);_base('DP11_01_base',.05,.045,.012,M,'Body',11102)
    for i in range(80):
        a=r_.uniform(0,math.tau);root=(math.cos(a)*r_.uniform(.004,.026),math.sin(a)*r_.uniform(.004,.026),-.004)
        _blade(f'DP11_01_b{i}',root,a,r_.uniform(.20,.36),r_.uniform(.008,.012),r_.uniform(.1,.7),M,'sedge_dry' if i%13==0 else 'sedge','Body',droop=r_.uniform(.35,.75),twist=r_.uniform(-.4,.4))
    return dict(PLANT)
def dp11_02(M):
    """大莎草叢 (DP11B-cand-1): a big fountaining clump, long blades bending down to the ground, dry blades at the base"""
    r_=_rnd.Random(11201);_base('DP11_02_base',.09,.08,.016,M,'Body',11202)
    for i in range(92):
        a=r_.uniform(0,math.tau);root=(math.cos(a)*r_.uniform(.006,.045),math.sin(a)*r_.uniform(.006,.045),-.004)
        dry=i%9==0
        _blade(f'DP11_02_b{i}',root,a,r_.uniform(.42,.60)*(.6 if dry else 1),r_.uniform(.009,.013),r_.uniform(.12,.8),M,'sedge_dry' if dry else 'sedge','Body',droop=r_.uniform(.5,.95),twist=r_.uniform(-.4,.4))
    return dict(PLANT)
def dp11_03(M):
    """穗莎草 (DP11C-cand-2): upright thin blades and five slender stalks carrying small brown seed spikes"""
    r_=_rnd.Random(11301);_base('DP11_03_base',.05,.045,.012,M,'Body',11302)
    for i in range(72):
        a=r_.uniform(0,math.tau);root=(math.cos(a)*r_.uniform(.004,.028),math.sin(a)*r_.uniform(.004,.028),-.004)
        _blade(f'DP11_03_b{i}',root,a,r_.uniform(.24,.38),r_.uniform(.006,.009),r_.uniform(.1,.45),M,'sedge','Body',droop=r_.uniform(.2,.6),twist=r_.uniform(-.3,.3))
    for s in range(5):
        a=math.tau*s/5+r_.uniform(-.3,.3);h=r_.uniform(.36,.44);top=Vector((math.cos(a)*.03,math.sin(a)*.03,h))
        _tube(f'DP11_03_st{s}',[(math.cos(a)*.005,math.sin(a)*.005,0),(math.cos(a)*.015,math.sin(a)*.015,h*.5),top],.0013,.0009,M,'stem_green','Body',sides=4)
        ax=(top-Vector((math.cos(a)*.015,math.sin(a)*.015,h*.5))).normalized()
        _tube(f'DP11_03_sp{s}',[top-ax*.004,top+ax*.010,top+ax*.024,top+ax*.032],.0035,.0012,M,'spike','Body',sides=6)
    return dict(PLANT)

PROPS.update({'DP08_01':dp08_01,'DP08_02':dp08_02,'DP08_03':dp08_03,'DP09_01':dp09_01,'DP09_02':dp09_02,'DP09_03':dp09_03,'DP09_04':dp09_04,
              'DP11_01':dp11_01,'DP11_02':dp11_02,'DP11_03':dp11_03})
