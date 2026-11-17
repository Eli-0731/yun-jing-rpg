# YP10 shapes (the 11/14 120h pack, batch A), read by build_yp.py after yp_items_e.py (same namespace).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _slab(name,c4,t,mat,grp,bev=.003,jit=.0010,seed=1,dn=0.):
    """a board cut to four corners (a flat quad, any trapezoid), thickness t about that plane (moved dn along its normal)"""
    P=[Vector(p) for p in c4];n=(P[1]-P[0]).cross(P[3]-P[0]).normalized();bm=bmesh.new()
    a=[bm.verts.new(p+n*(dn-t/2)) for p in P];b=[bm.verts.new(p+n*(dn+t/2)) for p in P]
    bm.faces.new(list(reversed(a)));bm.faces.new(b)
    for i in range(4):bm.faces.new((a[i],a[(i+1)%4],b[(i+1)%4],b[i]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);o=finish(name,bm,mat,grp)
    if bev:bevel(o,bev,1,angle=50)
    if jit:jitter(o,jit,seed,freq=11)
    return o
def _sack(pid,tag,M,size,seed,mat4,neck,ndir,nr=.060):
    """a full sack: a bulging body (flat underneath), the gathered neck standing out of it at `neck` towards `ndir`
    (both in the sack's own frame), the mouth cloth flaring in pleats above two turns of cord; mat4 places it."""
    o=_blob(f'{pid}_Sack{tag}',size,seed,M['burlap'],'Body',sub=3,flats=0,bottom=.30,bumps=7,amp=.06,scale=.25);o.data.transform(mat4)
    d=(mat4.to_3x3()@Vector(ndir)).normalized();c=mat4@Vector(neck);rot=Vector((0,0,1)).rotation_difference(d).to_matrix().to_4x4();rot.translation=c
    ph=seed*.7;NS=20
    t=_turned(f'{pid}_Neck{tag}',[(nr*.5,-.055,0),(nr,.0,0),(nr*.72,.030,.15),(nr*.56,.052,.25),(nr*.74,.072,.9),(nr*1.08,.100,1.6),(nr*1.02,.112,1.6),(nr*.5,.098,.6)],NS,M['burlap'],'Body',
              gfun=lambda k:.5+.5*math.sin(k*math.tau*5/NS+ph)+.25*math.sin(k*math.tau*2/NS+ph*2),scale=.25);t.data.transform(rot)
    for q in range(2):_ring(f'{pid}_Tie{tag}{q}',c+d*(.047+.009*q),d,nr*.56+.004,.0045,M['hemp'],'Body',n=11,wob=.002)
    s=d.orthogonal().normalized()
    for q in range(2):   # the two cord ends hanging from the knot
        a=c+d*.052+s*(nr*.56+.004)+d.cross(s)*(.012*(q*2-1));e=a+s*(.05+.02*q)+d*.01+Vector((0,0,-.045-.03*q))+d.cross(s)*(.035*(q*2-1))
        tube(f'{pid}_TieEnd{tag}{q}',[a,a.lerp(e,.45)+s*.016+d*.012,e],.0042,M['hemp'],'Body',sides=6,scale=.05)
    return o

# ---------------- YP10 wheelbarrow with two sacks (cand-4) ----------------
def YP10(M):
    """a solid plank wheel (iron tyre, an iron ring and rivets on each face, two battens a side, a turned hub) between the
    front ends of two long shafts that rise and thin into the handles; a tray of separate boards flaring upwards sits on
    the shafts; two splayed legs with braces and a cross bar; two full sacks, tied at the neck, pressed into the tray."""
    rr=random.Random(7001);W1,W2,DK,IR,HP=M['cedar_b'],M['cedar'],M['hardwood'],M['iron'],M['hemp']
    RW=.26;A=.231;LS=1.55;O=Vector((-.62,0,RW));U=Vector((math.cos(A),0,math.sin(A)));N=Vector((-math.sin(A),0,math.cos(A)));Y=Vector((0,1,0))
    T=lambda u,v,w:O+U*u+Y*v+N*w;ys=lambda u:.105+.17*u/LS
    # the wheel
    ph=.55;e=Vector((math.cos(ph),0,math.sin(ph)));p=Vector((-math.sin(ph),0,math.cos(ph)))
    _lathe('YP10_Wheel',[(0,.2475),(1,.2475)],(O-Y*.024,O+Y*.024),W2,'Body',NS=36,scale=.3)
    _lathe('YP10_Tyre',[(0,RW),(1,RW),(1,.2485),(0,.2485)],(O-Y*.029,O+Y*.029),IR,'Body',NS=36,scale=.2,loop=True)
    _lathe('YP10_Hub',[(0,.024),(.10,.040),(.30,.049),(.70,.049),(.90,.040),(1,.024)],(O-Y*.078,O+Y*.078),DK,'Body',NS=14,scale=.2)
    _rod('YP10_Axle',O-Y*.150,O+Y*.150,.015,DK,'Body',sides=10,scale=.15)
    for s in (-1,1):
        tg='LR'[s>0]
        _lathe(f'YP10_FaceRing{tg}',[(0,.2480),(1,.2480),(1,.215),(0,.215)],(O+Y*s*.0225,O+Y*s*.0282),IR,'Body',NS=36,scale=.2,loop=True)
        for k in range(12):
            a=math.tau*(k+.5*(s>0))/12;c=O+Vector((math.cos(a),0,math.sin(a)))*.2315+Y*s*.0275
            _lathe(f'YP10_Rivet{tg}{k:02d}',[(0,.0078),(.55,.0066),(1,0)],(c,c+Y*s*.006),IR,'Detail_Rivets',NS=6,scale=.05)
        for q,off in enumerate((-.10,.10)):
            hl=.184;c=O+e*off+Y*s*.030
            _bar(f'YP10_Batten{tg}{q}',c-p*hl,c+p*hl,.046,.016,W1,'Body',up=(0,1,0),bev=.003,seed=7010+q+3*s)
            for j in (-1,0,1):_nail(f'YP10_BattenNail{tg}{q}{j+1}',c+p*hl*.72*j+Y*s*.008,(0,s,0),IR,r=.0055,grp='Detail_Rivets')
        _rod(f'YP10_Linchpin{tg}',O+Y*s*.139+Vector((0,0,-.034)),O+Y*s*.139+Vector((0,0,.040)),.0055,IR,'Body',sides=6,scale=.05)
    # the two shafts, thinning and rounding into the handles
    dS={}
    for s in (-1,1):
        tg='LR'[s>0];f=lambda u,w=0.:T(u,s*ys(u),w);dS[s]=(f(LS)-f(0)).normalized()
        st=[(f(-.075),.050,.060,.008),(f(.2),.050,.060,.008),(f(1.10),.050,.060,.008),(f(1.22,-.003),.044,.046,.012),(f(1.33,-.006),.040,.040,.0116),(f(1.52,-.010),.039,.039,.0113),(f(1.55,-.011),.028,.028,.008)]
        _beam(f'YP10_Shaft{tg}',st,W1,'Body',up=N,seed=7020+s)
        for q in range(5):_ring(f'YP10_Grip{tg}{q}',f(1.37+.0105*q,-.007),dS[s],.0232,.0038,HP,'Body',n=10)
    # the tray: bottom planks on the shafts, the sides flaring upwards and outwards
    u0,u1,ua,ub=.26,.94,.14,1.03;hb,ht,wb,wh=.205,.290,.050,.200
    for k in range(4):
        v=-hb+.004+(2*hb-.008)*(k+.5)/4;th=.019+.003*(k%2)
        _bar(f'YP10_Bottom{k}',T(u0-.006*(k%2),v,.030+th/2),T(u1+.005*((k+1)%2),v,.030+th/2),(2*hb-.008)/4-.003,th,W2 if k%2 else W1,'Body',up=N,bev=.003,jit=.0012,seed=7030+k)
    uA=lambda q:u0+(ua-u0)*q;uB=lambda q:u1+(ub-u1)*q;hv=lambda q:hb+(ht-hb)*q;hw=lambda q:wb+wh*q
    for s in (-1,1):
        tg='LR'[s>0]
        for k,(q0,q1) in enumerate(((-.06,.50),(.515,1.0))):
            _slab(f'YP10_Side{tg}{k}',[T(uA(q0)-.012,s*hv(q0),hw(q0)),T(uB(q0)+.012,s*hv(q0),hw(q0)),T(uB(q1)+.012+.012*k,s*hv(q1),hw(q1)),T(uA(q1)-.012-.010*k,s*hv(q1),hw(q1))],.019+.002*k,W1 if k else W2,'Body',seed=7040+k+3*s,dn=.0015*k*s)
        n=(Y*s*wh-N*(ht-hb)).normalized()
        for k,uf in enumerate((.24,.76)):
            ux=lambda q:uA(q)+(uB(q)-uA(q))*uf
            a=T(ux(-.12),s*hv(-.12),hw(-.12))+n*.0165;b=T(ux(1.0),s*hv(1.0),hw(1.0))+n*.0165
            _bar(f'YP10_SideBatten{tg}{k}',a,b,.044,.016,W2,'Body',up=n,bev=.003,seed=7050+k+3*s)
            for j in (.2,.72):_nail(f'YP10_SideNail{tg}{k}{int(j*10)}',a.lerp(b,j)+n*.008,n,IR,r=.0055,grp='Detail_Rivets')
    for tg,uq,sg in (('Front',uA,-1),('Back',uB,1)):
        for k,(q0,q1) in enumerate(((-.04,.47),(.485,.99))):
            _slab(f'YP10_{tg}{k}',[T(uq(q0),-hv(q0)+.012,hw(q0)),T(uq(q0),hv(q0)-.012,hw(q0)),T(uq(q1),hv(q1)-.012,hw(q1)),T(uq(q1),-hv(q1)+.012,hw(q1))],.019+.002*(1-k),W2 if k else W1,'Body',seed=7060+k+3*sg,dn=.006*k*sg)
    # two splayed legs under the back of the tray, a brace to each shaft, a cross bar
    UL=.80;foot={}
    for s in (-1,1):
        tg='LR'[s>0];top=T(UL,s*ys(UL),.0);ft=Vector((top.x+.07,s*(ys(UL)+.085),-.004));foot[s]=(top,ft)
        o=_bar(f'YP10_Leg{tg}',ft,top+(top-ft).normalized()*.02,.050,.046,W1,'Body',up=(1,0,0),seed=7070+s);_flat_foot(o)
        a=ft.lerp(top,.42);b=T(.50,s*ys(.50),-.012)
        _bar(f'YP10_Brace{tg}',a,b,.032,.030,W2,'Body',up=(0,s,0),bev=.003,seed=7074+s)
        for q in range(3):_ring(f'YP10_LegTie{tg}{q}',T(UL+.036+.0105*q,s*ys(UL),0),dS[s],.0445,.0042,HP,'Body',n=12)
    a=foot[-1][1].lerp(foot[-1][0],.55);b=foot[1][1].lerp(foot[1][0],.55)
    _bar('YP10_LegCross',a+(a-b).normalized()*.04,b+(b-a).normalized()*.04,.036,.032,W2,'Body',up=(1,0,0),bev=.003,seed=7078)
    # two full sacks pressed into the tray, the back one leaning on the front one
    R0=Matrix((U,Y,N)).transposed().to_4x4()
    def place(u,v,w,tilt,turn):
        m=Matrix.Translation(T(u,v,w))@R0@Matrix.Rotation(turn,4,'Z')@Matrix.Rotation(tilt,4,'Y');return m
    _sack('YP10','A',M,(.47,.41,.38),7081,place(.45,-.012,wb-.012,-.10,.10),(.17,.01,.29),(.60,.06,.80))
    _sack('YP10','B',M,(.45,.40,.36),7082,place(.77,.016,wb+.012,-.34,-.20),(.165,-.01,.275),(.74,-.08,.67),nr=.056)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];h=np.zeros(px.shape,np.float32)
        sack=filled*(mid>.5);Q=P-np.array(O[:],np.float32);rw=np.hypot(Q[...,0],Q[...,2]);whl=filled*(rw<.268)*(np.abs(py)<.04)
        iron=whl*(rw>.213);wood=filled*(1-sack)*(1-iron)*(col[...,0]>col[...,2]*1.25)
        col,rough=_wood_age(col,rough,h,P,wood,0,7090,edge,grey=.40,stain=.22)
        disc=whl*(rw<.213)*(np.abs(onrm[...,1])>.8)*(np.abs(py)<.026);cp=Q[...,0]*float(p.x)+Q[...,2]*float(p.z)   # the wheel is three planks: two seams across each face
        seam=disc*np.clip(1-np.minimum(np.abs(cp-.080),np.abs(cp+.083))/.0035,0,1);h-=.0030*seam;col=col*(1-.65*seam[...,None])
        rust=iron*np.clip((_fb(P,22.,7091,3)-.42)*3,0,1);col=col*(1-.5*rust[...,None])+rust[...,None]*.5*np.array([.40,.20,.10]);rough=np.clip(rough+.1*rust,0,1);h+=iron*.0006*(_fb(P,60.,7092,2)-.5)
        run=wood*(rw<.25)*(rw>.17)*(np.abs(py)<.05)*np.clip((_fb(P,(40.,3.,40.),7093,2)-.45)*3,0,1);col=col*(1-.25*run[...,None])+run[...,None]*.25*np.array([.36,.20,.11])   # rust washed onto the wood beside the iron
        top=wood*np.clip(onrm[...,2],0,1)*np.clip((pz-.34)/.05,0,1)*np.clip(.4+noise,0,1);g=col.mean(2,keepdims=True);col=col*(1-.28*top[...,None])+top[...,None]*.28*(g*np.array([1.10,1.06,.98])+.04)   # rim tops sun-greyed
        grip=wood*np.clip((px-.62)/.12,0,1);col=col*(1+.14*grip[...,None]);rough=np.clip(rough-.18*grip,0,1)                                                 # the handles: polished by hands
        mud=filled*np.clip((.11-pz)/.10,0,1)*np.clip(.3+noise,0,1);col=col*(1-.55*mud[...,None])+mud[...,None]*.55*np.array([.30,.23,.16]);rough=np.clip(rough+.1*mud,0,1)
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,wood*(px>-.3),h=.14,amt=.5,soil=.03)
        # the sacks: dusty folds, a sewn patch on each, darker where they press together and into the tray
        fold=sack*np.clip((_fb(P,(9.,9.,26.),7094,3)-.5)*2.4,-1,1);h+=.0022*fold*np.abs(sack);col=col*(1+.10*fold[...,None])
        low=sack*np.clip((.42-pz)/.12,0,1);col=col*(1-.18*low[...,None])
        for (c,w_,d_,tint,sd) in ((T(.47,-.07,wb+.34),.13,.11,(.36,.40,.46),1),(T(.86,.08,wb+.36),.11,.12,(.50,.40,.30),2)):
            c=np.array(c[:],np.float32);ax_=np.array((math.cos(.3*sd),math.sin(.3*sd),0),np.float32);ay_=np.array((-ax_[1],ax_[0],0),np.float32)
            dx=np.abs((P-c)@ax_)/(w_/2);dy=np.abs((P-c)@ay_)/(d_/2);mx=np.maximum(dx,dy);ins=sack*(mx<1)*(np.abs(pz-c[2])<.09)*(onrm[...,2]>.25);rim=ins*(mx>.80)
            st=rim*(np.sin(((P-c)@ax_+(P-c)@ay_)*230)>0);col=col*(1-ins[...,None])+ins[...,None]*(np.array(tint)*(.80+.4*noise[...,None]));col=col*(1-.55*st[...,None]);h+=.0014*ins-.0012*st
        R_['h']=h;return col,rough
    M['burlap']['mid']=1.
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.9,'grime':.8,'ao_k':.5,'uv_angle':55,'collision_box':((1.30,.66,.62),(-.12,0,.31)),
            'collision':'one box over the wheel, tray and sacks; the handles are not solid',
            'notes':['a solid plank wheel: an iron tyre, an iron ring with twelve rivets on each face, two nailed battens a side, a turned hub on an axle with linchpins outside the shafts',
                     'two shafts run from the axle up to the handles (thinned, rounded, bound with cord); the tray is separate boards: four bottom planks, two boards each side and end, flaring upwards, two nailed battens on each side',
                     'two splayed legs with a brace to each shaft and a cross bar, lashed with cord; it stands on the wheel and the two legs',
                     'two full sacks tied at the neck with two turns of cord, the mouth cloth flaring in pleats; a sewn patch on each is painted, with its stitches in the normal map',
                     'Detail_Rivets (rivets and nail heads) is off at the standard tier; painted, with the relief also in the normal map: checks, the two seams of the three wheel planks, rust, mud low down']}
PROPS['YP10']=YP10

# ---------------- YP02 washing line with three faded cloths (cand-4) ----------------
def YP02(M):
    """two bamboo poles set in the ground, a bamboo cross pole lashed across their tops, a hemp rope tied between them
    and sagging; over the rope hang a pale jacket (body and two sleeves), a faded blue cloth and a striped towel.
    Each cloth is a piece with thickness folded over the rope: the folds deepen towards the hems, the hems are uneven."""
    rr=random.Random(7201);PX=1.05;ZR=1.60;SAG=.17;RR=.0075;ZB=1.86;BB,HP=M['bamboo_old'],M['hemp']
    zr=lambda x:ZR-SAG*(1-min(1.,abs(x)/(PX-.03))**2)
    for q,s in enumerate((-1,1)):
        _bcane(f'YP02_Pole{q}',(s*(PX+.012),.004*s,0),(s*PX,0,1.99),.033,.026,BB,'Body',gap=.30,sides=10,ph=.2+.5*q,bow=.012,bowdir=(s,.3,0))
        _xlash(f'YP02_Lash{q}',(s*PX,.026,ZB),(1,0,0),(0,0,1),.056,HP,'Body',cord=.0048)
        for j in range(3):_ring(f'YP02_LashTurn{q}{j}',(s*PX,.022,ZB-.05-.011*j),(0,.25,1),.050,.0048,HP,'Body',n=12)
        for j in range(3):_ring(f'YP02_RopeTurn{q}{j}',(s*PX,0,ZR-.010+.0145*j),(0,0,1),.0345,RR,HP,'Body',n=12)
        a=Vector((s*(PX+.02),-.034,ZR));tube(f'YP02_RopeEnd{q}',[a,a+Vector((s*.012,-.012,-.06)),a+Vector((s*.006,-.008,-.15)),a+Vector((s*.018,-.004,-.21))],RR*.9,HP,'Body',sides=6,scale=.08)
    _bcane('YP02_Bar',(-PX-.20,.054,ZB),(PX+.20,.054,ZB+.01),.027,.024,BB,'Body',gap=.34,sides=10,ph=.7,bow=.008)
    xs=np.linspace(-(PX-.022),PX-.022,41);tube('YP02_Rope',[(x,0,zr(x)) for x in xs],RR,HP,'Body',sides=6,scale=.08)
    def hem(L,seed,tears=2,amt=.042):
        r_=random.Random(seed);ph=[r_.uniform(0,6.28) for _ in range(2)];tc=[(r_.uniform(.2,.8),r_.uniform(.5,1.)*amt) for _ in range(tears)]
        return lambda u:L*(1+.035*math.sin(u*10+ph[0])+.02*math.sin(u*23+ph[1]))-sum(d*max(0.,1-abs(u-c)/.17)**1.5 for c,d in tc)
    def hang(name,x0,x1,front,back,mat,seed,rp=RR,**kw):
        zc=2.;o,hf,hb=_drape(name,x0,x1,zc,rp,front,back,mat,'Body',seed,**kw)
        for v in o.data.vertices:v.co.z+=zr(v.co.x)-zc
        return o
    L1,L2,L3=M['linen'],M['linen_blue'],M['linen_b'];jx=-.60
    hang('YP02_JacketBody',jx-.25,jx+.25,hem(.60,7210),hem(.58,7211,1),L1,7213,amp=.038,kx=17.,flare=-.02,side_drop=.03)
    for q,sg in enumerate((-1,1)):
        a,b=sorted((jx+sg*.246,jx+sg*.455));fl=(lambda u,sg=sg:.25+.07*(u if sg>0 else 1-u)+.012*math.sin(u*14+sg))
        hang(f'YP02_Sleeve{q}',a,b,fl,fl,L1,7214+q,rp=RR+.004,amp=.028,kx=21,side_drop=.015)
    hang('YP02_BlueCloth',-.03,.47,hem(.66,7220,3,.055),hem(.60,7221,2),L2,7222,amp=.055,kx=15.,flare=-.03,side_drop=.045)
    hang('YP02_Towel',.615,.865,hem(.40,7230,1,.04),hem(.34,7231,1,.04),L3,7232,amp=.026,kx=24.,side_drop=.01)
    for q,s in enumerate((-1,1)):   # Detail_: small stones wedged round each pole foot and a few grass tufts
        for k in range(4):
            a=math.tau*k/4+rr.uniform(-.4,.4);d=rr.uniform(.06,.10);sz=rr.uniform(.06,.11)
            _blob(f'YP02_Stone{q}{k}',(sz,sz*rr.uniform(.7,1),sz*rr.uniform(.45,.65)),7240+4*q+k,M['stone'],'Detail_Stones',sub=2,scale=.2).data.transform(Matrix.Translation((s*PX+math.cos(a)*d,math.sin(a)*d,-.004)))
        for k in range(5):
            a=math.tau*(k+.5)/5+rr.uniform(-.3,.3);d=rr.uniform(.10,.17);_tuft_even(f'YP02_Tuft{q}{k}',Vector((s*PX+math.cos(a)*d,math.sin(a)*d,-.004)),M['radish_leaf'],'Detail_Weeds',rr,n=4,h=rr.uniform(.07,.13))
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];h=np.zeros(px.shape,np.float32)
        cloth=filled*(mid>.5);zl=ZR-SAG*(1-np.clip(np.abs(px)/(PX-.03),0,1)**2);dz=zl-pz
        fade=cloth*np.clip((dz-.15)/.5,0,1);col=col*(1-.12*fade[...,None])                                            # dirtier towards the hems
        sun=cloth*np.clip((_fb(P,(3.,3.,2.),7250,2)-.45)*3,0,1);g=col.mean(2,keepdims=True);col=col*(1-.22*sun[...,None])+sun[...,None]*.22*(g*1.15+.05)   # washed-out, sun-bleached patches
        h+=cloth*.0010*(_fb(P,(40.,40.,14.),7251,2)-.5)                                                               # small creases
        jk=cloth*(np.abs(px-jx)<.25);band=jk*(py<0)*(np.abs(px-(jx-.015+.16*np.clip(dz,0,.6)))<.020)*(dz>.03)*(dz<.50);col=col*(1-.22*band[...,None]);h+=.0010*band   # the overlapping front edge of the jacket
        for k in range(4):   # cloth knot buttons down that edge
            bz=.10+.11*k;d=np.hypot(px-(jx-.015+.16*bz),dz-bz);bt=jk*(py<0)*np.clip(1-d/.011,0,1);col=col*(1-.5*bt[...,None]);h+=.0018*bt
        tw=cloth*(px>.60)*(px<.88);st=tw*np.clip(1-np.abs(((px-.615)/.25*5.5)%1-.5)/.16,0,1)*np.clip(.7+.6*(noise-.5),0,1);col=col*(1-.75*st[...,None])+st[...,None]*.75*np.array([.30,.38,.50])   # the blue stripes of the towel
        for (cx,cz,w_,h_,tint,front) in ((jx+.09,.46,.11,.10,(.52,.56,.62),1),(.30,.44,.13,.14,(.62,.58,.50),1),(.08,.40,.10,.09,(.30,.36,.46),0)):   # sewn patches
            dxp=np.abs(px-cx)/(w_/2);dzp=np.abs(dz-cz)/(h_/2);mx=np.maximum(dxp,dzp);ins=cloth*((py<0) if front else (py>0))*(mx<1);rim=ins*(mx>.84);st=rim*(np.sin((px+pz)*250)>0)
            col=col*(1-ins[...,None])+ins[...,None]*(np.array(tint)*(.85+.3*noise[...,None]));col=col*(1-.55*st[...,None]);h+=.0012*ins-.0010*st
        bam=filled*(1-cloth)*(col[...,0]>col[...,2]*1.2)
        ft=bam*np.clip((.45-pz)/.40,0,1)*np.clip((noise-.30)*2.5,0,1);col=col*(1-.45*ft[...,None])+ft[...,None]*.45*np.array([.20,.27,.10])   # the feet of the poles: green with damp
        gry=bam*np.clip((_fb(P,(5.,5.,2.),7252,2)-.5)*3,0,1);col=col*(1-.3*gry[...,None])+gry[...,None]*.3*np.array([.50,.47,.40]);rough=np.clip(rough+.08*gry,0,1)
        crk=bam*(pz>.5)*np.clip(1-np.abs(np.abs(px)-PX-.004*np.sin(pz*9))/.0022,0,1)*(py<0)*np.clip((_vn(P,(1.,1.,2.2),7253)-.45)*6,0,1);h-=.0020*crk;col=col*(1-.6*crk[...,None])   # drying cracks down the canes
        R_['h']=h;return col,rough
    for k in ('linen','linen_b','linen_blue'):M[k]['mid']=1.
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.7,'grime':.6,'ao_k':.4,'uv_angle':60,'collision_box':((.12,.12,1.95),(-PX,0,.975)),
            'collision':'the box is the left pole; give the right pole the same box at +1.05 m. The rope and the cloth are not solid',
            'notes':['two bamboo poles set in the ground, a bamboo cross pole lashed across their tops with a cross lashing and three turns; the three-view has this cross pole (the pack names two poles and a rope)',
                     'a hemp rope tied round each pole (three turns and a hanging end), sagging 17 cm in the middle',
                     'a pale jacket (body and two sleeves), a faded blue cloth, a striped towel: each a piece with thickness folded over the rope, folds deepening towards uneven, torn hems; no alpha cards',
                     'painted, with the relief also in the normal map: the jacket front edge and four knot buttons, three sewn patches, the towel stripes, sun-bleached patches, damp green pole feet, drying cracks',
                     'Detail_Stones (8 stones at the pole feet) and Detail_Weeds (10 grass tufts) are off at the standard tier']}
PROPS['YP02']=YP02
