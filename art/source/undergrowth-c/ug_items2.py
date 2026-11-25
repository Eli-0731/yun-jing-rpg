# C 林下植物（undergrowth-c）: UG01–UG06 (after ug_items.py: _crv, _ttube, _Leaves). Blender: X = width, -Y = front, Z = up.
# Leaves are meshes cut to each leaf's own outline (ug_shapes.py) with the leaf's veins and edge in its own source texture
# (ug_sources.py, mapped with keep_uv), one by one, no leaf cards. Work pack: each item ≤ 4,000 triangles.
exec(open(HERE/'ug_shapes.py',encoding='utf-8').read())

class _LS:
    """a set of leaves in one part: 'Tiled' UV written here (keep_uv), face int 'leaf' = leaf number, vertex float 'lbase' = 1 at the stalk"""
    def __init__(s):
        s.bm=bmesh.new();s.uv=s.bm.loops.layers.uv.new('Tiled');s.la=s.bm.faces.layers.int.new('leaf');s.lb=s.bm.verts.layers.float.new('lbase');s.n=0
    @staticmethod
    def frame(d,up):
        d=Vector(d).normalized();side=d.cross(Vector(up)).normalized();return d,side,side.cross(d).normalized()
    @staticmethod
    def bendpt(x,y,z,L,bend):
        """leaf-space point (x along, y across, z off the blade, in leaf lengths) on a blade bent along its length: bend = total turn
        in radians (negative: the tip droops)"""
        if abs(bend)<1e-4:return x*L,y*L,z*L
        k=bend/L;s_=x*L;th=k*s_;a=math.sin(th)/k;u=(1-math.cos(th))/k
        return a-math.sin(th)*z*L,y*L,u+math.cos(th)*z*L
    def _face(s,vs,uvs):
        f=s.bm.faces.new(vs);f[s.la]=s.n;f.smooth=True
        for l,uv in zip(f.loops,uvs):l[s.uv].uv=uv
    def poly(s,P,C,base,d,up,L,ws=1.,bend=0.,fold=0.,wave=0.,freq=6.,ph=0.,rings=(.62,.28),npts=28,lift=None,curl=0.):
        """one leaf cut to outline P (resampled to npts by arc length), rings shrunk towards C, a centre vertex.
        fold: the halves rise to a V (cupped); wave: the edge rises and falls; curl: the edge rolls up (dead leaves)"""
        s.n+=1;D,S_,U=s.frame(d,up);b=Vector(base)
        seg=np.r_[0,np.cumsum(np.hypot(*np.diff(np.vstack([P,P[:1]]),axis=0).T))];t=np.linspace(0,seg[-1],npts,endpoint=False)
        Q=np.column_stack([np.interp(t,seg,np.r_[P[:,0],P[0,0]]),np.interp(t,seg,np.r_[P[:,1],P[0,1]])])
        X0,HW=shape_box(P);C=np.array(C,float)
        def V(x,y):
            ny=abs(y)/HW
            z=fold*abs(y)+wave*math.sin(freq*x+ph)*ny**2+curl*ny**3*HW
            if lift:z+=lift(x,y)
            a,yy,zz=s.bendpt(x,y*ws,z,L,bend);v=s.bm.verts.new(b+D*a+S_*yy+U*zz)
            return v,(y/(2*HW)+.5,(x-X0)/(1-X0))
        R_=[[V(*q) for q in Q]]
        for r in rings:R_.append([V(*(C+(q-C)*r)) for q in Q])
        cv=V(*C);ib=int(np.argmin(np.hypot(Q[:,0],Q[:,1])));R_[0][ib][0][s.lb]=1.
        for A_,B_ in zip(R_,R_[1:]):
            for i in range(npts):
                j=(i+1)%npts;s._face([A_[i][0],A_[j][0],B_[j][0],B_[i][0]],[A_[i][1],A_[j][1],B_[j][1],B_[i][1]])
        for i in range(npts):
            j=(i+1)%npts;s._face([R_[-1][i][0],R_[-1][j][0],cv[0]],[R_[-1][i][1],R_[-1][j][1],cv[1]])
    def strap(s,base,d,up,L,HW,nu=14,bend=-1.,fold=.06,wave=0.,freq=9.,ph=0.,taper=.18):
        """a long strap leaf: rows along the midrib, five columns (edge, half, midrib, half, edge)"""
        s.n+=1;D,S_,U=s.frame(d,up);b=Vector(base);rows=[]
        for i in range(nu+1):
            x=i/nu;w=HW*max(.05,(min(1,x/taper)**.6)*(1-x**3)**.8) if x<1 else 0.
            if i==nu:   # the tip: one vertex
                a,yy,zz=s.bendpt(1.,0.,0.,L,bend);v=s.bm.verts.new(b+D*a+S_*yy+U*zz);rows.append([(v,(.5,1.))]);continue
            row=[]
            for j in (-2,-1,0,1,2):
                y=w*j/2;z=fold*abs(y)/HW*HW+wave*HW*math.sin(freq*x*math.pi+ph+j*.4)*(abs(j)/2)**1.5
                a,yy,zz=s.bendpt(x,y/L,z/L,L,bend);v=s.bm.verts.new(b+D*a+S_*yy+U*zz)
                if i==0 and j==0:v[s.lb]=1.
                row.append((v,(.5+.5*j/2*(w/HW),x)))
            rows.append(row)
        for A_,B_ in zip(rows,rows[1:]):
            for j in range(4):
                if len(B_)==1:s._face([A_[j][0],A_[j+1][0],B_[0][0]],[A_[j][1],A_[j+1][1],B_[0][1]])
                else:s._face([A_[j][0],A_[j+1][0],B_[j+1][0],B_[j][0]],[A_[j][1],A_[j+1][1],B_[j+1][1],B_[j][1]])
    def five(s,base,d,up,L,W,droop=.15,cup=.10):
        """a five-vertex pinna (outline of four points and a raised midrib), UV over the whole square"""
        s.n+=1;D,S_,U=s.frame(d,up);b=Vector(base)+D*.002
        t=b+D*L-U*droop*L;r_=b+D*L*.40-S_*W*.5+U*cup*W;l_=b+D*L*.40+S_*W*.5+U*cup*W;m=b+D*L*.46+U*W*.10
        vs=[s.bm.verts.new(p) for p in (b,r_,t,l_,m)];vs[0][s.lb]=1.
        uv=[(.5,0.),(0.,.40),(.5,1.),(1.,.40),(.5,.46)]
        for i in range(4):s._face([vs[4],vs[i],vs[(i+1)%4]],[uv[4],uv[i],uv[(i+1)%4]])
    def done(s,name,mat,grp):return finish(name,s.bm,mat,grp,keep_uv=True)

def _lump(name,c,r,h,mat,grp,seg=10,ring=4,below=.08,rr=None):
    """a low rounded crown / mound: a squashed half-ball (top at h above c, bottom 'below' under it), lumpy"""
    bm=bmesh.new();rr=rr or random.Random(1);rows=[]
    for i in range(ring+1):
        t=i/ring;row=[]
        for k in range(seg):
            a=math.tau*k/seg;j=1+rr.uniform(-.12,.12)
            rad=r*math.sin(math.pi/2*(1-t))*j if i<ring else 0.;z=h*math.cos(math.pi/2*(1-t)) if t>0 else -below
            row.append(bm.verts.new(Vector(c)+Vector((math.cos(a)*rad,math.sin(a)*rad,z))))
            if i==ring:break
        rows.append(row)
    bot=[bm.verts.new(Vector(c)+Vector((math.cos(math.tau*k/seg)*r*.55,math.sin(math.tau*k/seg)*r*.55,-below))) for k in range(seg)]
    for A_,B_ in zip(rows,rows[1:]):
        for k in range(seg):
            if len(B_)==1:bm.faces.new((A_[k],A_[(k+1)%seg],B_[0]))
            else:bm.faces.new((A_[k],A_[(k+1)%seg],B_[(k+1)%seg],B_[k]))
    for k in range(seg):bm.faces.new((bot[(k+1)%seg],bot[k],rows[0][k],rows[0][(k+1)%seg]))
    bm.faces.new(list(reversed(bot)))
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,.12)

def _plant_meta(pal,R,notes,extra=None,dark=(.30,.26,.20),gz=0.):
    """the meta every UG plant shares: origin at the crown on the ground, plain decimation for LOD1/2 (each item ≤ 4,000 at LOD0),
    vertex colour (height tone, A occlusion) and the wind UV"""
    P_=np.array(pal,np.float32)
    def tone(px,py,pz,H):
        r=np.hypot(px,py);ex=np.clip(.65*pz/max(H,.05)+.45*np.clip(r/R,0,1)-.10,0,1);t=np.clip(ex*(len(P_)-1),0,len(P_)-1-1e-3);lo=t.astype(np.int32);m=(t-lo)[...,None]
        return P_[lo]*(1-m)+P_[np.minimum(lo+1,len(P_)-1)]*m,.55+.45*ex
    def vcol(co,isleaf,H):   # glTF multiplies the base colour by COLOR_0: RGB is a grey shade (0.78 low / inside … 1.0 up / outside), A occlusion
        tc,occ=tone(co[:,0],co[:,1],co[:,2],H);g=.78+.22*(occ-.55)/.45;return np.column_stack([g,g,g,occ])
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        # gz: the ground under the item (UG06 vines: 2 root radii under the origin; before 2026-11-25 the vine leaves on the sides of
        # the root, below z = 0, were painted with the ground dirt and went near black)
        P_=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);pz=P_[...,2]-gz;H=meta['height']
        sh=np.clip(.80+.30*pz/max(H,.05),.80,1.08)*filled+(1-filled);col=col*sh[...,None]          # a little darker low down and inside
        dirt=filled*np.clip((.03-pz)/.06,0,1);col=col*(1-.45*dirt[...,None])+dirt[...,None]*.45*np.array(dark)
        if extra:meta['_onrm']=onrm;col,rough=extra(col,rough,P_,noise,filled,meta);meta.pop('_onrm',None)
        return col,rough
    return {'paint':paint,'wear':0.,'grime':.2,'ao_k':.30,'uv_angle':60,'ground0':True,'vcol':vcol,
            'origin_note':'crown centre on the ground (z = 0); the crown runs on a few cm under the ground; front = -Y (Blender) / -Z (FBX, Unity)','notes':notes}

# ---------------- UG01 waist-high sword fern clump (cand-1) ----------------
def UG01(M):
    """about eleven once-pinnate fronds fountaining up and out from one hairy crown, the tips bending over; two fiddleheads in the
    middle; three old brown fronds lying on the ground. Pinnae are five-vertex blades, one by one in pairs along each stalk."""
    rr=random.Random(8301);Z=Vector((0,0,1));LS=_LS();DS=_LS()
    _lump('UG01_Crown',(0,0,0),.075,.06,M['ug_scale'],'Body',seg=9,ring=3,below=.09,rr=rr)
    fr=[]   # (azimuth °, elevation °, length m): the front view is a fountain, the side a little narrower and leaning right/back
    for k,az in enumerate((-158,-122,-88,-55,-22,10,44,82,120,158)):
        fr.append((az+rr.uniform(-9,9),rr.uniform(63,72) if k%2 else rr.uniform(74,84),rr.uniform(1.15,1.35)))
    nb=0
    for k,(az,el,Lf) in enumerate(fr):
        a=math.radians(az);o=Vector((math.cos(a),math.sin(a)*.75,0)).normalized();e=math.radians(el)
        ctrl=[o*.02+Z*-.02];p=o*.03+Z*.03;th=e
        B=math.radians(rr.uniform(78,96))
        for i in range(6):   # the stalk rises and arches over evenly, the tip turning down
            p=p+(o*math.cos(th)+Z*math.sin(th))*Lf/6;ctrl.append(p.copy());th-=B/6*(.55+.18*i)
        ctrl=[c+Vector((.03,.04,0))*(i/6)**2 for i,c in enumerate(ctrl)]   # the whole clump leans a little right and back
        pts,P,T,S=_crv(ctrl,11);rad=[.0065*(1-.75*i/(len(pts)-1))+.0012 for i in range(len(pts))]
        _ttube(f'UG01_Stalk{k}',pts,rad,M['ug_rachis'],'Body',sides=3,scale=.2)
        roll=math.radians(rr.uniform(-22,22));npair=26;Lmax=.13*Lf
        for i in range(npair):
            u=.12+.87*(i+.5)/npair;w=(u-.13)/.85;Lp=Lmax*(max(w,.02)**.35*(1-w)**.6)/.45*(1.04 if i%2 else .98)
            if Lp<.008:continue
            q=P(u);t=T(u);lat=t.cross(Z);lat=lat.normalized() if lat.length>1e-3 else Vector((1,0,0))
            lat=Matrix.Rotation(roll,3,t)@lat;n=lat.cross(t).normalized()
            if n.z<0:n=-n
            for sd in (1,-1):
                qq=q+t*(.006 if sd>0 else -.006)
                d=(lat*sd*math.cos(math.radians(64))+t*math.sin(math.radians(64))-n*.10).normalized()
                LS.five(qq,d,n,Lp,Lp*.25,droop=rr.uniform(.06,.16),cup=.12);nb+=1
    for k,(az,h) in enumerate(((-40,.30),(25,.24))):   # two fiddleheads: a stalk, then a tight coil turned forward
        a=math.radians(az);o=Vector((math.cos(a),math.sin(a),0));base=o*.015
        top=base+Z*h+o*.03;ax=Z.cross(o).normalized();coil=[base+Z*-.02,base+Z*h*.5+o*.01,top]
        c0=top+o*.022;r0=.024
        for j in range(1,15):
            ph=j/14*math.tau*1.35;r_=r0*(1-.70*j/14);coil.append(c0+(-o*math.cos(ph)+Z*math.sin(ph))*r_)
        pts,P,T,S=_crv(coil,22);_ttube(f'UG01_Fiddle{k}',pts,[.0055*(1-.6*i/(len(pts)-1)) for i in range(len(pts))],M['ug_rachis'],'Body',sides=4,scale=.1)
    for k,az in enumerate((-115,30,150)):   # old fronds lying on the ground round the crown: short, dull grey-brown, the pinnae
        # wide and overlapping so the frond reads as one flat withered blade, not a row of separate orange dashes
        a=math.radians(az+rr.uniform(-10,10));o=Vector((math.cos(a),math.sin(a),0));L_=rr.uniform(.36,.44)
        ctrl=[o*.03+Z*.02,o*(L_*.45)+Z*.022,o*L_+Vector((-o.y,o.x,0))*.05+Z*.010];pts,P,T,S=_crv(ctrl,6)
        _ttube(f'UG01_Dead{k}',pts,[.0035*(1-.6*i/(len(pts)-1)) for i in range(len(pts))],M['ug_rachis'],'Body',sides=3,scale=.2)
        for i in range(12):
            u=.10+.86*(i+.5)/12;w=(u-.10)/.86;Lp=.085*(max(w,.02)**.35*(1-w)**.70)/.40
            if Lp<.014:continue
            q=P(u);t=T(u);lat=t.cross(Z).normalized()
            for sd in (1,-1):
                d=(lat*sd*.75+t*.45-Z*.16).normalized();DS.five(q,d,Z+lat*sd*.25,Lp,Lp*.46,droop=.14,cup=.30)
    LS.done('UG01_Pinnae',M['ug_pinna'],'Body');DS.done('UG01_DeadPinnae',M['ug_pinna_dead'],'Body')
    meta=_plant_meta([(.10,.20,.16),(.15,.27,.20),(.21,.35,.25),(.28,.42,.29)],.7,
      ['about eleven once-pinnate fronds fountaining up and out from one hairy crown, the tips bending over, the clump leaning a little right and back',
       f'{nb} five-vertex pinnae in pairs along the stalks, longest a third of the way up, shortening to the tip; the pinna texture carries the midrib and the toothed edge',
       'two fiddleheads (a stalk ending in a tight coil) in the middle; three short old fronds lying flat on the ground, dull withered grey-brown, the pinnae wide and overlapping',
       'LOD1 / LOD2: decimated (each item is ≤ 4,000 triangles at LOD0)'])
    return meta
PROPS['UG01']=UG01

# ---------------- UG02 heart-leaved forest plant (cand-1, D2 V2 lower left) ----------------
def UG02(M):
    """about thirteen broad heart-shaped leaves, each on its own long thin red-green stalk from a low crown, held at different heights
    and angles, cupped along the midrib, the tip drooping; three small young leaves in the middle"""
    rr=random.Random(8302);Z=Vector((0,0,1));LS=_LS()
    _lump('UG02_Crown',(0,0,0),.04,.025,M['ug_redstem'],'Body',seg=8,ring=2,below=.07,rr=rr)
    L_=[]
    for k,az in enumerate((-170,-140,-112,-85,-58,-30,-5,22,50,80,110,140,165)):
        L_.append((az+rr.uniform(-10,10),rr.uniform(.18,.50) if k%2 else rr.uniform(.30,.58),rr.uniform(.17,.25),False))
    L_+= [(rr.uniform(-180,180),rr.uniform(.12,.22),rr.uniform(.07,.10),True) for _ in range(3)]
    for k,(az,h,Ll,young) in enumerate(L_):
        a=math.radians(az);o=Vector((math.cos(a),math.sin(a)*.85,0)).normalized();reach=(.08 if young else rr.uniform(.12,.26))
        tip=o*reach+Z*h;ctrl=[o*.01+Z*-(.024+.0023*(k%7)),o*.015+Z*h*.35,o*reach*.6+Z*h*.85,tip];pts,P,T,S=_crv(ctrl,8)
        _ttube(f'UG02_Stalk{k}',pts,[(.0055 if not young else .0035)*(1-.4*i/(len(pts)-1)) for i in range(len(pts))],M['ug_redstem'],'Body',sides=5,scale=.15)
        dip=math.radians(rr.uniform(15,45) if not young else rr.uniform(-10,15))
        d=(o*math.cos(dip)-Z*math.sin(dip)+Vector((rr.uniform(-.2,.2),rr.uniform(-.2,.2),0))).normalized()
        up=(Z-d*d.dot(Z)).normalized();up=(up+o*.15).normalized()
        LS.poly(HEART,HEART_C,tip-d*.006,d,up,Ll,ws=1.,bend=-rr.uniform(.35,.75),fold=rr.uniform(.10,.20),wave=.02,freq=5,ph=rr.uniform(0,6),npts=28)
    LS.done('UG02_Leaves',M['ug_heart'],'Body')
    return _plant_meta([(.09,.18,.15),(.13,.25,.20),(.18,.32,.25),(.24,.38,.29)],.45,
      ['about thirteen heart-shaped leaves 17–25 cm long, each on its own red-green stalk from a low crown, at different heights and angles, cupped along the midrib, tips drooping; three young leaves in the middle',
       'each leaf is a mesh cut to the heart outline (outline and two rings, 140 triangles), its pale main vein and side veins in its own texture; wet sheen (roughness 0.40)',
       'LOD1 / LOD2: decimated (each item is ≤ 4,000 triangles at LOD0)'])
PROPS['UG02']=UG02

# ---------------- UG03 strap-leaved forest plant (cand-2) ----------------
def UG03(M):
    """a rosette of about sixteen tongue-shaped leaves with wavy edges and a sunken dark midrib, arching up and out from a low crown;
    young leaves upright in the middle; two old leaves yellowing on the ground"""
    rr=random.Random(8303);Z=Vector((0,0,1));LS=_LS();DS=_LS()
    _lump('UG03_Crown',(0,0,0),.035,.03,M['ug_rachis'],'Body',seg=8,ring=2,below=.07,rr=rr)
    n=16
    for k in range(n):
        az=math.radians(k*137.5+rr.uniform(-12,12));o=Vector((math.cos(az),math.sin(az)*.8,0)).normalized()
        inner=k<4;el=math.radians(rr.uniform(78,86) if inner else rr.uniform(56,76));L=rr.uniform(.40,.48) if inner else rr.uniform(.46,.58)
        d=o*math.cos(el)+Z*math.sin(el);up=(Z-d*d.dot(Z)).normalized()
        LS.strap(o*.012,d,-o if el>1.3 else up,L,rr.uniform(.026,.033),nu=14,bend=-(rr.uniform(.3,.6) if inner else rr.uniform(.8,1.35)),
                 fold=.10,wave=rr.uniform(.18,.28),freq=rr.uniform(7,10),ph=rr.uniform(0,6))
    for k,az in enumerate((-60,150)):
        a=math.radians(az);o=Vector((math.cos(a),math.sin(a),0))
        DS.strap(o*.03+Z*.0015,(o+Z*.01).normalized(),Z,rr.uniform(.36,.42),.026,nu=10,bend=-.05,fold=.18,wave=.10,freq=6)
    LS.done('UG03_Leaves',M['ug_strap'],'Body');DS.done('UG03_OldLeaves',M['ug_strap_dead'],'Body')
    return _plant_meta([(.07,.15,.07),(.11,.22,.10),(.16,.29,.13),(.22,.35,.16)],.4,
      ['about sixteen strap leaves 30–50 cm long, wavy edges, sunken dark midrib, arching up and out from a low crown; four young leaves upright in the middle; two old yellowing leaves lying on the ground',
       'each leaf is a strip of fifteen rows by five columns along the midrib (no leaf cards), its midrib and fine side veins in its own texture; glossy (roughness 0.38)',
       'LOD1 / LOD2: decimated (each item is ≤ 4,000 triangles at LOD0)'])
PROPS['UG03']=UG03

# ---------------- UG04 white forest wildflower clump (cand-1, D2 V6 lower right) ----------------
def UG04(M):
    """about twelve deeply cut dark-green leaves close to the ground; seven thin stalks above them, each with one open white
    six-petalled flower and a yellow centre, at different heights facing up and to the side; two closed buds"""
    rr=random.Random(8304);Z=Vector((0,0,1));LS=_LS();PS=_LS()
    _lump('UG04_Crown',(0,0,0),.025,.015,M['ug_stem'],'Body',seg=7,ring=2,below=.06,rr=rr)
    for k in range(12):
        az=math.radians(k*137.5+rr.uniform(-15,15));o=Vector((math.cos(az),math.sin(az)*.85,0)).normalized()
        reach=rr.uniform(.04,.11);h=rr.uniform(.03,.10);tip=o*reach+Z*h;pts,P,T,S=_crv([o*.005+Z*-.02,o*reach*.3+Z*h*.8,tip],6)
        _ttube(f'UG04_LeafStalk{k}',pts,[.0022]*len(pts),M['ug_stem'],'Body',sides=4,scale=.1)
        d=(o+Z*rr.uniform(-.15,.25)).normalized();up=(Z-d*d.dot(Z)).normalized()
        LS.poly(PALM,PALM_C,tip,d,up,rr.uniform(.055,.075),bend=-.25,fold=.10,wave=.04,freq=8,rings=(.45,),npts=30)
    tips=[]
    for k,(az,h,lean) in enumerate(((-150,.22,20),(-95,.25,10),(-40,.19,25),(10,.24,12),(60,.21,22),(115,.17,30),(170,.23,15))):
        a=math.radians(az+rr.uniform(-8,8));o=Vector((math.cos(a),math.sin(a)*.8,0)).normalized();ln=math.radians(lean)
        top=o*(.02+h*math.sin(ln))+Z*h;pts,P,T,S=_crv([o*.004+Z*-.02,o*.01+Z*h*.4,o*(.02+h*math.sin(ln)*.6)+Z*h*.85,top],9)
        _ttube(f'UG04_Stalk{k}',pts,[.0018]*len(pts),M['ug_stem'],'Body',sides=4,scale=.1)
        f=(T(1.)*.6+Z*.4+o*.35).normalized();tips.append((top,f))
        side=f.orthogonal().normalized();rot=rr.uniform(0,6.28)
        for j in range(6):   # six petals round the centre, cupped up towards the flower's face
            ang=rot+j*math.tau/6;pd=(Matrix.Rotation(ang,3,f)@side).normalized();pd=(pd+f*.22).normalized()
            pu=(f-pd*pd.dot(f)).normalized();PS.poly(PETAL,PETAL_C,top+pd*.002,pd,pu,rr.uniform(.017,.020),ws=1.1,bend=.35,fold=.10,rings=(),npts=10)
        bm=bmesh.new();c=[bm.verts.new(top+f*.0035)];rim=[bm.verts.new(top+(Matrix.Rotation(math.tau*q/8,3,f)@side)*.0055+f*.001) for q in range(8)]
        for q in range(8):bm.faces.new((rim[q],rim[(q+1)%8],c[0]))
        bot=bm.verts.new(top-f*.004)
        for q in range(8):bm.faces.new((rim[(q+1)%8],rim[q],bot))
        finish(f'UG04_Centre{k}',bm,M['pollen'],'Body',.05)
    for k,(az,h) in enumerate(((-120,.16),(80,.14))):   # closed buds: five petals folded into an egg
        a=math.radians(az);o=Vector((math.cos(a),math.sin(a),0));top=o*.03+Z*h
        pts,P,T,S=_crv([o*.004+Z*-.02,o*.012+Z*h*.6,top],7);_ttube(f'UG04_BudStalk{k}',pts,[.0016]*len(pts),M['ug_stem'],'Body',sides=4,scale=.1)
        f=(T(1.)+Z*.3).normalized();side=f.orthogonal().normalized()
        for j in range(5):
            pd=(Matrix.Rotation(j*math.tau/5,3,f)@side);d=(f*.9+pd*.30).normalized();pu=(pd-d*d.dot(pd)).normalized()
            PS.poly(PETAL,PETAL_C,top+pd*.002,d,pu,.014,ws=.8,bend=-.9,fold=.25,rings=(),npts=10)
    LS.done('UG04_Leaves',M['ug_palm'],'Body');PS.done('UG04_Petals',M['ug_petal'],'Body')
    return _plant_meta([(.09,.18,.08),(.13,.24,.10),(.18,.30,.13),(.85,.85,.80)],.2,
      ['about twelve palmately cut leaves (five toothed lobes) close to the ground on short stalks; seven thin flower stalks 17–25 cm, each with one open white six-petalled flower (petals one by one, cupped) and a yellow centre; two closed buds',
       'leaf veins and the faint petal veins in their own textures',
       'LOD1 / LOD2: decimated (each item is ≤ 4,000 triangles at LOD0)'])
PROPS['UG04']=UG04

# ---------------- UG05 fallen-leaf heaps, three sizes (cand-3) ----------------
def _ug05(M,pid,R,h,n,seed,twigs,bark,Lr=(.06,.11)):
    # 2026-11-25: was a flat dome (height / width about 0.12) on an elliptic, near-black mound whose rim showed all round, so in the Unity
    # forest patch and the D2 match it read as a dark round cake. Now, as in the three-view: a heaped pile (height / width about 0.25,
    # a low skirt rising to a rounded top), a lobed outline, leaves following the slope with their own tilt (some tucked in steeply),
    # the mound smaller than the leaves' spread and a mid brown, and loose single leaves lying flat on the ground round the edge.
    rr=random.Random(seed);LS=_LS();Z=Vector((0,0,1))
    p1,p2,p3=rr.uniform(0,6.3),rr.uniform(0,6.3),rr.uniform(0,6.3)
    def rim(a):return 1+.11*math.sin(3*a+p1)+.07*math.sin(5*a+p2)
    def mound(x,y):
        a=math.atan2(y/.85,x);s=math.hypot(x,y/.85)/(R*rim(a))
        if s>=1:return 0.
        return h*(1-s)**1.7*(1+.7*s)*(1+.10*s*math.sin(4*a+p3))
    def grad(x,y,e=.004):
        return Vector((-(mound(x+e,y)-mound(x-e,y))/(2*e),-(mound(x,y+e)-mound(x,y-e))/(2*e),1)).normalized()
    # the mound under the leaves: litter, a mid brown, its rim a little inside the leaves' spread and a little under the ground
    bm=bmesh.new();rows=[];seg=20;ring=6
    for i in range(ring+1):
        t=i/ring;row=[]
        for k in range(seg if i<ring else 1):
            a=math.tau*k/seg;rad=R*.96*rim(a)*(1-t)**.9;x,y=math.cos(a)*rad,math.sin(a)*rad*.85
            row.append(bm.verts.new((x,y,mound(x,y)-.004*(i==0))))
        rows.append(row)
    for A_,B_ in zip(rows,rows[1:]):
        for k in range(seg):
            if len(B_)==1:bm.faces.new((A_[k],A_[(k+1)%seg],B_[0]))
            else:bm.faces.new((A_[k],A_[(k+1)%seg],B_[(k+1)%seg],B_[k]))
    for f in bm.faces:f.smooth=True
    from mathutils.bvhtree import BVHTree
    bvh=BVHTree.FromBMesh(bm)
    def mz(x,y):   # the mound mesh's own height (its flat faces sag under the smooth formula; leaves lie on the mesh)
        hit=bvh.ray_cast(Vector((x,y,1.)),Vector((0,0,-1.)));return max(hit[0].z,0.) if hit[0] else 0.
    finish(f'{pid}_Mound',bm,M['ug_litter'],'Body',.25)
    placed=[];tries=0;ok=0;nl=int(n*.16)   # nl loose leaves on the ground round the heap
    while ok<n and tries<n*40:
        tries+=1;loose=ok>=n-nl
        a=rr.uniform(0,6.28)
        s=rr.uniform(.98,1.25) if loose else min(1.,rr.random()**.75*1.02)
        d_=R*rim(a)*s;x,y=math.cos(a)*d_,math.sin(a)*d_*.85
        Ln=rr.uniform(*Lr)*(.8 if loose else 1.);z=mz(x,y)
        if any((x-p[0])**2+(y-p[1])**2<(Ln*.30)**2 and abs(z-p[2])<.02 for p in placed):continue
        k=sum(1 for p in placed if (x-p[0])**2+(y-p[1])**2<(Ln*.5)**2 and p[3]==loose)   # stacked on earlier leaves (not counting itself): a little higher
        placed.append((x,y,z,loose));ok+=1
        b=rr.uniform(0,6.28);dd=Vector((math.cos(b),math.sin(b),0))
        if loose:   # flat on the ground, edges curled up a little
            nrm=Vector((rr.uniform(-.06,.06),rr.uniform(-.06,.06),1)).normalized();base=Vector((x,y,-.0025+.0025*min(k,3)));bend=rr.uniform(-.05,.2)
        else:
            g=grad(x,y);t_=rr.random()
            tilt=rr.uniform(-.30,.30) if t_<.75 or s>.8 else rr.uniform(.45,.85)*(1 if rr.random()<.5 else -1)   # a quarter tucked in steeply (not on the skirt, where they would stand clear)
            ax=dd.cross(g).normalized();nrm=(g*math.cos(tilt)+ax.cross(g)*math.sin(tilt)).normalized()
            dd=(dd-nrm*dd.dot(nrm)).normalized()
            base=Vector((x,y,z+.0018+.0025*min(k,4)))-dd*Ln*.45;bend=rr.uniform(-.3,.3)
        P,C=(OAK,OAK_C) if rr.random()<.45 else (OVAL,OVAL_C)
        nv0=len(LS.bm.verts);LS.poly(P,C,base,dd,nrm,Ln,ws=rr.uniform(.85,1.1),bend=bend,fold=rr.uniform(-.05,.12),curl=rr.uniform(.05,.35),rings=(),npts=12)
        # no part of a leaf under the ground: a steep or drooping leaf on the skirt went 2–3 cm under it, and the build then lifted the
        # whole heap to put its lowest point on z = 0, so the loose leaves hung in the air
        LS.bm.verts.ensure_lookup_table();nv=LS.bm.verts[nv0:];low=min(v.co.z for v in nv)
        if low<-.0035:   # the mound's rim is 4 mm under z = 0 and is the lowest point; the leaves stop just above it
            for v in nv:v.co.z+=-.0035-low
    for k in range(twigs):   # a few thin twigs lying across the top
        a=rr.uniform(0,3.14);c=Vector((rr.uniform(-R,R)*.4,rr.uniform(-R,R)*.3,0));dv=Vector((math.cos(a),math.sin(a),0));L_=rr.uniform(.25,.45)*R/.45
        pts=[c+dv*L_*(i/6-.5) for i in range(7)]
        for p in pts:p.z=mound(p.x,p.y)+.012+.006*math.sin(p.x*20)
        _ttube(f'{pid}_Twig{k}',pts,[.0035*(1-.4*i/6) for i in range(7)],M['twig'],'Body',sides=4,scale=.1)
    if bark:   # one curled piece of bark half in the heap
        bm=bmesh.new();c=Vector((R*.25,-R*.2,0));vs=[]
        for i in range(5):
            row=[]
            for j in range(4):
                ang=-.9+1.8*j/3;x=c.x+(i/4-.5)*.14;y=c.y+math.sin(ang)*.025;z=mound(x,y)+.008+(1-math.cos(ang))*.018+.004
                row.append(bm.verts.new((x,y,z)))
            vs.append(row)
        for A_,B_ in zip(vs,vs[1:]):
            for j in range(3):bm.faces.new((A_[j],A_[j+1],B_[j+1],B_[j]))
        bmesh.ops.solidify(bm,geom=bm.faces[:],thickness=.004)
        finish(f'{pid}_Bark',bm,M['bark'],'Body',.15)
    LS.done(f'{pid}_Leaves',M['ug_oval'],'Body')
    def extra(col,rough,P_,noise,filled,meta):   # each patch of leaves its own shade of russet, ochre or dull orange; wet and dark at the bottom
        # 2026-11-25: smaller patches and three tones (dull red-brown, russet, pale tan) so neighbouring leaves differ, as in the three-view
        # each leaf lies at its own tilt, so its normal (coarsely rounded) picks its tone; the smooth mound changes tone only slowly
        nq=np.round(meta['_onrm']*2.5);hk=np.abs(np.sin(nq[...,0]*12.9898+nq[...,1]*78.233+nq[...,2]*37.719+seed*.013)*43758.5453)%1.
        hue=.55*hk+.45*_fb(P_,(14.,14.,14.),seed,2);t=np.clip((hue-.25)*2.2,0,1)[...,None];pale=np.clip((hue-.66)*4,0,1)[...,None]
        col=col*((1-t)*np.array([.86,.70,.66])+t*np.array([1.02,.96,.80]));col=col*(1-pale)+pale*(col.mean(2,keepdims=True)*.35+np.array([.50,.40,.27])*.75)
        g_=col.mean(2,keepdims=True);col=g_+(col-g_)*.78
        # the bottom only a little darker and no longer glossier (2026-11-25: in URP the glossy wet bottom and the loose leaves
        # round the heap mirrored the grey-blue sky and read as a blue-grey ring)
        wet=filled*np.clip((h*.30-P_[...,2])/(h*.30),0,1);col=col*(1-.18*wet[...,None])
        return col,rough
    meta=_plant_meta([(.30,.18,.09),(.42,.27,.13),(.55,.37,.19)],R,
      [f'a heap of fallen leaves about {2*R:.2f} m across and {h:.2f} m high (a low skirt rising to a rounded top, lobed outline): {n} oval and lobed leaves one by one in layers over a brown litter mound, following the slope each at its own tilt, a quarter tucked in steeply, curled edges; about {int(n*.16)} loose single leaves lying flat on the ground round the edge'
       +(f', {twigs} twigs' if twigs else '')+(', a curled piece of bark' if bark else ''),
       'drier and lighter on top, darker and wet at the bottom; each leaf\'s veins in the leaf texture',
       'LOD1 / LOD2: decimated (each item is ≤ 4,000 triangles at LOD0)'],extra=extra,dark=(.12,.08,.05))
    meta.pop('ground0');meta['origin_note']='footprint centre, bottom z = 0 (the rim of the heap a few mm under it), front = -Y (Blender) / -Z (FBX, Unity)'
    return meta
PROPS['UG05_01']=lambda M:_ug05(M,'UG05_01',.20,.10,120,8351,1,False,(.055,.095))
PROPS['UG05_02']=lambda M:_ug05(M,'UG05_02',.42,.18,270,8352,3,True,(.075,.135))
PROPS['UG05_03']=lambda M:_ug05(M,'UG05_03',.64,.24,290,8353,4,True,(.09,.17))

# ---------------- UG06 creeping vine segments to lay along roots (cand-5) ----------------
def _ug06(M,pid,Rr,Ln,phi,seed,shoots,ground=0.):
    """a thin stem hugging a root of radius Rr (axis along X at z = -Rr, its top line at z = 0), small heart leaves lying on the
    bark, tiny clinging rootlets; phi(t) is the stem's angle round the root (0 on top), ground > 0: the last part runs down onto the ground"""
    rr=random.Random(seed);LS=_LS();Z=Vector((0,0,1))
    def surf(x,a,off=0.):
        return Vector((x,math.sin(a)*(Rr+off),-Rr+math.cos(a)*(Rr+off)))
    path=[]
    N=int(Ln/.02)
    for i in range(N+1):
        t=i/N;x=-Ln/2+Ln*t;a=phi(t)
        path.append(surf(x,a,.0035))
    if ground:   # down the side and onto the ground (z = -2Rr)
        x=path[-1].x;a0=phi(1.)
        for j in range(1,7):path.append(surf(x+.01*j,a0+(math.pi*.5-a0)*j/6,.0035))
        for j in range(1,int(ground/.03)+1):path.append(Vector((x+.06+.03*j,Rr+.004+.02*math.sin(j),-2*Rr+.0035)))
    pts,P,T,S=_crv(path,len(path))
    # 2026-11-25: stem 3.4 → 4.6 mm, leaves 4.0–5.8 → 5.0–8.2 cm about every 2.3 cm (was 2.6), each lifted a little (0–6°) at the stalk and bending down along the curve of the root, because
    # in the Unity forest patch the vine read only as a thin line on the root (the D2 concept's vine leaves are also bigger and denser);
    # then (same day) a leaf about every 2.0 cm, straight stalks, and its own paler sage-green leaf (ug_vine)
    _ttube(f'{pid}_Stem',pts,[.0046*(1-.35*i/(len(pts)-1)) for i in range(len(pts))],M['ug_redstem'],'Body',sides=4,scale=.1)
    def nrm_at(p):
        if p.z<-2*Rr+.01:return Z
        return Vector((0,p.y,p.z+Rr)).normalized()
    nl=int(S/.020);red=set(rr.sample(range(nl),max(2,nl//8)))
    for i in range(nl):
        u=(i+rr.uniform(.15,.85))/nl;p=P(u);t=T(u);n=nrm_at(p);sd=1 if i%2 else -1
        if rr.random()<.12:sd=-sd   # now and then two leaves on one side, so the row is not a regular saw edge
        side=t.cross(n).normalized()*sd;fw=rr.uniform(.15,.95)*(1 if rr.random()<.8 else -.6)
        d=(side*.8+t*fw).normalized();d=(d-n*d.dot(n)).normalized()
        Ll=rr.uniform(.050,.082);q=p+d*.010+n*(.005+.0016*(i%3));lf=rr.uniform(.0,.10)   # i%3: neighbours at three heights, never in one plane
        dl=(d+n*lf).normalized();nl_=(n-d*lf).normalized()   # the blade rises a little from the bark, each leaf by its own angle
        _ttube(f'{pid}_Petiole{i}',[p,q],[.0014]*2,M['ug_redstem'],'Body',sides=3,scale=.05,cap0=False,cap1=False)
        LS_=LS if i not in red else RL;LS_.poly(HEART,HEART_C,q,dl,nl_,Ll,bend=.24,fold=.05,rings=(),npts=12)
        if i%3==0:   # clinging rootlets into the bark
            for j in range(3):
                r0=p-side*sd*.002;r1=r0+(-side*sd*.006+t*(j-1)*.004)-n*.0025
                _ttube(f'{pid}_Rootlet{i}{j}',[r0,(r0+r1)/2-n*.0005,r1],[.0007,.0006,.0004],M['ug_redstem'],'Body',sides=3,scale=.05,cap0=False)
    for k,u0 in enumerate(shoots):   # short side shoots lifting off the root with a few young leaves
        p=P(u0);n=nrm_at(p);t=T(u0);sh=[p,p+n*.04+t*.02,p+n*.09+t*.05+t.cross(n)*.02,p+n*.13+t*.06]
        sp,SP,ST,SS=_crv(sh,8);_ttube(f'{pid}_Shoot{k}',sp,[.0024*(1-.5*i/(len(sp)-1)) for i in range(len(sp))],M['ug_redstem'],'Body',sides=4,scale=.08)
        for j,v in enumerate((.35,.6,.85,1.)):
            q=SP(v);tt=ST(v);sd=1 if j%2 else -1;d=(tt.cross(n).normalized()*sd+tt*.5+n*.3).normalized()
            LS.poly(HEART,HEART_C,q,d,(n+tt*.3),.030+.008*j*(j<3),bend=-.2,fold=.10,rings=(),npts=12)
    return LS
def _ug06_item(pid,Rr,Ln,phi,seed,shoots,ground=0.):
    def f(M):
        global RL
        RL=_LS();LS=_ug06(M,pid,Rr,Ln,phi,seed,shoots,ground)
        LS.done(f'{pid}_Leaves',M['ug_vine'],'Body');RL.done(f'{pid}_RedLeaves',M['ug_heart_red'],'Body')
        meta=_plant_meta([(.09,.18,.15),(.12,.23,.18),(.16,.29,.22)],Ln/2,
          [f'a thin creeping vine {Ln:.1f} m long made to lie on a root {2*Rr:.2f} m thick (radius {Rr:.2f} m): the root axis runs along X, {Rr:.2f} m under the origin; the origin is on the root\'s top line'
           +(f'; the last part climbs down the root\'s side and runs {ground:.1f} m over the ground ({2*Rr:.2f} m under the origin)' if ground else ''),
           'the stem (about 9 mm across at the start) hugs the bark (3.5 mm off it), pale sage-green heart-shaped leaves with silvery veins, 5–8 cm long about every 2.0 cm on short stalks, mostly alternate, pointing each its own way, lifted a little at the stalk and bending down to follow the curve of the root, a few red-brown; tiny clinging rootlets every few leaves'
           +(f'; {len(shoots)} short side shoots lift off the root with young leaves' if shoots else ''),
           'the root is not part of the model; LOD1 / LOD2: decimated (each item is ≤ 4,000 triangles at LOD0)'],gz=-2*Rr)
        meta['origin_note']=f'on the top line of a root of radius {Rr:.2f} m whose axis runs along X {Rr:.2f} m below; front = -Y (Blender) / -Z (FBX, Unity)'
        return meta
    return f
PROPS['UG06_01']=_ug06_item('UG06_01',.15,.9,lambda t:.25*math.sin(t*5.5)+.05,8361,(.62,))
PROPS['UG06_02']=_ug06_item('UG06_02',.22,1.2,lambda t:.40*math.sin(t*7.+.6)-.1*t,8362,(.30,.72))
PROPS['UG06_03']=_ug06_item('UG06_03',.30,1.0,lambda t:-.3+1.5*t*t+.12*math.sin(t*9),8363,(.25,))
PROPS['UG06_04']=_ug06_item('UG06_04',.18,.8,lambda t:.20*math.sin(t*4.)+.75*t**3,8364,(),ground=.35)
