# DP20 小型細根網 (six) — exec'd by build_floor.py after floor_items4.py (bark sources, _limb, _centre, _stone, _pad).
# A low sheet of wet soil under each net; each root weaves in and out of it, wet soil heaped over the deepest dips, fine rootlets off the sides;
# some tips lift out of the ground. One step thinner than DR13 (d2-roots-b): 1–5 cm.

def _rootsoil_src(S):
    """the soil under a root net: mid wet brown with a painted net of fine rootlets (
    drawn as wandering, thinning, splitting strokes and raised in the normal map) and a few olive moss flecks; the modelled roots lie over it"""
    K.rng=np.random.default_rng(2001)
    base=lerp((.12,.088,.06),(.26,.19,.125),np.clip(.5+.8*(fbm(4,3)-.5),0,1));net=np.zeros((K.R,K.R),np.float32)
    rng=np.random.default_rng(2002);RR=K.R
    def stamp(x,y,ww):   # one soft disc, wrapping round the tile
        r=int(ww)+2;ix=np.arange(int(x)-r,int(x)+r+1);iy=np.arange(int(y)-r,int(y)+r+1)
        d=np.sqrt((ix[None,:]-x)**2+(iy[:,None]-y)**2);v=np.clip(1-d/max(ww,.6),0,1)**.6
        ys,xs=np.ix_(iy%RR,ix%RR);net[ys,xs]=np.maximum(net[ys,xs],v)
    def walk(x,y,a,ww,L,depth):   # a rootlet: wanders, thins, now and then splits
        n=int(L/1.5)
        for s in range(n):
            t=s/n;w_=ww*(1-.75*t);stamp(x,y,w_);a+=rng.normal(0,.13);x+=math.cos(a)*1.5;y+=math.sin(a)*1.5
            if depth<3 and rng.random()<.045:walk(x,y,a+rng.choice((-1,1))*rng.uniform(.5,1.1),w_*.7,L*.45*(1-t)+25,depth+1)
    for i in range(55):walk(rng.uniform(0,RR),rng.uniform(0,RR),math.pi/2*rng.choice((-1,1))+rng.normal(0,.5),rng.uniform(3.5,7.5),rng.uniform(350,650),0)   # mostly along V
    tone=.8+.4*fbm(12,2);mf=np.clip((fbm(7,3)-.64)*5,0,1)*(1-net)
    col=base*(1-net[...,None])+net[...,None]*np.array([.42,.35,.27])*tone[...,None]
    col=col*(1-mf[...,None])+mf[...,None]*np.array([.15,.17,.07])
    S['rootsoil']=(col,1.3*net+.5*fbm(30,2)+.4*mf,2.2,.85,0,0)
SRC_HOOKS.append(_rootsoil_src)

_GZ=[None]   # height of the soil sheet under the roots (set by _sheet); the roots and pads follow it
def _gz(x,y):return _GZ[0](x,y) if _GZ[0] else 0.

def _sheet(name,cx,cy,rx,ry,h,M,grp,seed,segs=30,depth=.012):
    """the root mat's soil: a low irregular sheet of wet soil with a ragged outline, its rim on z = 0 and a skirt under the ground;
    sets _GZ so the roots lying on it follow its surface"""
    r_=_rnd.Random(seed);ph=[r_.uniform(0,6.3) for _ in range(6)];off=Vector((ph[3],ph[4],ph[5]))*7
    def rr(th):return 1+.3*(.5*math.sin(2*th+ph[0])+.3*math.sin(3*th+ph[1])+.2*math.sin(7*th+ph[2]))
    def hz(x,y):
        dx,dy=(x-cx)/rx,(y-cy)/ry;f=math.hypot(dx,dy)/rr(math.atan2(dy,dx))
        return h*max(0.,1-f*f)**.5*(1+.45*_mn.noise(Vector((x*5,y*5,0))+off)) if f<1 else 0.
    bm=bmesh.new();FR=(.2,.42,.62,.78,.9,1.);rows=[];top=bm.verts.new((cx,cy,hz(cx,cy)))
    for f in FR:
        row=[]
        for k in range(segs):
            th=math.tau*k/segs;s=rr(th)*f*(1+(.06*r_.uniform(-1,1) if f==1 else 0));x,y=cx+math.cos(th)*rx*s,cy+math.sin(th)*ry*s
            row.append(bm.verts.new((x,y,hz(x,y) if f<1 else 0.)))
        rows.append(row)
    for k in range(segs):
        k1=(k+1)%segs;bm.faces.new((top,rows[0][k],rows[0][k1]))
        for i in range(len(rows)-1):bm.faces.new((rows[i][k],rows[i+1][k],rows[i+1][k1],rows[i][k1]))
    sk=[bm.verts.new((cx+(v.co.x-cx)*.95,cy+(v.co.y-cy)*.95,-depth)) for v in rows[-1]];bot=bm.verts.new((cx,cy,-depth))
    for k in range(segs):
        k1=(k+1)%segs;bm.faces.new((rows[-1][k1],rows[-1][k],sk[k],sk[k1]));bm.faces.new((sk[k1],sk[k],bot))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for fc in bm.faces:fc.smooth=True
    _GZ[0]=hz;return finish(name,bm,M['rootsoil'],grp,scale=.7)

def _mosses(name,pts,M,grp,seed):
    """moss patches lying on the soil sheet"""
    for j,(x,y,rx,ry) in enumerate(pts):_pad(f'{name}_moss{j}',(x,y,_gz(x,y)),rx,ry,.012,M,grp,seed+j,segs=14,depth=.008,noise=.35)

def _hairs(name,pts,r0,r1,M,grp,seed,n,L=(.05,.13)):
    """fine rootlets off a root: short thin roots leaving its sides, lying on the soil, a little curly"""
    r_=_rnd.Random(seed)
    for j in range(n):
        i=r_.randint(1,len(pts)-2);q=pts[i];d=pts[i+1]-pts[i-1];a=math.atan2(d.y,d.x)+r_.choice((-1,1))*r_.uniform(.5,1.3)
        Lh=r_.uniform(*L);rh=max(.0018,min(.0045,(r0+(r1-r0)*i/(len(pts)-1))*.35));p=Vector((q.x,q.y,0));ps=[];dz=q.z-_gz(q.x,q.y)
        for k in range(4):
            t=k/3;ps.append(Vector((p.x,p.y,_gz(p.x,p.y)+rh*(.1+.5*r_.random())+dz*(1-t)**2)))
            a+=r_.uniform(-.6,.6);p=p+Vector((math.cos(a),math.sin(a),0))*Lh/3
        _limb(f'{name}_h{j}',ps,rh,rh*.45,M,grp,seed+300+j,ends=('tip','tip'),sides=4,rough=.08,mat='bark',bulge=.05)

def _root(name,p0,yaw,L,r0,r1,M,grp,seed,curl=.25,tip_up=False,dive=True,pads=1,ds=None,arch=0.,hairs=0):
    """one root from p0 (its start dives into the soil) heading yaw: wandering in the ground plane by `curl`, its height
    weaving between 1 r under and 0.6 r over the soil sheet; tip_up: the last part lifts out; pads: soil heaped over the deepest dips;
    hairs: fine rootlets off its sides"""
    r_=_rnd.Random(seed);ds=ds or max(.03,min(.07,r0*4));n=max(4,int(L/ds)+1);off=Vector((r_.uniform(0,40),r_.uniform(0,40),0))
    p=Vector((p0[0],p0[1],0));pts=[];rel=[];y=yaw
    for i in range(n):
        t=i/(n-1);r=r0+(r1-r0)*t
        z=r*(.05+.65*_mn.noise(Vector((t*L/.22,0,0))+off))
        z+=arch*max(0.,math.sin(math.pi*(t-.1)/.8))**1.5 if .1<t<.9 else 0.   # arch: loops up over the other roots (the knot)
        if arch and .1<t<.9:z=max(z,-r*.3)
        if dive and t<.12:z=min(z,-r*(1.1-t*6))
        if tip_up and t>.82:z=max(z,r)+(t-.82)/.18*(.012+r*2.5)
        rel.append(z);pts.append(Vector((p.x,p.y,z+_gz(p.x,p.y))))
        y+=curl*_mn.noise(Vector((t*L/.4,5,0))+off)*ds/.1;p=p+Vector((math.cos(y),math.sin(y),0))*L/(n-1)
    _limb(name,pts,r0,r1,M,grp,seed,ends=('tip','tip'),sides=6 if r0>.016 else 5 if r0>.008 else 4,rough=.1,mat='bark',bulge=.1)
    dips=sorted(range(2,n-2),key=lambda i:rel[i])[:pads]
    for j,i in enumerate(dips):
        r=r0+(r1-r0)*i/(n-1)
        if rel[i]<-r*.2:_pad(f'{name}_soil{j}',(pts[i].x,pts[i].y,_gz(pts[i].x,pts[i].y)),r*4+.02,r*3.2+.016,r*.55+.003,M,grp,seed+70+j,segs=10,mat='rootsoil',rings=(.5,1.),noise=.3)
    if hairs:_hairs(name,pts,r0,r1,M,grp,seed,hairs)
    return pts

def _rootfork(name,p,yaw,L,r,M,grp,r_,depth,maxd,spread=.7,tip_frac=.3,hairs=0):
    pts=_root(name,p,yaw,L,r,max(.002,r*.4),M,grp,r_.randint(0,99999),curl=.3,tip_up=r_.random()<tip_frac,dive=depth==0,pads=1 if r>.009 else 0,hairs=hairs if depth==maxd else 0)
    if depth<maxd:
        for c in range(r_.choice((2,2,3))):
            i=int(len(pts)*r_.uniform(.15,.75));q=pts[i]
            _rootfork(f'{name}_{c}',(q.x,q.y),yaw+r_.choice((-1,1))*r_.uniform(.3,spread),L*r_.uniform(.5,.68),max(.003,r*(1-.6*i/len(pts))*.65),M,grp,r_,depth+1,maxd,spread,tip_frac,hairs)

def _thin(name,r_,n,box,M,seed,hairs=2):
    """extra thin roots criss-crossing the mat"""
    for i in range(n):
        x,y=r_.uniform(box[0],box[1]),r_.uniform(box[2],box[3])
        _root(f'{name}_t{i}',(x,y),r_.uniform(-math.pi,math.pi),r_.uniform(.3,.6),r_.uniform(.004,.007),.002,M,'Body',seed+i,curl=.5,tip_up=r_.random()<.25,pads=0,hairs=hairs)

O_ROOT='footprint centre, z = 0 on the ground; a low sheet of wet soil (up to 2 cm), the roots weave 1–5 cm in and out of it, moss patches on it'
WR=dict(grime=.7,wear=.3,origin_text=O_ROOT)
def dp20_01(M):
    """交錯細根 (DP20A-cand-1): about 1 m, roots 1–3 cm crossing each other half buried, a few tips sticking out"""
    r_=_rnd.Random(20101);_sheet('DP20_01_soil',0,0,.5,.36,.012,M,'Body',20100)
    for i,(x,y,yaw,L,r) in enumerate(((-.45,-.1,.2,.9,.014),(-.4,.15,-.3,.8,.011),(-.2,-.25,.7,.6,.008),(0,.25,-.9,.55,.008),(-.3,0,.05,.7,.006),(.05,-.2,.35,.45,.006))):
        _root(f'DP20_01_r{i}',(x,y),yaw,L,r,r*.35,M,'Body',20110+i,curl=.3,tip_up=i in (1,3,5),hairs=4 if r>.007 else 2)
    _thin('DP20_01',r_,5,(-.4,.3,-.3,.3),M,20130)
    _mosses('DP20_01',((-.25,.12,.09,.06),(.18,-.1,.07,.05),(.3,.18,.05,.04)),M,'Body',20160)
    _centre();return dict(WR)
def dp20_02(M):
    """扇形根網 (DP20B-cand-7): 1.2 m, a net of thin roots fanning out from one 5 cm root"""
    r_=_rnd.Random(20201);_sheet('DP20_02_soil',-.05,0,.6,.5,.014,M,'Body',20200);pts=_root('DP20_02_main',(-.6,0),0.,.42,.025,.016,M,'Body',20201,curl=.1,pads=1,hairs=0)
    q=pts[-1]
    for i,a in enumerate((-.9,-.65,-.4,-.15,.1,.35,.6,.85)):
        _rootfork(f'DP20_02_f{i}',(q.x,q.y),a,r_.uniform(.5,.7),.009,M,'Body',r_,1,2,spread=.45,hairs=0)
    _mosses('DP20_02',((-.35,.2,.1,.07),(.1,-.3,.08,.05),(.25,.25,.06,.05)),M,'Body',20260)
    _centre();return dict(WR)
def dp20_03(M):
    """根結 (DP20C-cand-1): a tangled knot 1.3 m across, roots 1–4 cm looping over each other, moss in the gaps"""
    r_=_rnd.Random(20301);_sheet('DP20_03_soil',0,0,.55,.55,.015,M,'Body',20300)
    for i in range(7):
        a=math.tau*i/7+r_.uniform(-.3,.3);d=r_.uniform(.3,.45)
        _root(f'DP20_03_r{i}',(math.cos(a)*d,math.sin(a)*d),a+math.pi+r_.uniform(-.7,.7),r_.uniform(.75,1.0),r_.uniform(.008,.02),.004,M,'Body',20310+i,curl=1.1,tip_up=i%3==0,arch=r_.uniform(.03,.11),hairs=2)
    _thin('DP20_03',r_,4,(-.35,.35,-.35,.35),M,20330)
    for j in range(4):
        a=r_.uniform(0,math.tau);d=r_.uniform(.05,.3);x,y=math.cos(a)*d,math.sin(a)*d;_pad(f'DP20_03_moss{j}',(x,y,_gz(x,y)),r_.uniform(.05,.09),r_.uniform(.04,.07),.018,M,'Body',20350+j,segs=14,depth=.01)
    _centre();return dict(WR)
def dp20_04(M):
    """三股平行根 (DP20D-cand-5): three thin roots 1.5 m lying side by side, twisting a little round each other"""
    r_=_rnd.Random(20401);_sheet('DP20_04_soil',0,.01,.74,.15,.01,M,'Body',20400,segs=34)
    for k,(ph,r) in enumerate(((0.,.02),(2.1,.016),(4.2,.013))):
        n=34;pts=[]
        for i in range(n):
            t=i/(n-1);x=-.75+1.5*t;a=ph+t*math.tau*2.2;y=.028*math.cos(a)+.04*math.sin(t*4.1);z=r*(.1+.9*math.sin(a))*.6
            if t<.08 or (k==1 and t>.92):z=min(z,-r*1.1)
            pts.append(Vector((x,y,z+_gz(x,y))))
        _limb(f'DP20_04_r{k}',pts,r,r*.45,M,'Body',20410+k,ends=('tip','tip'),sides=6 if r>.016 else 5,rough=.1,mat='bark',bulge=.1)
        _hairs(f'DP20_04_r{k}',pts,r,r*.45,M,'Body',20420+k,7,L=(.05,.11))
    for j,(x,y) in enumerate(((-.35,.0),(.3,.02))):_pad(f'DP20_04_soil{j}',(x,y,_gz(x,y)),.07,.06,.025,M,'Body',20450+j,segs=12,mat='rootsoil',rings=(.5,1.),noise=.3)
    _mosses('DP20_04',((-.6,-.06,.06,.04),(.55,.07,.05,.035)),M,'Body',20460)
    _centre();return dict(WR)
def dp20_05(M):
    """分岔根網 (DP20E-cand-8): 1.7 m, roots splitting again and again into finer roots, half buried"""
    r_=_rnd.Random(20501);_sheet('DP20_05_soil',-.05,0,.78,.48,.013,M,'Body',20500)
    _rootfork('DP20_05_r',(-.85,0),0.,1.15,.02,M,'Body',r_,0,3,spread=.8,tip_frac=.25,hairs=1)
    _mosses('DP20_05',((-.4,.15,.09,.06),(.2,-.2,.07,.05),(.45,.2,.06,.04)),M,'Body',20560)
    _centre();return dict(WR)
def dp20_06(M):
    """寬根網卡石 (DP20F-cand-1): 2 × 1 m, many 1–5 cm roots crossing, half buried, small stones caught between them"""
    r_=_rnd.Random(20601);_sheet('DP20_06_soil',-.05,0,.95,.52,.015,M,'Body',20600,segs=30)
    for i,(x,y,yaw,L,r) in enumerate(((-1.,-.15,.1,1.9,.024),(-.95,.3,-.25,1.5,.016),(-.8,-.45,.4,1.4,.012),(-.3,.45,-.6,1.,.01),(0,-.5,.8,.9,.009),(-.6,0,-.05,1.3,.008),(.2,.4,-1.2,.7,.006),(-.1,-.1,.5,.8,.006))):
        _root(f'DP20_06_r{i}',(x,y),yaw,L,r,r*.35,M,'Body',20610+i,curl=.35,tip_up=i in (2,5,7),hairs=1,pads=1 if r>.012 else 0)
    _thin('DP20_06',r_,3,(-.8,.6,-.35,.35),M,20630,hairs=0)
    for j,(x,y,s) in enumerate(((-.25,.05,.07),(.15,-.12,.05),(.4,.15,.06),(-.55,-.2,.045))):
        _stone(f'DP20_06_st{j}',(x,y),(s,s*.8,s*.6),M,'Body',20650+j,cuts=3,sink=.4,subdiv=2,lump=.1)
    _mosses('DP20_06',((-.7,.2,.12,.07),(-.1,.3,.08,.05),(.55,-.2,.1,.06)),M,'Body',20670)
    _centre();return dict(WR)

TABLE.update({'DP20_01':('RootNetCrossing',(1.2,.9,.10),'standard'),'DP20_02':('RootNetFan',(1.4,1.2,.10),'standard'),'DP20_03':('RootKnot',(1.6,1.6,.12),'standard'),
 'DP20_04':('RootsParallel',(1.7,.4,.10),'standard'),'DP20_05':('RootNetBranching',(1.95,1.4,.12),'standard'),'DP20_06':('RootNetWideStones',(2.3,1.3,.14),'standard')})
PROPS.update({k:globals()[k.lower()] for k in ('DP20_01','DP20_02','DP20_03','DP20_04','DP20_05','DP20_06')})
