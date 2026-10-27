"""QX_SpiritHerb_Qinglan rebuild (creek orchid, Cymbidium-like spirit herb). Semi-real.
Form: a fan clump of keeled strap leaves, narrow at the base, widest at a third, long acute tips, arching in
brush-stroke S curves that cross each other; papery sheaths and pseudobulbs at the base | three upright
scapes with papery bracts carrying 5-7 nodding blossoms each (three cupped sepals, two hooded petals, a
recurved spotted lip, a pale column), the top ones still buds | a moss-covered stone behind the clump.
Ground: the shared soil / pebble / moss / litter / grass bed.
Post: scapes cut to stubs with fresh cut faces, most leaves sickle-cut at 8-18 cm, the young inner leaves
left, two new shoots; cut leaves, a cut scape and two fallen blossoms on the soil.
Origin: clump base at (0,0,0) = ground level; front -Y.
"""
import bpy,bmesh,math,random
from mathutils import Vector,Matrix,noise
import qx_kit as K
import qx_ore as O
import qx_gate as G
import qx_chilu as C
import qx_ground as GR

TAU=math.tau
BED=(.40,.36)

# ---------------------------------------------------------------- geometry
def leaf_path(base,az,L,t0,t1,sway,n=24):
    pts,h=K.arch(base,az,L,t0,t1,n,1.5);side=Vector((-h.y,h.x,0))
    return [p+side*sway*math.sin(math.pi*j/n)*(j/n) for j,p in enumerate(pts)],h

def leaf_widths(W,n,cut=None):
    ws=[]
    for j in range(n+1):
        t=j/n;w=W*(.38+.62*math.sin(min(1,t/.33)*math.pi/2))*(1-t)**.62
        ws.append(w+.0005)
    return ws

def petal_into(bm,c,d,f,L,W,curl,cup,rows,var,shape=.75,taper=.2):
    """Cupped lanceolate perianth part from c along d (unit), facing f; curl bends the tip toward +f."""
    side=f.cross(d).normalized();pts=[];ws=[]
    for j in range(rows+1):
        t=j/rows;pts.append(c+d*L*t+f*curl*L*t*t);ws.append(W*math.sin(math.pi*min(t*1.08,.999))**shape*(1-taper*t)+.0003)
    K.ribbon_into(bm,pts,ws,side,cup,0,7,var,lambda u:u*u)

def flower_into(bm,col_bm,c,f,u,sc,rng,bud=False):
    f=f.normalized();u=(u-f*u.dot(f)).normalized();s=f.cross(u)
    vr=rng.random()
    if bud:
        for v in K.ico_into(bm,2,.0032*sc,Matrix.Translation(c+f*.008*sc)@f.to_track_quat('Z','Y').to_matrix().to_4x4()@Matrix.Diagonal((1,1,2.6,1))):
            K.tag_uv(v,.5,.3+.6*K.c01((v.co-c).dot(f)/(.02*sc)),(vr,.35,0))
        return
    def dirn(a,fw):return (u*math.cos(a)+s*math.sin(a)+f*fw).normalized()
    petal_into(bm,c,dirn(0,.18),f,.031*sc,.0054*sc,.22,.30,12,(vr,0,0))                        # dorsal sepal, hooding forward
    for sg in (-1,1):petal_into(bm,c,dirn(sg*2.05,.10),f,.029*sc,.0050*sc,.10,.28,12,(vr,0,0))     # lateral sepals
    for sg in (-1,1):petal_into(bm,c+f*.002,dirn(sg*.62,.65),f,.021*sc,.0056*sc,.30,.40,10,(vr,0,0),.8,.1)   # petals over the column
    lip=(-u*.35+f).normalized();side=f.cross(lip).normalized();pts=[];ws=[]                      # recurved spotted lip
    for j in range(11):
        t=j/10;pts.append(c+f*.004+lip*.016*sc*t-u*.015*sc*t**2.0);ws.append(.0080*sc*(.5+.5*math.sin(math.pi*min(t*.9+.1,.999))**.6)+.0003)
    K.ribbon_into(bm,pts,ws,side,.36,0,7,(vr,0,1),lambda q:q*q)
    K.tube_into(col_bm,[c,c+f*.007*sc+u*.002,c+f*.013*sc+u*.003],[.0022*sc,.002*sc,.0016*sc],6)     # column
    for v in col_bm.verts[-12:]:K.tag_uv(v,.5,.5,(0,0,.6))

def sheath_into(bm,base,az,L,W,rng):
    h=Vector((math.cos(az),math.sin(az),0));side=Vector((-h.y,h.x,0))
    pts=[base+Vector((0,0,L*t))+h*.004*t*t for t in [j/6 for j in range(7)]]
    K.ribbon_into(bm,pts,[W*(1-.55*t)**.8+.0006 for t in [j/6 for j in range(7)]],side,1.1,rng.uniform(-.3,.3),7,(rng.random(),0,0),lambda u:u*u)

# ---------------------------------------------------------------- materials
def mat_orchid_leaf(name):
    """Glossy deep jade-green strap leaf: fine parallel veins, pale keel, yellow-green sheath base, thin
    yellow margin, dry straw tips (Var.g = dry tip length), fresh pale cut face (Var.b), back-light."""
    m,nt,bs=K.pbr(name,False,.32,.45);u,v=K.uv(nt);r,g,b=K.attr(nt);ob=K.coord(nt)
    mr,mx,ad,mrng,m_=K.mul,K.mix,K.add,K.mrange,K.math_
    ax=m_(nt,'ABSOLUTE',m_(nt,'SUBTRACT',u,.5))
    veins=K.wave_t(nt,K.comb(nt,u,0),11,'X',.2,1)
    col=K.ramp(nt,ad(nt,mr(nt,K.noise_t(nt,ob,6,4),.6),mr(nt,r,.4)),[(0,(.012,.040,.016)),(.5,(.020,.060,.024)),(1,(.034,.085,.032))])
    col=mx(nt,mr(nt,mrng(nt,v,.10,.0),.85),col,(.09,.12,.035))                                     # sheath base
    col=mx(nt,mr(nt,mrng(nt,ax,.04,.0),.45),col,(.06,.12,.05))                                     # keel
    col=mx(nt,mr(nt,mrng(nt,ax,.44,.5),.6),col,(.10,.12,.03))                                      # margin
    col=mx(nt,mr(nt,mrng(nt,veins,.75,1),.25),col,(.006,.02,.008))
    dry=mr(nt,mrng(nt,ad(nt,v,mr(nt,K.noise_t(nt,ob,20,3),.06)),m_(nt,'SUBTRACT',1.0,mr(nt,g,.30)),ad(nt,m_(nt,'SUBTRACT',1.0,mr(nt,g,.30)),.04)),mrng(nt,g,.01,.05))
    col=mx(nt,dry,col,K.ramp(nt,K.noise_t(nt,ob,30,3),[(0,(.16,.12,.06)),(1,(.26,.21,.11))]))
    col=mx(nt,mr(nt,mrng(nt,v,.7,1),mrng(nt,dry,.0,.3,.25,0)),col,(.07,.06,.02))                   # browning ahead of the dry zone
    cut=mrng(nt,b,.4,.9);col=mx(nt,cut,col,(.30,.34,.16))
    K.finish(nt,bs,col,mx(nt,dry,(.30,.30,.30),(.75,.75,.75)),ad(nt,mr(nt,veins,.25),mr(nt,mrng(nt,ax,.05,.0),-.4)),.25,.001)
    out=next(x for x in nt.nodes if x.type=='OUTPUT_MATERIAL');tr=K.node(nt,'ShaderNodeBsdfTranslucent')
    K._set(nt,tr.inputs['Color'],mx(nt,dry,(.06,.20,.05),(.30,.22,.08)))
    mixs=K.node(nt,'ShaderNodeMixShader',{0:.22});nt.links.new(bs.outputs[0],mixs.inputs[1]);nt.links.new(tr.outputs[0],mixs.inputs[2]);nt.links.new(mixs.outputs[0],out.inputs['Surface'])
    return m

def mat_blossom(name):
    """Pale jade sepals and petals with darker parallel veins and a greener base; ivory lip with red-violet
    spots (Var.b = 1); ivory column (Var.b = .6); buds greener (Var.g); soft inner light = spirit accent."""
    m,nt,bs=K.pbr(name,False,.42,.4);u,v=K.uv(nt);r,g,b=K.attr(nt);ob=K.coord(nt)
    mr,mx,ad,mrng,m_=K.mul,K.mix,K.add,K.mrange,K.math_
    ax=m_(nt,'ABSOLUTE',m_(nt,'SUBTRACT',u,.5))
    vein=mr(nt,mrng(nt,K.wave_t(nt,K.comb(nt,u,0),3.5,'X',.3,1),.80,.98),mrng(nt,v,.05,.25))
    col=K.ramp(nt,ad(nt,v,mr(nt,r,.15)),[(0,(.28,.36,.16)),(.3,(.60,.66,.44)),(1,(.80,.82,.66))])
    col=mx(nt,mr(nt,vein,.45),col,(.30,.20,.10))
    col=mx(nt,mr(nt,mrng(nt,ax,.40,.5),.3),col,(.62,.70,.56))
    lip=mrng(nt,b,.8,.95);spots=mr(nt,mr(nt,mrng(nt,K.voronoi_t(nt,K.comb(nt,mr(nt,u,9),mr(nt,v,13)),1),.26,.14),mrng(nt,v,.10,.25)),mrng(nt,v,.85,.65))
    lipc=mx(nt,spots,(.70,.68,.50),(.30,.035,.07));lipc=mx(nt,mrng(nt,v,.85,1),lipc,(.62,.62,.44))
    col=mx(nt,lip,col,lipc);col=mx(nt,mr(nt,mrng(nt,b,.5,.6),mrng(nt,b,.7,.62)),col,(.66,.68,.55))
    col=mx(nt,mr(nt,g,.8),col,(.12,.22,.08))
    sub=bs.inputs.get('Subsurface Weight')
    if sub:sub.default_value=.35;bs.inputs['Subsurface Radius'].default_value=(.5,.8,.4);bs.inputs['Subsurface Scale'].default_value=.002
    nt.links.new(K.ramp(nt,m_(nt,'SUBTRACT',1.0,v),[(0,(0,0,0)),(.6,(.03,.07,.05)),(1,(.10,.22,.16))]),bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.25
    K.finish(nt,bs,col,None,ad(nt,mr(nt,vein,.4),mr(nt,K.noise_t(nt,ob,150,2),.3)),.12,.0005)
    out=next(x for x in nt.nodes if x.type=='OUTPUT_MATERIAL');tr=K.node(nt,'ShaderNodeBsdfTranslucent');K._set(nt,tr.inputs['Color'],(.72,.76,.55))
    mixs=K.node(nt,'ShaderNodeMixShader',{0:.25});nt.links.new(bs.outputs[0],mixs.inputs[1]);nt.links.new(tr.outputs[0],mixs.inputs[2]);nt.links.new(mixs.outputs[0],out.inputs['Surface'])
    return m

def mat_scape(name):
    """Scape: jade green with a purple flush toward the top and on the bracts; fine striations; Var.b = fresh cut."""
    m,nt,bs=K.pbr(name,True,.45,.35);ob=K.coord(nt);z=K.sep(nt,ob)[2];r,g,b=K.attr(nt)
    col=K.ramp(nt,K.add(nt,K.mrange(nt,z,.05,.45),K.mul(nt,K.noise_t(nt,ob,12,3),.2)),[(0,(.08,.13,.045)),(.6,(.12,.16,.06)),(1,(.16,.13,.09))])
    col=K.mix(nt,K.mrange(nt,b,.4,.9),col,(.42,.48,.26))
    K.finish(nt,bs,col,None,K.noise_t(nt,K.scaled(nt,ob,(1,1,12)),80,2),.12,.001);return m

def mat_sheath(name):
    """Papery dry sheath: straw to mid brown, fine longitudinal fibres, darker frayed tips."""
    m,nt,bs=K.pbr(name,False,.8,.3);u,v=K.uv(nt);r,g,b=K.attr(nt);ob=K.coord(nt)
    fib=K.wave_t(nt,K.comb(nt,K.mul(nt,u,1.0),0),24,'X',2,2)
    col=K.ramp(nt,K.add(nt,K.mul(nt,fib,.35),K.add(nt,K.mul(nt,r,.35),K.mul(nt,v,.3))),[(0,(.07,.05,.025)),(.5,(.15,.11,.06)),(1,(.24,.19,.11))])
    col=K.mix(nt,K.mrange(nt,v,.0,.25,.6,0),col,(.10,.13,.05))
    K.finish(nt,bs,col,None,fib,.15,.0008)
    out=next(x for x in nt.nodes if x.type=='OUTPUT_MATERIAL');tr=K.node(nt,'ShaderNodeBsdfTranslucent');K._set(nt,tr.inputs['Color'],(.30,.20,.08))
    mixs=K.node(nt,'ShaderNodeMixShader',{0:.18});nt.links.new(bs.outputs[0],mixs.inputs[1]);nt.links.new(tr.outputs[0],mixs.inputs[2]);nt.links.new(mixs.outputs[0],out.inputs['Surface'])
    return m

# ---------------------------------------------------------------- build
def build(post):
    rng=random.Random(3101);ctx=K.ctx
    M={'leaf':mat_orchid_leaf('QX_Src_Qinglan_Leaf'),'blossom':mat_blossom('QX_Src_Qinglan_Blossom'),'scape':mat_scape('QX_Src_Qinglan_Scape'),
       'sheath':mat_sheath('QX_Src_Qinglan_Sheath'),'bulb':C.mat_stem_real('QX_Src_Qinglan_Pseudobulb'),
       'skirt':O.mat_skirt('QX_Src_Qinglan_Soil_Bed'),'moss':O.mat_moss_real('QX_Src_Qinglan_Moss'),
       'rock':O.mat_rock_real('QX_Src_Qinglan_Stone',False,False),'litter':C.mat_litter('QX_Src_Qinglan_Leaf_Litter')}
    hf=GR.bed('Qinglan',BED,.035,rng,M,14,22,[(-.22,.10,.08,.05),(.18,-.16,.06,.04)],7,.12,seed=31)
    # --- moss-covered stone behind the clump (the orchid grows in its lee)
    rb=O.hull_block((.06,.26,.05),(.17,.11,.10),4711,70,.42,(0,0,.5),rmin=.82);O.finish_block(rb,.02,0.0)
    G.dressed('Qinglan_Stone',rb,M['rock'],M['moss'],17,.006,.28,.38,True)
    # --- pseudobulbs and papery sheaths
    bu=K.new_bm()
    for k in range(4):
        a=k*TAU/4+.4;K.lathe_into(bu,[(0,0),(.014,.006),(.019,.020),(.016,.036),(.008,.046),(0,.049)],10,(.024*math.cos(a),.024*math.sin(a),hf(0,0)-.012),a,.06)
    K.link('Qinglan_Pseudobulbs',bu,[M['bulb']])
    sh=K.new_bm()
    for k in range(7):sheath_into(sh,Vector((.02*math.cos(k*GOLDEN_A),.02*math.sin(k*GOLDEN_A),hf(0,0)-.01)),k*GOLDEN_A,rng.uniform(.05,.09),rng.uniform(.012,.018),rng)
    K.link('Qinglan_Sheaths',sh,[M['sheath']])
    # --- leaves: outer long arching ones first, inner young ones shorter and more upright
    lv=K.new_bm();cut=[];z0=hf(0,0)-.005
    for i in range(22):
        inner=i>=16;az=i*K.GOLDEN+rng.uniform(-.2,.2)
        L=rng.uniform(.20,.32) if inner else rng.uniform(.42,.66);W=rng.uniform(.007,.009) if inner else rng.uniform(.009,.013)
        t0=rng.uniform(.02,.15) if inner else rng.uniform(.10,.32);t1=rng.uniform(.5,.9) if inner else rng.uniform(1.25,2.05)
        n=24;pts,h=leaf_path(Vector((.018*math.cos(az),.018*math.sin(az),z0)),az,L,t0,t1,rng.uniform(-.05,.05),n)
        ws=leaf_widths(W,n);side=Vector((-h.y,h.x,0));dry=rng.choice((0,0,0,.6,1.0)) if not inner else 0.0;tw=rng.uniform(-1.1,1.1)
        if post and not inner:
            keep=max(4,round(n*rng.uniform(.08,.18)/(L/.5)*1.6));keep=min(keep,n-4);pts=pts[:keep+1];ws=ws[:keep+1];ws[-1]=ws[-2]
            pts[-1]=pts[-1]+(pts[-1]-pts[-2]).normalized()*.004*rng.uniform(-1,1)                          # angled sickle cut
            K.ribbon_into(lv,pts,ws,side,.5,tw*keep/n,5,v1=keep/n,var_fn=lambda j,nn,rr=rng.random():(rr,0,1.0 if j==nn-1 else 0),prof=lambda u:abs(u))
            cut.append((L,W,az,keep/n));continue
        K.ribbon_into(lv,pts,ws,side,.5,tw,5,(rng.random(),dry,0),lambda u:abs(u))
    if post:                                                                                        # new shoots
        for j in range(2):
            az=j*2.6+1.0;pts,h=K.arch((.008*math.cos(az),.008*math.sin(az),z0),az,.09,.02,.25,10);K.ribbon_into(lv,pts,leaf_widths(.006,10),Vector((-h.y,h.x,0)),.5,0,5,(.2,0,0),lambda u:abs(u),v1=.35)
    K.link('Qinglan_Leaves',lv,[M['leaf']])
    sc_bm=K.new_bm();bl=K.new_bm()
    scapes=[(.5,.44),(2.9,.40),(4.6,.36)]
    if post:
        for j,(az,H) in enumerate(scapes):                                                          # stubs with fresh cut faces
            b0=Vector((.012*math.cos(az),.012*math.sin(az),z0));top=b0+Vector((.006*math.cos(az),.006*math.sin(az),rng.uniform(.035,.06)))
            rings=K.tube_into(sc_bm,[b0,top],[.0034,.0032],8)
            for v in rings[-1]:K.tag_uv(v,.5,.5,(0,0,1))
            sheath_into(sc_bm,b0,az+.5,.03,.007,rng)
        fl=[]                                                                                       # the cut scape lying on the soil
        a=.9;c=Vector((-.17,-.12,0));d=Vector((math.cos(a),math.sin(a),0))
        pts=[c+d*.32*t for t in [k/10 for k in range(11)]];pts=[p+Vector((0,0,hf(p.x,p.y)+.004+.006*math.sin(t*3))) for t,p in zip([k/10 for k in range(11)],pts)]
        K.tube_into(sc_bm,pts,[.003-.001*k/10 for k in range(11)],6)
        for k in (5,7,9):
            p=pts[k];flower_into(bl,sc_bm,p+Vector((0,0,.006)),Vector((0,0,1))+Vector((rng.uniform(-.3,.3),rng.uniform(-.3,.3),0)),d,.9,rng)
        for x,y in [(.14,-.20),(-.05,-.24)]:                                                        # fallen blossoms
            flower_into(bl,sc_bm,Vector((x,y,hf(x,y)+.006)),Vector((rng.uniform(-.4,.4),rng.uniform(-.4,.4),1)),Vector((1,0,0)),.85,rng)
        ly=K.new_bm()                                                                               # cut leaves on the soil
        for k,(L,W,az,kv) in enumerate(cut[:5]):
            a=k*1.9+rng.uniform(-.4,.4);rr=rng.uniform(.10,.28);c=Vector((rr*math.cos(a),rr*math.sin(a),0));d=Vector((math.cos(a+1.4),math.sin(a+1.4),0));L2=L*(1-kv)*rng.uniform(.6,.9)
            pts=[]
            for s in range(13):
                t=s/12;q=c+d*L2*(t-.5)+d.cross(Vector((0,0,1)))*.04*math.sin(t*2.6);pts.append(q+Vector((0,0,hf(q.x,q.y)+.003+.012*t*t)))
            K.ribbon_into(ly,pts,[W*(1-t/12)**.55+.0006 for t in range(13)],Vector((0,0,1)).cross(d),.45,rng.uniform(-.8,.8),5,(rng.random(),.0,0),lambda u:abs(u),v0=kv)
    else:
        for j,(az,H) in enumerate(scapes):
            b0=Vector((.012*math.cos(az),.012*math.sin(az),z0));h=Vector((math.cos(az),math.sin(az),0));n=18
            pts=[b0+h*(.05*(t**1.4)+.012*math.sin(t*math.pi))+Vector((0,0,H*t)) for t in [k/n for k in range(n+1)]]
            K.tube_into(sc_bm,pts,[.0034-.0016*k/n for k in range(n+1)],8)
            for t0,Lb in ((.12,.035),(.26,.03),(.40,.022)):sheath_into(sc_bm,pts[int(t0*n)],az+t0*9,Lb,.006,rng)
            nf=7 if j==0 else 6
            for k in range(nf):
                t=.48+.48*k/(nf-1);i0=int(t*n);p=pts[min(i0,n)];sd=(1 if k%2 else -1)
                out=(h.cross(Vector((0,0,1)))*sd*.9+h*.35).normalized();c=p+out*.02+Vector((0,0,-.006))
                K.tube_into(sc_bm,[p,p+out*.010+Vector((0,0,.002)),c],[.0016,.0014,.0013],5,False)            # pedicel + ovary
                sheath_into(sc_bm,p,az+sd*1.2,.012,.003,rng)                                                # floral bract
                face=(out+Vector((0,0,-.25))).normalized()
                flower_into(bl,sc_bm,c,face,Vector((0,0,1)),rng.uniform(1.2,1.38),rng,bud=k>=nf-2)
    ly_v={v:K.ctx.vdata.pop(v) for v in ly.verts if v in K.ctx.vdata} if post else {}
    bl_v={v:K.ctx.vdata.pop(v) for v in bl.verts if v in K.ctx.vdata}                              # K.link clears vdata: keep the blossoms' UV / Var
    K.link('Qinglan_Scapes',sc_bm,[M['scape']])
    K.ctx.vdata.update(bl_v)
    if len(bl.verts):K.link('Qinglan_Blossoms',bl,[M['blossom']],True)
    else:bl.free()
    if post:K.ctx.vdata.update(ly_v);K.link('Qinglan_Cut_Leaves_On_Soil',ly,[M['leaf']])
    ctx.extra.update({'state_change':'post: scapes cut to stubs, outer leaves sickle-cut, young leaves kept, two new shoots, cut leaves / scape / blossoms on the soil' if post else 'pre'})

GOLDEN_A=2.39996
