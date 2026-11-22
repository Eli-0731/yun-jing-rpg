# DP18 松果與落果 (three kinds) and DP19 落葉堆 (three kinds) — exec'd by build_floor.py after floor_items1.py.
# Every scale, nut and leaf is its own modelled piece (no cards); the leaf piles have a low dark core under the leaves.

def _litter_sources(S):
    K.rng=np.random.default_rng(1801)   # dry leaf: russet / ochre / faded brown, a darker midrib, spots
    mid=np.exp(-((X-.5)/.04)**2);t=np.clip(.5+.7*(fbm(4,3)-.5),0,1);spot=np.clip((fbm(18,2)-.64)*4,0,1)
    vein=np.clip(.5+.5*np.sin(math.tau*(Y*10+np.abs(X-.5)*5)),0,1)**8*(1-mid)
    def leaf(lo,hi):return (lerp(lo,hi,t)*(1-.3*spot[...,None])-mid[...,None]*.04-vein[...,None]*.03,.6*mid+.4*vein+.3*fbm(30,2),1.3,.82,0,0)
    S['leaf_russet']=leaf((.24,.10,.05),(.44,.22,.10))
    S['leaf_ochre']=leaf((.34,.22,.08),(.54,.38,.16))
    S['leaf_brown']=leaf((.18,.12,.07),(.34,.24,.14))
    S['leaf_wet']=leaf((.06,.04,.025),(.15,.09,.05))   # wet leaves under the pile: dark
    K.rng=np.random.default_rng(1802)
    f=np.clip((fbm(30,2,aniso=6)-.5)*2+.5,0,1)
    S['cone']=(lerp((.16,.09,.05),(.36,.22,.12),np.clip(.5+.5*(fbm(5,3)-.5)+.3*(f-.5),0,1))*(1-.35*np.clip((Y-.75)*4,0,1))[...,None]+np.clip((Y-.85)*6,0,1)[...,None]*np.array([.12,.10,.07]),.8*f,1.4,.85,0,0)   # scale tips paler, worn
    S['nut']=(lerp((.18,.10,.05),(.36,.22,.11),np.clip(.5+.5*(fbm(6,3)-.5),0,1)),.4*fbm(40,2),1.,.55,0,0)
    S['acorncap']=(lerp((.16,.12,.08),(.30,.24,.16),np.clip(.5+.6*(fbm(60,2)-.5),0,1)),1.2*fbm(80,1),2.,.9,0,0)
    S['fruit']=(lerp((.18,.05,.04),(.34,.11,.07),np.clip(.5+.6*(fbm(5,3)-.5),0,1))*(1-.25*np.clip((fbm(20,2)-.6)*4,0,1))[...,None],.4*fbm(30,2),1.,.5,0,0)
    S['fruit_in']=(lerp((.42,.30,.18),(.60,.46,.28),np.clip(.5+.6*(fbm(10,2)-.5),0,1)),.6*fbm(40,2),1.,.7,0,0)
    S['duff']=(lerp((.05,.035,.02),(.12,.08,.05),np.clip(.5+.6*(fbm(6,3)-.5),0,1)),.8*fbm(30,2),1.4,.9,0,0)
SRC_HOOKS.append(_litter_sources)

def _leafp(name,base,d,n,L,W,M,mat,grp,shape='oval',seg=4,fold=.12,curl=.15,teeth=0,lobes=0):
    """one modelled leaf: outline by shape (oval, lance, round, lobed), a midrib fold, a curl; u across, v base → tip"""
    d=Vector(d).normalized();n=Vector(n);s=d.cross(n).normalized();n=s.cross(d).normalized();base=Vector(base)
    rl=_rnd.Random(_zl.crc32(name.encode())).uniform(-.45,.45);n.rotate(Matrix.Rotation(rl,3,d));s=d.cross(n).normalized()
    def wid(t):
        w=math.sin(math.pi*t)**.8 if shape!='round' else math.sin(math.pi*t)**.55
        if lobes:w*=1+.28*max(0.,math.sin(t*lobes*math.pi))**2   # lobed (maple / oak-like) edge
        return w
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');rows=[]
    for i in range(seg+1):
        t=i/seg;w=max(.0004,W*wid(t)/2);c=base+d*L*t-n*curl*L*t*t
        rows.append((bm.verts.new(c-s*w-n*fold*w),bm.verts.new(c+n*fold*w*.2),bm.verts.new(c+s*w-n*fold*w)))
    for i in range(seg):
        a,b=rows[i],rows[i+1]
        for p,q in ((0,1),(1,2)):
            fc=bm.faces.new((a[p],a[q],b[q],b[p]))
            for l,(cc,rr) in zip(fc.loops,((p,i),(q,i),(q,i+1),(p,i+1))):l[lay].uv=((0,.5,1)[cc],rr/seg)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,M[mat],grp,keep_uv=True)

def _ellip(name,c,r,M,mat,grp,seed,seg=8,ring=6,up=(0,0,1),squash=1.,bump=0.):
    r_=_rnd.Random(seed);c=Vector(c);ax=Vector(up).normalized();u=ax.orthogonal().normalized();v=ax.cross(u);bm=bmesh.new();V=[]
    top=bm.verts.new(c+ax*r[2]);bot=bm.verts.new(c-ax*r[2])
    for i in range(1,ring):
        a=math.pi*i/ring;row=[]
        for k in range(seg):
            b=math.tau*k/seg;rr=1+bump*r_.uniform(-1,1)
            row.append(bm.verts.new(c+(u*math.cos(b)*r[0]+v*math.sin(b)*r[1])*math.sin(a)*rr+ax*math.cos(a)*r[2]))
        V.append(row)
    for k in range(seg):
        k1=(k+1)%seg;bm.faces.new((top,V[0][k],V[0][k1]));bm.faces.new((bot,V[-1][k1],V[-1][k]))
        for i in range(ring-2):bm.faces.new((V[i][k],V[i+1][k],V[i+1][k1],V[i][k1]))
    for f in bm.faces:f.smooth=True
    return finish(name,bm,M[mat],grp,scale=.05)

# ---------------- DP18 (three-views: art/references/DP18/prompt.txt) ----------------
def _cone(name,c,L,R,lie,M,grp,seed,n=64):
    """a pine cone lying on its side: a spindle core, scales on a golden-angle spiral, opened outward, tips up"""
    r_=_rnd.Random(seed);c=Vector(c);ax=Vector((math.cos(lie),math.sin(lie),0.));up=Vector((0,0,1));sd=ax.cross(up)
    _ellip(name+'_core',c+up*R*.75,(R*.45,R*.45,L*.48),M,'cone',grp,seed,seg=8,ring=6,up=ax)
    for i in range(n):
        t=(i+.5)/n;a=i*2.39996;prof=math.sin(math.pi*min(.98,t*1.05))**.7
        p=c+up*R*.75+ax*(L*(t-.5)*.95)+(up*math.cos(a)+sd*math.sin(a))*R*.35*prof
        rad=(up*math.cos(a)+sd*math.sin(a));out=rad*.75+ax*1.0   # scales lean toward the tip and overlap in rows (an opened cone)
        _leafp(f'{name}_s{i}',p,out,rad,R*(.38+.38*prof),R*(.42+.3*prof),M,'cone',grp,shape='round',seg=3,fold=.2,curl=-.35)
def dp18_01(M):
    """三顆松果 (DP18A-cand-3): three opened pine cones 6–9 cm lying on the ground"""
    for i,(x,y,L,lie) in enumerate(((0,0,.085,.3),(-.07,.035,.07,1.9),(.06,.045,.062,-1.0))):
        _cone(f'DP18_01_c{i}',(x,y,-.004),L,L*.32,lie,M,'Body',18101+i)
    return {'grime':.5,'wear':.3}
def dp18_02(M):
    """堅果與殼斗 (DP18B-cand-3): eight small nuts and acorn-like seeds with caps, two dry leaves"""
    r_=_rnd.Random(18201)
    for i in range(8):
        a=r_.uniform(0,math.tau);rr=math.sqrt(r_.random())*.08;x,y=math.cos(a)*rr,math.sin(a)*rr*.8;s=r_.uniform(.010,.016);lie=r_.uniform(0,math.tau)
        ax=Vector((math.cos(lie),math.sin(lie),r_.uniform(-.2,.6))).normalized()
        _ellip(f'DP18_02_n{i}',(x,y,s*.75),(s*.8,s*.8,s*1.15),M,'nut','Body',18210+i,seg=8,ring=6,up=ax)
        if i%3!=2:_ellip(f'DP18_02_k{i}',Vector((x,y,s*.75))+ax*s*.85,(s*.85,s*.85,s*.45),M,'acorncap','Body',18230+i,seg=8,ring=4,up=ax,bump=.06)
    for i,(x,y,a) in enumerate(((-.05,-.04,.5),(.06,.03,2.4))):
        _leafp(f'DP18_02_l{i}',(x,y,.002),(math.cos(a),math.sin(a),.02),(0,0,1),.075,.04,M,'leaf_brown','Body',shape='oval',seg=4,fold=.15,curl=-.1)
    return {'grime':.5,'wear':.2}
def dp18_03(M):
    """野果 (DP18C-cand-1): five round dull-red wild fruits 2–3 cm, one split open, among two dry leaves"""
    r_=_rnd.Random(18301)
    for i,(x,y,r) in enumerate(((0,0,.014),(.03,.01,.012),(-.028,.012,.013),(.012,-.028,.011),(-.015,-.03,.012))):
        if i==4:   # split open: two halves with the pale flesh showing
            for h,sgn in enumerate((-1,1)):
                _ellip(f'DP18_03_f{i}h{h}',(x+sgn*.006,y,r*.7),(r,r,r*.6),M,'fruit','Body',18320+h,seg=10,ring=5,up=(sgn*.9,0,.4))
                _ellip(f'DP18_03_f{i}in{h}',(x+sgn*.0035,y,r*.75),(r*.8,r*.8,r*.25),M,'fruit_in','Body',18330+h,seg=10,ring=3,up=(sgn*.9,0,.4))
        else:_ellip(f'DP18_03_f{i}',(x,y,r*.85),(r,r,r*.9),M,'fruit','Body',18310+i,seg=10,ring=7)
    for i,(x,y,a) in enumerate(((-.04,.02,2.0),(.035,-.025,-.6))):
        _leafp(f'DP18_03_l{i}',(x,y,.002),(math.cos(a),math.sin(a),.03),(0,0,1),.085,.045,M,'leaf_brown','Body',shape='oval',seg=4,fold=.2,curl=-.12)
    return {'grime':.5,'wear':.2}

# ---------------- DP19 leaf piles (three-views: art/references/DP19/prompt.txt) ----------------
def _pile(name,rx,ry,H,n,M,grp,seed,ridge=False,seg=3):
    """a pile of separate curled leaves over a low dark core: the leaves are dropped onto a mound surface in layers,
    the lower layers wet and dark, the top dry russet / ochre / brown"""
    r_=_rnd.Random(seed)
    def hz(x,y):
        q=(x/rx)**2+(y/ry)**2
        h=H*max(0.,1-q)**.9
        if ridge:h=H*max(0.,1-(x/rx)**2)**.8*max(0.,1-((y+ry*.3)/ry)**2)**.6   # a drift piled against an edge on +Y
        return h
    _pad(name+'_core',(0,-ry*.3 if ridge else 0,-.002),rx*.85,ry*(.7 if ridge else .85),H*.92,M,grp,seed+1,segs=20,mat='duff',skirt='duff',depth=.01,noise=.12)
    for i in range(n):
        a=r_.uniform(0,math.tau);rr=math.sqrt(r_.random())*1.02;x,y=math.cos(a)*rr*rx,math.sin(a)*rr*ry
        layer=i/n;z=hz(x,y)*(.72+.28*layer)+.002   # each layer rests on the one below (no leaf hovering over the pile)
        mat='leaf_wet' if layer<.25 else r_.choice(('leaf_russet','leaf_ochre','leaf_brown','leaf_russet'))
        b=r_.uniform(0,math.tau);d=Vector((math.cos(b),math.sin(b),r_.uniform(-.25,.25)));nn=Vector((r_.uniform(-.35,.35),r_.uniform(-.35,.35),1))
        L=r_.uniform(.055,.09);lob=r_.choice((0,0,0,5))
        _leafp(f'{name}_l{i}',(x-d.x*L*.5,y-d.y*L*.5,z),d,nn,L,L*r_.uniform(.5,.75),M,mat,grp,shape='oval',seg=seg,fold=r_.uniform(.1,.35),curl=r_.uniform(-.3,.25),lobes=lob)
def dp19_01(M):
    """小落葉堆 (DP19A-cand-2): a low small pile, 0.35 m across, 6 cm tall"""
    _pile('DP19_01',.17,.15,.05,120,M,'Body',19101,seg=4);return {'grime':.5,'wear':0}
def dp19_02(M):
    """中落葉堆 (DP19B-cand-2): 0.6 m across, 0.1 m tall, dry on top and wet below"""
    _pile('DP19_02',.29,.25,.09,230,M,'Body',19201,seg=3);return {'grime':.5,'wear':0}
def dp19_03(M):
    """落葉長條 (DP19C-cand-2): a drift 0.9 m long and 0.3 m wide piled against an edge"""
    _pile('DP19_03',.45,.15,.08,240,M,'Body',19301,ridge=True,seg=3);return {'grime':.5,'wear':0}

TABLE.update({'DP18_01':('PineConesThree',(.24,.18,.07),'standard'),'DP18_02':('NutsAndAcorns',(.24,.22,.05),'standard'),'DP18_03':('WildFruits',(.20,.16,.05),'standard'),
 'DP19_01':('LeafPileSmall',(.40,.36,.09),'standard'),'DP19_02':('LeafPileMedium',(.68,.60,.14),'standard'),'DP19_03':('LeafDrift',(1.0,.40,.13),'standard')})
PROPS.update({'DP18_01':dp18_01,'DP18_02':dp18_02,'DP18_03':dp18_03,'DP19_01':dp19_01,'DP19_02':dp19_02,'DP19_03':dp19_03})
