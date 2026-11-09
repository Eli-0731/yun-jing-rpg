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

# ---------------- FI02 wooden line spool with hemp line (cand-1) ----------------
def FI02(M):
    """built upright as in cand-1 and laid on its side (Ø0.28 × 0.12): two side posts with finger notches worn into their
    outer edges, a bottom bar and a round top bar, an axle through the posts with the hemp line wound round it in uneven
    layers and a few crossing turns; the right axle end is a newer, paler replacement peg; the loose end tied off on the top bar"""
    H,W=.28,.28
    for sgn,seed in ((-1,201),(1,202)):
        x=sgn*(W/2-.0225);o=box(f'FI02_Post{"LR"[sgn>0]}',(.045,.105,H),(x,0,H/2),M['cedar_b'],'Body',bev=.006,segs=2,cuts=0,jit=.0012,seed=seed)
        for zc in (.165,.205):_boolean(o,_cutter(f'FI02_Notch{sgn}{int(zc*1000)}',(.04,.2,.026),(sgn*(W/2+.011),0,zc)))   # finger notches on the outer edge
    box('FI02_Base',(W-.07,.085,.032),(0,0,.034),M['cedar_b'],'Body',bev=.005,segs=2,jit=.0008,seed=203)
    _rod('FI02_TopBar',(-W/2+.03,0,.245),(W/2-.03,0,.245),.013,M['cedar'],'Body')
    _rod('FI02_Axle',(-W/2-.006,0,.135),(W/2-.032,0,.135),.011,M['cedar'],'Body')
    _rod('FI02_PegNew',(W/2-.036,0,.135),(W/2+.008,0,.135),.0118,M['floatwood'],'Body')   # the replaced peg: fresher, paler wood
    _lathe('FI02_Core',[(0,.044),(1,.044)],((-.088,0,.135),(.088,0,.135)),M['hemp'],'Body',NS=20,scale=.08)
    for k,(r,x0,x1,n) in enumerate(((.0478,-.084,.084,20),(.0532,.078,-.072,17))):   # the wound line: two uneven layers
        pts=[]
        for a in np.linspace(0,math.tau*n,n*14):
            t=a/(math.tau*n);x=x0+(x1-x0)*t;rr=r+.0012*math.sin(a*.37+k)
            pts.append(Vector((x,rr*math.cos(a),.135+rr*math.sin(a))))
        tube(f'FI02_Layer{k}',pts,.0036,M['hemp'],'Body',sides=4,scale=.05)
    for k,(x0,x1,ph) in enumerate(((-.07,.06,.3),(.05,-.06,2.1))):   # a few crossing turns on top
        pts=[Vector((x0+(x1-x0)*a/math.tau,.0592*math.cos(a+ph),.135+.0592*math.sin(a+ph))) for a in np.linspace(0,math.tau,18)]
        tube(f'FI02_Cross{k}',pts,.0034,M['hemp'],'Body',sides=4,scale=.05)
    a0=math.radians(80);p0=Vector((-.06,.059*math.cos(a0),.135+.059*math.sin(a0)))   # the loose end, tied round the top bar
    tie=[p0,Vector((-.075,.02,.2)),Vector((-.088,.018,.243))]+[Vector((-.091-.0045*i/12,.0172*math.cos(a),.245+.0172*math.sin(a))) for i,a in enumerate(np.linspace(math.pi*.45,math.pi*.45+math.tau*2,24))]
    tie+=[Vector((-.104,-.014,.226)),Vector((-.106,-.017,.205))]
    tube('FI02_LooseEnd',tie,.0032,M['hemp'],'Detail_LooseEnd',sides=4,scale=.05)
    for o in parts:o.data.transform(Matrix.Rotation(-math.pi/2,4,'X'))   # lay it on its side: the posts' broad faces on the ground
    return {'wear':1.2,'grime':1.0,'notes':['built upright (as the reference) and laid on its side: 0.28 × 0.28 × 0.12 m',
            'the right axle end is a separate, paler replacement peg','Detail_LooseEnd: the loose end tied round the top bar']}
PROPS['FI02']=FI02

# ---------------- FI03 bamboo-ring landing net (cand-2) ----------------
def FI03(M):
    """lying flat: a split-bamboo ring, teardrop-shaped, its two ends run into a short handle and are bound with dark
    cord; the knotted hemp net has collapsed under the ring onto the ground (so the item is only a few cm high); one
    repaired patch of darker cord; the grip wrapped in old cloth"""
    cx,a,b=1.02,.28,.215;rr=.0085;zr=rr+.0035
    def ring(th):   # teardrop: the back (towards the handle) drawn in to the throat
        return Vector((cx+a*math.cos(th),b*math.sin(th)*(1-.62*max(0,-math.cos(th))**2.2),zr))
    pts=[Vector((.69,-.0098,.0128)),Vector((.72,-.0105,.0128))]+[ring(t) for t in np.linspace(math.radians(-172),math.radians(172),64)]+[Vector((.72,.0105,.0128)),Vector((.70,.0098,.0128))]   # the two ends run on along either side of the handle, under the bindings   # the two ends lie along either side of the handle (on top of each other they were coplanar)
    tube('FI03_Ring',pts,rr,M['bamboo'],'Body',sides=8,scale=.3)
    tube('FI03_Handle',[Vector((x,0,.0128)) for x in np.linspace(0,.775,15)],.0125,M['bamboo'],'Body',sides=10,scale=.3)   # ends just past the throat (further in, its underside met the net)
    for i,x in enumerate((.70,.737,.774)):   # cord binding where the ring ends meet the handle
        _ring(f'FI03_Bind{i}',(x,0,.0128),(1,0,0),.0215,.0022,M['cord_dark'],'Body',n=15,floor=.0048)   # squeezed flat under the handle, its underside inside the handle
    for i,th in enumerate((-2.0,-1.0,0,1.0,2.0)):   # small bindings round the ring
        p=ring(th);t_=(ring(th+.01)-ring(th-.01)).normalized();_ring(f'FI03_RBind{i}',p,t_,rr+.0022,.0017,M['cord_dark'],'Body',n=11)
    wrap=[Vector((.04+.16*q/(math.tau*7),.0148*math.cos(q),.0128+.0148*math.sin(q))) for q in np.linspace(0,math.tau*7,7*14)]
    tube('FI03_GripWrap',wrap,.0046,M['linen_b'],'Body',sides=4,scale=.05)   # old cloth wound round the grip
    def inside(x,y):
        if x<.80 or x>cx+a:return False   # the net starts clear of the handle
        th=math.acos(max(-1,min(1,(x-cx)/a)));return abs(y)<b*math.sin(th)*(1-.62*max(0,-math.cos(th))**2.2)-.004
    sp=.034;k=0
    for fam in (1,-1):   # the net: two families of diagonal cords lying on the ground inside the ring, a little wavy
        for c0 in np.arange(-1.0,1.0,sp):
            seg=[]
            for s_ in np.arange(-.6,.6,.012):
                x=cx+(s_+c0)*.7071;y=fam*(s_-c0)*.7071
                if inside(x,y):   # a slack net is never a straight grid: each cord wanders a few mm sideways
                    w_=.0035*math.sin(s_*23+c0*17)+.002*math.sin(s_*51+c0*7);x+=w_*.7071*fam;y-=w_*.7071
                    seg.append(Vector((x,y,.0013+.0009*(1+math.sin(x*41+y*37+fam))*.5+(.0024 if fam>0 else 0))))   # the two families 2.4 mm apart where they cross (1.1 mm read as coplanar near the throat)
                elif len(seg)>2:break
                else:seg=[]
            if len(seg)>2:tube(f'FI03_Net{k:02d}',seg,.0011,M['net'],'Body',sides=3,scale=.04);k+=1
    kr=random.Random(33);kb=bmesh.new()   # knots: a small lump at the mesh crossings (octahedra, a few triangles each)
    for u_ in np.arange(-1.0,1.0,sp):
        for v_ in np.arange(-1.0,1.0,sp):
            x=cx+(u_+v_)*.7071;y=(v_-u_)*.7071   # where cord u_ of one family crosses cord v_ of the other
            if not inside(x,y) or kr.random()<.35:continue
            r_=.0016+.0006*kr.random();bmesh.ops.create_icosphere(kb,subdivisions=0,radius=r_,matrix=Matrix.Translation((x,y,.0034)))
    if kb.verts:finish('FI03_Knots',kb,M['net'],'Body',.04)
    else:kb.free()
    for i in range(4):   # the repaired patch: short darker cords across the mesh
        x0,y0=cx+.10+.012*i,.07-.008*i
        tube(f'FI03_Repair{i}',[Vector((x0-.03,y0-.02,.0042)),Vector((x0,y0,.0052)),Vector((x0+.03,y0+.025,.0042))],.0014,M['cord_dark'],'Detail_Repair',sides=3,scale=.04)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        px=pos[...,0]-meta['offset'][0];pz=pos[...,2]-meta['offset'][2]
        wet=np.clip((px-(cx+.05))/.2,0,1)*np.clip(1-pz/.008,0,1)*filled   # the far half of the net still damp
        col=col*(1-.25*wet[...,None]);rough=np.clip(rough-.15*wet,0,1);return col,rough
    return {'paint':paint,'wear':.8,'grime':.6,'uv_angle':50,'notes':['lying flat; the net bag has collapsed under the ring, so the item is a few cm high',
            'the net is modelled cord by cord (thin tubes); Detail_Repair: the darker repaired cords']}
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
