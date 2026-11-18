# C 路邊小物（wayside-c）WS05 稻草堆與稻束. Blender: X = width, -Y = front, Z = up; origin: footprint centre, bottom z = 0.

def _hank(name,pts,w,t,mat,grp,roll=0.,nside=6,scale=.15,upf=None):
    """a flat hank of straw lying along pts: an elliptic tube w wide and t thick, its flat side down"""
    pts=[Vector(p) for p in pts];bm=bmesh.new();rings=[];Z=Vector((0,0,1));n=len(pts)
    for i,p in enumerate(pts):
        tg=(pts[min(i+1,n-1)]-pts[max(i-1,0)]).normalized();U=upf(p) if upf else Z;sd=tg.cross(U).normalized();up=sd.cross(tg).normalized()   # upf: the surface normal it lies on
        f=math.sin(math.pi*(i+.5)/n)**.35   # thin at both ends
        rings.append([bm.verts.new(p+sd*math.cos(math.tau*k/nside+roll)*w/2*f+up*math.sin(math.tau*k/nside+roll)*t/2*f) for k in range(nside)])
    for a,b in zip(rings,rings[1:]):
        for k in range(nside):bm.faces.new((a[k],a[(k+1)%nside],b[(k+1)%nside],b[k]))
    bm.faces.new(list(reversed(rings[0])));bm.faces.new(rings[-1])
    for f_ in bm.faces:f_.smooth=True
    return finish(name,bm,mat,grp,scale)

# ---------------- WS05_01 low heap of threshed rice straw (cand-1) ----------------
def WS05_01(M):
    """a low, lopsided heap of threshed rice straw, made the way VG04's haystack is (yard-roadside-c): a solid core and four
    overlapping skirts of straw lying over it, their lower rims jagged in the shape, each askew and a few centimetres
    out from the one under it (no two share a plane), straws hanging out from under every rim, a loose lump thrown on top; no alpha cards. Stray stalks sticking out are Detail_Stalks. The heap is squeezed to 0.85 in depth."""
    rr=random.Random(int(__import__('os').environ.get('WS_SEED',9505)));NS=44;ph=[rr.uniform(0,6.28) for _ in range(6)];HAY=M['hay'];OLD=M['hay_old'];parts0=len(parts)
    ZP=[0,.10,.24,.38,.49,.56,.60];RP_=[.70,.70,.62,.48,.32,.16,.03]
    def Rf(th,z):
        r=float(np.interp(z,ZP,RP_));return r*(1+.07*math.sin(2*th+ph[0])+.05*math.sin(3*th+ph[1]+z*3)+.03*math.sin(5*th+ph[2]-z*5))
    def surf(name,zs,rfun,mat,grp,close=None,vscale=.4):
        bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');R_=[]
        for i in range(len(zs)):
            ring=[]
            for k in range(NS):
                th=math.tau*k/NS;z=zs[i](th,k) if callable(zs[i]) else zs[i];r=rfun(th,z,i,k);ring.append(bm.verts.new((r*math.cos(th),r*math.sin(th),z)))
            R_.append(ring)
        du=rr.random();dv=rr.random()
        for i in range(len(zs)-1):
            for k in range(NS):
                q=(R_[i][k],R_[i][(k+1)%NS],R_[i+1][(k+1)%NS],R_[i+1][k]);f=bm.faces.new(q);f.smooth=True
                for l,(kk,ii) in zip(f.loops,((k,i),(k+1,i),(k+1,i+1),(k,i+1))):
                    v=R_[ii][kk%NS].co;l[lay].uv=(kk/NS*4.4/vscale*.5+du,-v.z/vscale+dv+.25*Vector((v.x,v.y)).length/vscale)
        if close:
            if 'top' in close:
                c=bm.verts.new((0,0,max(v.co.z for v in R_[0])+.02))
                for k in range(NS):bm.faces.new((c,R_[0][(k+1)%NS],R_[0][k]))
            if 'bottom' in close:bm.faces.new(list(R_[-1]))
        RC=[[v.co.copy() for v in ring] for ring in R_];return finish(name,bm,mat,grp,vscale,keep_uv=True),RC
    surf('WS05_01_Core',[.60,.55,.47,.36,.24,.12,.0],lambda th,z,i,k:max(.03,Rf(th,z)-.03),OLD,'Body',close=('top','bottom'))
    LAY=[(.30,.012),(.43,.15),(.51,.29),(.555,.41)]
    for q,(zt,zb) in enumerate(LAY):
        jz=[rr.uniform(-.06,.03) for _ in range(NS)];jr=[rr.uniform(0,.09) for _ in range(NS)];low=q==0;tp=rr.uniform(0,6.28);ta=rr.uniform(.04,.08)
        def zrow(s,zt=zt,zb=zb,jz=jz,low=low,tp=tp,ta=ta):return (lambda th,k:zt+(zb-.05*(not low)-zt)*s+(jz[k]*s*s if not low else abs(jz[k])*.3*s*s)+(ta*math.sin(th+tp)+.02*math.sin(3*th+tp*2))*(0. if low else 1.))
        def rfun(th,z,i,k,q=q,jr=jr,tp=tp):s_=i/4;return Rf(th,z)+.010-.06*(1-s_)**2+(.07+.03*math.sin(2*th+tp))*s_*s_+jr[k]*s_*s_+(.03 if q%2 else 0)
        o,RC=surf(f'WS05_01_Skirt{q}',[zrow(s_) for s_ in (0,.25,.5,.75,1.)],rfun,HAY if q%2==0 else M['straw'],'Body')
        rim=RC[-1];row=RC[-2]
        for k in range(1,NS,1 if q==0 else 2):   # straws hanging out from under the rim, each its own way: the ragged edge, in the shape (no alpha cards)
            a_=rim[k];inn=row[k];out=Vector((a_.x,a_.y,0)).normalized();sd=Vector((-out.y,out.x,0));L=rr.uniform(.08,.18)
            dv=(out*rr.uniform(.4,1.)+sd*rr.uniform(-.5,.5)+Vector((0,0,-rr.uniform(.4,1.2)))).normalized();st=inn.lerp(a_,.55) if q else a_.copy()   # the lowest skirt lies almost on the ground: its straws start at the rim itself, not along the skirt
            e=a_+dv*L;e.z=max(e.z,.006+.0007*k)
            _taper(f'WS05_01_Hang{q}{k:02d}',[st,a_+dv*L*.35,e],[.0040,.0034,.0012],HAY,'Body',sides=3,scale=.1,up=(rr.uniform(-1,1),rr.uniform(-1,1),.6))
    o=_blob('WS05_01_Top',(.40,.34,.15),9531,OLD,'Body',sub=3,scale=.3,bumps=9,amp=.26,flats=0,bottom=.45);o.data.transform(Matrix.Translation((.04,-.02,.47)))   # a loose lump of straw thrown on top
    for k in range(30):   # Detail_Stalks: stray stalks standing out of the skirts
        th=rr.uniform(0,math.tau);z=rr.uniform(.08,.52);r=Rf(th,z)+.03;p=Vector((r*math.cos(th),r*math.sin(th),z));out=Vector((math.cos(th),math.sin(th),0));L=rr.uniform(.14,.30);sd=Vector((-out.y,out.x,0))*rr.uniform(-.5,.5)
        _taper(f'WS05_01_Stalk{k:02d}',[p-out*.15,p+out*L*.35+sd*L*.2-Vector((0,0,L*.15)),p+out*L*.6+sd*L*.45-Vector((0,0,min(L*.5,z*.8)))],[.0042,.0034,.0012],HAY,'Detail_Stalks',sides=3,scale=.1,up=(rr.uniform(-1,1),rr.uniform(-1,1),.4))
    for o in parts[parts0:]:o.data.transform(Matrix.Scale(.85,4,Vector((0,1,0))))   # oval: 0.85 as deep as wide
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);pz=P[...,2]
        gy=filled*np.clip((_fb(P,(3.,3.,3.),9520,2)-.42)*2.5,0,1);col=col*(1-.30*gy[...,None])+gy[...,None]*.30*np.array([.55,.52,.44])   # grey, rained-on straw among the golden
        dk=filled*np.clip((.10-pz)/.10,0,1)*np.clip(.35+noise,0,1);col=col*(1-.35*dk[...,None])+dk[...,None]*.35*np.array([.30,.25,.17])   # damp and darker near the ground
        return col,rough
    return {'paint':paint,'wear':.2,'grime':.6,'ao_k':.6,'uv_angle':66,'collision_box':((1.1,.9,.45),(0,0,.225)),'collision':'one low box in the middle of the heap',
            'notes':['a low lopsided heap of threshed rice straw about 1.5 × 1.25 × 0.6 m, built the way VG04 is: a solid core and four overlapping skirts of straw with rims jagged in the shape, each askew and a few centimetres out from the one under it; straws hang out from under every rim (the ragged edge in the shape, no alpha cards); a loose lump of straw thrown on top',
                     'Detail_Stalks (30 stray stalks sticking out) is off at the standard tier',
                     'golden and grey rained-on straw, damp and darker near the ground, painted; the paving slab and the field of the three-view are left out']}
PROPS['WS05_01']=WS05_01

# ---------------- WS05_02 three rice sheaves standing (cand-1) ----------------
def _sheaf(pid,k,M,rr,c,H,n=64):
    """one sheaf of rice straw standing to dry: straws from a ring at the foot through the tied waist up to drooping heads;
    each straw keeps its place in the bundle (foot, waist and top radius in proportion) so none crosses another"""
    zw=H*rr.uniform(.48,.54);rw=.052;rf=.17;rt=.085;ph=rr.uniform(0,6.28);tl=Vector((rr.uniform(-.03,.03),rr.uniform(-.03,.03),0))
    for i in range(n):
        q=math.sqrt((i+.5)/n);a=i*2.39996+ph   # sunflower order in the waist
        dw=Vector((math.cos(a),math.sin(a),0))
        foot=c+dw*(.012+rf*q*rr.uniform(.92,1.04))+Vector((0,0,-.004));waist=c+dw*(rw*q)+Vector((0,0,zw))+tl
        top=c+dw*(rt*q*rr.uniform(.9,1.1))+Vector((0,0,H*rr.uniform(.92,1.0)))+tl*1.6
        rs=rr.uniform(.0019,.0026)
        pts=[foot,foot.lerp(waist,.5)+dw*.006*q,waist,waist.lerp(top,.5)+dw*.004*q,top]
        _ttube(f'{pid}_S{k}{i:02d}',pts,[rs*1.1,rs,rs*.9,rs*.85,rs*.7],M['straw'],'Body',sides=3,scale=.06,roll=rr.uniform(0,6.28))
        if q>.35 and rr.random()<.75:   # the head: a drooping panicle of grain over the outside
            o=(dw*(.6+.4*q)+Vector((0,0,.35))).normalized();Lh=rr.uniform(.10,.16)
            hp=[top-o*.004,top+o*Lh*.4+Vector((0,0,.01)),top+o*Lh*.75-Vector((0,0,Lh*.25)),top+o*Lh-Vector((0,0,Lh*.6))]
            _ttube(f'{pid}_H{k}{i:02d}',hp,[rs*.9,.0060,.0055,.0022],M['grain'],'Body',sides=4,scale=.05,roll=rr.uniform(0,6.28))
    for j in range(2):   # two turns of straw rope round the waist, riding past their start
        z=zw+.012*(j-.5);N=22;r_=rw+.004;path=[c+tl+Vector((r_*math.cos(math.tau*1.1*s/N+ph),r_*math.sin(math.tau*1.1*s/N+ph),z+.009*s/N)) for s in range(N+1)]
        _ttube(f'{pid}_Tie{k}{j}',path,[.0055]*len(path),M['straw'],'Body',sides=5,scale=.08,roll=rr.uniform(0,6.28))

def WS05_02(M):
    """three sheaves of rice straw standing in a row to dry, each tied at the waist with two turns of straw rope, spread out
    at the foot like a small tent, the grain heads drooping over the top"""
    rr=random.Random(int(__import__('os').environ.get('WS_SEED',9551)))
    for k,(x,y,H) in enumerate(((-.34,.02,.86),(0.,-.03,.92),(.33,.04,.84))):_sheaf('WS05_02',k,M,rr,Vector((x,y,0)),H)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);pz=P[...,2]
        dk=filled*np.clip((.10-pz)/.10,0,1);col=col*(1-.35*dk[...,None])+dk[...,None]*.35*np.array([.32,.26,.16])
        gy=filled*np.clip((_fb(P,(5.,5.,3.),9560,2)-.55)*3,0,1);col=col*(1-.25*gy[...,None])+gy[...,None]*.25*np.array([.56,.52,.42]);return col,rough
    return {'paint':paint,'wear':.2,'grime':.4,'ao_k':.5,'uv_angle':60,
            'notes':['three sheaves of rice straw standing in a row: 64 straws each, from a ring at the foot through the tied waist to the top, each straw keeping its place in the bundle so none crosses another',
                     'two turns of straw rope round each waist; drooping grain heads over the outside of the top; can be placed one row at a time along a paddy edge (A6)',
                     'damp, darker feet and some greyed straw, painted; no collision']}
PROPS['WS05_02']=WS05_02
