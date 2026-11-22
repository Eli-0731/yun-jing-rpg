# DP07 苔被片 (six thin moss sheets) and DP13 地衣片 (four lichen patches) — exec'd by build_moss.py after moss_items.py.
# Both are thin shells that lie ON a host surface (a boulder top, a flat slab, a root, a stone side, a block edge, bark).
# The host is not part of the model: each sheet is built over an analytic host surface P(u, v) with normal N(u, v),
# its edge lands on the host and a narrow skirt runs 6 mm into it, so on any host of about that shape nothing floats.
# Origin: the host surface point under the sheet's centre, z along that surface's normal (for the flat ones: z = 0 on the ground).

def _lichen_sources(S):
    K.rng=np.random.default_rng(6301)   # crustose: pale grey-white areoles (small scales) with darker cracks and rings
    cell=np.clip((fbm(70,1)-.45)*3,0,1);crack=np.clip((.42-fbm(90,1))*6,0,1);ring=.5+.5*np.sin(math.tau*fbm(6,2)*7)
    t=np.clip(.55+.5*(fbm(5,3)-.5)+.25*(ring-.5),0,1)
    S['crust']=(lerp((.38,.42,.37),(.58,.62,.55),t)*(1-.45*crack[...,None]),1.0*cell-.8*crack,2.4,.92,0,0)
    K.rng=np.random.default_rng(6302)   # foliose: soft grey-green lobes, paler rims, darker brown-grey centres
    lob=np.clip((fbm(30,2)-.4)*2.5,0,1);t=np.clip(.5+.6*(fbm(6,3)-.5),0,1)
    S['foliose']=(lerp((.40,.46,.40),(.62,.68,.58),t)*(.85+.15*lob[...,None]),1.2*lob+.5*fbm(60,2),2.0,.85,0,0)
    K.rng=np.random.default_rng(6303)   # cup lichen: pale sage scales and cups
    sc=np.clip((fbm(80,1)-.45)*3,0,1);t=np.clip(.5+.6*(fbm(5,3)-.5),0,1)
    S['cup']=(lerp((.46,.52,.42),(.66,.72,.58),t)*(.85+.15*sc[...,None]),1.0*sc,1.6,.85,0,0)
    K.rng=np.random.default_rng(6304)   # host bark under the D strip edge (only the skirt): dark grey-brown
    S['hostbark']=(lerp((.10,.08,.06),(.22,.18,.14),np.clip(.5+.6*(fbm(8,3,aniso=6)-.5),0,1)),.8*fbm(30,2,aniso=6),2.,.95,0,0)
SRC_HOOKS.append(_lichen_sources)

def _sheet(name,host,U,V,M,mat,grp,seed,thick=.02,noise=.18,rag=.03,n=1400,cushions=30,cush_r=(.03,.07),cush_h=.6,
           prof=(2.,.45),drip=0.,drip_n=9,skirt='soil',sink=.006,uvs=.5,lift=None,nmin=160):
    """a thin sheet over host(u, v) → (P, N) inside an irregular outline of half-size U × V (m):
    jittered hex points + rim ring, Delaunay; height along N = thick·profile + cushions; the rim on the host, a skirt sinks into it.
    rag: small-scale raggedness of the edge (fringe without strands); drip: long ragged tongues hanging to −v (stone sides)."""
    r_=_rnd.Random(seed);ph=[r_.uniform(0,6.3) for _ in range(10)]
    def rr(t):
        base=1+noise*(.5*math.sin(2*t+ph[0])+.3*math.sin(3*t+ph[1])+.2*math.sin(5*t+ph[2]))+rag*(.6*math.sin(17*t+ph[3])+.5*math.sin(29*t+ph[4])+.4*math.sin(47*t+ph[5])+.3*math.sin(71*t+ph[7]))   # fine fringe, no saw teeth
        if drip:   # tongues on the lower side (sin t < 0)
            s=max(0.,-math.sin(t));base+=drip*s**1.5*(.6*max(0.,math.sin(drip_n*t+ph[6]))**3+.4*max(0.,math.sin(int(drip_n*1.7)*t+ph[8]))**4)   # blunt tongues of different lengths (sharp ones read as thorns)   # many narrow tongues of different lengths
        return base
    nth=max(nmin,int(2*math.pi*math.sqrt((U*U+V*V)/2)/(math.sqrt(4*U*V*math.pi/n/1.3)*.6)))   # a dense rim: the fringe harmonics need ~3 points per wiggle
    th=[math.tau*k/nth for k in range(nth)]
    rim=[(math.cos(t)*U*rr(t),math.sin(t)*V*rr(t)) for t in th]
    area=math.pi*U*V*1.1;sp=math.sqrt(area/(n*math.sqrt(3)/2));pts=list(rim);F=[1.]*nth
    j=0;yy=-V*2.5
    while yy<V*2.5:
        xx=-U*2.5+(sp/2 if j%2 else 0.)
        while xx<U*2.5:
            x=xx+r_.uniform(-.22,.22)*sp;y=yy+r_.uniform(-.22,.22)*sp;t=math.atan2(y/V,x/U);f=math.hypot(x/U,y/V)/rr(t)
            R=math.hypot(U*math.cos(t),V*math.sin(t))*rr(t)
            if f<1 and (1-f)*R>.55*sp:pts.append((x,y));F.append(f)
            xx+=sp
        yy+=sp*math.sqrt(3)/2;j+=1
    P=np.array(pts);F=np.array(F)
    h=thick*(1-np.clip(F,0,1)**prof[0])**prof[1]
    if cushions:
        def inside(rg):
            t=rg.uniform(0,math.tau);f=math.sqrt(rg.random())*.9;return (math.cos(t)*U*rr(t)*f,math.sin(t)*V*rr(t)*f)
        cen=_poisson(r_,cushions,inside,cush_r[0]*1.2);rad=[r_.uniform(*cush_r) for _ in cen];amp=[r_.uniform(.5,1.)*cush_h*thick for _ in cen]
        h=h+_field(P,cen,amp,rad,.8)*np.clip((1-F)*4,0,1)
    if lift is not None:h=h+lift(P,F)
    h[F>=.999]=0.
    from mathutils.geometry import delaunay_2d_cdt
    cv,_,cf,_,_,_=delaunay_2d_cdt([Vector(p) for p in pts],[],[list(range(nth))],2,1e-7)
    assert len(cv)==len(pts),'the triangulation added or merged points'
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');du,dv=r_.random(),r_.random();Vs=[]
    for (u,v),hh in zip(pts,h):
        p,nn=host(u,v);Vs.append(bm.verts.new(p+nn*hh))
    for f in cf:
        fc=bm.faces.new([Vs[i] for i in f])
        for l,i in zip(fc.loops,f):l[lay].uv=(pts[i][0]/uvs+du,pts[i][1]/uvs+dv)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    vi={v:i for i,v in enumerate(Vs)}
    for fc in bm.faces:   # every face looks away from the host
        fc.smooth=True;uc=np.mean([pts[vi[v]] for v in fc.verts],0)
        if fc.normal.dot(host(float(uc[0]),float(uc[1]))[1])<0:fc.normal_flip()
    o=finish(name,bm,M[mat],grp,keep_uv=True)
    bm=bmesh.new()   # skirt: from the rim into the host
    a=[bm.verts.new(host(*rim[k])[0]) for k in range(nth)];b=[]
    for k in range(nth):
        p,nn=host(rim[k][0]*.96,rim[k][1]*.96);b.append(bm.verts.new(p-nn*sink))
    for k in range(nth):
        k1=(k+1)%nth;bm.faces.new((a[k1],a[k],b[k],b[k1]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    finish(name+'_skirt',bm,M[skirt],grp,scale=.2)
    return o

# ---------------- hosts (u, v in metres along the surface; P, N) ----------------
def H_flat():return lambda u,v:(Vector((u,v,0.)),Vector((0,0,1.)))
def H_dome(Rs):   # boulder top: a sphere of radius Rs, its top at the origin
    def f(u,v):
        d=Vector((u,v,0.));L=d.length
        if L<1e-9:return Vector((0,0,0.)),Vector((0,0,1.))
        a=L/Rs;n=Vector((math.sin(a)*u/L,math.sin(a)*v/L,math.cos(a)));return n*Rs-Vector((0,0,Rs)),n
    return f
def H_cyl(Rc):   # root lying along X, top at the origin; v is the arc length across the root
    return lambda u,v:(Vector((u,Rc*math.sin(v/Rc),Rc*math.cos(v/Rc)-Rc)),Vector((0,math.sin(v/Rc),math.cos(v/Rc))))
def H_wall():   # vertical stone side: the host plane y = 0, the sheet on its −Y side; v up
    return lambda u,v:(Vector((u,0.,v)),Vector((0,-1.,0)))
def H_edge(re=.025):   # block edge along X, rounded by re: top face z = 0 behind (y > 0), front face y = 0 below (z < 0); v across the edge, + toward the top
    L=math.pi/2*re
    def f(u,v):
        if v>=L/2:return Vector((u,re+v-L/2,0.)),Vector((0,0,1.))
        if v<=-L/2:return Vector((u,0.,-re-(-v-L/2))),Vector((0,-1.,0))
        a=(v+L/2)/L*math.pi/2;n=Vector((0,-math.cos(a),math.sin(a)));return Vector((u,re,-re))+n*re,n
    return f
def H_trunk(Rt):   # vertical trunk of radius Rt, axis behind the origin (y = +Rt); u is the arc length round it, v up
    return lambda u,v:(Vector((Rt*math.sin(u/Rt),Rt-Rt*math.cos(u/Rt),v)),Vector((math.sin(u/Rt),-math.cos(u/Rt),0)))

def _cups(name,host,pts,M,grp,seed):   # cup lichen: small trumpet cups standing on the mat
    r_=_rnd.Random(seed)
    for i,(u,v) in enumerate(pts):
        p,n=host(u,v);h=r_.uniform(.008,.018);rb=r_.uniform(.0012,.002);rt=r_.uniform(.003,.0055)
        ax=(n+Vector((r_.uniform(-.2,.2),r_.uniform(-.2,.2),0))).normalized();uax=ax.orthogonal().normalized();vax=ax.cross(uax);s=8
        bm=bmesh.new();rings=[]
        for t,(z,r) in enumerate(((-.002,rb),(h*.55,rb*1.05),(h*.85,rt*.6),(h,rt),(h*.9,rt*.8))):
            rings.append([bm.verts.new(p+ax*z+(uax*math.cos(math.tau*k/s)+vax*math.sin(math.tau*k/s))*r) for k in range(s)])
        for a_,b_ in zip(rings,rings[1:]):
            for k in range(s):bm.faces.new((a_[k],a_[(k+1)%s],b_[(k+1)%s],b_[k]))
        cc=bm.verts.new(p+ax*h*.72)
        for k in range(s):bm.faces.new((rings[-1][k],rings[-1][(k+1)%s],cc))
        for f in bm.faces:f.smooth=True
        finish(f'{name}{i}',bm,M['cup'],grp,scale=.05)

# ---------------- DP07 items (three-views: art/references/DP07/prompt.txt) ----------------
O_HOST='the host surface point under the sheet centre, z along that surface normal (the host is not in the model: {h})'
def dp07_01(M):
    """石頂苔帽 (DP07A-cand-1): a thin cap of moss over the top of a round boulder (radius 0.55 m), its fringed edge hanging a little down the sides"""
    _sheet('DP07_01',H_dome(.55),.47,.42,M,'moss','Body',7101,thick=.030,noise=.16,rag=.03,n=1500,cushions=40,cush_r=(.03,.07),cush_h=.7,skirt='moss_old')
    return {'lift_to_ground':True,'paint':_moss_paint,'grime':.6,'wear':0,'origin_text':O_HOST.format(h='a boulder top of radius about 0.55 m')}
def dp07_02(M):
    """平石苔片 (DP07B-cand-1): a flat patch of moss with a few low cushions, for a flat slab"""
    _sheet('DP07_02',H_flat(),.30,.22,M,'moss','Body',7201,thick=.020,noise=.20,rag=.03,n=1300,cushions=26,cush_r=(.025,.06),cush_h=.9,skirt='moss_old')
    return {'paint':_moss_paint,'grime':.6,'wear':0,'origin_text':O_HOST.format(h='a flat slab; z = 0 on its face')}
def dp07_03(M):
    """根頂苔條 (DP07C-cand-1): a 1 m strip of moss along the round top of a root (radius 0.12 m), hanging down its sides"""
    _sheet('DP07_03',H_cyl(.12),.50,.13,M,'moss','Body',7301,thick=.022,noise=.12,rag=.035,n=1500,cushions=30,cush_r=(.025,.05),cush_h=.7,skirt='moss_old')
    return {'lift_to_ground':True,'paint':_moss_paint,'grime':.6,'wear':0,'origin_text':O_HOST.format(h='a root of radius about 0.12 m lying along X')}
def dp07_04(M):
    """石側垂苔 (DP07D-cand-2): a thin sheet clinging to the vertical side of a stone, its lower edge in ragged dripping tongues"""
    _sheet('DP07_04',H_wall(),.29,.24,M,'moss','Body',7401,thick=.016,noise=.14,rag=.035,n=1300,cushions=18,cush_r=(.02,.05),cush_h=.6,drip=.38,drip_n=17,skirt='moss_old')
    return {'lift_to_ground':True,'paint':_moss_paint,'grime':.6,'wear':0,'origin_text':O_HOST.format(h='a vertical stone face, the plane y = 0; the moss on its -Y side')}
def dp07_05(M):
    """小苔斑 (DP07E-cand-1): a small irregular patch on a gently curved stone (radius 1 m)"""
    _sheet('DP07_05',H_dome(1.0),.16,.12,M,'moss','Body',7501,thick=.016,noise=.26,rag=.035,n=800,cushions=12,cush_r=(.015,.035),cush_h=.8,skirt='moss_old')
    return {'lift_to_ground':True,'paint':_moss_paint,'grime':.6,'wear':0,'origin_text':O_HOST.format(h='a gently curved stone of radius about 1 m')}
def dp07_06(M):
    """包角苔 (DP07F-cand-2): a sheet over the edge of a squared block, half on the top, half hanging down the front in tongues"""
    _sheet('DP07_06',H_edge(.025),.25,.20,M,'moss','Body',7601,thick=.018,noise=.12,rag=.035,n=1300,cushions=20,cush_r=(.02,.05),cush_h=.6,drip=.36,drip_n=15,skirt='moss_old')
    return {'lift_to_ground':True,'paint':_moss_paint,'grime':.6,'wear':0,'origin_text':O_HOST.format(h='the edge of a squared block along X: top face z = 0 behind, front face y = 0 below')}

# ---------------- DP13 items (three-views: art/references/DP13/prompt.txt) ----------------
def dp13_01(M):
    """殼狀地衣 (DP13A-cand-1): a round crust of grey-white lichen, flat on stone (2–4 mm)"""
    _sheet('DP13_01',H_dome(.8),.13,.12,M,'crust','Body',13101,thick=.003,noise=.10,rag=.03,n=700,cushions=0,skirt='crust',sink=.004,uvs=.25)
    return {'lift_to_ground':True,'grime':.3,'wear':0,'origin_text':O_HOST.format(h='a stone of radius about 0.8 m (works on flat stone too)')}
def dp13_02(M):
    """葉狀地衣 (DP13B-cand-3): five grey-green leafy rosettes, lobed, their rims lifted and curled a little"""
    r_=_rnd.Random(13201);cen=[(0,0),(.06,.05),(-.06,.04),(.05,-.06),(-.05,-.05)]
    for i,(cx,cy) in enumerate(cen):
        rad=.055 if i==0 else r_.uniform(.035,.045)
        def host(u,v,cx=cx,cy=cy):p,n=H_dome(.8)(u+cx,v+cy);return p,n
        def lift(P,F,rad=rad):a=np.arctan2(P[:,1],P[:,0]);return .004*np.clip(F-.55,0,1)/.45*(.6+.4*np.sin(a*7))   # curled lobe rims
        _sheet(f'DP13_02_r{i}',host,rad,rad*.92,M,'foliose','Body',13210+i,thick=.004,noise=.08,rag=.12,n=220,cushions=0,skirt='foliose',sink=.004,uvs=.2,lift=lift,nmin=96)
    return {'lift_to_ground':True,'grime':.4,'wear':0,'origin_text':O_HOST.format(h='a stone of radius about 0.8 m')}
def dp13_03(M):
    """杯狀地衣 (DP13C-cand-2): a mat of pale sage scales with small trumpet cups 1–2 cm tall"""
    host=H_dome(.6)
    _sheet('DP13_03',host,.08,.07,M,'cup','Body',13301,thick=.006,noise=.18,rag=.08,n=500,cushions=14,cush_r=(.01,.02),cush_h=.8,skirt='moss_old',sink=.004,uvs=.2)
    r_=_rnd.Random(13302);pts=_poisson(r_,26,lambda rg:(rg.uniform(-.06,.06),rg.uniform(-.05,.05)),.011)
    pts=[p for p in pts if (p[0]/.07)**2+(p[1]/.06)**2<1]
    _cups('DP13_03_c',host,pts,M,'Body',13303)
    return {'lift_to_ground':True,'grime':.4,'wear':0,'origin_text':O_HOST.format(h='a mossy stone of radius about 0.6 m')}
def dp13_04(M):
    """樹皮上的地衣條 (DP13D-cand-1): a narrow strip of grey-green crusty lichen with a few leafy lobes, on a trunk of radius 0.3 m, running up it"""
    _sheet('DP13_04',H_trunk(.3),.055,.20,M,'crust','Body',13401,thick=.003,noise=.20,rag=.10,n=700,cushions=10,cush_r=(.008,.018),cush_h=1.0,skirt='hostbark',sink=.004,uvs=.25)
    return {'lift_to_ground':True,'grime':.3,'wear':0,'origin_text':O_HOST.format(h='a vertical trunk of radius about 0.3 m, its axis at y = +0.3 m')}

PROPS.update({'DP07_01':dp07_01,'DP07_02':dp07_02,'DP07_03':dp07_03,'DP07_04':dp07_04,'DP07_05':dp07_05,'DP07_06':dp07_06,
              'DP13_01':dp13_01,'DP13_02':dp13_02,'DP13_03':dp13_03,'DP13_04':dp13_04})
