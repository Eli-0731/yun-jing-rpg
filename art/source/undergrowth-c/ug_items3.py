# C 林下植物（undergrowth-c）: SH02 fine-leaved understory shrub and SP01 young broadleaf sapling. Same method and parts as SH01
# (ug_items.py: _crv, _ttube, _Leaves, _spray): stems → branches → twigs in three orders of thickness, five-vertex leaves one by one
# along the twigs, leaf LODs thinned instead of decimated (meta['foliage']), colour in the albedo, a grey shade + occlusion in COLOR_0.

def _tone_fn(pal,R,lift=.12):
    P_=np.array(pal,np.float32);n=len(P_)
    def tone(px,py,pz,H):
        r=np.hypot(px,py);ex=np.clip(.62*pz/H+.48*np.clip(r/R,0,1)-lift,0,1);t=np.clip(ex*(n-1),0,n-1-1e-3);lo=t.astype(np.int32);m=(t-lo)[...,None]
        return P_[lo]*(1-m)+P_[np.minimum(lo+1,n-1)]*m,.50+.50*ex
    return tone

def _woody_meta(tone,seed,yellow,notes,origin_note,foliage,bark=(.33,.29,.25)):
    """paint (leaf tone, a few yellowing leaves low down, faint veins, moss / lichen / soil on the wood) and vertex colour for SH02 / SP01"""
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P_=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P_[...,0],P_[...,1],P_[...,2];H=meta['height'];h=np.zeros(px.shape,np.float32)
        leaf=filled*(mid>.5);wood=filled*(mid<=.5)*(pz>-.5)
        lum=col.mean(2);lr=np.clip(lum/max(float(lum[leaf>0].mean()) if leaf.any() else .3,1e-3),.6,1.4)
        tc,occ=tone(px,py,pz,H);tc=tc*(.82+.18*lr[...,None])
        yl=leaf*(pz<.55*H)*np.clip((_fb(P_,(9.,9.,9.),seed+1,2)-.62)*5,0,1)
        tc=tc*(1-yl[...,None])+yl[...,None]*np.array(yellow)
        vein=leaf*np.clip(1-np.abs(_vn(P_,(60.,60.,60.),seed+2)-.5)/.06,0,1)*.08;tc=tc*(1+vein[...,None])
        col=col*(1-leaf[...,None])+leaf[...,None]*tc;rough=np.where(leaf>0,np.clip(.74+.08*(noise-.5),0,1),rough)
        wl=col.mean(2);wl=np.clip(wl/max(float(wl[wood>0].mean()) if wood.any() else .3,1e-3),.7,1.3)   # the wood toned to a dull grey-brown, keeping the bark detail
        bk=np.array(bark)*(.85+.15*wl[...,None]+.10*(_fb(P_,(5.,5.,30.),seed+5,2)[...,None]-.5));col=col*(1-wood[...,None]*.80)+wood[...,None]*.80*bk
        moss=wood*np.clip((.30-pz)/.22,0,1)*np.clip((_fb(P_,(14.,14.,6.),seed+3,2)-.38)*3,0,1);col=col*(1-.75*moss[...,None])+moss[...,None]*.75*np.array([.20,.28,.11]);h+=.0008*moss
        lich=wood*(pz>.30)*np.clip((_fb(P_,(22.,22.,9.),seed+4,2)-.66)*6,0,1);col=col*(1-.40*lich[...,None])+lich[...,None]*.40*np.array([.56,.58,.50])
        dirt=wood*np.clip((.06-pz)/.10,0,1);col=col*(1-.35*dirt[...,None])+dirt[...,None]*.35*np.array([.18,.14,.10])
        R_['h']=h;return col,rough
    def vcol(co,isleaf,H):   # glTF multiplies the base colour by COLOR_0: RGB a grey shade (0.78 low / inside … 1.0 up / outside), A occlusion
        tc,occ=tone(co[:,0],co[:,1],co[:,2],H);o2=np.clip(.55+.45*co[:,2]/H,0,1)
        g=np.where(isleaf,.78+.22*(occ-.5)/.5,.80+.20*o2);a=np.where(isleaf,occ,o2);return np.column_stack([g,g,g,a])
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.15,'grime':.35,'ao_k':.35,'uv_angle':60,'ground0':True,
            'foliage':foliage,'vcol':vcol,'origin_note':origin_note,'notes':notes}

def _litter(name,rr,n,r0,r1,M,size=(.045,.07),sq=.8,gap=.11):
    LT=_Leaves();placed=[];tries=0
    while len(placed)<n and tries<5000:
        tries+=1;a=rr.uniform(0,6.28);d=r0+(r1-r0)*rr.random()**.8;p=Vector((math.cos(a)*d,math.sin(a)*d*sq,.0012))
        if any((p-q).length<gap for q in placed):continue
        placed.append(p);b=rr.uniform(0,6.28);dd=Vector((math.cos(b),math.sin(b),0))
        up=Vector((rr.uniform(-.06,.06),rr.uniform(-.06,.06),1));Ln=rr.uniform(*size);LT.add(p,dd,up,Ln,Ln*.42,droop=.0,cup=.0)
    LT.done(name,M['leaf_dry'],'Detail_Litter');return len(placed)

def _twig(name,p,d,L,r,mat,lift=.18,sag=0.,sides=3,scale=.12):
    Z=Vector((0,0,1));tc=[p-d*.003,p+d*L*.5+Z*L*(lift*.35-sag*.4),p+d*L+Z*L*(lift-sag)];tp,TP,TT,TS=_crv(tc,4)
    _ttube(name,tp,[r*max(.45,1-.55*i/(len(tp)-1)) for i in range(len(tp))],mat,'Body',sides=sides,scale=scale);return TP,TT

def _side_dir(t,ang,be,out=None,Z=Vector((0,0,1)),lift=0.):
    ax=Z.cross(t).normalized() if abs(t.z)<.95 else t.orthogonal().normalized()
    sd=(ax*math.cos(ang)+t.cross(ax)*math.sin(ang)).normalized()
    if out is not None and sd.dot(out)<-.6:sd=(sd+out*1.2).normalized()
    return (t*math.cos(be)+sd*math.sin(be)+Z*lift).normalized(),sd

# ---------------- SH02 fine-leaved, sparser understory shrub ----------------
SH02_PAL=[(.170,.265,.150),(.235,.345,.180),(.315,.430,.205),(.420,.520,.240),(.560,.620,.300)]
def SH02(M):
    """about nine very thin wiry stems from one point, fanning out; on each, side branches alternating round it and many fine
    twigs that spread sideways in thin layers; very small narrow leaves one by one along the twigs, sparse, so the twigs and the
    background show through. The stems run on 0.18 m under the ground."""
    rr=random.Random(int(__import__('os').environ.get('UG_SEED',8201)));rl=random.Random(int(__import__('os').environ.get('UG_LSEED',8259)))
    Z=Vector((0,0,1));LV=_Leaves();n0=_Leaves.n
    BK,TW,LF=M['bark'],M['twig'],M['herb'];M['herb']['mid']=1.
    lean_all=Vector((.10,.05,0))
    stems=[(az,ln,L*.86) for az,ln,L in ((-172,40,1.00),(-140,28,1.18),(-108,10,1.42),(-80,6,1.46),(-50,20,1.24),(-16,32,1.12),(24,42,.98),(118,12,1.36),(160,26,1.16))]
    nb=nt_=0;LS=.037   # 2026-11-25: .031 → .037 and a leaf or two more per twig: at 12 m in Unity the bush had nearly vanished
    for k,(az,lean,Ls) in enumerate(stems):
        a=math.radians(az+rr.uniform(-8,8));out=Vector((math.cos(a),math.sin(a)*.6,0)).normalized();ln=math.radians(lean+rr.uniform(-4,4));ph=rr.uniform(0,6.28)
        side=Z.cross(out).normalized();ob=Vector((math.cos(a),math.sin(a),0))
        def sp(u,out=out,ob=ob,ln=ln,ph=ph,side=side,Ls=Ls):
            return ob*.045+Z*(Ls*math.cos(ln)*u)+out*(Ls*math.sin(ln)*u**1.3+.05*math.sin(u*3.1))+side*(.06*math.sin(u*4.6+ph))+lean_all*u*u
        ctrl=[ob*.045+Z*-.18]+[sp(u) for u in (0.,.25,.5,.75,1.)]
        pts,P,T,S=_crv(ctrl,16);r0=rr.uniform(.0058,.0078)
        rad=[r0*(1.15 if p.z<0 else 1.)*max(.25,1-.75*min(1.,max(0.,p.z)/(Ls*.98)))**.9 for p in pts]
        _ttube(f'SH02_Stem{k}',pts,rad,BK,'Body',sides=5,scale=.22)
        ns=rr.choice((5,6,6,7));us=sorted(rr.uniform(.24,.90) for _ in range(ns));sph=rr.uniform(0,6.28)
        for j,u in enumerate(us):
            p=P(u);t=T(u);d,sd=_side_dir(t,sph+j*2.4+rr.uniform(-.4,.4),math.radians(rr.uniform(50,72)),out)
            d=(d-Z*d.dot(Z)*.45).normalized()   # the branches spread sideways rather than up: thin layers
            Lb=rr.uniform(.22,.40)*(1.15-.45*u);rb=max(.0022,rad[min(len(rad)-1,int(u*(len(rad)-1)))]*.55)
            bc=[p-d*.003,p+d*Lb*.5+Z*Lb*.05,p+d*Lb+Z*Lb*.10];bp,BP,BT,BS=_crv(bc,7)
            nb+=1;_ttube(f'SH02_Br{k}{j}',bp,[rb*max(.32,1-.68*i/(len(bp)-1)) for i in range(len(bp))],TW,'Body',sides=4,scale=.16)
            _spray(LV,BP,BT,.55,1.,rl.randint(4,6),LS,rl,phase=rl.uniform(0,6.28),lift=.30)
            nt=rr.choice((3,4,4,5));ut=sorted(rr.uniform(.18,.92) for _ in range(nt))
            for q,v in enumerate(ut):
                tp=BP(v);tt=BT(v);td,_=_side_dir(tt,rr.uniform(0,6.28)+q*2.6,math.radians(rr.uniform(40,62)),lift=.05)
                td=(td-Z*td.dot(Z)*.5).normalized();Lt=rr.uniform(.10,.22)
                TP,TT=_twig(f'SH02_Tw{k}{j}{q}',tp,td,Lt,.0015,TW,lift=.10,sag=.06);nt_+=1
                _spray(LV,TP,TT,.12,1.,rl.randint(8,11),LS,rl,phase=rl.uniform(0,6.28),lift=.30)
        _spray(LV,P,T,.80,1.,rl.randint(8,11),LS*1.05,rl,phase=rl.uniform(0,6.28),grow=(.9,1.05),lift=.30)
    LV.done('SH02_Leaves',LF,'Body');nl=_Leaves.n-n0
    nlit=_litter('SH02_Litter',rr,26,.08,.42,M,size=(.025,.045),gap=.08)
    tone=_tone_fn(SH02_PAL,.75)
    return _woody_meta(tone,8211,(.48,.45,.20),
      ['about nine very thin wiry stems from one point, fanning out (wider from the front than from the side, leaning a little to the right); the stems run on 0.18 m under the ground',
       f'{nb} side branches (four to six per stem, alternating round it) spreading sideways in thin layers, {nt_} fine twigs: three orders of thickness',
       f'{nl} small five-vertex leaves (3–4.3 cm), one by one along the twigs, alternate, sparse so the twigs show; a young leaf at each tip; no leaf cards',
       'leaf colour in the albedo: up and out lighter, down and in deeper and cooler, a few low leaves yellowing; COLOR_0 RGB a grey shade (0.78–1), A canopy occlusion; UV2 "Wind": u wind weight, v phase',
       'LOD1: a quarter of the leaves, each 2.2 × larger, the wood decimated to 12 %; LOD2: a twelfth of the leaves, 3.6 × larger, wood 11 % (less would flatten the thin stems into fins)',
       f'moss and soil at the stem feet, pale lichen higher up, painted; Detail_Litter ({nlit} fallen leaves) is off at the standard tier; no collision (it is walked through)'],
      'stem base centre on the ground (z = 0); the stems run on 0.18 m under the ground; front = -Y (Blender) / -Z (FBX, Unity)',
      ((4,2.2,.12),(12,3.6,.11)),bark=(.30,.27,.24))   # LOD1 / LOD2: fewer but larger leaves, leaf area ≥ LOD0 (2.2²/4, 3.6²/12) so the far bush keeps its mass
PROPS['SH02']=SH02

# ---------------- SP01 young broadleaf sapling ----------------
SP01_PAL=[(.185,.280,.150),(.255,.365,.180),(.340,.450,.205),(.450,.540,.240),(.590,.640,.300)]
def SP01(M):
    """one slender trunk, a little leaning and curving to the light, the lower 1.2 m bare but for two short dead twigs; above it
    main branches in loose irregular tiers, out and up at different angles, each with twigs; leaves one by one along the twigs in
    flat sprays; a leader shoot with young leaves at the top. The trunk runs on 0.3 m under the ground (樹木重做 v2: roots 0.3 m)."""
    rr=random.Random(int(__import__('os').environ.get('UG_SEED',8401)));rl=random.Random(int(__import__('os').environ.get('UG_LSEED',8459)))
    Z=Vector((0,0,1));LV=_Leaves();n0=_Leaves.n
    BK,TW,LF=M['bark'],M['twig'],M['herb'];M['herb']['mid']=1.
    Ht=2.95;lean=Vector((.16,.10,0))
    def tr(u):return Z*(Ht*u)+lean*(u**1.6)+Vector((.035*math.sin(u*5.0+.6),.025*math.sin(u*3.7+1.9),0))*u
    ctrl=[Z*-.30]+[tr(u) for u in (0.,.15,.35,.55,.75,.90,1.)]
    pts,P,T,S=_crv(ctrl,34);r0=.024
    rad=[r0*(1.25 if p.z<0 else 1.+.45*max(0.,1-p.z/.12))*max(.10,1-.90*min(1.,max(0.,p.z)/Ht))**.85 for p in pts]
    _ttube('SP01_Trunk',pts,rad,BK,'Body',sides=8,scale=.30)
    def rad_at(u):return rad[min(len(rad)-1,int((u*Ht+.30)/(Ht+.30)*(len(rad)-1)))]
    # two short dead twigs on the bare lower trunk
    for q,(u,az) in enumerate(((.18,-60),(.30,140))):
        p=P(u);t=T(u);a=math.radians(az);d=(Vector((math.cos(a),math.sin(a),0))*.9+Z*.35).normalized();Ld=rr.uniform(.08,.13)
        _twig(f'SP01_Dead{q}',p,d,Ld,max(.003,rad_at(u)*.30),BK,lift=.05,sides=4,scale=.12)
    # main branches in loose tiers (azimuth °, height on the trunk, length, rise)
    mb=[(-160,.42,.92,.16),(-25,.45,.86,.20),(85,.50,.78,.22),(-95,.56,.74,.26),(150,.60,.70,.28),(30,.65,.62,.30),(-140,.70,.56,.34),(110,.75,.50,.36),(-40,.80,.42,.42),(170,.85,.34,.48)]
    nb=nt_=0;LS=.080
    for j,(az,u,Lb,rise) in enumerate(mb):
        p=P(u);a=math.radians(az+rr.uniform(-10,10));out=Vector((math.cos(a),math.sin(a)*.8,0)).normalized()
        d=(out+Z*rise*1.4).normalized();rb=max(.0045,rad_at(u)*.48);Lb*=rr.uniform(.92,1.10)
        bc=[p-d*.004,p+d*Lb*.45+Z*Lb*.04,p+d*Lb+Z*Lb*(rise*.25+.05)];bp,BP,BT,BS=_crv(bc,9)
        nb+=1;_ttube(f'SP01_Br{j}',bp,[rb*max(.28,1-.72*i/(len(bp)-1)) for i in range(len(bp))],BK if rb>.006 else TW,'Body',sides=5,scale=.2)
        _spray(LV,BP,BT,.32,1.,rl.randint(9,11),LS,rl,phase=rl.uniform(0,6.28),lift=.25,wid=(.52,.64))
        nt=rr.choice((7,8,9));ut=sorted(rr.uniform(.15,.92) for _ in range(nt))
        for q,v in enumerate(ut):
            tp=BP(v);tt=BT(v);td,_=_side_dir(tt,rr.uniform(0,6.28)+q*2.6,math.radians(rr.uniform(38,58)),out,lift=.10)
            td=(td-Z*td.dot(Z)*.4).normalized();Lt=rr.uniform(.18,.32)*(1.1-.4*v)
            TP,TT=_twig(f'SP01_Tw{j}{q}',tp,td,Lt,.0026,TW,lift=.16,sag=.04,sides=3,scale=.12);nt_+=1
            _spray(LV,TP,TT,.10,1.,rl.randint(10,13),LS,rl,phase=rl.uniform(0,6.28),lift=.25,wid=(.52,.64))
    # leader: the trunk's own top with young lighter leaves, and short twigs near it
    _spray(LV,P,T,.88,1.,rl.randint(8,10),LS*.85,rl,phase=rl.uniform(0,6.28),grow=(.8,.95),lift=.35,wid=(.50,.60))
    for q in range(3):
        u=.88+.035*q;p=P(u);td,_=_side_dir(T(u),q*2.4+rr.uniform(-.3,.3),math.radians(48),lift=.15);Lt=rr.uniform(.12,.18)
        TP,TT=_twig(f'SP01_Top{q}',p,td,Lt,.0022,TW,lift=.20,sides=3,scale=.12);nt_+=1
        _spray(LV,TP,TT,.2,1.,rl.randint(5,7),LS*.85,rl,phase=rl.uniform(0,6.28),lift=.30,wid=(.50,.60))
    LV.done('SP01_Leaves',LF,'Body');nl=_Leaves.n-n0
    nlit=_litter('SP01_Litter',rr,30,.10,.55,M,size=(.05,.08),gap=.12)
    tone=_tone_fn(SP01_PAL,.85,lift=.20)
    return _woody_meta(tone,8411,(.50,.46,.20),
      ['one slender trunk about 4 cm across at the foot, flaring a little at the ground, leaning and curving a little to the light; the lower 1.2 m bare but for two short dead twigs; the trunk runs on 0.3 m under the ground',
       f'five main branches in loose irregular tiers and {nb-5} shorter side shoots higher up the leader, out and up at different angles, {nt_} twigs: three orders of thickness',
       f'{nl} five-vertex leaves (7–10 cm), one by one along the twigs and the outer halves of the branches, alternate, in flat sprays; a leader shoot with young leaves at the top; no leaf cards',
       'leaf colour in the albedo: up and out lighter and warmer, down and in deeper and cooler, a few low leaves yellowing; COLOR_0 RGB a grey shade (0.78–1), A canopy occlusion; UV2 "Wind": u wind weight, v phase',
       'LOD1: a quarter of the leaves, each 1.6 × larger, the wood decimated to 15 %; LOD2: a twelfth of the leaves, 2.5 × larger, wood 6 %',
       f'moss and soil at the trunk foot, pale lichen higher up, painted; Detail_Litter ({nlit} fallen leaves) is off at the standard tier; no collision (it is walked through)'],
      'trunk base centre on the ground (z = 0); the trunk runs on 0.3 m under the ground; front = -Y (Blender) / -Z (FBX, Unity)',
      ((4,1.6,.15),(12,2.5,.06)),bark=(.36,.33,.29))
PROPS['SP01']=SP01
