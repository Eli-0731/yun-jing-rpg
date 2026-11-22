# DP14 細枯枝 (eight), DP15 中斷枝 (six), DP22 泡在水窪裡的落葉與枝 (one) — exec'd by build_floor.py after floor_items2.py.
# Bark: Poly Haven bark_brown_02 (CC0, 2k; standard §5), not in the repo: the folder in DR_TEX (default D:/yun-jing-cache/polyhaven-bark/),
# the same scan as d2-roots-b / d2-logs-b. Its luminance and height drive a D2 grey-brown painted bark (low contrast, lichen flecks).
import os as _os
_BARK=_os.environ.get('DR_TEX','D:/yun-jing-cache/polyhaven-bark/')

def _bark_sources(S):
    def load(fn):
        p=_BARK+fn
        assert _os.path.exists(p),f'{p}: Poly Haven bark_brown_02 (CC0, 2k) is not in the repo; put it there (standard §5) or set DR_TEX'
        im=bpy.data.images.load(p,check_existing=False);im.scale(K.R,K.R)
        a=np.empty(K.R*K.R*4,np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im);return a.reshape(K.R,K.R,4)
    d=load('bark_brown_02_diff_2k.png');h=load('bark_brown_02_disp_2k.png')[...,0]
    lum=d[...,0]*.3+d[...,1]*.5+d[...,2]*.2;ln=(lum-lum.mean())/(lum.std()+1e-6);hd=(h-h.mean())/(h.std()+1e-6)
    K.rng=np.random.default_rng(1401)
    t=np.clip(.5+.16*ln+.12*hd+.22*(fbm(3,3)-.5),0,1)
    col=lerp((.14,.12,.10),(.47,.41,.35),t)*(1+.10*(fbm(2,2)-.5)[...,None]*np.array([1.,.4,-.6]))   # D2 grey-brown, a little warmer in places
    lic=np.clip((fbm(26,3)-.70)*5,0,1)*np.clip(hd+.5,0,1)   # pale grey-green lichen flecks on the bark plates
    col=col*(1-.55*lic[...,None])+lic[...,None]*np.array([.40,.43,.36])*.55
    S['bark']=(col,.45*hd+.15*ln,2.0,.9,0,0)
    S['bark_root']=(col*np.array([.80,.70,.58]),.45*hd+.15*ln,2.0,.88,0,0)   # roots: darker and browner
    S['bark_wet']=(col*np.array([.50,.47,.44]),.45*hd,1.6,.55,0,0)
    K.rng=np.random.default_rng(1402)   # broken wood: pale, fibres along V, dark gaps between the splinters
    vf=np.clip((fbm(40,2,aniso=30)-.5)*2+.5,0,1);gap=np.clip((.3-vf)*4,0,1)
    S['woodpale']=(lerp((.36,.29,.20),(.62,.52,.38),np.clip(.5+.5*(fbm(4,3,aniso=8)-.5)+.4*(vf-.5),0,1))*(1-.45*gap[...,None]),1.4*vf,2.4,.85,0,0)
    S['barkin']=(lerp((.38,.28,.18),(.58,.45,.30),np.clip(.5+.5*(fbm(5,3,aniso=10)-.5)+.25*(vf-.5),0,1)),.6*vf,1.2,.75,0,0)   # inner bark: pale tan
SRC_HOOKS.append(_bark_sources)

def _centre():
    """footprint centre on (0, 0): the parts are built from one end"""
    P=np.array([v.co[:] for o in parts for v in o.data.vertices]);c=(P.min(0)+P.max(0))/2
    for o in parts:o.data.transform(Matrix.Translation((-c[0],-c[1],0)))

def _shell(name,bm,faces,M,grp,seed,th=.004,mat='moss',relax=6):
    """a thin moss shell over the given faces of bm (outward normals): its outline relaxed along itself, the edge tucked in"""
    off=Vector((seed%37,seed%53,seed%71))*.37;bm.verts.index_update();bm2=bmesh.new();vm={}
    for f in faces:
        vs=[]
        for v in f.verts:
            if v.index not in vm:vm[v.index]=bm2.verts.new(v.co.copy())
            vs.append(vm[v.index])
        try:bm2.faces.new(vs)
        except ValueError:pass
    if not bm2.faces:bm2.free();return None
    bm2.normal_update();bnd={v for e in bm2.edges if e.is_boundary for v in e.verts}
    for _ in range(relax):
        new={}
        for v in bnd:
            nb=[e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb)==2:new[v]=v.co*.4+(nb[0].co+nb[1].co)*.3
        for v,co in new.items():v.co=co
    for v in bm2.verts:v.co+=v.normal*(th*(1+.7*max(0,_mn.noise(v.co*60+off))) if v not in bnd else -th*.5)
    for f in bm2.faces:f.smooth=True
    return finish(name,bm2,M[mat],grp,scale=.15)

def _limb(name,pts,r0,r1,M,grp,seed,ends=('broken','tip'),sides=None,peel=0.,moss=0.,moss_thr=.3,rough=.07,mat='bark',spl=1.,knot=0,bulge=.12):
    """one piece of branch along pts: rings with bark bumps, own 'Tiled' UV (u round, v along: the scan's furrows run along the branch);
    ends: 'tip' (closes to a point), 'cut' (flat, pale wood), 'broken' (a crown of pale splinters, every other one long; spl: their length);
    peel: patches where the bark is gone (pale wood, a little sunk); moss: a shell over the faces looking up; knot: bumps of old side shoots"""
    r_=_rnd.Random(seed);pts=[Vector(p) for p in pts];n=len(pts)
    sides=sides or (8 if r0>.028 else 6 if r0>.009 else 5 if r0>.004 else 4)
    s=[0.]
    for a,b in zip(pts,pts[1:]):s.append(s[-1]+(b-a).length)
    L=max(s[-1],1e-6);Tl=min(.5,max(.05,r0*10));circ=math.tau*r0;off=Vector((r_.uniform(0,40),r_.uniform(0,40),r_.uniform(0,40)));du=r_.random()
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');rings=[];fr=[];prev=None;roll=r_.uniform(0,6.3)
    kn=[(r_.uniform(.15,.85),r_.uniform(0,6.3)) for _ in range(knot)];rad=[]
    for i,p in enumerate(pts):
        t=(pts[min(i+1,n-1)]-pts[max(i-1,0)]).normalized()
        u=(prev-t*prev.dot(t)).normalized() if prev is not None else (Matrix.Rotation(roll,3,t)@t.orthogonal()).normalized();prev=u;v=t.cross(u);fr.append((t,u,v))
        f=s[i]/L;r=r0+(r1-r0)*f;rad.append(r);row=[]
        for k in range(sides):
            a=math.tau*k/sides;d=u*math.cos(a)+v*math.sin(a);rr=r*(1+rough*_mn.noise(p*(2.5/r0)+d*.8+off)+bulge*_mn.noise(Vector((s[i]/(r0*7),0,0))+off))   # bulge: slow swelling along the length
            for kt,ka in kn:rr+=r0*.35*math.exp(-((f-kt)*L/(r0*1.6))**2)*max(0.,math.cos(a-ka))**3
            row.append(bm.verts.new(p+d*rr))
        rings.append(row)
    U=lambda k:du+k/sides*circ/Tl;peelv=set()
    for i in range(n-1):
        for k in range(sides):
            k1=(k+1)%sides;fc=bm.faces.new((rings[i][k],rings[i][k1],rings[i+1][k1],rings[i+1][k]))
            for l,(kk,ii) in zip(fc.loops,((k,i),(k+1,i),(k+1,i+1),(k,i+1))):l[lay].uv=(U(kk),s[ii]/Tl)
            if peel and _mn.noise(Vector((s[i]/(r0*7),math.cos(math.tau*k/sides)*1.4,math.sin(math.tau*k/sides)*1.4))+off)>.62-peel:fc.material_index=1;peelv.update(fc.verts)
    for i,row in enumerate(rings):
        for v in row:
            if v in peelv:v.co=pts[i]+(v.co-pts[i])*.9
    def cap(i,sgn,kind):
        p=pts[i];t=fr[i][0]*sgn;u,v=fr[i][1],fr[i][2];row=rings[i];r=rad[i]
        def uvp(q):d=q-p;return (d.dot(u)/Tl+.31,d.dot(t)/Tl+d.dot(v)/Tl*.3+.17)
        if kind=='tip':c=bm.verts.new(p+t*r*1.8);fs=[(row[k],row[(k+1)%sides],c) for k in range(sides)];mi=0
        elif kind=='cut':c=bm.verts.new(p+t*r*.15);fs=[(row[k],row[(k+1)%sides],c) for k in range(sides)];mi=1
        else:
            sp=[]
            for k in range(sides):
                Lk=r*spl*(r_.uniform(1.,3.4) if k%2==0 else r_.uniform(.2,1.1))
                sp.append(bm.verts.new(row[k].co+t*Lk-(row[k].co-p)*r_.uniform(.15,.5)))
            c=bm.verts.new(p+t*r*.5)
            fs=[(row[k],row[(k+1)%sides],sp[(k+1)%sides],sp[k]) for k in range(sides)]+[(sp[k],sp[(k+1)%sides],c) for k in range(sides)];mi=1
        for vs in fs:
            fc=bm.faces.new(vs);fc.material_index=mi
            for l in fc.loops:l[lay].uv=uvp(l.vert.co)
    cap(0,-1,ends[0]);cap(n-1,1,ends[1])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.normal_update()
    for f in bm.faces:f.smooth=f.material_index==0
    if moss:
        mf=[f for f in bm.faces if f.material_index==0 and f.normal.z+.6*_mn.noise(f.calc_center_median()*(1.2/max(r0,.01))+off)>moss_thr+(1-moss)*.35]
        if mf:_shell(name+'_moss',bm,mf,M,grp,seed,th=min(.005,max(.0015,r0*.18)))
    o=finish(name,bm,M[mat],grp,keep_uv=True);o.data.materials.append(M['woodpale']);return o

def _path(p0,yaw,L,r0,r1,seed,turns=(),wob=.05,z0=None,ztrans=.15,lift=0.,pitch=0.,bury=.4):
    """a lying branch's centre line: heading yaw in the ground plane, bent by turns [(t, angle, width)], a small wobble.
    z: the branch rests on the ground with bury × r (at least 3.5 mm) in the soil; z0: the start height (a side branch leaves
    its parent's axis and comes down to the ground over ztrans m); lift: the far end raised that many metres (resting on something);
    pitch: a straight rise (twigs sticking up from a lying branch)"""
    r_=_rnd.Random(seed);ds=max(.012,min(.08,r0*2.2,L/6));n=max(4,int(L/ds)+1);ph=r_.uniform(0,6.3);p=Vector(p0);pts=[p.copy()]
    for i in range(1,n):
        t=i/(n-1);y=yaw+sum(a*(.5+.5*math.tanh((t-tt)/max(w,.01))) for tt,a,w in turns)+wob*math.sin(t*L*4+ph)
        p=p+Vector((math.cos(y)*math.cos(pitch),math.sin(y)*math.cos(pitch),math.sin(pitch)))*L/(n-1);pts.append(p.copy())
    for i,q in enumerate(pts):
        t=i/(n-1);r=r0+(r1-r0)*t;zg=r-max(bury*r,.0035)+lift*t**1.5+(q.z-p0[2] if pitch else 0)
        if z0 is not None:w=min(1.,t*L/ztrans);w=w*w*(3-2*w);zg=z0+(zg-z0)*w
        q.z=zg if not pitch else q.z   # a rising branch keeps its straight climb from p0
    return pts

def _sprigs(name,p,yaw,L,r,M,grp,r_,depth=0,maxd=1,up=.3,mat='bark'):
    """small twigs at a thin end: each a gently bent stick rising a little off the branch, two children from its upper half"""
    pitch=r_.uniform(.06,up);d=Vector((math.cos(yaw)*math.cos(pitch),math.sin(yaw)*math.cos(pitch),math.sin(pitch)))
    side=Vector((-math.sin(yaw),math.cos(yaw),0))*r_.uniform(-1,1)*L*.08
    P=lambda t:Vector(p)+d*L*t+side*math.sin(math.pi*t)
    _limb(name,[P(t) for t in (0,.34,.67,1.)],r,max(.0008,r*.45),M,grp,r_.randint(0,99999),ends=('cut','tip'),sides=4 if r>.0025 else 3,rough=0.,mat=mat)
    if depth<maxd:
        for c,sg in enumerate((-1,1)):
            t=r_.uniform(.4,.8);_sprigs(f'{name}_{c}',P(t),yaw+sg*r_.uniform(.35,.8),L*r_.uniform(.45,.65),max(.0008,r*(1-.55*t)*.6),M,grp,r_,depth+1,maxd,up,mat)

def _lying(name,L,r0,r1,M,grp,seed,turns=(),wob=.05,sides=(),ends=('broken','broken'),moss=0.,peel=0.,spl=1.,knot=0,tip_sprigs=0,sprig_L=.2,mat='bark'):
    """a lying branch along +X with side branches [(t, side ±1, angle, length, radius, end, sprigs)] that come off its axis and
    lie down beside it; thin ends may carry small twigs"""
    r_=_rnd.Random(seed);pts=_path((-L/2,0,0),0.,L,r0,r1,seed,turns,wob)
    _limb(name,pts,r0,r1,M,grp,seed,ends=ends,peel=peel,moss=moss,spl=spl,knot=knot,mat=mat)
    s=[0.]
    for a,b in zip(pts,pts[1:]):s.append(s[-1]+(b-a).length)
    for j,sd in enumerate(sides):
        t,sg,ang,Lc,rc,end,spr=sd[:7];pt=sd[7] if len(sd)>7 else 0.   # pt: the side branch rises at that angle instead of lying down
        i=min(range(len(pts)),key=lambda i:abs(s[i]-t*s[-1]));d=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]);yaw=math.atan2(d.y,d.x)+sg*ang
        cp=_path(pts[i],yaw,Lc,rc,rc*.5,seed+31*j+1,turns=((.5,-sg*ang*.35,.3),),wob=.04,z0=pts[i].z,ztrans=max(.06,Lc*.3),pitch=pt)
        _limb(f'{name}_b{j}',cp,rc,rc*.5,M,grp,seed+31*j+2,ends=('cut',end),moss=moss*.6,mat=mat)
        if spr:
            d=cp[-1]-cp[-2];y=math.atan2(d.y,d.x)
            for q in range(spr):_sprigs(f'{name}_b{j}_s{q}',cp[-1-q*2],y+(-.5+q*.5),sprig_L*.8,rc*.45,M,grp,r_,mat=mat)
    for q in range(tip_sprigs):
        i=len(pts)-1-q*2;d=pts[i]-pts[i-1];_sprigs(f'{name}_s{q}',pts[i],math.atan2(d.y,d.x)+(-.45+q*.45),sprig_L,r1*.8,M,grp,r_,mat=mat)
    _centre()

O_LIE='footprint centre, z = 0 on the ground; the branch lies on it with 3–8 mm (40 % of its radius) in the soil, side twigs rise off it'
W=dict(grime=.5,wear=.5,origin_text=O_LIE)
# ---------------- DP14 thin twigs (three-views: art/references/DP14/prompt.txt) ----------------
def dp14_01(M):
    """短細枝 (DP14A-cand-1): 0.2 m, 1 cm thick, one small side twig, a fibrous broken end"""
    _lying('DP14_01',.2,.005,.0035,M,'Body',14101,turns=((.5,.15,.2),),sides=((.45,1,.6,.06,.0025,'tip',0),),ends=('broken','tip'));return dict(W)
def dp14_02(M):
    """分叉細枝 (DP14B-cand-2): 0.35 m, 1.5 cm, a fork near one end, both ends splintered"""
    _lying('DP14_02',.35,.0075,.005,M,'Body',14201,sides=((.72,-1,.45,.1,.004,'tip',0),),ends=('broken','broken'));return dict(W)
def dp14_03(M):
    """微彎細枝 (DP14C-cand-2): 0.5 m, 2 cm, slightly curved, two short side twigs, a fibrous broken end"""
    _lying('DP14_03',.5,.01,.006,M,'Body',14301,turns=((.3,.22,.25),(.7,.2,.25)),sides=((.35,1,.7,.08,.004,'tip',0),(.6,-1,.6,.06,.0035,'tip',0)),ends=('broken','tip'));return dict(W)
def dp14_04(M):
    """S 形苔枝 (DP14D-cand-4): 0.7 m, 2.5 cm, a gentle S, a patch of moss on top, splintered ends"""
    _lying('DP14_04',.7,.0125,.008,M,'Body',14401,turns=((.3,.45,.15),(.7,-.5,.15)),ends=('broken','broken'),moss=.45);return dict(W)
def dp14_05(M):
    """剝皮細枝 (DP14E-cand-1): 0.9 m, 3 cm, three side twigs, a little bark peeled off, fibrous ends"""
    _lying('DP14_05',.9,.015,.009,M,'Body',14501,turns=((.5,.1,.3),),sides=((.3,1,.6,.15,.006,'tip',0),(.5,-1,.7,.12,.005,'tip',0),(.75,1,.5,.1,.004,'tip',0)),ends=('broken','broken'),peel=.22);return dict(W)
def dp14_06(M):
    """兩折歪枝 (DP14F-cand-2): 1.1 m, 3 cm, bent in two places, dark lichen spots, splintered ends"""
    _lying('DP14_06',1.1,.015,.01,M,'Body',14601,turns=((.33,.55,.04),(.68,-.62,.04)),wob=.03,ends=('broken','broken'),knot=2);return dict(W)
def dp14_07(M):
    """直細枝 (DP14G-cand-2): 1.3 m, 3.5 cm, straight, a forked thin end, a fibrous broken thick end, a little moss"""
    _lying('DP14_07',1.3,.0175,.009,M,'Body',14701,wob=.02,sides=((.86,1,.35,.18,.005,'tip',0),(.9,-1,.3,.14,.004,'tip',0)),ends=('broken','tip'),moss=.2);return dict(W)
def dp14_08(M):
    """長細枝 (DP14H-cand-3): 1.5 m, 4 cm, many small side twigs along it, splintered ends"""
    _lying('DP14_08',1.5,.02,.009,M,'Body',14801,turns=((.5,.12,.3),),sides=((.15,1,.7,.08,.004,'tip',0),(.3,-1,.6,.12,.005,'tip',0),(.45,1,.55,.1,.004,'tip',0),(.6,-1,.7,.09,.004,'tip',0),(.75,1,.5,.12,.004,'tip',0),(.88,-1,.6,.07,.003,'tip',0)),ends=('broken','broken'),knot=2);return dict(W)

# ---------------- DP15 medium broken branches (three-views: art/references/DP15/prompt.txt) ----------------
def dp15_01(M):
    """一叉斷枝 (DP15A-cand-1): 1.6 m, 7 cm, one fork, long pale splinters at the broken end, a few twigs at the other"""
    _lying('DP15_01',1.6,.035,.016,M,'Body',15101,turns=((.5,.12,.3),),sides=((.45,1,.5,.6,.018,'tip',2,.35),),ends=('broken','tip'),spl=2.2,tip_sprigs=2,knot=2);return dict(W)
def dp15_02(M):
    """彎曲雙叉 (DP15B-cand-3): 2 m, 8 cm, curving, two forks, a jagged broken end, twigs at the thin end, moss patches"""
    _lying('DP15_02',2.0,.04,.017,M,'Body',15201,turns=((.3,.3,.3),(.7,.25,.3)),sides=((.35,-1,.6,.55,.018,'tip',2,.3),(.62,1,.5,.45,.015,'tip',1)),ends=('broken','tip'),moss=.45,spl=1.8,tip_sprigs=2);return dict(W)
def dp15_03(M):
    """長側枝 (DP15C-cand-1): 2.2 m, 9 cm, fairly straight with one long side branch, a broken end with pale splinters"""
    _lying('DP15_03',2.2,.045,.02,M,'Body',15301,wob=.03,sides=((.4,1,.45,1.0,.024,'tip',2,.12),),ends=('broken','tip'),spl=2.,tip_sprigs=2,knot=2);return dict(W)
def dp15_04(M):
    """Y 形斷枝 (DP15D-cand-1): 2.5 m, 9 cm, a Y fork in the middle, one broken end, twiggy thin ends, lichen spots"""
    _lying('DP15_04',2.5,.045,.018,M,'Body',15401,turns=((.5,-.3,.05),),sides=((.5,1,.5,1.15,.028,'tip',3,.2),),ends=('broken','tip'),spl=1.8,tip_sprigs=3,knot=1);return dict(W)
def dp15_05(M):
    """剝皮彎枝 (DP15E-cand-1): 2.8 m, 10 cm, gently bent, bark peeling showing pale wood, one broken end, a few twigs"""
    _lying('DP15_05',2.8,.05,.022,M,'Body',15501,turns=((.5,.25,.4),),sides=((.7,1,.6,.3,.01,'tip',1,.45),(.82,-1,.5,.25,.008,'tip',0,.3)),ends=('broken','tip'),peel=.25,spl=1.8,tip_sprigs=2);return dict(W)
def dp15_06(M):
    """苔斷枝 (DP15F-cand-1): 3 m, 11 cm, two side branches, moss on the upper side, long pale splinters, twigs at the other end"""
    _lying('DP15_06',3.0,.055,.022,M,'Body',15601,turns=((.45,.15,.3),),sides=((.38,1,.55,.7,.025,'tip',2,.32),(.6,-1,.6,.6,.02,'tip',2)),ends=('broken','tip'),moss=.5,spl=2.6,tip_sprigs=3,knot=1);return dict(W)

# ---------------- DP22 soaked leaves and twigs for the DS03 puddle (three-view: art/references/DP22/prompt.txt) ----------------
def dp22_01(M):
    """水窪落葉 (DP22A-cand-1): a dozen dark wet leaves and three thin twigs lying flat in a 0.8 m puddle, some half sunk"""
    r_=_rnd.Random(22101)
    for j,(x,y,yaw,L,r) in enumerate(((-.12,.05,.3,.38,.006),(.08,-.1,2.2,.3,.005),(.05,.14,-.4,.24,.004))):
        pts=_path((x-math.cos(yaw)*L/2,y-math.sin(yaw)*L/2,0),yaw,L,r,r*.6,22110+j,wob=.04,bury=1.)   # half sunk: the axis on the water line
        _limb(f'DP22_01_t{j}',pts,r,r*.6,M,'Body',22120+j,ends=('broken','tip'),mat='bark_wet')
    for i in range(18):
        a=r_.uniform(0,math.tau);rr=math.sqrt(r_.random())*.32;x,y=math.cos(a)*rr,math.sin(a)*rr*.85
        b=r_.uniform(0,math.tau);sink=i%4==0;L=r_.uniform(.075,.12)
        d=Vector((math.cos(b),math.sin(b),-.35 if sink else r_.uniform(-.04,.04)));nn=Vector((r_.uniform(-.15,.15),r_.uniform(-.15,.15),1))
        z=-.004 if sink else .0012+.0011*i   # floating leaves each a little higher than the one before (no two in one plane)
        _leafp(f'DP22_01_l{i}',(x-d.x*L*.5,y-d.y*L*.5,z),d,nn,L,L*r_.uniform(.5,.7),M,'leaf_wet' if i%3 else 'leaf_brown','Body',shape='oval',seg=6,fold=r_.uniform(.05,.15),curl=r_.uniform(-.08,.06),lobes=r_.choice((0,5,5)))
    _centre()
    return dict(grime=.4,wear=.2,origin_text='footprint centre, z = 0 on the water line of the DS03 puddle: the leaves float on it or dip under, the twigs lie half sunk')

TABLE.update({'DP14_01':('TwigShort',(.26,.12,.04),'standard'),'DP14_02':('TwigForked',(.42,.14,.04),'standard'),'DP14_03':('TwigCurved',(.58,.22,.05),'standard'),
 'DP14_04':('TwigSMossy',(.80,.26,.06),'standard'),'DP14_05':('TwigPeeled',(1.0,.30,.07),'standard'),'DP14_06':('TwigCrooked',(1.22,.40,.07),'standard'),
 'DP14_07':('TwigStraightFork',(1.45,.30,.08),'standard'),'DP14_08':('TwigLong',(1.65,.36,.09),'standard'),
 'DP15_01':('BranchForkA',(1.9,.70,.30),'standard'),'DP15_02':('BranchCurvedTwoFork',(2.3,.90,.32),'standard'),'DP15_03':('BranchLongSide',(2.5,.95,.32),'standard'),
 'DP15_04':('BranchYFork',(2.8,1.2,.34),'standard'),'DP15_05':('BranchPeeled',(3.1,1.0,.34),'standard'),'DP15_06':('BranchMossy',(3.3,1.3,.36),'standard'),
 'DP22_01':('PuddleLeavesTwigs',(.80,.70,.06),'standard')})
PROPS.update({k:globals()[k.lower()] for k in ('DP14_01','DP14_02','DP14_03','DP14_04','DP14_05','DP14_06','DP14_07','DP14_08','DP15_01','DP15_02','DP15_03','DP15_04','DP15_05','DP15_06','DP22_01')})
