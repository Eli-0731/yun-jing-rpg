# LV13–LV20 shapes (the 11/08 40h pack), read by build_lv.py after lv_items.py and lv_items_b.py.
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _hoop2(name,pts,r,mat,grp,sides=8,scale=.06,phase=.5):
    """a closed ring tube through pts (a loop round Z, no repeated end): each section in its radial–vertical plane,
    faces welded all the way round (lapped tube ends lay in one plane with each other)"""
    bm=bmesh.new();N=len(pts);R_=[]
    for p in pts:
        p=Vector(p);n=Vector((p.x,p.y,0)).normalized()
        R_.append([bm.verts.new(p+(n*math.cos(math.tau*(k+phase)/sides)+Vector((0,0,1))*math.sin(math.tau*(k+phase)/sides))*r) for k in range(sides)])
    for i in range(N):
        a,b=R_[i],R_[(i+1)%N]
        for k in range(sides):bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)
def _ring_band(name,c,r_out,r_in,z0,z1,mat,grp,NS=48,scale=.2):
    """a short tube wall (outer r_out, inner r_in) from z0 to z1 round the vertical line through c"""
    c=Vector(c);return _lathe(name,[(0,r_out),(1,r_out),(1,r_in),(0,r_in)],(c+Vector((0,0,z0)),c+Vector((0,0,z1))),mat,grp,NS=NS,scale=scale,loop=True)
def _staves(name,c,prof,t,n,gap,mat,grp,rows=6):
    """a coopered wall: n separate staves round the vertical line through c, following prof = [(z, r)] (outer radius),
    thickness t, a gap (rad) between neighbours"""
    c=Vector(c);out=[]
    zs=[p[0] for p in prof];rs=[p[1] for p in prof]
    for k in range(n):
        a0=math.tau*k/n+gap/2;a1=math.tau*(k+1)/n-gap/2;bm=bmesh.new();O=[];I=[]
        for z in np.linspace(zs[0],zs[-1],rows):
            r=float(np.interp(z,zs,rs));O.append([bm.verts.new(c+Vector((r*math.cos(a),r*math.sin(a),z))) for a in np.linspace(a0,a1,3)]);I.append([bm.verts.new(c+Vector(((r-t)*math.cos(a),(r-t)*math.sin(a),z))) for a in np.linspace(a0,a1,3)])
        for i in range(rows-1):
            for j in range(2):bm.faces.new((O[i][j],O[i][j+1],O[i+1][j+1],O[i+1][j]));bm.faces.new((I[i][j],I[i+1][j],I[i+1][j+1],I[i][j+1]))
            bm.faces.new((O[i][0],O[i+1][0],I[i+1][0],I[i][0]));bm.faces.new((O[i][2],I[i][2],I[i+1][2],O[i+1][2]))
        for j in range(2):bm.faces.new((O[0][j],I[0][j],I[0][j+1],O[0][j+1]));bm.faces.new((O[-1][j],O[-1][j+1],I[-1][j+1],I[-1][j]))
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        for f in bm.faces:f.smooth=False
        out.append(finish(f'{name}{k:02d}',bm,mat,grp,.15))
    return out

# ---------------- LV13 a stack of three bamboo steamer baskets with a domed lid (cand-3) ----------------
def LV13(M):
    """three steamer tiers of the same make, each a split-bamboo band round a woven floor with a thicker foot ring; the
    upper tier's foot ring sits over the lower one's rim (the joint between layers); each tier turned a little and set
    a few millimetres off; vertical binding strips on the bands; a shallow domed woven lid with a rim band and a bamboo
    loop handle, the lid edge frayed (Detail_); the lowest tier darkened by steam."""
    R=.200;H=.104;rr=random.Random(1313);TOP=[]
    for k in range(3):
        c=Vector((.004*math.sin(k*2.1),.003*math.cos(k*1.7),0));z0=k*H+(.003 if k else 0)
        rot=rr.uniform(-.4,.4)
        _ring_band(f'LV13_Band{k}',c,R,R-.0075,z0+.004,z0+H,M['bamboo_old'],'Body',NS=56)
        _ring_band(f'LV13_Foot{k}',c,R+.0045,R-.004,z0,z0+.019,M['bamboo_old'],'Body',NS=56)   # the foot ring: it sits over the rim of the tier below
        _lathe(f'LV13_Floor{k}',[(0,R-.0015),(1,R-.0015),(1,0)],(c+Vector((0,0,z0+.012)),c+Vector((0,0,z0+.016))),M['weave'],'Body',NS=56,scale=.3)
        for j in range(4):   # binding strips on the band
            a=rot+math.tau*j/4;n=Vector((math.cos(a),math.sin(a),0));rs=R+.0009
            _strip(f'LV13_Bind{k}{j}',[c+n*rs+Vector((0,0,z0+.021)),c+n*rs+Vector((0,0,z0+H*.55)),c+n*rs+Vector((0,0,z0+H-.004))],lambda i,n=n:n,.012,.0016,M['bamboo_split'],'Body')
        a=rot+.6;seam=[c+Vector(((R+.0012)*math.cos(t),(R+.0012)*math.sin(t),0)) for t in np.linspace(a,a+.22,5)]   # the band's lapped joint
        rows=[[tuple(p+Vector((0,0,z0+.024))),tuple(p+Vector((0,0,z0+H-.008)))] for p in seam]
        _sheet(f'LV13_Seam{k}',rows,None,None,M['bamboo_old'],'Body',t=.0016)
        TOP.append((c,z0))
    c=TOP[-1][0];zl=3*H+.003   # the lid: rim band, then a woven dome
    _ring_band('LV13_LidRim',c,R+.006,R-.003,zl-.004,zl+.022,M['bamboo_old'],'Body',NS=56)
    prof=[(0,R+.002),(.15,R-.01),(.35,R-.05),(.6,R-.11),(.82,R-.16),(1,.03),(1,.004),(.94,.004),(.80,R-.165),(.58,R-.117),(.33,R-.058),(.13,R-.018),(0,R-.006)]
    _lathe('LV13_Lid',prof,(c+Vector((0,0,zl+.016)),c+Vector((0,0,zl+.016+.085))),M['weave'],'Body',NS=56,scale=.25,loop=True)
    ztop=zl+.016+.085
    _lathe('LV13_Knob',[(0,.026),(.5,.022),(1,.014)],(c+Vector((0,0,ztop-.006)),c+Vector((0,0,ztop+.006))),M['bamboo_old'],'Body',NS=16,scale=.05)
    hl=[c+Vector((.018*math.cos(a),0,ztop+.004+.03*math.sin(a))) for a in np.linspace(0,math.pi,11)]
    tube('LV13_Handle',hl,.0045,M['bamboo_split'],'Body',sides=6,scale=.05)
    for k in range(40):   # frayed strips at the lid edge
        a=math.tau*(k+rr.uniform(-.3,.3))/40;u=Vector((math.cos(a),math.sin(a),0));L=rr.uniform(.008,.022)
        p0=c+u*(R+.004)+Vector((0,0,zl+.020));_taper(f'LV13_Fray{k:02d}',[p0,p0+u*L*.6+Vector((0,0,.002)),p0+u*L+Vector((0,0,-.004))],[.0016,.0012,.0004],M['bamboo_split'],'Detail_Fray',sides=3,scale=.04,up=Vector((0,0,1)))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];pz=P[...,2]
        st=filled*np.clip((.13-pz)/.10,0,1);col=col*(1-.35*st[...,None])+st[...,None]*np.array([.06,.03,.02])   # steam-darkened lower tier
        sp=filled*np.clip((noise-.62)*4,0,1)*np.clip((.20-pz)/.15,0,1);col=col*(1-.25*sp[...,None])
        return col,rough
    return {'paint':paint,'wear':.8,'grime':.8,'uv_angle':50,'notes':['three tiers of the same make: band, foot ring over the tier below, woven floor (weave in the texture), four binding strips and a lapped joint; each turned and set a few mm off',
            'a shallow woven dome lid with a rim band, knob and loop handle; Detail_Fray: frayed strips at the lid edge; the lowest tier darkened by steam']}
PROPS['LV13']=LV13

# ---------------- LV14 a three-tier lacquered wooden food carrying box (cand-2) ----------------
def LV14(M):
    """a footed base, three square-ish tiers and a lid stacked on it, each tier sitting on the one below by a lip (a dark
    groove shows between them), the middle tier set a few mm off; dark-red lacquer worn to the wood at the edges,
    corners and handle; small brass corner pieces; an arched carrying handle rising from two side posts, pinned through
    every tier, its top bound with hemp; a patch board on one side."""
    W,D=.33,.235;TH=.105
    box('LV14_Base',(W+.02,D+.02,.045),(0,0,.0225),M['lacquer'],'Body',bev=.004,cuts=2,seed=1401)
    z=.045;tiers=[]
    for k in range(3):
        dx=.005 if k==1 else 0
        box(f'LV14_Lip{k}',(W-.018,D-.018,.012),(dx,0,z+.002),M['hardwood'],'Body',bev=.001,seed=1410+k)   # the lip that sits in the tier below
        box(f'LV14_Tier{k}',(W,D,TH-.004),(dx,0,z+.004+(TH-.004)/2),M['lacquer'],'Body',bev=.004,cuts=2,jit=.0006,seed=1420+k)
        tiers.append((dx,z+.004,z+TH));z+=TH
    box('LV14_LidLip',(W-.018,D-.018,.012),(0,0,z+.002),M['hardwood'],'Body',bev=.001,seed=1430)
    box('LV14_Lid',(W,D,.045),(0,0,z+.004+.0225),M['lacquer'],'Body',bev=.008,cuts=2,seed=1431)
    zl=z+.049
    for k,(dx,za,zb) in enumerate(tiers+[(0,z+.004,zl)]):   # brass corner plates on the front and back faces
        for sx in (-1,1):
            for sy in (-1,1):
                for zz,sz in ((za+.014,1),(zb-.014,-1)):
                    box(f'LV14_Corner{k}{sx}{sy}{sz}',(.024,.0024,.022),(dx+sx*(W/2-.013),sy*(D/2+.0016),zz),M['brass'],'Body',bev=.0006,segs=1,seed=1440)
    PX=W/2+.022   # the handle: two posts outside the short ends, an arch over the top
    for k,sx in enumerate((-1,1)):
        box(f'LV14_Post{k}',(.018,.032,zl+.02-.01),(sx*PX,0,(zl+.02+.01)/2),M['lacquer'],'Body',bev=.003,seed=1450+k)
        for j,(dx,za,zb) in enumerate(tiers):   # pins through the post into each tier's end
            _rod(f'LV14_Pin{k}{j}',(sx*(PX+.012),0,(za+zb)/2),(sx*(W/2-.004+dx*sx),0,(za+zb)/2),.0052,M['brass'],'Body',sides=10,scale=.04)
    za=zl+.02;arch=[Vector((PX*math.cos(a),0,za+.075*math.sin(a))) for a in np.linspace(0,math.pi,21)]
    arch=[Vector((-p.x,p.y,p.z)) for p in arch]
    tube('LV14_Arch',arch,.0115,M['lacquer'],'Body',sides=8,scale=.08)
    for k in range(7):   # hemp bound round the top of the arch
        a=math.pi/2+(k-3)*.075;c=Vector((PX*math.cos(a),0,za+.075*math.sin(a)));t=Vector((-math.sin(a)*PX,0,.075*math.cos(a))).normalized()
        _ring(f'LV14_Wrap{k}',c,t,.0115+.0024,.0024,M['hemp'],'Body',n=13)
    box('LV14_Patch',(.0025,.06,.045),(W/2+.0016+.005,0,tiers[1][1]+.05),M['cedar_new'],'Body',bev=.001,seed=1460)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        wood=np.array([.46,.32,.20])
        w=filled*np.clip(edge*2.2-.25+(noise-.5)*.5,0,1)**1.5   # lacquer rubbed off at edges and corners only
        col=col*(1-w[...,None])+w[...,None]*wood*(.8+.4*noise[...,None]);rough=np.clip(rough+.25*w,0,1)
        return col,rough
    return {'paint':paint,'wear':1.1,'grime':.7,'uv_angle':50,'notes':['a footed base, three tiers and a lid; each sits on a lip set into the one below (a dark groove between layers); the middle tier 5 mm off',
            'an arched handle on two side posts, brass pins into every tier, hemp at the top; brass corner plates; lacquer worn to the wood at edges (painted), a patch board']}
PROPS['LV14']=LV14

# ---------------- LV15 a tall-stemmed clay oil lamp stand (cand-3) ----------------
def LV15(M):
    """one turned profile: a flared foot, a slender stem with a collar half way, a cup that holds the dish; the dish is a
    shallow glazed bowl with a little pouring lip, oil in it and a twisted cotton wick laid from the middle to the lip;
    soot above the wick, oil runs down the stem, a chip out of the foot."""
    prof=[(0,0),(0,.085),(.012,.086),(.026,.080),(.040,.064),(.055,.040),(.075,.027),(.12,.022),(.19,.021),(.195,.030),(.205,.031),(.215,.022),(.29,.020),(.33,.023),(.345,.034),(.352,.036)]
    zs=[z for z,_ in prof];top=zs[-1]
    st=_lathe('LV15_Stand',[(z/top,r) for z,r in prof]+[(1,0)],(Vector((0,0,0)),Vector((0,0,top))),M['clay_red'],'Body',NS=40,scale=.15)
    _boolean(st,_cutter('LV15_Chip',(.03,.03,.024),(.072,-.05,.008)))
    zd=top-.004   # the dish
    dp=[(0,.006),(0,.032),(.3,.052),(.75,.066),(1,.071),(1,.064),(.80,.059),(.38,.045),(.12,.026),(.12,.006)]
    _lathe('LV15_Dish',dp,(Vector((0,0,zd)),Vector((0,0,zd+.034))),M['glaze'],'Body',NS=40,scale=.12,loop=True)
    _lathe('LV15_Oil',[(0,.044),(1,.044),(1,0)],(Vector((0,0,zd+.010)),Vector((0,0,zd+.0145))),M['glaze'],'Body',NS=32,scale=.12)
    w=[Vector((.0,.0,zd+.0155)),Vector((.025,-.004,zd+.017)),Vector((.048,-.006,zd+.024)),Vector((.062,-.006,zd+.033)),Vector((.068,-.006,zd+.040))]
    rope('LV15_Wick',w,.0034,M['linen'],'Body')
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        th=np.arctan2(py,px);r=np.hypot(px,py)
        drip=filled*(pz<zd)*(pz>.05)*np.clip((np.sin(th*7+1.3)+.4*np.sin(th*17)-.6)*3,0,1)*np.clip((pz-.05)/.25+.3*(noise-.5),0,1)   # oil runs down the stem
        col=col*(1-.40*drip[...,None]);rough=np.clip(rough-.25*drip,0,1)
        soot=filled*(pz>zd+.02)*np.clip(1-np.hypot(px-.066,py+.006)/.03,0,1);col=col*(1-.7*soot[...,None])
        foot=filled*np.clip((.02-pz)/.02,0,1);col=col*(1-.25*foot[...,None])
        return col,rough
    return {'paint':paint,'wear':.8,'grime':.8,'uv_angle':50,'notes':['the stand is one turned profile (foot, stem, collar, cup) with a chip cut out of the foot; the dish a glazed shell with oil in it',
            'a twisted cotton wick from the middle of the dish to the rim; soot and oil runs painted']}
PROPS['LV15']=LV15

# ---------------- LV16 a three-legged washbasin stand with a coopered wooden basin (cand-1) ----------------
def LV16(M):
    """three splayed square legs; three rails at the top make a triangle the basin rests on, three stretchers lower down;
    every rail and stretcher tenoned through its leg (the tenon ends show); the basin is sixteen staves round a round
    bottom, two bamboo hoops with lapped bindings; a peg on one leg with a coarse cloth hung over it; water stains."""
    rr=random.Random(1616);ZT=.640;ang=[math.pi/2+math.tau*k/3 for k in range(3)]
    tops=[Vector((.148*math.cos(a),.148*math.sin(a)*.9,ZT)) for a in ang];feet=[Vector((.250*math.cos(a),.250*math.sin(a)*.86,0)) for a in ang]   # legs splay out
    yoff=-(max(p.y for p in feet)+min(p.y for p in feet))/2
    tops=[p+Vector((0,yoff,0)) for p in tops];feet=[p+Vector((0,yoff,0)) for p in feet]
    def legpt(k,z):return feet[k].lerp(tops[k],z/ZT)
    for k in range(3):
        d=(tops[k]-feet[k]);L=d.length;o=finish(f'LV16_Leg{k}',box_bm((.040,.040,L+.006),(0,0,0)),M['cedar_b'],'Body');bevel(o,.004,2);jitter(o,.0012,1610+k,freq=12)
        o.data.transform(Vector((0,0,1)).rotation_difference(d.normalized()).to_matrix().to_4x4());o.data.transform(Matrix.Translation((feet[k]+tops[k])/2))
        me=o.data;mz=min(v.co.z for v in me.vertices);xz=max(v.co.z for v in me.vertices)
        for v in me.vertices:v.co.z=max(0.,min(v.co.z,ZT+.002))   # feet cut flat on the ground, tops flat under the basin
    for nm,z,h in (('Rail',ZT-.025,.040),('Stretcher',.20,.030)):
        for k in range(3):
            a,b=legpt(k,z),legpt((k+1)%3,z);d=(b-a).normalized();L=(b-a).length+.05   # long enough to pass through both legs: tenon ends show
            o=finish(f'LV16_{nm}{k}',box_bm((L,.026,h),(0,0,0)),M['cedar'],'Body');bevel(o,.003,2)
            o.data.transform(Matrix.Rotation(math.atan2(d.y,d.x),4,'Z'));o.data.transform(Matrix.Translation((a+b)/2+Vector((0,0,.004*k))))
    # the basin
    c=Vector((0,yoff*0,ZT+.002));prof=[(0,.134),(.04,.142),(.10,.160),(.16,.176),(.168,.178)]   # held to the 0.4 m depth with its hoops
    _staves('LV16_Stave',c,prof,.014,16,.012,M['cedar_new'],'Body')
    _lathe('LV16_Bottom',[(0,.129),(1,.136),(1,0)],(c+Vector((0,0,.004)),c+Vector((0,0,.020))),M['cedar_new'],'Body',NS=32,scale=.15)
    for k,z in enumerate((.035,.128)):
        r=float(np.interp(z,[p[0] for p in prof],[p[1] for p in prof]))+.0062
        _hoop2(f'LV16_Hoop{k}',[c+Vector((r*math.cos(t),r*math.sin(t),z)) for t in np.linspace(0,math.tau,64,endpoint=False)],.0058,M['bamboo_old'],'Body')
        a=1.1+k*2.2;p=c+Vector(((r+.006)*math.cos(a),(r+.006)*math.sin(a),z))
        _ring(f'LV16_HoopTie{k}',p,(math.cos(a+math.pi/2),math.sin(a+math.pi/2),0),.010,.0018,M['hemp'],'Body',n=11)
    # a peg on the front leg and a cloth over it
    k=1;pz=.50;lp=legpt(k,pz);out=Vector((lp.x,lp.y-yoff,0)).normalized()
    pa=lp+out*.012;pb=lp+out*.055+Vector((0,0,.012));_rod('LV16_Peg',pa-out*.015,pb,.0075,M['cedar'],'Body',sides=10,scale=.05)
    side=Vector((-out.y,out.x,0));rows=[]
    for i,u in enumerate(np.linspace(-1,1,7)):
        row=[]
        for j,v in enumerate(np.linspace(0,1,9)):
            drop=.03+.20*v;x=u*.07
            p=pb+side*x*(1+.15*v)+out*(-.008+.012*math.sin(v*3+u)+.0105)+Vector((0,0,.010-drop*(1-.25*abs(u))*1.0 if v>0 else .0105))
            if v==0:p=pb+side*x+Vector((0,0,.0085))+out*(-.03+.03*(1-abs(u)))
            row.append(tuple(p))
        rows.append(row)
    _sheet('LV16_Cloth',rows,None,None,M['linen_b'],'Body',t=.0022)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        bas=filled*(pz>ZT)*(np.hypot(px,py)>.14)
        wet=bas*np.clip((np.sin(np.arctan2(py,px)*9+noise*2)-.3)*2,0,1)*np.clip((ZT+.12-pz)/.1,0,1);col=col*(1-.35*wet[...,None])
        ft=filled*np.clip((.08-pz)/.07,0,1)*np.clip((noise-.45)*3,0,1);col=col*(1-.3*ft[...,None])+ft[...,None]*np.array([.08,.11,.04])
        return col,rough
    return {'paint':paint,'wear':.9,'grime':.8,'uv_angle':50,'notes':['three splayed legs; top rails and lower stretchers pass through the legs (tenon ends show); the basin rests on the top rails',
            'the basin: sixteen staves with gaps, a round bottom, two bamboo hoops tied where they lap; a peg on the front leg with a cloth over it; water stains painted']}
PROPS['LV16']=LV16

# ---------------- LV17 desk things: brush rack, inkstone, paperweight (cand-1) ----------------
def LV17(M):
    """a low wooden tray; at the back a small rack (two posts on feet, a top bar) with three brushes hanging from hooks;
    at the front a black inkstone with a shallow well and a grinding slope, dried ink in the well, and a plain bronze
    paperweight bar with a dull patina. No writing anywhere."""
    box('LV17_Tray',(.46,.26,.026),(0,0,.013),M['hardwood'],'Body',bev=.004,cuts=2,seed=1701)
    ZB=.026
    for k,x in enumerate((-.10,.10)):
        box(f'LV17_Foot{k}',(.024,.07,.014),(x,.075,ZB+.006),M['hardwood'],'Body',bev=.002,seed=1702+k)
        box(f'LV17_Post{k}',(.016,.016,.200-ZB-.012),(x,.075,(ZB+.010+.188)/2),M['hardwood'],'Body',bev=.002,seed=1704+k)
    box('LV17_Bar',(.25,.018,.016),(0,.075,.192),M['hardwood'],'Body',bev=.003,seed=1706)
    for k,x in enumerate((-.055,0,.055)):   # hooks and brushes
        hz=.184;tube(f'LV17_Hook{k}',[Vector((x,.075,hz+.004)),Vector((x,.075,hz-.006))]+[Vector((x+.004*math.sin(a),.075,hz-.010-.004*math.cos(a))) for a in np.linspace(0,math.tau*.85,8)],.0011,M['brass'],'Body',sides=5,scale=.03)
        top=Vector((x,.075,hz-.012));L=.105-.01*k
        _lathe(f'LV17_Shaft{k}',[(0,.0040),(.06,.0052),(1,.0050)],(top+Vector((0,0,.0005)),top-Vector((0,0,L))),M['bamboo'],'Body',NS=10,scale=.04)
        _lathe(f'LV17_Ferrule{k}',[(0,.0062),(1,.0062)],(top-Vector((0,0,L-.004)),top-Vector((0,0,L+.008))),M['hardwood'],'Body',NS=12,scale=.04)
        _lathe(f'LV17_Tip{k}',[(0,.0058),(.3,.0072),(.7,.005),(1,0)],(top-Vector((0,0,L+.006)),top-Vector((0,0,L+.040))),M['bristle'],'Body',NS=12,scale=.04)
    ink=box('LV17_Inkstone',(.165,.115,.026),(-.115,-.045,ZB+.013),M['inkstone'],'Body',bev=.004,seed=1710)
    _boolean(ink,_cutter('LV17_Well',(.11,.075,.02),(-.115,-.045,ZB+.026+.002)))
    _boolean(ink,_cutter('LV17_Pool',(.04,.06,.02),(-.115-.045,-.045,ZB+.026-.004)))
    box('LV17_Weight',(.19,.026,.020),(.115,-.06,ZB+.010),M['bronze'],'Body',bev=.002,seed=1712,rot=Matrix.Rotation(.08,4,'Z'))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        well=filled*(np.abs(px+.115)<.056)*(np.abs(py+.045)<.04)*(pz<ZB+.025)*(pz>ZB+.005)*(onrm[...,2]>.5)
        col=col*(1-.6*well[...,None]);rough=np.clip(rough-.2*well*(np.abs(px+.16)<.02),0,1)   # dried ink in the well, wet sheen in the pool
        return col,rough
    return {'paint':paint,'wear':.8,'grime':.6,'uv_angle':50,'notes':['a low tray with a brush rack (posts on feet, top bar, three brushes on brass hooks), an inkstone with a well and a pool cut in, and a bronze paperweight bar',
            'no writing or carving anywhere; dried ink painted in the well']}
PROPS['LV17']=LV17

# ---------------- LV18 a wooden abacus, lying flat (cand-3) ----------------
def LV18(M):
    """a dark hardwood frame with a beam across it and 13 thin rods; two beads above the beam and five below on every rod,
    lens-shaped and polished by use. The beads are made with Array modifiers from one bead (5 along the rod, 13 across
    the rods; 2 above), not placed one by one; one bead has a chip (a small boolean cut). Lying flat on a table as the
    work pack's size (0.35 × 0.12 × 0.05 m)."""
    W,D,T=.35,.12,.030;FB=.011;NR=13;pitch=(W-2*FB)/NR
    for k,(sx,sy,x,y) in enumerate(((W,FB,0,-D/2+FB/2),(W,FB,0,D/2-FB/2),(FB,D-2*FB,-W/2+FB/2,0),(FB,D-2*FB,W/2-FB/2,0))):
        box(f'LV18_Frame{k}',(sx,sy,T),(x,y,T/2),M['hardwood'],'Body',bev=.002,seed=1801+k)
    yb=D/2-FB-.032   # the beam: two beads above it, five below
    box('LV18_Beam',(W-2*FB+.004,.008,.020),(0,yb,T/2),M['hardwood'],'Body',bev=.0015,seed=1806)
    zc=T/2;y0,y1=-D/2+FB-.003,D/2-FB+.003
    for i in range(NR):
        x=-W/2+FB+pitch*(i+.5);_rod(f'LV18_Rod{i}',(x,y0,zc),(x,y1,zc),.0016,M['bamboo_split'],'Body',sides=6,scale=.03)
    def bead(name,y):
        o=_lathe(name,[(0,.0028),(.18,.0072),(.5,.0108),(.82,.0072),(1,.0028)],(Vector((-W/2+FB+pitch*.5,y-.004,zc)),Vector((-W/2+FB+pitch*.5,y+.004,zc))),M['beadwood'],'Body',NS=16,scale=.03)
        return o
    lo=bead('LV18_BeadsLow',-D/2+FB+.0045+.0005);m=lo.modifiers.new('a','ARRAY');m.use_relative_offset=False;m.use_constant_offset=True;m.constant_offset_displace=(0,.0092,0);m.count=5
    m2=lo.modifiers.new('b','ARRAY');m2.use_relative_offset=False;m2.use_constant_offset=True;m2.constant_offset_displace=(pitch,0,0);m2.count=NR
    for mm in list(lo.modifiers):apply(lo,mm)
    up=bead('LV18_BeadsUp',D/2-FB-.0045-.0005);m=up.modifiers.new('a','ARRAY');m.use_relative_offset=False;m.use_constant_offset=True;m.constant_offset_displace=(0,-.0092,0);m.count=2
    m2=up.modifiers.new('b','ARRAY');m2.use_relative_offset=False;m2.use_constant_offset=True;m2.constant_offset_displace=(pitch,0,0);m2.count=NR
    for mm in list(up.modifiers):apply(up,mm)
    xc=-W/2+FB+pitch*7.5;_boolean(lo,_cutter('LV18_Chip',(.006,.006,.006),(xc+.0095,-D/2+FB+.005+2*.0092,zc+.007)))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        w=filled*np.clip(edge*1.4+(noise-.6),0,1);col=col*(1+.25*w[...,None]);return col,rough   # frame corners worn paler
    return {'paint':paint,'wear':1.0,'grime':.6,'uv_angle':50,'notes':['frame, beam and 13 rods; 91 beads from one bead with two Array modifiers (5 × 13 below the beam, 2 × 13 above), applied; one chipped bead',
            'lying flat (the work pack gives 0.35 × 0.12 × 0.05 m as w × d × h)']}
PROPS['LV18']=LV18

# ---------------- LV19 a shallow bamboo winnowing basket, open at one side (cand-4) ----------------
def LV19(M):
    """one continuous shallow shell: its floor rises to a back wall and two side walls and comes down to nothing at the
    open front (the pouring edge); a thick bamboo rim round the back and sides tied on at intervals, a flat strip along
    the pouring edge; a woven patch; a few grains of rice in it (Detail_). The weave is in the texture."""
    W,D,H=.38,.29,.135;NU,NV=33,19
    def S(s,t):   # s across (-1..1), t from the front (0) to the back (1)
        w=W*math.sqrt(max(0.,1-max(0.,(t-.55)/.45)**2*.6));x=s*w;y=-D+2*D*t
        z=H*min(1.,(t**1.6)*.85+(abs(s)**6)*(.25+.75*t)**.7)+.004
        return Vector((x,y,z))
    rows=[[tuple(S(s,t)) for t in np.linspace(0,1,NV)] for s in np.linspace(-1,1,NU)]
    _sheet('LV19_Shell',rows,None,None,M['weave'],'Body',t=.006)
    rim=[S(-1,t) for t in np.linspace(.02,1,10)]+[S(s,1) for s in np.linspace(-1,1,17)[1:-1]]+[S(1,t) for t in np.linspace(1,.02,10)]
    rim=[p+Vector((0,0,.0078)) for p in rim]
    tube('LV19_Rim',_spline(rim,2),.0095,M['bamboo_old'],'Body',sides=8,scale=.06)
    lip=[S(s,0)+Vector((0,.012,.0062)) for s in np.linspace(-1,1,13)]   # just above the shell (lying on it, the two read as one plane)
    _strip('LV19_Lip',lip,lambda i:Vector((0,0,1)),.026,.004,M['bamboo_split'],'Body')
    for k,u in enumerate(np.linspace(.08,.92,9)):   # ties on the rim
        i=int(u*(len(rim)-1));p=rim[i];t=(rim[min(i+1,len(rim)-1)]-rim[max(i-1,0)]).normalized()
        _ring(f'LV19_Tie{k}',p,t,.0095+.0022,.0018,M['hemp'],'Body',n=11)
    rr=random.Random(1919);pat=[[tuple(S(s,t)+Vector((0,0,.0045))) for t in np.linspace(.38,.55,4)] for s in np.linspace(.30,.52,4)]
    _sheet('LV19_Patch',pat,None,None,M['bamboo_split'],'Body',t=.002)
    for k in range(14):
        s=rr.uniform(-.7,.7);t=rr.uniform(.1,.6);p=S(s,t)+Vector((0,0,.004));a=rr.uniform(0,math.tau)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=5,radius=1,location=p);o=bpy.context.object;o.scale=(.0034,.0018,.0016);o.rotation_euler=(0,0,a);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)   # location too: without it every grain sat at the origin
        bm=bmesh.new();bm.from_mesh(o.data);bpy.data.objects.remove(o);finish(f'LV19_Rice{k:02d}',bm,M['egg'],'Detail_Rice',.02)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];py=P[...,1]
        lip=filled*np.clip((-D+.06-py)/.06,0,1);col=col*(1-.35*lip[...,None])+lip[...,None]*np.array([.08,.05,.02]);rough=np.clip(rough-.15*lip,0,1)   # the worn pouring edge
        return col,rough
    return {'paint':paint,'wear':.9,'grime':.7,'uv_angle':50,'notes':['one shell: floor rising to a back wall and side walls, down to nothing at the open front; the weave in the texture',
            'a thick bamboo rim tied on at nine places, a flat strip along the pouring edge (worn darker, painted), a woven patch; Detail_Rice: a few grains']}
PROPS['LV19']=LV19

# ---------------- LV20 a round palm-leaf fan and a half-open folding fan, lying side by side (cand-3) ----------------
def LV20(M):
    """left: a round palm-leaf fan (a 3 mm leaf disc, a bamboo rim, a round handle bound with cloth, the leaf edge frayed);
    right: a folding fan opened about 100°, ten bamboo ribs fanned from a pivot (alternately tilted so they stack),
    two thicker guard sticks, a pleated plain paper leaf (no painting, no writing). Both lying flat."""
    rr=random.Random(2020)
    c=Vector((-.10,.03,.0));R=.098;zl=.0065
    rows=[]
    for a in np.linspace(0,math.tau,49):
        rows.append([(c.x+r*math.cos(a)*1.0,c.y+r*math.sin(a)*1.08,zl+.0015*math.sin(a*3)*(r/R)) for r in np.linspace(.004,R-.0046,7)])   # the leaf ends just inside the rim (tucked into it, its edge lay in the rim's faces)
    _band('LV20_Leaf',rows,M['palm'],'Body',t=.003,seed=2001)
    _hoop2('LV20_Rim',[(c.x+R*math.cos(a),c.y+R*math.sin(a)*1.08,zl+.0015*math.sin(a*3)) for a in np.linspace(0,math.tau,56,endpoint=False)],.0032,M['bamboo_split'],'Body',sides=8,phase=0.)   # corners up and down: no flat top face lying along the leaf
    h0=Vector((c.x,c.y-R*1.08+.012,.0062));h1=h0+Vector((0,-.115,0))
    _lathe('LV20_Handle',[(0,.0058),(.1,.0062),(.9,.0060),(1,.0052)],(h0,h1),M['cedar'],'Body',NS=10,scale=.05)
    for k in range(5):_ring(f'LV20_Wrap{k}',h0+Vector((0,-.012-.007*k,0)),(0,1,0),.0062+.0018,.0018,M['linen_b'],'Body',n=11)
    for k in range(18):   # frayed leaf edge
        a=rr.uniform(.4,2.6);u=Vector((math.cos(a),math.sin(a)*1.08,0)).normalized();p0=c+Vector((R*math.cos(a),R*math.sin(a)*1.08,zl))
        _taper(f'LV20_Fray{k:02d}',[p0-u*.004,p0+u*rr.uniform(.006,.014)],[.0012,.0004],M['palm'],'Detail_Fray',sides=3,scale=.03,up=Vector((rr.uniform(-1,1),rr.uniform(-1,1),rr.uniform(-1,1))))
    # the folding fan
    pv=Vector((.168,-.12,0));A0,A1=math.radians(80),math.radians(180);NR=10;L=.20   # 10 ribs, 11° apart (closer, their ends at the pivot read as one plane)   # opened 100°, spread up and to the left, clear of the palm fan
    angs=[A0+(A1-A0)*i/(NR-1) for i in range(NR)]
    def rib_z(i):return .0015+.0016*i   # the lowest rib lies on the ground, each next one on the one below
    for i,a in enumerate(angs):
        d=Vector((math.cos(a),math.sin(a),0));s=Vector((-d.y,d.x,0));tilt=(.21 if i%2 else -.21);z=rib_z(i)
        w=.0085 if i in (0,NR-1) else .0062;th=.0028 if i in (0,NR-1) else .0016
        bm=bmesh.new();pts=[]
        for u,ww in ((0,w*1.15),(.35,w),(1,w*.7)):
            for v in (-1,1):
                for t_ in (-1,1):
                    pts.append(pv+d*(L*u)+s*(v*ww/2)+Vector((0,0,z+t_*th/2))+Vector((0,0,1))*math.sin(tilt)*v*ww/2)
        vs=[bm.verts.new(p) for p in pts]   # 3 sections × 4 corners
        def q(a,b,c_,dd):bm.faces.new((vs[a],vs[b],vs[c_],vs[dd]))
        for j in range(2):
            o=j*4;n=o+4
            q(o+0,n+0,n+2,o+2);q(o+1,o+3,n+3,n+1);q(o+0,o+1,n+1,n+0);q(o+2,n+2,n+3,o+3)
        q(0,2,3,1);q(8,9,11,10)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        finish(f'LV20_Rib{i:02d}',bm,M['bamboo_split'],'Body',.05)
    _lathe('LV20_Rivet',[(0,.0055),(1,.0055)],(pv+Vector((0,0,.0012)),pv+Vector((0,0,rib_z(NR-1)+.0025))),M['brass'],'Body',NS=12,scale=.03)
    prow=[]
    NP=2*(NR-1)+1
    for j in range(NP):
        a=A0+(A1-A0)*j/(NP-1);d=Vector((math.cos(a),math.sin(a),0));zi=float(np.interp(j/2,range(NR),[rib_z(i) for i in range(NR)]))
        pl=.0028*(1 if j%2 else -1)
        prow.append([tuple(pv+d*r+Vector((0,0,zi+pl+.0012))) for r in np.linspace(.085,L-.004,5)])
    _sheet('LV20_Paper',prow,None,None,M['paper'],'Body',t=.0008)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        leaf=filled*(np.hypot(px-c.x,(py-c.y)/1.08)<R)*(pz>.003)
        th=np.arctan2(py-(c.y-R*1.08),px-c.x);v=.5+.5*np.sin(th*60)   # palm veins fanning from the handle
        col=col*(1-.18*(leaf*v)[...,None])
        return col,rough
    return {'paint':paint,'wear':.8,'grime':.5,'uv_angle':50,'notes':['a palm-leaf fan: 3 mm leaf disc, bamboo rim, cloth-bound handle (Detail_Fray: frayed leaf edge); veins painted',
            'a folding fan opened 100°: 10 ribs stacked on a brass rivet (alternately tilted 12°), thicker guards, a pleated plain paper leaf with nothing on it']}
PROPS['LV20']=LV20
