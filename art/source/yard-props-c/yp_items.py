# YP03–YP05 shapes (the 11/14 120h pack, batch A: A1 yard props), read by build_yp.py.
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _drop_part(o):
    parts.remove(o);bpy.data.objects.remove(o)
def _flat_foot(o,z=.004):
    """a splayed leg's end is square to the leg: bring everything under z down to the ground so the foot stands flat"""
    for v in o.data.vertices:
        if v.co.z<z:v.co.z=0.
def _moss_low(col,rough,P,onrm,noise,cav,filled,h=.10,amt=.5,soil=.05):
    """moss creeping up from the ground and soil right at the foot (painted)"""
    pz=P[...,2];ms=filled*np.clip((noise-.45)*3+np.clip((h-pz)/h,0,1)*1.1-.55+(cav-.5)*.6,0,1)*np.clip((h*1.6-pz)/(h*.6),0,1)
    col=col*(1-amt*ms[...,None])+ms[...,None]*amt*np.array([.21,.29,.11]);rough=np.clip(rough+.05*ms,0,1)
    so=filled*np.clip((soil-pz)/soil,0,1)*np.clip(.4+noise,0,1);col=col*(1-.45*so[...,None])+so[...,None]*.45*np.array([.22,.17,.11])
    return col,rough

# ---------------- YP03 wooden water bucket with a ladle (cand-4) ----------------
def YP03(M):
    """a coopered bucket, wider at the top: fourteen staves, two riveted iron hoops, a bottom board; two opposite staves
    run up past the rim, drilled, and a hemp rope goes through them as the handle (knotted outside). Water near the rim.
    A long-handled wooden ladle lies across the rim, its bowl just in the water."""
    rr=random.Random(6301);WD,WB,IR,HP=M['cedar'],M['cedar_b'],M['iron'],M['hemp']
    H=.30;R0=.150;R1=.178;T=.014;N=14;rw=lambda z:R0+(R1-R0)*z/H;turn=Matrix.Rotation(-math.pi/N,4,'Z')
    st=_staves('YP03_Stave',(0,0,0),[(0,R0),(H,R1)],T,N,.012,WD,'Body',rows=4)
    ear=_staves('YP03_Ear',(0,0,0),[(0,R0),(H,R1),(.405,rw(.405))],T+.004,N,.012,WB,'Body',rows=6)
    for k in range(N):
        if k in (0,7):_drop_part(st[k])
        else:
            _drop_part(ear[k]);st[k].data.transform(Matrix.Translation((0,0,rr.uniform(-.004,.003))))   # stave tops not all level
            st[k].data.transform(turn)
    for k in (0,7):
        e=ear[k];e.data.transform(turn);s=1 if k==0 else -1
        _boolean(e,_cyl_cutter(f'YP03_cutEar{k}',(s*(rw(.365)-.008),0,.365),(1,0,0),.0125,.06))
    for q,(z0,z1) in enumerate(((.055,.083),(.212,.240))):   # two iron hoops with a ring of rivets
        zm=(z0+z1)/2;_ring_band(f'YP03_Hoop{q}',(0,0,0),rw(zm)+.004,rw(zm)-.0015,z0,z1,IR,'Body',NS=28,scale=.2)
        for j in range(10):
            a=math.tau*(j+.5*q)/10+rr.uniform(-.05,.05);n=Vector((math.cos(a),math.sin(a),0));p=n*(rw(zm)+.0035)+Vector((0,0,zm))
            _lathe(f'YP03_Rivet{q}{j}',[(0,.0058),(.6,.0048),(1,0)],(p,p+n*.0042),IR,'Detail_Rivets',NS=6,scale=.03)
    _lathe('YP03_Bottom',[(0,R0-.004),(1,rw(.036)-.004)],((0,0,.020),(0,0,.036)),WB,'Body',NS=28)
    zw=.262;wo=_lathe('YP03_Water',[(0,rw(zw)-T+.003),(1,rw(zw)-T+.003)],((0,0,zw-.012),(0,0,zw)),M['water'],'Body',NS=28)
    for p_ in wo.data.polygons:p_.use_smooth=False   # a flat sheet, not a dome
    # the rope handle: through both ears, a knot outside each
    xe=rw(.365);pts=[Vector((-xe-.022,0,.352)),Vector((-xe+.004,0,.365))]
    pts+=[Vector((.150*math.cos(t),.028*math.sin(t),.378+.082*math.sin(t))) for t in np.linspace(math.pi,0,15)]
    pts+=[Vector((xe-.004,0,.365)),Vector((xe+.022,0,.352))]
    rope('YP03_Rope',pts,.0085,HP,'Body')
    for q,s in enumerate((-1,1)):
        o=_blob(f'YP03_Knot{q}',(.036,.034,.036),6310+q,HP,'Body',sub=2,bumps=4,amp=.10,scale=.06);o.data.transform(Matrix.Translation((s*(xe+.021),0,.332)))
    # the ladle: a turned bowl and a long handle, lying across the rim clear of the ears
    ph=math.radians(-27);d=Vector((math.cos(ph),math.sin(ph),0));cc=-d*.074
    _lathe('YP03_LadleBowl',[(0,.002),(0,.034),(.45,.058),(1,.063),(1,.057),(.5,.052),(.14,.030),(.14,.002)],(cc+Vector((0,0,.250)),cc+Vector((0,0,.305))),M['floatwood'],'Body',NS=20,scale=.15,loop=True)
    _lathe('YP03_LadleHandle',[(0,.0105),(.5,.0095),(.93,.009),(.97,.0115),(1,.0105)],(cc+d*.052+Vector((0,0,.2955)),d*.292+Vector((0,0,.3185))),M['floatwood'],'Body',NS=8,scale=.15)
    # one stave was mended with a small board
    o=box('YP03_Patch',(.062,.008,.044),(0,0,0),WB,'Body',bev=.002,segs=1,jit=.0006,seed=6320,rot=Matrix.Rotation(.12,4,'Y'))
    o.data.transform(Matrix.Translation((.03,-(rw(.135)+.001),.135)))
    for q,(dx,dz) in enumerate(((-.022,.014),(.022,.012),(-.021,-.013),(.023,-.014))):
        p=Vector((.03+dx,-(rw(.135)+.0045),.135+dz));_lathe(f'YP03_Nail{q}',[(0,.0035),(1,0)],(p,p+Vector((0,-.0025,0))),IR,'Detail_Rivets',NS=6,scale=.03)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2];pr=np.hypot(px,py)
        wall=filled*(pr>.13)*(np.abs(onrm[...,2])<.6)
        for zh in (.055,.212):   # rust run a little way down from each hoop
            run=wall*np.clip((zh-pz)/.05,0,1)*np.clip((pz-zh+.07)/.02,0,1)*np.clip((np.sin(np.arctan2(py,px)*23+noise*5)-.2)*1.4,0,1)
            col=col*(1-.30*run[...,None])+run[...,None]*.30*np.array([.33,.19,.10])
        inside=filled*(pr<.166)*(pz>.262)*(pz<.31)*(np.abs(onrm[...,2])<.6);col=col*(1-.30*inside[...,None])   # wet band inside above the water
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,wall,h=.07,amt=.45,soil=.03)
        return col,rough
    return {'paint':paint,'wear':.9,'grime':.9,'damp':.075,'uv_angle':60,
            'notes':['fourteen staves (their tops not level), two iron hoops each with ten rivets (Detail_Rivets), a bottom board let into the staves',
                     'two opposite staves run up past the rim and are drilled; the hemp rope handle goes through and is knotted outside','still water 4 cm below the rim; the ladle (turned bowl, long handle) lies across the rim clear of the ears',
                     'one stave mended with a small nailed board; painted: rust runs under the hoops, the wet band inside, damp and moss at the foot']}
PROPS['YP03']=YP03

# ---------------- YP04 stone mortar and wooden pestle (cand-3) ----------------
def YP04(M):
    """one thick block of stone, hand-chiselled: the outside is broken into facets (not a smooth cylinder), a little
    waisted, a foot ring at the bottom, a deep round bowl. The wooden pestle leans in the bowl against the rim:
    a rounded working end, the shaft thinner upward, four turns of cord at the grip, a knob on top. Husked grain in the bowl."""
    rr=random.Random(6401);ST,WD,HP=M['stone'],M['cedar_b'],M['hemp'];NS=18
    rings=[(.150,0.,0),(.203,.004,0),(.214,.030,0),(.206,.072,0),(.187,.105,0),(.181,.20,0),(.196,.32,0),(.213,.40,0),(.216,.436,0),(.206,.452,0),
           (.168,.452,0),(.158,.43,0),(.150,.36,0),(.125,.27,0),(.08,.205,0),(.03,.185,0)]
    outer=rings[:10];dense=[outer[0]]
    for a_,b_ in zip(outer[1:],outer[2:]):   # more rows down the outside so the facets are about as tall as they are wide
        n_=max(1,round((b_[1]-a_[1])/.055));dense+=[(a_[0]+(b_[0]-a_[0])*i/n_,a_[1]+(b_[1]-a_[1])*i/n_,0) for i in range(n_)]
    rings=dense+rings[9:]
    o=_turned('YP04_Mortar',rings,NS,ST,'Body',scale=.35)
    zrow={}
    for v in o.data.vertices:   # chisel facets: every outside vertex pushed in or out and round a little, each on its own
        r=math.hypot(v.co.x,v.co.y)
        if r>.172 and .02<v.co.z<.445:
            a=math.atan2(v.co.y,v.co.x)+rr.uniform(-.06,.06)+zrow.setdefault(round(v.co.z,3),rr.uniform(-.09,.09));r+=rr.uniform(-.009,.007);v.co.x=r*math.cos(a);v.co.y=r*math.sin(a);v.co.z+=rr.uniform(-.012,.012)
        elif r>.14 and v.co.z>.445:v.co.z+=rr.uniform(-.006,.004)   # the rim is not level
    for p in o.data.polygons:
        c=p.center
        if math.hypot(c.x,c.y)>.165 and c.z<.449:p.use_smooth=False
    cut=_cutter('YP04_cutCrack',(.006,.050,.125),(0,0,0));cut.data.transform(Matrix.Rotation(.10,4,'Y'));cut.data.transform(Matrix.Translation((.045,-.212,.405)))
    _boolean(o,cut)   # a crack down from the rim on the front (outer half of the wall only)
    A=Vector((.035,.018,.196));B=Vector((.238,-.036,.700));d=(B-A).normalized();L=(B-A).length
    _lathe('YP04_Pestle',[(0,0),(.02,.030),(.07,.043),(.14,.044),(.22,.036),(.5,.029),(.8,.026),(.9,.027),(.93,.040),(.965,.046),(.99,.034),(1,0)],(A,B),WD,'Body',NS=14,scale=.25)
    for q in range(4):_ring(f'YP04_Cord{q}',A+d*(L*(.655+.021*q)),d,.0295,.0042,HP,'Body',n=14)
    g=_lathe('YP04_Grain',[(0,.125),(.55,.095),(.9,.04),(1,0)],((0,0,.198),(0,0,.243)),M['hay'],'Body',NS=16,scale=.12);jitter(g,.004,6410,freq=40)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2];pr=np.hypot(px,py)
        stone=filled*(col[...,2]>col[...,0]*.72)
        out=stone*(pr>.16)*(pz<.45)
        col=col*(1-.16*(out*np.clip(.9-noise*1.2,0,1))[...,None])                                                          # weathered darker outside, unevenly
        bowl=stone*(pr<.165)*(pz>.19);col=col*(1+.04*bowl[...,None]);rough=np.clip(rough-.12*bowl,0,1)                 # the bowl worn smoother and paler
        dust=stone*(pz>.445)*np.clip(.3+noise,0,1);col=col*(1-.15*dust[...,None])+dust[...,None]*.15*np.array([.66,.60,.47])   # meal dust on the rim
        col,rough=_moss_low(col,rough,P,onrm,noise,cav,out,h=.13,amt=.55,soil=.045)
        grain=filled*(1-stone)*(pz<.25)*(pr<.13);sp=np.clip((np.sin(px*900+py*300)*np.sin(py*800-px*250)-.2)*2,0,1)
        col=col*(1-.18*(grain*sp)[...,None])
        return col,rough
    return {'paint':paint,'wear':.9,'grime':.9,'uv_angle':60,'collision_box':((.43,.43,.45),(0,0,.225)),
            'notes':['one block of stone: the outside is chiselled into facets (flat shaded, every vertex moved on its own), a little waisted, a foot ring; the bowl is deep and round and smooth; a crack runs down from the rim on the front',
                     'the pestle leans in the bowl against the rim: rounded working end, four turns of cord at the grip, a knob on top; a small heap of grain in the bowl',
                     'the stone patch and iron staples of the three-view are left out (a cracked mortar is not mended that way)',
                     'painted: the weathered outside, the smoother worn bowl, meal dust on the rim, moss and soil at the foot; the collision box is the mortar only']}
PROPS['YP04']=YP04

# ---------------- YP05 wooden benches, long and short (cand-4) ----------------
def _bench(M,pid,L,seed,patch):
    """a thick plank seat dished where people sit, its edges not straight; four square legs splayed toward the ends and
    to front and back, their tenons through the seat (end grain shows on top); a short rail at each end and a long rail
    front and back, the rail tenons through the legs and keyed with a wedge."""
    rr=random.Random(seed);WD,WB,EG=M['cedar'],M['cedar_b'],M['endgrain'];W=.26;H=.45;T=.076;NSt=11;st=[]
    ph=[rr.uniform(0,6.28) for _ in range(4)]
    for i in range(NSt):
        u=i/(NSt-1);x=-L/2+L*u;dish=.016*math.sin(math.pi*u)**1.5+.004*math.sin(3*math.pi*u+ph[0])*math.sin(math.pi*u)
        w=W+.010*math.sin(2.2*math.pi*u+ph[1])+.006*math.sin(5*math.pi*u+ph[2])-(.012 if i in (0,NSt-1) else 0)
        yo=.004*math.sin(1.7*math.pi*u+ph[3]);st.append(((x,yo,H-T/2-dish/2),w,T-dish,.013))
    _beam(f'{pid}_Seat',st,WD,'Body',jit=.0015,seed=seed)
    lx0=L/2-.125;lx1=L/2-.050;ly0=W/2-.058;ly1=W/2+.024;ZT=H-T+.012
    def legpt(sx,sy,z):
        a=Vector((sx*lx1,sy*ly1,0));b=Vector((sx*lx0,sy*ly0,ZT));return a.lerp(b,z/ZT)
    for q,(sx,sy) in enumerate(((-1,-1),(1,-1),(-1,1),(1,1))):
        o=_bar(f'{pid}_Leg{q}',legpt(sx,sy,-.014),legpt(sx,sy,ZT),.072,.062,WB if q%3 else WD,'Body',up=(1,0,0),bev=.005,seed=seed+q,ends=(1.06,.94));_flat_foot(o)
        t0=legpt(sx,sy,ZT-.02);dz=(legpt(sx,sy,ZT)-legpt(sx,sy,0)).normalized()
        o=_bar(f'{pid}_Tenon{q}',t0,t0+dz*((H+.004-t0.z)/dz.z),.040,.028,EG,'Body',up=(1,0,0),bev=.002,jit=.0004,seed=seed+10+q)   # through the seat
        u_=(sx*lx0+L/2)/L;zt=H-(.016*math.sin(math.pi*u_)**1.5+.004*math.sin(3*math.pi*u_+ph[0])*math.sin(math.pi*u_))+.004
        for v in o.data.vertices:v.co.z=min(v.co.z,zt)   # sawn off 4 mm proud of the seat
    zs=.150;zl=.205
    for q,sx in enumerate((-1,1)):   # short end rails, through both legs
        a=legpt(sx,-1,zs);b=legpt(sx,1,zs);dv=(b-a).normalized()
        _bar(f'{pid}_EndRail{q}',a-dv*.058,b+dv*.058,.030,.044,WD,'Body',up=(0,0,1),bev=.004,seed=seed+20+q)
        for j,(p,s) in enumerate(((a,-1),(b,1))):
            k=p+dv*s*.043;_bar(f'{pid}_EndKey{q}{j}',k+Vector((0,0,-.030)),k+Vector((.004*sx,0,.034)),.010,.012,WB,'Detail_Keys',up=(1,0,0),bev=.0015,jit=0,ends=(.7,1.15))
    for q,sy in enumerate((-1,1)):   # long rails front and back
        a=legpt(-1,sy,zl);b=legpt(1,sy,zl);dv=(b-a).normalized()
        _bar(f'{pid}_Rail{q}',a-dv*.062,b+dv*.062,.030,.046,WB,'Body',up=(0,0,1),bev=.004,seed=seed+30+q,jit=.0012)
        for j,(p,s) in enumerate(((a,-1),(b,1))):
            k=p+dv*s*.047;_bar(f'{pid}_Key{q}{j}',k+Vector((0,0,-.031)),k+Vector((0,.004*sy,.035)),.010,.012,WD,'Detail_Keys',up=(0,1,0),bev=.0015,jit=0,ends=(.7,1.15))
    if patch:   # a mended place on the front edge of the seat
        o=box(f'{pid}_Patch',(.19,.009,.034),(patch,-W/2-.0005,H-.034),WB,'Body',bev=.002,segs=1,jit=.0008,seed=seed+40)
        for q,dx in enumerate((-.075,-.025,.03,.078)):
            p=Vector((patch+dx,-W/2-.005,H-.034+.006*(-1)**q));_lathe(f'{pid}_Nail{q}',[(0,.0035),(1,0)],(p,p+Vector((0,-.0025,0))),M['iron'],'Detail_Keys',NS=6,scale=.03)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        top=filled*(pz>H-.03)*np.clip(onrm[...,2],0,1)
        sit=top*np.clip(1-(np.abs(py)/(W*.42))**2,0,1)*np.clip(.45+.8*noise,0,1)*np.clip(1-(np.abs(px)/(L*.46))**4,0,1)
        col=col*(1+.16*sit[...,None]);rough=np.clip(rough-.22*sit,0,1)                      # sat smooth and pale along the middle
        foot=filled*np.clip((.07-pz)/.07,0,1)*np.clip(.3+noise,0,1);col=col*(1-.45*foot[...,None])+foot[...,None]*.45*np.array([.23,.18,.12])   # mud on the feet
        ms=filled*np.clip((noise-.6)*4,0,1)*np.clip((.16-pz)/.1,0,1);col=col*(1-.4*ms[...,None])+ms[...,None]*.4*np.array([.22,.30,.11])
        return col,rough
    return {'paint':paint,'wear':1.,'grime':.9,'uv_angle':60,'collision_box':((L,.30,H),(0,0,H/2)),
            'notes':['a thick plank seat, dished in the middle (in the shape), its edges not straight; four legs splayed toward the ends and to front and back, their tenons through the seat, sawn off 4 mm proud',
                     'a short rail at each end and a long rail front and back; the rail tenons go through the legs and are keyed with wedges (Detail_Keys)'+('; a nailed mending board on the front edge of the seat' if patch else ''),
                     'painted: the seat worn pale and smooth along the middle, mud and a little moss on the feet']}
PROPS['YP05_01']=lambda M:_bench(M,'YP05_01',1.50,6501,.36)
PROPS['YP05_02']=lambda M:_bench(M,'YP05_02',.62,6502,0)
