# C 林下植物（undergrowth-c）: shared plant parts, then SH01. Blender: X = width, -Y = front, Z = up; origin at the stem base on the ground.
# Method (樹木重做-v2-分工.md, tree-method guide): stems → side branches → twigs in three clear orders of thickness;
# leaves are five-vertex leaves (four outline points and a raised midrib) set one by one along the twigs, alternate, stalk on the twig.

def _crv(ctrl,n=24):
    """Catmull-Rom through the control points, n samples; returns the points and P(u) by arc length"""
    C=[Vector(c) for c in ctrl];C=[C[0]*2-C[1]]+C+[C[-1]*2-C[-2]];pts=[]
    for i in range(1,len(C)-2):
        p0,p1,p2,p3=C[i-1],C[i],C[i+1],C[i+2];m=max(2,n//(len(C)-3))
        for j in range(m):
            t=j/m;t2,t3=t*t,t*t*t
            pts.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3))
    pts.append(C[-2]);s=[0.]
    for a,b in zip(pts,pts[1:]):s.append(s[-1]+(b-a).length)
    S=s[-1] or 1.
    def P(u):
        d=min(max(u,0.),1.)*S;i=max(0,min(len(s)-2,next((k for k in range(len(s)-1) if s[k+1]>=d),len(s)-2)));f=(d-s[i])/max(s[i+1]-s[i],1e-9)
        return pts[i].lerp(pts[i+1],f)
    def T(u):return (P(min(u+.01,1.))-P(max(u-.01,0.))).normalized()
    return pts,P,T,S

def _ttube(name,pts,radii,mat,grp,sides=6,scale=.3,cap0=True,cap1=True):
    """a tapering tube along pts (radius per point), frames carried along the path so it does not twist"""
    pts=[Vector(p) for p in pts];bm=bmesh.new();rings=[];prev=None
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        u=(prev-t*prev.dot(t)).normalized() if prev is not None else t.orthogonal().normalized();prev=u;v=t.cross(u)
        rings.append([bm.verts.new(p+(u*math.cos(math.tau*k/sides)+v*math.sin(math.tau*k/sides))*radii[i]) for k in range(sides)])
    for a,b in zip(rings,rings[1:]):
        for k in range(sides):bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
    if cap0:bm.faces.new(list(reversed(rings[0])))
    if cap1:bm.faces.new(rings[-1])
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)

class _Leaves:
    """many five-vertex leaves in one part: face int 'leaf' = leaf number, vertex float 'lbase' = 1 on the stalk point"""
    n=0
    def __init__(s):s.bm=bmesh.new();s.la=s.bm.faces.layers.int.new('leaf');s.lb=s.bm.verts.layers.float.new('lbase')
    def add(s,base,d,up,L,W,droop=.18,cup=.10):
        _Leaves.n+=1;k=_Leaves.n;d=Vector(d).normalized();up=Vector(up);side=d.cross(up).normalized();up=side.cross(d).normalized()
        b=Vector(base)+d*.002;mid=b+d*L*.46
        t=b+d*L-up*droop*L;r_=b+d*L*.40+side*W*.5-up*cup*W;l_=b+d*L*.40-side*W*.5-up*cup*W;m=mid+up*W*.13
        vs=[s.bm.verts.new(p) for p in (b,r_,t,l_,m)];vs[0][s.lb]=1.
        for i in range(4):
            f=s.bm.faces.new((vs[4],vs[i],vs[(i+1)%4]));f[s.la]=k;f.smooth=True
        return k
    def done(s,name,mat,grp,passes=3):
        """leaves that lie close and nearly parallel would read as one doubled surface: roll one of each such pair 26° about its midrib"""
        from mathutils.kdtree import KDTree
        lv={}
        for f in s.bm.faces:lv.setdefault(f[s.la],set()).update(f.verts)
        keys=sorted(lv)
        for _ in range(passes):
            info=[]
            for k in keys:
                vs=list(lv[k]);b_=next((v for v in vs if v[s.lb]>.5),vs[0]);c=sum((v.co for v in vs),Vector())/len(vs)
                tip=max(vs,key=lambda v:(v.co-b_.co).length);ax=(tip.co-b_.co);L=ax.length
                o=[v for v in vs if v is not b_ and v is not tip]
                n=(tip.co-b_.co).cross(o[0].co-o[1].co).normalized() if len(o)>=2 else Vector((0,0,1))
                info.append((k,vs,b_,ax.normalized() if L>0 else Vector((1,0,0)),c,n,L))
            kd=KDTree(len(info))
            for i,it in enumerate(info):kd.insert(it[4],i)
            kd.balance();moved=0;done_=set()
            for i,(k,vs,b_,ax,c,n,L) in enumerate(info):
                if i in done_:continue
                for (_,j,d) in kd.find_range(c,L*.9):
                    if j<=i or j in done_:continue
                    if abs(n.dot(info[j][5]))>.93:
                        k2,vs2,b2,ax2,c2,n2,L2=info[j];R=Matrix.Rotation(.45,3,ax2)
                        for v in vs2:v.co=b2.co+R@(v.co-b2.co)
                        done_.add(j);moved+=1
            if not moved:break
        return finish(name,s.bm,mat,grp,.06)

def _spray(L_,P,T,u0,u1,n,size,rr,phase=0.,tip=True,lift=.42,grow=(.75,1.15)):
    """leaves along one branch from u0 to u1: alternate in a spiral (137.5° apart), each leaving at 35–60° from the branch, turned up to the light"""
    Z=Vector((0,0,1))
    for i in range(n):
        u=u0+(u1-.06-u0)*(i+.5+rr.uniform(-.3,.3))/n;   # the last leaf stops short of the tip leaf
        p=P(u);t=T(u);ax=t.orthogonal().normalized()
        if abs(t.z)<.9:ax=Z.cross(t).normalized()
        ang=phase+i*2.39996+rr.uniform(-.35,.35);sd=(ax*math.cos(ang)+t.cross(ax)*math.sin(ang)).normalized()
        be=math.radians(rr.uniform(35,60));d=(t*math.cos(be)+sd*math.sin(be)+Z*lift).normalized()
        up=(Z+sd*.35-d*d.dot(Z)).normalized()
        g=grow[0]+(grow[1]-grow[0])*(u-u0)/max(u1-u0,1e-6);Ln=size*g*rr.uniform(.82,1.12)
        L_.add(p,d,up,Ln,Ln*rr.uniform(.44,.56),droop=rr.uniform(.08,.26))
    if tip:
        t=T(1.);up=(Z-t*t.dot(Z));up=up.normalized() if up.length>1e-3 else Vector((1,0,0));Ln=size*.62
        ro=rr.uniform(-.7,.7);up=(up*math.cos(ro)+t.cross(up)*math.sin(ro)).normalized()   # each tip leaf rolled its own way round the shoot
        L_.add(P(1.)-t*.004,(t+Z*.15).normalized(),up,Ln,Ln*.40,droop=.05)

# ---------------- SH01 understory broadleaf shrub (cand-2) ----------------
SH01_PAL=np.array([(.150,.235,.140),(.215,.315,.170),(.295,.400,.200),(.400,.490,.235),(.560,.600,.300)],np.float32)
def _sh_tone(px,py,pz,H,R=.85):
    """leaf colour: up and out light and warm, down and in deep and cool, blended continuously (no bands); A: canopy occlusion"""
    r=np.hypot(px,py);ex=np.clip(.62*pz/H+.48*np.clip(r/R,0,1)-.12,0,1);tone=np.clip(ex*4,0,3.999);lo=tone.astype(np.int32);mx=(tone-lo)[...,None]
    col=SH01_PAL[lo]*(1-mx)+SH01_PAL[np.minimum(lo+1,4)]*mx;occ=.50+.50*ex
    return col,occ
def SH01(M):
    """seven thin stems from one point in the leaf litter, each curving out at its own angle; three to five side branches on each,
    alternating round the stem, three or four twigs on each branch; leaves one by one along the twigs and the outer halves of
    the branches, a young leaf at every tip. The lower part of every stem is bare. One branch is broken off short.
    The stems run on 0.18 m under the ground, so the shrub can be set into uneven ground."""
    rr=random.Random(int(__import__('os').environ.get('UG_SEED',8101)));Z=Vector((0,0,1));LV=_Leaves()
    rl=random.Random(int(__import__('os').environ.get('UG_LSEED',8159)))   # the leaves have their own random stream: the branches stay put while a leaf seed is chosen
    BK,TW,LF=M['bark'],M['twig'],M['herb'];M['herb']['mid']=1.
    lean_all=Vector((.10,.16,0))   # the whole shrub leans a little to the right and back (the side view of cand-2)
    # front view: a fan across X; the side view is narrower: Y is squeezed
    stems=[(-174,34,1.32),(-142,21,1.58),(-106,9,1.78),(-66,15,1.50),(-24,25,1.64),(16,36,1.28),(146,24,1.42)]
    nb=0
    for k,(az,lean,Ls) in enumerate(stems):
        a=math.radians(az+rr.uniform(-8,8));out=Vector((math.cos(a),math.sin(a)*.55,0)).normalized();ln=math.radians(lean+rr.uniform(-4,4));ph=rr.uniform(0,6.28)
        side=Z.cross(out).normalized()
        ob=Vector((math.cos(a),math.sin(a),0))   # the stem feet stand on a ring 14 cm across, unsquashed, so no two touch
        def sp(u,out=out,ob=ob,ln=ln,ph=ph,side=side,Ls=Ls):
            return ob*.070+Z*(Ls*math.cos(ln)*u)+out*(Ls*math.sin(ln)*u**1.2)+side*(.055*math.sin(u*4.2+ph))+lean_all*u*u
        ctrl=[ob*.062+Z*-.18]+[sp(u) for u in (0.,.22,.45,.7,1.)]
        pts,P,T,S=_crv(ctrl,18);r0=rr.uniform(.0125,.0165)
        rad=[r0*(1.15 if p.z<0 else 1.)*max(.22,1-.78*min(1.,max(0.,p.z)/(Ls*.98)))**.9 for p in pts]
        _ttube(f'SH01_Stem{k}',pts,rad,BK,'Body',sides=7,scale=.25)
        ns=rr.choice((4,5,5,6));us=sorted(rr.uniform(.30,.90) for _ in range(ns));sph=rr.uniform(0,6.28)
        for j,u in enumerate(us):
            p=P(u);t=T(u);ax=Z.cross(t).normalized() if abs(t.z)<.95 else t.orthogonal().normalized()
            ang=sph+j*2.4+rr.uniform(-.4,.4);sd=(ax*math.cos(ang)+t.cross(ax)*math.sin(ang)).normalized()
            if sd.dot(out)<-.6:sd=(sd+out*1.2).normalized()   # no branch back into the middle of the shrub
            be=math.radians(rr.uniform(35,58));d=(t*math.cos(be)+sd*math.sin(be)).normalized()
            Lb=rr.uniform(.32,.58)*(1.2-.5*u);broken=(k==2 and j==0)
            if broken:Lb=.07
            rb=max(.0032,rad[min(len(rad)-1,int(u*(len(rad)-1)))]*.55)
            bc=[p-d*.004,p+d*Lb*.45+Z*Lb*.06+sd*Lb*.05,p+d*Lb+Z*Lb*.32] if not broken else [p-d*.004,p+d*Lb*.5,p+d*Lb]
            bp,BP,BT,BS=_crv(bc,8);br=[rb*max(.30,1-.70*i/(len(bp)-1)) for i in range(len(bp))]
            if broken:br=[rb*(1-.25*i/(len(bp)-1)) for i in range(len(bp))]
            nb+=1;_ttube(f'SH01_Br{k}{j}',bp,br,BK if rb>.004 else TW,'Body',sides=5,scale=.2)
            if broken:continue
            _spray(LV,BP,BT,.58,1.,rl.randint(4,6),.090,rl,phase=rl.uniform(0,6.28))
            nt=rr.choice((4,5,5,6));ut=sorted(rr.uniform(.22,.90) for _ in range(nt))
            for q,v in enumerate(ut):
                tp=BP(v);tt=BT(v);tax=Z.cross(tt).normalized() if abs(tt.z)<.95 else tt.orthogonal().normalized()
                ta=rr.uniform(0,6.28)+q*2.6;ts=(tax*math.cos(ta)+tt.cross(tax)*math.sin(ta)).normalized()
                td=(tt*math.cos(math.radians(45))+ts*math.sin(math.radians(45))+Z*.25).normalized();Lt=rr.uniform(.11,.24)
                tc=[tp-td*.003,tp+td*Lt*.5+Z*Lt*.06,tp+td*Lt+Z*Lt*.18];tpp,TP,TT,TS=_crv(tc,4)
                _ttube(f'SH01_Tw{k}{j}{q}',tpp,[.0024*max(.45,1-.55*i/(len(tpp)-1)) for i in range(len(tpp))],TW,'Body',sides=3,scale=.12)
                _spray(LV,TP,TT,.22,1.,rl.randint(7,9),.090,rl,phase=rl.uniform(0,6.28))
        _spray(LV,P,T,.78,1.,rl.randint(6,8),.088,rl,phase=rl.uniform(0,6.28),grow=(.9,1.05))   # the stem's own leading shoot
    LV.done('SH01_Leaves',LF,'Body')
    LT=_Leaves()   # Detail_Litter: fallen leaves lying round the stem base
    placed=[]
    while len(placed)<34:
        a=rr.uniform(0,6.28);d=.10+.38*rr.random()**.8;p=Vector((math.cos(a)*d,math.sin(a)*d*.8,.0012))
        if any((p-q).length<.11 for q in placed):continue   # no two fallen leaves on top of each other
        placed.append(p);b=rr.uniform(0,6.28);dd=Vector((math.cos(b),math.sin(b),0))
        up=Vector((rr.uniform(-.06,.06),rr.uniform(-.06,.06),1));Ln=rr.uniform(.045,.07);LT.add(p,dd,up,Ln,Ln*.42,droop=.0,cup=.0)
    LT.done('SH01_Litter',M['leaf_dry'],'Detail_Litter')
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P_=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P_[...,0],P_[...,1],P_[...,2];H=meta['height'];h=np.zeros(px.shape,np.float32)
        leaf=filled*(mid>.5);wood=filled*(mid<=.5)*(pz>-.5)
        lum=col.mean(2);lr=np.clip(lum/max(float(lum[leaf>0].mean()) if leaf.any() else .3,1e-3),.6,1.4)
        tc,occ=_sh_tone(px,py,pz,H);tc=tc*(.82+.18*lr[...,None])
        yl=leaf*(pz<.62*H)*np.clip((_fb(P_,(9.,9.,9.),8111,2)-.60)*5,0,1)   # a few older leaves low down turning yellow
        tc=tc*(1-yl[...,None])+yl[...,None]*np.array([.50,.46,.20])
        vein=leaf*np.clip(1-np.abs(_vn(P_,(60.,60.,60.),8112)-.5)/.06,0,1)*.08;tc=tc*(1+vein[...,None])
        col=col*(1-leaf[...,None])+leaf[...,None]*tc;rough=np.where(leaf>0,np.clip(.78+.08*(noise-.5),0,1),rough)
        moss=wood*np.clip((.32-pz)/.22,0,1)*np.clip((_fb(P_,(14.,14.,6.),8113,2)-.38)*3,0,1);col=col*(1-.75*moss[...,None])+moss[...,None]*.75*np.array([.20,.28,.11]);h+=.0008*moss
        lich=wood*(pz>.25)*np.clip((_fb(P_,(22.,22.,9.),8114,2)-.66)*6,0,1);col=col*(1-.45*lich[...,None])+lich[...,None]*.45*np.array([.56,.58,.50])
        dirt=wood*np.clip((.06-pz)/.10,0,1);col=col*(1-.35*dirt[...,None])+dirt[...,None]*.35*np.array([.18,.14,.10])
        R_['h']=h;return col,rough
    def vcol(co,isleaf,H):
        tc,occ=_sh_tone(co[:,0],co[:,1],co[:,2],H);bark=np.array([.40,.35,.29]);o2=np.clip(.55+.45*co[:,2]/H,0,1)
        rgb=np.where(isleaf[:,None],tc,bark[None,:]);a=np.where(isleaf,occ,o2);return np.column_stack([rgb,a])
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.15,'grime':.35,'ao_k':.35,'uv_angle':60,'ground0':True,
            'foliage':((4,1.6,.15),(12,2.5,.06)),'vcol':vcol,
            'origin_note':'stem base centre on the ground (z = 0); the stems run on 0.18 m under the ground; front = -Y (Blender) / -Z (FBX, Unity)',
            'notes':['seven thin stems from one point, each curving out at its own angle (a fan across the front, narrower from the side, the whole shrub leaning a little right and back); the stems run on 0.18 m under the ground',
                     f'{nb} side branches (three to five per stem, alternating round it), three or four twigs on each: three orders of thickness; one branch broken off short',
                     f'{_Leaves.n-34} five-vertex leaves (four outline points and a raised midrib), one by one along the twigs and the outer halves of the branches, alternate, the stalk on the twig, a young leaf at each tip; no leaf cards',
                     'leaf colour: up and out light and warm, down and in deep and cool, blended continuously, a few low leaves yellowing; in the albedo and in the vertex colour (A: canopy occlusion); UV2 "Wind": u wind weight (0 at the stem base, 1 at the leaf tips), v phase',
                     'LOD1: a quarter of the leaves, each 1.6 × larger, the wood decimated to 15 %; LOD2: a twelfth of the leaves, 2.5 × larger, wood 6 %',
                     'moss and soil at the stem feet, pale lichen higher up, painted; Detail_Litter (34 fallen leaves) is off at the standard tier; no collision (it is walked through)']}
PROPS['SH01']=SH01
