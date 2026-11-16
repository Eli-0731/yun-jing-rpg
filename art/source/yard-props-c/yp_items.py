# YP03–YP05 shapes (the 11/14 120h pack, batch A: A1 yard props), read by build_yp.py.
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _drop_part(o):
    parts.remove(o);bpy.data.objects.remove(o)
def _flat_foot(o,z=.004):
    """a splayed leg's end is square to the leg: bring everything under z down to the ground so the foot stands flat"""
    for v in o.data.vertices:
        if v.co.z<z:v.co.z=0.
def _moss_low(col,rough,P,onrm,noise,cav,filled,h=.10,amt=.5,soil=.05):
    """moss creeping up from the ground and soil right at the foot (painted)"""
    pz=P[...,2];ms=filled*np.clip((noise-.45)*3+np.clip((h-pz)/h,0,1)*1.1-.55+(cav-.5)*.6,0,1)*np.clip((h*1.6-pz)/(h*.6),0,1)
    col=col*(1-amt*ms[...,None])+ms[...,None]*amt*np.array([.21,.29,.11]);rough=np.clip(rough+.05*ms,0,1)
    so=filled*np.clip((soil-pz)/soil,0,1)*np.clip(.4+noise,0,1);col=col*(1-.45*so[...,None])+so[...,None]*.45*np.array([.22,.17,.11])
    return col,rough

# ---- painted detail: 3D noise on the baked position map, and a height field that build_yp.py adds to the normal map (meta['relief']) ----
def _h32(i,j,k,seed):
    n=(i*73856093)^(j*19349663)^(k*83492791)^(seed*2654435761);n&=0xffffffff
    n=((n^(n>>15))*2246822519)&0xffffffff;n=((n^(n>>13))*3266489917)&0xffffffff;n^=n>>16
    return (n&0xffffff).astype(np.float32)/16777215.
def _vn(P,f,seed=0):
    """value noise 0..1; f: cells per metre (one number or one per axis)"""
    Q=(P*(np.asarray(f,np.float32)*np.ones(3,np.float32))).astype(np.float32);I=np.floor(Q);T=Q-I;T=T*T*(3-2*T);I=I.astype(np.int64);out=0
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                out=out+(T[...,0] if dx else 1-T[...,0])*(T[...,1] if dy else 1-T[...,1])*(T[...,2] if dz else 1-T[...,2])*_h32(I[...,0]+dx,I[...,1]+dy,I[...,2]+dz,seed)
    return out
def _fb(P,f,seed=0,o=3):
    f=np.asarray(f,np.float32)*np.ones(3,np.float32);s=0;a=.5;t=0
    for q in range(o):s=s+a*_vn(P,f*2**q,seed+q*17);t+=a;a*=.5
    return s/t
def _wor(P,f,seed=0,jit=.9):
    """cells: distance to the nearest and second point (in cells), a random number per cell, the vector from the cell's point, a random tilt per cell"""
    Q=(P*(np.asarray(f,np.float32)*np.ones(3,np.float32))).astype(np.float32);I=np.floor(Q);F=Q-I;I=I.astype(np.int64);sh=P.shape[:2]
    d1=np.full(sh,9.,np.float32);d2=d1.copy();ci=np.zeros(sh+(3,),np.int64);vec=np.zeros(sh+(3,),np.float32)
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for dz in (-1,0,1):
                c=I+np.array((dx,dy,dz));pt=np.stack([_h32(c[...,0],c[...,1],c[...,2],seed+s_) for s_ in (1,2,3)],-1)
                v=F-(np.array((dx,dy,dz),np.float32)+.5+jit*(pt-.5));d=np.sqrt((v*v).sum(-1));nw=d<d1
                d2=np.where(nw,d1,np.minimum(d2,d));d1=np.where(nw,d,d1);ci=np.where(nw[...,None],c,ci);vec=np.where(nw[...,None],v,vec)
    cid=_h32(ci[...,0],ci[...,1],ci[...,2],seed+7);tilt=np.stack([_h32(ci[...,0],ci[...,1],ci[...,2],seed+s_) for s_ in (11,12,13)],-1)-.5
    return d1,d2,cid,vec,tilt
def _segd(P,pts,w):
    """1 on a polyline falling to 0 at distance w"""
    best=np.full(P.shape[:2],1e9,np.float32)
    for a,b in zip(pts[:-1],pts[1:]):
        a=np.array(a[:],np.float32);d=np.array(b[:],np.float32)-a;L=max(float(d@d),1e-12);t=np.clip(((P-a)@d)/L,0,1);q=P-a-t[...,None]*d;best=np.minimum(best,np.sqrt((q*q).sum(2)))
    return np.clip(1-best/w,0,1)
def _wood_age(col,rough,h,P,m,grain,seed,edge,checks=1.,grey=.22,chips=1.,w=.05,stain=.16):
    """old timber where the mask m is set, grain along axis `grain`: checks along the grain (cut into the height too), darker
    streaks, sun-greyed patches, nibbled pale edges"""
    ax=[i for i in range(3) if i!=grain];gl=np.full(3,5.,np.float32);gl[grain]=1.5;f0=30.
    s=(P[...,ax[0]]+.618*P[...,ax[1]])*f0+1.6*(_vn(P,gl,seed)-.5);cell=np.floor(s).astype(np.int64);fr=s-cell;z0=np.zeros_like(cell)
    Pa=P.copy();Pa[...,grain]+=_h32(cell,z0,z0,seed+4)*3.;ga=np.full(3,.01,np.float32);ga[grain]=3.4   # each line has its own run of lengths along the grain
    ln=np.clip(1-np.abs(fr-.5)/(w*.03*f0),0,1)*(_h32(cell,z0,z0,seed+2)>.5)*np.clip((_vn(Pa,ga,seed+5)-.5)*7,0,1)*m*checks
    h-=.0016*ln;col=col*(1-.55*ln[...,None]);rough=np.clip(rough+.08*ln,0,1)
    f2=np.full(3,48.,np.float32);f2[grain]=1.3;st=np.clip((_vn(P,f2,seed+9)-.5)*2.2,0,1)*np.clip((_fb(P,3.,seed+10,2)-.35)*3,0,1)*m;col=col*(1-stain*st[...,None])
    Pw_=P+.06*np.stack([_fb(P,4.,seed+14+q_,2)-.5 for q_ in range(3)],-1).astype(np.float32);gr=np.clip((_fb(Pw_,2.6,seed+13,2)-.46)*2.4,0,1)*m*grey;col=col*(1-gr[...,None])+gr[...,None]*np.array([.47,.44,.39]);rough=np.clip(rough+.10*gr,0,1)
    ch=m*np.clip((edge-.62)*2.6,0,1)*np.clip((_fb(P,45.,seed+3,2)-.47)*4,0,1)*chips;col=col*(1-.40*ch[...,None])+ch[...,None]*.40*np.array([.60,.48,.33]);h-=.0010*ch
    return col,rough
def _knot(col,h,P,c,r,nrm_mask):
    """a knot in a board: a dark eye, a ring round it, a little raised"""
    d=np.sqrt(((P-np.array(c,np.float32))**2).sum(2))/r;k=np.clip(1-d,0,1)*nrm_mask;ring=np.clip(1-np.abs(d-.8)/.25,0,1)*nrm_mask
    col=col*(1-.45*k[...,None])*(1-.25*ring[...,None]);h+=.0008*k-.0008*ring;return col

def _chip_staves(obs,rr,c=(0.,0.),p=.16):
    """stave tops broken: some lose a corner, a few are worn short"""
    for o in obs:
        u=rr.random()
        if u>p+.12:continue
        zt=max(v.co.z for v in o.data.vertices);am=math.atan2(sum(v.co.y-c[1] for v in o.data.vertices),sum(v.co.x-c[0] for v in o.data.vertices));sd=rr.choice((-1,1));dp=rr.uniform(.006,.013)
        for v in o.data.vertices:
            if v.co.z>zt-.008:
                da=(math.atan2(v.co.y-c[1],v.co.x-c[0])-am+math.pi)%math.tau-math.pi
                if u>p:v.co.z-=dp*.55
                elif da*sd>0:v.co.z-=dp
def _pail_age(col,rough,h,P,onrm,edge,filled,rw,H,bands,splits,seed):
    """a coopered pail standing at the origin of P: old staves (checks along the grain, splits down from the rim), rusty pitted hoops"""
    px,py,pz=P[...,0],P[...,1],P[...,2];pr=np.hypot(px,py);th=np.arctan2(py,px);rwz=rw(np.clip(pz,0,H))
    wall=filled*(pr>rwz-.02)*(pr<rwz+.03)*(np.abs(onrm[...,2])<.6)*(pz<H+.11)
    hp=np.zeros(pr.shape,np.float32)
    for z0,z1 in bands:hp=np.maximum(hp,((pz>z0-.001)&(pz<z1+.001)&(pr>rwz+.0005)).astype(np.float32))
    wd=wall*(1-hp)*(col[...,0]>col[...,2]*1.3)
    col,rough=_wood_age(col,rough,h,P,wd,2,seed,edge,grey=.30,stain=.22)
    for a0,ln in splits:
        ck=wd*np.clip(1-np.abs((th-a0-.03*np.sin(pz*55+a0*7)+np.pi)%(2*np.pi)-np.pi)*pr/.0026,0,1)*np.clip((pz-(H-ln))/.02,0,1)*(pz<H+.01);h-=.0028*ck;col=col*(1-.7*ck[...,None])
    ir=wall*hp;ru=np.clip((_fb(P,28.,seed+31,3)-.42)*3.5,0,1)*ir;col=col*(1-.55*ru[...,None])+ru[...,None]*.55*np.array([.40,.21,.10]);h-=.0007*ru;rough=np.clip(rough+.1*ru,0,1)
    return col,rough

# ---------------- YP03 wooden water bucket with a ladle (cand-4) ----------------
def YP03(M):
    """a coopered bucket, wider at the top: fourteen staves, two riveted iron hoops, a bottom board; two opposite staves
    run up past the rim, drilled, and a hemp rope goes through them as the handle (knotted outside). Water near the rim.
    A long-handled wooden ladle lies across the rim, its bowl just in the water."""
    rr=random.Random(6301);WD,WB,IR,HP=M['cedar'],M['cedar_b'],M['iron'],M['hemp']
    H=.30;R0=.150;R1=.178;T=.014;N=14;rw=lambda z:R0+(R1-R0)*z/H;turn=Matrix.Rotation(-math.pi/N,4,'Z')
    st=_staves('YP03_Stave',(0,0,0),[(0,R0),(H,R1)],T,N,.012,WD,'Body',rows=4)
    ear=_staves('YP03_Ear',(0,0,0),[(0,R0),(H,R1),(.405,rw(.405))],T+.004,N,.012,WB,'Body',rows=6)
    for k in range(N):
        if k in (0,7):_drop_part(st[k])
        else:
            _drop_part(ear[k]);st[k].data.transform(Matrix.Translation((0,0,rr.uniform(-.004,.003))))   # stave tops not all level
            st[k].data.transform(turn)
    for k in (0,7):
        e=ear[k];e.data.transform(turn);s=1 if k==0 else -1
        _boolean(e,_cyl_cutter(f'YP03_cutEar{k}',(s*(rw(.365)-.008),0,.365),(1,0,0),.0125,.06))
    _chip_staves([st[k] for k in range(N) if k not in (0,7)],rr)
    for q,(z0,z1) in enumerate(((.055,.083),(.212,.240))):   # two iron hoops with a ring of rivets
        zm=(z0+z1)/2;_ring_band(f'YP03_Hoop{q}',(0,0,0),rw(zm)+.004,rw(zm)-.0015,z0,z1,IR,'Body',NS=28,scale=.2)
        for j in range(10):
            a=math.tau*(j+.5*q)/10+rr.uniform(-.05,.05);n=Vector((math.cos(a),math.sin(a),0));p=n*(rw(zm)+.0035)+Vector((0,0,zm))
            _lathe(f'YP03_Rivet{q}{j}',[(0,.0058),(.6,.0048),(1,0)],(p,p+n*.0042),IR,'Detail_Rivets',NS=6,scale=.03)
        a=2.1+q*.5;n=Vector((math.cos(a),math.sin(a),0));o=box(f'YP03_Lap{q}',(.005,.040,z1-z0+.003),(0,0,0),IR,'Body',bev=.001,segs=1,jit=0,rot=Matrix.Rotation(a,4,'Z'))   # where the hoop's ends overlap
        o.data.transform(Matrix.Translation(n*(rw(zm)+.0045)+Vector((0,0,zm))))
    _lathe('YP03_Bottom',[(0,R0-.004),(1,rw(.036)-.004)],((0,0,.020),(0,0,.036)),WB,'Body',NS=28)
    zw=.262;wo=_lathe('YP03_Water',[(0,rw(zw)-T+.003),(1,rw(zw)-T+.003)],((0,0,zw-.012),(0,0,zw)),M['water'],'Body',NS=28)
    for p_ in wo.data.polygons:p_.use_smooth=False   # a flat sheet, not a dome
    # the rope handle: through both ears, a knot outside each
    xe=rw(.365);pts=[Vector((-xe-.022,0,.352)),Vector((-xe+.004,0,.365))]
    pts+=[Vector((.150*math.cos(t),.028*math.sin(t),.378+.082*math.sin(t))) for t in np.linspace(math.pi,0,15)]
    pts+=[Vector((xe-.004,0,.365)),Vector((xe+.022,0,.352))]
    rope('YP03_Rope',pts,.0085,HP,'Body')
    for q,s in enumerate((-1,1)):
        o=_blob(f'YP03_Knot{q}',(.036,.034,.036),6310+q,HP,'Body',sub=2,bumps=4,amp=.10,scale=.06);o.data.transform(Matrix.Translation((s*(xe+.021),0,.332)))
    # the ladle: a turned bowl and a long handle, lying across the rim clear of the ears
    ph=math.radians(-27);d=Vector((math.cos(ph),math.sin(ph),0));cc=-d*.074
    _lathe('YP03_LadleBowl',[(0,.002),(0,.034),(.45,.058),(1,.063),(1,.057),(.5,.052),(.14,.030),(.14,.002)],(cc+Vector((0,0,.250)),cc+Vector((0,0,.305))),M['floatwood'],'Body',NS=20,scale=.15,loop=True)
    _lathe('YP03_LadleHandle',[(0,.0105),(.5,.0095),(.93,.009),(.97,.0115),(1,.0105)],(cc+d*.052+Vector((0,0,.2955)),d*.292+Vector((0,0,.3185))),M['floatwood'],'Body',NS=8,scale=.15)
    # one stave was mended with a small board
    o=box('YP03_Patch',(.062,.008,.044),(0,0,0),WB,'Body',bev=.002,segs=1,jit=.0006,seed=6320,rot=Matrix.Rotation(.12,4,'Y'))
    o.data.transform(Matrix.Translation((.03,-(rw(.135)+.001),.135)))
    for q,(dx,dz) in enumerate(((-.022,.014),(.022,.012),(-.021,-.013),(.023,-.014))):
        p=Vector((.03+dx,-(rw(.135)+.0045),.135+dz));_lathe(f'YP03_Nail{q}',[(0,.0035),(1,0)],(p,p+Vector((0,-.0025,0))),IR,'Detail_Rivets',NS=6,scale=.03)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];pr=np.hypot(px,py);h=np.zeros(pr.shape,np.float32)
        wall=filled*(pr>.13)*(np.abs(onrm[...,2])<.6)
        col,rough=_pail_age(col,rough,h,P,onrm,edge,filled,rw,H,((.055,.083),(.212,.240)),((-1.2,.11),(.9,.07),(2.6,.13),(-2.5,.06)),6330)
        for zh in (.055,.212):   # rust run a little way down from each hoop
            run=wall*np.clip((zh-pz)/.05,0,1)*np.clip((pz-zh+.07)/.02,0,1)*np.clip((np.sin(np.arctan2(py,px)*23+noise*5)-.2)*1.4,0,1)
            col=col*(1-.36*run[...,None])+run[...,None]*.36*np.array([.33,.19,.10])
        inside=filled*(pr<.166)*(pz>.262)*(pz<.31)*(np.abs(onrm[...,2])<.6);col=col*(1-.30*inside[...,None])   # wet band inside above the water
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,wall,h=.08,amt=.5,soil=.03)
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.9,'grime':.9,'damp':.075,'uv_angle':60,
            'notes':['fourteen staves (their tops not level, some with a corner broken off or worn short), two iron hoops each with ten rivets (Detail_Rivets) and a lapped joint, a bottom board let into the staves',
                     'two opposite staves run up past the rim and are drilled; the hemp rope handle goes through and is knotted outside','still water 4 cm below the rim; the ladle (turned bowl, long handle) lies across the rim clear of the ears',
                     'one stave mended with a small nailed board; painted, with the relief also in the normal map: checks along the staves, splits down from the rim, rusty pitted hoops and rust runs under them, sun-greyed patches, the wet band inside, damp and moss at the foot']}
PROPS['YP03']=YP03

# ---------------- YP04 stone mortar and wooden pestle (cand-3) ----------------
def YP04(M):
    """one thick block of stone, hand-chiselled: the outside is broken into facets (not a smooth cylinder), a little
    waisted, a foot ring at the bottom, a deep round bowl. The wooden pestle leans in the bowl against the rim:
    a rounded working end, the shaft thinner upward, four turns of cord at the grip, a knob on top. Husked grain in the bowl."""
    rr=random.Random(6401);ST,WD,HP=M['stone'],M['cedar_b'],M['hemp'];NS=40
    rings=[(.150,0.,0),(.203,.004,0),(.214,.030,0),(.206,.072,0),(.187,.105,0),(.181,.20,0),(.196,.32,0),(.213,.40,0),(.216,.436,0),(.206,.452,0),
           (.168,.452,0),(.158,.43,0),(.150,.36,0),(.125,.27,0),(.08,.205,0),(.03,.185,0)]
    def _dense(rs,step):
        out=[]
        for a_,b_ in zip(rs[:-1],rs[1:]):
            n_=max(1,round(math.hypot(b_[1]-a_[1],b_[0]-a_[0])/step));out+=[(a_[0]+(b_[0]-a_[0])*i/n_,a_[1]+(b_[1]-a_[1])*i/n_,0) for i in range(n_)]
        return out
    rings=[rings[0]]+_dense(rings[1:10],.026)+_dense(rings[9:],.04)+[rings[-1]]
    o=_turned('YP04_Mortar',rings,NS,ST,'Body',scale=.35)
    wv=[(rr.randint(2,7),rr.uniform(7,24),rr.uniform(0,6.28),rr.uniform(0,6.28),rr.uniform(.0025,.0055)) for _ in range(8)]
    flats=[(rr.uniform(0,6.28),rr.uniform(.08,.40),rr.uniform(.20,.42),rr.uniform(.05,.13),rr.uniform(.006,.012)) for _ in range(9)]   # angle, z, width (rad), half height, depth: broad flats left by the pick
    chips=((2.3,.06,.014),(-.4,.045,.010),(.9,.035,.008),(-2.6,.05,.011))
    for v in o.data.vertices:   # hewn from one block: broad uneven flats and swells, nothing turned-round about the outside
        r=math.hypot(v.co.x,v.co.y);a=math.atan2(v.co.y,v.co.x);z=v.co.z
        if r>.172 and .02<z<.447:
            r+=sum(am*math.sin(k*a+pa)*math.sin(m*z+pz) for k,m,pa,pz,am in wv)+rr.uniform(-.0012,.0012)
            for a0,z0,wd,hh,dp in flats:
                da=abs((a-a0+math.pi)%math.tau-math.pi)/wd;dz=abs(z-z0)/hh
                if da<1 and dz<1:r-=dp*(1-da*da)*(1-dz*dz)
            v.co.x=r*math.cos(a);v.co.y=r*math.sin(a)
        elif r>.14 and z>.447:   # the rim: not level, and knocked off in four places
            v.co.z+=.004*math.sin(2*a+1.1)+.003*math.sin(5*a+.4)+rr.uniform(-.0015,.0015)
            for a0,wd,dp in chips:
                fl=max(0.,1-abs((a-a0+math.pi)%math.tau-math.pi)*r/wd)**.6
                if fl>0 and r>.185:k_=1-dp*fl/r;v.co.x*=k_;v.co.y*=k_;v.co.z-=dp*fl*.8
    cut=_cutter('YP04_cutCrack',(.006,.050,.125),(0,0,0));cut.data.transform(Matrix.Rotation(.10,4,'Y'));cut.data.transform(Matrix.Translation((.045,-.212,.405)))
    _boolean(o,cut)   # a crack down from the rim on the front (outer half of the wall only)
    A=Vector((.035,.018,.196));B=Vector((.238,-.036,.700));d=(B-A).normalized();L=(B-A).length
    _lathe('YP04_Pestle',[(0,0),(.02,.030),(.07,.043),(.14,.044),(.22,.036),(.5,.029),(.8,.026),(.9,.027),(.93,.040),(.965,.046),(.99,.034),(1,0)],(A,B),WD,'Body',NS=14,scale=.25)
    for q in range(4):_ring(f'YP04_Cord{q}',A+d*(L*(.655+.021*q)),d,.0295,.0042,HP,'Body',n=14)
    g=_lathe('YP04_Grain',[(0,.125),(.55,.095),(.9,.04),(1,0)],((0,0,.198),(0,0,.243)),M['hay'],'Body',NS=16,scale=.12);jitter(g,.004,6410,freq=40)
    R_={};czs=[.03,.10,.17,.24,.30,.345];cth=[-1.50,-1.44,-1.47,-1.39,-1.40,-1.362]
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];pr=np.hypot(px,py);th=np.arctan2(py,px);h=np.zeros(pr.shape,np.float32)
        stone=filled*(col[...,2]>col[...,0]*.72)
        out=stone*(pr>.16)*(pz<.45)
        col=col*(1-.16*(out*np.clip(.9-noise*1.2,0,1))[...,None])                                                          # weathered darker outside, unevenly
        Pw=P+.012*np.stack([_fb(P,18.,6425+q_,2)-.5 for q_ in range(3)],-1).astype(np.float32)
        d1,d2,cid,vec,tilt=_wor(Pw,24.,6420);tl=(pz*.8+th*pr*.55)*55.+1.5*(_vn(P,6.,6429)-.5);tool=out*np.clip(1-np.abs(tl-np.floor(tl)-.5)/.22,0,1)*np.clip((_fb(Pw,7.,6430,2)-.54)*5,0,1)
        h+=out*(.0075*(_fb(Pw,22.,6426,3)-.5)+.0040*(_fb(P,85.,6427,2)-.5))-.0012*tool;col=col*(1-.06*tool[...,None])   # rough-hewn, with runs of slanting pick strokes                                            # pick marks: small tilted facets, in the normal map
        col=col*(1+.16*(out*(_fb(Pw,22.,6426,3)-.5))[...,None])          # each facet a little lighter or darker, the ridges between them pale
        e1,e2,eid,_,_=_wor(P,95.,6421);pit=stone*(pz<.452)*(eid>.62)*np.clip(1-e1/.34,0,1);h-=.0013*pit;col=col*(1-.20*pit[...,None])   # small pits all over
        st=out*np.clip((_vn(P,(38.,38.,2.5),6423)-.56)*3,0,1)*np.clip((pz-.12)/.2,0,1);col=col*(1-.14*st[...,None])        # rain streaks down from the rim
        f1,f2,fid,_,_=_wor(Pw,15.,6422);li=out*(fid>.86)*np.clip((.34-f1-.5*(_fb(P,45.,6428,2)-.5))/.10,0,1)*(pz>.10)
        col=col*(1-.38*li[...,None])+li[...,None]*.38*np.array([.70,.71,.62]);h+=.0006*li                                  # pale crusty lichen
        ck=out*np.clip(1-np.abs(th-np.interp(pz,czs,cth))*pr/.0045,0,1)*(pz<.36)*(pz>.035);h-=.003*ck;col=col*(1-.7*ck[...,None])   # the crack runs on down from the cut
        bowl=stone*(pr<.165)*(pz>.19);col=col*(1+.04*bowl[...,None]);rough=np.clip(rough-.12*bowl,0,1)                 # the bowl worn smoother and paler
        dust=stone*(pz>.445)*np.clip(.3+noise,0,1);col=col*(1-.15*dust[...,None])+dust[...,None]*.15*np.array([.66,.60,.47])   # meal dust on the rim
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,out,h=.15,amt=.6,soil=.045)
        grain=filled*(1-stone)*(pz<.25)*(pr<.13);sp=np.clip((np.sin(px*900+py*300)*np.sin(py*800-px*250)-.2)*2,0,1)
        col=col*(1-.18*(grain*sp)[...,None])
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.9,'grime':.9,'uv_angle':60,'collision_box':((.43,.43,.45),(0,0,.225)),
            'notes':['one block of stone, hewn: the outside is uneven swells and broad pick flats (in the shape), a little waisted, a foot ring; the rim is not level and knocked off in four places; the bowl is deep and round and smooth; a crack runs down from the rim on the front',
                     'the pestle leans in the bowl against the rim: rounded working end, four turns of cord at the grip, a knob on top; a small heap of grain in the bowl',
                     'the stone patch and iron staples of the three-view are left out (a cracked mortar is not mended that way)',
                     'painted, with the relief also in the normal map: small tilted pick facets and pits, the crack going on down, rain streaks, pale lichen, the smoother worn bowl, meal dust on the rim, moss and soil at the foot; the collision box is the mortar only']}
PROPS['YP04']=YP04

# ---------------- YP05 wooden benches, long and short (cand-4) ----------------
def _bench(M,pid,L,seed,patch):
    """a thick plank seat dished where people sit, its edges not straight; four square legs splayed toward the ends and
    to front and back, their tenons through the seat (end grain shows on top); a short rail at each end and a long rail
    front and back, the rail tenons through the legs and keyed with a wedge."""
    rr=random.Random(seed);WD,WB,EG=M['cedar'],M['cedar_b'],M['endgrain'];W=.26;H=.45;T=.076;NSt=11;st=[]
    ph=[rr.uniform(0,6.28) for _ in range(4)]
    for i in range(NSt):
        u=i/(NSt-1);x=-L/2+L*u;dish=.016*math.sin(math.pi*u)**1.5+.004*math.sin(3*math.pi*u+ph[0])*math.sin(math.pi*u)
        w=W+.010*math.sin(2.2*math.pi*u+ph[1])+.006*math.sin(5*math.pi*u+ph[2])-(.012 if i in (0,NSt-1) else 0)
        yo=.004*math.sin(1.7*math.pi*u+ph[3]);st.append(((x,yo,H-T/2-dish/2),w,T-dish,.013))
    seat=_beam(f'{pid}_Seat',st,WD,'Body',jit=.0015,seed=seed)
    xb=(-L/2+.19) if patch else (L/2-.092);ub=(xb+L/2)/L   # a cord binding round the seat (on the long bench it holds a split end together)
    dsh=.016*math.sin(math.pi*ub)**1.5+.004*math.sin(3*math.pi*ub+ph[0])*math.sin(math.pi*ub);hw=(W+.010*math.sin(2.2*math.pi*ub+ph[1])+.006*math.sin(5*math.pi*ub+ph[2]))/2;hh=(T-dsh)/2
    yb=.004*math.sin(1.7*math.pi*ub+ph[3]);zb=H-T/2-dsh/2;sg=lambda v:(1 if v>=0 else -1)*abs(v)**.42;pts=[]
    for i in range(4*16+1):
        f_=i/16*math.tau;pts.append(Vector((xb+.0102*i/16,yb+(hw+.0042)*sg(math.cos(f_)),zb+(hh+.0042)*sg(math.sin(f_)))))
    tube(f'{pid}_Bind',pts,.0046,M['hemp'],'Body',sides=6,scale=.06)   # a single cord (a laid rope here cost 15,000 triangles)
    o=_blob(f'{pid}_BindKnot',(.030,.026,.020),seed+50,M['hemp'],'Body',sub=2,bumps=4,amp=.12,scale=.06);o.data.transform(Matrix.Translation((xb+.02,yb-.05,zb+hh-.003)))
    if patch and seat is not None:
        cut=_cutter(f'{pid}_cutSplit',(.30,.0045,.14),(0,0,0));cut.data.transform(Matrix.Rotation(.035,4,'Z'));cut.data.transform(Matrix.Translation((-L/2+.12,.034,H-.04)));_boolean(seat,cut)   # the end is split along the grain
    lx0=L/2-.125;lx1=L/2-.050;ly0=W/2-.058;ly1=W/2+.024;ZT=H-T+.012
    def legpt(sx,sy,z):
        a=Vector((sx*lx1,sy*ly1,0));b=Vector((sx*lx0,sy*ly0,ZT));return a.lerp(b,z/ZT)
    for q,(sx,sy) in enumerate(((-1,-1),(1,-1),(-1,1),(1,1))):
        o=_bar(f'{pid}_Leg{q}',legpt(sx,sy,-.014),legpt(sx,sy,ZT),.072,.062,WB if q%3 else WD,'Body',up=(1,0,0),bev=.005,seed=seed+q,ends=(1.06,.94));_flat_foot(o)
        t0=legpt(sx,sy,ZT-.02);dz=(legpt(sx,sy,ZT)-legpt(sx,sy,0)).normalized()
        o=_bar(f'{pid}_Tenon{q}',t0,t0+dz*((H+.004-t0.z)/dz.z),.040,.028,EG,'Body',up=(1,0,0),bev=.002,jit=.0004,seed=seed+10+q)   # through the seat
        u_=(sx*lx0+L/2)/L;zt=H-(.016*math.sin(math.pi*u_)**1.5+.004*math.sin(3*math.pi*u_+ph[0])*math.sin(math.pi*u_))+.004
        for v in o.data.vertices:v.co.z=min(v.co.z,zt)   # sawn off 4 mm proud of the seat
    zs=.150;zl=.205
    for q,sx in enumerate((-1,1)):   # short end rails, through both legs
        a=legpt(sx,-1,zs);b=legpt(sx,1,zs);dv=(b-a).normalized()
        _bar(f'{pid}_EndRail{q}',a-dv*.058,b+dv*.058,.030,.044,WD,'Body',up=(0,0,1),bev=.004,seed=seed+20+q)
        for j,(p,s) in enumerate(((a,-1),(b,1))):
            k=p+dv*s*.043;_bar(f'{pid}_EndKey{q}{j}',k+Vector((0,0,-.030)),k+Vector((.004*sx,0,.034)),.010,.012,WB,'Detail_Keys',up=(1,0,0),bev=.0015,jit=0,ends=(.7,1.15))
    for q,sy in enumerate((-1,1)):   # long rails front and back
        a=legpt(-1,sy,zl);b=legpt(1,sy,zl);dv=(b-a).normalized()
        _bar(f'{pid}_Rail{q}',a-dv*.062,b+dv*.062,.030,.046,WB,'Body',up=(0,0,1),bev=.004,seed=seed+30+q,jit=.0012)
        for j,(p,s) in enumerate(((a,-1),(b,1))):
            k=p+dv*s*.047;_bar(f'{pid}_Key{q}{j}',k+Vector((0,0,-.031)),k+Vector((0,.004*sy,.035)),.010,.012,WD,'Detail_Keys',up=(0,1,0),bev=.0015,jit=0,ends=(.7,1.15))
    if patch:   # a mended place on the front edge of the seat
        o=box(f'{pid}_Patch',(.19,.009,.034),(patch,-W/2-.0005,H-.034),WB,'Body',bev=.002,segs=1,jit=.0008,seed=seed+40)
        for q,dx in enumerate((-.075,-.025,.03,.078)):
            p=Vector((patch+dx,-W/2-.005,H-.034+.006*(-1)**q));_lathe(f'{pid}_Nail{q}',[(0,.0035),(1,0)],(p,p+Vector((0,-.0025,0))),M['iron'],'Detail_Keys',NS=6,scale=.03)
    R_={};kn=[(rr.uniform(-L*.36,L*.36),rr.uniform(-.08,.08),rr.uniform(.012,.022)) for _ in range(3 if L>1 else 2)]
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];h=np.zeros(px.shape,np.float32)
        wood=filled*(col[...,0]>col[...,2]*1.3);bind=(np.abs(px-xb-.02)<.034)*(pz>H-T-.012)
        sm=wood*(pz>H-T-.008)*(1-bind);lg=wood*(pz<=H-T-.008)*(np.abs(px)>lx0-.07)*(np.abs(pz-.150)>.026)*(np.abs(pz-.205)>.027)
        col,rough=_wood_age(col,rough,h,P,sm,0,seed,edge,checks=1.2,grey=.30)
        col,rough=_wood_age(col,rough,h,P,lg,2,seed+60,edge,grey=.15)
        a1,a2,aid,_,_=_wor(P,(8.,20.,20.),seed+70);h+=sm*.0011*(a1-.45)                       # shallow adze scallops along the plank
        top=sm*(onrm[...,2]>.7);P2=P*np.array([1,1,0],np.float32)
        for kx,ky,kr in kn:col=_knot(col,h,P2,(kx,ky,0),kr,top)
        top=filled*(pz>H-.03)*np.clip(onrm[...,2],0,1)
        sit=top*np.clip(1-(np.abs(py)/(W*.42))**2,0,1)*np.clip(.45+.8*noise,0,1)*np.clip(1-(np.abs(px)/(L*.46))**4,0,1)
        col=col*(1+.16*sit[...,None]);rough=np.clip(rough-.22*sit,0,1)                      # sat smooth and pale along the middle
        foot=filled*np.clip((.07-pz)/.07,0,1)*np.clip(.3+noise,0,1);col=col*(1-.45*foot[...,None])+foot[...,None]*.45*np.array([.23,.18,.12])   # mud on the feet
        ms=filled*np.clip((noise-.6)*4,0,1)*np.clip((.16-pz)/.1,0,1);col=col*(1-.4*ms[...,None])+ms[...,None]*.4*np.array([.22,.30,.11])
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':1.,'grime':.9,'uv_angle':60,'collision_box':((L,.30,H),(0,0,H/2)),
            'notes':['a thick plank seat, dished in the middle (in the shape), its edges not straight; four legs splayed toward the ends and to front and back, their tenons through the seat, sawn off 4 mm proud',
                     'a short rail at each end and a long rail front and back; the rail tenons go through the legs and are keyed with wedges (Detail_Keys)'+('; a nailed mending board on the front edge of the seat; one end is split along the grain and bound round with four turns of cord' if patch else '; four turns of cord bound round one end of the seat'),
                     'painted, with the relief also in the normal map: checks along the grain, knots, shallow adze scallops, sun-greyed patches; the seat worn pale and smooth along the middle, mud and a little moss on the feet']}
PROPS['YP05_01']=lambda M:_bench(M,'YP05_01',1.50,6501,.36)
PROPS['YP05_02']=lambda M:_bench(M,'YP05_02',.62,6502,0)
