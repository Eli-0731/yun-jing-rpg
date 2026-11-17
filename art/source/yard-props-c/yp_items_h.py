# YP13 shapes (the 11/14 120h pack, batch A), read by build_yp.py after yp_items_g.py (same namespace).
# Every item follows the three-view picked in art/references/YP13/prompt.txt. Blender: X = width, -Y = front, Z = up.
# Two creek-side plants for A1 (setting image V5), each its own model; every leaf, petal and grain is its own piece, no leaf cards.

def _yp13_base(pid,M,rr,W,D,n_stone,seed):
    """Detail_Base: a thin patch of damp earth under the plant and a few small water-rounded stones on its rim"""
    ph=[rr.uniform(0,6.28) for _ in range(3)]
    zf=lambda x,y:.020+.008*math.sin(x*17+ph[0])*math.sin(y*15+ph[1])+.004*math.sin(x*41+y*33+ph[2])
    _earth(f'{pid}_Earth',W,D,zf,M['soil'],'Detail_Base',NX=14,NY=12,scale=.4,p=2.4,wob=.10,seed=seed);M['soil']['mid']=1.
    for k in range(n_stone):
        a=math.tau*k/n_stone+rr.uniform(-.4,.4);s=rr.uniform(.05,.11);r=rr.uniform(.43,.48)
        _blob(f'{pid}_Stone{k}',(s,s*rr.uniform(.7,1),s*rr.uniform(.45,.65)),seed+10+k,M['stone'],'Detail_Base',sub=2,scale=.2).data.transform(Matrix.Translation((math.cos(a)*W*r,math.sin(a)*D*r,.004)))

# ---------------- YP13_01 a clump of tall creek grass in seed (water grass, cand-3) ----------------
def YP13_01(M):
    """about sixty long folded blades from one base: the middle ones upright, the outer ones arching over and hanging;
    five thin seed stalks stand above the leaves, each ending in a loose drooping panicle of small grains; a few dead
    blades lie on the ground round the base."""
    rr=random.Random(int(__import__('os').environ.get('YP_SEED',7302)))
    lw=lambda u:(.55+.45*min(1.,u/.12))*(1-u**2.2)**.8 if u<.99 else .04
    N=72
    for k in range(N):
        g=(k+.5)/N;a=k*2.39996+rr.uniform(-.25,.25);d=(math.cos(a),math.sin(a));rb=.012+.105*g**.8
        th=.04+.58*g**1.3+rr.uniform(-.04,.07);L=(1.00-.48*g)*rr.uniform(.84,1.08);dr=.14+.60*g+rr.uniform(-.06,.08)
        _blade(f'YP13_01_B{k:02d}',Vector((d[0]*rb,d[1]*rb,-.012-.0007*k)),d,L,rr.uniform(.040,.058)*(1.1-.25*g),th,dr,lw,M['reed'],'Body',nu=9,nv=2,cup=rr.uniform(.45,.8),twist=rr.uniform(-.7,.7))
    for k in range(7):   # dead blades lying out over the ground
        a=math.tau*k/7+rr.uniform(-.3,.3);d=(math.cos(a),math.sin(a));L=rr.uniform(.30,.48)
        _blade(f'YP13_01_Dead{k}',Vector((d[0]*.09,d[1]*.09,.030+.004*k)),d,L,rr.uniform(.022,.030),1.50,rr.uniform(.02,.06),lw,M['leaf_dry'],'Body',nu=6,nv=2,cup=.3,twist=rr.uniform(-1.2,1.2))
    for k in range(5):   # seed stalks: a thin culm, then a drooping panicle
        a=math.tau*k/5+rr.uniform(-.4,.4);d=Vector((math.cos(a),math.sin(a),0));s_=Vector((-d.y,d.x,0));H=rr.uniform(.98,1.20);lean=rr.uniform(.08,.22);b=d*rr.uniform(.01,.04)+Vector((0,0,-.01))
        f=lambda u,H=H,lean=lean,b=b,d=d:b+d*(lean*H*u**1.6+.10*H*max(0.,u-.78)**1.5*4)+Vector((0,0,H*u-.25*H*max(0.,u-.78)**2*4))
        us=(0,.2,.4,.6,.75,.85,.93,1.);_taper(f'YP13_01_Culm{k}',[f(u) for u in us],[.0030,.0028,.0025,.0021,.0017,.0013,.0010,.0006],M['straw'],'Body',sides=4,scale=.08)
        for j in range(16):
            u=.74+.26*j/15;p=f(u);sd=(1 if j%2 else -1);o=(s_*sd*math.cos(j*.9)+d*math.sin(j*.9)).normalized();Lb=rr.uniform(.025,.050)*(1.15-.6*(u-.74)/.26)
            e=p+o*Lb+Vector((0,0,-Lb*rr.uniform(.2,.7)));_taper(f'YP13_01_Br{k}{j:02d}',[p,p.lerp(e,.5)+Vector((0,0,.004)),e],[.0009,.0008,.0006],M['straw'],'Body',sides=3,scale=.05)
            for q in range(2):
                c=p.lerp(e,.55+.45*q);gd=(o+Vector((0,0,-.9))).normalized();r=rr.uniform(.0024,.0032)
                _taper(f'YP13_01_Gr{k}{j:02d}{q}',[c,c+gd*.004,c+gd*.010],[.0007,r,.0005],M['grain'],'Body',sides=4,scale=.04)
    _yp13_base('YP13_01',M,rr,.52,.48,5,7310)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);pz=P[...,2];pr=np.hypot(P[...,0],P[...,1])
        lf=filled*(mid<.5)*(col[...,1]>col[...,0]*1.12)
        out=lf*np.clip((pr-.22)/.25,0,1)*np.clip(.2+1.6*(_fb(P,(9.,9.,5.),7320,2)-.3),0,1);col=col*(1-.55*out[...,None])+out[...,None]*.55*np.array([.66,.58,.26])    # the hanging outer ends yellowing
        tip=lf*np.clip((pz-.78)/.15,0,1);col=col*(1-.35*tip[...,None])+tip[...,None]*.35*np.array([.70,.66,.32])
        low=lf*np.clip((.16-pz)/.14,0,1);col=col*(1-.45*low[...,None])+low[...,None]*.45*np.array([.42,.34,.18]);rough=np.clip(rough+.06*low,0,1)                      # brown, dead sheaths at the base
        spot=lf*np.clip((_vn(P,(70.,70.,25.),7321)-.84)*12,0,1);col=col*(1-.5*spot[...,None])+spot[...,None]*.5*np.array([.44,.32,.14])                               # brown spots
        soil=filled*(mid>.5);col=col*(1-.25*soil[...,None]);rough=np.clip(rough-.12*soil*np.clip(noise*1.5,0,1),0,1)                                                  # damp earth
        return col,rough
    return {'paint':paint,'wear':.3,'grime':.4,'ao_k':.5,'uv_angle':60,
            'notes':['a clump of tall creek grass about 1 m high: 72 long folded blades, upright in the middle, arching and hanging on the outside; every blade is its own piece, no leaf cards',
                     'five seed stalks above the leaves, each with a drooping panicle (16 small branches, 32 grains); seven dead blades lying round the base',
                     'Detail_Base (a thin patch of damp earth and five small stones) is off at the standard tier; the blades start 1 cm under the ground so the clump can be pressed into uneven ground; no collision',
                     'painted: yellowing outer ends and tips, brown dead sheaths at the base, brown spots']}
PROPS['YP13_01']=YP13_01

# ---------------- YP13_02 a low clump of small white flowers (cand-4) ----------------
def YP13_02(M):
    """a low bushy clump: broad toothed leaves at the base, twenty thin stems with paired leaves growing smaller upwards;
    each stem forks at the top into three stalks carrying a small five-petalled flower or a bud. Most flowers are white,
    a few pale purple."""
    rr=random.Random(int(__import__('os').environ.get('YP_SEED',7353)))
    for k in range(16):   # the broad basal leaves
        a=k*2.39996+rr.uniform(-.2,.2);d=(math.cos(a),math.sin(a));L=rr.uniform(.12,.17);g=(k*.618)%1
        _blade(f'YP13_02_Base{k:02d}',Vector((d[0]*(.03+.006*k),d[1]*(.03+.006*k),.014+.003*k)),d,L,L*rr.uniform(.52,.62),.80+.028*k,rr.uniform(.25,.5),lambda u:_leaf_oval(u,.07),M['herb_dark'],'Body',nu=6,nv=2,cup=rr.uniform(.15,.3),twist=rr.uniform(-.3,.3))
    nf=0
    for k in range(20):
        a=k*2.39996+rr.uniform(-.2,.2);g=(k+.5)/20;cr=.02+.17*g**.7;Ht=rr.uniform(.22,.33)*(1.05-.30*g)
        f=_stemf(f'YP13_02_Stem{k:02d}',(cr*math.cos(a),cr*math.sin(a),-.008),a,Ht,.15+.55*g+rr.uniform(-.1,.1),.0024,M['vine'],bow=rr.uniform(-.08,.08));a0=rr.uniform(0,math.tau)
        for i in range(5):
            u=.30+.54*i/4
            for j in range(2):
                la=a0+i*math.pi/2+j*math.pi+rr.uniform(-.3,.3);L=.092*rr.uniform(.8,1.1)*(1-.50*i/4)
                _blade(f'YP13_02_L{k:02d}{i}{j}',f(u)+Vector((0,0,.002*j)),(math.cos(la),math.sin(la)),L,L*.52,rr.uniform(.9,1.35),rr.uniform(.2,.5),lambda u_:_leaf_oval(u_,.07),M['herb'],'Body',nu=4,nv=2,cup=.3,twist=rr.uniform(-.3,.3))
        top=f(1.)
        for j in range(3):   # the fork: three thin stalks, a flower or a bud on each
            fa=a0+math.tau*j/3+rr.uniform(-.3,.3);Lp=rr.uniform(.030,.055);o=Vector((math.cos(fa),math.sin(fa),0));e=top+o*Lp*.55+Vector((0,0,Lp))
            _taper(f'YP13_02_Ped{k:02d}{j}',[top+o*.0030+Vector((0,0,-.002+.0015*j)),top.lerp(e,.5)+o*.005,e],[.0012,.0011,.0010],M['vine'],'Body',sides=4,scale=.05,up=(math.cos(fa+.6+.5*j),math.sin(fa+.6+.5*j),.4))
            if rr.random()<.68:
                nf+=1;pm=M['petal'] if rr.random()<.2 else M['petal_white'];r=rr.uniform(.016,.020);p0=rr.uniform(0,6.28)
                for q in range(5):
                    pa=p0+math.tau*q/5;_blade(f'YP13_02_P{k:02d}{j}{q}',e+Vector((math.cos(pa)*.0042,math.sin(pa)*.0042,.0009*q)),(math.cos(pa),math.sin(pa)),r,r*.68,.93+.22*(q%2)+.03*q,rr.uniform(-.1,.15),lambda u_:.12+.88*math.sin(math.pi*min(1.,u_*.86+.02))**.7,pm,'Body',nu=3,nv=2,cup=.25,scale=.05)
                _taper(f'YP13_02_Eye{k:02d}{j}',[e+Vector((0,0,-.0015)),e+Vector((0,0,.0012)),e+Vector((0,0,.0034))],[.0052,.0048,.0008],M['pollen'],'Body',sides=5,scale=.03)
            else:
                dn=(e-top).normalized();_taper(f'YP13_02_Bud{k:02d}{j}',[e-dn*.002,e+dn*.003,e+dn*.009],[.0012,.0036,.0008],M['petal_white'],'Body',sides=5,scale=.04)
                _taper(f'YP13_02_Cal{k:02d}{j}',[e-dn*.003,e+dn*.0005,e+dn*.0042],[.0011,.0030,.0034],M['herb_dark'],'Body',sides=5,scale=.04)
    _yp13_base('YP13_02',M,rr,.50,.46,4,7360)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);pz=P[...,2]
        lf=filled*(mid<.5)*(col[...,1]>col[...,0]*1.15)*(col[...,1]>col[...,2]*1.15)
        yl=lf*np.clip((_fb(P,12.,7370,2)-.56)*4,0,1);col=col*(1-.32*yl[...,None])+yl[...,None]*.32*np.array([.58,.62,.24])        # some leaves yellow-green
        low=lf*np.clip((.06-pz)/.05,0,1)*np.clip(.3+noise,0,1);col=col*(1-.35*low[...,None])+low[...,None]*.35*np.array([.34,.28,.15])   # the lowest leaves splashed with earth
        soil=filled*(mid>.5);col=col*(1-.25*soil[...,None]);rough=np.clip(rough-.12*soil*np.clip(noise*1.5,0,1),0,1)
        return col,rough
    return {'paint':paint,'wear':.3,'grime':.4,'ao_k':.5,'uv_angle':60,
            'notes':[f'a low clump about 0.35 m high: 16 broad basal leaves, 20 thin stems with paired toothed leaves (200), each stem forking into three stalks: {nf} five-petalled flowers (mostly white, a few pale purple) and {60-nf} buds',
                     'every leaf and petal is its own piece, no leaf cards; the flower eye is a small yellow dome',
                     'Detail_Base (a thin patch of damp earth and four small stones) is off at the standard tier; the stems start under the ground so the clump can be pressed into uneven ground; no collision']}
PROPS['YP13_02']=YP13_02
