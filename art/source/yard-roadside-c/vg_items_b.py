# VG05–VG08 shapes (the 11/11 36h pack, batch B: roadside pieces), read by build_vg.py after vg_items.py (same namespace).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _bar(name,a,b,w,h,mat,grp,up=(0,0,1),bev=.004,segs=1,jit=.0008,seed=1,ends=(1.,1.),scale=None):
    """a squared timber from a to b: w across, h along `up`; ends = section scale at a and at b (a tapered spoke)"""
    a,b=Vector(a),Vector(b);d=b-a;L=d.length;x=d.normalized();z=Vector(up);z=(z-x*z.dot(x)).normalized();y=z.cross(x)
    bm=box_bm((L,w,h))
    for v in bm.verts:
        s=ends[0] if v.co.x<0 else ends[1];v.co.y*=s;v.co.z*=s
    o=finish(name,bm,mat,grp) if scale is None else finish(name,bm,mat,grp,scale)
    if bev:bevel(o,bev,segs)
    if jit:jitter(o,jit,seed,freq=9)
    R=Matrix((x,y,z)).transposed().to_4x4();o.data.transform(R);o.data.transform(Matrix.Translation((a+b)/2));return o
def _beam(name,st,mat,grp,up=(0,0,1),jit=.0008,seed=1):
    """a hewn timber through stations st = [(point, w, h, chamfer)]: a chamfered rectangle that can thin and round
    into a handle (chamfer ≈ 0.29 w gives an octagon)"""
    P=[Vector(s[0]) for s in st];bm=bmesh.new();R_=[]
    for i,(p,w,h,c) in enumerate(st):
        t=(P[min(i+1,len(P)-1)]-P[max(i-1,0)]).normalized();z=Vector(up);z=(z-t*z.dot(t)).normalized();y=z.cross(t)
        sec=[(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),(w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c),(-w/2+c,-h/2)]
        R_.append([bm.verts.new(P[i]+y*u+z*v) for u,v in sec])
    for a,b in zip(R_,R_[1:]):
        for k in range(8):bm.faces.new((a[k],a[(k+1)%8],b[(k+1)%8],b[k]))
    bm.faces.new(list(reversed(R_[0])));bm.faces.new(R_[-1])
    o=finish(name,bm,mat,grp)
    if jit:jitter(o,jit,seed,freq=7)
    return o
def _arcblock(name,c,a0,a1,ri,ro,y0,y1,mat,grp,n=8,bev=.004):
    """a curved block in the X–Z plane round c (a wheel felloe): angles a0..a1, radii ri..ro, from y0 to y1"""
    c=Vector(c);bm=bmesh.new();R_=[]
    for a in np.linspace(a0,a1,n):
        e=Vector((math.cos(a),0,math.sin(a)));R_.append([bm.verts.new(c+e*r+Vector((0,y,0))) for r,y in ((ri,y0),(ro,y0),(ro,y1),(ri,y1))])
    for a,b in zip(R_,R_[1:]):
        for k in range(4):bm.faces.new((a[k],a[(k+1)%4],b[(k+1)%4],b[k]))
    bm.faces.new(list(reversed(R_[0])));bm.faces.new(R_[-1])
    o=finish(name,bm,mat,grp)
    if bev:bevel(o,bev,1)
    return o

# ---------------- VG05 two-wheeled handcart, intact and empty (cand-3) ----------------
def VG05(M):
    """two long beams run the whole length and thin into the handles; four cross beams tenoned through them (the tenon
    ends show); a bed of six planks; low rails: posts let into the beams, a side board and a top rail through the posts;
    two wheels: hub, twelve spokes, six felloes, an iron tyre with rivets, on an axle held by two blocks under the beams;
    a prop leg with two braces under the front cross beam. Intact and empty (not the overturned wreck A2_OverturnedCart)."""
    rr=random.Random(5501);W1,W2,DK,IR,HP=M['cedar_b'],M['cedar'],M['hardwood'],M['iron'],M['hemp']
    BY=.30;BZ=.47;XA=.30;RW=.36;YW=.445    # beam offset and height, axle position, wheel radius, wheel plane
    # the two long beams, thinning and rounding into the handles
    for s in (-1,1):
        st=[((1.05,s*BY,BZ),.070,.080,.008),((.3,s*BY,BZ),.070,.080,.008),((-.36,s*BY,BZ),.070,.080,.008),((-.50,s*BY,BZ-.004),.058,.064,.013),
            ((-.64,s*BY,BZ-.008),.050,.050,.0146),((-.86,s*BY,BZ-.014),.046,.046,.0135),((-1.035,s*BY,BZ-.02),.047,.047,.0138),((-1.07,s*BY,BZ-.021),.034,.034,.010)]
        _beam(f'VG05_Beam{"LR"[s>0]}',st,W1,'Body',seed=5510+s)
    # cross beams, tenoned through the long beams
    for k,x in enumerate((-.45,.02,.60,1.0)):
        _bar(f'VG05_Cross{k}',(x,-.376-.004*k,BZ+.0195),(x,.376+.004*k,BZ+.0195),.052,.048,W2,'Body',seed=5520+k)
    # the bed: six planks along the cart, each its own width, length and thickness
    ws=[.118,.124,.112,.121,.115,.126];tot=sum(ws)+.003*5;y=-tot/2
    for k,w in enumerate(ws):
        th=.026+.003*((k*3)%4);x0=-.33-rr.uniform(0,.018);x1=1.068-rr.uniform(0,.016)
        _bar(f'VG05_Plank{k}',(x0,y+w/2,BZ+.038+th/2),(x1,y+w/2,BZ+.038+th/2),w,th,W2 if k%2 else W1,'Body',bev=.003,jit=.0012,seed=5530+k);y+=w+.003
    # low rails: posts let into the beams, a board inside them, a top rail through them
    PX=(-.28,.40,1.02);PY=.33
    for s in (-1,1):
        for k,x in enumerate(PX):
            top=.93-.02*(k==1);_bar(f'VG05_Post{"LR"[s>0]}{k}',(x,s*PY,.445),(x,s*PY,top),.045,.045,W1,'Body',up=(1,0,0),seed=5540+k+4*s)
        _bar(f'VG05_SideBoard{"LR"[s>0]}',(-.315,s*.2975,.598),(1.045,s*.2975,.598),.020,.114,W2,'Body',up=(0,0,1),bev=.003,seed=5550+s)
        _bar(f'VG05_TopRail{"LR"[s>0]}',(-.335,s*PY,.848),(1.072,s*PY,.848),.030,.050,W2,'Body',seed=5552+s)
    _bar('VG05_BackBoard',(.9875,-.2872,.592),(.9875,.2872,.592),.020,.100,W1,'Body',bev=.003,seed=5556)
    _bar('VG05_BackRail',(1.02,-.388,.775),(1.02,.388,.775),.030,.046,W2,'Body',seed=5557)
    for s in (-1,1):   # the rear posts are bound to the top rail with cord
        for q in range(3):_ring(f'VG05_Tie{"LR"[s>0]}{q}',(1.02,s*PY,.888+.0105*q),(0,0,1),.0305,.0048,HP,'Body',n=12)
    # the axle and its two blocks under the beams
    _rod('VG05_Axle',(XA,-.548,RW),(XA,.548,RW),.027,DK,'Body',sides=12,scale=.2)
    for s in (-1,1):
        _bar(f'VG05_AxleBlock{"LR"[s>0]}',(XA-.10,s*BY,.378),(XA+.10,s*BY,.378),.074,.104,W1,'Body',seed=5560+s)
        _rod(f'VG05_Linchpin{"LR"[s>0]}',(XA,s*.540,RW-.045),(XA,s*.540,RW+.05),.0065,IR,'Body',sides=6,scale=.05)
    # the wheels
    def wheel(tag,s,ph):
        c=Vector((XA,s*YW,RW));Y=Vector((0,1,0))
        _lathe(f'VG05_Hub{tag}',[(0,.046),(.03,.060),(.30,.079),(.5,.083),(.70,.079),(.97,.060),(1,.046)],(c-Y*.088,c+Y*.088),DK,'Body',NS=16,scale=.2)
        for q,yy in enumerate((-.066,.066)):_lathe(f'VG05_HubBand{tag}{q}',[(0,.0705),(1,.0705),(1,.060),(0,.060)],(c+Y*(yy-.011),c+Y*(yy+.011)),IR,'Body',NS=16,scale=.1,loop=True)
        for k in range(12):
            a=ph+math.tau*k/12;e=Vector((math.cos(a),0,math.sin(a)))
            _bar(f'VG05_Spoke{tag}{k:02d}',c+e*.062,c+e*.308,.040,.036,W2,'Body',up=(0,1,0),bev=.003,jit=.0006,seed=5570+k,ends=(1.,.78))
        for k in range(6):
            a0=ph+math.tau*(k-.5)/6+.007;a1=ph+math.tau*(k+.5)/6-.007
            _arcblock(f'VG05_Felloe{tag}{k}',c,a0,a1,.298,.3452,-.0275,.0275,W1 if k%2 else W2,'Body',n=9)
        _lathe(f'VG05_Tyre{tag}',[(0,RW),(1,RW),(1,.3445),(0,.3445)],(c-Y*.031,c+Y*.031),IR,'Body',NS=48,scale=.2,loop=True)
        for k in range(12):   # rivet heads on the outer face of the felloes
            a=ph+math.tau*(k+.5)/12;p=c+Vector((math.cos(a),0,math.sin(a)))*.324+Y*s*.0265
            _lathe(f'VG05_Rivet{tag}{k:02d}',[(0,.0095),(.55,.0080),(1,0)],(p,p+Y*s*.0075),IR,'Body',NS=6,scale=.05)
    wheel('L',-1,.17);wheel('R',1,.43)
    # the prop leg under the front cross beam, two braces, a cord binding
    _bar('VG05_Leg',(-.45,0,0),(-.45,0,BZ+.01),.056,.056,W1,'Body',up=(1,0,0),seed=5580)
    for s in (-1,1):_bar(f'VG05_Brace{"LR"[s>0]}',(-.45,s*.012,.20),(-.45,s*.225,BZ-.012),.032,.030,W2,'Body',up=(1,0,0),bev=.003,seed=5582+s)
    for q in range(3):_ring(f'VG05_LegTie{q}',(-.45,0,.270+.011*q),(0,0,1),.041,.005,HP,'Body',n=12)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];pz=P[...,2]
        mud=filled*np.clip((.13-pz)/.12,0,1)*np.clip(.3+noise,0,1)     # road mud on the tyres and the leg's foot
        col=col*(1-.55*mud[...,None])+mud[...,None]*.55*np.array([.30,.23,.16]);rough=np.clip(rough+.1*mud,0,1)
        top=filled*np.clip(onrm[...,2],0,1)*np.clip((pz-.48)/.05,0,1)*np.clip(.4+noise,0,1)   # the bed and rail tops: sun-greyed, worn pale
        g=col.mean(2,keepdims=True);col=col*(1-.30*top[...,None])+top[...,None]*.30*(g*np.array([1.10,1.06,.98])+.04)
        grip=filled*np.clip((-.62-P[...,0])/.2,0,1)*(np.abs(P[...,1])>.2)                    # the handles: polished by hands
        col=col*(1+.14*grip[...,None]);rough=np.clip(rough-.18*grip,0,1)
        ms=filled*np.clip((cav-.5)*2.2,0,1)*np.clip((noise-.5)*3,0,1)*np.clip((.75-pz)/.5,0,1)   # a little moss in the low joints
        col=col*(1-.35*ms[...,None])+ms[...,None]*.35*np.array([.22,.30,.11])
        return col,rough
    return {'paint':paint,'wear':.9,'grime':.7,'uv_angle':50,'collision_box':((1.44,1.10,.90),(.36,0,.45)),
            'notes':['two long beams run the whole length and thin into the handles; four cross beams pass through them (tenon ends show); the bed is six separate planks',
                     'wheels: a turned hub with two iron bands, twelve tapered spokes, six felloes, an iron tyre and rivet heads; the axle runs through two blocks under the beams, a linchpin outside each hub',
                     'low rails: posts let into the beams, a side board, a top rail through the posts; a prop leg with two braces keeps the bed level',
                     'intact and empty; the collision box covers the bed and wheels, not the handles']}
PROPS['VG05']=VG05

# ---------------- VG06 carrying pole and two baskets, set down (cand-1) ----------------
def VG06(M):
    """two round baskets stand on the ground, the flat pole lies across their rims with its cords slack. The weave is
    in the texture; modelled: the rim hoop and its bindings, two split-bamboo strips crossing under each bottom and
    running up the sides, four cords per basket gathered round the pole, a peg near each end of the pole."""
    rr=random.Random(5601);WV,SP_,OLD,HP=M['weave'],M['bamboo_split'],M['bamboo_old'],M['hemp']
    PR=[(.0,0.),(.06,0.),(.112,0.),(.150,.012),(.184,.060),(.205,.140),(.216,.235),(.221,.325)];ZR=.325;ZP=ZR+.0105+.0125;XC=.62
    def basket(tag,xc,rot,k):
        c=Vector((xc,0,.0045));prof=[(r*k,z) for r,z in PR[2:]]
        o=_shell(f'VG06_Basket{tag}',prof,.008,36,WV,'Body',scale=.22);o.data.transform(Matrix.Rotation(rot,4,'Z'));o.data.transform(Matrix.Translation(c))
        _hoop2(f'VG06_Rim{tag}',[c+Vector(((PR[-1][0]*k+.002)*math.cos(t),(PR[-1][0]*k+.002)*math.sin(t),ZR)) for t in np.linspace(0,math.tau,40,endpoint=False)],.0105,OLD,'Body',sides=6,phase=0.)
        for q in range(8):   # the rim is bound to the basket wall every eighth of the way round
            a=rot+math.tau*(q+.5)/8;p=c+Vector(((PR[-1][0]*k+.002)*math.cos(a),(PR[-1][0]*k+.002)*math.sin(a),ZR))
            _ring(f'VG06_RimTie{tag}{q}',p,(-math.sin(a),math.cos(a),.38),.0150,.0026,HP,'Body',n=9)
        P2=[(-r*k,z) for r,z in reversed(PR[1:])]+[(0.,0.)]+[(r*k,z) for r,z in PR[1:]]
        for j,th in enumerate((rot+.3,rot+.3+math.pi/2)):   # two strips cross under the bottom and run up to the rim
            e=Vector((math.cos(th),math.sin(th),0));path=[];N_=[]
            for i,(ro,z) in enumerate(P2):
                a_,b_=P2[max(i-1,0)],P2[min(i+1,len(P2)-1)];t=Vector((b_[0]-a_[0],b_[1]-a_[1])).normalized();n2=Vector((t.y,-t.x))
                low=max(0.,1-abs(ro)/.13);off=.0012+(.0046*low if j else 0.)
                n3=e*n2.x+Vector((0,0,n2.y));path.append(c+e*ro+Vector((0,0,z))+n3*off);N_.append(n3)
            path[0].z-=.004;path[-1].z-=.004
            _strip(f'VG06_Strip{tag}{j}',path,lambda i,N_=N_:N_[i],.024,.0036,SP_,'Body',scale=.2)
        # four cords from the rim, slack, gathered round the pole above the basket's middle
        for q in range(4):
            a=rot+math.pi/4+math.tau*q/4;e=Vector((math.cos(a),math.sin(a),0));R_=PR[-1][0]*k;sy=1 if e.y>0 else -1
            top=Vector((xc+.012*(q-1.5),sy*.030,ZP+.004))
            pts=[c+e*(R_+.016)+Vector((0,0,ZR-.022)),c+e*(R_+.0165)+Vector((0,0,ZR+.004)),c+e*(R_+.002)+Vector((0,0,ZR+.0165)),c+e*(R_*.80)+Vector((0,0,ZR+.004)),
                 c+e*(R_*.52)+Vector((0,0,ZR-.022-.01*(q%2))),Vector((top.x+e.x*.03,sy*.070,ZR-.008)),top+Vector((0,sy*.006,-.004)),Vector((top.x,sy*.004,ZP+.0215))]
            tube(f'VG06_Cord{tag}{q}',_spline(pts,3),.0042,HP,'Body',sides=5,scale=.05)
        for q in range(3):   # the wrap round the pole
            x=xc+.013*(q-1);loop=K.round_loop([(x,-.0315,ZP-.0165),(x,.0315,ZP-.0165),(x+.004,.0315,ZP+.0165),(x+.004,-.0315,ZP+.0165)],.009,n=3)[:-2]
            tube(f'VG06_Wrap{tag}{q}',loop,.0042,HP,'Body',sides=5,scale=.05)
    basket('L',-XC,.4,1.0);basket('R',XC,2.1,.965)
    # the flat pole across the rims: widest and thickest in the middle, ends thinner and a little upturned
    st=[]
    for x in (-.878,-.862,-.74,-.45,-.15,.15,.45,.74,.862,.878):
        u=abs(x)/.878;w=.060-.014*u*u;h=.025-.004*u*u;end=abs(x)>.87
        st.append(((x,0,ZP+.016*max(0,u-.74)**1.5/.05**.5*.25),w*(.72 if end else 1),h*(.7 if end else 1),.0075*(.7 if end else 1)))
    _beam('VG06_Pole',st,OLD,'Body',jit=.0006,seed=5610)
    for s in (-1,1):_rod(f'VG06_Peg{"LR"[s>0]}',(s*.705,0,ZP-.020),(s*.705,.002,ZP+.030),.0062,M['cedar_b'],'Body',sides=7,scale=.05)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        pole=filled*(pz>ZP-.014)*(np.abs(py)<.031)*(onrm[...,2]>-.5)
        shine=pole*np.clip(1-np.abs(px)/.30,0,1)                          # the middle of the pole: polished by the shoulder
        col=col*(1+.22*shine[...,None])+shine[...,None]*np.array([.05,.035,.01]);rough=np.clip(rough-.30*shine,0,1)
        node=pole*np.clip(1-np.abs(np.abs(px)-.50)/.006,0,1);node2=pole*np.clip(1-np.abs(np.abs(px)-.80)/.006,0,1)   # bamboo nodes
        col=col*(1-.45*np.maximum(node,node2)[...,None])
        low=filled*np.clip((.10-pz)/.09,0,1)*np.clip(.35+noise,0,1)       # the basket bottoms: damp and soiled from standing on the ground
        col=col*(1-.40*low[...,None])+low[...,None]*.40*np.array([.20,.19,.11])
        ms=filled*np.clip((.16-pz)/.12,0,1)*np.clip((noise-.55)*4,0,1);col=col*(1-.4*ms[...,None])+ms[...,None]*.4*np.array([.22,.30,.11])
        return col,rough
    return {'paint':paint,'wear':.7,'grime':.7,'uv_angle':50,'collision':'none in the model',
            'notes':['set down: the baskets stand on the ground, the pole lies across both rims and the cords hang slack',
                     'the weave is in the texture (the wall is a plain bowl with thickness); modelled: rim hoop with eight bindings, two split-bamboo strips crossing under the bottom, four cords per basket, the wraps round the pole, two pegs',
                     'the middle of the pole is painted paler and smoother (polished by the shoulder); bamboo nodes are painted']}
PROPS['VG06']=VG06
