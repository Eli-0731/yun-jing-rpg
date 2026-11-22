# DP20 小型細根網 (six) — exec'd by build_floor.py after floor_items4.py (bark sources, _limb, _centre, _stone, _pad).
# Each root weaves in and out of the soil: its axis rises and dips round the ground line, wet soil heaped over the deepest dips;
# some tips lift out of the ground. One step thinner than DR13 (d2-roots-b): 1–5 cm.

def _root(name,p0,yaw,L,r0,r1,M,grp,seed,curl=.25,tip_up=False,dive=True,pads=1,ds=None,arch=0.):
    """one root from p0 (its start dives into the soil) heading yaw: wandering in the ground plane by `curl`, its height
    weaving between 1 r under and 0.6 r over the ground; tip_up: the last part lifts out; pads: soil heaped over the deepest dips"""
    r_=_rnd.Random(seed);ds=ds or max(.03,min(.07,r0*4));n=max(4,int(L/ds)+1);off=Vector((r_.uniform(0,40),r_.uniform(0,40),0))
    p=Vector((p0[0],p0[1],0));pts=[];y=yaw
    for i in range(n):
        t=i/(n-1);r=r0+(r1-r0)*t
        z=r*(.05+.65*_mn.noise(Vector((t*L/.22,0,0))+off))
        z+=arch*max(0.,math.sin(math.pi*(t-.1)/.8))**1.5 if .1<t<.9 else 0.   # arch: loops up over the other roots (the knot)
        if arch and .1<t<.9:z=max(z,-r*.3)
        if dive and t<.12:z=min(z,-r*(1.1-t*6))
        if tip_up and t>.82:z=max(z,r)+(t-.82)/.18*(.012+r*2.5)
        pts.append(Vector((p.x,p.y,z)))
        y+=curl*_mn.noise(Vector((t*L/.4,5,0))+off)*ds/.1;p=p+Vector((math.cos(y),math.sin(y),0))*L/(n-1)
    _limb(name,pts,r0,r1,M,grp,seed,ends=('tip','tip'),sides=6 if r0>.016 else 5 if r0>.008 else 4,rough=.1,mat='bark_root',bulge=.1)
    dips=sorted(range(2,n-2),key=lambda i:pts[i].z)[:pads]
    for j,i in enumerate(dips):
        r=r0+(r1-r0)*i/(n-1)
        if pts[i].z<-r*.2:_pad(f'{name}_soil{j}',(pts[i].x,pts[i].y,0),r*4+.02,r*3.2+.016,r*.55+.003,M,grp,seed+70+j,segs=12,mat='soil',rings=(.5,1.),noise=.3)
    return pts

def _rootfork(name,p,yaw,L,r,M,grp,r_,depth,maxd,spread=.7,tip_frac=.3):
    pts=_root(name,p,yaw,L,r,max(.002,r*.4),M,grp,r_.randint(0,99999),curl=.3,tip_up=r_.random()<tip_frac,dive=depth==0,pads=1 if r>.006 else 0)
    if depth<maxd:
        for c in range(r_.choice((2,2,3))):
            i=int(len(pts)*r_.uniform(.15,.75));q=pts[i]
            _rootfork(f'{name}_{c}',(q.x,q.y),yaw+r_.choice((-1,1))*r_.uniform(.3,spread),L*r_.uniform(.5,.68),max(.003,r*(1-.6*i/len(pts))*.65),M,grp,r_,depth+1,maxd,spread,tip_frac)

O_ROOT='footprint centre, z = 0 on the ground; the roots weave 1–5 cm in and out of the soil, soil heaped over the dips'
WR=dict(grime=.7,wear=.3,origin_text=O_ROOT)
def dp20_01(M):
    """交錯細根 (DP20A-cand-1): about 1 m, roots 1–3 cm crossing each other half buried, a few tips sticking out"""
    r_=_rnd.Random(20101)
    for i,(x,y,yaw,L,r) in enumerate(((-.45,-.1,.2,.9,.014),(-.4,.15,-.3,.8,.011),(-.2,-.25,.7,.6,.008),(0,.25,-.9,.55,.008),(-.3,0,.05,.7,.006),(.05,-.2,.35,.45,.006))):
        _root(f'DP20_01_r{i}',(x,y),yaw,L,r,r*.35,M,'Body',20110+i,curl=.3,tip_up=i in (1,3,5))
    _centre();return dict(WR)
def dp20_02(M):
    """扇形根網 (DP20B-cand-7): 1.2 m, a net of thin roots fanning out from one 5 cm root"""
    r_=_rnd.Random(20201);pts=_root('DP20_02_main',(-.6,0),0.,.42,.025,.016,M,'Body',20201,curl=.1,pads=2)
    q=pts[-1]
    for i,a in enumerate((-.9,-.65,-.4,-.15,.1,.35,.6,.85)):
        _rootfork(f'DP20_02_f{i}',(q.x,q.y),a,r_.uniform(.5,.7),.009,M,'Body',r_,1,2,spread=.45)
    _centre();return dict(WR)
def dp20_03(M):
    """根結 (DP20C-cand-1): a tangled knot 1.3 m across, roots 1–4 cm looping over each other, moss in the gaps"""
    r_=_rnd.Random(20301)
    for i in range(7):
        a=math.tau*i/7+r_.uniform(-.3,.3);d=r_.uniform(.3,.45)
        _root(f'DP20_03_r{i}',(math.cos(a)*d,math.sin(a)*d),a+math.pi+r_.uniform(-.7,.7),r_.uniform(.75,1.0),r_.uniform(.008,.02),.004,M,'Body',20310+i,curl=1.1,tip_up=i%3==0,arch=r_.uniform(.03,.11))
    for j in range(4):
        a=r_.uniform(0,math.tau);d=r_.uniform(.05,.3);_pad(f'DP20_03_moss{j}',(math.cos(a)*d,math.sin(a)*d,0),r_.uniform(.05,.09),r_.uniform(.04,.07),.018,M,'Body',20350+j,segs=14,depth=.01)
    _centre();return dict(WR)
def dp20_04(M):
    """三股平行根 (DP20D-cand-5): three thin roots 1.5 m lying side by side, twisting a little round each other"""
    for k,(ph,r) in enumerate(((0.,.02),(2.1,.016),(4.2,.013))):
        n=34;pts=[]
        for i in range(n):
            t=i/(n-1);x=-.75+1.5*t;a=ph+t*math.tau*2.2;y=.028*math.cos(a)+.04*math.sin(t*4.1);z=r*(.1+.9*math.sin(a))*.6
            if t<.08 or (k==1 and t>.92):z=min(z,-r*1.1)
            pts.append((x,y,z))
        _limb(f'DP20_04_r{k}',pts,r,r*.45,M,'Body',20410+k,ends=('tip','tip'),sides=6 if r>.016 else 5,rough=.1,mat='bark_root',bulge=.1)
    for j,(x,y) in enumerate(((-.35,.0),(.3,.02))):_pad(f'DP20_04_soil{j}',(x,y,0),.07,.06,.025,M,'Body',20450+j,segs=14,mat='soil',rings=(.5,1.),noise=.3)
    _centre();return dict(WR)
def dp20_05(M):
    """分岔根網 (DP20E-cand-8): 1.7 m, roots splitting again and again into finer roots, half buried"""
    r_=_rnd.Random(20501);_rootfork('DP20_05_r',(-.85,0),0.,1.15,.02,M,'Body',r_,0,3,spread=.8,tip_frac=.25);_centre();return dict(WR)
def dp20_06(M):
    """寬根網卡石 (DP20F-cand-1): 2 × 1 m, many 1–5 cm roots crossing, half buried, small stones caught between them"""
    r_=_rnd.Random(20601)
    for i,(x,y,yaw,L,r) in enumerate(((-1.,-.15,.1,1.9,.024),(-.95,.3,-.25,1.5,.016),(-.8,-.45,.4,1.4,.012),(-.3,.45,-.6,1.,.01),(0,-.5,.8,.9,.009),(-.6,0,-.05,1.3,.008),(.2,.4,-1.2,.7,.006),(-.1,-.1,.5,.8,.006))):
        _root(f'DP20_06_r{i}',(x,y),yaw,L,r,r*.35,M,'Body',20610+i,curl=.35,tip_up=i in (2,5,7))
    for j,(x,y,s) in enumerate(((-.25,.05,.07),(.15,-.12,.05),(.4,.15,.06),(-.55,-.2,.045))):
        _stone(f'DP20_06_st{j}',(x,y),(s,s*.8,s*.6),M,'Body',20650+j,cuts=3,sink=.4,subdiv=3,lump=.1)
    _centre();return dict(WR)

TABLE.update({'DP20_01':('RootNetCrossing',(1.2,.9,.10),'standard'),'DP20_02':('RootNetFan',(1.4,1.2,.10),'standard'),'DP20_03':('RootKnot',(1.6,1.6,.12),'standard'),
 'DP20_04':('RootsParallel',(1.7,.4,.10),'standard'),'DP20_05':('RootNetBranching',(1.95,1.4,.12),'standard'),'DP20_06':('RootNetWideStones',(2.3,1.3,.14),'standard')})
PROPS.update({k:globals()[k.lower()] for k in ('DP20_01','DP20_02','DP20_03','DP20_04','DP20_05','DP20_06')})
