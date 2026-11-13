# LV01–LV06 shapes, read by build_lv.py (exec'd into its namespace: M = source materials; helpers from the creekside kit:
# tube, box, _sheet, _cane, _lathe, _ring, _rod, _plate, finish …). Every item follows the three-view picked in
# art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _strip(name,path,nrm,w,t,mat,grp,scale=.3):   # w: a width, or a function of the point index
    """a flat strip (split bamboo, cloth band) of width w and thickness t along a path; nrm(i) is the face normal there
    (the strip lies across it); rows are made of three points so the strip can bend a little across"""
    P=[Vector(p) for p in path];rows=[]
    for i,p in enumerate(P):
        tg=(P[min(i+1,len(P)-1)]-P[max(i-1,0)]).normalized();n=Vector(nrm(i)).normalized();s=tg.cross(n).normalized()
        w_=w(i) if callable(w) else w;rows.append([tuple(p-s*w_/2),tuple(p+s*w_/2)])   # two points across: a flat strip
    return _sheet(name,rows,None,None,mat,grp,t=t)

def _taper(name,pts,radii,mat,grp,sides=3,scale=.08,up=None):
    """a tube whose radius changes point by point (twigs, straw: thin at both ends); same frame transport as tube()"""
    pts=[Vector(p) for p in pts];bm=bmesh.new();rings=[];prev=Vector(up) if up is not None else None
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        u=(prev-t*prev.dot(t)).normalized() if prev is not None else t.orthogonal().normalized();prev=u;v=t.cross(u)
        rings.append([bm.verts.new(p+(u*math.cos(math.tau*k/sides)+v*math.sin(math.tau*k/sides))*radii[i]) for k in range(sides)])
    for a,b in zip(rings,rings[1:]):
        for k in range(sides):bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
    bm.faces.new(list(reversed(rings[0])));bm.faces.new(rings[-1])
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)

# ---------------- LV01 woven bamboo chicken coop cover (cand-3) ----------------
def LV01(M):
    """an upturned dome of split bamboo: 16 strips running down from a rope knot and handle at the top, 6 rings woven over
    and under them, all ending in a thick bound bottom rim (darker, worn by the ground); one fresher strip laid over a broken
    one and tied; some straw caught in the weave and two feathers by the rim (Detail_)"""
    R,Hd,z0=.355,.455,.048   # dome radius at the rim, dome height above the rim, height where the dome starts
    def dome(phi,th,off=0.):   # phi: 0 at the top … pi/2 at the rim; a slightly flattened top, as cand-3
        c_=max(0.,math.cos(phi));s_=min(1.,math.sin(phi));r=R*s_**.92+off*s_;z=z0+Hd*c_**1.08+off*c_   # past the rim (phi > pi/2) it stays at the rim's radius
        return Vector((r*math.cos(th),r*math.sin(th),z))
    def dn(phi,th):   # outward normal of the dome
        a=dome(phi+.01,th)-dome(phi-.01,th);b=dome(phi,th+.01)-dome(phi,th-.01);n=a.cross(b).normalized()
        return n if n.dot(dome(phi,th)-Vector((0,0,z0)))>0 else -n
    NM,NR,ph0=22,7,.30;rw=random.Random(101)
    for i in range(NM):   # strips from just under the top knot down into the rim
        th=math.tau*i/NM+rw.uniform(-.03,.03);phis=list(np.linspace(ph0,math.pi/2,22))+[math.pi/2]
        path=[dome(p,th) for p in phis[:-1]]+[dome(math.pi/2,th)+Vector((0,0,-.032))]   # the foot goes straight down into the rim (bent at 45° it lay on the rim's chamfer)
        _strip(f'LV01_Rib{i:02d}',path,lambda k,th=th,phis=phis:dn(min(phis[k],math.pi/2-.001),th),lambda k:.020+.011*min(1,k/10),.006,M['bamboo_old'],'Body')   # narrower near the top, where the strips crowd together
    rings=np.linspace(.50,1.42,NR)
    for j,phi in enumerate(rings):   # rings: over one strip, under the next (6.5 mm out/in: closer, their faces lay on the strips')
        pts=[];nn=[]
        for q in np.linspace(0,math.tau*(1-.6/(NM*4)),NM*4):   # stops just short of its start (a lap over the start lay coplanar on it)
            off=.0065*math.cos(NM/2*q+j*math.pi);pts.append(dome(phi,q,off));nn.append(dn(phi,q))
        _strip(f'LV01_Ring{j}',pts,lambda k,nn=nn:nn[min(k,len(nn)-1)],.031,.005,M['bamboo_old'],'Body')
    # the thick bottom rim: a rounded band all round, the strips' ends inside it
    _lathe('LV01_Rim',[(0,.392),(.08,.397),(.5,.398),(.92,.396),(1,.390),(1,.346),(.9,.341),(.5,.340),(.1,.341),(0,.346)],((0,0,.0),(0,0,.064)),M['cedar_b'],'Body',NS=48,loop=True)
    for k in range(8):   # rope ties round the rim, three turns side by side, a rounded-square loop round the band (an ellipse cut its corners)
        th=math.tau*(round(k*NM/8)+.5)/NM   # between two strips' feet (on a foot, the turns and the strip crowded together)
        c=Vector((.369*math.cos(th),.369*math.sin(th),.032));rd=Vector((math.cos(th),math.sin(th),0));tg=Vector((-math.sin(th),math.cos(th),0))
        for t_ in range(3):
            pts=[c+tg*((t_-1)*.0066)+rd*(.0345*math.copysign(abs(math.cos(a))**.5,math.cos(a)))+Vector((0,0,.0405*math.copysign(abs(math.sin(a))**.5,math.sin(a)))) for a in np.linspace(-.6,math.pi+.6,19)]   # outside, over the top, inside: the rim sits on the ground, so no rope under it
            pts=[c+tg*((t_-1)*.0066)+(pts[0]-c-tg*((t_-1)*.0066))*.55]+pts+[c+tg*((t_-1)*.0066)+(pts[-1]-c-tg*((t_-1)*.0066))*.55]   # both ends tucked into the band
            tube(f'LV01_Tie{k}{t_}',pts,.0026,M['hemp'],'Body',sides=5,scale=.05)
    # the top: a rope knot binding the strips' ends, and a twisted-rope handle loop
    top=dome(0,0);_lathe('LV01_TopCap',[(0,.0),(.2,.116),(.6,.124),(.85,.092),(1,0)],((0,0,top.z-.034),(0,0,top.z+.001)),M['bamboo_old'],'Body',NS=28)   # the strips' ends gathered under the knot: a low crown just under the dome, so the rope turns show above it
    for t_ in range(5):   # rope wound round the gathered ends, each turn a little higher and smaller
        ph_=.33-t_*.045;c_=dome(ph_,0,.009+.0012*t_);r_=math.hypot(c_.x,c_.y)
        pts=[Vector((r_*math.cos(a),r_*math.sin(a),c_.z+.0015*math.sin(3*a))) for a in np.linspace(0,math.tau,33)];pts[-1]=pts[-1]+Vector((0,0,.0045))
        tube(f'LV01_Knot{t_}',pts,.0042,M['hemp'],'Body',sides=6,scale=.05)
    hz=top.z-.006   # the handle ends sit in the crown
    for s_ in (0,1):   # two strands twisted round each other into the loop
        pts=[]
        for a in np.linspace(0,math.pi,30):
            c=Vector((.052*math.cos(a),0,hz+.072*math.sin(a)));tn=Vector((-math.sin(a),0,math.cos(a)));nr_=Vector((math.cos(a),0,math.sin(a)))
            w_=a*7+s_*math.pi;pts.append(c+(nr_*math.cos(w_)+Vector((0,1,0))*math.sin(w_))*.0045)
        tube(f'LV01_Handle{s_}',pts,.0058,M['hemp'],'Body',sides=6,scale=.05)
    # the repair: a fresher, wider strip over a broken one (front, a little left of centre), tied at two places
    th=-math.pi/2-.42;phis=list(np.linspace(.62,1.25,10))
    _strip('LV01_Repair',[dome(p,th,.012) for p in phis],lambda k:dn(phis[k],th),.032,.006,M['bamboo_split'],'Body')
    for p in (.70,1.17):
        c=dome(p,th,.012);ax=(dome(p+.01,th)-dome(p-.01,th)).normalized()
        _ring(f'LV01_RepairTie{int(p*100)}',c,ax,.021,.0022,M['hemp'],'Body',n=13)
    # straw caught in the weave low down and two feathers on the ground against the rim (Detail_)
    sr=random.Random(7)
    for k in range(9):
        th=-math.pi/2+.35+k*.13+sr.uniform(-.05,.05);a_=Vector((.352*math.cos(th),.352*math.sin(th),.05));b_=dome(sr.uniform(1.28,1.42),th+sr.uniform(-.06,.06),.018)   # lying inside on the ground, the ends poking out between the strips
        tube(f'LV01_Straw{k}',[a_,a_.lerp(b_,.6)+Vector((0,0,.006)),b_],.0018,M['straw'],'Detail_Straw',sides=4,scale=.06)
    for k,(th,rot) in enumerate(((-math.pi/2+.9,.6),(-math.pi/2-1.2,-.4))):
        c=Vector((.405*math.cos(th),.405*math.sin(th),.0035));d=Vector((-math.sin(th+rot*.3),math.cos(th+rot*.3),0));s=Vector((-d.y,d.x,0));rows=[]   # along the rim
        for u in np.linspace(0,1,7):
            w_=max(.0016,.012*math.sin(math.pi*min(1,u*1.15))**.8);p=c+d*(u-.5)*.065+Vector((0,0,.002*math.sin(math.pi*u)))
            rows.append([tuple(p-s*w_),tuple(p+Vector((0,0,.0012))),tuple(p+s*w_*.8)])
        _sheet(f'LV01_Feather{k}',rows,None,M,M['feather'],'Detail_Feathers',t=.0015)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];pz=P[...,2]
        low=np.clip((.11-pz)/.09,0,1)*filled   # the bottom rim and the strips' feet: darker, earth on them
        col=col*(1-.30*low[...,None])+low[...,None]*np.array([.05,.035,.02]);rough=np.clip(rough+.05*low,0,1)
        moss=filled*np.clip((noise-.45)*2.5,0,1)*np.clip(1-np.abs(pz-.25)/.2,0,1)*np.clip(onrm[...,2]+.4,0,1)   # a green-grey bloom on the strips, as cand-3
        col=col*.9*(1-.22*moss[...,None])+moss[...,None]*np.array([.06,.08,.02])
        return col,rough
    return {'paint':paint,'wear':.9,'grime':1.0,'uv_angle':50,'notes':['an upturned dome (0.8 × 0.6 m): 16 strips from the top knot to the rim, 6 rings over and under them',
            'thick bottom rim bound with rope at 8 places; one fresher repair strip tied over a broken one',
            'Detail_Straw: straw caught in the weave; Detail_Feathers: two feathers by the rim']}
PROPS['LV01']=LV01

# ---------------- LV02 twig broom and wooden dustpan (cand-3, laid down) ----------------
def LV02(M):
    """cand-3 draws the broom standing, but the prompt and the pack's 0.3 m height have it lying beside the dustpan: the
    broom lies along X, its bound head resting on the ground and the bamboo handle sloping down to its end; a bundle of dry
    twigs bound in three places and splayed into a flat, worn fan; a rope wrap and a frayed tail at the handle top, a cloth
    band tied across mid-handle. Beside the handle, a dustpan of three floor boards, two wedge side boards, a back board and
    a horseshoe grip lashed on with crossed rope; a patch board nailed into the floor; the front lip scuffed."""
    rr=random.Random(206)   # 202–205 and 207 left a few crossing twigs coplanar (loose QA)
    xb0,xb1,xe=-.41,-.24,.62   # binding start … where the handle leaves the bundle … handle end
    hy=-.058;zb=.040;ze=.0165   # broom axis: y, height at the binding, height of the handle end (it rests on the ground there)
    ax=lambda x:Vector((x,hy,zb+(ze-zb)*max(0,(x-xb1)/(xe-xb1))))
    cs0,cs1=xb1+.02,xb0-.095;crad=lambda x:float(np.interp((x-cs0)/(cs1-cs0),[0,.3,.62,.8,1],[.022,.030,.035,.040,.0]))   # the bound core's radius at x
    # the twigs: from inside the bound part out to a flat fan, the lower ones pressed on the ground
    NT=64
    for k in range(NT):
        a=rr.uniform(0,math.tau);x0=rr.uniform(xb0-.085,xb0-.012);r0=crad(x0)-.003;p0=ax(x0)+Vector((0,r0*math.cos(a),r0*math.sin(a)))   # from the flared end of the bound core, spread over its surface (from its end face they ran side by side, coplanar)
        sy=math.cos(a)*rr.uniform(.5,1.0)+rr.uniform(-.3,.3);L=rr.uniform(.30,.44)
        tip=Vector((xb0+.15-L,hy+sy*.11,max(.004,zb+math.sin(a)*rr.uniform(.012,.05)-.02)))
        rad=Vector((0,math.cos(a),math.sin(a)));mid=p0.lerp(tip,.40)+Vector((0,rr.uniform(-.012,.012),rr.uniform(-.004,.01)));pts=[p0,p0+Vector((-.02,0,0))+rad*.012,mid,mid.lerp(tip,.55)+Vector((0,rr.uniform(-.02,.02),0)),tip]   # each twig a little crooked
        fl=.0036+rr.uniform(0,.0075);pts=[Vector((p.x,p.y,max(p.z,fl+.008*(1-i/4)))) for i,p in enumerate(pts)]   # only the tip touches the ground, each at its own height (pressed flat, crossing twigs' faces lay coplanar)
        rl=rr.uniform(0,math.tau);rt=rr.uniform(.0024,.0032)
        _taper(f'LV02_Twig{k:02d}',pts,[.0005,rt,rt*.95,rt*.75,.0006],M['twig'],'Body',up=(0,math.cos(rl),math.sin(rl)))   # thin at both ends: same-plane end caps of 90 twigs lay coplanar
        if k%4==0:   # a forked side twig
            b0=pts[2];bt=b0+Vector((-.09,rr.uniform(-.04,.04),.0));bt.z=max(.0035+rr.uniform(0,.0075),bt.z)
            _taper(f'LV02_Fork{k:02d}',[b0,b0.lerp(bt,.5)+Vector((0,0,.002)),bt],[.0016,.0016,.0005],M['twig'],'Body',up=(0,math.sin(k),math.cos(k)))
    _lathe('LV02_Bundle',[(0,.022),(.3,.030),(.62,.035),(.8,.040),(1,.0)],(ax(cs0),ax(cs1)),M['twig'],'Body',NS=14)   # the bound core the wraps sit on, flaring where the twigs spread
    for j,(x,n) in enumerate(((xb1-.012,6),(xb1-.075,4),(xb0+.012,7))):   # three bindings, unevenly wide, hugging the core
        pts=[]
        for q in np.linspace(0,math.tau*n,n*12):xx=x-.0052*q/math.tau;r_=crad(xx)+.0024;pts.append(ax(xx)+Vector((0,r_*math.cos(q),r_*math.sin(q))))
        tube(f'LV02_Bind{j}',pts,.0026,M['hemp'],'Body',sides=5,scale=.05)
    # the bamboo handle, a rope wrap at its top end with a frayed tail, a dark cloth band tied mid-handle
    xs=list(np.linspace(xb1+.01,xe,14))
    _cane('LV02_Handle',[ax(x) for x in xs],[.0155-.0015*(x-xb1)/(xe-xb1) for x in xs],M['bamboo'],'Body',nodes=[.19,.38,.55,.71],sides=10)
    for q_ in range(7):
        x=xe-.012-q_*.0058;r_=.0172
        tube(f'LV02_TopWrap{q_}',[ax(x)+Vector((0,r_*math.cos(a),r_*math.sin(a))) for a in np.linspace(0,math.tau,15)],.0026,M['hemp'],'Body',sides=5,scale=.05)
    t0=ax(xe-.03)+Vector((0,-.017,.004))
    tube('LV02_TopTail',[t0,t0+Vector((-.012,-.012,-.008)),t0+Vector((-.028,-.02,-.012)),Vector((t0.x-.045,t0.y-.022,.003))],.0022,M['hemp'],'Detail_Tail',sides=4,scale=.05)
    xc=.18
    _lathe('LV02_Cloth',[(0,.0138),(.12,.0178),(.88,.0178),(1,.0138)],(ax(xc-.035),ax(xc+.035)),M['linen_blue'],'Body',NS=14)
    for s_ in (1,-1):   # two cords crossing over the cloth band
        tube(f'LV02_ClothTie{s_}',[ax(xc+s_*.03-s_*.06*a/math.tau)+Vector((0,.0185*math.cos(a+(s_<0)*math.pi),.0185*math.sin(a+(s_<0)*math.pi))) for a in np.linspace(0,math.tau,17)],.0018,M['hemp'],'Body',sides=4,scale=.05)   # the second starts half a turn round (one's start on the other's end was coplanar)
    # the dustpan, beside the handle: floor of three boards, wedge sides, back board, horseshoe grip
    W,y0,y1=.27,-.030,.188;cx=.18   # width, front lip y, back y, centre x
    for i in range(3):
        xa=cx-W/2+.0125+i*(W-.025)/3+.0012;xb=xa+(W-.025)/3-.0024   # between the side boards, not under them (their bottoms lay coplanar)
        box(f'LV02_Floor{i}',(xb-xa,y1-y0-.0175,.011),((xa+xb)/2,(y0+y1-.0145)/2,.0055),M['cedar_b'],'Body',bev=.0018,segs=1,jit=.0004,seed=210+i)
    hb=.145
    for sgn in (-1,1):   # wedge side boards: low at the lip, full height at the back (drawn in Y–Z, turned into place)
        o=_plate(f'LV02_Side{"LR"[sgn>0]}',[(y0+.004,0),(y0+.004,.016),(y1,hb),(y1,0)],-.006,.006,M['cedar_b'],'Body',bev=.002,jit=.0004,seed=215+sgn)
        o.data.transform(Matrix.Rotation(math.pi/2,4,'Z'));o.data.transform(Matrix.Scale(-1,4,(1,0,0)));o.data.transform(Matrix.Translation((cx+sgn*(W/2-.006),0,0)))
    _plate('LV02_Back',[(cx-W/2+.012,0),(cx-W/2+.012,hb-.004),(cx-.04,hb+.006),(cx+.04,hb+.006),(cx+W/2-.012,hb-.004),(cx+W/2-.012,0)],y1-.014,y1,M['cedar_b'],'Body',bev=.002,jit=.0004,seed=219)
    gz=hb+.055;outer=[(cx+.026*math.cos(a),gz+.03*math.sin(a)) for a in np.linspace(0,math.pi,9)];inner=[(cx+.012*math.cos(a),gz+.015*math.sin(a)) for a in np.linspace(math.pi,0,7)]
    _plate('LV02_Grip',[(cx+.026,hb-.03)]+outer+[(cx-.026,hb-.03),(cx-.012,hb-.03),(cx-.012,gz)]+inner+[(cx+.012,gz),(cx+.012,hb-.03)],y1-.012,y1+.008,M['cedar'],'Body',bev=.0025,jit=.0003,seed=220)
    for s_ in (1,-1):   # crossed rope lashing the grip's legs to the top of the back board
        c=Vector((cx,y1-.003,hb-.006))
        pts=[c+Vector((s_*.024*math.cos(a),.0135*math.sin(a),.02*math.cos(a))) for a in np.linspace(0,math.tau,15)]
        tube(f'LV02_GripTie{s_}',pts,.0024,M['hemp'],'Body',sides=5,scale=.05)
    box('LV02_Patch',(.07,.06,.004),(cx+.065,y0+.05,.0125),M['cedar_new'],'Body',bev=.001,segs=1,jit=.0003,seed=222)
    for k,(dx,dy) in enumerate(((-.028,-.023),(.028,-.023),(-.028,.023),(.028,.023))):   # nail heads in the patch
        _rod(f'LV02_Nail{k}',(cx+.065+dx,y0+.05+dy,.0115),(cx+.065+dx,y0+.05+dy,.0162),.0028,M['iron'],'Detail_Nails',sides=6)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        held=filled*np.clip(1-np.abs(px-(xe-.12))/.1,0,1)*(np.abs(py-hy)<.03)   # where the hand holds the handle: smoother, a touch lighter
        col=col*(1+.15*held[...,None]);rough=np.clip(rough-.25*held,0,1)
        tips=filled*np.clip((xb1-.25-px)/.15,0,1)   # the worn broom tips: paler with dust
        col=col*(1-.1*tips[...,None])+tips[...,None]*np.array([.05,.045,.035])
        pan=filled*(px>cx-W/2-.01)*(py>y0-.01)*np.clip((.03-pz)/.03,0,1)   # dirt on the pan floor
        col=col*(1-.15*pan[...,None]);return col,rough
    return {'paint':paint,'wear':1.1,'grime':.9,'uv_angle':50,'notes':['lying down beside the dustpan (cand-3 draws it standing; the prompt and the 0.3 m height have it lying)',
            f'{NT} twigs (some forked) bound in three places into a flat worn fan; bamboo handle with a rope wrap at the top and a cloth band tied mid-way',
            'dustpan: three floor boards, wedge sides, back board and a horseshoe grip lashed with crossed rope; a patch board nailed into the floor',
            'Detail_Tail: the frayed rope tail at the handle top; Detail_Nails: the patch nail heads']}
PROPS['LV02']=LV02

# ---------------- LV03 bamboo ladder (cand-4) ----------------
def LV03(M):
    """two thick bamboo poles, wider apart at the foot than at the top, with nodes at uneven spacing; seven rungs lashed to
    them, each joint the same way (turns round the pole above and below the rung, two turns crossed over it in an X);
    the fourth rung a fresher bamboo replacement; the rungs dark and worn smooth in the middle where they are stepped on.
    Built upright (the pack's 0.1 m depth): leaning it against a wall is done when it is placed."""
    rr=random.Random(303);Hh=2.38;rp0,rp1=.031,.026
    px=lambda z,s:s*(.207-.03*z/Hh)   # pole axis x at height z (s = -1 left, +1 right)
    pr=lambda z:rp0+(rp1-rp0)*z/Hh
    for s in (-1,1):
        nodes=sorted({round(z,3) for z in np.cumsum([rr.uniform(.27,.36) for _ in range(9)]) if .1<z<Hh-.08})
        zs=sorted(set([.0,Hh]+list(np.linspace(0,Hh,26))+[n+d for n in nodes for d in (-.014,-.006,0,.006,.014)]))
        zs=[z for z in zs if 0<=z<=Hh]
        rad=[pr(z)*(1+.13*max(0,1-min(abs(z-n) for n in nodes)/.014)) for z in zs]   # a raised ring at each node
        _taper(f'LV03_Pole{"LR"[s>0]}',[(px(z,s)+.002*math.sin(z*3+s),0,z) for z in zs],rad,M['bamboo'],'Body',sides=10,scale=.3)
    zr=[.27,.585,.89,1.21,1.52,1.84,2.15];zr=[z+rr.uniform(-.02,.02) for z in zr]
    for j,z in enumerate(zr):
        new=j==3;r_=.0165 if not new else .0155
        xa,xb=px(z,-1)+pr(z)*.3,px(z,1)-pr(z)*.3   # the rung's ends sit inside the poles
        sag=-.004 if not new else 0
        pts=[(xa+(xb-xa)*t,0,z+sag*math.sin(math.pi*t)) for t in np.linspace(0,1,9)]
        _taper(f'LV03_Rung{j}',pts,[r_*(1-.08*math.sin(math.pi*t)*(not new)) for t in np.linspace(0,1,9)],M['bamboo_split'] if new else M['cedar'],'Body',sides=8,scale=.25)
        if new:   # the fresh bamboo rung has two nodes of its own
            for t in (.3,.72):
                c=Vector((xa+(xb-xa)*t,0,z));_lathe(f'LV03_RungNode{int(t*100)}',[(0,r_*.96),(.5,r_*1.12),(1,r_*.96)],(c-Vector((.006,0,0)),c+Vector((.006,0,0))),M['bamboo_split'],'Body',NS=8)
        for s in (-1,1):   # the lashing at each end of the rung
            P=Vector((px(z,s),0,z));R_=pr(z)+.0028;k0=j*2+(s>0)
            for side,zz in (('A',.026),('B',-.026)):   # turns round the pole above and below the rung
                pts=[]
                for q in np.linspace(0,math.tau*2,21):pts.append(P+Vector((R_*math.cos(q),R_*math.sin(q),zz+math.copysign(.0054,zz)*q/math.tau-math.copysign(.004,zz))))
                tube(f'LV03_Wrap{k0}{side}',pts,.0025,M['hemp'],'Body',sides=4,scale=.05)
            inw=Vector((-s,0,0))
            for d in (1,-1):   # two turns crossed over the joint, a rounded loop in a plane tipped 45°
                u=(Vector((0,0,1))+inw*d).normalized();w=Vector((0,1,0));v=u.cross(w).normalized()
                pts=[P+w*(R_+.003)*math.cos(q)+v*((R_+.0085)*1.42)*math.sin(q) for q in np.linspace(0,math.tau,17)]   # clear of the pole on its outer side too (shifted 12 mm in, it grazed the pole there)
                pts[-1]=pts[-1]+w*.004   # the end rides beside the start
                tube(f'LV03_X{k0}{"pm"[d<0]}',pts,.0024,M['hemp'],'Body',sides=4,scale=.05)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px_,pz=P[...,0],P[...,2]
        foot=filled*np.clip((.35-pz)/.3,0,1);moss=foot*np.clip((noise-.45)*2.5,0,1)   # the feet: earth and a little moss
        col=col*(1-.30*foot[...,None])+moss[...,None]*np.array([.06,.09,.02]);rough=np.clip(rough+.05*foot,0,1)
        step=filled*np.clip(1-np.abs(px_)/.1,0,1)*np.clip(onrm[...,2],0,1)   # rung tops in the middle: trodden darker and smooth
        col=col*(1-.18*step[...,None]);rough=np.clip(rough-.2*step,0,1)
        return col,rough
    return {'paint':paint,'wear':.9,'grime':.9,'uv_angle':50,'notes':['built upright, 0.5 wide × 2.4 high (the pack\'s 0.1 m depth): lean it against a wall when placed',
            'two poles with nodes at uneven spacing, wider at the foot; seven rungs lashed the same way at every joint (turns above and below, an X over the rung)',
            'the fourth rung is a fresher bamboo replacement; rung tops darker in the middle where they are stepped on']}
PROPS['LV03']=LV03

def _shell(name,prof,thick,NS,mat,grp,zfun=None,scale=.3):
    """a thin bowl turned about Z: prof = [(r, z)] from the bottom centre out to the rim (outer surface); the inner
    surface is the same moved in by thick; zfun(theta, r) adds height (a sagging rim); closed at the bottom by fans"""
    bm=bmesh.new();zf=zfun or (lambda th,r:0.)
    def ring(r,z,th_off=0.):return [bm.verts.new((r*math.cos(math.tau*k/NS),r*math.sin(math.tau*k/NS),z+zf(math.tau*k/NS,r))) for k in range(NS)]
    outer=[ring(r,z) for r,z in prof];inner=[ring(max(.002,r-thick*.7),z+thick) for r,z in prof]
    co=bm.verts.new((0,0,prof[0][1]+zf(0,0)));ci=bm.verts.new((0,0,prof[0][1]+thick+zf(0,0)))
    for k in range(NS):bm.faces.new((co,outer[0][(k+1)%NS],outer[0][k]));bm.faces.new((ci,inner[0][k],inner[0][(k+1)%NS]))
    for A_,B_ in zip(outer,outer[1:]):
        for k in range(NS):bm.faces.new((A_[k],A_[(k+1)%NS],B_[(k+1)%NS],B_[k]))
    for A_,B_ in zip(inner,inner[1:]):
        for k in range(NS):bm.faces.new((A_[k],B_[k],B_[(k+1)%NS],A_[(k+1)%NS]))
    for k in range(NS):bm.faces.new((outer[-1][k],outer[-1][(k+1)%NS],inner[-1][(k+1)%NS],inner[-1][k]))   # the cut edge at the rim
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)

# ---------------- LV04 hanging bamboo basket drying vegetables (cand-1) ----------------
def LV04(M):
    """a shallow round basket of split bamboo (the weave in the texture), bound round its rim with a thick strip, the rim
    sagging a little on one side; three hemp cords tied to the rim go up to a knot and a loop to hang it by, their ends and
    fibres frayed; a few dried leaves and red chillies lying in it; a grey cloth patch on the side.
    The origin is at the bottom of the basket: on its own it stands on the ground, cords up (it is hung when placed)."""
    R=.228;Hb=.112;NS=40
    sag=lambda th,r:-.010*max(0,math.cos(th-2.4))**2*(r/R)**2   # the rim droops a little on one side
    prof=[(.0,.0),(.05,.0015),(.10,.006),(.15,.018),(.19,.040),(.214,.066),(.225,.090),(R,Hb)]
    _shell('LV04_Basket',prof,.007,NS,M['weave'],'Body',zfun=sag,scale=.32)
    rimz=lambda th:Hb+sag(th,R)
    rp=[Vector(((R+.002)*math.cos(t),(R+.002)*math.sin(t),rimz(t)+.004)) for t in np.linspace(0,math.tau,61)][:-1]
    _strip('LV04_Rim',rp+[rp[0]+(rp[1]-rp[0])*.3+Vector((0,0,.0))],lambda i:Vector((math.cos(math.tau*i/60),math.sin(math.tau*i/60),0)),.022,.007,M['bamboo_old'],'Body')
    for k in range(12):   # thin strips lashing the rim band on, every 30°
        th=math.tau*(k+.37)/12;c=Vector((R*math.cos(th),R*math.sin(th),rimz(th)+.002));rd=Vector((math.cos(th),math.sin(th),0));tg=Vector((-math.sin(th),math.cos(th),0))
        pts=[c+rd*(.0115*math.copysign(abs(math.cos(a))**.5,math.cos(a)))+Vector((0,0,.0165*math.copysign(abs(math.sin(a))**.5,math.sin(a)))) for a in np.linspace(0,math.tau,15)]
        pts[-1]=pts[-1]+tg*.004
        _strip(f'LV04_Lash{k:02d}',pts,lambda i,tg=tg:tg,.006,.0018,M['bamboo_split'],'Body')
    # three cords from the rim up to a knot, then one up to the hanging loop
    kz=.60;K_=Vector((0,0,kz))
    for j,th in enumerate((math.pi/2,math.pi/2+math.tau/3,math.pi/2+2*math.tau/3)):
        a_=Vector(((R+.004)*math.cos(th),(R+.004)*math.sin(th),rimz(th)+.004))
        pts=[a_+Vector((0,0,-.006)),a_+Vector((0,0,.03))]+[a_.lerp(K_,t)+Vector((0,0,.008*math.sin(math.pi*t))) for t in np.linspace(.12,.97,8)]
        tube(f'LV04_Cord{j}',pts,.0055,M['hemp'],'Body',sides=6,scale=.08)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.011,location=a_+Vector((0,0,.004)));kk=bpy.context.object;kk.scale=(1.1,1.1,1.35);bpy.ops.object.transform_apply(scale=True)
        bm=bmesh.new();bm.from_mesh(kk.data);bpy.data.objects.remove(kk);finish(f'LV04_RimKnot{j}',bm,M['hemp'],'Body',.06)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.017,location=K_+Vector((0,0,.006)));kk=bpy.context.object;kk.scale=(1,1,1.4);bpy.ops.object.transform_apply(scale=True)
    bm=bmesh.new();bm.from_mesh(kk.data);bpy.data.objects.remove(kk);finish('LV04_Knot',bm,M['hemp'],'Body',.06)
    lp=[K_+Vector((.005,0,.014)),K_+Vector((.006,0,.05))]+[Vector((.021*math.sin(a),.0,kz+.115-.045*math.cos(a))) for a in np.linspace(.5,math.tau-.5,13)]+[K_+Vector((-.006,0,.05)),K_+Vector((-.005,0,.014))]
    tube('LV04_Loop',lp,.0052,M['hemp'],'Body',sides=6,scale=.08)
    fr=random.Random(41)
    for k in range(14):   # frayed fibres sticking out of the cords (Detail_)
        j=k%3;th=(math.pi/2,math.pi/2+math.tau/3,math.pi/2+2*math.tau/3)[j];a_=Vector((R*math.cos(th),R*math.sin(th),rimz(th)));t=fr.uniform(.15,.9)
        p=a_.lerp(K_,t);d=Vector((fr.uniform(-1,1),fr.uniform(-1,1),fr.uniform(-.6,.3))).normalized()
        tube(f'LV04_Fray{k:02d}',[p,p+d*.012,p+d*.022+Vector((0,0,-.006))],.0009,M['hemp'],'Detail_Frays',sides=3,scale=.04)
    # dried leaves and chillies lying in the basket, following its inside
    zin=lambda r:float(np.interp(r,[p_[0] for p_ in prof],[p_[1] for p_ in prof]))+.007
    lr=random.Random(42)
    for k,(cx_,cy_,ang,L,W_) in enumerate(((-.07,.04,.6,.17,.07),(-.02,-.06,2.2,.15,.06),(.06,.07,-.9,.14,.065),(-.10,-.05,1.4,.12,.05))):
        d=Vector((math.cos(ang),math.sin(ang),0));s_=Vector((-d.y,d.x,0));rows=[]
        for u in np.linspace(0,1,7):
            w_=max(.004,W_*math.sin(math.pi*min(1,u*1.05))**.7)
            row=[]
            for v in np.linspace(-1,1,5):
                p=Vector((cx_,cy_,0))+d*(u-.5)*L+s_*v*w_*.5;r_=math.hypot(p.x,p.y)
                p.z=zin(r_)+.0035+.0035*(1-v*v)*math.sin(u*9+k)+.003*k+.0025*math.sin(v*6+u*7)   # crinkled, each leaf a little above the last
                row.append(tuple(p))
            rows.append(row)
        _sheet(f'LV04_Leaf{k}',rows,None,None,M['leaf_dry'],'Body',t=.0015)
    for k,(cx_,cy_,ang) in enumerate(((.085,-.035,.3),(.12,.005,-.4),(.075,-.115,1.0),(.145,-.065,.9),(.15,.06,2.6))):   # on the basket floor, clear of the leaves
        d=Vector((math.cos(ang),math.sin(ang),0));s_=Vector((-d.y,d.x,0));L=lr.uniform(.07,.095)
        pts=[];rad=[]
        for u in np.linspace(0,1,8):
            p=Vector((cx_,cy_,0))+d*(u-.5)*L+s_*.012*math.sin(math.pi*u)*(1 if k%2 else -1);r_=math.hypot(p.x,p.y);rr_=.0085*(1-u**2.2)**.6+.0012
            p.z=zin(r_)+rr_+.0004;pts.append(p);rad.append(rr_)   # lying on the basket floor
        _taper(f'LV04_Chilli{k}',pts,rad,M['chilli'],'Body',sides=8,scale=.1)
        st=pts[0]-d*.004;tube(f'LV04_Stem{k}',[pts[0]+d*.002,st,st-d*.008+Vector((0,0,.004))],.0018,M['leaf_dry'],'Body',sides=5,scale=.05)
    # the grey cloth patch on the side, sewn on with a few stitches
    th0=-2.1;rows=[]
    for v in np.linspace(.040,.092,5):
        row=[]
        for t in np.linspace(th0-.17,th0+.17,6):
            r_=float(np.interp(v,[p_[1] for p_ in prof],[p_[0] for p_ in prof]))+.0035;row.append((r_*math.cos(t),r_*math.sin(t),v+sag(t,r_)))
        rows.append(row)
    _sheet('LV04_Patch',rows,None,None,M['ash'],'Body',t=.0016)   # a grey cloth (the pale linen read as paper)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];pz=P[...,2]
        under=filled*np.clip((.05-pz)/.05,0,1)*np.clip(-onrm[...,2],0,1)   # the underside: darker, a little green
        col=col*(1-.25*under[...,None])+under[...,None]*np.array([.03,.05,.01]);return col,rough
    return {'paint':paint,'wear':.9,'grime':.8,'uv_angle':50,'notes':['a shallow basket (0.46 m across) with its rim drooping a little on one side; the weave is in the texture, the rim band lashed every 30°',
            'three cords tied to the rim go up to a knot and a hanging loop (0.8 m high in all); the origin is at the basket bottom: it stands on the ground until hung',
            'four dried leaves and five chillies lying in it; a grey cloth patch on the side','Detail_Frays: fibres sticking out of the cords']}
PROPS['LV04']=LV04

# ---------------- LV05 three pickling jars with lids and press stones (cand-2) ----------------
def LV05(M):
    """three wide-mouthed glazed jars, each its own outline (not BM03's narrow-necked pot): a big one with broad shoulders, a
    straight-sided middle one, a squat small one; the mouths unglazed, a thick clay lid on each and a smooth river stone
    pressing it down; glaze drips running down from the shoulders, the big lid chipped, damp dark earth round the feet.
    The three stand apart (each can be moved on its own) and are not joined."""
    J=[   # name, centre x, y, height of the jar body, profile [(s, r)] from foot to mouth, lid radius, stone size
        ('Big',.08,.05,.43,[(0,.120),(.06,.128),(.25,.158),(.48,.175),(.66,.172),(.82,.150),(.93,.128),(.97,.126),(1,.128)],.152,(.075,.058,.042)),
        ('Mid',-.285,-.035,.30,[(0,.098),(.06,.105),(.30,.122),(.60,.124),(.82,.116),(.93,.103),(.97,.101),(1,.103)],.124,(.055,.045,.032)),
        ('Small',.335,-.115,.215,[(0,.080),(.08,.090),(.35,.104),(.62,.103),(.84,.090),(.95,.082),(1,.083)],.102,(.045,.038,.028)),
    ]
    info=[]
    for k,(nm,cx,cy,H,prof,lr,st) in enumerate(J):
        c0=Vector((cx,cy,0));top=Vector((cx,cy,H))
        sn=prof[-2][0];_lathe(f'LV05_{nm}Jar',[(s_/sn,r_) for s_,r_ in prof[:-1]],(c0,c0+Vector((0,0,H*sn))),M['glaze'],'Body',NS=36)   # the glazed body up to the neck (profile s rescaled to this shorter axis)
        ra=prof[-2][1];rb=prof[-1][1]
        _lathe(f'LV05_{nm}Mouth',[(0,ra-.0015),(.35,rb+.004),(1,rb+.003)],(c0+Vector((0,0,H*prof[-2][0]-.004)),top),M['clay'],'Body',NS=36)   # the unglazed mouth band
        lt=.034 if k==0 else .028
        lid=_lathe(f'LV05_{nm}Lid',[(0,lr-.004),(.15,lr),(.85,lr),(1,lr-.006),(1,0)],(top-Vector((0,0,.004)),top+Vector((0,0,lt))),M['clay'],'Body',NS=36)
        if k==0:   # the chipped edge of the big lid
            ct=_cutter('LV05_Chip',(.07,.05,.04),(0,0,0));tn_=Vector((-.62,.80,0)).normalized()   # a chunk off the top edge: a cutter tipped over the edge, not a square notch
            ct.data.transform(Matrix.Rotation(.75,4,tn_));ct.data.transform(Matrix.Translation((cx-lr*.86,cy-lr*.66,H+lt+.006)));_boolean(lid,ct)
        sz=Vector(st);bpy.ops.mesh.primitive_uv_sphere_add(segments=18,ring_count=10,radius=1,location=(cx+.01*(k-1),cy-.006*k,H+lt+sz.z*.82));so=bpy.context.object
        so.scale=sz;so.rotation_euler=(0,.08*(k-1),.4+k);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        bm=bmesh.new();bm.from_mesh(so.data);bpy.data.objects.remove(so)
        for v in bm.verts:   # a river stone: rounded, a little lopsided, flat where it sits on the lid
            v.co.x*=1+.08*math.sin(v.co.y*40+k);v.co.z=max(v.co.z,-sz.z*.82+.001)
        for f_ in bm.faces:f_.smooth=True
        bmesh.ops.translate(bm,verts=bm.verts,vec=(cx+.01*(k-1),cy-.006*k,H+lt+sz.z*.82));finish(f'LV05_{nm}Stone',bm,M['stone'],'Body',.25)
        info.append((cx,cy,H,max(r for _,r in prof)))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        for cx,cy,H,R in info:
            on=filled*(np.hypot(px-cx,py-cy)<R+.006)*(pz<H*.93)
            th=np.arctan2(py-cy,px-cx);h=pz/H
            L=.25+.35*(.5+.5*np.sin(th*11+cx*40))   # each drip its own length
            drip=on*np.clip((np.sin(th*23+2.5*np.sin(th*7+cy*30))-.62)*4,0,1)*np.clip((h-(.80-L))/.08,0,1)*np.clip((.86-h)/.05,0,1)
            col=col*(1-.55*drip[...,None])+drip[...,None]*np.array([.50,.28,.14])*.55;rough=np.clip(rough+.15*drip,0,1)
            foot=on*np.clip((.10-pz)/.08,0,1)   # damp earth splashed up the foot, a little moss
            moss=foot*np.clip((noise-.5)*3,0,1)
            col=col*(1-.35*foot[...,None])+moss[...,None]*np.array([.05,.08,.02]);rough=np.clip(rough+.3*foot,0,1)
        return col,rough
    return {'paint':paint,'wear':.8,'grime':.9,'uv_angle':50,'notes':['three jars standing apart (not joined): big 0.35 × 0.47 m with broad shoulders, middle straight-sided, small squat',
            'wide mouths with an unglazed band, a thick clay lid on each and a river stone pressing it; the big lid chipped',
            'unlike BM03 (narrow neck, no lid): wide mouth, heavy lid, press stone; glaze drips and damp earth round the feet are painted']}
PROPS['LV05']=LV05

# ---------------- LV06 chopping block with a chopping knife (cand-4) ----------------
def LV06(M):
    """a thick stump, its foot flaring into root lobes, pale weathered wood with a few strips of bark still on and peeling
    away at the top; the cut top shows growth rings, radial checks and many crossing cut marks; a broad chopping knife
    driven into the top at a slant, its wooden handle bound with cloth; three split logs and some chips at its foot."""
    H=.40;NS=40;rr=random.Random(606)
    for k_ in ('bark','cedar_new','iron','cedar','linen_b','endgrain'):M[k_]['mid']=1   # paint mask: everything but the stump wood
    def rad(z,th):
        base=float(np.interp(z,[0,.03,.09,.18,H],[.228,.212,.188,.176,.168]))
        lobe=.12*max(0,math.cos(5*th+.7))**2*max(0,1-z/.16)   # root lobes at the foot
        return base*(1+lobe+.025*math.sin(3*th+1.3)+.012*math.sin(7*th))
    zs=[0,.012,.03,.06,.09,.13,.18,.24,.30,.35,.385,H-.006]
    bm=bmesh.new();rings=[[bm.verts.new((rad(z,math.tau*k/NS)*math.cos(math.tau*k/NS),rad(z,math.tau*k/NS)*math.sin(math.tau*k/NS),z)) for k in range(NS)] for z in zs]
    for A_,B_ in zip(rings,rings[1:]):
        for k in range(NS):bm.faces.new((A_[k],A_[(k+1)%NS],B_[(k+1)%NS],B_[k]))
    bm.faces.new(list(reversed(rings[0])));bm.faces.new(rings[-1])
    for f in bm.faces:f.smooth=True
    finish('LV06_Stump',bm,M['stumpwood'],'Body',.4)
    # the cut top: an end-grain disc set into the trunk's top
    tb=bmesh.new();tr=[[tb.verts.new((rad(H,math.tau*k/NS)*s_*math.cos(math.tau*k/NS),rad(H,math.tau*k/NS)*s_*math.sin(math.tau*k/NS),z)) for k in range(NS)] for s_,z in ((.985,H-.012),(.995,H-.002),(.97,H))]
    for A_,B_ in zip(tr,tr[1:]):
        for k in range(NS):tb.faces.new((A_[k],A_[(k+1)%NS],B_[(k+1)%NS],B_[k]))
    c_=tb.verts.new((0,0,H+.0015));cb=tb.verts.new((0,0,H-.012))
    for k in range(NS):tb.faces.new((c_,tr[-1][k],tr[-1][(k+1)%NS]));tb.faces.new((cb,tr[0][(k+1)%NS],tr[0][k]))
    finish('LV06_Top',tb,M['endgrain'],'Body',.45)
    # strips of bark still on the sides, the top ones peeling outwards
    for k in range(9):
        th0=k*math.tau/9+rr.uniform(-.15,.15);w=rr.uniform(.35,.55);z0=rr.uniform(.003,.03);z1=rr.uniform(.24,H-.015);peel=k%2==0   # down to the roots
        rows=[]
        for z in np.linspace(z0,z1,6):
            row=[]
            for t in np.linspace(-w/2,w/2,5):
                th=th0+t+(.05*math.sin(z*45+k)*(abs(t)>w*.4));out=.006+(.012*((z-(z1-.07))/.07)**2 if peel and z>z1-.07 else 0)   # ragged side edges; curling out at the top
                zz=z+(.022*math.sin(t*31+k*2)*(z>z1-.01))   # a torn, uneven top edge
                rd=rad(zz,th)+out;row.append((rd*math.cos(th),rd*math.sin(th),zz))
            rows.append(row)
        _sheet(f'LV06_Bark{k}',rows,None,None,M['bark'],'Body',t=.008)
    # the chopping knife: a broad blade with a slanted front, driven into the top at a slant, handle bound with cloth
    ang=math.radians(18);Rk=Matrix.Rotation(ang,4,'Y')   # the knife tipped in its own plane: handle end up, front down into the wood
    base=Vector((-.06,-.015,H-.012))   # the back end of the edge, 1.2 cm into the wood (the front goes in 6 cm)
    bl=[(0,0),(.155,0),(.165,.012),(.150,.095),(.0,.088)]   # blade outline (along, up): the edge along the bottom, slanted front
    bmb=bmesh.new();f0=[bmb.verts.new((a,-.0022,b)) for a,b in bl];f1=[bmb.verts.new((a,.0022,b)) for a,b in bl]
    bmb.faces.new(f0);bmb.faces.new(list(reversed(f1)))
    for i in range(len(bl)):bmb.faces.new((f0[i],f1[i],f1[(i+1)%len(bl)],f0[(i+1)%len(bl)]))
    bmesh.ops.recalc_face_normals(bmb,faces=bmb.faces)
    for v in bmb.verts:v.co=Rk@v.co+base
    blade=finish('LV06_Blade',bmb,M['iron'],'Body',.15);bevel(blade,.0012,1,40)
    hd=(Rk@Vector((-1,0,.15))).normalized();h0=Rk@Vector((.004,0,.058))+base;he=h0+hd*.13   # the handle goes on from the blade's back end
    _taper('LV06_Handle',[h0-hd*.004,h0+hd*.02,h0+hd*.07,he],[.0125,.0135,.0145,.0155],M['cedar'],'Body',sides=10,scale=.15)
    for q in range(6):   # cloth bound round the handle next to the blade
        c=h0+hd*(.024+q*.0062);u=hd.orthogonal().normalized();v=hd.cross(u)
        tube(f'LV06_Wrap{q}',[c+(u*math.cos(a)+v*math.sin(a))*.0160+hd*.0055*a/math.tau for a in np.linspace(0,math.tau,13)],.0028,M['linen_b'],'Body',sides=4,scale=.05)
    t0=h0+hd*.06+Vector((0,-.018,0))
    for j,(dx,L) in enumerate(((.004,.05),(-.006,.07))):   # two cloth ends hanging (Detail_)
        tube(f'LV06_ClothEnd{j}',[t0+Vector((dx,.003,.006)),t0+Vector((dx*1.5,-.002,-L*.4)),t0+Vector((dx*2,.0,-L))],.0035,M['linen_b'],'Detail_ClothEnds',sides=4,scale=.05)
    # three split logs and a scatter of chips at the foot
    for k,(x,y,rot,L,R_) in enumerate(((-.10,-.215,.25,.19,.052),(.07,-.225,-.35,.17,.047),(-.01,-.255,1.35,.15,.042))):
        out=[(0,0)]+[(R_*math.cos(a),R_*math.sin(a)) for a in np.linspace(0,math.pi/2*.92,7)]   # a quarter round: two split faces and the bark side
        o=_plate(f'LV06_Log{k}',out,-L/2,L/2,M['cedar_new'],'Body',bev=.002,jit=.0008,seed=620+k)
        o.data.transform(Matrix.Rotation(-math.pi/4-(.2 if k==2 else 0),4,'Y'));o.data.transform(Matrix.Rotation(rot,4,'Z'))
        me=o.data;mz=min(v.co.z for v in me.vertices);o.data.transform(Matrix.Translation((x,y,-mz+(.046 if k==2 else 0))))   # the third rests on the other two
    for k in range(10):
        a=rr.uniform(-2.6,-.5);d=rr.uniform(.22,.27)
        c=Vector((d*math.cos(a),d*math.sin(a),.0016));s_=Vector((rr.uniform(.006,.015),rr.uniform(.004,.008),.0016))
        cb_=bmesh.new();bmesh.ops.create_cube(cb_,size=2);rz=Matrix.Rotation(rr.uniform(0,3),4,'Z')
        for v in cb_.verts:v.co=rz@Vector((v.co.x*s_.x,v.co.y*s_.y,v.co.z*s_.z))+c
        finish(f'LV06_Chip{k}',cb_,M['cedar_new'],'Detail_Chips',.1)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        top=filled*(pz>H-.004)*(onrm[...,2]>.8)*(np.hypot(px,py)<.19)
        cuts=np.zeros_like(pz)
        cr=random.Random(77)
        for _ in range(16):   # crossing cut marks: thin dark lines with a pale fresh edge
            a=cr.uniform(0,math.pi);o_=cr.uniform(-.12,.12);L=cr.uniform(.06,.16);cx_,cy_=o_*math.cos(a+1.57),o_*math.sin(a+1.57)
            d=np.abs((px-cx_)*math.sin(a)-(py-cy_)*math.cos(a));al=np.abs((px-cx_)*math.cos(a)+(py-cy_)*math.sin(a))
            cuts=np.maximum(cuts,np.clip(1-d/.0022,0,1)*(al<L/2))
        col=col*(1-.55*(cuts*top)[...,None]);rough=np.clip(rough+.1*cuts*top,0,1)
        side=filled*(pz<H-.004)*(np.hypot(px,py)<.30)*(1-mid)   # the weathered stump wood: greyer, with darker vertical streaks
        th_=np.arctan2(py,px);streak=np.clip((np.sin(th_*37+3*np.sin(th_*5))-.4)*2,0,1)*(.5+.5*np.sin(pz*9+th_*3))
        col=col*(1-side[...,None]*(.18+.22*streak[...,None]))*np.where(side[...,None]>0,np.array([.97,.97,1.0]),1)
        foot=filled*np.clip((.10-pz)/.09,0,1);moss=foot*np.clip((noise-.45)*3,0,1)   # earth and moss at the foot
        col=col*(1-.30*foot[...,None])+moss[...,None]*np.array([.06,.09,.02])
        return col,rough
    return {'paint':paint,'wear':1.0,'grime':1.0,'uv_angle':50,'notes':['a stump 0.4 m high, its foot flaring into root lobes; pale weathered wood with seven strips of bark, the top ones peeling',
            'the cut top: end grain with growth rings and checks, crossing cut marks painted on it; a broad chopping knife driven in at a slant, handle bound with cloth',
            'three split logs at the foot; Detail_ClothEnds: the hanging cloth ends; Detail_Chips: wood chips']}
PROPS['LV06']=LV06
