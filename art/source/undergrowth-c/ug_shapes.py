# C 林下植物（undergrowth-c）: leaf outlines shared by the leaf meshes (ug_items2.py) and the leaf source textures (ug_sources.py).
# Leaf space: x along the midrib from the stalk (x = 0) to the tip (x = 1), y across (+ = the leaf's left). Each outline is a closed
# polygon, star-shaped about its centre point C, so a leaf mesh is the outline plus rings shrunk towards C (no leaf cards).
# A texture texel (u, v) maps to y = (u - .5) * 2 * HW, x = X0 + v * (1 - X0): the leaf painted in the source and the mesh line up.

def _cr(ctrl,n):
    """Catmull-Rom through 2D control points (open), n points"""
    C=[np.array(c,float) for c in ctrl];C=[2*C[0]-C[1]]+C+[2*C[-1]-C[-2]];out=[]
    seg=len(C)-3
    for i in range(1,len(C)-2):
        p0,p1,p2,p3=C[i-1],C[i],C[i+1],C[i+2];m=max(2,n//seg)
        for j in range(m):
            t=j/m;out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    out.append(C[-2]);return np.array(out)

def _mirror(half):
    """the left half (tip first … to the stalk) mirrored to a closed outline: tip → left side → base → right side"""
    right=half[::-1][1:-1]*np.array([1,-1]);return np.vstack([half,right])

# cordate leaf (UG02): a deep heart notch where the stalk joins, round lobes behind the stalk, a drawn-out drooping tip
HEART=_mirror(_cr([(1.,0.),(.80,.10),(.58,.30),(.30,.42),(.06,.40),(-.13,.27),(-.15,.12),(-.06,.035),(0.,0.)],34))
HEART_C=(.34,0.)
# palmate deeply cut leaf (UG04): five toothed lobes round the stalk point
def _palm(n_lobe=5,depth=.55,teeth=3,span=300.):
    pts=[]
    a0=math.radians(span/2)
    for k in range(n_lobe*(2*teeth+2)):
        f=k/(n_lobe*(2*teeth+2));a=a0-f*2*a0
        lobe=(f*n_lobe)%1.;  # 0 … 1 across one lobe
        r=1-depth*(1-math.sin(math.pi*lobe)**.7)           # deep cuts between lobes
        r*=1-.10*(1-abs(math.cos(math.pi*lobe*(2*teeth+1)))) # teeth on every lobe
        r*=1-.35*(abs(a)/a0)**3                              # the back lobes are shorter
        pts.append((r*math.cos(a),r*math.sin(a)))
    pts.append((0.,0.));return np.array(pts)
PALM=_palm();PALM_C=(.08,0.)
# petal (UG04): a broad rounded spoon
PETAL=_mirror(_cr([(1.,0.),(.92,.22),(.70,.34),(.40,.30),(.14,.15),(0.,0.)],12));PETAL_C=(.45,0.)
# dead leaves (UG05): an oval and a lobed oak-like leaf
OVAL=_mirror(_cr([(1.,0.),(.85,.14),(.55,.25),(.25,.22),(.06,.10),(0.,0.)],12));OVAL_C=(.45,0.)
OAK=_mirror(_cr([(1.,0.),(.90,.16),(.80,.12),(.70,.27),(.58,.18),(.46,.31),(.34,.20),(.22,.28),(.10,.14),(.02,.06),(0.,0.)],26));OAK_C=(.45,0.)

def shape_box(P):
    """leaf-space box of an outline: X0 (min x) and HW (half width), for the texture mapping"""
    return float(P[:,0].min()),float(np.abs(P[:,1]).max())

def inside(P,x,y):
    """even-odd point-in-polygon on numpy grids"""
    ins=np.zeros(x.shape,bool);n=len(P)
    for i in range(n):
        x1,y1=P[i];x2,y2=P[(i+1)%n]
        if y1==y2:continue
        c=((y1>y)!=(y2>y))&(x<(x2-x1)*(y-y1)/(y2-y1)+x1);ins^=c
    return ins

def seg_dist(x,y,a,b):
    a=np.array(a,float);b=np.array(b,float);d=b-a;L2=max(float(d@d),1e-12)
    t=np.clip(((x-a[0])*d[0]+(y-a[1])*d[1])/L2,0,1);return np.hypot(x-a[0]-t*d[0],y-a[1]-t*d[1]),t

def poly_dist(x,y,pts):
    """distance to an open polyline and the position along it (0 … 1)"""
    best=np.full(x.shape,9.);pos=np.zeros(x.shape);L=[0.]
    for a,b in zip(pts,pts[1:]):L.append(L[-1]+math.dist(a,b))
    for i,(a,b) in enumerate(zip(pts,pts[1:])):
        d,t=seg_dist(x,y,a,b);m=d<best;best=np.where(m,d,best);pos=np.where(m,(L[i]+t*(L[i+1]-L[i]))/max(L[-1],1e-9),pos)
    return best,pos

def leaf_grid(P,R):
    """leaf-space coordinates of every texel of an R × R source texture (x along, y across)"""
    X0,HW=shape_box(P);u=np.arange(R)[None,:]/R+.5/R;v=np.arange(R)[:,None]/R+.5/R
    y=(u-.5)*2*HW+0*v;x=X0+v*(1-X0)+0*u;return x,y

def leaf_uv(P,x,y):
    X0,HW=shape_box(P);return (y/(2*HW)+.5,(x-X0)/(1-X0))
