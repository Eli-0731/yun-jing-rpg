# C 路邊小物（wayside-c）WS02 乾草叢（高、矮）. Every blade is its own piece, no leaf cards (as YP13_01 in yard-props-c).

def _droop_ok(L,th,dr,bz,floor=.008):
    """the most a blade may droop so its tip stays just above the ground (a drooping tip under the ground lifted the whole clump)"""
    return min(dr,max(0.,(L*math.cos(th)+bz-floor)/L))

def _ws_base(pid,M,rr,W,D,n_stone,seed,grp='Detail_Base'):
    """a thin patch of dry earth under the clump and a few small stones on its rim (Detail_)"""
    ph=[rr.uniform(0,6.28) for _ in range(3)]
    zf=lambda x,y:.016+.006*math.sin(x*17+ph[0])*math.sin(y*15+ph[1])+.003*math.sin(x*41+y*33+ph[2])
    _earth(f'{pid}_Earth',W,D,zf,M['soil_dry'],grp,NX=14,NY=12,scale=.4,p=2.4,wob=.10,seed=seed);M['soil_dry']['mid']=1.
    for k in range(n_stone):
        a=math.tau*k/n_stone+rr.uniform(-.4,.4);s=rr.uniform(.04,.08);r=rr.uniform(.43,.48)
        _blob(f'{pid}_Stone{k}',(s,s*rr.uniform(.7,1),s*rr.uniform(.45,.65)),seed+10+k,M['stone'],grp,sub=2,scale=.2).data.transform(Matrix.Translation((math.cos(a)*W*r,math.sin(a)*D*r,.003)))

def _dry_paint(seed,green_h):
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);pz=P[...,2];pr=np.hypot(P[...,0],P[...,1])
        lf=filled*(mid<.5)
        br=lf*np.clip((_fb(P,(7.,7.,5.),seed,2)-.45)*2.5,0,1);col=col*(1-.35*br[...,None])+br[...,None]*.35*np.array([.52,.40,.26])   # some blades pale brown, some straw
        gr=lf*np.clip((green_h-pz)/green_h,0,1)*np.clip(1-pr/.25,0,1)*np.clip((_fb(P,(12.,12.,8.),seed+1,2)-.40)*3,0,1);col=col*(1-.55*gr[...,None])+gr[...,None]*.55*np.array([.32,.40,.18])   # a few green blades low inside
        dk=lf*np.clip((.06-pz)/.06,0,1);col=col*(1-.35*dk[...,None])+dk[...,None]*.35*np.array([.30,.24,.16])   # darker, older at the base
        soil=filled*(mid>.5);col=col*(1-.12*soil[...,None]);return col,np.clip(rough+.05*lf,0,1)
    return paint

# ---------------- WS02_01 tall clump of dry silver grass (cand-4) ----------------
def WS02_01(M):
    """about seventy long folded blades from a dense base, arching out, straw-coloured to pale brown with a few green ones low
    inside; six thin culms stand above the blades, each ending in a feathery plume of a dozen silky racemes"""
    rr=random.Random(int(__import__('os').environ.get('WS_SEED',9201)))
    lw=lambda u:(.55+.45*min(1.,u/.10))*(1-u**2.0)**.8 if u<.99 else .04
    N=70
    for k in range(N):
        g=(k+.5)/N;a=k*2.39996+rr.uniform(-.25,.25);d=(math.cos(a),math.sin(a));rb=.010+.095*g**.8
        th=.05+.55*g**1.2+rr.uniform(-.04,.08);L=(.95-.40*g)*rr.uniform(.82,1.08);dr=_droop_ok(L,th,.16+.55*g+rr.uniform(-.06,.10),.002+.00012*k)
        _blade(f'WS02_01_B{k:02d}',Vector((d[0]*rb,d[1]*rb,.002+.00012*k)),d,L,rr.uniform(.016,.024)*(1.1-.2*g),th,dr,lw,M['hay'] if k%3 else M['hay_old'],'Body',nu=9,nv=2,cup=rr.uniform(.45,.8),twist=rr.uniform(-.8,.8))
    for k in range(6):   # culms with feathery plumes
        a=math.tau*k/6+rr.uniform(-.4,.4);d=Vector((math.cos(a),math.sin(a),0));s_=Vector((-d.y,d.x,0));H=rr.uniform(.95,1.18);lean=rr.uniform(.06,.20);b=d*rr.uniform(.01,.035)+Vector((0,0,-.01))
        f=lambda u,H=H,lean=lean,b=b,d=d:b+d*(lean*H*u**1.6+.06*H*max(0.,u-.80)**1.5*4)+Vector((0,0,H*u-.18*H*max(0.,u-.80)**2*4))
        us=(0,.2,.4,.6,.75,.85,.93,1.);_taper(f'WS02_01_Culm{k}',[f(u) for u in us],[.0030,.0028,.0025,.0021,.0017,.0013,.0010,.0006],M['straw'],'Body',sides=4,scale=.08)
        for j in range(16):   # silky racemes fanning from the top of the culm, bending over with their weight
            u=.80+.20*j/15;p=f(u);ang=j*2.39996;o=(s_*math.cos(ang)+d*math.sin(ang)*.6+Vector((0,0,.55))).normalized();Lr=rr.uniform(.10,.17)*(1.1-.4*j/15)
            pts=[p,p+o*Lr*.35,p+o*Lr*.7+Vector((0,0,-Lr*.08)),p+o*Lr+Vector((0,0,-Lr*.25))]
            _taper(f'WS02_01_Ra{k}{j:02d}',pts,[.0014,.0026,.0024,.0008],M['hay'],'Body',sides=4,scale=.05)
    _ws_base('WS02_01',M,rr,.42,.40,4,9230)
    return {'paint':_dry_paint(9240,.30),'wear':.2,'grime':.3,'ao_k':.45,'uv_angle':60,
            'notes':['a tall clump of dry silver grass about 1.1 m high: 70 long folded blades from a dense base, arching out; straw-coloured to pale brown, a few green ones low inside; every blade its own piece, no leaf cards',
                     'six thin culms above the blades, each ending in a plume of sixteen silky racemes bending over',
                     'Detail_Base (a thin patch of dry earth and four small stones) is off at the standard tier; the blades start inside the earth patch; no collision']}
PROPS['WS02_01']=WS02_01

# ---------------- WS02_02 low tuft of withered grass (cand-1) ----------------
def WS02_02(M):
    """a low tangled tuft of fine withered blades: most arch out and bend over, about one in four is broken and lies flat
    on the ground, a few faded green ones inside"""
    rr=random.Random(int(__import__('os').environ.get('WS_SEED',9254)))
    lw=lambda u:(.6+.4*min(1.,u/.10))*(1-u**2.0)**.8 if u<.99 else .04
    N=90
    for k in range(N):
        g=(k+.5)/N;a=k*2.39996+rr.uniform(-.3,.3);d=(math.cos(a),math.sin(a));rb=.008+.06*g**.8
        if k%4==3:   # broken: a short standing stub, then the rest lying out over the ground
            L1=rr.uniform(.06,.12);th=.35+.4*g;_blade(f'WS02_02_S{k:02d}',Vector((d[0]*rb,d[1]*rb,.002+.00014*k)),d,L1,rr.uniform(.010,.014),th,.05,lw,M['hay_old'],'Body',nu=4,nv=2,cup=.5,u0=0.,u1=.9)
            c=_bladec(Vector((d[0]*rb,d[1]*rb,.002+.00014*k)),d,L1,th,.05,.9);d2=(math.cos(a+rr.uniform(-.5,.5)),math.sin(a+rr.uniform(-.5,.5)))
            L2=rr.uniform(.14,.24);th2=1.15+rr.uniform(0,.15);dr2=max(.05,(c.z+L2*math.cos(th2)-.004)/L2)   # bent over from the break: its tip comes down onto the ground
            _blade(f'WS02_02_F{k:02d}',c,d2,L2,rr.uniform(.010,.013),th2,dr2,lw,M['hay_old'],'Body',nu=6,nv=2,cup=.3,twist=rr.uniform(-.9,.9))
            continue
        th=.08+.72*g**1.2+rr.uniform(-.05,.08);L=(.34-.08*g)*rr.uniform(.80,1.12);dr=_droop_ok(L,th,.22+.55*g+rr.uniform(-.06,.10),.002+.00014*k)
        _blade(f'WS02_02_B{k:02d}',Vector((d[0]*rb,d[1]*rb,.002+.00014*k)),d,L,rr.uniform(.010,.015),th,dr,lw,M['hay'] if k%3 else M['hay_old'],'Body',nu=8,nv=2,cup=rr.uniform(.4,.7),twist=rr.uniform(-1.,1.))
    _ws_base('WS02_02',M,rr,.30,.28,3,9260)
    return {'paint':_dry_paint(9270,.14),'wear':.2,'grime':.3,'ao_k':.45,'uv_angle':60,
            'notes':['a low tangled tuft about 0.3 m high: 90 fine withered blades, most arching out and bending over, one in four broken and lying flat on the ground; a few faded green ones inside; every blade its own piece, no leaf cards',
                     'Detail_Base (a thin patch of dry earth and three small stones) is off at the standard tier; the blades start inside the earth patch; no collision']}
PROPS['WS02_02']=WS02_02
