# DP16 小樹皮片與樹皮屑 (six) and DP21 小朽樹樁 (four) — exec'd by build_floor.py after floor_items3.py (bark sources, _limb, _shell, _centre).

def _settle(depth=.004):
    """the lowest point depth m under the ground (a piece resting on uneven soil never floats)"""
    z=min(v.co.z for o in parts for v in o.data.vertices)
    for o in parts:o.data.transform(Matrix.Translation((0,0,-z-depth)))

def _barkpiece(name,L,W,curl,thick,M,grp,seed,roll=0.,twist=0.,lcurl=0.,flip=False,moss=0.,at=(0,0,0),yaw=0.,nu=10,nv=None):
    """one piece of fallen bark along +X: across it the section bends by `curl` radians (an arch, bark side out and up),
    roll: one edge rolls further in; twist: the section turns end to end; lcurl: both ends lift; flip: lying the other way up
    (pale inner bark up). Outer face: the scan bark with fissures in the mesh; inner face: pale inner bark; edges: pale broken wood."""
    r_=_rnd.Random(seed);off=Vector((r_.uniform(0,40),r_.uniform(0,40),r_.uniform(0,40)));nv=nv or max(6,min(16,int(L/.022)))
    Tl=.25;bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');O=[];I=[];N=12
    for j in range(nv+1):
        b=j/nv;wb=W*(1+.14*_mn.noise(Vector((b*3,0,0))+off));ro=[];ri=[]
        for i in range(nu+1):
            a=i/nu-.5
            g=min(.05,.35/nv);b2=b+(g*(1+_mn.noise(Vector((a*4,9,0))+off)) if j==0 else (-g*1.1*(1+_mn.noise(Vector((a*4,7,0))+off)) if j==nv else 0))   # never past the next row (no fold)   # ragged torn ends
            phi=lambda q:curl*q+roll*max(0.,(q-.15)/.35)**2
            y=z=0.;st=a/N   # walk across the section from its middle
            for k in range(N):
                q=st*(k+.5);y+=math.cos(phi(q))*st*wb;z-=math.sin(phi(q))*st*wb*(1 if a>=0 else 1)
            ph=phi(a);n=Vector((0,math.sin(ph),math.cos(ph)))
            fis=1-abs(_mn.noise(Vector((a*wb*45,b2*L*6,0))+off))   # bark plates with furrows along the length
            c=Vector((b2*L,y,z));h=thick*(.5+.45*fis*(1 if thick>.007 else .5))
            po=c+n*h;pi_=c-n*thick*.5
            tw=Matrix.Rotation(twist*(b2-.5),3,'X')
            po=tw@po;pi_=tw@pi_
            lift=lcurl*L*abs(2*b2-1)**3;po.z+=lift;pi_.z+=lift
            ro.append(bm.verts.new(po));ri.append(bm.verts.new(pi_))
        O.append(ro);I.append(ri)
    def quad(vs,mi,uvs):
        f=bm.faces.new(vs);f.material_index=mi
        for l,uv in zip(f.loops,uvs):l[lay].uv=uv
        return f
    U=lambda i:(i/nu-.5)*W/Tl;V=lambda j:j/nv*L/Tl
    outer=[]
    for j in range(nv):
        for i in range(nu):
            outer.append(quad((O[j][i],O[j][i+1],O[j+1][i+1],O[j+1][i]),0,((U(i),V(j)),(U(i+1),V(j)),(U(i+1),V(j+1)),(U(i),V(j+1)))))
            quad((I[j][i],I[j+1][i],I[j+1][i+1],I[j][i+1]),1,((U(i),V(j)),(U(i),V(j+1)),(U(i+1),V(j+1)),(U(i+1),V(j))))
    for j in range(nv):   # the two long edges
        for i in (0,nu):quad((O[j][i],O[j+1][i],I[j+1][i],I[j][i]),2,((0,V(j)),(0,V(j+1)),(.05,V(j+1)),(.05,V(j))))
    for j in (0,nv):   # the torn ends
        for i in range(nu):quad((O[j][i],I[j][i],I[j][i+1],O[j][i+1]),2,((U(i),0),(U(i),.05),(U(i+1),.05),(U(i+1),0)))
    T=Matrix.Translation(Vector(at))@Matrix.Rotation(yaw,4,'Z')@(Matrix.Rotation(math.pi,4,'X') if flip else Matrix.Identity(4))@Matrix.Translation((-L/2,0,0))
    bm.transform(T);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.normal_update()
    for f in bm.faces:f.smooth=f.material_index!=2
    if moss:
        mf=[f for f in bm.faces if f.material_index==0 and f.normal.z+.6*_mn.noise(f.calc_center_median()*14+off)>.35+(1-moss)*.35]
        if mf:_shell(name+'_moss',bm,mf,M,grp,seed,th=.003)
    o=finish(name,bm,M['bark'],grp,keep_uv=True);o.data.materials.append(M['barkin']);o.data.materials.append(M['woodpale']);return o

O_BARK='footprint centre, z = 0 on the ground; the piece rests on it, its lowest edge 4 mm in the soil'
WB=dict(grime=.5,wear=.4,origin_text=O_BARK)
# ---------------- DP16 bark pieces (three-views: art/references/DP16/prompt.txt) ----------------
def dp16_01(M):
    """半管樹皮 (DP16A-cand-1): a small piece 0.15 m rolled like a half tube, rough grey-brown outside, pale tan inside"""
    _barkpiece('DP16_01',.15,.10,2.7,.006,M,'Body',16101);_settle();return dict(WB)
def dp16_02(M):
    """厚平樹皮 (DP16B-cand-1): flat and slightly cupped, 0.25 × 0.12 m, thick with fissures, pale inside"""
    _barkpiece('DP16_02',.25,.13,-.45,.014,M,'Body',16201,nu=10);_settle();return dict(WB)
def dp16_03(M):
    """扭轉樹皮條 (DP16C-cand-1): a long thin strip 0.35 m, 5 cm wide, twisted, curling at both ends"""
    _barkpiece('DP16_03',.35,.05,.9,.005,M,'Body',16301,twist=1.7,lcurl=.10,nu=6,nv=16);_settle();return dict(WB)
def dp16_04(M):
    """樹皮屑 (DP16D-cand-1): five broken flakes about 0.2 m across lying together, some upside down"""
    r_=_rnd.Random(16401)
    for i,(x,y,L,W,fl) in enumerate(((0,0,.09,.06,False),(-.06,.04,.07,.045,True),(.06,.03,.065,.04,False),(.03,-.05,.06,.04,True),(-.05,-.035,.05,.035,False))):
        _barkpiece(f'DP16_04_f{i}',L,W,r_.uniform(.3,1.1),.005,M,'Body',16410+i,flip=fl,at=(x,y,.002*i),yaw=r_.uniform(0,math.tau),nu=6,nv=6)
    _settle();return dict(WB)
def dp16_05(M):
    """彎厚樹皮塊 (DP16E-cand-1): a thick chunk 0.3 m, strongly curved, deep fissures, a little moss, pale inside"""
    _barkpiece('DP16_05',.30,.17,2.0,.024,M,'Body',16501,moss=.35,nu=12);_settle();return dict(WB)
def dp16_06(M):
    """一邊捲起的大樹皮 (DP16F-cand-1): a large sheet 0.4 × 0.2 m, rolled at one edge"""
    _barkpiece('DP16_06',.40,.24,.35,.008,M,'Body',16601,roll=-2.6,nu=14);_settle();return dict(WB)

# ---------------- DP21 rotten stumps (three-views: art/references/DP21/prompt.txt) ----------------
def _rotin_src(S):
    K.rng=np.random.default_rng(2101)   # the rotten inside of a stump: warm orange-brown, coarse fibres along V, dark gaps and pits
    vf=np.clip((fbm(36,2,aniso=24)-.5)*2+.5,0,1);pit=np.clip((fbm(14,2)-.62)*4,0,1);gap=np.clip((.32-vf)*4,0,1)
    S['rotin']=(lerp((.16,.09,.045),(.48,.29,.14),np.clip(.5+.6*(fbm(4,3,aniso=6)-.5)+.35*(vf-.5),0,1))*(1-.45*gap[...,None])*(1-.4*pit[...,None]),1.5*vf-1.1*pit,2.6,.9,0,0)
    S['moss_st']=(np.clip(S['moss'][0]*np.array([1.5,1.55,1.4]),0,1),)+tuple(S['moss'][1:])   # stump moss: a little lighter olive (it catches the light on the upright wall)
    S['rotout']=(S['rotin'][0]*np.array([.8,.78,.8])+np.array([.03,.03,.03]),)+tuple(S['rotin'][1:])   # bark gone on the outside: the rotten wood, weathered greyer than inside
SRC_HOOKS.append(_rotin_src)

def _stump(name,H,R,M,grp,seed,cols=26,hollow=.72,teeth=.22,spikes=(),notches=(),roots=5,moss=.5,root_r=.28):
    """a rotten hollow stump: a lathe of columns whose tops are jagged (teeth; spikes [(angle, extra height × H, width)];
    notches [(angle, depth × H, width)] break the wall down), flaring into root buttresses at the foot, 6 cm under the ground;
    the bark cut by deep vertical fissures, patches of it gone (rotten wood showing); inside a rough orange-brown rotten wall
    and floor, pale splintered wood only on the broken rim; thick roots run out of the buttresses into the soil, thin ones between;
    moss in blobs and streaks over the foot, down from the rim and on the rim itself"""
    r_=_rnd.Random(seed);off=Vector((r_.uniform(0,40),r_.uniform(0,40),r_.uniform(0,40)))
    ra=[math.tau*k/roots+r_.uniform(-.3,.3) for k in range(roots)]
    def dang(a,b):return (a-b+math.pi)%math.tau-math.pi
    hs=[]
    for k in range(cols):
        th=math.tau*k/cols;h=H*(1-teeth*(.5+.5*_mn.noise(Vector((math.cos(th)*2.2,math.sin(th)*2.2,0))+off))-teeth*1.1*r_.random()**2)   # broad high and low runs, then single splinters
        if r_.random()<.22:h+=H*teeth*.6*r_.random()   # a lone splinter standing up
        for a,e,w in spikes:h+=H*e*math.exp(-(dang(th,a)/w)**2)
        for a,dd,w in notches:h-=H*dd*math.exp(-(dang(th,a)/w)**2)
        hs.append(max(H*.15,h))
    butt=lambda th:sum(max(0.,math.cos(dang(th,a)))**10 for a in ra)
    def rout(th,z):
        zz=max(z,0.);fis=.15*abs(_mn.noise(Vector((math.cos(th)*5,math.sin(th)*5,z*.8))+off))   # ridged noise: deep vertical fissures between the bark plates
        return R*(1+(.38+.7*butt(th))*math.exp(-zz/(.17*H)))*(1.05-fis+.05*_mn.noise(Vector((math.cos(th)*2,math.sin(th)*2,z*3))+off))
    FO=(0,.03,.07,.12,.18,.26,.35,.45,.55,.65,.74,.82,.89,.95,1.);FI=(0,.15,.3,.45,.6,.75,.88,1.);Tl=.4;fl=H*.1
    bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');O=[];I=[]
    for k in range(cols):
        th=math.tau*k/cols;c,s=math.cos(th),math.sin(th);col=[];ci=[]
        for f in FO:z=-.06+(hs[k]+.06)*f;r=rout(th,z);col.append(bm.verts.new((c*r,s*r,z)))
        for f in FI:
            z=fl+(hs[k]-H*.04-fl)*f;r=min(rout(th,z)*hollow*(1+.16*_mn.noise(Vector((c*3,s*3,z*5))+off)-.12*abs(_mn.noise(Vector((c*9,s*9,z*2))+off))),rout(th,z)-.012)   # crumbling: lumps and gouges
            ci.append(bm.verts.new((c*r,s*r,z)))
        O.append(col);I.append(ci)
    def quad(vs,mi,uvs,smooth=True):
        f=bm.faces.new(vs);f.material_index=mi;f.smooth=smooth
        for l,uv in zip(f.loops,uvs):l[lay].uv=uv
        return f
    circ=math.tau*R/Tl;U=lambda k:k/cols*circ;out=[]
    for k in range(cols):
        k1=(k+1)%cols
        for j in range(len(FO)-1):out.append(quad((O[k][j],O[k1][j],O[k1][j+1],O[k][j+1]),0,((U(k),O[k][j].co.z/Tl),(U(k+1),O[k1][j].co.z/Tl),(U(k+1),O[k1][j+1].co.z/Tl),(U(k),O[k][j+1].co.z/Tl))))
        for j in range(len(FI)-1):quad((I[k][j],I[k][j+1],I[k1][j+1],I[k1][j]),1,((U(k),I[k][j].co.z/Tl),(U(k),I[k][j+1].co.z/Tl),(U(k+1),I[k1][j+1].co.z/Tl),(U(k+1),I[k1][j].co.z/Tl)))
        quad((O[k][-1],O[k1][-1],I[k1][-1],I[k][-1]),2,((U(k),0),(U(k+1),0),(U(k+1),.08),(U(k),.08)),smooth=False)   # the broken rim
    cf=bm.verts.new((0,0,fl-.01));cb=bm.verts.new((0,0,-.06))
    for k in range(cols):
        k1=(k+1)%cols;th=math.tau*k/cols
        quad((I[k][0],I[k1][0],cf),1,((math.cos(th)*R/Tl,math.sin(th)*R/Tl),(math.cos(th+math.tau/cols)*R/Tl,math.sin(th+math.tau/cols)*R/Tl),(0,0)))
        quad((O[k1][0],O[k][0],cb),1,((0,0),(.1,0),(.05,.1)))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.normal_update()
    fq=2.5/R;taken=set()
    if moss:   # moss: the best-scoring share of the outer faces (blobs, streaks down from the rim, the foot and the top band), and patches on the rim
        def score(f):
            c_=f.calc_center_median();th=math.atan2(c_.y,c_.x);k=int(round(th/math.tau*cols))%cols
            zb=max(0.,1-c_.z/(H*.3));zt=max(0.,1-(hs[k]-c_.z)/(H*.28))
            return .6*_mn.noise(c_*fq*.6+off)+.5*_mn.noise(Vector((math.cos(th)*3,math.sin(th)*3,c_.z*.6))+off*1.7)+.3*max(zb,zt)+.15*f.normal.z
        cand=[f for f in out if f.calc_center_median().z>-.01 and f.normal.z>-.35]
        sc_=sorted(((score(f),i) for i,f in enumerate(cand)),reverse=True);mf=[cand[i] for _,i in sc_[:int(len(cand)*moss*.62)]]
        rim=[f for f in bm.faces if f.material_index==2 and f.normal.z>.2 and _mn.noise(f.calc_center_median()*fq+off)>.3-moss*.4]
        bm.faces.index_update();taken={f.index for f in mf}
        _shell(name+'_moss',bm,mf+rim,M,grp,seed,th=min(.01,.005+R*.035),mat='moss_st',relax=3)
    for f in out:   # bark gone in patches: the rotten wood under it shows (outside the moss)
        if f.index not in taken and _mn.noise(f.calc_center_median()*fq*.35+off*2.3)>.3:f.material_index=3
    o=finish(name,bm,M['bark'],grp,keep_uv=True);o.data.materials.append(M['rotin']);o.data.materials.append(M['woodpale']);o.data.materials.append(M['rotout'])
    rl=[(a,1.) for a in ra]+[(a+math.pi/roots*r_.uniform(.7,1.3),.5) for a in ra]   # thick roots from the buttresses, thin ones between
    for j,(a,sz) in enumerate(rl):   # roots: out of the foot, arching down into the soil
        rr=R*root_r*sz*r_.uniform(.85,1.15);Lr=R*r_.uniform(2.6,3.4)*(.55+.45*sz);pts=[];w=r_.uniform(-1,1);aa=a
        p=Vector((math.cos(a),math.sin(a),0))*R*(.5 if sz==1 else .8)
        for i in range(11):   # out of the buttress, then lying half buried along the ground, winding; the tip dives
            t=i/10;z=H*(.2 if sz==1 else .06)*max(0.,1-t/.3)**1.5+rr*(.15-.3*t)-(max(0.,t-.85)/.15)*rr*.5
            pts.append((p.x,p.y,z));aa+=w*.35*math.sin(t*5+j);p=p+Vector((math.cos(aa),math.sin(aa),0))*Lr/10
        _limb(f'{name}_r{j}',pts,rr,rr*.4,M,grp,seed+40+j,ends=('cut','tip'),bulge=.1,rough=.09,mat='bark_root',sides=7 if sz==1 else 5)
    return o

O_STUMP='trunk centre, z = 0 on the ground; the stump foot and the roots run on 6–10 cm under it'
WS=dict(grime=.7,wear=.5,origin_text=O_STUMP)
def dp21_01(M):
    """小朽樁 (DP21A-cand-1): 0.3 m tall, 0.25 m wide, hollow, jagged top, moss on the sides, roots into the soil"""
    _stump('DP21_01',.30,.095,M,'Body',21101,cols=30,roots=4,moss=.55);return dict(WS)
def dp21_02(M):
    """破邊空心樁 (DP21B-cand-1): 0.5 m, 0.4 m wide, one side broken away showing the hollow, moss and lichen"""
    _stump('DP21_02',.50,.15,M,'Body',21201,cols=34,notches=((-math.pi/2,.62,.8),),roots=5,moss=.45);return dict(WS)
def dp21_03(M):
    """高木刺樁 (DP21C-cand-1): 0.7 m with a tall jagged splinter on one side, hollow, moss on the lower half"""
    _stump('DP21_03',.48,.19,M,'Body',21301,cols=36,spikes=((2.2,.5,.16),(2.7,.25,.1)),teeth=.25,roots=5,moss=.6);return dict(WS)
def dp21_04(M):
    """裂兩半的寬樁 (DP21D-cand-1): 1.0 m, 0.7 m wide, split into two jagged parts, soft rotten centre, thick moss, roots"""
    _stump('DP21_04',1.0,.26,M,'Body',21401,cols=40,notches=((-1.4,.7,.2),(1.75,.62,.2)),spikes=((0.2,.12,.2),(3.4,.1,.2)),hollow=.7,roots=6,moss=.8,root_r=.26);return dict(WS)

TABLE.update({'DP16_01':('BarkHalfTube',(.20,.14,.07),'standard'),'DP16_02':('BarkFlatThick',(.30,.18,.06),'standard'),'DP16_03':('BarkStripTwisted',(.40,.12,.09),'standard'),
 'DP16_04':('BarkFlakes',(.26,.22,.05),'standard'),'DP16_05':('BarkChunkCurved',(.36,.22,.12),'standard'),'DP16_06':('BarkSheetRolled',(.46,.28,.12),'standard'),
 'DP21_01':('StumpSmall',(.72,.72,.38),'standard'),'DP21_02':('StumpBrokenSide',(1.05,1.05,.60),'standard'),'DP21_03':('StumpSplinter',(1.4,1.4,.82),'standard'),'DP21_04':('StumpSplit',(1.8,1.8,1.12),'standard')})
PROPS.update({k:globals()[k.lower()] for k in ('DP16_01','DP16_02','DP16_03','DP16_04','DP16_05','DP16_06','DP21_01','DP21_02','DP21_03','DP21_04')})
