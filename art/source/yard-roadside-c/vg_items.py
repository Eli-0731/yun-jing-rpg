# VG01–VG04 shapes (the 11/11 36h pack, batch A), read by build_vg.py (exec'd into its namespace: M = source materials;
# helpers from the creekside / village kits: tube, box, finish, _sheet, _cane, _lathe, _ring, _rod, _taper, _hoop2 …).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _surf(name,rows,mat,grp,scale=.25,smooth=True,card=None):
    """a single-sided surface through a grid of points rows[i][j] (leaves, cloth cards). card: (u0,v0,u1,v1) → the
    faces also get a 'CardUV' layer spanning that rectangle (i along v, j along u) and the part is flagged as a card."""
    bm=bmesh.new();V=[[bm.verts.new(p) for p in row] for row in rows];nu,nv=len(V),len(V[0])
    cl=bm.loops.layers.uv.new('CardUV') if card else None
    for i in range(nu-1):
        for j in range(nv-1):
            f=bm.faces.new((V[i][j],V[i][j+1],V[i+1][j+1],V[i+1][j]));f.smooth=smooth
            if card:
                u0,v0,u1,v1=card
                for l,(jj,ii) in zip(f.loops,((j,i),(j+1,i),(j+1,i+1),(j,i+1))):l[cl].uv=(u0+(u1-u0)*jj/(nv-1),v0+(v1-v0)*ii/(nu-1))
    o=finish(name,bm,mat,grp,scale)
    if sum(p.normal.z*p.area for p in o.data.polygons)<0:o.data.flip_normals()   # a leaf's shading side is its upper side
    if card:o['card']=1
    return o
def _blade(name,base,dirh,L,W,th,droop,wfun,mat,grp,nu=6,nv=2,cup=.25,u0=0.,u1=1.,twist=0.,scale=.2):
    """a leaf blade growing from `base`: it leaves at `th` from the vertical towards dirh and droops with its length;
    half-width wfun(u)*W/2, edges cupped up; u0..u1: the part of the leaf this piece covers (stalk and blade are two pieces)"""
    d=Vector((dirh[0],dirh[1],0)).normalized();s=Vector((-d.y,d.x,0));Z=Vector((0,0,1));base=Vector(base);rows=[]
    def C(u):return base+d*(L*u*math.sin(th)+droop*L*u*u*.6)+Z*(L*u*math.cos(th)-droop*L*u*u)
    for i in range(nu+1):
        u=u0+(u1-u0)*i/nu;c=C(u);tg=(C(u+.01)-C(u-.01)).normalized();n=s.cross(tg).normalized()
        if n.z<0:n=-n
        sx=(s*math.cos(twist*u)+n*math.sin(twist*u));w=wfun(u)*W/2;row=[]
        for j in range(nv+1):
            q=-1+2*j/nv;row.append(tuple(c+sx*w*q+n*cup*w*q*q))
        rows.append(row)
    return _surf(name,rows,mat,grp,scale)
def _bladec(base,dirh,L,th,droop,u):
    """the midline of _blade at u"""
    d=Vector((dirh[0],dirh[1],0)).normalized();return Vector(base)+d*(L*u*math.sin(th)+droop*L*u*u*.6)+Vector((0,0,1))*(L*u*math.cos(th)-droop*L*u*u)
def _earth(name,W,D,zf,mat,grp,NX=60,NY=40,scale=.5,p=4.5,wob=.035,seed=1):
    """a closed mound of earth about W × D: the top is the height field zf(x, y), falling to the ground at the outline;
    the outline is a rounded rectangle (the square grid is drawn in onto a superellipse) with a wobbling edge; flat bottom on z = 0"""
    r_=random.Random(seed);ph=[r_.uniform(0,6.28) for _ in range(3)];bm=bmesh.new();G=[]
    for j in range(NY+1):
        row=[]
        for i in range(NX+1):
            u=-1+2*i/NX;v=-1+2*j/NY;m=max(abs(u),abs(v));k=(abs(u)**p+abs(v)**p)**(1/p);f=m/k if k>1e-9 else 1.
            a=math.atan2(v,u);f*=1+wob*m*m*(math.sin(a*5+ph[0])+.6*math.sin(a*11+ph[1])+.4*math.sin(a*17+ph[2]))/2
            x=u*f*W/2;y=v*f*D/2;e=min(1.,(1-m)/.15);e=e*e*(3-2*e);row.append(bm.verts.new((x,y,max(.003,zf(x,y)*e))))
        G.append(row)
    for j in range(NY):
        for i in range(NX):f=bm.faces.new((G[j][i],G[j][i+1],G[j+1][i+1],G[j+1][i]));f.smooth=True
    ring=[G[0][i] for i in range(NX+1)]+[G[j][NX] for j in range(1,NY+1)]+[G[NY][i] for i in range(NX-1,-1,-1)]+[G[j][0] for j in range(NY-1,0,-1)]
    low=[bm.verts.new((v.co.x,v.co.y,0)) for v in ring];n=len(ring)
    for k in range(n):bm.faces.new((ring[k],low[k],low[(k+1)%n],ring[(k+1)%n]))
    bm.faces.new(low);bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    return finish(name,bm,mat,grp,scale)

# ---------------- VG01 kitchen garden: three earth ridges with greens, radishes and spring onions (cand-3) ----------------
def VG01(M):
    """one piece of earth 2.8 × 1.9 m: three rounded ridges running front to back, trodden furrows between them, the rim
    sloping raggedly down to the ground. Every crop is one recipe (leaf count, size, lean, turn are parameters) repeated
    along its ridge with each plant's parameters drawn at random: an array plus randomness, not plants placed by hand."""
    rr=random.Random(4101);W,D=2.80,1.90;CX=(-.90,0.,.90);RW=.37;RH=.125;FUR=.032
    ph=[rr.uniform(0,6.28) for _ in range(8)]
    def zf(x,y):
        ex=W/2-abs(x)+.05*math.sin(y*5.1+ph[0])+.03*math.sin(y*13+ph[1]);ey=D/2-abs(y)+.05*math.sin(x*4.3+ph[2])+.03*math.sin(x*11+ph[3])
        e=1.                                                                # (the outer slope is made by _earth)
        ry=max(0.,min(1.,(D/2-.20-abs(y))/.16));ry=ry*ry*(3-2*ry)          # the ridges stop short of the front and back rim
        h=0.
        for k,c in enumerate(CX):
            t=abs(x-c-.025*math.sin(y*3.1+ph[4+k]))/RW                       # each ridge wanders a little
            if t<1:h=max(h,(1-t**2.3)*(RH+.014*math.sin(y*4.7+k*2.1+ph[7])))
        n=.010*math.sin(x*23+ph[5])*math.sin(y*19+ph[6])+.006*math.sin(x*47+y*31)
        return (FUR+h*ry+n)*e
    _earth('VG01_Earth',W,D,zf,M['soil'],'Body')
    def row(tag,c,n,side,make,jx=.03,jy=.035):
        """the array: n plants along one line of a ridge (side: -1 / +1 of the ridge centre), each with its own random offset"""
        for i in range(n):
            y=-D/2+.34+(D-.68)*i/(n-1)+rr.uniform(-jy,jy);x=c+side*.165+rr.uniform(-jx,jx)+.025*math.sin(y*3.1)
            make(f'{tag}{"L" if side<0 else "R"}{i:02d}',Vector((x,y,zf(x,y)-.006)))
    # leafy greens: a rosette of broad leaves on pale stalks, outer leaves lying further out
    def green(name,b):
        sz=rr.uniform(.78,1.12);n=rr.randint(7,9);a0=rr.uniform(0,math.tau)
        for k in range(n):
            a=a0+math.tau*k/n+rr.uniform(-.25,.25);inner=k%2;L=sz*(rr.uniform(.20,.25) if not inner else rr.uniform(.15,.19))
            g=(k*.618+.3)%1;th=(.50+.45*g if not inner else .12+.30*g);dr=rr.uniform(.25,.5) if not inner else rr.uniform(.05,.2)
            Wd=L*rr.uniform(.62,.78);d=(math.cos(a),math.sin(a));bb=b+Vector((d[0]*(.020 if not inner else .008),d[1]*(.020 if not inner else .008),-.010-.003*k))
            _taper(f'{name}_S{k}',[_bladec(bb,d,L,th,dr,u) for u in (0,.2,.4,.62)],[.0085*sz,.0075*sz,.0055*sz,.0022],M['veg_stem'],'Body',sides=3,scale=.06,up=(-d[1],d[0],0))   # the pale stalk and midrib: it runs into the blade
            _blade(f'{name}_B{k}',bb,d,L,Wd,th,dr,lambda u:.10+.90*math.sin(math.pi*min(1,(u-.14)/.90))**.6 if u<.985 else .12,M['veg'],'Body',nu=6,nv=2,cup=rr.uniform(.15,.4),u0=.16,u1=1,twist=0.)
    for side in (-1,1):row('VG01_Green',CX[0],6,side,green)
    # radishes: a white shoulder standing out of the soil and a tuft of long lobed leaves
    def radish(name,b):
        sz=rr.uniform(.8,1.15);r=.030*sz;bz=b+Vector((0,0,-.012))
        _lathe(f'{name}_Root',[(0,r*.96),(.55,r),(.88,r*.95),(1,r*.84)],(bz,bz+Vector((rr.uniform(-.006,.006),rr.uniform(-.006,.006),.052*sz))),M['radish'],'Body',NS=9,scale=.08)
        n=rr.randint(6,7);a0=rr.uniform(0,math.tau);top=bz+Vector((0,0,.049*sz))
        for k in range(n):
            a=a0+math.tau*k/n+rr.uniform(-.07,.07);L=sz*rr.uniform(.15,.21);th=.30+.50*((k*.618+.2)%1);lob=rr.uniform(20,30);p0=rr.uniform(0,6)
            _blade(f'{name}_L{k}',top+Vector((math.cos(a)*r*.72,math.sin(a)*r*.72,-.004*k)),(math.cos(a),math.sin(a)),L,L*rr.uniform(.26,.34),th,rr.uniform(.2,.55),
                   lambda u,lob=lob,p0=p0:(.10+.90*math.sin(math.pi*min(1,u*1.02))**.55*(.70+.30*math.sin(u*lob+p0))) if u>.16 else .10,M['radish_leaf'],'Body',nu=9,nv=2,cup=.3,twist=rr.uniform(-.6,.6))
    for side in (-1,1):row('VG01_Radish',CX[1],6,side,radish)
    # spring onions: clumps of thin upright hollow leaves, a few tips bent over
    def onion(name,b):
        n=rr.randint(5,7);sz=rr.uniform(.8,1.1)
        for k in range(n):
            a=math.tau*k/n+rr.uniform(-.25,.25);off=Vector((math.cos(a),math.sin(a),0));L=sz*rr.uniform(.15,.20);lean=rr.uniform(.03,.20);bend=rr.random()<.22
            p0=b+off*rr.uniform(.013,.022)+Vector((0,0,-.016-.0035*k));ro=rr.uniform(0,math.tau);pts=[p0,p0+off*lean*L*.3+Vector((0,0,L*.4)),p0+off*lean*L*.7+Vector((0,0,L*.78)),p0+off*(lean*L+(L*.16 if bend else 0))+Vector((0,0,L*(.90 if bend else 1.)))]
            _taper(f'{name}_{k}',pts,[.0052*sz,.0048*sz,.0036*sz,.0009],M['scallion'],'Body',sides=4,scale=.06,up=(math.cos(ro),math.sin(ro),.3))
    for side in (-1,1):row('VG01_Onion',CX[2],9,side,onion,jy=.02)
    def edge(x,y):e=min(1.,(1-max(abs(x)/(W/2),abs(y)/(D/2)))/.15);return e*e*(3-2*e)
    # Detail_: a few small stones along the rim and weeds in the furrows (the standard tier hides them)
    for k in range(7):
        q=rr.uniform(-.62,.62);sd=rr.choice((-1,1));x,y=((q*W/2,sd*(D/2-.15)) if k%2 else (sd*(W/2-.15),q*D/2));s=rr.uniform(.05,.10)   # along the sides, not at the rounded corners
        _blob(f'VG01_Stone{k}',(s,s*rr.uniform(.7,1),s*rr.uniform(.45,.7)),4110+k,M['stone'],'Detail_Stones',sub=2,scale=.2).data.transform(Matrix.Translation((x,y,max(0,zf(x,y)*edge(x,y)-.024)+.004)))
    for k in range(10):
        c=rr.choice((-.45,.45));x=c+rr.uniform(-.05,.05);y=rr.uniform(-D/2+.2,D/2-.2);b=Vector((x,y,zf(x,y)-.014))
        for q in range(4):
            a=math.tau*q/4+rr.uniform(-.5,.5);_blade(f'VG01_Weed{k}_{q}',b+Vector((math.cos(a)*.008,math.sin(a)*.008,0)),(math.cos(a),math.sin(a)),rr.uniform(.06,.10),.012,rr.uniform(.15,.55),.2,lambda u:math.sin(math.pi*min(1,u+.08))**.8,M['radish_leaf'],'Detail_Weeds',nu=3,nv=1,cup=.3)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        soil=filled*(mid>.5)
        fur=soil*np.clip((.085-pz)/.04,0,1)*np.clip(onrm[...,2],0,1)       # the trodden furrows and the rim: drier and paler
        col=col*(1-.22*soil[...,None]);col=col*(1-fur[...,None])+fur[...,None]*(col*1.30+np.array([.030,.024,.014]));rough=np.clip(rough+.05*fur,0,1)
        top=soil*np.clip((pz-.13)/.05,0,1)*np.clip((noise-.3)*2,0,1)        # freshly worked ridge tops: a little darker and damp
        col=col*(1-.18*top[...,None]);rough=np.clip(rough-.10*top,0,1)
        return col,rough
    M['soil']['mid']=1.
    return {'paint':paint,'wear':.3,'grime':.5,'ao_k':.55,'uv_angle':60,
            'collision':'box 2.8 × 1.9 × 0.2 m on the earth (the plants are not solid); the player walks round the plot',
            'notes':['three ridges on one piece of earth: rounded tops, trodden furrows, a ragged rim down to the ground; no fence or stone wall',
                     'each crop is one recipe repeated along its ridge with random size, leaf count, lean and turn (12 greens, 12 radishes, 18 onion clumps)',
                     'Detail_Stones (7 small stones on the rim) and Detail_Weeds (10 weeds in the furrows) are off at the standard tier']}
PROPS['VG01']=VG01

# ---------------- VG02 bamboo gourd trellis with a vine and three hanging gourds (cand-4) ----------------
def _bcane(name,a,b,r0,r1,mat,grp,gap=.26,sides=8,bow=0.,bowdir=(0,0,1),ph=0.):
    """a bamboo pole from a to b with few rings: at every node a short raised ring (three sections), straight between;
    radius r0 → r1, the pole bowed a little towards bowdir"""
    a,b=Vector(a),Vector(b);L=(b-a).length;bd=Vector(bowdir);ss=[0.];s=gap*(.35+.5*ph)
    while s<L-.04:ss+=[s-.012,s,s+.012];s+=gap*(1+.12*math.sin(s*7+ph*9))
    ss.append(L);pts=[];rad=[]
    for i,s in enumerate(ss):
        u=s/L;pts.append(a.lerp(b,u)+bd*bow*math.sin(math.pi*u));r=r0+(r1-r0)*u
        rad.append(r*1.16 if (0<i<len(ss)-1 and (i-1)%3==1) else r)
    return _taper(name,pts,rad,mat,grp,sides=sides,scale=.3)
def _xlash(name,c,a,b,R,mat,grp,cord=.0032):
    """a cross lashing where two poles (directions a, b) meet at c: two cord loops over the crossing, one on each diagonal"""
    a,b=Vector(a).normalized(),Vector(b).normalized()
    for k,ax in enumerate((a+b,a-b)):
        _ring(f'{name}_{k}',Vector(c),ax,R,cord,mat,grp,n=9)
def _leafcard(name,base,d,n,size,cell,mat,grp,cup=.12,droop=.25):
    """a leaf drawn on a card (alpha clip): a 2 × 2 patch growing from `base` along d, facing n, cupped across and drooping
    towards its tip; cell: the sprite's rectangle in the card strip (u0, v0, u1, v1)"""
    d=Vector(d).normalized();n=Vector(n);s=d.cross(n).normalized();n=s.cross(d).normalized();base=Vector(base)
    rows=[[tuple(base+d*size*(i/2)+s*size*(j/2-.5)+n*size*(cup*(j-1)**2-droop*(i/2)**2)) for j in range(3)] for i in range(3)]
    return _surf(name,rows,mat,grp,scale=.3,card=cell)
def _sprites(W_,H_,cells):
    """paint the card strip: cells = [(u0, u1, kind, seed)], kind 'leaf' (a five-lobed gourd leaf, stem at the bottom
    centre) or 'flower' (five yellow petals); returns rgb, alpha"""
    rgb=np.zeros((H_,W_,3),np.float32);al=np.zeros((H_,W_),np.float32)
    for u0,u1,kind,seed in cells:
        x0,x1=int(u0*W_),int(u1*W_);w=x1-x0;r=np.random.default_rng(seed)
        xx=(np.arange(w)[None,:]+.5)/w*2-1;yy=(np.arange(H_)[:,None]+.5)/H_      # x -1..1 across, y 0 (stem) .. 1 (tip)
        if kind=='leaf':
            cy=.50;dx=xx;dy=(yy-cy)*2;rad=np.hypot(dx,dy);th=np.arctan2(dx,dy)      # th = 0 towards the tip
            lob=.84+.065*np.cos(5*th)+.025*np.cos(15*th+r.uniform(0,6))+.03*np.sin(3*th+r.uniform(0,6))
            notch=1-.55*np.exp(-((np.abs(th)-math.pi)/.32)**2)                      # the heart-shaped cut at the stem
            R=lob*notch;a=(rad<R)|((np.abs(dx)<.045)&(yy<cy)&(yy>.02))              # blade, and the leaf stalk down to the base
            vein=np.zeros_like(rad)
            for va in (0,.62,-.62,1.25,-1.25,1.95,-1.95):
                dth=np.abs(np.arctan2(np.sin(th-va),np.cos(th-va)));vein=np.maximum(vein,np.clip(1-dth*rad/.035,0,1)*np.clip(1-rad/R.clip(.01)*.95,0,1)**.3)
            t=np.clip(.55-.35*rad/R.clip(.01)+.25*r.uniform(-1,1)+.2*np.sin(dx*7+dy*5+seed),0,1)
            dark=np.array([.13,.26,.08]);light=np.array([.40,.55,.17]);edge=np.clip((rad/R.clip(.01)-.72)/.28,0,1)
            c=dark[None,None,:]*(1-t[...,None])+light[None,None,:]*t[...,None]
            c=c*(1-.5*edge[...,None])+edge[...,None]*.5*np.array([.55,.56,.18])     # the rim going yellow
            c=c*(1-.6*vein[...,None])+vein[...,None]*.6*np.array([.62,.72,.36])
            if seed%3==0:c=c*.55+.45*np.array([.62,.55,.20])                         # an older, yellowing leaf
        else:
            dx=xx;dy=(yy-.5)*2;rad=np.hypot(dx,dy);th=np.arctan2(dx,dy);R=.55+.33*np.abs(np.cos(2.5*th));a=rad<R
            c=np.array([.92,.74,.14])[None,None,:]*(1-.35*np.clip(rad/R,0,1)[...,None]**2)+np.clip(.25-rad,0,1)[...,None]*np.array([.2,-.1,-.1])
        rgb[:,x0:x1]=np.where(a[...,None],c,np.array([.30,.42,.14]));al[:,x0:x1]=a   # outside the shape: leaf colour (no pale fringe after mip-mapping), alpha 0
    return rgb,al
def VG02(M):
    """four bamboo posts set in the ground; a top frame of two long beams and two cross beams, five thin rafters across
    and three laths along; a diagonal brace at each post and two rungs on each end; every joint is lashed with cord
    (two loops on each diagonal). A gourd vine climbs two posts and wanders over the top; leaves and flowers are cards
    (alpha clip); three bottle gourds of different sizes hang under the frame."""
    rr=random.Random(4202);PX,PY,H=.88,.48,1.63;B=M['bamboo'];BO=M['bamboo_old'];H2=M['hemp']
    posts=[(sx*PX,sy*PY) for sx in (-1,1) for sy in (-1,1)];lean={}
    for k,(x,y) in enumerate(posts):
        top=Vector((x+rr.uniform(-.025,.025),y+rr.uniform(-.02,.02),H+.10));lean[k]=(Vector((x,y,0)),top)
        _bcane(f'VG02_Post{k}',(x,y,0),top,.034,.029,BO,'Body',gap=.30,sides=9,ph=rr.random())
    def pp(k,z):a,b=lean[k];return a.lerp(b,(z-a.z)/(b.z-a.z))
    zb=H-.02     # long beams (along X) lie against the outside of the posts; cross beams (along Y) sit on them
    for q,sy in enumerate((-1,1)):
        y=sy*(PY+.058);_bcane(f'VG02_Beam{q}',(-PX-.17,y,zb+rr.uniform(-.01,.01)),(PX+.17,y,zb+rr.uniform(-.01,.01)),.027,.023,B,'Body',gap=.33,ph=rr.random(),bow=-.012)
        for sx in (-1,1):
            k=[i for i,p in enumerate(posts) if p==(sx*PX,sy*PY)][0];_xlash(f'VG02_LashB{q}{sx+1}',pp(k,zb)+Vector((0,sy*.03,0)),(1,0,0),(0,0,1),.047,H2,'Body')
    zc=zb+.050
    for q,sx in enumerate((-1,1)):
        x=sx*(PX+.060);_bcane(f'VG02_Cross{q}',(x,-PY-.22,zc),(x,PY+.22,zc),.025,.022,B,'Body',gap=.31,ph=rr.random(),bow=-.008)
        for sy in (-1,1):_xlash(f'VG02_LashC{q}{sy+1}',(x,sy*(PY+.058),zc-.025),(1,0,0),(0,1,0),.040,H2,'Body')
    zr=zb+.048;RX=(-.62,-.31,0.,.31,.62);RAF=[]
    for q,x in enumerate(RX):
        x1=x+rr.uniform(-.03,.03);RAF.append((x,x1));_bcane(f'VG02_Rafter{q}',(x,-PY-.20,zr+rr.uniform(-.004,.004)),(x1,PY+.20,zr),.017,.014,B,'Body',gap=.27,sides=7,ph=rr.random(),bow=-.010)
        for sy in (-1,1):_xlash(f'VG02_LashR{q}{sy+1}',(x,sy*(PY+.058),zr-.022),(1,0,0),(0,1,0),.032,H2,'Body',cord=.0028)
    zl=zr+.030
    for q,y in enumerate((-.30,.02,.32)):
        _bcane(f'VG02_Lath{q}',(-PX-.12,y,zl),(PX+.12,y+rr.uniform(-.03,.03),zl+rr.uniform(-.004,.004)),.013,.011,BO,'Body',gap=.25,sides=6,ph=rr.random(),bow=-.006)
        for j,x in enumerate((RX[0],RX[2],RX[4])):_xlash(f'VG02_LashL{q}{j}',(x,y,zl-.013),(1,0,.15),(0,1,.1),.0275,H2,'Body',cord=.0026)
    for k,(x,y) in enumerate(posts):   # a brace from each post up to its long beam, a rung pair on each end
        sx=1 if x>0 else -1;sy=1 if y>0 else -1;a=pp(k,H-.50)+Vector((0,sy*.030,0));b=Vector((x-sx*.46,sy*(PY+.030),zb-.030))
        _bcane(f'VG02_Brace{k}',a-(b-a).normalized()*.06,b+(b-a).normalized()*.07,.017,.015,B,'Body',gap=.24,sides=7,ph=rr.random())
        _xlash(f'VG02_LashBrA{k}',a,(b-a),(0,0,1),.036,H2,'Body',cord=.0028);_xlash(f'VG02_LashBrB{k}',b+Vector((0,sy*.012,.018)),(b-a),(1,0,0),.034,H2,'Body',cord=.0028)
    for q,sx in enumerate((-1,1)):
        ka=[i for i,p in enumerate(posts) if p==(sx*PX,-PY)][0];kb=[i for i,p in enumerate(posts) if p==(sx*PX,PY)][0]
        for j,z in enumerate((.62,1.20)):
            a=pp(ka,z)+Vector((sx*.045,0,0));b=pp(kb,z+rr.uniform(-.02,.02))+Vector((sx*.045,0,0));d=(b-a).normalized()
            _bcane(f'VG02_Rung{q}{j}',a-d*.10,b+d*.10,.018,.016,B,'Body',gap=.26,sides=7,ph=rr.random())
            _xlash(f'VG02_LashRuA{q}{j}',a-Vector((sx*.022,0,0)),d,(0,0,1),.040,H2,'Body',cord=.0028);_xlash(f'VG02_LashRuB{q}{j}',b-Vector((sx*.022,0,0)),d,(0,0,1),.040,H2,'Body',cord=.0028)
    # the vine: up two posts in a loose spiral, then wandering over the top; leaves on cards along it
    CELL=[(.005,.02,.245,.98),(.255,.02,.495,.98),(.505,.02,.745,.98)];FLOWER=(.760,.05,.990,.95);V=M['vine'];nl=[0]
    def leaves(path,every,size,up_bias,hang=False):
        acc=0.
        for a,b in zip(path,path[1:]):
            acc+=(b-a).length
            if acc<every:continue
            acc=rr.uniform(-.03,.03);tg=(b-a).normalized();side=Vector((rr.uniform(-1,1),rr.uniform(-1,1),rr.uniform(-.15,.15)));side=(side-tg*side.dot(tg)).normalized()
            n=(Vector((rr.uniform(-.5,.5),rr.uniform(-.5,.5),1.))*up_bias+side.cross(tg)*(1-up_bias)).normalized()
            if hang:
                rad_=Vector((a.x,a.y,0)).normalized();n=(rad_+Vector((0,0,.45))+Vector((rr.uniform(-.3,.3),rr.uniform(-.3,.3),0))).normalized();side=(Vector((rr.uniform(-.6,.6),rr.uniform(-.6,.6),-1))).normalized()
            _leafcard(f'VG02_Leaf{nl[0]:03d}',a-side*.012,side,n,size*rr.uniform(.75,1.2),CELL[nl[0]%3],M['veg'],'Body',cup=rr.uniform(.05,.16),droop=rr.uniform(.1,.35));nl[0]+=1
    for q,k in enumerate((0,3)):
        pts=[];turns=2.3+q*.4;a0=rr.uniform(0,6)
        for i in range(40):
            u=i/39;z=.02+u*(H+.02);c=pp(k,z);ang=a0+turns*math.tau*u;pts.append(c+Vector((math.cos(ang),math.sin(ang),0))*(.040+.006*math.sin(u*31)))
        tube(f'VG02_VinePost{q}',pts,.0075,V,'Body',sides=5,scale=.1);leaves(pts,.20,.21,.3,hang=True)
    for q,(y0,amp,phs) in enumerate(((-.36,.06,0.),(-.13,.09,2.),(.12,.09,4.),(.36,.06,1.))):
        pts=[Vector((x,y0+amp*math.sin(x*3.1+phs)+.04*math.sin(x*9+phs),zl+.020+.012*math.sin(x*14+phs))) for x in np.linspace(-PX-.02,PX+.02,44)]
        tube(f'VG02_VineTop{q}',pts,.0065,V,'Body',sides=5,scale=.1);leaves(pts,.078,.29,.92)
    for q,(x,y) in enumerate(((-.48,-.30),(.30,.32),(.66,.02),(-.10,.02))):   # four yellow flowers standing a little above the leaves
        b=Vector((x,y,zl-.004));_rod(f'VG02_FlowerStem{q}',b,b+Vector((0,0,.060)),.003,V,'Body',sides=4,scale=.05)
        _leafcard(f'VG02_Flower{q}',b+Vector((-.045,0,.057)),(1,0,0),(rr.uniform(-.2,.2),rr.uniform(-.2,.2),1),.09,FLOWER,M['veg'],'Body',cup=.10,droop=-.15)
    # three bottle gourds of different sizes hanging on short stems from the rafters
    for q,(ri,y,sz) in enumerate(((1,-.16,1.0),(2,.20,.70),(3,-.05,.52))):
        x=RAF[ri][0]+(RAF[ri][1]-RAF[ri][0])*(y+PY+.20)/(2*PY+.40)
        hang=.20+.05*q;t0=Vector((x,y,zr-.012));g0=t0+Vector((rr.uniform(-.015,.015),rr.uniform(-.015,.015),-hang));Lg=.40*sz;g1=g0+Vector((rr.uniform(-.01,.01),rr.uniform(-.01,.01),-Lg))
        tube(f'VG02_GourdStem{q}',[t0+Vector((0,0,.03)),t0+Vector((.01,0,-.03)),g0.lerp(t0,.4)+Vector((.006,.004,0)),g0+Vector((0,0,-.012))],.0058,V,'Body',sides=5,scale=.08)
        prof=[(0,.012),(.04,.024),(.14,.070),(.24,.092),(.33,.074),(.40,.060),(.48,.078),(.62,.150),(.76,.172),(.88,.140),(.96,.072),(1,0)]
        _lathe(f'VG02_Gourd{q}',[(s,r*sz*.95) for s,r in prof],(g0,g1),M['gourd_green'],'Body',NS=16,scale=.25)
    def pattern(W_,H_):return _sprites(W_,H_,[(.0,.25,'leaf',11),(.25,.5,'leaf',14),(.5,.75,'leaf',12),(.75,1.,'flower',5)])
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];pz=P[...,2]
        ft=filled*np.clip((.30-pz)/.28,0,1)*np.clip((noise-.35)*2.5,0,1)      # damp, mossy feet where the posts stand in the ground
        col=col*(1-.35*ft[...,None])+ft[...,None]*np.array([.07,.10,.04]);rough=np.clip(rough+.1*ft,0,1)
        return col,rough
    return {'paint':paint,'wear':.8,'grime':.9,'uv_angle':50,'card':{'strip':.22,'pattern':pattern,'alpha':True},
            'notes':['bamboo poles with raised nodes; every joint is lashed with cord (two loops on each diagonal of the crossing), nothing nailed',
                     'the vine stems and the three gourds are modelled; the leaves (three sprites) and four flowers are cards drawn in the top 22 % of the atlas, alpha clip: turn on Mip Maps Preserve Coverage for the albedo in Unity',
                     'the posts go into the ground (no base stones); no cloth wraps']}
PROPS['VG02']=VG02
