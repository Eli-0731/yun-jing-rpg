# FI01–FI05 shapes, read by build_wl.py (exec'd into its namespace: M = source materials, helpers from wl_kit and wl_items).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = length, -Y = front, Z = up.

def _cane(name,pts,radii,mat,grp,nodes=(),sides=10,node_bulge=.2,node_len=.012):
    """a bamboo cane along a polyline: radius per point, small raised rings at the node positions (arc length in m)"""
    P=[Vector(p) for p in pts];L=[0.]
    for a,b in zip(P,P[1:]):L.append(L[-1]+(b-a).length)
    dense=[];rad=[]
    for i in range(len(P)-1):
        n=max(2,int((L[i+1]-L[i])/.012))
        for k in range(n):
            t=k/n;s=L[i]+(L[i+1]-L[i])*t;r=radii[i]+(radii[i+1]-radii[i])*t
            for nd in nodes:   # node ring: a soft bump over about 1.2 cm
                d=abs(s-nd)
                if d<node_len:r*=1+node_bulge*(.5+.5*math.cos(math.pi*d/node_len))
            dense.append(P[i].lerp(P[i+1],t));rad.append(r)
    dense.append(P[-1]);rad.append(radii[-1])
    bm=bmesh.new();rings=[];prev=None
    for i,p in enumerate(dense):
        t=(dense[min(i+1,len(dense)-1)]-dense[max(i-1,0)]).normalized()
        u=(prev-t*prev.dot(t)).normalized() if prev is not None else t.orthogonal().normalized();prev=u;v=t.cross(u)
        rings.append([bm.verts.new(p+(u*math.cos(math.tau*k/sides)+v*math.sin(math.tau*k/sides))*rad[i]) for k in range(sides)])
    for a,b in zip(rings,rings[1:]):
        for k in range(sides):bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
    for ring,rev in ((rings[0],True),(rings[-1],False)):bm.faces.new(list(reversed(ring)) if rev else ring)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,.3)

# ---------------- FI01 slender bamboo fishing pole, stored (cand-2) ----------------
def FI01(M):
    """a 2.2 m jointed cane lying on the ground: polished wooden grip sleeve, the cane tapering node by node, the last
    35 cm bent to one side; a split-cane splint lashed over an old crack; the line run down the cane through two cord
    guides and wound on a small stick winder above the grip (stored, no hook or bait)"""
    Lp=2.2;r0,r1=.0145,.0042
    def R(x):return r0+(r1-r0)*(x/Lp)**1.15
    xs=list(np.linspace(.20,Lp-.36,24))+list(np.linspace(Lp-.34,Lp,9))
    def C(x):   # centreline: resting on the ground (z = radius) and the tip bending to +Y
        b=max(0,(x-(Lp-.36))/.36);return Vector((x-.08*b*b,.11*b*b,R(x)+.0006))
    pts=[C(x) for x in xs];rad=[R(x) for x in xs]
    nodes=[.20+s for s in np.cumsum([.27,.26,.25,.23,.22,.21,.19,.18,.16,.14])]
    _cane('FI01_Cane',pts,rad,M['bamboo'],'Body',nodes=[n-.20 for n in nodes],sides=10)
    # grip sleeve: polished wood, barrel-shaped, over the butt
    gx=np.linspace(0,.24,13);gr=[.016+.006*math.sin(math.pi*min(1,x/.24))**.7 for x in gx];gr[0]=.017;gr[-1]=.0155
    tube('FI01_Grip',[Vector((x,0,max(gr)+.0006)) for x in gx],.02,M['cedar'],'Body',sides=12,scale=.2)
    g=parts[-1];me=g.data
    for v in me.vertices:   # radius per station (tube() takes one radius)
        x=v.co.x;rr=float(np.interp(x,gx,gr));c=Vector((x,0,max(gr)+.0006));d=(v.co-c);d.x=0
        if d.length>1e-6:v.co=c+d.normalized()*rr
    for i,x in enumerate((.245,.255)):   # cord whipping where grip and cane meet
        r=R(x)+.0035;tube(f'FI01_Whip{i}',[Vector((x+.002*math.sin(a),r*math.cos(a),R(x)+.0006+r*math.sin(a))) for a in np.linspace(0,math.tau,15)],.0022,M['cord_dark'],'Body',sides=5,scale=.05)
    # split-cane splint over a crack in the upper cane, lashed in a cross at both ends
    sx0,sx1=1.30,1.52;sp=[C(x)+Vector((0,-R(x)*.95,.0)) for x in np.linspace(sx0,sx1,8)]
    _cane('FI01_Splint',sp,[.0042]*8,M['bamboo_split'],'Body',sides=6)
    for k,x in enumerate((sx0+.03,sx1-.03)):
        c=C(x);r=R(x)+.006
        for j in range(4):   # four turns side by side, 4 mm apart, each a little wider: turns on top of each other were coplanar
            a0=j*.9;rj=r+.0009*j;pts_=[c+Vector(((j-1.5)*.004+.005*math.sin(a*2+a0)*(1 if j%2 else -1),rj*math.cos(a),rj*math.sin(a))) for a in np.linspace(0,math.tau,15)]
            tube(f'FI01_Lash{k}{j}',pts_,.0018,M['hemp'],'Body',sides=5,scale=.05)
    # line winder: a short stick tied along the cane above the grip, the line wound round it
    wx0,wx1=.40,.56;wy=-(R(.48)+.012)
    tube('FI01_Winder',[Vector((x,wy,.0105)) for x in np.linspace(wx0,wx1,5)],.0045,M['floatwood'],'Detail_Line',sides=6,scale=.1)
    coil=[]   # the wound line: one continuous helix round the stick, two layers, a little uneven
    for k in range(2):
        for a in np.linspace(0,math.tau*11,11*12):
            x=wx0+.03+(a/(math.tau*11))*.10 if k==0 else wx0+.13-(a/(math.tau*11))*.09
            rr=.0062+.0018*k+.0006*math.sin(a*.7);coil.append(Vector((x,wy+rr*math.cos(a),.0105+rr*math.sin(a))))
    tube('FI01_Coil',coil,.0012,M['hemp'],'Detail_Line',sides=4,scale=.03)
    for k,x in enumerate((wx0+.02,wx1-.02)):   # ties holding the winder to the cane
        c=C(x);pts_=[Vector((x,(c.y+wy)/2+.017*math.cos(a)*1.1,.0105+.012*math.sin(a))) for a in np.linspace(0,math.tau,13)]
        tube(f'FI01_WTie{k}',pts_,.0016,M['hemp'],'Detail_Line',sides=4,scale=.03)
    # the line: from the winder up the cane through cord guides to the tip, a little slack between guides
    guides=[1.05,1.75,Lp-.02];prev=Vector((wx1,wy,.0105));line=[prev]
    for gi,gxx in enumerate(guides):   # one continuous line (separate pieces met cap to cap at the guides)
        tgt=C(gxx)+Vector((0,-R(gxx)-.003,R(gxx)*.4))
        line+=[prev.lerp(tgt,t)+Vector((0,-.004*math.sin(math.pi*t),-.002*math.sin(math.pi*t))) for t in np.linspace(0,1,12)[1:]];prev=tgt
        if gi<2:
            c=C(gxx);r=R(gxx)+.0075;tube(f'FI01_Guide{gi}',[Vector((gxx,c.y+r*math.cos(a),c.z+r*math.sin(a))) for a in np.linspace(0,math.tau,11)],.0014,M['cord_dark'],'Detail_Line',sides=4,scale=.03)
    tube('FI01_Line',line,.0009,M['hemp'],'Detail_Line',sides=4,scale=.03)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        px=pos[...,0]-meta['offset'][0]
        grip=np.clip((.24-px)/.03,0,1)*np.clip(px/.02,0,1)*filled   # hand-polished grip: smoother, a touch darker and warmer
        col=col*(1-.07*grip[...,None]);rough=np.clip(rough-.2*grip,0,1)
        return col,rough
    return {'paint':paint,'wear':.8,'grime':.7,'uv_angle':50,'notes':['lies flat along X; the work pack allows it to be leant against something when placed (rotate the whole item)',
            'Detail_Line: the line, its guides and the stick winder with the wound line; the splint and its lashing are part of the body']}
PROPS['FI01']=FI01
