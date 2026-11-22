# DP10 垂藤與細藤段 (four hanging vines) and DP12 枯萎的小灌叢 (three dead shrubs) — exec'd by build_moss.py after moss_items3.py.

def _dry_sources(S):
    K.rng=np.random.default_rng(7001)   # dry twig: grey-brown, fine lengthwise cracks, a few pale lichen flecks
    f=np.clip((fbm(40,2,aniso=25)-.5)*2+.5,0,1);fl=np.clip((fbm(30,2)-.72)*5,0,1)
    S['twig']=(lerp((.14,.11,.09),(.30,.26,.22),np.clip(.5+.5*(fbm(5,3,aniso=6)-.5)+.3*(f-.5),0,1))*(1-.3*fl[...,None])+fl[...,None]*np.array([.18,.19,.16]),.9*f,1.6,.9,0,0)
    K.rng=np.random.default_rng(7002)   # dead leaf: russet to faded brown, darker veins, curled
    mid=np.exp(-((X-.5)/.05)**2);t=np.clip(.5+.6*(fbm(5,3)-.5),0,1);spot=np.clip((fbm(20,2)-.62)*4,0,1)
    S['deadleaf']=(lerp((.22,.11,.06),(.42,.25,.13),t)*(1-.3*spot[...,None])-mid[...,None]*.05,.6*mid+.4*fbm(40,2),1.2,.8,0,0)
    K.rng=np.random.default_rng(7003)   # vine stem: dark grey-brown
    f=np.clip((fbm(50,2,aniso=30)-.5)*2+.5,0,1)
    S['vine']=(lerp((.08,.07,.05),(.19,.16,.12),f),.5*f,1.,.7,0,0)
SRC_HOOKS.append(_dry_sources)

def _hang(name,top,L,M,grp,seed,sway=.04,leaf_every=.04,leaf_len=(.028,.04),shape='oval',pairs=True,coil=0.,tendrils=3,thin=1.,lseg=3):
    """one hanging vine from `top` down L metres: a slightly swaying stem, leaves along it (pairs or alternate), a few tendrils;
    coil > 0: the last part lies on the ground in a loose coil of that radius"""
    r_=_rnd.Random(seed);top=Vector(top);ph=[r_.uniform(0,6.3) for _ in range(4)]
    n=max(8,int(L/.05));pts=[]
    for i in range(n+1):
        t=i/n;z=-L*t
        pts.append(top+Vector((sway*math.sin(t*7+ph[0])*t,sway*.7*math.sin(t*5+ph[1])*t,z)))
    if coil:   # the bottom end lies on the ground (z = top.z - L) and curls
        g=pts[-1].copy();c=[g+Vector((coil*(math.cos(a)-1),coil*math.sin(a),0.)) for a in np.linspace(0,math.tau*1.2,14)[1:]]
        for p in c:p.z=g.z+.004
        pts+=c
    _tube(name+'_stem',pts,.0035*thin,.0015*thin,M,'vine',grp,sides=5)
    s=0.;nxt=r_.uniform(.0,leaf_every);k=0
    for i in range(1,len(pts)):
        a,b=pts[i-1],pts[i];seg=(b-a).length;s+=seg
        while s>=nxt:
            p=a.lerp(b,1-(s-nxt)/max(seg,1e-9));t=(b-a).normalized();taper=1-.45*min(1,nxt/max(L,1e-6))
            for sgn in ((-1,1) if pairs else ((1 if k%2 else -1),)):
                ang=(0. if sgn>0 else math.pi)+r_.uniform(-.55,.55)   # leaves to both sides of the hanging stem, faces turned out (not edge-on)
                out=Vector((math.cos(ang),math.sin(ang)*.5,-.35)).normalized();face=Vector((-math.sin(ang)*.4,1.,.25)).normalized()*(1 if r_.random()<.75 else -1)
                ll=r_.uniform(*leaf_len)*taper
                _leafp(f'{name}_l{k}_{sgn}',p,out,face,ll,ll*(.8 if shape=='heart' else .6),M,'leaf' if k%4 else 'leaf_dark',grp,shape=shape,seg=lseg,fold=.15,curl=.18)
            k+=1;nxt+=leaf_every*r_.uniform(.8,1.2)
    for j in range(tendrils):   # thin curling tendrils
        i=r_.randint(2,len(pts)-3);p=pts[i];a0=r_.uniform(0,math.tau)
        tp=[p+Vector((math.cos(a0+q)*.012*q,math.sin(a0+q)*.012*q,-.004*q)) for q in np.linspace(0,3.5,8)]
        _tube(f'{name}_td{j}',tp,.0009,.0005,M,'vine','Fine',sides=3)

def _twigs(name,p,d,L,r,M,grp,r_,depth,maxd,leaves,brk=.25):
    """recursive dry twig: a slightly bent tube, two or three children from its upper half; some tips broken off short"""
    d=Vector(d).normalized();side=d.orthogonal().normalized();side.rotate(Matrix.Rotation(r_.uniform(0,6.3),3,d))
    pts=[p+d*L*t+side*L*.08*math.sin(t*math.pi)+Vector((0,0,-.02*L*t*t)) for t in (0,.33,.66,1.)]
    _tube(name,pts,r,r*.62,M,'twig',grp if depth<maxd-1 else 'Fine',sides=4 if r>.003 else 3)   # the two finest orders go to 'Fine' (dropped at LOD2)
    if depth>=maxd or (depth>1 and r_.random()<brk):
        if r_.random()<.35 and depth>=1:leaves.append((pts[-1],d))
        return
    for c in range(r_.choice((2,2,3)) if depth<2 else 2):
        t=r_.uniform(.45,.95);q=pts[0].lerp(pts[-1],t);nd=(d+Vector((r_.uniform(-.9,.9),r_.uniform(-.9,.9),r_.uniform(-.1,.5)))).normalized()
        _twigs(f'{name}_{c}',q,nd,L*r_.uniform(.5,.72),max(.0007,r*.6),M,grp,r_,depth+1,maxd,leaves,brk)

def _deadshrub(name,H,W,M,grp,seed,stems=3,maxd=4,nleaves=10,lean=0.):
    r_=_rnd.Random(seed);_base(name+'_base',W*.18,W*.15,.006,M,grp,seed+1);leaves=[]
    for s in range(stems):
        a=math.tau*s/stems+r_.uniform(-.4,.4);d=Vector((math.cos(a)*.35+lean,math.sin(a)*.35,1.))
        _twigs(f'{name}_t{s}',Vector((math.cos(a)*.01,math.sin(a)*.01,-.01)),d,H*.40,.0045*H/.7+.0015,M,grp,r_,0,maxd,leaves)
    r_.shuffle(leaves)
    for i,(p,d) in enumerate(leaves[:nleaves]):   # curled dead leaves hanging from twig tips
        dd=(Vector((r_.uniform(-1,1),r_.uniform(-1,1),-1.2))).normalized()
        _leafp(f'{name}_dl{i}',p,dd,d.orthogonal(),r_.uniform(.03,.045),r_.uniform(.015,.022),M,'deadleaf',grp,shape='oval',seg=3,fold=.35,curl=.6)

# ---------------- DP10 vines (three-views: art/references/DP10/prompt.txt) ----------------
O_HANG='the point the vine hangs from (an edge of a root or a stone): the model is raised so its lowest point is on z = 0; the hanging point is recorded below'
def dp10_01(M):
    """單條細藤 (DP10A-cand-1): one 0.6 m vine, pairs of small oval leaves, a few tendrils"""
    _hang('DP10_01',(0,0,.6),.6,M,'Body',10101,sway=.03,leaf_every=.05,leaf_len=(.045,.06),shape='oval',pairs=True,tendrils=4,lseg=6)
    return dict(PLANT,lift_to_ground=True,origin_text=O_HANG,fine_drop=['Fine'])
def dp10_02(M):
    """兩條互纏 (DP10B-cand-1): two 1.5 m vines twisting a little round each other, heart and oval leaves, fewer toward the tips"""
    for v,(x,ph) in enumerate(((-.01,0.),(.01,math.pi))):
        pts_top=(x,0,1.5);_hang(f'DP10_02_v{v}',pts_top,1.5-.12*v,M,'Body',10201+v,sway=.07,leaf_every=.045,leaf_len=(.045,.065),shape='heart' if v else 'oval',pairs=False,tendrils=3)
    return dict(PLANT,lift_to_ground=True,origin_text=O_HANG,fine_drop=['Fine'])
def dp10_03(M):
    """長藤 (DP10C-cand-1): one 3 m vine whose end lies on the ground in a loose coil, leaves in small clusters"""
    _hang('DP10_03',(0,0,3.0),3.0,M,'Body',10301,sway=.13,leaf_every=.06,leaf_len=(.045,.065),shape='heart',pairs=True,coil=.09,tendrils=5,thin=1.25)
    return dict(PLANT,lift_to_ground=True,origin_text=O_HANG,fine_drop=['Fine'])
def dp10_04(M):
    """藤簾 (DP10D-cand-1): five thin vines of 0.6–1.2 m hanging from a 0.6 m edge"""
    _tube('DP10_04_runner',[(-.30,0,1.2),(-.15,.004,1.203),(0,-.003,1.199),(.15,.003,1.202),(.30,0,1.2)],.004,.003,M,'vine','Body',sides=5)   # the vine runs along the edge; the five strands hang from it
    for v,(x,L) in enumerate(((-.27,.75),(-.13,1.15),(0.,.9),(.14,1.2),(.27,.65))):
        _hang(f'DP10_04_v{v}',(x,0,1.2),L,M,'Body',10401+v,sway=.03,leaf_every=.045,leaf_len=(.04,.055),shape='oval',pairs=False,tendrils=1,thin=.85)
    return dict(PLANT,lift_to_ground=True,origin_text=O_HANG,fine_drop=['Fine'])

# ---------------- DP12 dead shrubs (three-views: art/references/DP12/prompt.txt) ----------------
def dp12_01(M):
    """小枯灌 (DP12A-cand-1): 0.4 m of thin dry twigs from a short base, a handful of curled brown leaves"""
    _deadshrub('DP12_01',.40,.45,M,'Body',12101,stems=3,maxd=5,nleaves=8)
    return {'grime':.5,'wear':.3,'fine_drop':['Fine']}
def dp12_02(M):
    """中枯灌 (DP12B-cand-1): 0.7 m, branching dry stems, broken twig ends, a dozen russet dead leaves"""
    _deadshrub('DP12_02',.70,.60,M,'Body',12201,stems=5,maxd=4,nleaves=13)
    return {'grime':.5,'wear':.3,'fine_drop':['Fine']}
def dp12_03(M):
    """大枯灌 (DP12C-cand-1): 1.0 m, dense dry branches with fine tips, a few clusters of dead leaves, leaning a little"""
    _deadshrub('DP12_03',1.0,.80,M,'Body',12301,stems=5,maxd=4,nleaves=14,lean=.15)
    return {'grime':.5,'wear':.3,'fine_drop':['Fine']}

PROPS.update({'DP10_01':dp10_01,'DP10_02':dp10_02,'DP10_03':dp10_03,'DP10_04':dp10_04,'DP12_01':dp12_01,'DP12_02':dp12_02,'DP12_03':dp12_03})
