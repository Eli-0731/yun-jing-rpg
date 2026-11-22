# DP04 苔上的小菇與黏菌 (three kinds, 2–5 cm, for dotting the moss) — exec'd by build_dp.py after dp_items3.py

def _tiny_sources(S):
    """tiny bonnet caps (dull tan-ochre, paler rim), their gills and hair-thin stems; slime mould (muted mustard veins,
    dark umber sporangia, cream-ochre blobs)"""
    K.rng=np.random.default_rng(5401)
    groove=.5+.5*np.sin(math.tau*X*30+.4*fbm(6,2));gr=np.clip((.35-groove)*3,0,1)*np.clip((Y-.2)*2.5,0,1)
    t=np.clip(.55+.6*(fbm(5,3)-.5),0,1);mid=np.clip(1-Y*2.4,0,1)**1.4;rim=np.clip((Y-.8)*5,0,1)
    col=lerp((.36,.26,.15),(.52,.40,.25),t)*(1-.15*gr[...,None])
    col=col*(1-mid[...,None])+np.array([.30,.20,.11])[None,None,:]*mid[...,None]
    col=col*(1-rim[...,None])+np.array([.64,.56,.42])[None,None,:]*rim[...,None]
    S['tcap']=(col,1.2*groove+.4*fbm(20,2),1.4,.6,0,0)
    ln=.5+.5*np.sin(math.tau*X*40);S['tgill']=(lerp((.50,.44,.33),(.64,.57,.44),t)*(1-.35*np.clip((.25-ln)*4,0,1)[...,None]),1.2*ln,2.,.75,0,0)
    fib=np.clip((fbm(60,2,aniso=40)-.5)*2+.5,0,1);S['tstem']=(lerp((.50,.44,.34),(.66,.60,.48),np.clip(.5+.3*(fib-.5)+.3*(fbm(4,3)-.5),0,1)),.6*fib,.8,.6,0,0)
    K.rng=np.random.default_rng(5402)
    lump=fbm(40,2);t=np.clip(.5+.6*(fbm(6,3)-.5)+.3*(lump-.5),0,1)
    S['slime']=(lerp((.38,.30,.08),(.58,.47,.16),t),1.2*lump,1.6,.45,0,0)   # muted mustard, a little wet (low roughness)
    S['spore']=(lerp((.07,.045,.03),(.16,.10,.06),np.clip(.5+.6*(fbm(8,2)-.5),0,1)),.4*fbm(30,2),1.,.55,0,0)
    S['blob']=(lerp((.52,.44,.30),(.70,.61,.44),np.clip(.5+.6*(fbm(6,3)-.5),0,1)),.5*fbm(20,2),1.,.6,0,0)
SRC_HOOKS.append(_tiny_sources)

def _surf(o,x,y):
    """z of the top of object o (no modifiers, at the origin) above (x, y): a ray straight down"""
    ok,loc,n,i=o.ray_cast(Vector((x,y,1.)),Vector((0,0,-1.)))
    return (loc.z,n) if ok else (0.,Vector((0,0,1)))

def _sphere(name,c,r,squash,M,mat,grp,seed,seg=8,ring=5):
    r_=_rnd.Random(seed);c=Vector(c);bm=bmesh.new();V=[]
    top=bm.verts.new(c+Vector((0,0,r*squash)));bot=bm.verts.new(c-Vector((0,0,r*squash)))
    for i in range(1,ring):
        a=math.pi*i/ring;row=[]
        for k in range(seg):
            b=math.tau*k/seg;rr=r*(1+r_.uniform(-.06,.06))
            row.append(bm.verts.new(c+Vector((math.sin(a)*math.cos(b)*rr,math.sin(a)*math.sin(b)*rr,math.cos(a)*r*squash))))
        V.append(row)
    for k in range(seg):
        k1=(k+1)%seg;bm.faces.new((top,V[0][k],V[0][k1]));bm.faces.new((bot,V[-1][k1],V[-1][k]))
        for i in range(ring-2):bm.faces.new((V[i][k],V[i+1][k],V[i+1][k1],V[i][k1]))
    for f in bm.faces:f.smooth=True
    return finish(name,bm,M[mat],grp,scale=.04)

# ---------------- DP04 items (three-views: art/references/DP04/prompt.txt) ----------------
def dp04_01(M):
    """苔上小菇 (DP04A-cand-3): nine tiny bonnet mushrooms (2–5 cm) and two buttons on a low cushion of moss (0.12 m)"""
    _rnd.seed(4001);r_=_rnd.Random(4011);Mt=_Mw(M,'t')
    pad=_pad('DP04_01_pad',(0,0,0),.064,.052,.012,M,'Body',4012,segs=22);bpy.context.view_layer.update()
    S=[(-.004,.002,.050,.0085),(-.030,.008,.036,.0068),(.022,-.006,.040,.0072),(-.018,-.014,.028,.0055),(.036,.010,.030,.006),
       (.008,.016,.026,.0052),(-.042,-.010,.022,.0046),(.012,-.020,.022,.0045),(.044,-.014,.020,.0042)]
    for i,(x,y,H,R) in enumerate(S,1):
        z,_=_surf(pad,x,y)
        _shroom(f'DP04_01_m{i}',(x,y,z-.004),(r_.uniform(-.08,.08)+x*1.2,r_.uniform(-.06,.06)+y*1.2),H+.004,R,Mt,'Body',4020+i,segs=14 if R>.006 else 12,
                stem_r=max(.0009,R*.13),bend=.4,thick=.62,umbo=.10,droop=.30,under=.12,gill=.03,wave=.03,arch=1.4,young=.25)
    for i,(x,y) in enumerate(((-.008,-.022),(.028,.018)),1):
        z,_=_surf(pad,x,y);_shroom(f'DP04_01_b{i}',(x,y,z-.004),(0,0),.012,.0028,Mt,'Body',4040+i,segs=10,stem_r=.0009,bend=.1,thick=.6,umbo=0,droop=.05,under=.1,gill=.02,young=.9)
    return {'notes':'nine tiny bonnet mushrooms (2–5 cm) and two buttons on a low moss cushion'}

def dp04_02(M):
    """黏菌 (DP04B-cand-1): a mustard slime-mould net over moss and wet wood chips, a tuft of stalked dark sporangia and two cream blobs"""
    _rnd.seed(4002);r_=_rnd.Random(4111)
    pad=_pad('DP04_02_pad',(0,0,0),.072,.058,.014,M,'Body',4112,segs=24);bpy.context.view_layer.update()
    for i,(x,y,a) in enumerate(((-.04,.012,.4),(.035,-.02,-.3),(.05,.02,1.2)),1):   # wet wood chips poking out of the moss
        _chip(f'DP04_02_chip{i}',(x,y,-.002),.018,.008,.006,M,'Body',4120+i,segs=10)
    # plasmodium: a branching net of veins from two hubs, lying on the moss
    def vein(name,p0,ang,L,r0,depth):
        pts=[];x,y=p0;n=5;s0=.004 if depth==0 else .0   # main veins leave the hub from its rim (no tubes stacked in its centre)
        for k in range(n+1):
            t=k/n;d=s0+L*t;a_=ang+.5*math.sin(t*4+depth);xx=x+math.cos(a_)*d;yy=y+math.sin(a_)*d
            z,_=_surf(pad,xx,yy);pts.append((xx,yy,z+r0*.15))   # pressed into the moss
        tube(name,pts,r0,M['slime'],'Body',sides=4,caps=True,up=(0,0,1))
        if depth<1:   # one level of side branches, starting a little off the parent's axis (their ends inside the parent, not coplanar)
            for j in range(2):
                i_=2+j;sx,sy=pts[i_][:2];bb=ang+(.8 if j else -.8)
                vein(f'{name}_{j}',(sx+math.cos(bb)*r0*.6,sy+math.sin(bb)*r0*.6),bb+r_.uniform(-.2,.2),L*.6,r0*.7,depth+1)
    for h,(hx,hy) in enumerate(((-.012,.0),(.024,.004)),1):
        z,_=_surf(pad,hx,hy);_sphere(f'DP04_02_hub{h}',(hx,hy,z+.001),.0055,.45,M,'slime','Body',4130+h)
        for k in range(4):vein(f'DP04_02_v{h}{k}',(hx,hy),k*math.tau/4+h*.6+r_.uniform(-.3,.3),r_.uniform(.030,.042),.0015,0)
    pos=[]
    while len(pos)<18:   # sporangia 5 mm apart at least (no two stalks side by side)
        a=r_.uniform(0,math.tau);rr=r_.uniform(0,.032);p=(-.005+math.cos(a)*rr,.008+math.sin(a)*rr*.7)
        if all(math.hypot(p[0]-q[0],p[1]-q[1])>.005 for q in pos):pos.append(p)
    for i,(x,y) in enumerate(pos):   # sporangia: hair-thin dark stalk, round head
        z,_=_surf(pad,x,y);h=r_.uniform(.010,.019);lx,ly=r_.uniform(-.002,.002),r_.uniform(-.002,.002)
        tube(f'DP04_02_st{i}',[(x,y,z-.002),(x+lx*.5,y+ly*.5,z+h*.5),(x+lx,y+ly,z+h)],.00045,M['spore'],'Body',sides=3,caps=False)
        _sphere(f'DP04_02_sp{i}',(x+lx,y+ly,z+h+.0012),.0016,1.,M,'spore','Body',4150+i,seg=6,ring=4)
    for i,(x,y) in enumerate(((-.040,-.004),(-.034,-.010),(.042,.014),(.048,.010)),1):   # cream-ochre blobs
        z,_=_surf(pad,x,y);_sphere(f'DP04_02_blob{i}',(x,y,z+.002),.0045,.85,M,'blob','Body',4180+i)
    return {'notes':'slime mould: a mustard vein net, stalked sporangia and cream blobs on moss with wet wood chips'}

def dp04_03(M):
    """苔枝一排小鈴菇 (DP04C-cand-2): a short moss-covered fallen twig with seven tiny pale bell mushrooms in a loose row on top"""
    _rnd.seed(4003);r_=_rnd.Random(4211);Mw=_Mw(M)
    ztop=_logchunk('DP04_03_twig',(0,0,0),.15,.018,M,'Body',4212,sides=12,rings=11,bury=.005)
    for i in range(7):
        x=-.058+.116*i/6+r_.uniform(-.004,.004);y=r_.uniform(-.004,.004);H=(.024,.032,.040,.028,.036,.022,.030)[i];R=(.0050,.0060,.0068,.0055,.0062,.0045,.0058)[i]
        _shroom(f'DP04_03_m{i+1}',(x,y,ztop-.003),(r_.uniform(-.08,.08),r_.uniform(-.06,.06)),H,R,Mw,'Body',4220+i,segs=12,stem_r=.0009,bend=.35,
                thick=.66,umbo=.12,droop=.32,under=.12,gill=.03,wave=.03,arch=1.3,young=.3)
    return {'notes':'a short mossy fallen twig (half sunk 5 mm) with seven tiny pale bell mushrooms on top'}

PROPS.update({'DP04_01':dp04_01,'DP04_02':dp04_02,'DP04_03':dp04_03})
