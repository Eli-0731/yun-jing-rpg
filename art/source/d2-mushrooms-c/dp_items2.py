# DP02 白色小蕈叢 (three kinds) — exec'd by build_dp.py after dp_items.py (uses its _stem/_cap/_shroom/_pad/_chip helpers)

def _white_sources(S):
    """ivory caps / grey-white gills / ivory stems (DP02A, DP02C) and the pale aqua-white set (DP02B, V6 by the log);
    D2 light is overcast and misty, so 'white' stays a soft ivory around .7, never paper white"""
    X_,Y_=X,Y
    K.rng=np.random.default_rng(5201)   # cap: X round the cap, Y centre (0) → rim (1)
    groove=.5+.5*np.sin(math.tau*X_*44+.5*fbm(6,2));gr=np.clip((.35-groove)*3,0,1)*np.clip((Y_-.25)*2.5,0,1)   # radial grooves, from a third of the way out
    blot=fbm(5,3);mid=np.clip(1-Y_*2.6,0,1)**1.5
    def cap(lo,hi,centre):
        t=np.clip(.55+.6*(blot-.5),0,1);col=lerp(lo,hi,t)*(1-.10*gr[...,None])   # grooves mostly in the normal map, only a faint line in colour
        return col*(1-mid[...,None])+np.array(centre)[None,None,:]*mid[...,None]
    S['wcap']=(cap((.66,.62,.54),(.84,.80,.70),(.62,.52,.40)),1.3*groove+.4*blot,1.6,.62,0,0)   # D2 V6: warm cream-ivory, tan centre
    S['acap']=(cap((.55,.70,.68),(.74,.88,.84),(.66,.74,.66)),1.3*groove+.4*blot,1.6,.55,0,0)   # D2 V6 by the log: pale aqua-white
    K.rng=np.random.default_rng(5202)   # gills: fine radial lines, light grey with darker gaps
    ln=.5+.5*np.sin(math.tau*X_*58+.42*fbm(6,2));gap=np.clip((.25-ln)*4,0,1);t=np.clip(.6+.4*(fbm(5,3)-.5),0,1)
    S['wgill']=(lerp((.52,.48,.40),(.72,.67,.57),t)*(1-.40*gap[...,None]),1.6*ln,3.0,.75,0,0)
    S['agill']=(lerp((.45,.62,.60),(.62,.80,.77),t)*(1-.35*gap[...,None]),1.6*ln,3.0,.70,0,0)
    K.rng=np.random.default_rng(5203)   # stems: smooth, faint fibres along the length
    fib=np.clip((fbm(60,2,aniso=40)-.5)*2+.5,0,1);t=np.clip(.55+.4*(fbm(4,3,aniso=6)-.5)+.25*(fib-.5),0,1)
    S['wstem']=(lerp((.62,.58,.50),(.80,.76,.67),t),.8*fib,1.0,.6,0,0)
    S['astem']=(lerp((.54,.68,.66),(.72,.86,.82),t),.8*fib,1.0,.5,0,0)
    K.rng=np.random.default_rng(5204)   # bark of a rotting log (D2 V6 log): grey-brown, deep fissures along the length, mossy-green tint in the cracks
    fis=np.clip((fbm(26,2,aniso=8)-.42)*4.5,0,1);plate=np.clip((fbm(30,2,aniso=4)-.5)*2+.5,0,1);lich=np.clip((fbm(9,3)-.66)*4,0,1)
    t=np.clip(.5+.6*(fbm(4,3)-.5)+.35*(plate-.5),0,1)
    col=lerp((.17,.14,.11),(.36,.31,.25),t)*(1-.62*fis[...,None])+fis[...,None]*np.array([.03,.035,.02])
    col=col*(1-.5*lich[...,None])+lich[...,None]*np.array([.42,.45,.38])*.5   # a few grey-green lichen flecks
    S['bark']=(col,2.2*(1-fis)+.6*plate,4.2,.95,0,0)
SRC_HOOKS.append(_white_sources)

def _Mw(M,k='w'):return dict(M,cap=M[k+'cap'],gill=M[k+'gill'],stem=M[k+'stem'])

def _logchunk(name,c,L,R,M,grp,seed,sides=22,rings=17,bury=.015):
    """a short broken log section lying along X: rough round section (rotten wood), jagged broken ends,
    the upward faces in moss (own part, same vertices on the seam); it sinks `bury` under the ground (no float)"""
    r_=_rnd.Random(seed);c=Vector(c);ph=[r_.uniform(0,6.3) for _ in range(8)];cz=R-bury
    def rad(th,x):return R*(1+.05*math.sin(3*th+ph[0])+.04*math.sin(7*th+ph[1]+x*20)+.03*math.sin(x*35+ph[2])+.03*abs(math.sin(13*th+x*8+ph[4]))-.10*max(0,-math.sin(th))**4)   # the |sin| term: bark ridges along the log
    end=[[r_.uniform(-.003,.003)+.010*math.sin(2*k/sides*math.tau+ph[3+e])+.003*math.sin(5*k/sides*math.tau+ph[5+e]) for k in range(sides)] for e in (0,1)]   # broken, uneven ends (not a saw-cut)
    bm=bmesh.new();V=[]
    for i in range(rings):
        t=i/(rings-1);row=[]
        for k in range(sides):
            th=math.tau*k/sides;x=-L/2+L*t+(end[0][k] if i==0 else end[1][k] if i==rings-1 else 0)
            rr=rad(th,x)*(.93 if i in (0,rings-1) else 1)
            row.append(bm.verts.new(c+Vector((x,math.cos(th)*rr,cz+math.sin(th)*rr))))
        V.append(row)
    for i in range(rings-1):
        for k in range(sides):bm.faces.new((V[i][k],V[i][(k+1)%sides],V[i+1][(k+1)%sides],V[i+1][k]))
    for e,row in ((0,V[0]),(1,V[-1])):   # broken ends: a sunken soft centre (rotten heart)
        cv=bm.verts.new(sum((v.co for v in row),Vector())/sides+Vector((.012 if e==0 else -.012,0,0)))
        for k in range(sides):
            f=(row[k],row[(k+1)%sides],cv) if e==1 else (row[(k+1)%sides],row[k],cv);bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=len(f.verts)==4
    bm2=bm.copy()
    def nz(p):return math.sin(p.x*61+ph[6])*math.sin(p.y*83+p.x*29)+.6*math.sin(p.x*137+p.y*41+ph[7])   # ragged moss edge and cushions
    bmesh.ops.delete(bm2,geom=[f for f in bm2.faces if not(f.normal.z+.22*nz(f.calc_center_median())>.42 and abs(f.calc_center_median().x-c.x)<L*.45)],context='FACES')
    bmesh.ops.delete(bm2,geom=[v for v in bm2.verts if not v.link_faces],context='VERTS')
    bnd={v for e in bm2.edges if e.is_boundary for v in e.verts}
    for v in bm2.verts:   # moss: a thin shell 5 mm over the wood, its edge tucked 4 mm into the wood (never coplanar, never a slit)
        n=v.normal.copy();v.co+=n*((.005+.004*max(0,nz(v.co))) if v not in bnd else -.004)
    for f in bm2.faces:f.smooth=True
    w=finish(name,bm,M['bark'],grp,scale=.12);jitter(w,.002,seed,freq=70)
    finish(name+'_moss',bm2,M['moss'],grp,scale=.15)
    return cz+R

# ---------------- DP02 items (three-views: art/references/DP02/prompt.txt) ----------------
def dp02_01(M):
    """苔上八朵 (DP02A-cand-3): eight slender ivory mushrooms of different heights on a moss cushion, two buttons at the foot.
    Front view: ground line y 820, tallest cap top y 205 (615 px for 14 cm); (foot x, cap x, cap top y, cap width) in px, x about 290"""
    _rnd.seed(2001);Mw=_Mw(M);PX=.14/615
    _pad('DP02_01_pad',(0,0,0),.068,.055,.020,M,'Body',2011,segs=22)
    S=[(290,280,205,230,.000),(185,140,322,165,.010),(360,440,325,150,-.008),(240,232,445,120,-.014),(335,348,395,100,.016),
       (180,105,490,85,-.006),(370,440,512,90,.012)]
    for i,(fx,cx,top,w,dy) in enumerate(S,1):
        H=(820-top)*PX;R=w*PX/2*1.22;base=((fx-290)*PX,dy,.012)
        _shroom(f'DP02_01_m{i}',base,((cx-fx)*PX/H*1.0,dy*.6/H),H,R,Mw,'Body',2020+i,segs=24 if R>.015 else 18,stem_r=max(.0018,R*.12),bend=.45,
                thick=.40,umbo=.05,droop=.24,under=.12,gill=.05,wave=.06,arch=2.0)
    for i,(x,y,h,r) in enumerate(((.008,-.012,.024,.0042),(.016,-.006,.020,.0033)),1):   # two buttons; feet 1.4 cm down in the pad, clear of the closed caps
        _shroom(f'DP02_01_b{i}',(x,y,.005),(.05,-.05),h,r,Mw,'Body',2040+i,segs=12,stem_r=r*.35,bend=.1,thick=.5,umbo=0,droop=.05,under=.1,gill=.02,young=.9)
    return {'notes':'eight slender ivory mushrooms and two buttons on a moss cushion; caps and gills modelled, grooves in the texture'}

def dp02_02(M):
    """高細三朵 (DP02B-cand-1): one tall pale aqua-white mushroom with two shorter ones either side on a little moss mound (V6 by the log; no glow)"""
    _rnd.seed(2002);Ma=_Mw(M,'a')
    _pad('DP02_02_pad',(0,0,0),.05,.038,.022,M,'Body',2111,segs=20)
    for i,(base,lean,H,R,sr,segs) in enumerate((((0,.0,.016),(-.02,.01),.148,.028,.0042,32),
                                                 ((-.03,.006,.012),(-.12,.03),.086,.018,.0028,24),
                                                 ((.03,-.004,.012),(.13,-.02),.080,.017,.0027,24)),1):
        _shroom(f'DP02_02_m{i}',base,lean,H,R*1.3,Ma,'Body',2120+i,segs=segs,stem_r=sr,bend=.25,thick=.52,umbo=.07,droop=.30,under=.13,gill=.05,wave=.04,arch=1.7)
    return {'notes':'three tall pale aqua-white mushrooms on a moss mound; the setting view shows them faintly glowing, the model only takes the colour (no emission)'}

def dp02_03(M):
    """朽木塊上一群 (DP02C-cand-1): a broken chunk of rotten log with moss on top, five small ivory mushrooms on top and one from the end"""
    _rnd.seed(2003);Mw=_Mw(M)
    ztop=_logchunk('DP02_03_log',(0,0,0),.27,.052,M,'Body',2211)
    for i,(x,y,H,R,lean) in enumerate(((-.045,.004,.060,.0145,(-.05,.02)),(-.075,-.010,.042,.011,(-.18,-.05)),(-.015,.012,.036,.009,(.10,.06)),
                                        (.02,-.006,.030,.0075,(.12,-.04)),(.048,.004,.040,.010,(.15,.02))),1):
        _shroom(f'DP02_03_m{i}',(x,y,ztop-.006),lean,H*1.5,R*1.6,Mw,'Body',2220+i,segs=20 if R>.011 else 16,stem_r=max(.0018,R*.14),bend=.3,
                thick=.40,umbo=.05,droop=.24,under=.12,gill=.045,wave=.05,arch=2.0)
    # one from the broken right end: the stem leaves the wood sideways and turns up
    _shroom('DP02_03_m6',(.112,.0,.066),(.75,.05),.052,.015,Mw,'Body',2230,segs=16,stem_r=.0021,bend=.8,bend_dir=(-.4,0,1),thick=.40,umbo=.05,droop=.24,under=.12,gill=.045,arch=2.0)
    return {'notes':'a broken chunk of rotten log (half buried) with moss on top, six small ivory mushrooms'}

PROPS.update({'DP02_01':dp02_01,'DP02_02':dp02_02,'DP02_03':dp02_03})
