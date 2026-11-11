# GC01–GC06 shapes, read by build_gc.py (helpers from the creekside kit, its part helpers and the LV items).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _blob(name,size,seed,mat,grp,sub=4,flats=2,flat_amt=.6,bottom=.32,bumps=5,amp=.07,scale=.25,cut=0.):
    """a water-rounded stone: an icosphere pushed by a few broad bumps and dents (never a perfect ellipsoid), a couple of
    softly flattened faces, the underside flatter (it lay on the bed); size = (L, W, H) in m; bottom at z = 0, centred"""
    rr=random.Random(seed);bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=sub,radius=1.)
    B=[(Vector((rr.gauss(0,1),rr.gauss(0,1),rr.gauss(0,1))).normalized(),rr.uniform(-1,1)*amp,rr.uniform(.35,.8)) for _ in range(bumps)]
    F=[(Vector((rr.uniform(-1,1),rr.uniform(-1,1),rr.uniform(-.2,1))).normalized(),rr.uniform(.72,.85)) for _ in range(flats)]
    for v in bm.verts:
        d=v.co.normalized();r=1.
        for c,a,w in B:r+=a*math.exp(-((1-d.dot(c))/w)**2*2.5)
        p=d*r
        for n,t in F:   # a softly flattened face
            h=p.dot(n)-t
            if h>0:p-=n*h*flat_amt
        if p.z<-bottom*2:p.z=-bottom*2+(p.z+bottom*2)*.25   # the flatter underside
        v.co=p
    for _ in range(2):bmesh.ops.smooth_vert(bm,verts=bm.verts,factor=.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    co=np.array([v.co[:] for v in bm.verts]);lo,hi=co.min(0),co.max(0);S=np.array(size)/(hi-lo)
    for v in bm.verts:v.co=Vector(((v.co.x-(lo[0]+hi[0])/2)*S[0],(v.co.y-(lo[1]+hi[1])/2)*S[1],(v.co.z-lo[2])*S[2]))
    if cut:   # half-buried: keep only the part above the ground line, closed flat underneath, bottom at z = 0
        zc=cut*size[2];bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(0,0,zc),plane_no=(0,0,1),clear_inner=True)
        e_=[e for e in bm.edges if e.is_boundary]
        if e_:bmesh.ops.edgeloop_fill(bm,edges=e_)
        for v in bm.verts:v.co.z-=zc
        bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=.0005)
    for f in bm.faces:f.smooth=f.calc_area()<.01 or abs(f.normal.z)<.99
    return finish(name,bm,mat,grp,scale)

def _tuft_even(name,base,mat,grp,rr,n=4,h=.06):
    """a small grass tuft whose blades lean out evenly round the clock (random azimuths put two blades side by side
    in one plane: coplanar faces in the QA)"""
    a0=rr.uniform(0,math.tau)
    for i in range(n):
        a=a0+math.tau*i/n+rr.uniform(-.25,.25);lean=rr.uniform(.2,.5);d=(math.cos(a)*lean,math.sin(a)*lean,1)
        leaf(f'{name}_{i}',base+Vector((math.cos(a)*.004,math.sin(a)*.004,0)),d,(-math.sin(a),math.cos(a),0),h*rr.uniform(.6,1.1),.007,mat,grp,curl=.35,seg=5)

# ---------------- GC01 five separate water-rounded creek stones (cand-2) ----------------
def GC01(M):
    """five creek stones laid out apart, each its own outline: a big fat round one, a long flat one, a tall egg, a low flat
    one, a small round one; warm grey and blue-grey, pale quartz veins, the lower half wet and darker, silt in the hollows,
    a thin line of algae at the old water line. Each stone is its own object (S1–S5), origin at its bottom centre."""
    SZ=[((.40,.32,.26),101,'river',4,.30),((.32,.20,.14),102,'river_b',3,.40),((.20,.17,.20),103,'river',3,.25),((.22,.15,.10),104,'river_b',3,.45),((.12,.11,.09),105,'river',2,.3)]
    x=-.83;ST=[]
    for k,(sz,seed,m,fl,bt) in enumerate(SZ):
        o=_blob(f'GC01_S{k+1}',sz,seed,M[m],f'S{k+1}',flats=fl,bottom=bt,amp=.10,flat_amt=.5)
        cx=x+sz[0]/2;o.data.transform(Matrix.Rotation(random.Random(seed).uniform(-.3,.3),4,'Z'));o.data.transform(Matrix.Translation((cx,random.Random(seed+9).uniform(-.04,.04),0)))
        ST.append((cx,sz));x+=sz[0]+.1
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        H=np.zeros_like(pz)
        for cx,sz in ST:H=np.where(np.abs(px-cx)<sz[0]/2+.02,sz[2],H)
        h=pz/np.maximum(H,1e-3)
        vein=np.zeros_like(pz)
        for a,b,c,f in ((.8,.5,.3,38),(-.3,.9,.4,52),(.5,-.4,.8,30)):   # pale quartz veins: thin bands through the stone
            s=np.abs(np.sin((px*a+py*b+pz*c)*f+1.4*noise));vein=np.maximum(vein,np.clip((.07-s)/.07,0,1)*np.clip((noise-.35)*3,0,1))
        col=col*(1-.75*vein[...,None])+vein[...,None]*np.array([.80,.77,.70])*.75
        wet=filled*np.clip((.48-h)/.10,0,1);col=col*(1-.42*wet[...,None])+wet[...,None]*np.array([.0,.01,.02]);rough=np.clip(rough-.25*wet,0,1)
        alg=filled*np.exp(-((h-.5)/.035)**2)*np.clip((noise-.35)*2.5,0,1)   # a thin line of algae at the water line
        col=col*(1-.55*alg[...,None])+alg[...,None]*np.array([.10,.15,.05])
        silt=filled*np.clip((cav-.55)*4,0,1)*np.clip((.6-h)/.3,0,1)+filled*np.clip((.06-h)/.06,0,1)*.8   # silt in the hollows and round the foot
        col=col*(1-.45*silt[...,None])+silt[...,None]*np.array([.20,.16,.11])*.45
        lay=filled*(.5+.5*np.sin(pz*55+px*9+2*noise))   # a soft banding: the layers the stone was laid down in
        col=col*(1-.10*lay[...,None])
        return col,rough
    return {'paint':paint,'wear':.4,'grime':.6,'uv_angle':55,'separate':True,
            'notes':['five creek stones laid out 0.1 m apart along X, each its own object GC01_S1–S5 with its origin at its bottom centre (take any one out and it stands on the ground)',
                     'water-rounded but not perfect: broad bumps and dents and one or two softly flat faces, the underside flatter; quartz veins, wet lower half, silt and an algae line are painted']}
PROPS['GC01']=GC01

def _shard(name,size,seed,mat,grp,npts=30,bev=.004,flat=.12,scale=.25,ripple=1.):
    """an angular broken stone: the convex hull of points scattered on a lumpy ellipsoid (flat break faces of all sizes,
    sharp edges), the faces given a low ripple so they are never machine-flat, edges softened by a small bevel; the
    underside cut flat where it sits; size = (L, W, H); returns (object, the two biggest upward-facing break normals:
    painted as fresh lighter breaks)"""
    rr=random.Random(seed);bm=bmesh.new()
    for _ in range(npts):
        d=Vector((rr.gauss(0,1),rr.gauss(0,1),rr.gauss(0,1))).normalized()*rr.uniform(.80,1.0);bm.verts.new(d)
    bmesh.ops.convex_hull(bm,input=bm.verts[:]);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    co=np.array([v.co[:] for v in bm.verts]);lo,hi=co.min(0),co.max(0);S=np.array(size)/(hi-lo)
    for v in bm.verts:v.co=Vector(((v.co.x-(lo[0]+hi[0])/2)*S[0],(v.co.y-(lo[1]+hi[1])/2)*S[1],(v.co.z-lo[2])*S[2]))
    zc=flat*size[2]
    if flat:   # cut flat where it sits (loose stones); a stone in a pile rests on its own corners instead
        bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(0,0,zc),plane_no=(0,0,1),clear_inner=True)
        edges=[e for e in bm.edges if e.is_boundary]
        if edges:bmesh.ops.edgeloop_fill(bm,edges=edges)
    for v in bm.verts:v.co.z-=zc
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    up=sorted([f for f in bm.faces if f.normal.z>.15],key=lambda f:-f.calc_area())[:2];br=[f.normal.copy() for f in up]
    bmesh.ops.triangulate(bm,faces=bm.faces[:])
    if ripple:bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=2,use_grid_fill=True)
    bm.normal_update();ph=[rr.uniform(0,9) for _ in range(4)];L_=max(size)
    for v in bm.verts:   # a low ripple and a few chips on the break faces (the flat underside stays flat)
        if flat and v.co.z<.002:continue
        x,y,z=v.co/L_;d=.010*math.sin(x*11+ph[0])*math.sin(y*13+ph[1])+.007*math.sin(z*17+ph[2]+x*7)+.004*math.sin((x+y+z)*31+ph[3])
        v.co+=v.normal*d*min(size)*1.6*ripple   # scaled by the stone's thinnest side: a thin slab folded over with the long side
    bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=.0006*max(1.,L_/.1));bmesh.ops.recalc_face_normals(bm,faces=bm.faces)   # slivers from the cut gave a zero-area UV face
    for f in bm.faces:f.smooth=False
    o=finish(name,bm,mat,grp,scale)
    if bev:bevel(o,min(bev,.025*min(size)),2,angle=25)   # a 4 mm bevel folded over itself on the small stones
    b2=bmesh.new();b2.from_mesh(o.data);bmesh.ops.dissolve_degenerate(b2,edges=b2.edges[:],dist=.0004)   # bevel corners where many break edges meet left needle faces (zero-area UV)
    bmesh.ops.delete(b2,geom=[f for f in b2.faces if f.calc_area()<2e-8],context='FACES');b2.to_mesh(o.data);b2.free()
    return o,br

# ---------------- GC02 five separate angular broken path stones (cand-3) ----------------
def GC02(M):
    """five broken mountain stones laid out apart: a big one with a long slanting break, a wedge, a tall pointed slab, a low
    flat block, a small chunk; warm-grey rock with flat break faces and sharp (softened) edges — unlike GC01's water-rounded
    stones; the freshest breaks paler, dust in the creases, lichen on the old upper faces. Each stone its own object."""
    SZ=[((.30,.22,.18),201,34),((.22,.13,.16),202,26),((.12,.09,.24),203,28),((.21,.15,.08),204,30),((.12,.10,.08),205,22)]
    x=-.68;ST=[]
    for k,(sz,seed,n) in enumerate(SZ):
        o,br=_shard(f'GC02_S{k+1}',sz,seed,M['rock'],f'S{k+1}',npts=n)
        rot=random.Random(seed).uniform(-.4,.4);R=Matrix.Rotation(rot,4,'Z');o.data.transform(R)
        cx=x+sz[0]/2;o.data.transform(Matrix.Translation((cx,random.Random(seed+9).uniform(-.03,.03),0)))
        ST.append((cx,sz,[R.to_3x3()@b for b in br]));x+=sz[0]+.1
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        for cx,sz,br in ST:
            on=filled*(np.abs(px-cx)<sz[0]/2+.03)
            for b in br:   # the fresh breaks: paler, cleaner, a little warmer
                fr=on*np.clip((onrm[...,0]*b.x+onrm[...,1]*b.y+onrm[...,2]*b.z-.93)*20,0,1)
                col=col*(1-.5*fr[...,None])+fr[...,None]*np.array([.72,.67,.60])*.5;rough=np.clip(rough+.05*fr,0,1)
        dust=filled*np.clip((cav-.5)*3,0,1);col=col*(1-.25*dust[...,None])+dust[...,None]*np.array([.34,.28,.20])*.25   # dust in the creases
        lic=filled*np.clip(onrm[...,2],0,1)*np.clip((noise-.58)*5,0,1)   # lichen on the old upper faces
        col=col*(1-.6*lic[...,None])+lic[...,None]*np.array([.62,.64,.52])*.6
        lay=filled*(.5+.5*np.sin((pz*.8+px*.35+py*.2)*70+2*noise));col=col*(1-.08*lay[...,None])   # faint bedding layers
        return col,rough
    return {'paint':paint,'wear':.6,'grime':.6,'uv_angle':40,'separate':True,
            'notes':['five broken stones laid out 0.1 m apart along X, each its own object GC02_S1–S5 with its origin at its bottom centre',
                     'convex-hull break faces with a 4 mm bevel, the underside cut flat; the two biggest upward breaks painted as fresh pale breaks, dust, lichen and faint bedding painted']}
PROPS['GC02']=GC02

# ---------------- GC03 four separate flat stones half-buried in the ground (cand-6) ----------------
def GC03(M):
    """four flat fieldstones of different sizes, only their weathered rounded tops above the ground, each with a ring of
    packed earth round its foot (thick against the stone, thinning outwards) and short grass along the ring; a crack or
    two and small moss patches on the top edge are painted. Each stone with its earth and grass is one object (S1–S4)."""
    SZ=[((.58,.42,.40),301,3),((.46,.34,.32),302,3),((.38,.30,.28),303,2),((.32,.24,.24),304,2)]
    x=-1.08;ST=[]
    for k,(sz,seed,fl) in enumerate(SZ):
        g=f'S{k+1}';rr=random.Random(seed)
        o=_blob(f'GC03_S{k+1}',sz,seed,M['field'],g,flats=fl,amp=.06,flat_amt=.55,cut=.62,scale=.3)   # the top 38 % of a buried stone
        H=max(v.co.z for v in o.data.vertices)
        cx=x+sz[0]/2+.06;R=Matrix.Rotation(rr.uniform(-.5,.5),4,'Z');o.data.transform(R);o.data.transform(Matrix.Translation((cx,rr.uniform(-.04,.04),0)))
        cy=o.data.vertices[0].co.y*0+sum(v.co.y for v in o.data.vertices)/len(o.data.vertices)
        base=[v.co.copy() for v in o.data.vertices if v.co.z<.004]
        NA=48;rows=[];rs=[]
        for i in range(NA):   # the stone's foot outline: the farthest base point in each direction
            a=math.tau*i/NA;d=Vector((math.cos(a),math.sin(a),0))
            r0=max([(p-Vector((cx,cy,0))).dot(d) for p in base if abs((p-Vector((cx,cy,0))).normalized().dot(d))>.97] or [min(sz[0],sz[1])/2]);rs.append(r0)
        for i in range(NA):   # earth ring: thick at the stone, thinning out over 4–7 cm, a ragged outer edge
            a=math.tau*i/NA;d=Vector((math.cos(a),math.sin(a),0));r0=rs[i];w=rr.uniform(.04,.07)
            row=[]
            for t in np.linspace(0,1,5):
                r_=r0*.94+(w+r0*.06)*t;z=.022*(1-t)**1.6+.0012
                row.append((cx+d.x*r_,cy+d.y*r_,z))
            rows.append(row)
        rows.append(rows[0])
        P=[[Vector(p) for p in r] for r in rows];bm=bmesh.new();top=[[bm.verts.new(p) for p in r] for r in P[:-1]];bot=[[bm.verts.new((p.x,p.y,0.)) for p in r] for r in P[:-1]]
        n=len(top)
        for i in range(n):
            a_,b_=top[i],top[(i+1)%n];c_,d_=bot[i],bot[(i+1)%n]
            for j in range(4):bm.faces.new((a_[j],a_[j+1],b_[j+1],b_[j]));bm.faces.new((c_[j],d_[j],d_[j+1],c_[j+1]))
            bm.faces.new((a_[4],c_[4],d_[4],b_[4]));bm.faces.new((a_[0],b_[0],d_[0],c_[0]))
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        for f in bm.faces:f.smooth=True
        finish(f'GC03_S{k+1}_Earth',bm,M['soil'],g,.3)
        for j in range(14):   # short grass along the ring
            i=rr.randrange(NA);a=math.tau*i/NA+rr.uniform(-.05,.05);d=Vector((math.cos(a),math.sin(a),0));t=rr.uniform(.25,.85)
            r_=rs[i]*.94+(.05+rs[i]*.06)*t;z=.022*(1-t)**1.6+.0012-.003
            _tuft_even(f'GC03_S{k+1}_Grass{j}',Vector((cx+d.x*r_,cy+d.y*r_,z)),M['grass'],g,rr,n=rr.randint(3,5),h=rr.uniform(.035,.07))
        ST.append((cx,cy,sz,H));x+=sz[0]+.17
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        for cx,cy,sz,H in ST:
            on=filled*(np.abs(px-cx)<sz[0]/2)*(np.abs(py-cy)<sz[1]/2)*(pz>.01)
            h=pz/H;r=np.hypot((px-cx)/sz[0],(py-cy)/sz[1])
            mo=on*np.clip((noise-.45)*3,0,1)*np.exp(-((h-.55)/.25)**2)*np.clip(onrm[...,2],0,1)   # moss patches on the upper shoulder
            col=col*(1-.55*mo[...,None])+mo[...,None]*np.array([.13,.19,.05])
            crk=on*np.clip((.012-np.abs(np.sin((px-cx)*9+(py-cy)*23+noise*1.2))*.05)/.012,0,1)*(r<.35)   # a crack across the top
            col=col*(1-.6*crk[...,None])
            soil=on*np.clip((.10-h)/.10,0,1);col=col*(1-.35*soil[...,None])+soil[...,None]*np.array([.20,.15,.10])*.35   # earth line where it meets the ground
        return col,rough
    return {'paint':paint,'wear':.5,'grime':.8,'uv_angle':50,'separate':True,
            'notes':['four half-buried flat stones 0.3–0.58 m laid out apart, each with its earth ring and short grass as one object GC03_S1–S4, origin at its bottom centre',
                     'only the top of each stone is modelled (the part above ground, bottom flat at z = 0): place them straight on the ground; cracks, moss and the earth line are painted']}
PROPS['GC03']=GC03

# ---------------- GC04 a small cluster of ordinary wild mushrooms in leaf litter (cand-1) ----------------
def GC04(M):
    """seven ordinary mushrooms of different heights growing from a low patch of earth and fallen leaves: a big one in the
    middle, three middling, three small; each a pale stem (thicker and dirty at the foot, a little bent) under a tan to
    brown cap with gills below; two caps with a piece broken out of the rim. Not glowing (unlike the glowing fungi kit).
    Squeezed to the work pack's 0.15 m height, so lower and broader than cand-1."""
    rr=random.Random(404)
    # (x, y, stem height, cap radius, cap height, lean x, lean y, broken)
    MU=[(.005,.010,.092,.048,.030,.010,-.004,True),(-.062,-.020,.058,.033,.020,-.012,-.006,False),(.066,-.028,.050,.036,.019,.014,-.002,True),
        (.030,.060,.044,.026,.016,.004,.010,False),(-.030,-.068,.026,.020,.012,-.004,-.008,False),(-.072,.044,.022,.016,.010,-.008,.006,False),(.060,.048,.018,.012,.008,.006,.004,False)]
    CAPS=[]
    for k,(x,y,hs,R,hc,lx,ly,brk) in enumerate(MU):
        b=Vector((x,y,.004));t=Vector((x+lx,y+ly,.004+hs))
        rb=max(.004,R*.30);pts=[b+(t-b)*u+Vector((0,0,0))+Vector((lx,ly,0))*(.15*math.sin(math.pi*u)) for u in np.linspace(0,1,7)]
        _taper(f'GC04_Stem{k}',pts,[rb*1.25,rb*1.05,rb*.92,rb*.85,rb*.82,rb*.80,rb*.80],M['stem'],'Body',sides=10,scale=.06)
        zu=t.z;zr=zu-.18*hc   # cap: rim a little below the gill plane, gills a shallow cone up to the stem
        prof=[]
        for r in np.linspace(.002,R,9):prof.append((zu+.12*hc*(1-(r/R)**2)-(.18*hc)*(r/R)**3,r))   # underside (gills)
        prof.append((zr-.002,R*1.012))   # the rim's lip
        for r in np.linspace(R,.002,10):prof.append((zr+hc*(1-(r/R)**2)**.65+.002,r))   # the top
        z0=min(z for z,_ in prof)-.001;z1=max(z for z,_ in prof)+.001
        cap=_lathe(f'GC04_Cap{k}',[((z-z0)/(z1-z0),r) for z,r in prof],(Vector((t.x,t.y,z0)),Vector((t.x,t.y,z1))),M['cap'],'Body',NS=28,scale=.08,loop=True)
        if brk:   # a piece broken out of the rim
            a=rr.uniform(0,math.tau);c=Vector((t.x+math.cos(a)*R*1.05,t.y+math.sin(a)*R*1.05,zr+hc*.3))
            ct=_cutter(f'GC04_Break{k}',(R*.55,R*.38,hc*2.4),c);ct.data.transform(Matrix.Translation(-c));ct.data.transform(Matrix.Rotation(a+.4,4,'Z'));ct.data.transform(Matrix.Translation(c))
            _boolean(cap,ct)
        CAPS.append((t.x,t.y,zu,R))
    # a low patch of earth and moss, and fallen leaves lying on it
    NA=40;bm=bmesh.new();ring=[];top=[]
    for i in range(NA):
        a=math.tau*i/NA;r=.128+.012*math.sin(3*a+1)+.008*math.sin(7*a);ring.append(bm.verts.new((r*math.cos(a)*1.05,r*math.sin(a),0)));top.append(bm.verts.new((r*.72*math.cos(a)*1.05,r*.72*math.sin(a),.007)))
    c0=bm.verts.new((0,0,.0085))
    for i in range(NA):
        j=(i+1)%NA;bm.faces.new((ring[i],ring[j],top[j],top[i]));bm.faces.new((top[i],top[j],c0))
    bm.faces.new(list(reversed(ring)));bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    finish('GC04_Earth',bm,M['soil'],'Body',.2)
    def z_e(x,y):   # the earth patch height at (x, y): its outline wobbles with the angle
        a=math.atan2(y,x/1.05);ro=.128+.012*math.sin(3*a+1)+.008*math.sin(7*a);rt=.72*ro;r=math.hypot(x/1.05,y)
        return .007*min(1,max(0,(ro-r)/(ro-rt))) if r>rt else .007+.0015*(1-r/rt)
    placed=[]
    for k in range(13):   # leaves: a lens outline, a little curled, each lying on the earth or draped over the leaves under it (2.6 mm apart: no two in one plane)
        a=rr.uniform(0,math.tau);d=rr.uniform(.02,.13);cx,cy=d*math.cos(a)*1.05,d*math.sin(a);ang=rr.uniform(0,math.tau);L=rr.uniform(.045,.07);W=L*rr.uniform(.4,.55)
        dv=Vector((math.cos(ang),math.sin(ang),0));sv=Vector((-dv.y,dv.x,0));rows=[]
        for u in np.linspace(0,1,6):
            w=max(.002,W*math.sin(math.pi*min(1,u*1.02))**.8);row=[]
            for v in np.linspace(-1,1,4):
                p=Vector((cx,cy,0))+dv*(u-.5)*L+sv*v*w/2;z=z_e(p.x,p.y)+.003+.004*v*v+.002*math.sin(u*5+k)
                for q in placed:
                    if (q.x-p.x)**2+(q.y-p.y)**2<.022**2:z=max(z,q.z+.003)
                p.z=z;row.append(p)
            rows.append(row)
        placed+=[p for r in rows for p in r];rows=[[tuple(p) for p in r] for r in rows]
        _sheet(f'GC04_Leaf{k}',rows,None,None,M['leaf_brown' if k%3 else 'leaf_dry'],'Detail_Leaves',t=.0012)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        for cx,cy,zu,R in CAPS:
            r=np.hypot(px-cx,py-cy);under=filled*(r<R*1.02)*(onrm[...,2]<-.2)*(np.abs(pz-zu)<.02)
            th=np.arctan2(py-cy,px-cx);g=.5+.5*np.sin(th*int(R*1400))   # gills: fine radial lines
            col=col*(1-.25*(under*g)[...,None])
            top=filled*(r<R*1.05)*(onrm[...,2]>.2)*(pz>zu-.01)   # the cap darker in the middle, paler at the rim
            col=col*(1-.18*(top*np.clip(1-r/R,0,1))[...,None])
        dirt=filled*np.clip((.03-pz)/.025,0,1)*np.clip((noise-.3)*2,0,1)   # earth splashed up the stems
        col=col*(1-.4*dirt[...,None])+dirt[...,None]*np.array([.18,.13,.08])*.4
        return col,rough
    return {'paint':paint,'wear':.5,'grime':.7,'uv_angle':50,'notes':['seven ordinary non-glowing mushrooms 1.2–12.5 cm high on a low earth patch; two caps with a piece broken out of the rim',
            'cap: a lathe shell with the gill plane under it (gills painted as radial lines), stem bent a little, thicker and dirty at the foot',
            'Detail_Leaves: thirteen fallen leaves lying on the earth']}
PROPS['GC04']=GC04

def _shelf(name,base,a,b,th,mat,grp,droop=.004,NT=13,NR=6,scale=.08):
    """one bracket-fungus shelf: a half disc growing out of the bark towards -Y (a = half width along X, b = reach),
    thick at the bark (th) and thin at the rim, the top a little domed and the rim drooping; its straight back edge sits
    a centimetre inside the log"""
    bm=bmesh.new();T=[];B=[];base=Vector(base)
    for i in range(NT):
        th_=math.pi*i/(NT-1);c,s=math.cos(th_),math.sin(th_);rt=[];rb=[]
        for j in range(NR):
            r=j/(NR-1);x=a*r*c;y=-b*r*s-.012*(1-r);t_=th*(1-r)**.8+.0018;dz=-droop*r**2+.002*math.sin(th_*5)*r
            rt.append(bm.verts.new(base+Vector((x,y,dz+t_*.6))));rb.append(bm.verts.new(base+Vector((x,y,dz-t_*.4))))
        T.append(rt);B.append(rb)
    for i in range(NT-1):
        for j in range(NR-1):
            bm.faces.new((T[i][j],T[i][j+1],T[i+1][j+1],T[i+1][j]));bm.faces.new((B[i][j],B[i+1][j],B[i+1][j+1],B[i][j+1]))
        bm.faces.new((T[i][NR-1],B[i][NR-1],B[i+1][NR-1],T[i+1][NR-1]))   # the rim
    for k in (0,NT-1):   # the two ends of the half disc (inside the bark)
        for j in range(NR-1):bm.faces.new((T[k][j],B[k][j],B[k][j+1],T[k][j+1]))
    bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-6)
    hole=[e for e in bm.edges if e.is_boundary]
    if hole:bmesh.ops.edgeloop_fill(bm,edges=hole)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)

# ---------------- GC05 a mossy fallen-log section with layered bracket fungi (cand-4) ----------------
def GC05(M):
    """a short section of an old fallen log (taller than deep, as split and settled; the work pack's 0.2 m depth), dark
    wet bark with a strip broken off showing the pale rotten wood, both cut ends crumbling and hollowed; moss over the
    top with a few small plants; on the front two clusters of half-round bracket fungi stacked one over another (smaller
    going up), cream rims and concentric brown bands painted."""
    rr=random.Random(505);L=.19;RY=.072;RZ=.096;ZC=.096;NS=30;NX=22
    def ring(x,shrink=1.):
        pts=[]
        for k in range(NS):
            t=math.tau*k/NS;n=1+.05*math.sin(3*t+x*20)+.03*math.sin(7*t+1.7)+.02*math.sin(11*t+x*40)
            y=RY*math.cos(t)*n*shrink;z=ZC+RZ*math.sin(t)*n*shrink;z=max(z,.0)   # resting on the ground: flat underneath
            pts.append(Vector((x,y,z)))
        return pts
    bm=bmesh.new();R_=[]
    for i in range(NX):
        u=i/(NX-1);x=-L+2*L*u
        pts=ring(x)
        if i in (0,NX-1):   # ragged crumbling ends
            sg=-1 if i==0 else 1;pts=[p+Vector((sg*(.012*math.sin(5*k+i)+.008*math.sin(13*k)),0,0)) for k,p in enumerate(pts)]
        R_.append([bm.verts.new(p) for p in pts])
    for a_,b_ in zip(R_,R_[1:]):
        for k in range(NS):bm.faces.new((a_[k],b_[k],b_[(k+1)%NS],a_[(k+1)%NS]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    E0,E1=[v.co.copy() for v in R_[0]],[v.co.copy() for v in R_[-1]]   # the end rings (the bmesh is freed by finish)
    finish('GC05_Bark',bm,M['bark'],'Body',.3)
    for sg,R0 in ((-1,E0),(1,E1)):   # the cut ends: rotten wood, hollowed towards the middle
        bm=bmesh.new();rv=[bm.verts.new(v) for v in R0];mid=[bm.verts.new(Vector((v.x-sg*.018,v.y*.55,ZC+(v.z-ZC)*.55))) for v in R0]
        c=bm.verts.new(Vector((R0[0].x-sg*.032,0,ZC)))
        for k in range(NS):
            j=(k+1)%NS;bm.faces.new((rv[k],rv[j],mid[j],mid[k]));bm.faces.new((mid[k],mid[j],c))
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        for f in bm.faces:f.smooth=True
        finish(f'GC05_End{"LR"[sg>0]}',bm,M['stumpwood'],'Body',.2)
    def surf(x,t,off=0.):   # a point on the log surface (approximate: the same wobble as ring())
        n=1+.05*math.sin(3*t+x*20)+.03*math.sin(7*t+1.7)+.02*math.sin(11*t+x*40)
        return Vector((x,(RY+off)*math.cos(t)*n,ZC+(RZ+off)*math.sin(t)*n))
    # moss over the top, a thin layer with ragged edges, and small plants in it
    rows=[]
    for x in np.linspace(-L+.015,L-.015,16):
        t0=math.radians(50+10*math.sin(x*30));t1=math.radians(150+12*math.sin(x*23+1))
        rows.append([tuple(surf(x,t,.0045)) for t in np.linspace(t0,t1,9)])
    _sheet('GC05_Moss',rows,None,None,M['moss'],'Body',t=.004)
    for k in range(6):
        x=rr.uniform(-L+.04,L-.04);t=math.radians(rr.uniform(70,110));p=surf(x,t,.006)
        _tuft_even(f'GC05_Plant{k}',p,M['grass'],'Detail_Plants',rr,n=rr.randint(3,5),h=rr.uniform(.03,.055))
    # bracket fungi: two clusters on the front (-Y), stacked, smaller going up
    SH=[]
    for cx,stack in ((-.055,[(.072,.068,.050),(.095,.056,.042),(.116,.045,.034),(.135,.034,.026),(.152,.024,.019)]),(.095,[(.058,.050,.038),(.080,.039,.030),(.100,.028,.022)])):
        for j,(z,a,b) in enumerate(stack):
            x=cx+.008*math.sin(j*2.1);yb=-(RY*math.sqrt(max(.05,1-((z-ZC)/RZ)**2)))+.010   # the log's front surface at that height, the shelf's back a centimetre inside
            _shelf(f'GC05_Shelf{len(SH)}',(x,yb,z),a,b,.012 if a>.04 else .009,M['fungus'],'Body',droop=.004*a/.05)
            SH.append((x,yb,z,a,b))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        for x,yb,z,a,b in SH:   # concentric bands on the shelves, the rim cream
            r=np.hypot((px-x)/a,(py-yb)/b);on=filled*(r<1.05)*(np.abs(pz-z)<.014)*(py<yb-.009)*(np.abs(onrm[...,2])>.35)   # shelf faces only (the bark behind faces -Y)
            band=.5+.5*np.sin(r*26+noise);col=np.where(on[...,None]>0,col*(.82+.3*band[...,None])*np.array([1.,.92,.85])*(1-.25*(r<.5)[...,None])+np.clip((r-.82)*5,0,1)[...,None]*np.array([.20,.18,.14]),col)
        strip=filled*(np.abs(px+.02)<.09)*(py>.03)*(pz>.05)*(pz<.17)*(np.sin(px*9+pz*14+noise)>.2)   # a strip of bark broken off on the back: pale rotten wood
        col=np.where(strip[...,None]>0,col*.4+np.array([.42,.33,.23])*.6,col)
        wet=filled*np.clip((.05-pz)/.05,0,1);col=col*(1-.25*wet[...,None])   # damp at the foot
        return col,rough
    return {'paint':paint,'wear':.6,'grime':.9,'uv_angle':50,'notes':['a fallen-log section 0.38 m long, taller than deep (the 0.2 m depth limit), ragged hollowed rotten ends, moss over the top (Detail_Plants: small plants in it)',
            'two clusters of half-round bracket fungi stacked on the front, each shelf thick at the bark and thin at the rim, its back edge inside the bark; concentric bands painted']}
PROPS['GC05']=GC05

def _drop(o,placed,start=2.):
    """lower the object straight down until it rests on the ground (z = 0) or on what is already placed: the smallest
    gap found by rays down from its vertices and rays up from the placed vertices under it; sinks 0.5 mm so they touch"""
    from mathutils.bvhtree import BVHTree
    me=o.data;me.transform(Matrix.Translation((0,0,start)))
    V=[v.co.copy() for v in me.vertices];F=[tuple(p.vertices) for p in me.polygons]
    d=min(v.z for v in V);sup=min(V,key=lambda v:v.z).copy()
    if placed['V']:
        T=BVHTree.FromPolygons(placed['V'],placed['F'])
        for v in V:
            h=T.ray_cast(v+Vector((0,0,1e-4)),Vector((0,0,-1)))
            if h[0] is not None and h[3]<d:d=h[3];sup=v.copy()
        N=BVHTree.FromPolygons(V,F);lo=Vector((min(v.x for v in V),min(v.y for v in V)));hi=Vector((max(v.x for v in V),max(v.y for v in V)))
        for p in placed['V']:
            if lo.x<=p.x<=hi.x and lo.y<=p.y<=hi.y:
                h=N.ray_cast(p-Vector((0,0,1e-4)),Vector((0,0,1)))
                if h[0] is not None and h[3]<d:d=h[3];sup=p.copy()
    me.transform(Matrix.Translation((0,0,-(d+.0005))));me.update()
    b=len(placed['V']);placed['V']+=[v.co.copy() for v in me.vertices];placed['F']+=[tuple(b+i for i in p.vertices) for p in me.polygons]
    return sup

def _flush(o,placed,ang=12.,dist=.0034):
    """True when a face of o lies within dist of the plane of a placed face turned the same way (within ang degrees)
    and close by: the QA reads such pairs as coplanar"""
    from mathutils.kdtree import KDTree
    if not placed['F']:return False
    V=placed['V'];C=[];N=[]
    for f in placed['F']:
        a,b,c=V[f[0]],V[f[1]],V[f[2]];n=(b-a).cross(c-a)
        if n.length<1e-12:continue
        C.append((a+b+c)/3);N.append(n.normalized())
    kd=KDTree(len(C))
    for i,c in enumerate(C):kd.insert(c,i)
    kd.balance();ca=math.cos(math.radians(ang))
    for p in o.data.polygons:
        c=Vector(p.center);n=Vector(p.normal)
        for _,i,d in kd.find_range(c,.07):
            if n.dot(N[i])>ca and abs((c-C[i]).dot(N[i]))<dist:return True
    return False

def _settle(objs,ground_obj,frames=260):
    """let the rocks fall and come to rest with Blender's rigid-body solver (convex hulls, 0.5 mm margin, high friction):
    the earth patch and a ground slab are passive; afterwards each rock's resting transform is baked into its mesh"""
    sc=bpy.context.scene;sel(*objs);bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='BOUNDS')
    if sc.rigidbody_world is None:bpy.ops.rigidbody.world_add()
    W=sc.rigidbody_world;W.point_cache.frame_start=1;W.point_cache.frame_end=frames;W.substeps_per_frame=20;W.solver_iterations=30
    slab=bpy.data.objects.new('GC_GroundSlab',bpy.data.meshes.new('GC_GroundSlab'));sc.collection.objects.link(slab)
    bm=box_bm((6,6,.2),(0,0,-.1));bm.to_mesh(slab.data);bm.free()
    for o,act in [(slab,False),(ground_obj,False)]+[(o,True) for o in objs]:
        sel(o);bpy.ops.rigidbody.object_add(type='ACTIVE' if act else 'PASSIVE');rb=o.rigid_body
        rb.collision_shape='CONVEX_HULL' if act else ('BOX' if o is slab else 'MESH');rb.collision_margin=.0005;rb.friction=.95;rb.restitution=0.
        if act:
            d=o.dimensions;rb.mass=max(.05,2600*d.x*d.y*d.z*.5);rb.linear_damping=.35;rb.angular_damping=.6
    for f in range(1,frames+1):sc.frame_set(f)
    mws={o:o.matrix_world.copy() for o in objs}
    for o in objs+[slab,ground_obj]:sel(o);bpy.ops.rigidbody.object_remove()
    for o in objs:o.matrix_world=Matrix.Identity(4);o.data.transform(mws[o])
    bpy.data.objects.remove(slab);sc.frame_set(1)

# ---------------- GC06 a small natural pile of fallen rocks (cand-4) ----------------
def GC06(M):
    """twenty-odd angular rocks and a few rounded ones resting on each other at the foot of a slope: the big ones first,
    smaller ones dropped on and between them, each lowered until it rests on the ground or on a stone already there (no
    stone passes into another, none hangs in the air); a low spread of earth under the pile, gravel and grass between
    the lower stones (Detail_), fresh pale breaks on the top stones."""
    rr=random.Random(606);placed={'V':[],'F':[]};TOPS=[]
    def sel(*obs):
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:o.select_set(True)
        bpy.context.view_layer.objects.active=obs[0]
    bm=bmesh.new();NA=40;ring=[];top=[]   # the earth spread under the pile
    for i in range(NA):
        a=math.tau*i/NA;r=1+.06*math.sin(3*a+1)+.04*math.sin(5*a+2)
        ring.append(bm.verts.new((.56*r*math.cos(a),.46*r*math.sin(a),0)));top.append(bm.verts.new((.44*r*math.cos(a),.36*r*math.sin(a),.010)))
    c0=bm.verts.new((0,0,.012))
    for i in range(NA):
        j=(i+1)%NA;bm.faces.new((ring[i],ring[j],top[j],top[i]));bm.faces.new((top[i],top[j],c0))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)   # no underside: it lies on the ground and is never seen (a rock resting at z = 0 lay in one plane with it)
    for f in bm.faces:f.smooth=True
    E=finish('GC06_Earth',bm,M['soil'],'Body',.3);placed['V']+=[v.co.copy() for v in E.data.vertices];placed['F']+=[tuple(p.vertices) for p in E.data.polygons]
    ST=[('a',(.44,.36,.30),.00,.02),('a',(.40,.32,.26),-.22,-.10),('a',(.36,.30,.24),.24,.06),('r',(.24,.20,.17),-.05,-.24),('a',(.30,.24,.20),.10,.24),
        ('a',(.26,.22,.18),-.30,.16),('a',(.28,.20,.16),.34,-.18),('r',(.20,.18,.15),.42,.14),('a',(.22,.18,.16),-.42,-.08),('a',(.24,.18,.15),.05,-.02),
        ('a',(.20,.16,.14),-.12,.08),('a',(.18,.15,.14),.16,-.08),('r',(.16,.14,.12),-.30,-.28),('a',(.16,.13,.12),.28,.28),('a',(.15,.12,.11),.02,.12),
        ('a',(.14,.12,.10),-.06,-.12),('a',(.13,.11,.10),.12,.04),('r',(.13,.12,.10),-.46,.24),('a',(.12,.10,.09),.46,-.30),('a',(.12,.10,.09),-.18,.30),
        ('a',(.11,.09,.08),.20,-.30),('a',(.10,.09,.08),-.02,.02),('a',(.10,.08,.08),.36,.00),('a',(.09,.08,.07),-.34,.00)]
    for k,(kind,sz,x,y) in enumerate(ST):
        if kind=='a':o,br=_shard(f'GC06_Rock{k:02d}',sz,600+k,M['rock'],'Body',npts=rr.randint(22,32),flat=0.,bev=0)   # no bevel in the pile: its corners folded into slivers where 30 break edges met
        else:o=_blob(f'GC06_Round{k:02d}',sz,600+k,M['field'],'Body',flats=2,amp=.08);br=[]
        tl=.04 if k<3 else .16;me0=o.data.copy();best=None
        for tries in range(10):   # a turn of the stone where none of its faces lies flush with a neighbour's
            R=Matrix.Rotation(rr.uniform(0,math.tau),4,'Z')@Matrix.Rotation(rr.uniform(-tl,tl),4,'X')@Matrix.Rotation(rr.uniform(-tl,tl),4,'Y')
            px_,py_=x*.85,y*.85
            for slide in range(24):   # it rolls off a lone support point: slide away from it until it settles in a hollow (or on the ground)
                o.data=me0.copy();o.data.transform(R);o.data.transform(Matrix.Translation((px_,py_,0)))
                trial={'V':list(placed['V']),'F':list(placed['F'])};sp=_drop(o,trial)
                co=[v.co for v in o.data.vertices];c=sum(co,Vector())/len(co);off=Vector((c.x-sp.x,c.y-sp.y))
                if sp.z<.015 or off.length<.18*min(sz[0],sz[1]) or math.hypot(px_,py_)>.42:break   # settled, on the ground, or at the pile's edge
                px_+=off.normalized().x*.02;py_+=off.normalized().y*.02
            best=(trial,R)
            if not _flush(o,placed):break
        else:print('GC06_FLUSH_LEFT',o.name)
        placed['V'],placed['F']=best[0]['V'],best[0]['F'];R=best[1]
        zt=max(v.co.z for v in o.data.vertices);TOPS.append((x,y,zt,[R.to_3x3()@b for b in br]))
    for k in range(60):   # gravel round the lower stones, each dropped the same way (Detail_)
        a=rr.uniform(0,math.tau);d=rr.uniform(.30,.55);sz=(rr.uniform(.02,.045),rr.uniform(.016,.035),rr.uniform(.012,.025))
        o,_=_shard(f'GC06_Gravel{k:02d}',sz,700+k,M['rock'],'Detail_Gravel',npts=10,bev=0,ripple=0.,flat=0.);me0=o.data.copy()
        for tries in range(14):   # in the gaps at the foot of the pile: retry where it would land on top of a rock or flush with a face
            a=rr.uniform(0,math.tau) if tries else a;d=rr.uniform(.30,.55) if tries else d
            o.data=me0.copy();o.data.transform(Matrix.Rotation(rr.uniform(0,math.tau),4,'Z')@Matrix.Rotation(rr.uniform(-.5,.5),4,'X'));o.data.transform(Matrix.Translation((d*math.cos(a)*1.02,d*.82*math.sin(a),0)))
            trial={'V':list(placed['V']),'F':list(placed['F'])};_drop(o,trial)
            if max(v.co.z for v in o.data.vertices)<.07 and not _flush(o,placed):break
        placed['V'],placed['F']=trial['V'],trial['F']
    for k in range(16):   # grass between the lower stones
        a=rr.uniform(0,math.tau);d=rr.uniform(.36,.5);p=Vector((d*math.cos(a),d*.82*math.sin(a),0))
        from mathutils.bvhtree import BVHTree
        T=BVHTree.FromPolygons(placed['V'],placed['F']);h=T.ray_cast(p+Vector((0,0,1)),Vector((0,0,-1)))
        if h[0] is None or h[0].z>.05:continue
        _tuft_even(f'GC06_Grass{k:02d}',h[0]-Vector((0,0,.003)),M['grass'],'Detail_Grass',rr,n=rr.randint(3,5),h=rr.uniform(.05,.09))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        for x,y,zt,br in TOPS:
            if zt<.30:continue
            on=filled*(np.hypot(px-x,py-y)<.2)*(pz>zt-.15)
            for b in br:
                fr=on*np.clip((onrm[...,0]*b.x+onrm[...,1]*b.y+onrm[...,2]*b.z-.93)*20,0,1)
                col=col*(1-.5*fr[...,None])+fr[...,None]*np.array([.72,.67,.60])*.5
        dirt=filled*np.clip((.10-pz)/.09,0,1)*np.clip((noise-.35)*2,0,1)   # earth splashed on the lower stones
        col=col*(1-.35*dirt[...,None])+dirt[...,None]*np.array([.20,.15,.10])*.35
        dust=filled*np.clip((cav-.5)*3,0,1);col=col*(1-.25*dust[...,None])
        mo=filled*np.clip(onrm[...,2],0,1)*np.clip((noise-.62)*4,0,1)*np.clip((.25-pz)/.2,0,1);col=col*(1-.4*mo[...,None])+mo[...,None]*np.array([.12,.17,.05])*.4
        return col,rough
    return {'paint':paint,'wear':.6,'grime':.8,'uv_angle':40,'collision':'box: body_dimensions centred on the footprint (or a convex hull); the pile stands in the way, so standard tier',
            'notes':['24 rocks (20 angular, 4 rounded), big ones first; each lowered until it rests on the ground or on a stone already placed (rays down from its vertices and up from the stones under it): none passes into another, none hangs',
                     'a low earth spread under the pile; Detail_Gravel: 60 small chips dropped the same way; Detail_Grass: grass between the lower stones; fresh pale breaks on the top stones painted']}
PROPS['GC06']=GC06
