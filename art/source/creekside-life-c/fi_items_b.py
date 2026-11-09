# FI02–FI05 shapes (FI01 and _cane are in fi_items.py), read by build_wl.py after fi_items.py.
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = length, -Y = front, Z = up.

def _rod(name,a,b,r,mat,grp,sides=10,scale=.2):
    return tube(name,[Vector(a),Vector(b)],r,mat,grp,sides=sides,scale=scale)
def _lathe(name,prof,axis_pts,mat,grp,NS=24,scale=.2,loop=False):
    """a solid of revolution along the axis axis_pts[0] → axis_pts[1]; prof = [(s, r)] with s in 0..1.
    loop=False: an r of 0 at either end closes it with a point (else a flat cap); loop=True: the profile is a closed loop
    (a ring with a bore: outside, end, bore, other end) and the last section joins the first."""
    A,B=Vector(axis_pts[0]),Vector(axis_pts[1]);ax=(B-A);L=ax.length;d=ax.normalized();u=d.orthogonal().normalized();v=d.cross(u)
    bm=bmesh.new();rings=[];pts=[]
    for s,r in prof:
        c=A+d*(L*s)
        if r<=1e-6:rings.append(None);pts.append(bm.verts.new(c));continue
        rings.append([bm.verts.new(c+(u*math.cos(math.tau*k/NS)+v*math.sin(math.tau*k/NS))*r) for k in range(NS)]);pts.append(None)
    seq=[r for r in rings if r]
    pairs=list(zip(seq,seq[1:]))+([(seq[-1],seq[0])] if loop else [])
    for a,b in pairs:
        for k in range(NS):bm.faces.new((a[k],a[(k+1)%NS],b[(k+1)%NS],b[k]))
    if not loop:
        if rings[0] is None:[bm.faces.new((pts[0],seq[0][(k+1)%NS],seq[0][k])) for k in range(NS)]
        else:bm.faces.new(list(reversed(seq[0])))
        if rings[-1] is None:[bm.faces.new((pts[-1],seq[-1][k],seq[-1][(k+1)%NS])) for k in range(NS)]
        else:bm.faces.new(seq[-1])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)
def _ring(name,c,ax,r,cord,mat,grp,n=17,wob=0.,floor=None):
    """a cord loop of radius r round the axis ax through c. It runs on past its start and rides up over it (a cord
    wrapped round once): cap to cap, or the same path twice, lay in one plane. floor: no point below this height
    (a binding squeezed flat under something lying on the ground)."""
    ax=Vector(ax).normalized();u=ax.orthogonal().normalized();v=ax.cross(u);c=Vector(c);pts=[]
    for q in np.linspace(0,math.tau+.5,n+3):
        ramp=min(1,max(0,(q-math.tau+.15)/.5));rr=r+cord*.8*ramp
        p=c+ax*(wob*math.sin(3*q)+cord*2.2*ramp)+(u*math.cos(q)+v*math.sin(q))*rr   # the second pass lies beside the first
        if floor is not None:p.z=max(p.z,floor)
        pts.append(p)
    return tube(name,pts,cord,mat,grp,sides=4,scale=.05)

# ---------------- FI02 wooden line spool with hemp line (cand-1; #93 review: v1 lay on its side and read as a wooden box) ----------------
def _plate(name,outline,y0,y1,mat,grp,bev=.004,jit=.0008,seed=1):
    """a board cut to an outline: the polygon (x, z) drawn in the X–Z plane and extruded along Y from y0 to y1,
    edges softened by a bevel and nudged so they are never machine-straight"""
    bm=bmesh.new();f_=[bm.verts.new((x,y0,z)) for x,z in outline];b_=[bm.verts.new((x,y1,z)) for x,z in outline];n=len(outline)
    bm.faces.new(f_);bm.faces.new(list(reversed(b_)))
    for i in range(n):bm.faces.new((f_[i],b_[i],b_[(i+1)%n],f_[(i+1)%n]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);o=finish(name,bm,mat,grp)
    if bev:bevel(o,bev,2,angle=40)
    if jit:jitter(o,jit,seed,freq=18)
    return o
def _arc(c,r,a0,a1,n):
    return [(c[0]+r*math.cos(a),c[1]+r*math.sin(a)) for a in np.linspace(a0,a1,n)]
def FI02(M):
    """standing upright as in cand-1 (0.28 wide × 0.12 deep × 0.28 high): two side posts cut from thin board, their outer edges
    curved, with two finger notches worn in and a flared foot; a bottom bar with an arched underside and a round top bar join them;
    the axle carries the hemp line, wound unevenly with crossing turns, one slack loop hanging out and a loose end tied round the
    top bar with frayed tails; the right axle peg is a newer, paler replacement. The spool is open front and back."""
    W=.26;D=.056;zc=.135;rr=random.Random(202)   # W: outside of the posts; the axle pegs stick out 1 cm each side → 0.28 in all
    def post(sgn):   # outline in the post's own x (0 = inner edge, + = outward); mirrored for the left post
        o=[(0,.006),(0,.268),(.008,.275),(.026,.277),(.040,.270),(.045,.258)]   # top: the outer corner worn round
        o+=[(.044,.238)]+[(.044-.012*math.sin(a),.215+.012*math.cos(a)) for a in np.linspace(.15,math.pi-.15,7)]   # finger notch
        o+=[(.042,.196)]+[(.042-.011*math.sin(a),.176+.011*math.cos(a)) for a in np.linspace(.15,math.pi-.15,7)]   # second notch
        o+=[(.038,.152),(.036,.10),(.039,.06),(.047,.03),(.054,.012),(.052,0),(.006,0)]   # waist, then the foot flares out
        o=[(x+rr.uniform(-.0012,.0012),z+rr.uniform(-.0012,.0012)) for x,z in o]
        xi=sgn*(W/2-.054);pts=[(xi+sgn*x,z) for x,z in o]
        return pts if sgn>0 else list(reversed(pts))
    for sgn,seed in ((-1,211),(1,212)):_plate(f'FI02_Post{"LR"[sgn>0]}',post(sgn),-D/2,D/2,M['cedar_b'],'Frame',seed=seed)
    xi=W/2-.054   # inner edge of the posts
    base=[(-xi-.004,.058),(xi+.004,.058),(xi+.004,.010)]+[(x,.010+.016*math.sin(math.pi*(x+xi-.02)/(2*xi-.04))) for x in np.linspace(xi-.02,-xi+.02,9)]+[(-xi-.004,.010)]   # arched underside
    _plate('FI02_Base',base,-.023,.023,M['cedar_b'],'Frame',bev=.0035,seed=213)
    tb=[Vector((x,.002*math.sin(x*20),.246+.003*math.cos(math.pi*x/W))) for x in np.linspace(-xi-.008,xi+.008,9)]   # top bar, slightly bowed, into both posts
    tube('FI02_TopBar',tb,.012,M['cedar'],'Frame',sides=10,scale=.2)
    _rod('FI02_Axle',(-W/2-.010,0,zc),(xi+.006,0,zc),.0105,M['cedar'],'Frame')   # old peg end sticks out on the left
    _rod('FI02_PegNew',(xi-.004,0,zc),(W/2+.010,0,zc),.0115,M['floatwood'],'Frame')   # the replaced peg: fresher, paler wood
    _lathe('FI02_Core',[(0,.0295),(1,.0295)],((-xi+.006,0,zc),(xi-.006,0,zc)),M['hemp'],'Coil',NS=20,scale=.08)
    x0,x1=-xi+.008,xi-.008
    for k,(r,n,dirn) in enumerate(((.0335,18,1),(.0420,17,-1),(.0505,11,1))):   # three uneven layers, the last only part-way; 8.5 mm apart: a 2 mm gap between 6 mm lines (packed tight, the faces of one layer lay on the next, coplanar)
        pts=[];span=1 if k<2 else .62
        for a in np.linspace(0,math.tau*n,n*16):
            t=a/(math.tau*n);x=(x0+(x1-x0)*t*span) if dirn>0 else (x1-(x1-x0)*t*span);x+=(.004 if k==2 else 0)
            q=r+.0006*math.sin(a*.29+k)+.0004*math.sin(a*1.7+2*k)   # the turns ride up and down a little: wound by hand
            pts.append(Vector((x,q*math.cos(a),zc+q*math.sin(a))))
        tube(f'FI02_Layer{k}',pts,.003,M['hemp'],'Coil',sides=4,scale=.05,up=(0,1,0))
    for k,(xa,xb,ph,r) in enumerate(((-.06,.055,.4,.0548),(.05,-.06,2.3,.0553),(-.02,.062,4.4,.0543))):   # crossing turns on top
        pts=[Vector((xa+(xb-xa)*a/math.tau,r*math.cos(a+ph),zc+r*math.sin(a+ph))) for a in np.linspace(0,math.tau,20)]
        tube(f'FI02_Cross{k}',pts,.003,M['hemp'],'Coil',sides=4,scale=.05)
    # a slack turn come loose: leaves the coil at the front, sags down towards the bottom bar and goes back in
    xs=.02;r_=.0535;a0,a1=math.radians(-150),math.radians(-112)   # both ends on the front of the coil (-Y), the loop sagging in front of it
    lp=[Vector((xs,r_*math.cos(a0),zc+r_*math.sin(a0))),Vector((xs+.005,-.056,.092)),Vector((xs+.011,-.054,.072)),Vector((xs+.017,-.044,.066)),
        Vector((xs+.022,-.030,.070)),Vector((xs+.026,r_*math.cos(a1),zc+r_*math.sin(a1)))]
    tube('FI02_SlackLoop',lp,.003,M['hemp'],'Coil',sides=4,scale=.05)
    # the loose end: off the top of the coil, up to the top bar, three turns round it, a knot and two frayed tails hanging
    tx=-xi+.026;a_=math.radians(95);p0=Vector((tx-.004,.0585*math.cos(a_),zc+.0585*math.sin(a_)))   # leaves the coil from just above it (lying on a crossing turn it was coplanar)
    tie=[p0,Vector((tx,.010,.20)),Vector((tx,.016,.232))]+[Vector((tx+.0055*i/14,.0172*math.cos(q),.246+.0172*math.sin(q))) for i,q in enumerate(np.linspace(-math.pi*.4,-math.pi*.4+math.tau*2.6,30))]
    tube('FI02_Tie',tie,.0033,M['hemp'],'Body',sides=4,scale=.05)
    kp=tie[-1]
    for j,(dx,dy,L) in enumerate(((.009,.004,.055),(-.011,-.003,.075))):   # spread apart: side by side they ran coplanar   # frayed tails (Detail_)
        tl=[kp+Vector((dx*.15,-.002,-.002)),Vector((kp.x+dx*.5,-.030+dy,kp.z-.012)),Vector((kp.x+dx,-.046+dy,kp.z-L*.5)),Vector((kp.x+dx*1.4,-.052+dy,kp.z-L))]   # hang in front of the coil, not through it (y absolute: inside the 0.12 m depth)
        tube(f'FI02_Tail{j}',tl,.0026,M['hemp'],'Detail_LooseEnd',sides=4,scale=.05)
    def coil_card():   # LOD2: the line coil as one closed drum (20 sides) with the turns painted on: decimated, the 6 mm turns broke into spikes
        NS_=20;xa,xb=-xi+.007,xi-.007;R_=.0525;cv=[];cf=[];cu=[]
        for xx in (xa,xb):
            for k in range(NS_+1):a=math.tau*k/NS_;cv.append((xx,R_*math.cos(a),zc+R_*math.sin(a)))
        for k in range(NS_):cf.append((k,k+1,NS_+2+k,NS_+1+k));cu.append(((k/NS_,0),((k+1)/NS_,0),((k+1)/NS_,.8),(k/NS_,.8)))
        for side,xx in ((0,xa),(1,xb)):   # end discs: fans to a centre point, mapped onto the top fifth of the strip
            c_=len(cv);cv.append((xx,0,zc))
            for k in range(NS_):
                a0=side*(NS_+1)+k;a1=a0+1;cf.append((c_,a1,a0) if side==0 else (c_,a0,a1))
                uvc=(.5,.9);u0=(.5+.45*math.cos(math.tau*k/NS_)*.2,.9+.09*math.sin(math.tau*k/NS_));u1=(.5+.45*math.cos(math.tau*(k+1)/NS_)*.2,.9+.09*math.sin(math.tau*(k+1)/NS_))
                cu.append((uvc,u1,u0) if side==0 else (uvc,u0,u1))
        def pattern(W_,H_):
            u=(np.arange(W_)[None,:]+.5)/W_;v=(np.arange(H_)[:,None]+.5)/H_;t_=np.clip(v/.8,0,1)
            turns=.5+.5*np.sin(math.tau*(t_*17+u*1.0));cross=np.exp(-((((u*1.0-t_*1.0+.3)%.5)-.25)/.03)**2)*(v<.8)
            base=np.array([.36,.29,.19])+np.array([.24,.20,.14])*(.35+.5*turns)[...,None]
            base=base*(1-.25*cross[...,None])
            end=(v>=.8)[...,None]*np.array([.42,.34,.22]);base=np.where((v>=.8)[...,None],end,base)
            return base*np.ones((H_,W_,1)),np.ones((H_,W_),np.float32)
        return {'drop':['Coil'],'strip':.12,'alpha':False,'verts':cv,'faces':cf,'uvs':cu,'pattern':pattern}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2];ax_=np.abs(px)
        post=(ax_>xi-.002)*filled
        hand=post*np.clip(1-np.abs(pz-.196)/.05,0,1)*np.clip((ax_-(W/2-.02))/.012,0,1)   # outer edges round the finger notches: polished by hands
        hand=np.maximum(hand,post*np.clip((pz-.255)/.02,0,1)*.7)   # tops of the posts, where it is picked up
        col=col*(1+.30*hand[...,None])+hand[...,None]*np.array([.05,.035,.02]);rough=np.clip(rough-.30*hand,0,1)
        foot=np.clip((.035-pz)/.03,0,1)*filled*(1-mid)   # feet and the bottom bar's ends: dirt from the ground, a little moss
        moss=foot*np.clip((noise-.45)*3,0,1)*(ax_>xi-.03)
        col=col*(1-.28*foot[...,None])+moss[...,None]*np.array([.10,.13,.03])*.9;rough=np.clip(rough+.05*foot,0,1)
        return col,rough
    return {'paint':paint,'wear':1.2,'grime':1.2,'lod_ratios':{'Frame':(.6,.40),'Body':(.5,.35),'Coil':(.5,.1)},'card':coil_card(),'notes':['stands upright as in its three-view: 0.28 wide × 0.12 deep × 0.28 high; the coil is open front and back',
            'posts cut from 5.6 cm board with curved outer edges, two finger notches and flared feet; the right axle peg is a separate, paler replacement',
            'the line: three uneven layers, three crossing turns, one slack loop hanging out; tied round the top bar','Detail_LooseEnd: the two frayed tails']}
PROPS['FI02']=FI02

# ---------------- FI03 bamboo-ring landing net (cand-2; #93 review: v1's flat mesh read as a tennis racket) ----------------
def FI03(M):
    """pushed handle-first into the bank mud at 34°, as nets are left standing by the water ('leaning to one side', pack §1):
    a split-bamboo ring a little out of round, its ends lashed to the handle with dark cord; a knotted hemp bag of 3–4 cm
    meshes hanging about 20 cm below the ring, narrowing to a tied bottom; one patch mended with darker cord; the grip in an
    old cloth wrap with cord bindings at uneven places, the bare cane where the hand holds rubbed smooth.
    LOD2 drops the modelled net for a low card bag with the net painted in alpha."""
    tilt=math.radians(34);s0=.10   # handle coordinate at the ground (the butt is in the mud)
    R=Matrix.Rotation(-tilt,4,'Y');O=-(R@Vector((s0,0,0)));T=lambda p:R@Vector(p)+O   # handle frame (X along the handle) → world
    cx,a,b=1.02,.28,.20;rr=.0085;rw=random.Random(303);ph=[rw.uniform(0,6.3) for _ in range(4)]
    def ring(th):   # teardrop, drawn in to the throat; a hand-bent cane: a little out of round and not quite flat
        wob=1+.03*math.sin(2*th+ph[0])+.015*math.sin(3*th+ph[1])
        return Vector((cx+a*math.cos(th)*(1+.02*math.sin(2*th+ph[2])),b*math.sin(th)*(1-.62*max(0,-math.cos(th))**2.2)*wob,.004*math.sin(3*th+ph[3])))
    ends=[Vector((.69,-.0098,0)),Vector((.72,-.0105,0))]
    tube('FI03_Ring',[T(p) for p in ends+[ring(t) for t in np.linspace(math.radians(-172),math.radians(172),70)]+[Vector((.72,.0105,0)),Vector((.70,.0098,0))]],rr,M['bamboo'],'Body',sides=8,scale=.3)
    tube('FI03_Handle',[T((x,0,0)) for x in np.linspace(s0+.019,.775,16)],.0125,M['bamboo'],'Body',sides=10,scale=.3)
    hx=Vector(R@Vector((1,0,0)))
    for i,(x,n,w) in enumerate(((.694,15,0),(.715,13,.0015),(.738,17,.001))):   # the ring's ends lashed to the handle
        _ring(f'FI03_Bind{i}',T((x,0,0)),hx,.0215,.0022,M['cord_dark'],'Body',n=n,wob=w)
    for i,th in enumerate((-2.1,-1.05,.05,1.0,2.15)):   # small bindings round the ring, unevenly spaced
        p=T(ring(th));t_=(T(ring(th+.01))-T(ring(th-.01))).normalized();_ring(f'FI03_RBind{i}',p,t_,rr+.0022,.0017,M['cord_dark'],'Body',n=11)
    # grip: an old cloth strip wound on with uneven pitch, made as one sleeve whose radius steps up where each turn laps over
    # the last (a closed surface: separate overlapping strips baked into dark/white stripes), and cord bands at uneven places
    xg=np.linspace(.163,.337,60);pit=.019+.006*np.sin(xg*90)+.003*np.sin(xg*230);ng=np.concatenate([[0],np.cumsum(np.diff(xg)/pit[1:])])
    gb=bmesh.new();NSg=18;grs=[]
    for x,n_ in zip(xg,ng):
        end=min(1,(x-.163)/.006,(.337-x)/.006)   # the sleeve tapers into the cane at both ends
        ring_=[]
        for k in range(NSg):
            th=math.tau*k/NSg;r_=.0121+end*(.0015+.0011*((n_-th/math.tau)%1.0));ring_.append(gb.verts.new(T((x,r_*math.cos(th),r_*math.sin(th)))))
        grs.append(ring_)
    for A_,B_ in zip(grs,grs[1:]):
        for k in range(NSg):gb.faces.new((A_[k],A_[(k+1)%NSg],B_[(k+1)%NSg],B_[k]))
    gb.faces.new(list(reversed(grs[0])));gb.faces.new(grs[-1])
    for f_ in gb.faces:f_.smooth=True
    finish('FI03_GripCloth',gb,M['linen_b'],'Body',.1)
    for i,(x,turns) in enumerate(((.150,5),(.352,4),(.47,2),(.61,6))):   # cord bands: 5, 4, 2 and 6 turns, nothing evenly spaced
        r_=.0147;pts=[]
        for q in np.linspace(0,math.tau*turns,turns*12):pts.append(T((x+.0046*q/math.tau,r_*math.cos(q),r_*math.sin(q))))
        tube(f'FI03_Band{i}',pts,.0021,M['cord_dark'],'Body',sides=4,scale=.05)
    # mud round the handle where it is pushed in: a low irregular mound, flat underneath
    mb=bmesh.new();cen=T((s0,0,0));NSm=20;Rm=.08;rings_=[]   # a heap pushed up round the handle, high enough to hide its cut end
    for k,rk in enumerate(np.linspace(0,1,6)[1:]):
        ring_=[]
        for t in np.linspace(0,math.tau,NSm,endpoint=False):
            mx=Rm*rk*(1+.18*math.sin(3*t+1)+.08*math.sin(5*t))*math.cos(t)+.012*rk;my=Rm*rk*(1+.15*math.sin(2*t+2))*math.sin(t)
            mz=max(.0006,.032*(1-rk*rk)**1.4*(1+.15*math.sin(4*t)));ring_.append(mb.verts.new(cen+Vector((mx,my,mz))))
        rings_.append(ring_)
    top=mb.verts.new(cen+Vector((0,0,.033)))   # low and gently sloped: a steep flank met the handle's side at the same angle
    for k in range(NSm):mb.faces.new((top,rings_[0][k],rings_[0][(k+1)%NSm]))
    for A_,B_ in zip(rings_,rings_[1:]):
        for k in range(NSm):mb.faces.new((A_[k],B_[k],B_[(k+1)%NSm],A_[(k+1)%NSm]))
    for v in rings_[-1]:v.co.z=0
    for f_ in mb.faces:f_.smooth=True
    mb.faces.new(list(reversed(rings_[-1])));finish('FI03_Mud',mb,M['mud'],'Body',.3)   # smooth: a heap of mud, not a cut stone
    # the net bag: rim on the ring, hanging under gravity (world -Z) to a narrow tied bottom
    N,J=26,15;dth=np.linspace(-math.pi,math.pi,721);dp=[T(ring(t)) for t in dth];arc=np.concatenate([[0],np.cumsum([(b_-a_).length for a_,b_ in zip(dp,dp[1:])])])
    rim=[T(ring(float(np.interp(arc[-1]*(i+.5)/N,arc,dth)))) for i in range(N)]   # spaced evenly along the cane (evenly by angle they crowded at the throat, down to the bottom)
    C=sum(rim,Vector())/N;zlow=min(p.z for p in rim);Bz=zlow-.20;C2=Vector((C.x+.02,C.y,0))
    def S(th,t):   # bag surface: t = 0 on the rim, 1 at the bottom
        u=((th+math.pi)/math.tau*N-.5)%N;i0=int(u);fr=u-i0;Rp=rim[i0%N].lerp(rim[(i0+1)%N],fr)
        Rp=Rp+(C-Rp).normalized()*.004   # just inside the cane
        g=(1+.10*math.sin(math.pi*t))*(1-.70*t**1.5);hz=t**.8   # the bottom drawn in to 30 % of the ring: narrower, the last rows' cords ran side by side
        return Vector((C2.x+(Rp.x-C2.x)*g,C2.y+(Rp.y-C2.y)*g,Rp.z+(Bz-Rp.z)*hz))
    nr=random.Random(31);node={};sn={}
    for j in range(J+1):
        for i in range(N):
            th=-math.pi+math.tau*(i+.5+.5*(j%2))/N;p=S(th,j/J)
            if 0<j<J:p+=Vector((nr.uniform(-1,1),nr.uniform(-1,1),nr.uniform(-1,.5)))*.0028*(1-abs(2*j/J-1)*.3)   # slack: never a perfect grid
            node[i,j]=p
            e_=.01;nv=(S(th+e_,j/J)-S(th-e_,j/J)).cross(S(th,min(1,j/J+e_))-S(th,max(0,j/J-e_)))   # true surface normal (on the flat floor of the bag it points down)
            if nv.length>1e-9:
                nv.normalize();ho=Vector((p.x-C2.x,p.y-C2.y,0))
                if nv.dot(ho)+nv.dot(Vector((0,0,-1)))*(j/J)<0:nv=-nv
            sn[i,j]=nv
    def outward(p):d=p-Vector((C2.x,C2.y,p.z));return d.normalized() if d.length>1e-6 else Vector((0,0,-1))
    for fam,sh in ((1,.0013),(-1,-.0013)):   # two families of cords zig-zagging down: they cross (and are knotted) at every node
        for i in range(N):
            pts=[];ii=i
            for j in range(J+1):
                p=node[ii%N,j];pts.append(p+sn[ii%N,j]*sh)   # the two families sit either side of the net's surface
                if j<J:
                    nxt_i=(ii if j%2==0 else ii+1) if fam>0 else (ii-1 if j%2==0 else ii)   # row j node i sits at i + j%2/2: down-right / down-left neighbours
                    q=node[nxt_i%N,j+1];m_=(p+q)/2+Vector((0,0,-.0022));pts.append(m_+outward(m_)*sh);ii=nxt_i
            pts=pts[::2];L_=[0.]   # knot to knot (_cane adds a point half-way and swells the cord at each knot)
            for a_,b_ in zip(pts,pts[1:]):L_.append(L_[-1]+(b_-a_).length)
            _cane(f'FI03_Net{"AB"[fam<0]}{i:02d}',pts,[.0019]*len(pts),M['net'],'Net',nodes=L_[1:],sides=3,node_bulge=.75,node_len=.006)   # the knot is a swelling of the cord at every crossing (separate lumps lay coplanar with the cords)
    # the bottom: a cord ring through the last row (its meshes 1 cm apart: drawn in to one point they ran side by side, coplanar),
    # closed by seven cords drawn in to a tied knot a little lower
    bl=[node[i,J] for i in range(N)];bl=bl+[bl[0]+outward(bl[0])*.0042+Vector((0,0,-.002)),bl[1]+outward(bl[1])*.0045+Vector((0,0,-.003))]
    tube('FI03_BottomRing',bl,.0022,M['net'],'Net',sides=4,scale=.04)
    bc=Vector((C2.x,C2.y,Bz-.032));bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.011,location=bc);kk=bpy.context.object;kk.scale=(1.15,1,.85);bpy.ops.object.transform_apply(scale=True)
    bm=bmesh.new();bm.from_mesh(kk.data);bpy.data.objects.remove(kk);finish('FI03_BottomTie',bm,M['cord_dark'],'Net',.05)
    for k,i in enumerate(range(1,N,4)):
        p=node[i,J];e_=bc+(p-bc).normalized()*.006;tube(f'FI03_BottomCord{k}',[p,p.lerp(e_,.5)+Vector((0,0,-.004)),e_],.0018,M['net'],'Net',sides=3,scale=.04)   # each ends inside the tie, apart from the others
    tube('FI03_BottomTail',[bc+Vector((.002,0,-.008)),bc+Vector((.008,-.004,-.03)),bc+Vector((.004,-.006,-.05))],.0018,M['cord_dark'],'Net',sides=3,scale=.04)
    for k,((i,j),(i2,j2)) in enumerate((((5,4),(6,4)),((5,6),(6,6)),((6,5),(6,7)),((5,5),(5,7)))):   # the mended patch: darker cord across a few meshes (Detail_), never along a net cord
        p=node[i,j];q=node[i2,j2];a_=p+outward(p)*.0045;b_=q+outward(q)*.0045
        tube(f'FI03_Repair{k}',[a_,(a_+b_)/2+outward((a_+b_)/2)*.002,b_],.0017,M['cord_dark'],'Detail_Repair',sides=3,scale=.04)
    # LOD2 card: the same bag surface, 12 × 5 quads (+ a fan to the bottom), UV over the painted net strip (u around, v down)
    CU,CV=12,5;cv=[];cf=[];cuv=[]
    for j in range(CV+1):
        for i in range(CU+1):
            p=S(-math.pi+math.tau*i/CU,min(j/CV,.97));cv.append(tuple(p))
    for j in range(CV):
        for i in range(CU):
            a_=j*(CU+1)+i;cf.append((a_,a_+1,a_+CU+2,a_+CU+1));cuv.append(((i/CU,1-j/CV),((i+1)/CU,1-j/CV),((i+1)/CU,1-(j+1)/CV),(i/CU,1-(j+1)/CV)))
    def pattern(W_,H_):   # the net as the card shows it: 26 diamonds round, 15 rows, knots at the crossings, darker and damp towards the bottom
        u=(np.arange(W_)[None,:]+.5)/W_;v=1-(np.arange(H_)[:,None]+.5)/H_   # image rows go up: v = 0 at the top of the strip = the rim
        ri=u*N;rj=v*J;g=math.hypot(N/W_,J/(2*H_))
        dA=np.abs((ri-rj/2)-np.round(ri-rj/2))/g;dB=np.abs((ri+rj/2)-np.round(ri+rj/2))/g
        line=np.clip(2.2-np.minimum(dA,dB),0,1)
        kj=np.round(rj);ki=np.round(ri-.5*(kj%2))+.5*(kj%2);dk=np.hypot((ri-ki)*W_/N,(rj-kj)*H_/J);knot=np.clip(3.4-dk,0,1)
        al=np.maximum(line,knot);al=(al>.5).astype(np.float32)
        base=np.array([.50,.41,.27])*(1-.30*np.clip(v,0,1)**1.5)[...,None]*np.ones((1,W_,1))
        return base*(1-.15*knot[...,None]),al
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];pz=P[...,2];hd=np.array(hx[:]);O_=np.array(T((0,0,0))[:]);s=(P-O_)@hd   # s: distance along the handle
        held=filled*np.clip(1-np.abs(s-.41)/.05,0,1)*np.clip(1-np.linalg.norm((P-O_)-s[...,None]*hd,axis=2)/.02,0,1)   # bare cane between the cloth and the bands: rubbed smooth
        col=col*(1+.20*held[...,None])+held[...,None]*np.array([.03,.025,.01]);rough=np.clip(rough-.30*held,0,1)
        wet=filled*np.clip((zlow-.06-pz)/.12,0,1)   # the bottom of the bag still wet
        col=col*(1-.30*wet[...,None]);rough=np.clip(rough-.18*wet,0,1)
        return col,rough
    return {'paint':paint,'wear':.8,'grime':.6,'uv_angle':50,
            'card':{'drop':['Net'],'ratio':.35,'strip':.2,'verts':cv,'faces':cf,'uvs':cuv,'pattern':pattern},
            'notes':['pushed handle-first into the bank mud at 34°; the net bag hangs about 20 cm below the ring (#93 review): the pack\'s 0.06 m height was for the net lying flat',
                     'net: 26 meshes round (spaced evenly along the cane) × 15 rows of 3–4 cm, cords 3.8 mm swelling into a knot at every crossing; a cord ring round the bottom row, seven cords drawn in to a tied knot; Detail_Repair: the mended patch',
                     'LOD2: the modelled net is replaced by a 12 × 5 card bag with the net in the albedo alpha (alpha clip 0.5); the material is double-sided']}
PROPS['FI03']=FI03

# ---------------- FI04 long tapered bamboo fish trap (cand-3) ----------------
def FI04(M):
    """lying on its side: a ring of split-cane slats from a thick mouth hoop tapering to a tied tail bundle, held by cane
    hoops and hemp lashings, open between the slats so it reads hollow; inside the mouth a short woven funnel (the part
    that makes it a trap, not a basket); one patched slat; damp and dark on the side it lies on"""
    L=.86;Rm=.168
    def R(x):return Rm*(1-(x/L)**1.25*.86)
    N=22
    for i in range(N):
        a=math.tau*i/N;rows=[]
        for x in np.linspace(.006,L,26):
            r=R(x);w=min(.0105*(r/Rm)**.6+.004,.21*math.tau*r/N);c=Vector((x,r*math.cos(a),r*math.sin(a)));tn=Vector((0,-math.sin(a),math.cos(a)))   # never wider than 42 % of the spacing: at the tail they overlapped
            rows.append([tuple(c-tn*w),tuple(c+tn*w)])
        _sheet(f'FI04_Slat{i:02d}',rows,None,M,M['bamboo_split'],'Body',t=.0035)
    for j,(x,rr) in enumerate(((.006,.011),(.24,.006),(.48,.006),(.68,.005))):   # mouth hoop and cane hoops, just outside the slats
        _ring(f'FI04_Hoop{j}',(x,0,0),(1,0,0),R(x)+.002+rr,rr,M['bamboo'],'Body',n=49)
    for j,x in enumerate((.12,.36,.58)):   # hemp lashings
        _ring(f'FI04_Lash{j}',(x,0,0),(1,0,0),R(x)+.0045,.0028,M['hemp'],'Body',n=61,wob=.003)
    for i in range(16):   # the inner funnel: short slats from the mouth hoop to a narrow throat inside
        a=math.tau*(i+.5)/16;rows=[]
        for t in np.linspace(0,1,10):
            x=.012+.20*t;r=(Rm-.0045)*(1-t)+.045*t;w=min(.009*(1-.5*t)+.003,.42*math.tau*r/16*.5);c=Vector((x,r*math.cos(a),r*math.sin(a)));tn=Vector((0,-math.sin(a),math.cos(a)))   # starts against the inside of the slats (1 cm in, it floated)
            rows.append([tuple(c-tn*w),tuple(c+tn*w)])
        _sheet(f'FI04_Funnel{i:02d}',rows,None,M,M['bamboo_split'],'Body',t=.003)
    _ring('FI04_Throat',(.212,0,0),(1,0,0),.0475,.004,M['hemp'],'Body',n=25)
    for j in range(5):_ring(f'FI04_Tail{j}',(L-.05+j*.011,0,0),(1,0,0),R(L-.05+j*.011)+.0035,.003,M['hemp'],'Body',n=17)   # tail tied
    a=math.tau*5/N;rows=[]   # a patched slat: a short woven piece over a broken one
    for x in np.linspace(.40,.50,6):
        r=R(x)+.0055;c=Vector((x,r*math.cos(a),r*math.sin(a)));tn=Vector((0,-math.sin(a),math.cos(a)))
        rows.append([tuple(c-tn*.032),tuple(c),tuple(c+tn*.032)])
    _sheet('FI04_Patch',rows,None,M,M['hemp'],'Detail_Patch',t=.003)
    for k in range(6):   # frayed ends of the lashings
        x=(.12,.36,.58)[k%3];q=-1.2+.5*k;r=R(x)+.0045;p0=Vector((x,r*math.cos(q),r*math.sin(q)))
        tube(f'FI04_Fray{k}',[p0,p0+Vector((.004,.006*math.cos(q+1),.006*math.sin(q+1)-.008)),p0+Vector((.006,.008*math.cos(q+1),-.02))],.0012,M['hemp'],'Detail_Fray',sides=3,scale=.04,caps=False)
    ang=math.atan2(R(0)-R(L),L)   # tilt so the lower edge of the cone lies on the ground from mouth to tail
    for o in parts:o.data.transform(Matrix.Rotation(-ang,4,'Y'))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        pz=pos[...,2]-meta['offset'][2];wet=np.clip((.09+.03*(noise-.5)-pz)/.06,0,1)*filled   # the side it lies on: damp, darker, a little green
        col=col*(1-.30*wet[...,None])+wet[...,None]*np.array([.03,.05,.01]);rough=np.clip(rough-.12*wet,0,1);return col,rough
    return {'paint':paint,'wear':.6,'grime':.9,'uv_angle':50,'notes':['lies on its side, tilted so the cone rests on the ground from mouth to tail',
            'the inner funnel at the mouth is what makes it a trap (not the old carrying basket)','Detail_Patch: the woven patch; Detail_Fray: frayed lashing ends']}
PROPS['FI04']=FI04

# ---------------- FI05 three wooden floats on a loose line (layout cand-1; floats a-4, b-3, c-2) ----------------
def FI05(M):
    """a long spindle float with a peg, a short barrel float with a hole through it (one end chipped) and a small egg float
    with a neck groove, joined by one loose hemp line with an uneven hand-tied knot, lying on the ground"""
    cr=.0022;gz=cr+.0004   # line radius, height of the line where it lies on the ground
    # spindle (a): 0.20 m long, a peg at one end
    pa=Vector((-.23,.075,0));da=Vector((math.cos(.30),math.sin(.30),0));ra=.024
    prof=[(0,0)]+[(s,ra*(math.sin(math.pi*s)**.7)*(1-.22*s)) for s in np.linspace(.04,.96,14)]+[(1,0)]
    _lathe('FI05_Spindle',prof,(pa+Vector((0,0,ra)),pa+da*.20+Vector((0,0,ra))),M['floatwood'],'Body',NS=16)
    peg0=pa+da*.18+Vector((0,0,ra));peg1=pa+da*.235+Vector((0,0,ra));_rod('FI05_Peg',peg0,peg1,.0045,M['cedar'],'Body',sides=6)
    # barrel (b): 0.12 m, flat ends, a bore for the line, one end edge chipped
    pb=Vector((-.04,-.07,0));db=Vector((math.cos(-.22),math.sin(-.22),0));rb=.034;bo=.0072
    b0=pb+Vector((0,0,rb));b1=pb+db*.12+Vector((0,0,rb))
    o=_lathe('FI05_Barrel',[(0,rb*.88),(.05,rb*.98),(.5,rb),(.95,rb*.98),(1,rb*.88),(1,bo),(0,bo)],(b0,b1),M['floatwood'],'Body',NS=20,loop=True)
    ch=b1+Vector((0,0,rb*.85))-db*.006;_boolean(o,_cutter('FI05_Chip',(.03,.034,.022),ch))   # the chip off one end
    # egg (c): 0.08 m, a groove round its neck
    pc=Vector((.17,.085,0));dc=Vector((math.cos(2.7),math.sin(2.7),0));rc=.024
    def er(s):return rc*math.sqrt(max(0,1-(((s-.42)/.58) if s>.42 else ((s-.42)/.42))**2))*(1-.16*math.exp(-((s-.78)/.035)**2))
    prof=[(0,0)]+[(s,er(s)) for s in np.linspace(.03,.97,18)]+[(1,0)]
    _lathe('FI05_Egg',prof,(pc+Vector((0,0,rc)),pc+dc*.08+Vector((0,0,rc))),M['floatwood'],'Body',NS=16)
    gc=pc+dc*(.08*.78)+Vector((0,0,rc));_ring('FI05_GrooveTie',gc,dc,er(.78)+cr*.6,cr,M['hemp'],'Body',n=15)
    # the line: from the peg down to the ground, through the barrel's bore, along the ground to a knot, up to the egg's groove
    gp=lambda v:Vector((v.x,v.y,gz))
    k1=Vector((.08,-.02,0));k2=Vector((.11,.03,0))
    line=[peg1-da*.012,peg1+da*.006+Vector((0,0,-.006)),gp(peg1+da*.03+Vector((.0,-.02,0))),gp(pa+da*.26+Vector((.02,-.07,0))),gp(b0-db*.04),
          b0-db*.008,b0+db*.03,b0+db*.09,b1+db*.008,gp(b1+db*.04),gp(Vector((.07,-.07,0))),gp(k1),gp(k2),gp(gc+Vector((.025,-.03,0))),gc+Vector((.004,-.012,-.008))]
    for _ in range(3):   # Chaikin smoothing: a soft hemp line, not a wire with corners (both ends kept)
        sm=[line[0]]
        for p,q in zip(line,line[1:]):sm+=[p.lerp(q,.25),p.lerp(q,.75)]
        line=sm+[line[-1]]
    line=[Vector((p.x,p.y,max(p.z,gz))) for p in line]   # never below the ground
    dense=[]
    for p,q in zip(line,line[1:]):
        n=max(1,int((q-p).length/.012))
        for t in range(n):dense.append(p.lerp(q,t/n))
    dense.append(line[-1]);tube('FI05_Line',dense,cr,M['hemp'],'Body',sides=5,scale=.05)
    kc=(gp(k1)+gp(k2))/2+Vector((0,0,.004))   # the uneven knot on the line
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.0085,location=kc);kk=bpy.context.object;kk.scale=(1.3,.9,.7);bpy.ops.object.transform_apply(scale=True)
    bm=bmesh.new();bm.from_mesh(kk.data);bpy.data.objects.remove(kk);finish('FI05_Knot',bm,M['hemp'],'Body',.06);parts[-1].data.transform(Matrix.Translation((0,0,0)))
    tail=[kc+Vector((.004,.002,-.002)),gp(kc+Vector((.025,.02,0))),gp(kc+Vector((.045,.028,0))),gp(kc+Vector((.06,.026,0)))]   # a frayed tail from the knot
    tube('FI05_Tail',tail,cr*.9,M['hemp'],'Detail_Tail',sides=4,scale=.05)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        o_=Vector(meta['offset']);P=pos-np.array(o_[:])
        D=np.array(da[:]);rel=P-np.array((pa+Vector((0,0,ra)))[:]);s=(rel@D)/.20;dax=np.linalg.norm(rel-s[...,None]*.20*D,axis=2)
        band=(np.exp(-((s-.32)/.025)**2)+np.exp(-((s-.62)/.025)**2))*(dax<.03)*filled   # two faded paint rings on the spindle (float paint, no marks)
        col=col*(1-.45*band[...,None])+band[...,None]*np.array([.55,.24,.17])*.45
        pz=P[...,2];stain=np.clip((.018+.006*(noise-.5)-pz)/.012,0,1)*filled   # water stains up from where they lie
        col=col*(1-.22*stain[...,None]);return col,rough
    return {'paint':paint,'wear':.9,'grime':.8,'notes':['three floats of different shapes: spindle (a, ~0.2 m, peg), barrel (b, ~0.12 m, bore, one end chipped), egg (c, ~0.08 m, neck groove)',
            'one loose line ties them together through the barrel\'s bore, with a hand-tied knot; Detail_Tail: the frayed tail from the knot']}
PROPS['FI05']=FI05
