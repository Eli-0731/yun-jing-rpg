# YP07 shapes (the 11/14 120h pack, batch A), read by build_yp.py after yp_items_c.py (same namespace).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.
# The plants are made leaf by leaf (no leaf cards): tubes for the onion leaves, cupped blades for the herb leaves.

def _pot(pid,M,seed,H=.19,RT=.130,RB=.088,chips=()):
    """a hand-made terracotta pot: thick wall, rolled rim, a little out of round; chips: (angle, width, depth) knocked out of the rim.
    Returns the height of the soil in it."""
    RM=(RB+RT)/2
    prof=[(0,.002),(0,RB),(.04,RB+.006),(.5,RM+.007),(.86,RT-.003),(.92,RT+.008),(.97,RT+.011),(1,RT+.006),(1,RT-.006),(.90,RT-.015),(.5,RM-.007),(.10,RB-.008),(.08,.002)]
    o=_lathe(f'{pid}_Pot',prof,((0,0,0),(0,0,H)),M['terracotta'],'Body',NS=30,scale=.3,loop=True)
    for a0,wd,dp in chips:
        for v in o.data.vertices:
            if v.co.z>H-.05:
                r=math.hypot(v.co.x,v.co.y);fl=min(1.,max(0.,1-abs((math.atan2(v.co.y,v.co.x)-a0+math.pi)%math.tau-math.pi)*r/wd)*2.5)
                if fl>0:v.co.z-=dp*fl*min(1.,(v.co.z-(H-.05))/.03)
    jitter(o,.0028,seed,freq=7)
    s=_lathe(f'{pid}_Soil',[(0,RT-.011),(.5,RT-.028),(1,0)],((0,0,H-.036),(0,0,H-.012)),M['soil'],'Body',NS=20,scale=.25);jitter(s,.004,seed+1,freq=30)
    return H-.020
def _pot_paint(col,rough,h,P,onrm,noise,cav,filled,H,RT,seed,crack=None):
    """old terracotta: white lime bloom, a dark damp foot with moss, small pits; crack: (angle at the rim, length) painted and cut into the relief"""
    px,py,pz=P[...,0],P[...,1],P[...,2];pr=np.hypot(px,py);th=np.arctan2(py,px)
    pot=filled*(col[...,0]>col[...,1]*1.35)*(pz<H+.02)*(pr>.05);outer=pot*((px*onrm[...,0]+py*onrm[...,1])>0)
    lime=outer*np.clip((_fb(P,9.,seed,3)-.50)*3.5,0,1)*np.clip((pz-.03)/.06,0,1);col=col*(1-.42*lime[...,None])+lime[...,None]*.42*np.array([.74,.70,.62]);rough=np.clip(rough+.05*lime,0,1)
    d1,d2,cid,_,_=_wor(P,80.,seed+1);pit=pot*(cid>.7)*np.clip(1-d1/.33,0,1);h-=.0010*pit;col=col*(1-.16*pit[...,None])
    h+=outer*.0012*(_fb(P,(18.,18.,70.),seed+2,2)-.5)                                    # finger ridges left from shaping
    damp=outer*np.clip((.05-pz)/.04,0,1);col=col*(1-.30*damp[...,None])
    if crack:
        a0,ln=crack;ck=outer*np.clip(1-np.abs((th-a0-.05*np.sin(pz*60)+np.pi)%(2*np.pi)-np.pi)*pr/.0028,0,1)*np.clip((pz-(H-ln))/.02,0,1);h-=.003*ck;col=col*(1-.7*ck[...,None])
    return _moss_low(col,rough,P,onrm,noise,cav,outer,h=.07,amt=.6,soil=.02)
def _stemf(name,b,a,Ht,lean,r0,mat,bow=0.):
    """a herb stem from b, leaning toward angle a; returns the point at u (0..1) along it"""
    d=Vector((math.cos(a),math.sin(a),0));s=Vector((-d.y,d.x,0));Z=Vector((0,0,1))
    f=lambda u:Vector(b)+d*lean*Ht*u**1.4+s*bow*Ht*math.sin(math.pi*u)+Z*Ht*u
    _taper(name,[f(u) for u in (0,.3,.6,.85,1)],[r0,r0*.9,r0*.72,r0*.5,r0*.3],mat,'Body',sides=4,scale=.08);return f
def _leaf_oval(u,tooth=0.,n=38.):
    if u<.10:return .10
    v=(u-.10)/.90;return (.10+.90*math.sin(math.pi*min(1.,v*1.03))**.62)*(1+tooth*math.sin(u*n))*(1 if u<.985 else .15)

# ---------------- YP07_01 potted spring onions (cand-4) ----------------
def YP07_01(M):
    """a terracotta pot with three clumps of spring onions: every leaf a hollow tube rising from a pale sheath, a few bent over"""
    rr=random.Random(int(__import__('os').environ.get('YP_SEED',6701)));H=.19;RT=.130;zs=_pot('YP07_01',M,6702,H,RT,chips=((2.2,.03,.010),))
    for c in range(6):
        ca=math.tau*c/5+rr.uniform(-.2,.2);cr=rr.uniform(.058,.070) if c else 0.;cb=Vector((cr*math.cos(ca),cr*math.sin(ca),zs))
        for k in range(rr.randint(4,5)):
            a=math.tau*k/5+rr.uniform(-.4,.4);off=Vector((math.cos(a),math.sin(a),0));L=rr.uniform(.20,.30);lean=rr.uniform(.06,.30);bend=rr.random()<.2;r=rr.uniform(.0050,.0068)
            p0=cb+off*rr.uniform(.015,.030)+Vector((0,0,-.008-.0037*k-.0011*c-rr.uniform(0,.003)));ro=rr.uniform(0,math.tau)
            _taper(f'YP07_01_W{c}{k}',[p0,p0+off*lean*.012+Vector((0,0,.035)),p0+off*lean*.02+Vector((0,0,.062))],[.0012,r*1.4,r*1.22],M['onion_white'],'Body',sides=6,scale=.06,up=(math.cos(ro+.55),math.sin(ro+.55),.3))
            q0=p0+off*lean*.019+Vector((0,0,.052+.0013*k));tip=q0+off*(lean*L+(L*.20 if bend else 0))+Vector((0,0,L*(.88 if bend else 1.)))
            pts=[q0,q0+off*lean*L*.25+Vector((0,0,L*.35)),q0+off*lean*L*.62+Vector((0,0,L*.72)),q0+off*(lean*L*.9+(L*.07 if bend else 0))+Vector((0,0,L*(.90 if bend else .93))),tip]
            _taper(f'YP07_01_L{c}{k}',pts,[r,r*.95,r*.74,r*.45,.0008],M['scallion'],'Body',sides=5,scale=.06,up=(math.cos(ro),math.sin(ro),.3))
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);h=np.zeros(P.shape[:2],np.float32)
        col,rough=_pot_paint(col,rough,h,P,onrm,noise,cav,filled,H,RT,6710,crack=(-1.1,.09))
        lf=filled*(col[...,1]>col[...,0]*1.25)*(P[...,2]>H);tipy=lf*np.clip((P[...,2]-.40)/.08,0,1)*np.clip(.3+noise,0,1);col=col*(1-.4*tipy[...,None])+tipy[...,None]*.4*np.array([.62,.58,.30])   # the highest tips yellowing
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.7,'grime':.8,'ao_k':.45,'uv_angle':60,'collision_box':((.28,.28,.20),(0,0,.10)),
            'notes':['a thick hand-made terracotta pot (rolled rim, out of round, one chip in the rim), soil mounded inside','six clumps of spring onions, every leaf a five-sided tube rising from a pale sheath, about one in four bent over; no leaf cards',
                     'painted, with the relief also in the normal map: lime bloom, pits, finger ridges, a crack down from the rim, the damp foot with moss; the highest leaf tips yellowing']}
PROPS['YP07_01']=YP07_01

# ---------------- YP07_02 broad-leaved herb in a small wooden tub (cand-4) ----------------
def YP07_02(M):
    """a small coopered tub (twelve staves, two split-bamboo hoops) with a bushy broad-leaved herb: nine stems, the
    leaves in opposite pairs turning a quarter at every node, each leaf a cupped toothed blade."""
    rr=random.Random(int(__import__('os').environ.get('YP_SEED',6725)));H=.20;R0=.112;R1=.132;T=.012;N=12;rw=lambda z:R0+(R1-R0)*z/H
    st=_staves('YP07_02_Stave',(0,0,0),[(0,R0),(H,R1)],T,N,.010,M['cedar'],'Body',rows=4)
    for k,o in enumerate(st):o.data.transform(Matrix.Translation((0,0,rr.uniform(-.006,.004))))
    _chip_staves(st,rr,p=.10)
    for q,(z0,z1) in enumerate(((.045,.063),(.130,.148))):
        zm=(z0+z1)/2;_ring_band(f'YP07_02_Hoop{q}',(0,0,0),rw(zm)+.0045,rw(zm)-.001,z0,z1,M['bamboo_split'],'Body',NS=24,scale=.3)
        a=1.9+q*1.3;c=Vector((math.cos(a),math.sin(a),0))*(rw(zm)+.003)+Vector((0,0,zm))
        for j in range(3):_ring(f'YP07_02_HoopTie{q}{j}',c+Vector((-math.sin(a),math.cos(a),0))*(.006*(j-1)),(-math.sin(a),math.cos(a),0),.0125,.0022,M['cord_dark'],'Body',n=9)   # the hoop ends lashed together
    _lathe('YP07_02_Bottom',[(0,R0-.004),(1,rw(.03)-.004)],((0,0,.016),(0,0,.030)),M['cedar_b'],'Body',NS=24)
    s=_lathe('YP07_02_Soil',[(0,rw(.16)-T+.002),(.5,rw(.17)-T-.012),(1,0)],((0,0,H-.040),(0,0,H-.014)),M['soil'],'Body',NS=20,scale=.25);jitter(s,.004,6722,freq=30);zs=H-.022
    for k in range(13):
        a=math.tau*k/12*2.+rr.uniform(-.3,.3) if k else 0.;cr=rr.uniform(.03,.085) if k else 0.;Ht=rr.uniform(.15,.24) if k else .26
        f=_stemf(f'YP07_02_Stem{k}',(cr*math.cos(a),cr*math.sin(a),zs-.01),a,Ht,rr.uniform(.25,.55) if k else .05,.0036,M['vine'],bow=rr.uniform(-.08,.08));a0=rr.uniform(0,math.tau);nn=4 if Ht>.19 else 3
        for i in range(nn):
            u=.27+.65*i/(nn-1)+rr.uniform(-.04,.04);sz=(1.0-.35*(i/(nn-1)))*rr.uniform(.85,1.1)
            for j in range(2):
                la=a0+i*math.pi/2+j*math.pi+rr.uniform(-.25,.25);L=.098*sz
                la_=(math.cos(la),math.sin(la));_blade(f'YP07_02_L{k}{i}{j}',f(u)+Vector((0,0,.006*j-.003+(.008 if (k,i,j)==(4,2,1) else 0))),la_,L,L*rr.uniform(.62,.74),rr.uniform(.70,1.35),rr.uniform(.15,.7),lambda u_:_leaf_oval(u_,.09),M['herb'],'Body',nu=6,nv=2,cup=rr.uniform(.15,.35),twist=rr.uniform(-.4,.4))
        for j in range(4):   # the young leaves at the top
            la=a0+j*math.pi/2+.6;L=.034*rr.uniform(.8,1.1);_blade(f'YP07_02_T{k}{j}',f(.97),(math.cos(la),math.sin(la)),L,L*.6,rr.uniform(.45,.8),.2,lambda u_:_leaf_oval(u_,.06),M['herb'],'Body',nu=4,nv=2,cup=.35)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];pr=np.hypot(px,py);h=np.zeros(pr.shape,np.float32)
        wd=filled*(pz<H+.01)*(pr>.09)*(np.abs(onrm[...,2])<.6)*(col[...,0]>col[...,2]*1.3)*(col[...,0]>col[...,1]*1.15)
        col,rough=_wood_age(col,rough,h,P,wd,2,6730,edge,grey=.45,stain=.25)
        wet=wd*np.clip((.07-pz)/.06,0,1);col=col*(1-.30*wet[...,None])
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,wd,h=.09,amt=.6,soil=.02)
        lf=filled*(col[...,1]>col[...,0]*1.2)*(pz>H-.02);vy=lf*np.clip((_fb(P,14.,6731,2)-.55)*4,0,1);col=col*(1-.30*vy[...,None])+vy[...,None]*.30*np.array([.55,.60,.22])   # some leaves paler, yellow-green
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.7,'grime':.8,'ao_k':.45,'uv_angle':60,'collision_box':((.28,.28,.21),(0,0,.105)),
            'notes':['a small coopered tub: twelve staves (tops uneven, some chipped), two split-bamboo hoops with their ends lashed, a bottom board, soil mounded inside',
                     'thirteen stems; the leaves stand in opposite pairs, turned a quarter at each node, every leaf a cupped toothed blade (about 140 leaves), four young leaves at each top; no leaf cards',
                     'painted, with the relief also in the normal map: grey weathered staves with checks, a damp mossy foot; some leaves yellow-green']}
PROPS['YP07_02']=YP07_02

# ---------------- YP07_03 small flowering herb in a chipped pot (cand-4) ----------------
def YP07_03(M):
    """a terracotta pot with a piece broken out of the rim; a fine-leaved herb in flower: fourteen thin stems, small
    leaves in pairs, a short spike of small pale purple flowers at the top of each."""
    rr=random.Random(6741);H=.18;RT=.125;zs=_pot('YP07_03',M,6742,H,RT,RB=.090,chips=((-1.9,.050,.024),(.8,.025,.008)))
    for k in range(14):
        a=math.tau*k/13+rr.uniform(-.3,.3) if k else 0.;cr=rr.uniform(.03,.08) if k else 0.;Ht=rr.uniform(.13,.22)
        f=_stemf(f'YP07_03_Stem{k}',(cr*math.cos(a),cr*math.sin(a),zs-.01),a,Ht,rr.uniform(.3,.7) if k else .1,.0022,M['vine'],bow=rr.uniform(-.1,.1));a0=rr.uniform(0,math.tau)
        for i in range(5):
            u=.18+.58*i/4
            for j in range(2):
                la=a0+i*math.pi/2+j*math.pi+rr.uniform(-.3,.3);L=.034*rr.uniform(.75,1.1)*(1-.25*i/4)
                _blade(f'YP07_03_L{k}{i}{j}',f(u),(math.cos(la),math.sin(la)),L,L*.55,rr.uniform(.9,1.3),rr.uniform(.2,.5),lambda u_:_leaf_oval(u_),M['herb_dark'],'Body',nu=4,nv=2,cup=.3)
        for i in range(7):   # the flower spike: small buds round the top of the stem, the lowest open widest
            u=.80+.20*i/6;la=a0+i*2.4;p=f(u)+Vector((math.cos(la),math.sin(la),0))*.0035;r=.0062*(1-.45*i/6)*rr.uniform(.85,1.1);d=Vector((math.cos(la)*.6,math.sin(la)*.6,.8)).normalized()
            _taper(f'YP07_03_F{k}{i}',[p-d*r*.7,p,p+d*r*1.1],[.0012,r,.0010],M['petal'],'Body',sides=5,scale=.05)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);h=np.zeros(P.shape[:2],np.float32)
        col,rough=_pot_paint(col,rough,h,P,onrm,noise,cav,filled,H,RT,6750,crack=(-1.55,.12))
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.7,'grime':.8,'ao_k':.45,'uv_angle':60,'collision_box':((.27,.27,.19),(0,0,.095)),
            'notes':['a thick hand-made terracotta pot with a piece broken out of the rim and a smaller chip, soil mounded inside','fourteen thin stems, small leaves in opposite pairs (140 leaves), a spike of seven small pale purple buds on each stem; no leaf cards',
                     'painted, with the relief also in the normal map: lime bloom, pits, finger ridges, a crack running down from the broken place, the damp foot with moss']}
PROPS['YP07_03']=YP07_03
