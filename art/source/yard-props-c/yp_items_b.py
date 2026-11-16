# YP09, YP11, YP12 shapes (the 11/14 120h pack, batch A), read by build_yp.py after yp_items.py (same namespace).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _flatpoly(name,pts,z0,z1,mat,grp,bev=.003,jit=.0008,seed=1):
    """a board cut to an outline drawn on the ground (x, y), from z0 up to z1"""
    bm=bmesh.new();a=[bm.verts.new((x,y,z0)) for x,y in pts];b=[bm.verts.new((x,y,z1)) for x,y in pts];n=len(pts)
    bm.faces.new(list(reversed(a)));bm.faces.new(b)
    for i in range(n):bm.faces.new((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);o=finish(name,bm,mat,grp)
    if bev:bevel(o,bev,1,angle=50)
    if jit:jitter(o,jit,seed,freq=14)
    return o
def _rows(z0,z1,n,rr,gap=.004):
    """n board rows between z0 and z1, their widths a little unequal"""
    w=[rr.uniform(.85,1.15) for _ in range(n)];s=sum(w);out=[];z=z0
    for k in range(n):
        h=(z1-z0)*w[k]/s;out.append((z+gap/2,z+h-gap/2));z+=h
    return out
def _wall(pid,tag,axis,a,b,off,rows,BT,mats,rr,seed):
    """board rows of one wall: along X (axis 'x', at y = off) or along Y (axis 'y', at x = off), from a to b"""
    for k,(z0,z1) in enumerate(rows):
        L=b-a+rr.uniform(-.004,.004);c=(a+b)/2;size=(L,BT,z1-z0) if axis=='x' else (BT,L,z1-z0);cen=(c,off,(z0+z1)/2) if axis=='x' else (off,c,(z0+z1)/2)
        box(f'{pid}_{tag}{k}',size,cen,mats[(k+seed)%len(mats)],'Body',bev=.003,segs=1,cuts=1,jit=.0012,seed=seed*7+k)
def _nail(name,p,n,mat,r=.0065,grp='Detail_Nails'):
    p=Vector(p);n=Vector(n);return _lathe(name,[(0,r),(.6,r*.8),(1,0)],(p,p+n*.005),mat,grp,NS=6,scale=.03)

def _crate_age(col,rough,h,P,onrm,edge,filled,xp,yp,PW,seed,nail_z=(.06,.17,.28)):
    """old plank box: checks along each board's grain (walls along X or Y, posts upright), rust runs under the post nails"""
    px,py,pz=P[...,0],P[...,1],P[...,2];wood=filled*(col[...,0]>col[...,2]*1.3);vert=np.abs(onrm[...,2])<.6
    post=wood*(np.abs(px)>xp-PW/2-.002)*(np.abs(py)>yp-PW/2-.002)
    col,rough=_wood_age(col,rough,h,P,wood*vert*(np.abs(onrm[...,1])>.7)*(1-post),0,seed,edge,checks=1.2,grey=.28)
    col,rough=_wood_age(col,rough,h,P,wood*vert*(np.abs(onrm[...,0])>.7)*(1-post),1,seed+3,edge,checks=1.2,grey=.28)
    col,rough=_wood_age(col,rough,h,P,post,2,seed+6,edge,grey=.2)
    st=np.clip((_vn(P,(70.,70.,3.),seed+20)-.42)*3,0,1)
    for zn in nail_z:
        run=post*vert*np.clip(1-(zn-pz)/.06,0,1)*(pz<zn-.004)*st;col=col*(1-.34*run[...,None])+run[...,None]*.34*np.array([.30,.17,.09])
    return col,rough

# ---------------- YP09 wooden storage boxes: an open crate and a lidded rice chest (cand-4) ----------------
def YP09_01(M):
    """an open plank crate: four corner posts standing proud of the boards, three board rows on every side set between
    the posts, a boarded bottom, a rope handle through each end, big-headed nails on the posts."""
    rr=random.Random(6901);WD,WB,WN,HP,IR=M['cedar'],M['cedar_b'],M['cedar_new'],M['hemp'],M['iron'];W=.60;D=.40;H=.34;PW=.046;BT=.018
    xp=W/2-PW/2;yp=D/2-PW/2
    for q,(sx,sy) in enumerate(((-1,-1),(1,-1),(-1,1),(1,1))):
        _bar(f'YP09_01_Post{q}',(sx*xp,sy*yp,0),(sx*xp,sy*yp,H+rr.uniform(-.004,.006)),PW,PW,WB if q%2 else WD,'Body',up=(1,0,0),bev=.004,seed=6910+q,jit=.0012)
        for j,z in enumerate((.06,.17,.28)):
            _nail(f'YP09_01_NailF{q}{j}',(sx*xp+rr.uniform(-.004,.004),sy*(D/2),z+rr.uniform(-.008,.008)),(0,sy,0),IR)
            _nail(f'YP09_01_NailE{q}{j}',(sx*(W/2),sy*yp+rr.uniform(-.004,.004),z+.012+rr.uniform(-.008,.008)),(sx,0,0),IR)
    for q,sy in enumerate((-1,1)):_wall('YP09_01',f'Side{q}','x',-xp,xp,sy*yp,_rows(.022,H-.006,3,rr),BT,(WD,WB,WD),rr,q+1)
    for q,sx in enumerate((-1,1)):_wall('YP09_01',f'End{q}','y',-yp,yp,sx*xp,_rows(.022,H-.006,3,rr),BT,(WB,WD,WD),rr,q+3)
    bd=bpy.data.objects.get('YP09_01_Side02')
    if bd:   # the front top board has lost a corner
        cut=_cutter('YP09_01_cutCorner',(.16,.08,.09),(0,0,0));cut.data.transform(Matrix.Rotation(.62,4,'Y'));cut.data.transform(Matrix.Translation((xp-.035,-yp,H+.022)));_boolean(bd,cut)
    bd=bpy.data.objects.get('YP09_01_Side00')
    if bd:   # and the bottom one is split along the grain
        cut=_cutter('YP09_01_cutSplit',(.26,.08,.0045),(0,0,0));cut.data.transform(Matrix.Rotation(-.035,4,'Y'));cut.data.transform(Matrix.Translation((-xp+.10,-yp,.082)));_boolean(bd,cut)
    for k in range(4):   # bottom boards
        x0=-xp+(2*xp)*k/4;x1=-xp+(2*xp)*(k+1)/4;box(f'YP09_01_Bottom{k}',(x1-x0-.004,2*yp,.016),((x0+x1)/2,0,.030),WB,'Body',bev=.002,segs=1,jit=.001,seed=6930+k)
    for q,sx in enumerate((-1,1)):   # a rope handle through each end, knotted inside
        x0=sx*(xp-BT/2-.012);pts=[Vector((x0,-.085,.245))]+[Vector((sx*(xp+BT/2+.004+.040*math.sin(t)),-.085*math.cos(t),.245-.075*math.sin(t)**1.3)) for t in np.linspace(.12,math.pi-.12,11)]+[Vector((x0,.085,.245))]
        rope(f'YP09_01_Handle{q}',pts,.0085,HP,'Body')
        for j,sy in enumerate((-1,1)):
            o=_blob(f'YP09_01_Knot{q}{j}',(.030,.030,.030),6940+q*2+j,HP,'Body',sub=2,bumps=4,amp=.12,scale=.06);o.data.transform(Matrix.Translation((sx*(xp-BT/2-.016),sy*.085,.230)))
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);pz=P[...,2];h=np.zeros(pz.shape,np.float32)
        out=filled*(np.abs(onrm[...,2])<.6)
        col,rough=_crate_age(col,rough,h,P,onrm,edge,filled,xp,yp,PW,6945)
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,out,h=.07,amt=.45,soil=.035)
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':1.,'grime':1.,'damp':.05,'uv_angle':60,'collision_box':((W,D,H),(0,0,H/2)),
            'notes':['four corner posts standing proud; three board rows on every side set between the posts, their widths unequal, gaps between them; four bottom boards; the front top board has lost a corner and the bottom one is split along the grain',
                     'a hemp rope handle through each end, knotted inside; nails on the posts are Detail_Nails','painted, with the relief also in the normal map: checks along every board, sun-greyed patches, rust runs under the nails, damp, soil and moss at the foot']}
PROPS['YP09_01']=YP09_01

def YP09_02(M):
    """a rice chest: taller at the back than at the front, the end walls cut to the slope; a sloping lid of five boards
    with two battens under it, overhanging at the front; two iron strap hinges at the back, a wooden hasp at the front."""
    rr=random.Random(6902);WD,WB,WN,IR=M['cedar'],M['cedar_b'],M['cedar_new'],M['iron'];W=.60;D=.45;PW=.046;BT=.020;HF=.366;HB=.510
    xp=W/2-PW/2;yp=D/2-PW/2;sl=(.532-.372)/D;zl=lambda y:.372+(y+D/2)*sl   # the lid's middle plane
    for q,(sx,sy) in enumerate(((-1,-1),(1,-1),(-1,1),(1,1))):
        h=HF if sy<0 else HB
        _bar(f'YP09_02_Post{q}',(sx*xp,sy*yp,0),(sx*xp,sy*yp,h),PW,PW,WB if q%2 else WD,'Body',up=(1,0,0),bev=.004,seed=6950+q,jit=.0012)
        for j,z in enumerate([.06,.18,.30]+([.44] if sy>0 else [])):
            _nail(f'YP09_02_NailF{q}{j}',(sx*xp+rr.uniform(-.004,.004),sy*(D/2),z+rr.uniform(-.008,.008)),(0,sy,0),IR)
            _nail(f'YP09_02_NailE{q}{j}',(sx*(W/2),sy*yp+rr.uniform(-.004,.004),z+.012+rr.uniform(-.008,.008)),(sx,0,0),IR)
    _wall('YP09_02','Front','x',-xp,xp,-yp,_rows(.022,HF-.012,3,rr),BT,(WD,WB,WD),rr,1)
    _wall('YP09_02','Back','x',-xp,xp,yp,_rows(.022,HB-.012,4,rr),BT,(WB,WD,WD,WB),rr,2)
    for q,sx in enumerate((-1,1)):
        _wall('YP09_02',f'End{q}','y',-yp,yp,sx*xp,_rows(.022,.335,3,rr),BT,(WB,WD,WD),rr,q+3)
        o=_plate(f'YP09_02_Gable{q}',[(-yp,.339),(yp,.339),(yp,HB-.006),(-yp,HF-.006)],-BT/2,BT/2,WD,'Body',bev=.003,jit=.0012,seed=6960+q)   # the end wall's top board, cut to the slope
        o.data.transform(Matrix.Rotation(math.pi/2,4,'Z'));o.data.transform(Matrix.Translation((sx*xp,0,0)))
    for k in range(4):
        x0=-xp+(2*xp)*k/4;x1=-xp+(2*xp)*(k+1)/4;box(f'YP09_02_Bottom{k}',(x1-x0-.004,2*yp,.016),((x0+x1)/2,0,.030),WB,'Body',bev=.002,segs=1,jit=.001,seed=6970+k)
    bd=bpy.data.objects.get('YP09_02_Front1')
    if bd:   # the middle front board is split along the grain
        cut=_cutter('YP09_02_cutSplit',(.24,.08,.0045),(0,0,0));cut.data.transform(Matrix.Rotation(.03,4,'Y'));cut.data.transform(Matrix.Translation((-xp+.09,-yp,.205)));_boolean(bd,cut)
    LW=W+.024;y0=-D/2-.040;y1=D/2+.012;ws=[rr.uniform(.9,1.1) for _ in range(5)];x=-LW/2
    for k in range(5):   # the lid boards run front to back
        w=LW*ws[k]/sum(ws);dz=rr.uniform(-.0015,.0015);dy=rr.uniform(-.006,.004)
        _bar(f'YP09_02_Lid{k}',(x+w/2,y0+dy,zl(y0+dy)+dz),(x+w/2,y1,zl(y1)+dz),w-.004,.021,(WD,WB,WD,WN,WD)[k],'Body',up=(0,0,1),bev=.003,seed=6980+k,jit=.0012);x+=w
    nrm=Vector((0,-sl,1)).normalized()
    for q,y in enumerate((-.10,.10)):   # battens under the lid, inside the chest
        _bar(f'YP09_02_Batten{q}',Vector((-xp+.03,y,zl(y)))-nrm*.0205,Vector((xp-.03,y,zl(y)))-nrm*.0205,.040,.022,WB,'Body',up=nrm,bev=.003,seed=6990+q)
    for q,sx in enumerate((-1,1)):   # strap hinges: one leaf along the lid, one down the back
        xh=sx*.185;a=Vector((xh,.085,zl(.085)))+nrm*.0125;b=Vector((xh,y1-.002,zl(y1-.002)))+nrm*.0125
        _bar(f'YP09_02_HingeLid{q}',a,b,.034,.004,IR,'Body',up=nrm,bev=.001,jit=0,ends=(.75,1.))
        box(f'YP09_02_HingeBack{q}',(.034,.004,.085),(xh,yp+BT/2+.002,HB-.052),IR,'Body',bev=.001,segs=1)
        _rod(f'YP09_02_HingePin{q}',(xh-.021,y1+.004,zl(y1)+.004),(xh+.021,y1+.004,zl(y1)+.004),.006,IR,'Body',sides=8,scale=.05)
        for j,t in enumerate((.25,.7)):_nail(f'YP09_02_HingeNail{q}{j}',a.lerp(b,t)+nrm*.002,nrm,IR,r=.0045)
        _nail(f'YP09_02_HingeNailB{q}',(xh,yp+BT/2+.004,HB-.075),(0,1,0),IR,r=.0045)
    yh=y0+.004;_bar('YP09_02_Hasp',Vector((0,yh-.006,zl(yh)+.004)),Vector((0,yh+.017,zl(yh)-.085)),.040,.016,WB,'Body',up=(0,1,0),bev=.003,jit=.0006,seed=6995)   # a wooden tongue hanging from the lid edge
    box('YP09_02_HaspBlock',(.062,.046,.034),(0,-yp-BT/2-.023,HF-.070),WD,'Body',bev=.003,segs=1,jit=.0006,seed=6996)
    o=box('YP09_02_Patch',(.135,.010,.058),(0,0,0),WN,'Body',bev=.002,segs=1,jit=.0008,seed=6997,rot=Matrix.Rotation(.16,4,'Y'));o.data.transform(Matrix.Translation((.165,-yp-BT/2-.0035,.115)))
    for q,(dx,dz) in enumerate(((-.052,.006),(.052,-.004),(-.05,-.018),(.05,.02))):_nail(f'YP09_02_PatchNail{q}',(.165+dx,-yp-BT/2-.0085,.115+dz),(0,-1,0),IR,r=.0045)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];h=np.zeros(pz.shape,np.float32)
        out=filled*(np.abs(onrm[...,2])<.6)
        col,rough=_crate_age(col,rough,h,P,onrm,edge,filled,xp,yp,PW,6998)
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,out,h=.07,amt=.45,soil=.035)
        lid=filled*(onrm[...,2]>.7)*(pz>.36)*(col[...,0]>col[...,2]*1.3)
        col,rough=_wood_age(col,rough,h,P,lid,1,6999,edge,checks=1.3,grey=.40)
        P2=P*np.array([1,1,0],np.float32)
        for kx,ky,kr in ((-.20,.05,.018),(.07,-.13,.014),(.22,.12,.016)):col=_knot(col,h,P2,(kx,ky,0),kr,lid)
        ms=lid*np.clip((noise-.58)*3+np.clip((np.abs(px)-.2)/.1,0,1)*.4,0,1);col=col*(1-.40*ms[...,None])+ms[...,None]*.40*np.array([.24,.31,.12])   # a little moss on the lid, more toward the sides
        hand=lid*np.clip(1-np.hypot(px/.12,(py+.2)/.07),0,1);col=col*(1+.14*hand[...,None]);rough=np.clip(rough-.18*hand,0,1)                     # worn pale where the lid is lifted
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':1.,'grime':1.,'damp':.05,'uv_angle':60,'collision_box':((W+.02,D+.05,.54),(0,-.014,.27)),
            'notes':['a rice chest taller at the back: four corner posts, board rows between them, the end walls topped by a board cut to the slope; the middle front board is split along the grain',
                     'the lid is five boards running front to back with two battens under it, overhanging at the front; two iron strap hinges with a pin at the back, a wooden tongue and block as the hasp at the front; the lid is closed (one mesh with the chest)',
                     'one board mended with a nailed piece; nails are Detail_Nails; painted, with the relief also in the normal map: checks along every board, knots in the lid, sun-greyed patches, rust runs under the nails, damp and moss at the foot, moss on the lid, the pale worn place where the lid is lifted']}
PROPS['YP09_02']=YP09_02

# ---------------- YP12 large earthenware water vat (cand-3) ----------------
def YP12(M):
    """a big round-bellied vat thrown thick, a rolled rim; dark brown glaze above, bare clay below (painted). A wooden
    lid of three boards under two battens covers a little more than half of the mouth; water inside; a dried-gourd
    dipper with a wooden handle lies on the lid."""
    rr=random.Random(7201);WD,WB=M['cedar'],M['cedar_b'];HT=.80
    prof=[(0,.002),(0,.262),(.03,.284),(.11,.318),(.22,.352),(.36,.384),(.48,.394),(.60,.384),(.72,.356),(.775,.339),(.786,.345),(.797,.334),(.82,.322),(.868,.307),(.879,.313),(.890,.302),(.905,.300),(.935,.303),(.965,.322),(.99,.326),(1,.316),(1,.300),
          (.975,.280),(.94,.266),(.90,.262),(.82,.288),(.72,.326),(.60,.356),(.48,.366),(.36,.356),(.22,.320),(.11,.275),(.06,.235),(.05,.002)]   # two raised cord bands on the shoulder
    OS=[s for s,r in prof[1:20]];OR=[r for s,r in prof[1:20]];rz=lambda z:float(np.interp(z/HT,OS,OR))
    o=_lathe('YP12_Vat',prof,((0,0,0),(0,0,HT)),M['glaze'],'Body',NS=48,scale=.4,loop=True)
    for th_c,wd,dp in ((.95,.085,.016),(2.75,.05,.010),(-.55,.04,.008)):   # the rolled rim is chipped in three places
        for v in o.data.vertices:
            r=math.hypot(v.co.x,v.co.y)
            if v.co.z>HT-.045 and r>.296:
                da=abs((math.atan2(v.co.y,v.co.x)-th_c+math.pi)%math.tau-math.pi)*r;fl=max(0.,1-da/wd)**.6
                if fl>0:k_=1-dp*fl/r*1.1;v.co.x*=k_;v.co.y*=k_;v.co.z-=dp*fl*(.9 if v.co.z>HT-.02 else .2)
    jitter(o,.004,7202,freq=5)   # thrown by hand: never quite round
    zw=.715;wo=_lathe('YP12_Water',[(0,.272),(1,.272)],((0,0,zw-.012),(0,0,zw)),M['water'],'Body',NS=32)
    for p_ in wo.data.polygons:p_.use_smooth=False
    R=.338;zl=HT-.002;ys=[-.035,.085,.200,.322]
    for k in range(3):   # lid boards run across (along X), each cut to the circle
        ya,yb=ys[k]+.002,ys[k+1]-.002;A=[(-math.sqrt(R*R-y*y),y) for y in np.linspace(ya,yb,5)];B=[(math.sqrt(R*R-y*y),y) for y in np.linspace(yb,ya,5)]
        if k==0:A[0]=(A[0][0]+.05,A[0][1]);A.insert(1,(A[0][0]-.035,A[0][1]+.03))   # a corner split off the front board
        _flatpoly(f'YP12_Lid{k}',A+B,zl,zl+.022+rr.uniform(-.002,.002),(WD,WB,WD)[k],'Body',seed=7210+k)
    for q,x in enumerate((-.165,.170)):
        box(f'YP12_Batten{q}',(.052,.300,.022),(x,.142,zl+.036),WB,'Body',bev=.004,segs=1,cuts=1,jit=.0012,seed=7220+q,rot=Matrix.Rotation(.04*(-1)**q,4,'Z'))
        for j,y in enumerate((.02,.14,.26)):_nail(f'YP12_Nail{q}{j}',(x+rr.uniform(-.008,.008),y,zl+.0445),(0,0,1),M['iron'],r=.005)
    # the gourd dipper on the lid: half a gourd as the bowl, a stick bound to it
    c=Vector((-.015,.150,zl+.024))
    _lathe('YP12_DipperBowl',[(0,.002),(0,.030),(.22,.060),(.6,.079),(1,.074),(1,.068),(.6,.072),(.24,.054),(.07,.028),(.07,.002)],(c,c+Vector((0,0,.082))),M['gourd'],'Body',NS=20,scale=.2,loop=True)
    d=Vector((math.cos(-.42),math.sin(-.42),0));a=c+d*.070+Vector((0,0,.060));b=c+d*.345+Vector((0,0,.012))
    _lathe('YP12_DipperHandle',[(0,.0115),(.5,.010),(.94,.0095),(1,.011)],(a-d*.03,b),M['floatwood'],'Body',NS=9,scale=.15)
    for q in range(3):_ring(f'YP12_DipperCord{q}',a+(b-a).normalized()*(.006+.010*q),(b-a),.0138,.0034,M['hemp'],'Body',n=11)
    # a crack down the front-left of the wall, held by iron staples (the old way to mend a cracked vat)
    crk=[];th=-2.05
    for i,z in enumerate(np.linspace(.775,.24,14)):
        th+=rr.uniform(-.045,.05);r=rz(z)+.001;crk.append((r*math.cos(th),r*math.sin(th),float(z)))
    br=[crk[6]];thb=math.atan2(crk[6][1],crk[6][0])
    for i in range(1,5):
        z=crk[6][2]-.03*i;thb-=rr.uniform(.05,.11);r=rz(z)+.001;br.append((r*math.cos(thb),r*math.sin(thb),z))
    for q,i in enumerate((2,5,9)):
        pc=Vector(crk[i]);n=Vector((pc.x,pc.y,0)).normalized();tg=Vector((-n.y,n.x,0));u=Vector((0,0,1))*rr.uniform(-.25,.25)+tg;u.normalize()
        tube(f'YP12_Staple{q}',[pc-u*.034-n*.006,pc-u*.031+n*.0035,pc+u*.031+n*.0035,pc+u*.034-n*.006],.0042,M['iron'],'Detail_Staples',sides=6,scale=.05)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];pr=np.hypot(px,py);th=np.arctan2(py,px);h=np.zeros(pr.shape,np.float32)
        vat=filled*(pz<HT+.002)*(col[...,0]>col[...,2]*1.25)*(pr>.2)*(pz<.79)
        outer=vat*((px*onrm[...,0]+py*onrm[...,1])>0)
        nz=_fb(P,7.,7240)
        drp=np.clip((np.sin(th*11+2.)*np.sin(th*4+.7)-.55)*3,0,1)                                # where the glaze ran further down in tongues
        edge_z=.21+.05*np.sin(th*3+1.3)+.03*np.sin(th*7+.4)+.10*(nz-.5)-.07*drp               # where the glaze stops: an uneven line
        bare=outer*np.clip((edge_z-pz)/.012,0,1)
        Pw=P+.045*np.stack([_fb(P,9.,7244+q_,2)-.5 for q_ in range(3)],-1).astype(np.float32)   # warped, so the patches are not straight-sided
        d1,d2,cid,vec,tilt=_wor(Pw,8.,7241)                                                    # glaze flaked off in angular patches, more of them lower down
        fl=outer*(cid>.50+.75*np.clip((pz-.2)/.5,0,1))*np.clip(((d2-d1)-.20-.55*(nz-.5)-.25*(_fb(P,40.,7245,2)-.5))/.04,0,1)*(pz<.70)
        bare=np.maximum(bare,fl);clay=np.array([.58,.45,.34])*(1+.30*(_fb(P,22.,7242)-.5))[...,None]
        col=col*(1-bare[...,None])+bare[...,None]*clay;rough=np.clip(rough+.45*bare,0,1);h-=.0022*bare
        lip=outer*(1-bare)*np.clip(1-(pz-edge_z)/.03,0,1)*np.clip((pz-edge_z)/.004,0,1);h+=.0016*lip;col=col*(1-.22*lip[...,None])   # the glaze is thick and dark where it stopped
        sheen=outer*(1-bare)*np.clip((_fb(P,3.,7243)-.5)*3,0,1);col=col*(1+.20*sheen[...,None]*np.array([1.,.8,.7]));rough=np.clip(rough-.08*sheen,0,1)
        for zr in (.52,.535):   # two thrown lines round the belly
            g=outer*np.clip(1-np.abs(pz-zr-.004*np.sin(th*2))/.0035,0,1);h-=.0012*g;col=col*(1-.18*g[...,None])
        ck=outer*np.maximum(_segd(P,crk,.006),.8*_segd(P,br,.005));h-=.004*ck;col=col*(1-.75*ck[...,None]);rough=np.clip(rough+.3*ck,0,1)
        seep=outer*_segd(P,[(x,y,z-.035) for x,y,z in crk[3:]],.03)*np.clip(.3+nz,0,1);col=col*(1-.20*seep[...,None])+seep[...,None]*.20*np.array([.52,.50,.44])   # a pale seep stain along the crack
        drip=outer*np.clip((np.sin(th*13+1.1)*np.sin(th*5+.3)-.80)*6,0,1)*np.clip((pz-.50-.12*np.sin(th*4))/.12,0,1)*np.clip((.79-pz)/.04,0,1);col=col*(1-.22*drip[...,None])+drip[...,None]*.22*np.array([.60,.55,.47])   # pale lime runs down from the rim
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,outer,h=.14,amt=.65,soil=.05)
        inner=vat*(1-outer)*(pz>zw);col=col*(1-.25*inner[...,None])
        tide=vat*(1-outer)*np.clip(1-np.abs(pz-zw-.02)/.012,0,1);col=col*(1-.3*tide[...,None])+tide[...,None]*.3*np.array([.62,.60,.52])   # the scale line just above the water
        lid=filled*(pz>HT-.004)*(pr<.36)*(col[...,1]>col[...,2]*1.2)*(col[...,0]<.75)
        col,rough=_wood_age(col,rough,h,P,lid,0,7250,edge,grey=.35)
        col=_knot(col,h,P,(.11,.05,zl+.022),.016,lid*(onrm[...,2]>.7));col=_knot(col,h,P,(-.19,.27,zl+.022),.012,lid*(onrm[...,2]>.7))
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.6,'grime':.8,'uv_angle':66,'collision_box':((.78,.78,.86),(0,0,.43)),
            'notes':['one thick thrown wall with a rolled rim (inside modelled too), pushed a little out of round; two raised cord bands on the shoulder; the rim is chipped in three places; water 8 cm below the rim',
                     'the lid is three boards cut to the circle under two nailed battens (a corner split off the front board), covering a little more than half of the mouth; the dipper is half a gourd with a stick bound to it by three turns of cord',
                     'a crack runs down the front-left of the wall, held by three iron staples (Detail_Staples)',
                     'painted, with the relief also in the normal map: the glaze stops at an uneven line with tongues above bare clay, glaze flaked off in angular patches, the crack and its seep stain, two thrown lines, lime runs under the rim, the scale line inside, moss and soil at the foot, checks and knots in the lid']}
PROPS['YP12']=YP12

# ---------------- YP11 carrying pole and two water buckets, set down (cand-3) ----------------
def _pail(M,tag,cx,rot,seed):
    """a coopered water pail at x = cx: twelve staves, two riveted hoops, two ear staves (front and back) drilled for the bail rope"""
    rr=random.Random(seed);WD,WB,IR=M['cedar'],M['cedar_b'],M['iron'];H=.30;R0=.132;R1=.158;T=.013;N=12;rw=lambda z:R0+(R1-R0)*z/H
    T_=Matrix.Translation((cx,0,0));turn=Matrix.Rotation(-math.pi/N,4,'Z');c=(0,0,0)
    st=_staves(f'{tag}_Stave',c,[(0,R0),(H,R1)],T,N,.012,WD,'Body',rows=4);ear=_staves(f'{tag}_Ear',c,[(0,R0),(H,R1),(.385,rw(.385))],T+.004,N,.012,WB,'Body',rows=6)
    for k in range(N):
        if k in (3,9):_drop_part(st[k]);e=ear[k];e.data.transform(turn);s=1 if k==3 else -1;_boolean(e,_cyl_cutter(f'{tag}_cutEar{k}',(0,s*(rw(.35)-.008),.350),(0,1,0),.011,.06));e.data.transform(T_)
        else:_drop_part(ear[k]);st[k].data.transform(Matrix.Translation((0,0,rr.uniform(-.004,.003))));st[k].data.transform(turn);st[k].data.transform(T_)
    _chip_staves([st[k] for k in range(N) if k not in (3,9)],rr,c=(cx,0.))
    for q,(z0,z1) in enumerate(((.050,.076),(.208,.234))):
        zm=(z0+z1)/2;_ring_band(f'{tag}_Hoop{q}',(cx,0,0),rw(zm)+.004,rw(zm)-.0015,z0,z1,IR,'Body',NS=24,scale=.2)
        for j in range(8):
            a=rot+math.tau*(j+.5*q)/8+rr.uniform(-.05,.05);n=Vector((math.cos(a),math.sin(a),0));p=Vector((cx,0,zm))+n*(rw(zm)+.0035)
            _lathe(f'{tag}_Rivet{q}{j}',[(0,.0055),(.6,.0046),(1,0)],(p,p+n*.004),IR,'Detail_Rivets',NS=6,scale=.03)
    _lathe(f'{tag}_Bottom',[(0,R0-.004),(1,rw(.034)-.004)],((cx,0,.020),(cx,0,.034)),WB,'Body',NS=24)
    zw=.215+rr.uniform(-.02,.02);wo=_lathe(f'{tag}_Water',[(0,rw(zw)-T+.003),(1,rw(zw)-T+.003)],((cx,0,zw-.012),(cx,0,zw)),M['water'],'Body',NS=24)
    for p_ in wo.data.polygons:p_.use_smooth=False
    return rw
def YP11(M):
    """set down: the two pails stand on the ground and the shoulder pole lies across their rims, between the ears.
    Each pail's bail rope runs from its two ears up to a wooden hook that hangs from the pole end by a rope loop;
    with the load off, the hooks lie on the pole and the bails are slack."""
    rr=random.Random(7101);WD,HP,HW=M['cedar'],M['hemp'],M['hardwood'];XB=.56;ZP=.300+.004+.013
    pole=[];RW_=[None]
    for i,u in enumerate(np.linspace(-1,1,13)):   # a flat springy pole: wide and thick in the middle, narrower to the ends, a notch-like swelling at each tip
        w=.062-.022*abs(u)**1.6+(.012 if abs(u)>.93 else 0);h=.026-.006*abs(u)**2;pole.append(((u*.845,.004*math.sin(u*2.1),ZP+.003*math.sin(u*3.3+.6)),w,h,.008))
    _beam('YP11_Pole',pole,M['floatwood'],'Body',jit=.0012,seed=7102)
    for q,s in enumerate((-1,1)):
        rw=_pail(M,f'YP11_Pail{q}',s*XB,.3+q*1.1,7110+q);RW_[0]=rw;xh=s*(XB+.165);zt=ZP+.013
        hk=[Vector((xh-s*.045,.004,zt+.009)),Vector((xh,.002,zt+.009)),Vector((xh+s*.030,.006,zt+.010)),Vector((xh+s*.046,.022,zt+.010)),Vector((xh+s*.036,.040,zt+.010)),Vector((xh+s*.016,.044,zt+.010))]
        tube(f'YP11_Hook{q}',hk,.009,HW,'Body',sides=8,scale=.1)   # the wooden hook, lying on the pole
        for j in range(3):_ring(f'YP11_Lash{q}{j}',(xh-s*(.052+.010*j),.003,ZP),(1,0,0),.031,.0042,HP,'Body',n=14)   # the loop that ties the hook to the pole
        for j,sy in enumerate((-1,1)):   # the bail: from each ear up to the hook, slack
            e=Vector((s*XB,sy*(rw(.35)-.004),.350));k=Vector((s*XB,sy*(rw(.35)+.020),.338));top=Vector((xh+s*.004,sy*.012,zt+.018))
            mid=e.lerp(top,.5)+Vector((0,sy*.030,-.022));pts=[k,e,e.lerp(mid,.5)+Vector((0,0,.004)),mid,mid.lerp(top,.55)+Vector((0,0,.004)),top]
            rope(f'YP11_Bail{q}{j}',pts,.0065,HP,'Body')
            o=_blob(f'YP11_Knot{q}{j}',(.028,.028,.028),7120+q*2+j,HP,'Body',sub=2,bumps=4,amp=.12,scale=.06);o.data.transform(Matrix.Translation((s*XB,sy*(rw(.35)+.022),.322)))
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];h=np.zeros(pz.shape,np.float32)
        polem=filled*(pz>ZP-.016)*(pz<ZP+.016)*(np.abs(py)<.04)*(col[...,0]>col[...,2]*1.3)
        col,rough=_wood_age(col,rough,h,P,polem,0,7130,edge,grey=.2)
        worn=polem*np.clip(1-(np.abs(px)/.22)**2,0,1);col=col*(1+.20*worn[...,None]);rough=np.clip(rough-.25*worn,0,1)   # the middle worn pale and smooth by the shoulder
        for q,s in enumerate((-1,1)):
            Pq=P-np.array([s*XB,0,0],np.float32);near=filled*(np.abs(Pq[...,0])<.2)*(pz<ZP-.017)
            col,rough=_pail_age(col,rough,h,Pq,onrm,edge,near,RW_[0],.30,((.050,.076),(.208,.234)),(((-.6,.10),(2.2,.07),(-2.4,.12)),((.5,.08),(2.9,.11),(-1.9,.06)))[q],7140+q*9)
        wall=filled*(pz<.30)*(np.abs(onrm[...,2])<.6)*(np.abs(np.abs(px)-XB)<.17)
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,wall,h=.06,amt=.4,soil=.03)
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.9,'grime':.9,'damp':.07,'uv_angle':60,
            'notes':['set down, not carried: the two pails stand on the ground, the pole lies across their rims between the ears; the three-view shows it lifted',
                     'each pail: twelve staves (tops not level, some chipped), two hoops with rivets (Detail_Rivets), two drilled ear staves, water inside; the bail rope runs from the ears to a wooden hook tied to the pole end, slack',
                     'painted, with the relief also in the normal map: checks and rim splits in the staves, rusty hoops, checks in the pole and its middle worn pale, damp and moss at the feet of the pails']}
PROPS['YP11']=YP11
