# YP06 shapes (the 11/14 120h pack, batch A), read by build_yp.py after yp_items_b.py (same namespace).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _straws(tag,pts_dirs,rr,mat,grp,L=(.03,.06),r=.0026):
    """a fringe: one loose straw end from each point along its direction, each bent its own way"""
    for i,(p,d) in enumerate(pts_dirs):
        p=Vector(p);d=Vector(d).normalized();l=rr.uniform(*L);s=Vector((-d.y,d.x,0))*rr.uniform(-.35,.35)+Vector((0,0,rr.uniform(-.10,.30)))
        _taper(f'{tag}{i:03d}',[p-d*.012,p+(d+s*.4)*l*.5,p+(d+s)*l],[r,r*.85,r*.3],mat,grp,sides=3,scale=.08,up=(0,0,1))

# ---------------- YP06_01 rush mat, spread on the ground (cand-4) ----------------
def YP06_01(M):
    """a woven rush mat 1.7 × 0.85 m lying on the ground: not a flat sheet — it rides over the ground in low waves and
    one long rumple; loose straw ends stick out all round; one tear (painted, cut into the relief); a cloth patch sewn on."""
    rr=random.Random(6601);W,D=1.70,.85;ph=[rr.uniform(0,6.28) for _ in range(6)]
    def zf(x,y):
        und=.0035*math.sin(x*7+ph[0])*math.sin(y*9+ph[1])+.0025*math.sin(x*17+y*5+ph[2])
        rum=.014*math.exp(-((x*.45+y-.08)/.035)**2)*max(0.,1-abs(x+.25)/.45)          # a rumple running slantwise
        lift=.020*max(0.,1-math.hypot(x-W/2+.16,y+D/2-.14)/.26)**2                      # one corner riding up
        return .011+und+rum+lift
    _earth('YP06_01_Mat',W,D,zf,M['mat'],'Body',NX=56,NY=30,scale=.5,p=16.,wob=.010,seed=6602)
    pd=[]
    for k in range(52):
        x=-W/2+.07+(W-.14)*(k+rr.uniform(-.3,.3))/51
        for sy in (-1,1):pd.append(((x,sy*(D/2-.008),.006),(rr.uniform(-.25,.25),sy,0)))
    for k in range(26):
        y=-D/2+.07+(D-.14)*(k+rr.uniform(-.3,.3))/25
        for sx in (-1,1):pd.append(((sx*(W/2-.008),y,.006),(sx,rr.uniform(-.25,.25),0)))
    _straws('YP06_01_Fr',pd,rr,M['straw'],'Body')
    px_,py_=-.52,.03;rot=Matrix.Rotation(.12,4,'Z')   # the sewn cloth patch
    o=box('YP06_01_Patch',(.22,.17,.012),(0,0,0),M['linen_b'],'Body',bev=.002,segs=1,cuts=2,jit=.0012,seed=6610,rot=rot);o.data.transform(Matrix.Translation((px_,py_,zf(px_,py_)+.0005)))
    k=0
    for sx,sy,n in ((0,1,6),(0,-1,6),(1,0,4),(-1,0,4)):
        for i in range(n):
            t=(i+.5)/n-.5;loc=Vector((t*.20 if sx==0 else sx*.11,sy*.085 if sx==0 else t*.15,0));out=Vector((sx,sy,0));c=rot@loc+Vector((px_,py_,0));dv=rot@out
            a=c-dv*.012;b=c+dv*.014;tube(f'YP06_01_Stitch{k}',[(a.x,a.y,zf(a.x,a.y)+.0075),(c.x,c.y,zf(c.x,c.y)+.0105),(b.x,b.y,zf(b.x,b.y)+.0012)],.0017,M['cord_dark'],'Detail_Stitches',sides=3,scale=.05,up=(0,0,1));k+=1
    tear=[(.30,-.21),(.33,-.196),(.37,-.204),(.41,-.188),(.45,-.197),(.50,-.176),(.54,-.183)];R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];h=np.zeros(px.shape,np.float32);P2=P*np.array([1,1,0],np.float32)
        mat=filled*(mid>.5)*(onrm[...,2]>.3)
        tr=mat*_segd(P2,[(x,y,0) for x,y in tear],.013)*np.clip(.35+1.3*_fb(P,90.,6620,2),0,1)*np.clip(1-np.abs(px-.42)/.14,0,1)**.5;hole=np.clip((tr-.50)*5,0,1)
        col=col*(1-hole[...,None])+hole[...,None]*np.array([.17,.13,.09]);h-=.003*hole                                   # the tear: the ground shows through
        fray=np.clip(tr*2.2,0,1)*(1-hole);col=col*(1+.18*fray[...,None])                                                  # frayed pale ends round it
        gy=np.clip((_fb(P,3.,6621,3)-.45)*3,0,1)*mat;col=col*(1-.30*gy[...,None])+gy[...,None]*.30*np.array([.46,.43,.36])   # weathered grey patches
        dirt=mat*np.clip((_fb(P,5.,6622,3)-.52)*3,0,1);col=col*(1-.28*dirt[...,None])+dirt[...,None]*.28*np.array([.25,.19,.12])
        ms=mat*np.clip((_fb(P,7.,6623,3)-.60)*5,0,1)*np.clip((np.abs(py)-.18)/.2+(np.abs(px)-.5)/.4,0,1);col=col*(1-.45*ms[...,None])+ms[...,None]*.45*np.array([.26,.33,.13])   # a little moss toward the edges
        worn=mat*np.clip(1-np.hypot((px+.1)/.45,py/.22),0,1);col=col*(1+.10*worn[...,None]);rough=np.clip(rough-.10*worn,0,1)   # walked pale in the middle
        R_['h']=h;return col,rough
    M['mat']['mid']=1.
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.3,'grime':.5,'ao_k':.4,'uv_angle':66,
            'notes':['a woven rush mat lying on the ground, 1 cm thick: low waves, one slanting rumple and one corner riding up are in the shape; 156 loose straw ends round the edge',
                     'a cloth patch sewn on with 20 stitches (Detail_Stitches); the weave is in the texture and the normal map',
                     'painted, with the relief also in the normal map: one tear with frayed ends, grey weathered patches, dirt, a little moss toward the edges, the middle walked pale','no collision: it is walked over']}
PROPS['YP06_01']=YP06_01

# ---------------- YP06_02 the same mat rolled up and tied (cand-4) ----------------
def YP06_02(M):
    """the mat rolled into a spiral (the rings show at both ends), lying on its side, a little flattened by its own
    weight; two straw ropes round it, each knotted with two loose tails; straw ends stick out of both ends."""
    rr=random.Random(6651);L=.86;T=.009;PITCH=.0125;TURNS=4.3;R0=.030;NT=int(TURNS*18);NX=8;SQ=.90
    def rad(i):return R0+PITCH*TURNS*i/NT
    def pt(i,x,dr=0.):
        a=math.tau*TURNS*i/NT;r=rad(i)+dr;return Vector((x,r*math.cos(a),r*math.sin(a)*SQ))
    xo=[[(-L/2+rr.uniform(-.012,.012)*(1 if j in (0,NX) else 0)) if j==0 else (L/2+rr.uniform(-.012,.012)) if j==NX else -L/2+L*j/NX for j in range(NX+1)] for i in range(NT+1)]
    bm=bmesh.new();O=[[bm.verts.new(pt(i,xo[i][j],T/2)) for j in range(NX+1)] for i in range(NT+1)];I=[[bm.verts.new(pt(i,xo[i][j],-T/2)) for j in range(NX+1)] for i in range(NT+1)]
    for i in range(NT):
        for j in range(NX):
            f=bm.faces.new((O[i][j],O[i+1][j],O[i+1][j+1],O[i][j+1]));f.smooth=True
            f=bm.faces.new((I[i][j],I[i][j+1],I[i+1][j+1],I[i+1][j]));f.smooth=True
        bm.faces.new((O[i][0],I[i][0],I[i+1][0],O[i+1][0]));bm.faces.new((O[i][NX],O[i+1][NX],I[i+1][NX],I[i][NX]))
    for j in range(NX):bm.faces.new((O[0][j],O[0][j+1],I[0][j+1],I[0][j]));bm.faces.new((O[NT][j],I[NT][j],I[NT][j+1],O[NT][j+1]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);o=finish('YP06_02_Roll',bm,M['mat'],'Body',.5);jitter(o,.0015,6652,freq=20)
    pd=[]
    for i in range(0,NT+1,2):
        for s in (-1,1):p=pt(i,s*L/2);pd.append((p,(s,rr.uniform(-.3,.3),rr.uniform(-.3,.3))))
    for j in range(1,NX*3,3):
        x=-L/2+L*j/(NX*3);p=pt(NT,x,T/2);a=math.tau*TURNS;pd.append((p,(rr.uniform(-.3,.3),-math.sin(a),math.cos(a)*SQ)))   # the loose long edge of the outer turn
    _straws('YP06_02_Fr',pd,rr,M['straw'],'Body',L=(.025,.05))
    for q,x in enumerate((-.24,.25)):   # two straw ropes, each knotted on top
        ring=[Vector((x-.004+.008*k/20,(rad(NT)+T/2+.0052)*math.cos(math.tau*k/20+1.75),(rad(NT)+T/2+.0052)*math.sin(math.tau*k/20+1.75)*SQ)) for k in range(21)]
        rope(f'YP06_02_Tie{q}',ring,.0055,M['straw'],'Body')
        top=Vector((x,0,(rad(NT)+T/2+.008)*SQ));kb=_blob(f'YP06_02_Knot{q}',(.034,.030,.024),6660+q,M['straw'],'Body',sub=2,bumps=4,amp=.12,scale=.06);kb.data.transform(Matrix.Translation(top+Vector((0,.02,.0))))
        for j,sd in enumerate((-1,1)):
            a=top+Vector((sd*.008,.02,.006));rope(f'YP06_02_Tail{q}{j}',[a,a+Vector((sd*.025,.03,.012)),a+Vector((sd*.045,.065,-.012)),a+Vector((sd*.05,.085,-.045))],.0045,M['straw'],'Body')
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];h=np.zeros(px.shape,np.float32)
        mat=filled*(mid>.5)
        gy=np.clip((_fb(P,4.,6671,3)-.45)*3,0,1)*mat;col=col*(1-.30*gy[...,None])+gy[...,None]*.30*np.array([.46,.43,.36])
        dirt=mat*np.clip((_fb(P,6.,6672,3)-.52)*3,0,1);col=col*(1-.26*dirt[...,None])+dirt[...,None]*.26*np.array([.25,.19,.12])
        under=mat*np.clip((.035-pz)/.035,0,1);col=col*(1-.35*under[...,None]);ms=under*np.clip((noise-.5)*4,0,1);col=col*(1-.4*ms[...,None])+ms[...,None]*.4*np.array([.24,.31,.12])   # damp where it lies on the ground
        end=mat*np.clip((np.abs(px)-L/2+.02)/.02,0,1);col=col*(1-.25*end[...,None])                                                                                     # the cut ends are darker between the turns
        R_['h']=h;return col,rough
    M['mat']['mid']=1.
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.3,'grime':.7,'ao_k':.5,'uv_angle':66,'collision_box':((L,.18,.17),(0,0,.085)),
            'notes':['the mat rolled up: one spiral band 9 mm thick, a little over four turns (the rings show at both ends), flattened a little by its weight; straw ends stick out of both ends and along the loose edge',
                     'two straw ropes, each knotted on top with two loose tails','painted: grey weathered patches, dirt, damp and a little moss underneath']}
PROPS['YP06_02']=YP06_02

# ---------------- YP06_03 round bamboo tray with rice drying in it (cand-4) ----------------
def YP06_03(M):
    """a shallow woven tray 0.80 m across: the woven dish, a rim of two split-bamboo hoops lashed on with rattan at
    sixteen places, two crossed bamboo slats under it (it stands on them), a thin heap of unhusked rice inside."""
    rr=random.Random(6681);RR=.395;Z0=.012;ZR=.074
    o=_lathe('YP06_03_Dish',[(0,.002),(0,.315),(.22,.360),(1,RR),(1,RR-.008),(.30,.352),(.115,.305),(.115,.002)],((0,0,Z0),(0,0,ZR)),M['weave'],'Body',NS=44,scale=.5,loop=True);jitter(o,.0025,6682,freq=9)
    for q,(dz,r) in enumerate(((.000,RR+.002),(-.019,RR-.004))):   # the rim: two hoops of split bamboo, one above the other
        _ring_band(f'YP06_03_Hoop{q}',(0,0,0),r+.008,r-.008,ZR-.010+dz,ZR+.008+dz,M['bamboo_split'],'Body',NS=44,scale=.3)
    for k in range(16):   # rattan lashings round both hoops
        a=math.tau*(k+rr.uniform(-.15,.15))/16;c=Vector((RR*math.cos(a),RR*math.sin(a),ZR-.010));tg=Vector((-math.sin(a),math.cos(a),0))
        for j in range(3):_ring(f'YP06_03_Lash{k}{j}',c+tg*(.007*(j-1)),tg,.0235,.0026,M['cord_dark'],'Detail_Lashings',n=9)
    for q,a in enumerate((.35,.35+math.pi/2)):   # crossed slats under the dish
        d=Vector((math.cos(a),math.sin(a),0));_bar(f'YP06_03_Slat{q}',d*(-RR+.03)+Vector((0,0,.0065+.0002*q)),d*(RR-.03)+Vector((0,0,.0065+.0002*q)),.026,.011,M['bamboo_split'],'Body',up=(0,0,1),bev=.003,seed=6690+q,jit=.0008)
    g=_lathe('YP06_03_Rice',[(0,.330),(.35,.300),(.75,.20),(1,0)],((0,0,Z0+.006),(0,0,Z0+.030)),M['grain'],'Body',NS=40,scale=.4);jitter(g,.005,6695,freq=22)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];pr=np.hypot(px,py);h=np.zeros(px.shape,np.float32)
        rice=filled*(mid>.5)
        d1,d2,cid,_,_=_wor(P,(150.,150.,60.),6696);gr=rice*np.clip(1-d1/.55,0,1);h+=.0016*gr;col=col*(1+.14*rice[...,None])*(1+.08*(rice*(cid-.5))[...,None])   # single grains
        rk=rice*np.clip(1-np.abs(np.sin(px*38+py*9)+.25*np.sin(py*31))/.5,0,1)*np.clip((pr-.04)/.1,0,1);h-=.0018*rk;col=col*(1-.14*rk[...,None])                                           # raked into shallow furrows
        dish=filled*(1-rice)*(pr<RR+.03)
        gy=dish*np.clip((_fb(P,5.,6697,3)-.47)*3,0,1);col=col*(1-.28*gy[...,None])+gy[...,None]*.28*np.array([.44,.41,.35])
        ms=dish*np.clip((_fb(P,9.,6698,3)-.60)*5,0,1)*np.clip((pr-.30)/.06,0,1);col=col*(1-.40*ms[...,None])+ms[...,None]*.40*np.array([.25,.32,.13])
        R_['h']=h;return col,rough
    M['grain']['mid']=1.
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.5,'grime':.7,'uv_angle':66,'collision_box':((.80,.80,.08),(0,0,.04)),
            'notes':['a shallow woven dish (the weave is in the texture and the normal map), a rim of two split-bamboo hoops lashed with rattan at sixteen places (Detail_Lashings), two crossed slats under it',
                     'a thin heap of unhusked rice inside, thinner toward the rim; painted, with the relief also in the normal map: single grains, shallow rake furrows; grey patches and a little moss on the tray']}
PROPS['YP06_03']=YP06_03
