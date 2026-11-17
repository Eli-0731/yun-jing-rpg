# YP01 shapes (the 11/14 120h pack, batch A), read by build_yp.py after yp_items_f.py (same namespace).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.
# The bed and the crops are separate models so the crops can be changed: YP01_01 is the earth (three bare ridges),
# YP01_02 / _03 / _04 are one row of a crop each, as long as a ridge, with the origin on the ground under the ridge line.
# Each crop row carries its own hilled-up soil, a little larger than a bare ridge, so it covers the ridge it is put on.

YP01_CX=(-.62,0.,.62);YP01_RW=.27;YP01_RH=.120;YP01_FUR=.032
def _yp01_soil_paint(col,rough,P,onrm,noise,mid,filled,seed):
    pz=P[...,2];soil=filled*(mid>.5)
    fur=soil*np.clip((.085-pz)/.04,0,1)*np.clip(onrm[...,2],0,1);col=col*(1-.22*soil[...,None])       # the trodden furrows and the rim: drier and paler
    col=col*(1-fur[...,None])+fur[...,None]*(col*1.30+np.array([.030,.024,.014]));rough=np.clip(rough+.05*fur,0,1)
    top=soil*np.clip((pz-.125)/.04,0,1)*np.clip((noise-.3)*2,0,1);col=col*(1-.18*top[...,None]);rough=np.clip(rough-.10*top,0,1)   # freshly worked ridge tops: darker, damp
    return col,rough,soil
def _yp01_cap(pid,M,seed):
    """the hilled-up soil of one crop row: a ridge 0.66 × 2.56 m, 15 mm higher and 3 cm wider each side than a bare ridge"""
    r_=random.Random(seed);ph=[r_.uniform(0,6.28) for _ in range(4)];RWc=YP01_RW+.03;RHc=YP01_RH+.015
    def zf(x,y):
        t=min(1.,abs(x)/RWc);return YP01_FUR+(1-t**2.3)*(RHc+.010*math.sin(y*4.7+ph[0]))+.008*math.sin(x*23+ph[1])*math.sin(y*19+ph[2])+.005*math.sin(x*47+y*31+ph[3])
    _earth(f'{pid}_Soil',.66,2.56,zf,M['soil'],'Body',NX=12,NY=64,scale=.5,p=5.,wob=.02,seed=seed);M['soil']['mid']=1.
    return zf

# ---------------- YP01_01 the bed: 2 × 3 m of earth with three bare ridges (cand-4) ----------------
def YP01_01(M):
    """one piece of earth 2.0 × 3.0 m: three rounded ridges along its length, trodden furrows between them, the rim
    sloping raggedly down to the ground; small stones and weeds along the rim and in the furrows (Detail groups)."""
    rr=random.Random(7101);W,D=2.0,3.0;ph=[rr.uniform(0,6.28) for _ in range(8)]
    def zf(x,y):
        ry=max(0.,min(1.,(D/2-.30-abs(y))/.16));ry=ry*ry*(3-2*ry);h=0.
        for k,c in enumerate(YP01_CX):
            t=abs(x-c-.006*math.sin(y*3.1+ph[4+k]))/YP01_RW
            if t<1:h=max(h,(1-t**2.3)*(YP01_RH+.008*math.sin(y*4.7+k*2.1+ph[7])))
        return YP01_FUR+h*ry+.010*math.sin(x*23+ph[5])*math.sin(y*19+ph[6])+.006*math.sin(x*47+y*31)
    _earth('YP01_01_Earth',W,D,zf,M['soil'],'Body',NX=56,NY=72,scale=.5,seed=7102)
    def edge(x,y):e=min(1.,(1-max(abs(x)/(W/2),abs(y)/(D/2)))/.15);return e*e*(3-2*e)
    for k in range(9):
        q=rr.uniform(-.7,.7);sd=rr.choice((-1,1));x,y=((q*W/2,sd*(D/2-.13)) if k%2 else (sd*(W/2-.12),q*D/2));s=rr.uniform(.05,.11)
        _blob(f'YP01_01_Stone{k}',(s,s*rr.uniform(.7,1),s*rr.uniform(.45,.7)),7110+k,M['stone'],'Detail_Stones',sub=2,scale=.2).data.transform(Matrix.Translation((x,y,max(0,zf(x,y)*edge(x,y)-.024)+.004)))
    for k in range(14):
        c=rr.choice((-.31,.31));x=c+rr.uniform(-.04,.04);y=rr.uniform(-D/2+.25,D/2-.25);b=Vector((x,y,zf(x,y)-.012))
        if k>9:x=rr.choice((-1,1))*(W/2-.10);y=rr.uniform(-1.2,1.2);b=Vector((x,y,zf(x,y)*edge(x,y)-.008))
        for q in range(4):
            a=math.tau*q/4+rr.uniform(-.5,.5);_blade(f'YP01_01_Weed{k}_{q}',b+Vector((math.cos(a)*.008,math.sin(a)*.008,0)),(math.cos(a),math.sin(a)),rr.uniform(.06,.11),.013,rr.uniform(.15,.55),.2,lambda u:math.sin(math.pi*min(1,u+.08))**.8,M['radish_leaf'],'Detail_Weeds',nu=3,nv=1,cup=.3)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);h=np.zeros(P.shape[:2],np.float32)
        col,rough,soil=_yp01_soil_paint(col,rough,P,onrm,noise,mid,filled,7120)
        d1,d2,cid,_,_=_wor(P*np.array((1,1,0),np.float32),(22.,22.,1.),7121);clod=soil*(cid>.55)*np.clip(1-d1/.42,0,1);h+=.0035*clod;col=col*(1+.10*clod[...,None])            # clods
        pb=soil*(cid<.06)*np.clip(1-d1/.30,0,1);col=col*(1-pb[...,None])+pb[...,None]*np.array([.42,.40,.36]);h+=.004*pb                                                         # a few pebbles in the earth
        px=P[...,0];ft=soil*np.clip(1-np.abs(np.abs(px)-.31)/.10,0,1)*np.clip((_fb(P,(6.,3.,1.),7122,2)-.45)*4,0,1)*(P[...,2]<.07);h-=.004*ft;col=col*(1-.12*ft[...,None])       # footprints pressed into the furrows
        R_['h']=h;return col,rough
    M['soil']['mid']=1.
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.3,'grime':.5,'ao_k':.55,'uv_angle':60,'collision_box':((1.84,2.84,.16),(0,0,.08)),
            'collision':'one box over the earth: the player walks round the bed',
            'notes':['2.0 × 3.0 m of earth with three bare ridges along its length (centres at x = -0.62, 0, +0.62 m), trodden furrows, a ragged rim down to the ground',
                     'the crops are separate models (YP01_02 cabbages, YP01_03 spring onions, YP01_04 beans on a bamboo frame): put one on each ridge, origin on the ground under the ridge line; any crop fits any ridge',
                     'painted, with the relief also in the normal map: clods, a few pebbles, footprints in the furrows',
                     'Detail_Stones (9 stones on the rim) and Detail_Weeds (14 weeds) are off at the standard tier']}
PROPS['YP01_01']=YP01_01

# ---------------- YP01_02 a row of cabbages (cand-4) ----------------
def YP01_02(M):
    """six heading cabbages along one ridge: a pale heart, five inner leaves wrapping it, seven outer leaves lying open,
    each leaf a cupped blade with a ruffled edge on a thick white rib."""
    rr=random.Random(int(__import__('os').environ.get('YP_SEED',7138)));zf=_yp01_cap('YP01_02',M,7132)
    for i in range(6):
        y=-1.0+2.0*i/5+rr.uniform(-.03,.03);x=rr.uniform(-.03,.03);sz=rr.uniform(.86,1.10);b=Vector((x,y,zf(x,y)-.012));nm=f'YP01_02_C{i}'
        _lathe(f'{nm}_Heart',[(0,.045*sz),(.2,.098*sz),(.5,.118*sz),(.78,.096*sz),(.93,.055*sz),(1,0)],(b,b+Vector((rr.uniform(-.01,.01),rr.uniform(-.01,.01),.235*sz))),M['cabbage_heart'],'Body',NS=10,scale=.15)
        a0=rr.uniform(0,math.tau)
        for k in range(12):
            inner=k<5;a=a0+(math.tau*k/5+.3 if inner else math.tau*(k-5)/7)+rr.uniform(-.15,.15);d=(math.cos(a),math.sin(a))
            if inner:L=sz*rr.uniform(.20,.235);th=.17+.038*k+rr.uniform(-.01,.01);dr=rr.uniform(.10,.22);off=(.090+.0065*k)*sz;Wd=L*rr.uniform(1.05,1.2);cup=rr.uniform(.5,.62);zo=.004*k
            else:L=sz*rr.uniform(.22,.27);g=((k-5)*.618+.3)%1;th=.80+.46*g+.14*(i%2);dr=rr.uniform(.25,.5);off=.085*sz;Wd=L*rr.uniform(.74,.88);cup=rr.uniform(.18,.35);zo=-.004*(k-5)
            bb=b+Vector((d[0]*off,d[1]*off,.012+zo));rp_=rr.uniform(20,30);p0=rr.uniform(0,6)
            _taper(f'{nm}_R{k}',[_bladec(bb,d,L,th,dr,u)+Vector((0,0,-.004)) for u in (0,.25,.5,.74)],[.013*sz,.011*sz,.0075*sz,.0026],M['veg_stem'],'Body',sides=4,scale=.06,up=(-d[1],d[0],0))
            _blade(f'{nm}_B{k}',bb,d,L,Wd,th,dr,lambda u,rp_=rp_,p0=p0:(.20+.80*(1-abs(2*min(1.,(u-.04)/.95)-1)**2.6)**.5*(.93+.07*math.sin(u*rp_+p0))) if u<.985 else .45,M['veg'],'Body',nu=6,nv=4,cup=cup,u0=.05,u1=1,twist=rr.uniform(-.25,.25))
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);h=np.zeros(P.shape[:2],np.float32)
        col,rough,soil=_yp01_soil_paint(col,rough,P,onrm,noise,mid,filled,7140)
        lf=filled*(1-soil)*(col[...,1]>col[...,0]*1.15);hi=lf*np.clip((P[...,2]-.24)/.10,0,1);col=col*(1-.35*hi[...,None])+hi[...,None]*.35*np.array([.66,.74,.36])   # the inner leaves paler, yellow-green
        vn_=lf*np.clip((_fb(P,(60.,60.,60.),7141,2)-.5)*3,-1,1);h+=.0008*vn_                                                                                         # crinkled leaf surface
        hole=lf*(1-hi)*np.clip((_vn(P,90.,7142)-.80)*12,0,1);col=col*(1-.55*hole[...,None])+hole[...,None]*.55*np.array([.34,.26,.12])                              # insect bites on the outer leaves
        low=lf*np.clip((.17-P[...,2])/.05,0,1)*np.clip(.3+noise,0,1);col=col*(1-.35*low[...,None])+low[...,None]*.35*np.array([.36,.30,.17])                         # soil splashed on the lowest leaves
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.3,'grime':.5,'ao_k':.5,'uv_angle':60,
            'notes':['one row for one ridge of YP01_01 (origin on the ground under the ridge line); it carries its own hilled-up soil, which covers the bare ridge',
                     'six heading cabbages: a pale heart, five inner leaves wrapping it, seven outer leaves lying open; every leaf is a cupped blade with a ruffled edge on a thick white rib; no leaf cards',
                     'painted: paler inner leaves, insect bites and splashed soil on the outer leaves; no collision (the bed has the box)']}
PROPS['YP01_02']=YP01_02

# ---------------- YP01_03 a row of spring onions (cand-4) ----------------
def YP01_03(M):
    """eleven clumps of spring onions along one ridge: every leaf a hollow tube rising from a pale sheath, some bent over"""
    rr=random.Random(int(__import__('os').environ.get('YP_SEED',7151)));zf=_yp01_cap('YP01_03',M,7152)
    for i in range(11):
        y=-1.05+2.1*i/10+rr.uniform(-.02,.02);x=rr.uniform(-.035,.035);b=Vector((x,y,zf(x,y)));sz=rr.uniform(.85,1.15);n=rr.randint(6,8)
        for k in range(n):
            a=math.tau*k/n+rr.uniform(-.3,.3);off=Vector((math.cos(a),math.sin(a),0));L=sz*rr.uniform(.30,.44);lean=rr.uniform(.05,.28);bend=rr.random()<.22;r=rr.uniform(.0056,.0074)*sz
            p0=b+off*rr.uniform(.016,.034)+Vector((0,0,-.018-.0037*k));ro=rr.uniform(0,math.tau)
            _taper(f'YP01_03_W{i:02d}{k}',[p0,p0+off*lean*.012+Vector((0,0,.040)),p0+off*lean*.02+Vector((0,0,.072))],[.0014,r*1.4,r*1.22],M['onion_white'],'Body',sides=6,scale=.06,up=(math.cos(ro+.55),math.sin(ro+.55),.3))
            q0=p0+off*lean*.019+Vector((0,0,.060+.0013*k));tip=q0+off*(lean*L+(L*.22 if bend else 0))+Vector((0,0,L*(.86 if bend else 1.)))
            pts=[q0,q0+off*lean*L*.25+Vector((0,0,L*.35)),q0+off*lean*L*.62+Vector((0,0,L*.72)),q0+off*(lean*L*.9+(L*.08 if bend else 0))+Vector((0,0,L*(.89 if bend else .93))),tip]
            _taper(f'YP01_03_L{i:02d}{k}',pts,[r,r*.95,r*.74,r*.45,.0008],M['scallion'],'Body',sides=5,scale=.06,up=(math.cos(ro),math.sin(ro),.3))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32)
        col,rough,soil=_yp01_soil_paint(col,rough,P,onrm,noise,mid,filled,7160)
        lf=filled*(1-soil)*(col[...,1]>col[...,0]*1.25);tipy=lf*np.clip((P[...,2]-.50)/.10,0,1)*np.clip(.3+noise,0,1);col=col*(1-.4*tipy[...,None])+tipy[...,None]*.4*np.array([.62,.58,.30])   # the highest tips yellowing
        return col,rough
    return {'paint':paint,'wear':.3,'grime':.5,'ao_k':.5,'uv_angle':60,
            'notes':['one row for one ridge of YP01_01 (origin on the ground under the ridge line); it carries its own hilled-up soil, which covers the bare ridge',
                     'eleven clumps of spring onions, every leaf a five-sided tube rising from a pale sheath, about one in five bent over; no leaf cards; no collision (the bed has the box)']}
PROPS['YP01_03']=YP01_03

# ---------------- YP01_04 a row of beans on a bamboo frame (cand-4) ----------------
def YP01_04(M):
    """three pairs of bamboo canes crossed over the ridge, a ridge cane lying in the crossings, a rail tied half-way up
    each side; six bean vines wind up the canes: leaves of three leaflets on short stalks, a few pods, tendrils at the tops."""
    rr=random.Random(int(__import__('os').environ.get('YP_SEED',7171)));zf=_yp01_cap('YP01_04',M,7172);BB,HP=M['bamboo_old'],M['hemp'];ZX=1.26;RC=.0135
    canes=[]
    for i,y in enumerate((-1.0,0.,1.0)):
        for q,s in enumerate((-1,1)):
            yy=y+s*.0155;a=Vector((s*.20,yy,zf(s*.20,yy)-.05));x_=Vector((0,yy,ZX));b=a+(x_-a)*1.17
            _bcane(f'YP01_04_Cane{i}{q}',a,b,RC,RC*.82,BB,'Body',gap=.24,sides=8,ph=.3*i+.5*q,bow=.006,bowdir=(0,1,0));canes.append((a,b,s))
        _xlash(f'YP01_04_Lash{i}',(0,y,ZX),(.20,0,-1.1),(-.20,0,-1.1),.034,HP,'Body',cord=.0036)
        for j in range(2):_ring(f'YP01_04_LashTurn{i}{j}',(0,y+(j*2-1)*.0075,ZX+.010+.004*j),(.12*(j*2-1),1,0),.030+.002*j,.0036,HP,'Body',n=11)
    _bcane('YP01_04_Ridge',(0,-1.22,ZX+.036),(0,1.22,ZX+.040),.0125,.011,BB,'Body',gap=.27,sides=8,ph=.6,bow=.006)
    for q,s in enumerate((-1,1)):
        zr_=.70;xr=s*(.20*(ZX-zr_)/(ZX-.10)+RC+.012)
        _bcane(f'YP01_04_Rail{q}',(xr,-1.16,zr_),(xr,1.16,zr_+.01),.0105,.0095,BB,'Body',gap=.25,sides=7,ph=.2+q*.4)
        for i,y in enumerate((-1.0,0.,1.0)):
            for j in range(2):_ring(f'YP01_04_RailTie{q}{i}{j}',(xr-s*.0125,y+s*.0155,zr_+.003*j),(s*.35,(j*2-1)*.62,.70),.0225+.002*j,.0032,HP,'Body',n=10)
    lw=lambda u:.10 if u<.07 else (.10+.90*math.sin(math.pi*min(1.,((u-.07)/.93)**.75))**.85)
    for k,(a,b,s,vq) in enumerate([(*c,q) for c in canes for q in (0,1)]):
        d=(b-a).normalized();u_=d.orthogonal().normalized();v_=d.cross(u_);Lc=(b-a).length;Lv=Lc*(rr.uniform(.70,.80) if vq==0 else rr.uniform(.45,.66));pitch=.16+.04*((k//2)*.618%1);ph=(k//2)*1.7+vq*math.pi;hand=1;rv=.0030
        P_=lambda t:a+d*t+(u_*math.cos(ph+hand*math.tau*t/pitch)+v_*math.sin(ph+hand*math.tau*t/pitch))*(RC+rv+.0042)
        n=int(Lv/pitch*7);ts=[.04+(Lv-.04)*j/n for j in range(n+1)]
        k=f'{k}{vq}'
        _taper(f'YP01_04_Vine{k}',[P_(t) for t in ts],[rv*(1-.5*t/Lv) for t in ts],M['vine'],'Body',sides=4,scale=.08)
        t=.16+.05*vq
        while t<Lv-.03:
            p=P_(t);o=(p-(a+d*t));oh=Vector((o.x,o.y,0));oh=oh.normalized() if oh.length>1e-4 else Vector((s,0,0))
            if abs(oh.y)<.5 and oh.x*s<0:oh=Vector((oh.x*.3,(1 if oh.y>=0 else -1),0)).normalized()     # leaves turn out of the frame, not into it
            sz=rr.uniform(.8,1.15)*(1-.35*t/Lc);e=p+oh*(.060*sz)+Vector((0,0,.026*sz))
            _taper(f'YP01_04_St{k}_{int(t*100):03d}',[p,p.lerp(e,.5)+Vector((0,0,.006)),e],[.0020,.0020,.0024],M['vine'],'Body',sides=5,scale=.06)
            thc=rr.uniform(.90,1.20);_taper(f'YP01_04_Nd{k}_{int(t*100):03d}',[e+Vector((0,0,-.0085)),e+Vector((0,0,-.003)),e+Vector((0,0,.0035))],[.0016,.0056,.0010],M['vine'],'Body',sides=5,scale=.04)
            for j,da in enumerate((-1.05,0.,1.05)):
                la=math.atan2(oh.y,oh.x)+da+rr.uniform(-.15,.15);L=.118*sz*(1. if j==1 else .86)
                _blade(f'YP01_04_Lf{k}_{int(t*100):03d}{j}',e+Vector((math.cos(la)*.005,math.sin(la)*.005,-.005*abs(j-1))),(math.cos(la),math.sin(la)),L,L*rr.uniform(.62,.74),thc+.27*abs(j-1),rr.uniform(.25,.6),lw,M['herb'],'Body',nu=5,nv=2,cup=rr.uniform(.15,.35),twist=rr.uniform(-.3,.3))
            if rr.random()<.22:   # a pod hanging under the leaf stalk
                pp=p+oh*.002;Lp=rr.uniform(.08,.12);_taper(f'YP01_04_Pod{k}_{int(t*100):03d}',[pp,pp+oh*.012+Vector((0,0,-Lp*.35)),pp+oh*.016+Vector((0,0,-Lp*.75)),pp+oh*.012+Vector((0,0,-Lp))],[.0016,.0052,.0048,.0010],M['veg'],'Body',sides=5,scale=.06)
            t+=rr.uniform(.10,.14)
        e0=P_(ts[-1]);pts=[e0+Vector((s*-.01*j,.012*math.sin(j*1.3+ph),.018*j))+(u_*math.cos(j*1.5)+v_*math.sin(j*1.5))*.012*min(1,j/2) for j in range(7)]   # the growing tip and its tendril
        pts=[P_(ts[-1]-.012),P_(ts[-1]-.005)]+pts[1:]
        _taper(f'YP01_04_Tip{k}',pts,[rv*.75,rv*.55,rv*.45,rv*.4,rv*.35,rv*.3,rv*.25,.0005],M['vine'],'Body',sides=3,scale=.06)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);h=np.zeros(P.shape[:2],np.float32);pz=P[...,2]
        col,rough,soil=_yp01_soil_paint(col,rough,P,onrm,noise,mid,filled,7180)
        bam=filled*(1-soil)*(col[...,0]>col[...,1]*1.08)*(col[...,0]>col[...,2]*1.3)
        gry=bam*np.clip((_fb(P,(6.,6.,3.),7181,2)-.48)*3,0,1);col=col*(1-.35*gry[...,None])+gry[...,None]*.35*np.array([.50,.47,.40]);rough=np.clip(rough+.08*gry,0,1)
        ft=bam*np.clip((.42-pz)/.28,0,1)*np.clip((noise-.3)*2.5,0,1);col=col*(1-.45*ft[...,None])+ft[...,None]*.45*np.array([.22,.20,.12])     # the feet of the canes: dark with damp
        crk=bam*np.clip((_vn(P*np.array((1,1,.08),np.float32),(260.,260.,30.),7182)-.80)*9,0,1);h-=.0012*crk;col=col*(1-.4*crk[...,None])        # drying cracks along the canes
        lf=filled*(1-soil)*(col[...,1]>col[...,0]*1.2);yl=lf*np.clip((_fb(P,11.,7183,2)-.56)*4,0,1);col=col*(1-.35*yl[...,None])+yl[...,None]*.35*np.array([.60,.62,.24])   # some leaves yellow-green
        yg=lf*np.clip((pz-1.0)/.3,0,1);col=col*(1+.10*yg[...,None])                                                                               # younger, lighter leaves near the top
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.4,'grime':.5,'ao_k':.5,'uv_angle':60,
            'notes':['one row for one ridge of YP01_01 (origin on the ground under the ridge line); it carries its own hilled-up soil, which covers the bare ridge',
                     'the frame: three pairs of bamboo canes crossed over the ridge and lashed, a ridge cane lying in the crossings, a rail tied half-way up each side',
                     'six bean vines wind up the canes (each a thin tube round its cane); leaves of three leaflets on short stalks, a few hanging pods, a tendril at each growing tip; every leaflet is its own blade, no leaf cards',
                     'painted, with the relief also in the normal map: grey weathered cane with drying cracks and dark feet; some leaves yellow-green; no collision (the bed has the box)']}
PROPS['YP01_04']=YP01_04
