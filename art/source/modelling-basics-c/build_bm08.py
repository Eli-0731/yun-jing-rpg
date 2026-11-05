"""BM08 shrubs only. Blender 4.5.3, deterministic.
blender -b --factory-startup -P build_bm08.py -- [BM08_01 BM08_02]
Saved and selected AI references are required before any modelling begins (art/references/BM08/prompt.txt with a 「選用：」 line).
Shrubs are branch tubes plus alpha-cut leaf cards: twigs grow from the crown toward attractor points on the crown shell, each twig
ends in leaf sprays drawn into a 4 x 2 atlas (sunlit, shade and older variants). Leaf normals lean on the crown shape so the bush
shades as one mass. LODs are authored (fewer, larger cards; fewer tube sides), not collapsed, so the silhouette survives.
BM08_01 round dense creek willow 1.2 m (standard); BM08_02 loose forest-edge shrub with red berries 1.0 m (high).
Reuses Mesh / material / glb_cutout from build_bm09_bm10.py and png / material_maps from bm10_textures.py.
"""
import sys
sys.dont_write_bytecode=True
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
import bm10_textures as tx
import build_bm09_bm10 as fb
import meshfix
TEX=ROOT/'art/textures/modelling-basics-c';OUT=ROOT/'art/exports/modelling-basics-c'
IDS=['BM08_01','BM08_02']
SPEC={'BM08_01':dict(kind='willow',H=1.2,R=(.68,.60),tier='standard',seed=801,stems=13,attract=240,inner=50,card=(.30,.36),clumps=0,lod2=(.30,1.62)),
      'BM08_02':dict(kind='berry',H=1.0,R=(.64,.50),tier='high',seed=802,stems=8,attract=125,inner=10,card=(.30,.38),clumps=7,lod2=(.15,2.1))}

# ---------------- textures ----------------
def smooth(e0,e1,x):
    t=np.clip((x-e0)/(e1-e0),0,1);return t*t*(3-2*t)
def lowfreq(h,w,rng,k=6):
    """cheap smooth noise: a few random sines"""
    y,x=np.mgrid[0:h,0:w].astype(np.float32);o=np.zeros((h,w),np.float32)
    for i in range(k):
        a=rng.uniform(0,math.tau);f=rng.uniform(2,7)/max(h,w)*math.tau
        o+=np.sin((x*math.cos(a)+y*math.sin(a))*f+rng.uniform(0,math.tau))/k
    return o
def bleed(rgb,a,passes=24):
    """push leaf colour into the transparent area so mips and the alpha edge show no dark fringe"""
    c=rgb*a[...,None];w=a.copy()
    for _ in range(passes):
        s=np.zeros_like(c);n=np.zeros_like(w)
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            s+=np.roll(np.roll(c,dy,0),dx,1);n+=np.roll(np.roll(w,dy,0),dx,1)
        grow=(w<.5)&(n>0);c=np.where(grow[...,None],s/np.maximum(n,1e-6)[...,None],c);w=np.where(grow,1.,w)
    mean=(rgb*a[...,None]).sum((0,1))/max(a.sum(),1)
    return np.where(w[...,None]>.5,c/np.maximum(w,1e-6)[...,None],mean)

def draw_leaf(canvas,b,ang,L,W,kind,col,bend,rng,under=False):
    """one leaf into canvas (dict of arrays): base b (px), angle, length, half-width; curved midrib; soft 1 px edge"""
    rgb,a,h=canvas['rgb'],canvas['a'],canvas['h'];Hh,Ww=a.shape
    ax=np.array([math.cos(ang),math.sin(ang)]);nx=np.array([-ax[1],ax[0]])
    pad=W+abs(bend)*L+2
    x0=int(max(0,min(b[0],b[0]+ax[0]*L)-pad));x1=int(min(Ww,max(b[0],b[0]+ax[0]*L)+pad+1))
    y0=int(max(0,min(b[1],b[1]+ax[1]*L)-pad));y1=int(min(Hh,max(b[1],b[1]+ax[1]*L)+pad+1))
    if x1<=x0 or y1<=y0:return
    yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32);px=xx-b[0];py=yy-b[1]
    s=(px*ax[0]+py*ax[1])/L;d=px*nx[0]+py*nx[1]-bend*L*np.clip(s,0,1)**2
    if kind=='willow':prof=np.clip(np.sin(np.pi*np.clip(s,0,1)**.8),0,1)**.75*(1-.25*s)          # long lanceolate
    elif kind=='berry':prof=np.clip(np.sin(np.pi*np.clip(s,0,1)**1.35),0,1)**.7                  # ovate, widest below the middle, pointed tip
    else:prof=np.clip(np.sin(np.pi*np.clip(s,0,1)),0,1)**.6
    wl=W*prof;m=smooth(.5,-.5,np.abs(d)-wl)*(s>0)*(s<1)
    if kind=='berry':m=m*np.where(np.abs(d)>wl-1.6,.85+.15*np.sin(s*55),1)              # faint serration
    side=np.abs(d)/np.maximum(wl,1e-3)
    tone=.86+.20*(1-side)+.06*np.sin(s*7+rng.uniform(0,6))
    vein=np.exp(-(d/1.3)**2)*(s<.96)
    lat=np.exp(-(np.sin((s*(9 if kind=='willow' else 7)-side*.9)*np.pi)/.18)**2)*(side>.12)*(side<.85)
    c=np.array(col)*tone[...,None]+(np.array([.10,.10,.03]) if not under else np.array([.07,.08,.06]))*vein[...,None]+.02*lat[...,None]
    c=c*(1-.12*smooth(.75,1,side))[...,None]
    sub=(slice(y0,y1),slice(x0,x1))
    rgb[sub]=rgb[sub]*(1-m[...,None])+c*m[...,None];a[sub]=np.maximum(a[sub],m)
    h[sub]=np.maximum(h[sub],m*(.6+.4*np.sqrt(np.clip(1-side*side,0,1))-.25*vein))
    canvas['n'][sub]+=m
def draw_line(canvas,pts,r0,r1,col):
    rgb,a,h=canvas['rgb'],canvas['a'],canvas['h'];Hh,Ww=a.shape
    for i in range(len(pts)-1):
        p,q=np.array(pts[i]),np.array(pts[i+1]);ra=r0+(r1-r0)*i/(len(pts)-1);rb=r0+(r1-r0)*(i+1)/(len(pts)-1)
        x0=int(max(0,min(p[0],q[0])-ra-2));x1=int(min(Ww,max(p[0],q[0])+ra+3));y0=int(max(0,min(p[1],q[1])-ra-2));y1=int(min(Hh,max(p[1],q[1])+ra+3))
        if x1<=x0 or y1<=y0:continue
        yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32);v=q-p;t=np.clip(((xx-p[0])*v[0]+(yy-p[1])*v[1])/max(v@v,1e-6),0,1)
        dist=np.hypot(xx-(p[0]+t*v[0]),yy-(p[1]+t*v[1]));rr=ra+(rb-ra)*t;m=smooth(.5,-.5,dist-rr)
        sh=1-.35*np.clip(dist/np.maximum(rr,.5),0,1)
        sub=(slice(y0,y1),slice(x0,x1))
        rgb[sub]=rgb[sub]*(1-m[...,None])+(np.array(col)*sh[...,None])*m[...,None];a[sub]=np.maximum(a[sub],m);h[sub]=np.maximum(h[sub],m*.5*sh)
def draw_berry(canvas,c,r,col):
    rgb,a,h=canvas['rgb'],canvas['a'],canvas['h'];Hh,Ww=a.shape
    x0,x1,y0,y1=int(max(0,c[0]-r-2)),int(min(Ww,c[0]+r+3)),int(max(0,c[1]-r-2)),int(min(Hh,c[1]+r+3))
    if x1<=x0 or y1<=y0:return
    yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32);d=np.hypot(xx-c[0],yy-c[1])/r;m=smooth(1.05,.95,d)
    hl=np.exp(-((xx-c[0]+.35*r)**2+(yy-c[1]-.35*r)**2)/(.09*r*r))
    sh=(.7+.3*np.sqrt(np.clip(1-d*d,0,1)))[...,None]*np.array(col)+hl[...,None]*.18
    sub=(slice(y0,y1),slice(x0,x1))
    rgb[sub]=rgb[sub]*(1-m[...,None])+sh*m[...,None];a[sub]=np.maximum(a[sub],m);h[sub]=np.maximum(h[sub],m*np.sqrt(np.clip(1-d*d,0,1)))

PAL={'willow':dict(sun=[(.62,.67,.25),(.68,.69,.29),(.55,.63,.23)],shade=(.30,.46,.36),old=(.72,.66,.28),under=(.58,.64,.46),twig=(.42,.30,.17),
                   litter=[(.66,.55,.22),(.55,.42,.18),(.44,.40,.20),(.62,.48,.20)]),
     'berry':dict(sun=[(.58,.63,.23),(.64,.65,.27),(.50,.59,.22)],shade=(.26,.42,.34),old=(.72,.63,.27),under=(.50,.59,.44),twig=(.36,.22,.15),
                  litter=[(.58,.34,.14),(.62,.46,.18),(.48,.30,.16),(.55,.40,.20)])}
BERRY=(.62,.07,.05)

def leaf_atlas(prefix,kind,seed,size=2048):
    """4 x 2 slots, each 512 x 1024 (a spray card, twig up the middle from the bottom edge).
    row 0: three sunlit sprays, one shade spray; row 1: two older sprays, a sparse outer twiglet, a dense shade spray"""
    rng=random.Random(seed);P=PAL[kind];sw,sh=size//4,size//2
    cv={'rgb':np.zeros((size,size,3),np.float32),'a':np.zeros((size,size),np.float32),'h':np.zeros((size,size),np.float32),'n':np.zeros((size,size),np.float32)}
    for slot in range(8):
        col,row=slot%4,slot//4;ox,oy=col*sw,row*sh
        shade=slot in (3,7);old=slot in (4,5);sparse=slot==6
        # twig: from the bottom-centre up, a gentle S
        n=10;tw=[(ox+sw*.5+sw*.06*math.sin(i/n*2.6+slot),oy+6+(sh*.86)*i/n) for i in range(n+1)]
        draw_line(cv,tw,5.5 if kind=='willow' else 6.5,2.0,P['twig'])
        if kind=='willow':count,L,W=(7 if sparse else 12),(260,380),(24,33)
        else:count,L,W=(4 if sparse else 7),(200,260),(52,66)
        for i in range(count):
            t=.12+.86*i/max(1,count-1)+rng.uniform(-.02,.02);t=min(t,.985)
            k=int(t*n);f=t*n-k;k=min(k,n-1)
            p=np.array(tw[k])*(1-f)+np.array(tw[k+1])*f
            side=1 if i%2 else -1
            spread=(.8 if kind=='willow' else .95)*(1-.45*t)+rng.uniform(-.15,.15)       # leaves splay out low on the twig, lie closer near the tip
            ang=math.pi/2-side*spread
            if t>.95:ang=math.pi/2+rng.uniform(-.1,.1)
            Ll=rng.uniform(*L)*(.65+.5*math.sin(math.pi*min(1,t*1.1)))*(.9 if sparse else 1)
            if kind=='berry':Ll=min(Ll,sh*.27)
            Wl=rng.uniform(*W)*(Ll/np.mean(L))**.5
            bend=rng.uniform(-.06,.06)-side*(.34 if kind=='willow' else .08)   # willow leaves droop
            # keep the whole curved leaf inside its slot: shrink it until its midrib (plus half-width) clears the slot edges
            ax_=np.array([math.cos(ang),math.sin(ang)]);nx_=np.array([-ax_[1],ax_[0]])
            for _ in range(30):
                mid=[p+ax_*Ll*q+nx_*bend*Ll*q*q for q in (.25,.5,.75,1.)]
                if all(ox+Wl+4<m[0]<ox+sw-Wl-4 and oy+4<m[1]<oy+sh-Wl-4 for m in mid):break
                Ll*=.92;Wl*=.97
            under=(not shade) and rng.random()<(.28 if kind=='willow' else .18)
            if shade:c=np.array(P['shade'])*rng.uniform(.85,1.1)
            elif under:c=np.array(P['under'])*rng.uniform(.9,1.05)
            elif old:c=(np.array(P['old']) if rng.random()<.3 else np.array(rng.choice(P['sun'])))*rng.uniform(.9,1.05)
            else:c=np.array(rng.choice(P['sun']))*rng.uniform(.92,1.08)
            draw_line(cv,[tuple(p),tuple(p+np.array([math.cos(ang),math.sin(ang)])*6)],2.2,1.6,P['twig'])
            draw_leaf(cv,p+np.array([math.cos(ang),math.sin(ang)])*4,ang,Ll,Wl,kind,c,bend,rng,under)
        if kind=='berry' and sparse:   # berries painted only on the open twiglet; elsewhere they sat on the leaves like red spots (the 3D clusters carry them)
            for _ in range(3):   # berry clusters on short stalks near the twig
                t=rng.uniform(.35,.9);k=int(t*n);p=np.array(tw[k]);s=rng.choice((-1,1));q=p+np.array([s*rng.uniform(25,60),rng.uniform(-10,30)])
                q[0]=np.clip(q[0],ox+30,ox+sw-30)
                draw_line(cv,[tuple(p),tuple(q)],2.2,1.5,P['twig'])
                for _ in range(rng.randint(4,8)):
                    c=q+np.array([rng.uniform(-22,22),rng.uniform(-18,22)]);draw_line(cv,[tuple(q),tuple(c)],1.2,1.0,P['twig'])
                    draw_berry(cv,c,rng.uniform(16,20),np.array(BERRY)*rng.uniform(.8,1.1))
    a=cv['a'];rgb=cv['rgb']
    lf=lowfreq(size,size,rng);rgb=rgb*(1+.08*lf)[...,None]
    y=np.mgrid[0:size,0:size][0].astype(np.float32);vin=(y%sh)/sh
    ao=np.clip(.62+.38*vin,0,1)*np.clip(1-.12*np.clip(cv['n']-1,0,3),.6,1)   # darker toward the card root and where leaves overlap
    rgb=rgb*(.8+.2*ao)[...,None]
    rgb=bleed(rgb,(a>.5).astype(np.float32))
    return tx.material_maps(prefix,np.clip(rgb,0,1),cv['h']*.0009,a,np.full_like(a,.62),ao,TEX,normal_strength=1.)

def litter_atlas(prefix,kind,seed,size=512):
    """2 x 2 fallen leaves (and on the berry shrub two dropped berries) for flat cards on the ground"""
    rng=random.Random(seed);P=PAL[kind];h=size//2
    cv={'rgb':np.zeros((size,size,3),np.float32),'a':np.zeros((size,size),np.float32),'h':np.zeros((size,size),np.float32),'n':np.zeros((size,size),np.float32)}
    for s in range(4):
        ox,oy=(s%2)*h,(s//2)*h
        L=h*.86 if kind=='willow' else h*.8;W=L*(.075 if kind=='willow' else .3)
        draw_leaf(cv,np.array([ox+h*.5,oy+h*.07]),math.pi/2+rng.uniform(-.05,.05),L,W,kind,np.array(P['litter'][s]),rng.uniform(-.12,.12),rng)
    if kind=='berry':
        draw_berry(cv,(h*.25,h*.25),12,np.array(BERRY)*.7);draw_berry(cv,(h*.75,h*.3),11,np.array(BERRY)*.6)
    a=cv['a'];rgb=bleed(cv['rgb'],(a>.5).astype(np.float32))
    y=np.mgrid[0:size,0:size][0].astype(np.float32)
    return tx.material_maps(prefix,np.clip(rgb,0,1),cv['h']*.0008,a,np.full_like(a,.8),np.full_like(a,.92),TEX,normal_strength=1.)

def bark(prefix,kind,seed,size=512):
    rng=random.Random(seed);y,x=np.mgrid[0:size,0:size].astype(np.float32)/size
    streak=.5+.5*np.sin(x*math.tau*7+1.4*np.sin(y*math.tau*3+x*9))*np.sin(x*math.tau*17+.6)
    lf=lowfreq(size,size,rng)
    base=np.array([.36,.27,.17]) if kind=='willow' else np.array([.33,.21,.15])
    rgb=base*(.82+.22*streak[...,None]+.10*lf[...,None])
    lent=(np.sin(y*math.tau*14+np.sin(x*math.tau*2)*2)>.93)*(np.sin(x*math.tau*5+y*3)>.4)   # small pale lenticels
    rgb=np.where(lent[...,None],rgb*.5+np.array([.52,.46,.36])*.5,rgb)
    if kind=='willow':rgb=rgb*(1-.2*smooth(.3,.9,lf)[...,None])+np.array([.36,.38,.20])*.2*smooth(.3,.9,lf)[...,None]   # greenish young bark
    return tx.material_maps(prefix,np.clip(rgb,0,1),streak*.0004,np.ones_like(x),np.full_like(x,.82),np.full_like(x,.95),TEX,normal_strength=1.)

def berry_tex(prefix,size=256):
    y,x=np.mgrid[0:size,0:size].astype(np.float32)/size
    rgb=np.array(BERRY)*(.85+.15*np.sin(x*9)[...,None]*np.sin(y*7)[...,None])
    return tx.material_maps(prefix,np.clip(rgb,0,1),np.zeros_like(x),np.ones_like(x),np.full_like(x,.38),np.ones_like(x),TEX)

# ---------------- geometry ----------------
def catmull(pts,n):
    pts=[Vector(p) for p in pts];P=[pts[0]+(pts[0]-pts[1])]+pts+[pts[-1]+(pts[-1]-pts[-2])];out=[]
    for i in range(1,len(P)-2):
        for j in range(n):
            t=j/n;p0,p1,p2,p3=P[i-1],P[i],P[i+1],P[i+2]
            out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    out.append(pts[-1]);return out

def tube(mesh,points,r0,r1,sides,vscale=1.):
    """tapered tube with bark UVs running along it (v by length so the bark texture does not stretch)"""
    points=[Vector(p) for p in points];base=len(mesh.v);n=len(points);acc=0.;prev_a=None
    for i,p in enumerate(points):
        tg=(points[min(i+1,n-1)]-points[max(i-1,0)]).normalized()
        a=prev_a-tg*prev_a.dot(tg) if prev_a is not None else tg.cross(Vector((0,0,1)))
        if a.length<1e-3:a=tg.cross(Vector((1,0,0)))
        a.normalize();prev_a=a;b=tg.cross(a).normalized()
        if i:acc+=(p-points[i-1]).length
        r=r0+(r1-r0)*i/(n-1)
        for j in range(sides+1):
            ang=math.tau*j/sides;mesh.vertex(p+r*(a*math.cos(ang)+b*math.sin(ang)),(j/sides,acc*vscale/ max(r0*math.tau,1e-3)*.25))
    for i in range(n-1):
        for j in range(sides):
            a=base+i*(sides+1)+j;mesh.quad(a,a+1,a+sides+2,a+sides+1)

def card(mesh,base,d,side,L,W,slot,fold,droop,nrm_fn,custom):
    """bent leaf card: 3 rows along its length, folded slightly along the midline (2 columns); UV into atlas slot"""
    col,row=slot%4,slot//4;up=d.cross(side).normalized();first=len(mesh.v)
    for i in range(4):
        t=i/3;p=base+d*L*t-up*droop*L*t*t
        for k,s in enumerate((-1,0,1)):
            q=p+side*W*.5*s+up*fold*W*.5*(1-abs(s))
            mesh.vertex(q,((col+.5+.5*s)/4,(row+.003+.994*t)/2));custom.append(nrm_fn(q,up))
    for i in range(3):
        for k in range(2):
            a=first+i*3+k;mesh.quad(a,a+3,a+4,a+1)   # front face = up (outward)

BERRY_D=Vector((.25,.9,.45)).normalized();BERRY_U=BERRY_D.cross(Vector((0,0,1))).normalized();BERRY_V=BERRY_D.cross(BERRY_U).normalized()
def icosphere(mesh,c,r,custom=None):
    """20-triangle berry"""
    t=(1+5**.5)/2;V=[(-1,t,0),(1,t,0),(-1,-t,0),(1,-t,0),(0,-1,t),(0,1,t),(0,-1,-t),(0,1,-t),(t,0,-1),(t,0,1),(-t,0,-1),(-t,0,1)]
    F=[(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),(1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),(3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),(4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]
    b=len(mesh.v)
    for v in V:
        # UV: the sphere projected along BERRY_D, which no face of the icosahedron is edge-on to (projecting on x-z, as before,
        # flattened 4 of the 20 faces to zero UV area: 1,256 faces on BM08_02 in the #69 review)
        n=Vector(v).normalized();mesh.vertex(c+n*r,(.5+.45*n.dot(BERRY_U),.5+.45*n.dot(BERRY_V)))
        if custom is not None:custom.append(tuple(n))
    mesh.f.extend([(b+x,b+y,b+z) for x,y,z in F])

def skeleton(pid):
    """stems from the crown, twigs from the stems toward attractor points on the crown shell (and a few inside)"""
    S=SPEC[pid];r=random.Random(S['seed']);H=S['H'];Rx,Ry=S['R'];cz=H*.56;Rz=H*.44   # a dome: widest a little above the middle
    berry=S['kind']=='berry'
    stems=[]
    for k in range(S['stems']):
        a=math.tau*k/S['stems']+r.uniform(-.3,.3);lean=r.uniform(.25,.8) if not berry else r.uniform(.3,1.0)
        b0=Vector((math.cos(a)*r.uniform(0,.05),math.sin(a)*r.uniform(0,.05),0))
        top=Vector((math.cos(a)*Rx*lean*.8,math.sin(a)*Ry*lean*.8,H*r.uniform(.72,.97)))
        if berry and k%3==0:top=Vector((math.cos(a)*Rx*r.uniform(.85,1.05),math.sin(a)*Ry*r.uniform(.85,1.05),H*r.uniform(.55,.75)))   # long arching canes
        mid=b0.lerp(top,.45)+Vector((math.cos(a),math.sin(a),0))*r.uniform(.04,.12)+Vector((0,0,r.uniform(.02,.08)))
        pts=catmull([b0,b0.lerp(mid,.5)+Vector((0,0,.04)),mid,top],4)
        stems.append(pts)
    # attractors: the crown shell (clumped for the loose shrub), plus inner fill so the crown never reads hollow
    att=[]
    centres=[Vector((r.gauss(0,1),r.gauss(0,1),r.gauss(.4,.6))).normalized() for _ in range(S['clumps'])]
    while len(att)<S['attract']:
        v=Vector((r.gauss(0,1),r.gauss(0,1),r.gauss(0,1))).normalized()
        if v.z<-.62:continue
        if v.z<0 and r.random()<.35:continue   # fewer under the widest line, so the crown rounds in toward the stems
        if centres:
            near=max(v.dot(c) for c in centres)
            if near<.80 and r.random()<.85:continue
        f=r.uniform(.80,1.0) if not berry else r.uniform(.7,1.05)
        if r.random()<.12:f*=r.uniform(1.06,1.16)   # a few twigs poke out past the crown and break the outline
        p=Vector((v.x*Rx*f,v.y*Ry*f,cz+v.z*Rz*f));p.z=max(p.z,.10 if not berry else .22)
        att.append((p,False))
    for _ in range(S['inner']):
        v=Vector((r.gauss(0,1),r.gauss(0,1),r.gauss(.3,.7))).normalized();f=r.uniform(.35,.7)
        att.append((Vector((v.x*Rx*f,v.y*Ry*f,max(.18,cz+v.z*Rz*f))),True))
    pts=[(p,si,i) for si,s in enumerate(stems) for i,p in enumerate(s) if i>=3]
    twigs=[];used={}
    for p,inner in att:
        # #69 review: twigs that left one stem point toward neighbouring attractors ran inside each other for their first
        # stretch (same-facing coplanar pairs). Each use of a stem point now costs 6 cm, so twigs spread along the stems.
        q,si,i=min(pts,key=lambda e:(e[0]-p).length+.15*abs(e[0].z-p.z)+.06*used.get((e[1],e[2]),0))
        used[(si,i)]=used.get((si,i),0)+1
        mid=q.lerp(p,.5)+Vector((0,0,.03+.05*(p-q).length))
        twigs.append((catmull([q,mid,p],3),inner,(p-q).length,si,i))
    berries=[];anchors=[]
    if berry:
        outer=[t for t in twigs if not t[1]];r.shuffle(outer)
        for tw in outer[:46]:   # clusters hang just below the twig ends
            c=tw[0][-1]+Vector((r.uniform(-.03,.03),r.uniform(-.03,.03),-r.uniform(.03,.07)))
            berries.append([c+Vector((r.gauss(0,.014),r.gauss(0,.014),-abs(r.gauss(0,.016)))) for _ in range(r.randint(5,9))]);anchors.append((tw[0][-1],c))
    return dict(stems=stems,twigs=twigs,berries=berries,berry_anchors=anchors,centre=Vector((0,0,cz)),radii=(Rx,Ry,Rz))

def shrub_meshes(pid,sk,lod):
    S=SPEC[pid];r=random.Random(S['seed']*10+lod);berry=S['kind']=='berry'
    leaves=fb.Mesh();wood=fb.Mesh();lit=fb.Mesh();ber=fb.Mesh();cl=[];cb=[]
    C=sk['centre'];Rx,Ry,Rz=sk['radii']
    def nrm(q,up):
        """leaf normals: mostly the crown ellipsoid's outward direction, a little of the card, so the crown shades as one mass"""
        o=Vector(((q.x-C.x)/Rx**2,(q.y-C.y)/Ry**2,(q.z-C.z)/Rz**2)).normalized()
        cu=up if up.dot(o)>0 else -up
        return tuple((o*.78+cu*.22).normalized())
    sides=[6,4,3][lod];stem_seg=[1,2,3][lod]
    stem_r=[(.022 if not berry else .019)*(1-.25*(k%3)/2) for k in range(len(sk['stems']))]
    for k,s in enumerate(sk['stems']):
        pts=s[::stem_seg] if s[-1] in s[::stem_seg] else s[::stem_seg]+[s[-1]]
        tube(wood,pts,stem_r[k],.006,sides)
    for i,(pts,inner,L,si,at) in enumerate(sk['twigs']):
        if lod==1 and inner and i%2:continue
        if lod==2 and (inner or i%5):continue
        tp=pts[::2]+([pts[-1]] if (len(pts)-1)%2 else []) if lod==0 else [pts[0],pts[len(pts)//2],pts[-1]]
        sr=stem_r[si]+(.006-stem_r[si])*at/(len(sk['stems'][si])-1)   # the stem's radius where the twig leaves it
        if lod<2 or berry:tube(wood,tp,min(.0075 if L>.25 else .0055,.75*sr),.0022,4 if (lod==0 and L>.25 and not inner) else 3)   # never thicker than its stem
    # leaf cards: each outer twig carries sprays at its tip and along it; inner twigs carry shade sprays
    cl0=S['card'];ncard=0
    for i,(pts,inner,L,si,at) in enumerate(sk['twigs']):
        per=1 if inner else 3
        for j in range(per):
            rr=random.Random(S['seed']*1000+i*7+j)          # same card choice on every LOD; LODs keep a subset and enlarge it
            u=rr.random()
            if lod==1 and u>.5:continue
            if lod==2 and (u>S['lod2'][0] or inner):continue   # willow keeps more, smaller cards so LOD2 lands near 15%
            t=1. if j==0 else rr.uniform(.45,.85);k=min(len(pts)-1,int(t*(len(pts)-1)))
            p=pts[k];tg=(pts[min(k+1,len(pts)-1)]-pts[max(k-1,0)]).normalized()
            # cards lie roughly tangent to the crown (face outward, so they are seen face-on from outside), run along the twig
            # direction turned a little about the outward axis, lean out by ~25 degrees and droop at the sides
            out=Vector(((p.x-C.x)/Rx**2,(p.y-C.y)/Ry**2,(p.z-C.z)/Rz**2)).normalized()
            tp=tg-out*tg.dot(out)
            if tp.length<.2:tp=Vector((0,0,1))-out*out.z
            if tp.length<.2:tp=out.orthogonal()
            tp.normalize();q=rr.uniform(-1.,1.);b2=out.cross(tp);tp=(tp*math.cos(q)+b2*math.sin(q)).normalized()
            if tp.z<-.2 and rr.random()<.6:tp=(tp-Vector((0,0,2*tp.z))).normalized()   # mostly up/sideways from the twig
            lean=(.45+.9*max(0,out.z)) if not inner else .2      # on the crown top the sprays point up and out, so the top is not a flat lid
            d=(tp+out*lean+Vector((0,0,-.25*max(0,1-abs(out.z))))).normalized()
            side=out.cross(d).normalized();rot=rr.uniform(-.45,.45);up=d.cross(side);side=(side*math.cos(rot)+up*math.sin(rot)).normalized()
            L_=rr.uniform(*cl0)*(1. if not inner else .85)*[1,1.32,S['lod2'][1]][lod];W_=L_*.5
            if inner:slot=3 if rr.random()<.6 else 7
            else:
                hz=(p.z-C.z)/Rz
                slot=rr.choice((0,1,2)) if hz>-.2 else rr.choice((0,4,5))
                if rr.random()<.12:slot=6
                if hz<-.45 and rr.random()<.5:slot=7
            base=p-d*L_*.06
            card(leaves,base,d,side,L_,W_,slot,rr.uniform(.15,.35),rr.uniform(.05,.18),nrm,cl);ncard+=1
    # berries (geometry, so they read in silhouette as well as in the atlas)
    if berry:   # LOD2 keeps a third of the clusters, three berries each, larger
        for ci,cluster in enumerate(sk['berries']):
            if lod==1 and ci%2:continue
            if lod==2 and ci%3:continue
            # #69 review: the clusters hung 3-7 cm under the twig ends with nothing holding them (berries up to 22 mm from any
            # wood). A stalk now runs from the twig end to the cluster, and a short stem from there into every berry.
            tip,c=sk['berry_anchors'][ci]
            tube(wood,[tip,tip.lerp(c,.5)+Vector((0,0,.006)),c],.0022,.0014,3)
            for b in (cluster if lod<2 else cluster[:3]):
                icosphere(ber,b,.0095 if lod<2 else .012,cb)
                if lod<2:c1=c+(b-c).normalized()*.0012;tube(wood,[c1,b],.0012,.0009,3)   # starts inside the stalk end, not on its point (one welded piece cannot be separated)
    # fallen leaves at the base (Detail_Litter)
    rr=random.Random(S['seed']+55);n=[26,14,6][lod]
    placed=[]
    for k in range(n):
        L_=(.10 if not berry else .075)*rr.uniform(.85,1.15)*[1,1.15,1.4][lod]
        for _ in range(40):   # #69 review: every leaf lies on the ground (was stacked .6 mm per leaf, up to 17 mm up), apart from the others
            a=rr.uniform(0,math.tau);d=rr.uniform(.08,max(Rx,Ry)*.95);c=Vector((math.cos(a)*d,math.sin(a)*d,.0004))
            if all((c-q).length>.72*(L_+Lq) for q,Lq in placed):break
        placed.append((c,L_))
        b_=rr.uniform(0,math.tau);dirv=Vector((math.cos(b_),math.sin(b_),0));side=Vector((-dirv.y,dirv.x,0))
        slot=k%4;col,row=slot%2,slot//2;first=len(lit.v)
        for i in range(2):
            for s in (-1,1):
                q=c+dirv*L_*(i-.5)+side*L_*.5*s+Vector((0,0,.004*abs(i-.5)*rr.random()))
                lit.vertex(q,((col+.5+.5*s)/2,(row+i)/2))
        lit.quad(first,first+2,first+3,first+1)   # facing up
    return {'Leaves':(leaves,cl),'Branches':(wood,None),'Berries':(ber,cb),'Detail_Litter':(lit,None)},ncard

def run(pid):
    assert pid in IDS
    S=SPEC[pid];ref=ROOT/'art/references/BM08/prompt.txt'
    assert ref.exists() and '\u9078\u7528\uff1a' in ref.read_text(encoding='utf-8'), 'Save and select AI references first'
    assert len(list(ref.parent.glob('*-cand-*.png')))>=8
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    TEX.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    root=bpy.data.objects.new(pid+'_GroundOrigin',None);sc.collection.objects.link(root);root['minTier']=S['tier']
    kind=S['kind'];textures={'Leaves':leaf_atlas(pid+'_Leaves',kind,S['seed']),'Branches':bark(pid+'_Branches',kind,S['seed']),
                             'Detail_Litter':litter_atlas(pid+'_Detail_Litter',kind,S['seed'])}
    res={'Leaves':2048,'Branches':512,'Detail_Litter':512,'Berries':256}
    if kind=='berry':textures['Berries']=berry_tex(pid+'_Berries')
    mats={g:fb.material(pid+'_'+g,p,g in ('Leaves','Detail_Litter')) for g,p in textures.items()}
    sk=skeleton(pid);groups={};lod0=[];cards=[];sep={}
    for lod in range(3):
        meshes,nc=shrub_meshes(pid,sk,lod);cards.append(nc)
        for g,(mesh,custom) in meshes.items():
            if g not in mats or not mesh.f:continue
            o=mesh.object(f'{pid}_{g}_LOD{lod}',mats[g]);o.parent=root;o.hide_render=lod!=0;groups.setdefault(g,[]).append(o)
            if custom:o.data.normals_split_custom_set_from_vertices(custom)
            if lod==0:lod0.append(o)
    body=[o for o in lod0 if '_Detail_' not in o.name];lo,hi=fb.bounds(body)
    factor=S['H']/(hi[2]-lo[2]);offset=np.array([-(hi[0]+lo[0])/2,-(hi[1]+lo[1])/2,-lo[2]])
    for objects in groups.values():
        for o in objects:
            cn=[tuple(l.normal) for l in o.data.loops] if o.data.has_custom_normals else None
            for v in o.data.vertices:
                v.co=(Vector(v.co)+Vector(offset))*factor
                if v.co.z<0:v.co.z=0
            if cn:o.data.normals_split_custom_set(cn)
    for o in groups.get('Detail_Litter',[]):   # #69: the shift above lifts the ground to the sunk stem bases (6.8 mm); lay the litter back on it
        dz=min(v.co.z for v in o.data.vertices)-.0004
        for v in o.data.vertices:v.co.z-=dz
    for gs in (('Branches','Berries'),('Leaves',),('Detail_Litter',)):   # #69 review: same-facing coplanar pieces (twig on twig, card on card, leaf on leaf, berry on its stalk)
        for i in range(len(groups.get(gs[0],[]))):   # one LOD at a time (BM08_01 has no berries)
            moved,left=meshfix.separate_meshes([groups[g][i].data for g in gs if g in groups]);sep.setdefault('+'.join(gs),[]).append([moved,left])
    bpy.context.view_layer.update()
    lo,hi=fb.bounds(lod0);blo,bhi=fb.bounds(body)
    tri=lambda o:sum(len(p.vertices)-2 for p in o.data.polygons)
    details=[g for g in groups if g.startswith('Detail_')]
    info={'id':pid,'dimensions_xyz_m':[round(float(v),6) for v in hi-lo],'body_dimensions_xyz_m':[round(float(v),6) for v in bhi-blo],
          'target_axis':'z','target_m':S['H'],'minTier':S['tier'],'detailObjects':details,
          'detailMeshes':[o.name for g in details for o in groups[g]],
          'groups':{g:{'material':pid+'_'+g,'texture_px':res[g],'triangles':[tri(o) for o in obs],'maps':['alb','nrm','maskurp','orm'],
                       'alphaCutoff':.45 if g in ('Leaves','Detail_Litter') else 0} for g,obs in groups.items()},
          'triangles_total':[sum(tri(obs[l]) for obs in groups.values()) for l in range(3)],
          'triangles_without_detail':[sum(tri(obs[l]) for g,obs in groups.items() if not g.startswith('Detail_')) for l in range(3)],
          'leaf_cards':cards,'separated_pieces':sep,
          'reference':str(ref.relative_to(ROOT)).replace('\\','/'),'origin':'crown centre at the soil line, bottom z = 0, front = -Y (Blender) / -Z (FBX, Unity)',
          'textures':{g:{k:str(Path(v).relative_to(ROOT)).replace('\\','/') for k,v in maps.items()} for g,maps in textures.items()},'collision':{},
          'notes':{'build':('round dense creek willow: 13 stems, twigs grown to an ellipsoid crown shell, narrow willow-leaf sprays on bent alpha cards'
                            if kind=='willow' else 'loose forest-edge shrub: 8 stems with long arching canes, leaves in clumps with gaps so twigs show, red berry clusters as geometry and in the atlas'),
                   'lod':'authored: LOD1 keeps half the cards 1.32x larger, LOD2 the outer cards (willow 30% at 1.62x, berry 15% at 2.1x) and only the stems; tube sides 6/4/3',
                   'collision':'none: a shrub to brush past, nothing to stop on','detail':'Detail_Litter (fallen leaves at the base); the standard tier hides it',
                   'material':'Leaves and litter are alpha-cut (cutoff 0.45), double-sided; leaf normals lean on the crown ellipsoid. Albedo sRGB, Normal tangent +Y, ORM=AO/roughness/metal, MaskURP=metal/AO/0/smoothness. Drawn procedurally, no photo sources.'}}
    assert abs(float(bhi[2]-blo[2])-S['H'])<1e-5
    root['detailObjects']=json.dumps(details)
    fb.select([root]+lod0)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/(pid+'.blend')),compress=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(pid+'.glb')),use_selection=True,export_format='GLB',export_apply=True,export_extras=True)
    fb.glb_cutout(OUT/(pid+'.glb'))
    fb.select([root]+[o for obs in groups.values() for o in obs])
    bpy.ops.export_scene.fbx(filepath=str(OUT/(pid+'.fbx')),use_selection=True,object_types={'MESH','EMPTY'},global_scale=1.,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
    print('BM_DONE',json.dumps(info));return info

if __name__=='__main__':
    assert bpy.app.version[:3]==(4,5,3), 'Pinned Blender 4.5.3 required'
    ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else IDS
    for pid in ids:
        info=run(pid)
        for name in ('model_info_bm08.json','model_info.json'):
            mf=OUT/name;d=json.loads(mf.read_text(encoding='utf-8')) if mf.exists() else {}
            d[pid]=info;mf.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
