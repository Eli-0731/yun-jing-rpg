# C 路邊小物（wayside-c）WS06 柴捆. Blender: X = width, -Y = front, Z = up; origin: footprint centre, bottom z = 0.

def _pack_disc(R,rr,radii,overlap=-.0004,tries=4000):
    """stick centres in a disc of radius R, the sticks just touching: 0.4 mm apart (sticks that run into each other side by side put their facets
    in one plane: coplanar in the QA), none left floating with a wider gap"""
    C=[]
    for r in radii:
        best=None
        for t in range(tries):
            a=rr.uniform(0,math.tau);d=(R-r)*math.sqrt(rr.random());p=(d*math.cos(a),d*math.sin(a))
            ok=all(math.hypot(p[0]-q[0],p[1]-q[1])>=r+s-overlap for q,s in C)
            if ok:
                touch=min([math.hypot(p[0]-q[0],p[1]-q[1])-(r+s) for q,s in C]+[R-r-d])   # prefer the place closest to a neighbour or the rim: a tight bundle
                if best is None or touch<best[0]:best=(touch,p)
                if touch<.002 and t>40:break
        if best:C.append((best[1],r))
    for i,(p,r) in enumerate(C):   # a stick left with a gap all round grows until it touches its nearest neighbour (none floats inside the bundle)
        g=min([math.hypot(p[0]-q[0],p[1]-q[1])-(r+s) for j,(q,s) in enumerate(C) if j!=i]+[R-math.hypot(*p)-r])
        if g>.0008:C[i]=(p,min(r*1.5,r+g-.0004))
    return C

def _bundle(pid,k,M,rr,L,R,ctr,nstick,grp='Body'):
    """one bundle of brushwood: sticks of mixed thickness along X packed in a disc of radius R, each a little bent and of its
    own length, a few split ones (three-sided wedges, pale), forked twigs sticking out at the ends, two twisted straw ropes"""
    radii=sorted([rr.choice((rr.uniform(.010,.016),rr.uniform(.016,.026),rr.uniform(.026,.038))) for _ in range(nstick)],reverse=True)
    C=_pack_disc(R,rr,radii);out=0.;cx,cy,cz=ctr;BW=rr.uniform(-.012,.012);BZ=rr.uniform(-.008,.0)
    for i,((y,z),r) in enumerate(C):
        x0=-L/2+rr.uniform(-.05,.06);x1=L/2+rr.uniform(-.06,.05);split=r>.016 and rr.random()<.22
        n=6;bw=BW;bz=BZ   # the bundle bows as one (sticks bent on their own opened gaps between them mid-length)
        pts=[(cx+x0+(x1-x0)*j/n,cy+y+bw*math.sin(math.pi*j/n),cz+z+bz*math.sin(math.pi*j/n)) for j in range(n+1)]
        if split:_ttube(f'{pid}_B{k}S{i:02d}',pts,[r*1.15]*len(pts),M['hardwood'],grp,sides=3,scale=.25,roll=rr.uniform(0,6.28))
        else:_ttube(f'{pid}_B{k}S{i:02d}',pts,[r*(1-.04*j/n) for j in range(n+1)],M['twig'] if r<.014 else M['bark'],grp,sides=7 if r>.014 else 5,scale=.25,roll=rr.uniform(0,6.28))
        out=max(out,math.hypot(y,z)+r)
        if r<.016 and math.hypot(y,z)>R*.45 and rr.random()<.35:   # a forked twig running on past the bundle end
            s=1 if rr.random()<.5 else -1;e=Vector(pts[-1] if s>0 else pts[0]);d=Vector((s,y*2.5,z*2.5+.3)).normalized()
            Lt=rr.uniform(.07,.15);tw=[e-d*.01,e+d*Lt*.5,e+d*Lt+Vector((0,0,.02))]
            _ttube(f'{pid}_B{k}T{i:02d}',tw,[r*.55,r*.38,r*.2],M['twig'],grp,sides=4,scale=.12)
    for q,xr in enumerate((-.26,.24)):   # two twisted straw ropes biting into the outer sticks; the loop rides past its start
        x=cx+xr*L+rr.uniform(-.03,.03);rp=.0090;rad=out+rp*.35;N=26;ph=rr.uniform(0,6.28)
        path=[(x+(.022*i/N),cy+rad*math.cos(ph+math.tau*1.12*i/N),cz+rad*math.sin(ph+math.tau*1.12*i/N)) for i in range(N+1)]
        rope(f'{pid}_B{k}Rope{q}',path,rp,M['straw'],grp,plies=3,sides=5)
        kn=Vector(path[-1]);tail=[kn,kn+Vector((.02,.0,.03)),kn+Vector((.035,.01,.07))]   # a short tail where it is knotted
        _ttube(f'{pid}_B{k}Knot{q}',tail,[rp*1.2,rp*.9,rp*.6],M['straw'],grp,sides=5,scale=.1)
    return out

def WS06(M):
    """two bundles of firewood, one lying on the other: dry brushwood sticks and split branches of mixed thickness, each bundle
    tied with two loops of twisted straw rope; forked twigs stick out at the ends; a few loose twigs on the ground (Detail_Twigs)"""
    rr=random.Random(int(__import__('os').environ.get('WS_SEED',9604)));L=.98;R=.125
    o1=_bundle('WS06',0,M,rr,L,R,(0,0,R-.004),28)
    o2=_bundle('WS06',1,M,rr,L*.94,R*.95,(.03,.012,R-.004+o1+R*.95-.018),25)   # the top bundle rests in the groove of the lower one's sticks
    zg=min((o.matrix_world@v.co).z for o in parts for v in o.data.vertices)   # the ground is where the lower bundle's lowest stick lies
    for i in range(6):   # loose twigs on the ground
        for t in range(40):   # on the ground beside the bundles, never under them
            a=math.tau*(i+rr.uniform(.15,.85))/6;d=rr.uniform(.22,.34);p=Vector((d*math.cos(a)*1.45,d*math.sin(a)*.62,zg))   # one twig to each sixth of the way round: they never cross
            h=rr.uniform(0,6.28);Lt=rr.uniform(.12,.24);r=rr.uniform(.004,.007);e=p+Vector((math.cos(h),math.sin(h),0))*Lt
            if all(abs(q.y)>.19 or abs(q.x)>.60 for q in (p,e,(p+e)/2)):break
        dv=Vector((math.cos(h),math.sin(h),0));sd=Vector((-dv.y,dv.x,0))
        pts=[p+dv*Lt*j/4+sd*.01*math.sin(j*1.3)+Vector((0,0,r*.92)) for j in range(5)]
        _ttube(f'WS06_Twig{i}',pts,[r*(1-.4*j/4) for j in range(5)],M['twig'],'Detail_Twigs',sides=4,scale=.12)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];h=np.zeros(px.shape,np.float32)
        wood=filled*(col[...,0]>col[...,2]*1.05)
        end=wood*np.clip((np.abs(onrm[...,0])-.75)*6,0,1)   # sawn and broken ends: pale wood with growth rings and a darker rim
        rings=.5+.5*np.sin(np.hypot(py*np.sign(py),pz)*900+_fb(P,(30.,30.,30.),9611,1)*6);ec=np.array([.72,.60,.42])*(.86+.14*rings[...,None])
        col=col*(1-end[...,None])+end[...,None]*ec;h-=.0006*end*rings
        gry=wood*(1-end)*np.clip((_fb(P,(4.,6.,6.),9612,2)-.5)*3,0,1);col=col*(1-.30*gry[...,None])+gry[...,None]*.30*np.array([.50,.47,.42])   # weathered grey sticks among brown ones
        li=wood*(1-end)*np.clip((_fb(P,(16.,16.,16.),9613,2)-.70)*5,0,1);col=col*(1-.4*li[...,None])+li[...,None]*.4*np.array([.55,.60,.42])   # a little lichen
        R_['h']=h;return col,rough
    for k in ('hardwood',):M[k]['mid']=0.
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.5,'grime':.6,'ao_k':.5,'uv_angle':55,
            'collision_box':((L,.26,.47),(0,0,.235)),'collision':'one box round both bundles',
            'notes':['two bundles of firewood, one lying in the groove of the other: 28 and 25 sticks of mixed thickness packed so each touches a neighbour, each a little bent and of its own length; about one in five of the thick ones is a split three-sided wedge',
                     'forked twigs run on past the bundle ends; each bundle is tied with two loops of three-ply twisted straw rope that bite into the outer sticks, with a short knotted tail',
                     'painted, with the rings also in the normal map: pale sawn ends with growth rings, weathered grey sticks among brown ones, a little lichen; Detail_Twigs (6 loose twigs on the ground) is off at the standard tier; the paving slab of the three-view is left out']}
PROPS['WS06']=WS06
