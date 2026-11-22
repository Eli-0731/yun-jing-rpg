# DP03 層狀菌 (three kinds: thin shelf brackets, hoof polypores, lingzhi) — exec'd by build_dp.py after dp_items2.py.
# These hang on a trunk, a log or a stump: each sits on a slab of bark / rotten wood whose BACK face is the flat plane y = 0
# (the origin is the centre of that plane), so it can be set flush on any trunk; the brackets stick out to −Y (the front).

def _bracket_sources(S):
    """bracket tops: concentric growth bands along V (the 'Tiled' v runs from the bark (0) to the rim (1)), a pale growing rim;
    pore undersides: pale beige with fine pores. D2: low saturation, the lingzhi red kept dark and muted."""
    K.rng=np.random.default_rng(5301)
    wob=fbm(5,3);fine=fbm(80,2,aniso=6)
    def bands(freq):return .5+.5*np.sin(math.tau*(Y*freq+.35*wob+.04*fbm(12,2)))
    def top(cols,freq,rimc,rim_w,gloss):
        b=bands(freq);b2=bands(freq*2.3);t=np.clip(.5*b+.3*b2+.2*fine,0,1)
        n=len(cols);idx=np.clip(t*(n-1),0,n-1.001);i0=idx.astype(int);f=(idx-i0)[...,None];C=np.array(cols)
        col=C[i0]*(1-f)+C[i0+1]*f
        rim=np.clip((Y-(1-rim_w)+.03*(wob-.5))/max(rim_w*.5,.01),0,1)[...,None]
        col=col*(1-rim)+np.array(rimc)[None,None,:]*rim
        return col,1.1*b+.5*b2+.4*fine,2.6,gloss
    c,h,s,r=top([(.20,.14,.10),(.36,.25,.16),(.47,.35,.23),(.31,.27,.23),(.52,.40,.27)],9,(.70,.62,.48),.10,.85)   # thin shelves: umber, tawny, grey-brown bands
    S['shelf']=(c,h,s,r,0,0)
    c,h,s,r=top([(.15,.12,.09),(.27,.19,.13),(.38,.23,.14),(.23,.19,.15),(.42,.28,.17)],6,(.50,.38,.24),.07,.9)   # hoof: dark grey-brown, dull rust, ochre edge
    S['hoof']=(c,h,s,r,0,0)
    c,h,s,r=top([(.20,.08,.06),(.30,.12,.08),(.36,.16,.10),(.26,.11,.07),(.40,.20,.12)],5,(.62,.50,.34),.12,.42)   # lingzhi: muted deep red-brown, lacquer (lower roughness)
    S['lingzhi']=(c,h,s,r,0,0)
    K.rng=np.random.default_rng(5302)
    pore=np.clip((fbm(160,1)-.55)*4,0,1);t=np.clip(.55+.5*(fbm(6,3)-.5),0,1)
    S['pore']=(lerp((.50,.44,.34),(.70,.64,.52),t)*(1-.25*pore[...,None]),1.2*pore,1.6,.9,0,0)
    K.rng=np.random.default_rng(5303)
    fib=np.clip((fbm(50,2,aniso=30)-.5)*2+.5,0,1);t=np.clip(.5+.5*(fbm(4,3,aniso=5)-.5)+.3*(fib-.5),0,1)
    S['lstalk']=(lerp((.18,.08,.05),(.34,.16,.10),t),1.0*fib,1.4,.45,0,0)
    K.rng=np.random.default_rng(5304)   # trunk bark for the slabs (DP03 three-views): lighter grey-brown plates, deep vertical fissures, moss and lichen patches
    fis=np.clip((fbm(22,2,aniso=7)-.40)*4.5,0,1);plate=np.clip((fbm(34,2,aniso=3)-.5)*2+.5,0,1)
    mos=np.clip((fbm(6,3)-.58)*4,0,1)*np.clip((fbm(40,2)-.35)*3,0,1);lich=np.clip((fbm(11,3)-.70)*5,0,1)
    t=np.clip(.5+.6*(fbm(4,3)-.5)+.4*(plate-.5),0,1)
    col=lerp((.27,.22,.17),(.52,.44,.34),t)*(1-.55*fis[...,None])+fis[...,None]*np.array([.03,.03,.02])
    col=col*(1-mos[...,None])+mos[...,None]*np.array([.15,.17,.07])
    col=col*(1-.6*lich[...,None])+lich[...,None]*np.array([.46,.50,.42])*.6
    S['bark2']=(col,2.4*(1-fis)+.8*plate+.6*mos,4.4,.95,0,0)
SRC_HOOKS.append(_bracket_sources)

def _slab(name,W,H,T,M,mat,grp,seed,nx=14,nz=16,ridge=.006,round_=False):
    """bark / rotten-wood slab: back face flat on y = 0 (sits flush on a trunk), front at y ≈ −T with vertical bark ridges,
    an irregular outline (broken edge). round_: a rounder outline (the lingzhi's piece of stump)."""
    r_=_rnd.Random(seed);ph=[r_.uniform(0,6.3) for _ in range(8)]
    def P(u,v,front):
        if round_:
            a=math.atan2(v,u);rr=1+.06*math.sin(3*a+ph[0])+.04*math.sin(7*a+ph[1])
            m=max(abs(u),abs(v));q=math.hypot(u,v) or 1;u_,v_=u/q*m,v/q*m   # square grid → disc
            x=u_*W/2*rr;z=v_*H/2*rr
        else:
            x=u*W/2*(1+.04*math.sin(3*v+ph[0])+.015*math.sin(9*v+ph[1]));z=v*H/2*(1+.035*math.sin(3*u+ph[2])+.015*math.sin(8*u+ph[3]))
        if not front:return Vector((x,0,z))
        e=min(1-abs(u),1-abs(v));fall=min(1,e*4)   # thinner toward the broken edge
        y=-T*(.35+.65*fall)-ridge*fall*(abs(math.sin(x*95+math.sin(z*23+ph[4])*1.5))+.5*math.sin(z*60+x*30+ph[5]))
        return Vector((x,y,z))
    bm=bmesh.new()
    F=[[bm.verts.new(P(-1+2*i/nx,-1+2*j/nz,True)) for i in range(nx+1)] for j in range(nz+1)]
    B=[[bm.verts.new(P(-1+2*i/nx,-1+2*j/nz,False)) for i in range(nx+1)] for j in range(nz+1)]
    for j in range(nz):
        for i in range(nx):
            bm.faces.new((F[j][i],F[j][i+1],F[j+1][i+1],F[j+1][i]));bm.faces.new((B[j][i],B[j+1][i],B[j+1][i+1],B[j][i+1]))
    ring=[(0,i) for i in range(nx)]+[(j,nx) for j in range(nz)]+[(nz,i) for i in range(nx,0,-1)]+[(j,0) for j in range(nz,0,-1)]
    for k in range(len(ring)):
        (a,b),(c_,d)=ring[k],ring[(k+1)%len(ring)];bm.faces.new((F[a][b],B[a][b],B[c_][d],F[c_][d]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=abs(f.normal.y)>.3 and f.normal.y<0
    lay=bm.loops.layers.uv.new('Tiled');du=r_.random()   # straight-on projection: the bark fissures always run up the trunk (V = z)
    for f in bm.faces:
        for l in f.loops:l[lay].uv=(l.vert.co.x/.11+du,l.vert.co.z/.11)
    return finish(name,bm,M[mat],grp,keep_uv=True)

def _shelf(name,cx,cz,y0,Rx,D,T,M,top,grp,seed,a=.55,th=(0.,math.pi),segs=20,droop=.3,rim=.006,wave=.05,tilt=0.):
    """one bracket: grows from a short line on the bark (half-width a·Rx at y = y0, inside the slab) out to −Y in a fan
    between the angles th; top (material `top`, v = 0 at the bark … 1 at the rim) over a rounded growing rim to a flatter
    pore underside ('pore'). T: thickness at the bark; droop: how far the rim sags (× T); tilt lifts the outer edge."""
    r_=_rnd.Random(seed);ph=[r_.uniform(0,6.3) for _ in range(6)]
    def w(t):return 1+wave*math.sin(5*t+ph[0])+wave*.6*math.sin(9*t+ph[1])
    def xy(t,r):
        ww=w(t) if r>.5 else 1+(w(t)-1)*r*2
        st=math.sin(t);st=max(st,.12) if a>.3 else (st if st>=0 else .6*st)   # brackets fan out from the bark; a lingzhi cap wraps a little behind its stalk
        return cx+Rx*math.cos(t)*(a+(1-a)*r)*ww,y0-D*r*st*ww
    def zt(t,r):return cz+T*(1-r**1.4)-T*droop*r**2+tilt*r+.004*math.sin(7*t+ph[2])*r**3
    def zb(t,r):return cz-T*.30*(1-r)**1.3-T*droop*r**2+tilt*r-rim+.004*math.sin(7*t+ph[2])*r**3
    th0,th1=th;n=segs
    ts=[th0+(th1-th0)*k/n for k in range(n+1)]
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');rows=[];vs=(0,.3,.55,.78,.92,1.0)
    for r in vs:rows.append([bm.verts.new(Vector((*xy(t,r),zt(t,r)))) for t in ts])
    # rounded rim: out a little past r = 1, half-way down, then the underside rim
    rows.append([bm.verts.new(Vector((*xy(t,1.035),(zt(t,1)+zb(t,1))/2))) for t in ts]);vs=vs+(1.0,)
    rows.append([bm.verts.new(Vector((*xy(t,1.0),zb(t,1)))) for t in ts]);vs=vs+(.96,)
    span=Rx*(th1-th0)
    for i in range(len(rows)-1):
        for k in range(n):
            fc=bm.faces.new((rows[i][k],rows[i][k+1],rows[i+1][k+1],rows[i+1][k]))
            for l,(kk,ii) in zip(fc.loops,((k,i),(k+1,i),(k+1,i+1),(k,i+1))):l[lay].uv=(kk/n*span/.12,min(vs[ii],1.0))
    for fc in bm.faces:fc.smooth=True
    finish(name+'_top',bm,M[top],grp,keep_uv=True)
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');rows=[]
    for r in (1.0,.7,.4,0.):rows.append([bm.verts.new(Vector((*xy(t,r),zb(t,r)))) for t in ts])
    for i in range(3):
        for k in range(n):
            fc=bm.faces.new((rows[i][k+1],rows[i][k],rows[i+1][k],rows[i+1][k+1]))
            for l,(u_,v_) in zip(fc.loops,((k+1,i),(k,i),(k,i+1),(k+1,i+1))):l[lay].uv=(u_/n*span/.08,v_/3)
    for fc in bm.faces:fc.smooth=True
    finish(name+'_pores',bm,M['pore'],grp,keep_uv=True)

# ---------------- DP03 items (three-views: art/references/DP03/prompt.txt) ----------------
def dp03_01(M):
    """薄層架 (DP03A-cand-3): six thin shelves in staggered tiers on a slab of bark; front view 715 px for the 0.30 m slab"""
    _rnd.seed(3001);PX=.30/715;T=.017
    _slab('DP03_01_bark',.245,.30,T,M,'bark2','Body',3011)
    S=[(245,255,138,.075),(395,340,190,.085),(260,435,215,.10),(232,550,158,.075),(410,590,193,.09),(290,728,130,.07)]
    for i,(x,y,hw,D) in enumerate(S,1):
        _shelf(f'DP03_01_s{i}',(x-320)*PX,(492-y)*PX,-T+.008,hw*PX,D,.014,M,'shelf','Body',3020+i,a=.5,segs=22,droop=.7,rim=.003,wave=.06,tilt=-.004)
    return {'notes':'six thin bracket shelves on a slab of bark; the back of the slab is flat (y = 0) to sit on a trunk','wall':True,'origin_text':'bottom centre of the flat back of the slab (y = 0, the plane that sits on the trunk / log / stump), z up; the brackets stick out to -Y (Blender) / -Z (FBX, Unity)'}

def dp03_02(M):
    """厚蹄形三個 (DP03B-cand-3): three thick hoof polypores stacked small → large downward on a slab of bark"""
    _rnd.seed(3002);T=.018
    _slab('DP03_02_bark',.24,.30,T,M,'bark2','Body',3111)
    for i,(x,z,Rx,D,Th) in enumerate(((.0,.090,.064,.068,.030),(-.005,.025,.082,.088,.036),(.0,-.062,.104,.112,.044)),1):   # a clear gap under each hoof
        _shelf(f'DP03_02_h{i}',x,z,-T+.010,Rx,D,Th,M,'hoof','Body',3120+i,a=.62,segs=22,droop=.35,rim=.008,wave=.025,tilt=0.)
    return {'notes':'three hoof polypores on a slab of bark; flat back (y = 0)','wall':True,'origin_text':'bottom centre of the flat back of the slab (y = 0, the plane that sits on the trunk / log / stump), z up; the brackets stick out to -Y (Blender) / -Z (FBX, Unity)'}

def dp03_03(M):
    """靈芝三朵 (DP03C-cand-3): three kidney-shaped lingzhi caps on short curved side stalks from a round piece of rotten stump wood;
    the caps are muted (the three-view red is more saturated than D2)"""
    _rnd.seed(3003);T=.016;Ml=dict(M,stem=M['lstalk'])
    _slab('DP03_03_wood',.22,.22,T,M,'bark2','Body',3211,round_=True)
    for i,(bx,bz,cx,cy,cz,Rx,D) in enumerate(((-.030,.010,-.035,-.075,.060,.056,.048),(.030,-.035,.050,-.065,.000,.045,.040),(-.030,-.060,-.045,-.055,-.050,.032,.028)),1):   # caps held out on visible curved stalks
        top=Vector((cx,cy+D*.15,cz-.006))
        _stem(f'DP03_03_l{i}_stalk',(bx,-T+.006,bz),top,.0085 if i<3 else .006,.0075 if i<3 else .0055,Ml,'Body',sides=10,bulb=1.0,bend=Vector((0,-.004,-.016)),rings=7)
        _shelf(f'DP03_03_l{i}',cx,cz,cy+D*.15,Rx,D,.020,M,'lingzhi','Body',3220+i,a=.12,th=(-.25*math.pi,1.25*math.pi),segs=28,droop=.35,rim=.006,wave=.03,tilt=.004)
    return {'notes':'three lingzhi caps on side stalks from a round piece of rotten stump wood; flat back (y = 0)','wall':True,'origin_text':'bottom centre of the flat back of the slab (y = 0, the plane that sits on the trunk / log / stump), z up; the brackets stick out to -Y (Blender) / -Z (FBX, Unity)'}

PROPS.update({'DP03_01':dp03_01,'DP03_02':dp03_02,'DP03_03':dp03_03})
