# C 路邊小物（wayside-c）WS03 碎石堆、WS04 疊石小塔. Blender: X = width, -Y = front, Z = up; origin: footprint centre, bottom z = 0.
# Stones are placed the way GC06 (ground-cover-c) places its rocks: each is lowered until it rests on the ground or on a stone
# already there (_drop), and turned until none of its faces lies flush with a neighbour's (_flush).

# _ttube: the same tapering tube as undergrowth-c/ug_items.py (batch B)
def _ttube(name,pts,radii,mat,grp,sides=6,scale=.3,cap0=True,cap1=True,roll=0.):
    """a tapering tube along pts (radius per point), frames carried along the path so it does not twist"""
    pts=[Vector(p) for p in pts];bm=bmesh.new();rings=[];prev=None
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        u=(prev-t*prev.dot(t)).normalized() if prev is not None else (Matrix.Rotation(roll,3,t)@t.orthogonal()).normalized();prev=u;v=t.cross(u)   # roll: parallel tubes side by side do not line up their facets
        rings.append([bm.verts.new(p+(u*math.cos(math.tau*k/sides)+v*math.sin(math.tau*k/sides))*radii[i]) for k in range(sides)])
    for a,b in zip(rings,rings[1:]):
        for k in range(sides):bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
    if cap0:bm.faces.new(list(reversed(rings[0])))
    if cap1:bm.faces.new(rings[-1])
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)

def _settle_one(o,placed,rr,x,y,tilt,tries=10,slide=True,R0=None,rmax=9.):
    """put stone o at (x, y): try turns until it lies flush with nothing; slide off a lone support point (as GC06)"""
    me0=o.data.copy();best=None
    for t in range(tries):
        R=(R0 or Matrix.Identity(4))@Matrix.Rotation(rr.uniform(0,math.tau),4,'Z')@Matrix.Rotation(rr.uniform(-tilt,tilt),4,'X')@Matrix.Rotation(rr.uniform(-tilt,tilt),4,'Y')
        px,py=x,y
        for s in range(24 if slide else 1):
            o.data=me0.copy();o.data.transform(R);o.data.transform(Matrix.Translation((px,py,0)))
            trial={'V':list(placed['V']),'F':list(placed['F'])};sp=_drop(o,trial)
            co=[v.co for v in o.data.vertices];c=sum(co,Vector())/len(co);off=Vector((c.x-sp.x,c.y-sp.y))
            w_=min(max(v.x for v in co)-min(v.x for v in co),max(v.y for v in co)-min(v.y for v in co))
            if not slide or sp.z<.012 or off.length<.18*w_ or math.hypot(px,py)>rmax:break
            px+=off.normalized().x*.015;py+=off.normalized().y*.015
        best=(trial,R)
        if not _flush(o,placed):break
    placed['V'],placed['F']=best[0]['V'],best[0]['F'];return best[1]

def _ground_weeds(pid,M,placed,rr,n,rmin,rmax,sx=1.,sy=1.,grp='Detail_Weeds',hmax=.05,h=(.06,.12)):
    """small grass tufts on the ground between the stones: only where a ray down meets the ground, not a stone"""
    from mathutils.bvhtree import BVHTree
    T=BVHTree.FromPolygons(placed['V'],placed['F']) if placed['F'] else None;k=0
    for i in range(n*4):
        if k>=n:break
        a=rr.uniform(0,math.tau);d=rr.uniform(rmin,rmax);p=Vector((d*math.cos(a)*sx,d*math.sin(a)*sy,0))
        hit=T.ray_cast(p+Vector((0,0,1)),Vector((0,0,-1))) if T else (None,)
        if hit[0] is not None and hit[0].z>hmax:continue
        _tuft_even(f'{pid}_Weed{k:02d}',(hit[0] if hit[0] is not None else p)-Vector((0,0,.003)),M['radish_leaf'],grp,rr,n=rr.randint(3,5),h=rr.uniform(*h));k+=1

def _stone_paint(col,rough,P,onrm,noise,mid,filled,seed,moss_h=.10,dust=.5):
    """grey granite: dust on the up faces, moss and soil low down and in the shade, a few pale fresh breaks"""
    px,py,pz=P[...,0],P[...,1],P[...,2];st=filled*(mid<.5);up=np.clip(onrm[...,2],0,1)
    du=st*up**2*np.clip((_fb(P,(6.,6.,6.),seed,2)-.35)*2.5,0,1)*dust;col=col*(1-.30*du[...,None])+du[...,None]*.30*np.array([.66,.60,.50])
    mo=st*np.clip((moss_h-pz)/moss_h,0,1)*np.clip((_fb(P,(11.,11.,8.),seed+1,2)-.42)*3,0,1)*np.clip(.6-onrm[...,2]*.3,0,1);col=col*(1-.7*mo[...,None])+mo[...,None]*.7*np.array([.22,.28,.12])
    so=st*np.clip((.03-pz)/.03,0,1);col=col*(1-.4*so[...,None])+so[...,None]*.4*np.array([.24,.19,.14])
    fr=st*np.clip((_vn(P,(4.,4.,4.),seed+2)-.80)*6,0,1)*up;col=col*(1-.35*fr[...,None])+fr[...,None]*.35*np.array([.70,.68,.62])
    rough=np.clip(rough+.06*du-.05*mo,0,1);return col,rough,mo

# ---------------- WS03 roadside heap of broken stone (cand-2) ----------------
def WS03(M):
    """angular grey granite left from mending the road: a few head-sized pieces first, fist-sized ones dropped on and between
    them, each lowered until it rests on the ground or on a stone already there; chips and gravel spilling round the foot
    (Detail_Gravel), a few weeds in the gaps (Detail_Weeds)"""
    rr=random.Random(int(__import__('os').environ.get('WS_SEED',9301)));placed={'V':[],'F':[]}
    ST=[(.30,.24,.20,.00,.02),(.28,.22,.17,-.24,-.06),(.26,.22,.16,.26,.04),(.24,.18,.15,-.06,-.20),(.22,.20,.14,.08,.20),(.22,.17,.13,-.34,.14),
        (.20,.16,.13,.38,-.12),(.18,.15,.12,-.42,-.10),(.18,.14,.11,.18,-.18),(.17,.14,.12,-.16,.14),(.15,.12,.10,.04,.02),(.15,.13,.10,.30,.20),
        (.14,.11,.10,-.30,-.24),(.13,.11,.09,.46,.06),(.13,.10,.09,-.48,.06),(.12,.10,.09,.12,-.30),(.12,.10,.08,-.10,.30),(.11,.09,.08,.24,-.30),
        (.11,.09,.08,-.04,-.06),(.10,.09,.08,.20,.06),(.10,.08,.07,-.22,.02),(.10,.08,.07,.36,.28),(.09,.08,.07,-.38,-.30),(.09,.07,.06,.52,-.18)]
    for k,(a,b,c,x,y) in enumerate(ST):
        o,br=_shard(f'WS03_Stone{k:02d}',(a,b,c),9310+k,M['stone'],'Body',npts=rr.randint(20,30),flat=0.,bev=0)
        _settle_one(o,placed,rr,x*.80,y*.72,.05 if k<5 else .18,rmax=.30)
    for k in range(70):   # chips and gravel at the foot (Detail_Gravel)
        sz=(rr.uniform(.025,.055),rr.uniform(.02,.04),rr.uniform(.014,.03));o,_=_shard(f'WS03_Chip{k:02d}',sz,9400+k,M['stone'],'Detail_Gravel',npts=10,bev=0,ripple=0.,flat=0.);me0=o.data.copy()
        for t in range(14):
            a=rr.uniform(0,math.tau);d=rr.uniform(.28,.50)
            o.data=me0.copy();o.data.transform(Matrix.Rotation(rr.uniform(0,math.tau),4,'Z')@Matrix.Rotation(rr.uniform(-.5,.5),4,'X'));o.data.transform(Matrix.Translation((d*math.cos(a),d*.78*math.sin(a),0)))
            trial={'V':list(placed['V']),'F':list(placed['F'])};_drop(o,trial)
            if max(v.co.z for v in o.data.vertices)<.08 and not _flush(o,placed):break
        placed['V'],placed['F']=trial['V'],trial['F']
    _ground_weeds('WS03',M,placed,rr,8,.24,.46,1.,.8)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);col,rough,mo=_stone_paint(col,rough,P,onrm,noise,mid,filled,9390)
        h=-.0012*filled*np.clip((_vn(P,(30.,30.,30.),9391)-.75)*5,0,1);R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.5,'grime':.8,'ao_k':.5,'uv_angle':50,
            'notes':['24 angular granite pieces from head-sized to fist-sized, each lowered until it rests on the ground or on a stone already there, turned so no face lies flush with a neighbour (the GC06 method)',
                     'Detail_Gravel (70 chips at the foot) and Detail_Weeds (8 grass tufts in the gaps) are off at the standard tier',
                     'painted, with small pits in the normal map: dust on the up faces, moss and soil low down, a few pale fresh breaks; the paving slab of the three-view is left out',
                     'no collision in the model (it is low enough to step over); add a box from body_dimensions if the scene needs one']}
PROPS['WS03']=WS03

# ---------------- WS04 cairns of three and five stones (cand-4) ----------------
def _cairn(pid,M,sizes,seed):
    """flat rounded river stones stacked big to small, each lowered onto the one below, a little off centre and tilted (the
    stack leans, but every stone's centre stays over the one under it); a few grass tufts round the foot (Detail_Weeds)"""
    rr=random.Random(seed);placed={'V':[],'F':[]};cx=cy=0.;lean=Vector((rr.uniform(-1,1),rr.uniform(-1,1),0)).normalized()
    for k,(a,b,c) in enumerate(sizes):
        o=_blob(f'{pid}_Stone{k}',(a,b,c),seed+10+k,M['stone'] if k%2==0 else M['field'] if 'field' in M else M['stone'],'Body',flats=3,amp=.12,bumps=7,bottom=.40)
        if k:cx+=lean.x*a*.12+rr.uniform(-.015,.015);cy+=lean.y*a*.12+rr.uniform(-.015,.015)
        _settle_one(o,placed,rr,cx,cy,.10+.03*k,slide=False)
    _ground_weeds(pid,M,placed,rr,4,sizes[0][0]*.52,sizes[0][0]*.75)
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2]
        st=filled*(mid<.5);hue=np.clip((_fb(P,(3.,3.,3.),seed+1,1)-.5)*3,-1,1)   # some stones warmer brown, some greyer
        col=col*(1+st[...,None]*hue[...,None]*np.array([.10,.03,-.08]))
        col,rough,mo=_stone_paint(col,rough,P,onrm,noise,mid,filled,seed+2,moss_h=.14,dust=.3)
        R_['h']=-.0008*filled*np.clip((_vn(P,(40.,40.,40.),seed+3)-.78)*5,0,1);return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.4,'grime':.6,'ao_k':.5,'uv_angle':50,
            'notes':[f'{len(sizes)} flat rounded river stones stacked big to small, each lowered onto the one below and turned so their faces never lie flush; a little off centre and tilted, the centre of each over the stone under it',
                     'Detail_Weeds (4 grass tufts round the foot) is off at the standard tier; painted: warmer and greyer stones, dust on top, moss low down; the paving slab of the three-view is left out',
                     'no collision in the model; add a box from body_dimensions if the scene needs one']}
def WS04_01(M):return _cairn('WS04_01',M,[(.30,.26,.13),(.22,.19,.10),(.15,.13,.085)],9411)
def WS04_02(M):return _cairn('WS04_02',M,[(.34,.30,.14),(.28,.24,.115),(.22,.19,.095),(.17,.15,.08),(.12,.10,.065)],9421)
PROPS['WS04_01']=WS04_01;PROPS['WS04_02']=WS04_02
