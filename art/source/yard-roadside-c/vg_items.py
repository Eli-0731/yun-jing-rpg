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
            'collision_box':((2.60,1.70,.17),(0,0,.085)),'collision':'one box over the earth (the plants are not solid): the player walks round the plot',
            'notes':['three ridges on one piece of earth: rounded tops, trodden furrows, a ragged rim down to the ground; no fence or stone wall',
                     'each crop is one recipe repeated along its ridge with random size, leaf count, lean and turn (12 greens, 12 radishes, 18 onion clumps)',
                     'Detail_Stones (7 small stones on the rim) and Detail_Weeds (10 weeds in the furrows) are off at the standard tier']}
PROPS['VG01']=VG01

# ---------------- VG02 bamboo gourd trellis with a vine and three hanging gourds (cand-4) ----------------
def _bcane(name,a,b,r0,r1,mat,grp,gap=.26,sides=8,bow=0.,bowdir=(0,0,1),ph=0.,bulge=1.16):
    """a bamboo pole from a to b with few rings: at every node a short raised ring (three sections), straight between;
    radius r0 → r1, the pole bowed a little towards bowdir"""
    a,b=Vector(a),Vector(b);L=(b-a).length;bd=Vector(bowdir);ss=[0.];s=gap*(.35+.5*ph)
    while s<L-.04:ss+=[s-.012,s,s+.012];s+=gap*(1+.12*math.sin(s*7+ph*9))
    ss.append(L);pts=[];rad=[]
    for i,s in enumerate(ss):
        u=s/L;pts.append(a.lerp(b,u)+bd*bow*math.sin(math.pi*u));r=r0+(r1-r0)*u
        rad.append(r*bulge if (0<i<len(ss)-1 and (i-1)%3==1) else r)
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

# ---------------- VG03 clothes-drying pole: two forked posts, a bamboo pole, a jacket and a pair of trousers (cand-4) ----------------
def _drape(name,x0,x1,zc,rp,front,back,mat,grp,seed,t=.0045,amp=.022,flare=0.,kx=17.,side_drop=0.):
    """a piece of cloth hung over a pole running along X (centre height zc, radius rp): it goes up the back, over the pole
    and down the front; front / back: the hanging lengths (a number, or a function of u = 0..1 across). Its weight pulls
    it into vertical folds that deepen towards the hem, the hem waves, the sides hang a little lower (side_drop).
    Returns the object and the two hem polylines (front, back)."""
    r_=random.Random(seed);ph=[r_.uniform(0,6.28) for _ in range(6)];g=rp*1.06+t/2+.0005;gt=rp+t/2-.0008;nx=max(4,int(round((x1-x0)/.036)))
    rows=[];hf=[];hb=[];nb=max(3,int((back(.5) if callable(back) else back)/.055));nf=max(3,int((front(.5) if callable(front) else front)/.055))
    for i in range(nx+1):
        u=i/nx;x=x0+(x1-x0)*u;lf=(front(u) if callable(front) else front);lb=(back(u) if callable(back) else back)
        e=side_drop*(2*u-1)**2;lf=lf*(1+.025*math.sin(u*9+ph[0]))+e;lb=lb*(1+.03*math.sin(u*7+ph[1]))+e
        def fold(d,L,sg):   # the fold depth at drop d of a flap of length L
            q=min(1.,d/max(L,1e-6));return amp*q**1.3*(math.sin(x*kx+ph[2]+sg)+.5*math.sin(x*kx*2.3+ph[3]+sg*2))
        row=[]
        for j in range(nb,0,-1):d=lb*j/nb;q=d/lb;row.append((x+flare*(2*u-1)*q+.006*math.sin(q*5+ph[4]+x*3),g+.006*q+fold(d,lb,1.7),zc-d))
        for a in np.linspace(0,math.pi,7):row.append((x,g*math.cos(a),zc+(g+(gt-g)*math.sin(a)**2)*math.sin(a)))   # its weight presses it onto the top of the pole
        for j in range(1,nf+1):d=lf*j/nf;q=d/lf;row.append((x+flare*(2*u-1)*q+.006*math.sin(q*5+ph[5]+x*3),-g-.006*q-fold(d,lf,0.),zc-d))
        rows.append(row);hb.append(Vector(row[0]));hf.append(Vector(row[-1]))
    n0=min(len(r) for r in rows);assert all(len(r)==n0 for r in rows),'_drape: the flap lengths must give the same row count'
    return _sheet(name,rows,None,None,mat,grp,t=t),hf,hb
def _fringe(name,hem,nrm,mat,grp,cells,h=.05,seed=0,step=2):
    """a ragged, frayed edge below a hem: a row of cards (alpha clip) hanging from the hem polyline, each showing one of
    the ragged-edge sprites; the card starts 4 mm above the hem so it runs into the cloth"""
    r_=random.Random(seed);n=Vector(nrm)
    for k in range(0,len(hem)-step,step):
        a,b=hem[k],hem[k+step];hh=h*r_.uniform(.7,1.15);up=Vector((0,0,.004));off=n*0.
        rows=[[tuple(a-Vector((0,0,hh))+off),tuple(b-Vector((0,0,hh))+off)],[tuple(a+up+off),tuple(b+up+off)]]
        _surf(f'{name}{k:02d}',rows,mat,grp,scale=.3,card=cells[r_.randrange(len(cells))])
def _rags(W_,H_,cells,base):
    """the ragged hem sprites: cloth colour above a torn edge with a few loose threads; cells = [(u0, u1, seed)]"""
    rgb=np.zeros((H_,W_,3),np.float32);al=np.zeros((H_,W_),np.float32)
    for u0,u1,seed in cells:
        x0,x1=int(u0*W_),int(u1*W_);w=x1-x0;r=np.random.default_rng(seed);xx=(np.arange(w)[None,:]+.5)/w;yy=(np.arange(H_)[:,None]+.5)/H_
        edge=.55+.16*np.sin(xx*math.tau*1.5+r.uniform(0,6))+.10*np.sin(xx*math.tau*4+r.uniform(0,6))+.06*np.sin(xx*math.tau*9+r.uniform(0,6))
        a=yy>edge
        for _ in range(7):   # loose threads hanging below the tear
            cx=r.uniform(.05,.95);L=r.uniform(.15,.45);wob=.02*np.sin(yy*30+r.uniform(0,6));e0=.55+.16*np.sin(cx*math.tau*1.5)
            a|=(np.abs(xx-cx-wob)<.012)&(yy>e0-L)&(yy<e0+.1)
        tone=.80+.20*yy+.06*np.sin(xx*40+seed)
        rgb[:,x0:x1]=np.asarray(base)[None,None,:]*tone[...,None];al[:,x0:x1]=a
    return rgb,al
def VG03(M):
    """two posts of natural crooked timber forked at the top, set in the ground; a bamboo pole lies in the two crotches and
    is tied down; a jacket hangs with its sleeves threaded on the pole, a pair of trousers is folded over it. The cloth
    hangs in folds that deepen towards the hems (the practice point); the hems are frayed (alpha clip cards)."""
    rr=random.Random(4303);ZC=1.475;RP=.021;PXs=(-1.09,1.09);W1=M['cedar_b']
    for q,px in enumerate(PXs):
        sg=1 if px>0 else -1;c=[Vector((px+sg*.03,0,-0.0)),Vector((px+sg*.012,.012*sg,.45)),Vector((px-sg*.010,-.010*sg,.95)),Vector((px,0,ZC-.085))]
        _taper(f'VG03_Post{q}',c,[.052,.048,.044,.041],W1,'Body',sides=9,scale=.3)
        for j,sy in enumerate((-1,1)):   # the fork: two limbs leaving the trunk below the pole and passing either side of it
            a=c[-1]+Vector((0,0,-.03));b=Vector((px+sg*.02*j,sy*.060,ZC+.02));e=Vector((px+sg*(.03 if j else -.02),sy*(.115+.02*j),ZC+.30+.05*j))
            _taper(f'VG03_Fork{q}{j}',[a,a.lerp(b,.6)+Vector((0,sy*.012,0)),b,b.lerp(e,.55)+Vector((0,sy*.006,0)),e],[.036,.033,.030,.027,.024],W1,'Body',sides=8,scale=.3)
        for j in range(3):_ring(f'VG03_Tie{q}{j}',(px+(j-1)*.013,(j-1)*.004,ZC-.012),(.25*(j-1),1,0),.050+.003*j,.0042,M['hemp'],'Body',n=13,wob=.003)   # cord over the pole and under the crotch
        _ring(f'VG03_TieX{q}',(px,0,ZC-.11),(0,0,1),.047,.0042,M['hemp'],'Body',n=13)
    _bcane('VG03_Pole',(-1.27,0,ZC),(1.27,0,ZC),RP,RP,M['bamboo'],'Body',gap=.30,sides=12,ph=.4,bow=0.,bulge=1.06)   # straight and even: the cloth lies on its nodes
    CEL=[(.01,.03,.32,.97),(.34,.03,.65,.97),(.67,.03,.99,.97)];L1=M['linen'];L2=M['linen_b'];zc=ZC
    # the jacket: body and two sleeves, each a piece hung over the pole
    jx=-.37
    o,hf,hb=_drape('VG03_JacketBody',jx-.30,jx+.30,zc,RP,.74,.72,L1,'Body',4310,amp=.062,kx=15.,flare=-.035,side_drop=.035)
    _fringe('VG03_JacketHemF',hf,(0,-1,0),M['linen'],'Body',CEL,seed=1);_fringe('VG03_JacketHemB',hb,(0,1,0),M['linen'],'Body',CEL,seed=2)
    for q,sg in enumerate((-1,1)):
        a,b=sorted((jx+sg*.295,jx+sg*.585))
        fl=(lambda u,sg=sg:.30+.09*(u if sg>0 else 1-u))   # the sleeve widens a little to its cuff
        o,hf,hb=_drape(f'VG03_Sleeve{q}',a,b,zc,RP+.004,fl,fl,L1,'Body',4320+q,amp=.034,kx=19,side_drop=.02)
        _fringe(f'VG03_SleeveHem{q}',hf,(0,-1,0),M['linen'],'Body',CEL,h=.035,seed=3+q)
    # the trousers: folded over the pole at the waist; in front the two legs hang side by side
    tx=.42
    for q,sg in enumerate((-1,1)):
        a,b=sorted((tx+sg*.012,tx+sg*.235))
        o,hf,hb=_drape(f'VG03_Leg{q}',a,b,zc,RP,.80+.03*q,.25,L2,'Body',4330+q,amp=.046,kx=19,flare=.012*sg,side_drop=.015)
        _fringe(f'VG03_LegHem{q}',hf,(0,-1,0),M['linen_b'],'Body',CEL,seed=6+q)
    def pattern(W_,H_):return _rags(W_,H_,[(.0,.333,3),(.333,.667,5),(.667,1.,8)],(.60,.55,.45))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        cloth=filled*(mid>.5)
        fade=cloth*np.clip((ZC-.15-pz)/.6,0,1);col=col*(1-.10*fade[...,None])                      # dirtier towards the hems
        band=cloth*(py<0)*(np.abs(px-(jx-.02+.05*(ZC-pz)))<.022)*(pz>ZC-.56)*(pz<ZC-.03);col=col*(1-.22*band[...,None])   # the collar band down the front opening (painted)
        for (cx,cz,w,h,tint) in ((jx+.10,ZC-.52,.12,.10,(.50,.47,.42)),(tx-.11,ZC-.50,.10,.12,(.47,.48,.50))):   # two sewn patches on the front
            dxp=np.abs(px-cx)/(w/2);dzp=np.abs(pz-cz)/(h/2);ins=cloth*(py<0)*(np.maximum(dxp,dzp)<1);rim=ins*(np.maximum(dxp,dzp)>.86)
            st=rim*(np.sin((px+pz)*260)>0)                                                          # running stitches round the patch
            col=col*(1-ins[...,None])+ins[...,None]*(np.array(tint)*(.85+.3*noise[...,None]));col=col*(1-.55*st[...,None])
        ft=filled*(1-cloth)*np.clip((.30-pz)/.28,0,1)*np.clip((noise-.35)*2.5,0,1)                  # mossy feet of the posts
        col=col*(1-.35*ft[...,None])+ft[...,None]*np.array([.07,.10,.04])
        return col,rough
    for k in ('linen','linen_b'):M[k]['mid']=1.
    return {'paint':paint,'wear':.7,'grime':.6,'ao_k':.4,'uv_angle':60,'card':{'strip':.10,'pattern':pattern,'alpha':True},
            'notes':['two forked posts of crooked natural timber set in the ground; the bamboo pole lies in the crotches and is tied with cord',
                     'the jacket hangs with its sleeves on the pole, the trousers are folded over it; the folds deepen towards the hems and are in the shape, not only in the normal map',
                     'frayed hems are cards in the top 10 % of the atlas (alpha clip): turn on Mip Maps Preserve Coverage for the albedo in Unity; the two patches are painted',
                     'no cloth wraps or boards on the posts']}
PROPS['VG03']=VG03

# ---------------- VG04 rice-straw haystacks: _01 complete, _02 with one side pulled away (cand-3) ----------------
def _straw_fringe(W_,H_,cells):
    """the straw fringe sprites: a solid band of straw at the top breaking into separate strands of uneven length;
    cells = [(u0, u1, seed)]"""
    rgb=np.zeros((H_,W_,3),np.float32);al=np.zeros((H_,W_),np.float32)
    for u0,u1,seed in cells:
        x0,x1=int(u0*W_),int(u1*W_);w=x1-x0;r=np.random.default_rng(seed);xx=(np.arange(w)[None,:]+.5)/w;yy=(np.arange(H_)[:,None]+.5)/H_
        a=(yy>.80)&(xx>-1);shade=np.zeros((H_,w),np.float32)+.5
        for _ in range(26):
            cx=r.uniform(.02,.98);L=r.uniform(.25,.80)*(1 if r.random()<.75 else 1.2);wd=r.uniform(.012,.028);lean=r.uniform(-.10,.10)
            xs=cx+lean*(.85-yy)+.01*np.sin(yy*14+r.uniform(0,6));m=(np.abs(xx-xs)<wd*np.clip((yy-(.85-L))/.25,.25,1))&(yy>.85-L)&(yy<.9)
            a|=m;shade=np.where(m,r.uniform(.25,1.),shade)
        c=np.array([.46,.37,.19])[None,None,:]*(1-shade[...,None])+np.array([.80,.68,.40])[None,None,:]*shade[...,None]
        rgb[:,x0:x1]=np.where(a[...,None],c*(.75+.25*yy[...,None]),np.array([.62,.52,.30]));al[:,x0:x1]=a
    return rgb,al
def _haystack(M,pid,seed,pulled):
    """a rounded, slightly lopsided dome of rice straw round a centre pole: a solid core, six overlapping skirts of
    thatch whose lower rims are jagged in the shape, a fringe of loose strands under every rim (alpha clip cards), a small
    straw cap tied round the pole. pulled: one side of the lower half has been pulled away, the hollow shows the bundles
    the stack is built from, and loose straw lies in front of it."""
    rr=random.Random(seed);NS=48;ph=[rr.uniform(0,6.28) for _ in range(8)];TH0=-1.05;HAY=M['hay'];OLD=M['hay_old']
    ZP=[0,.25,.55,.90,1.25,1.55,1.80,1.98,2.07];RP_=[.78,.84,.86,.81,.70,.55,.36,.19,.06]
    def cav(th,z):
        if not pulled:return 0.
        d=abs(math.atan2(math.sin(th-TH0),math.cos(th-TH0)));a=max(0.,min(1.,(.78-d)/.30));a=a*a*(3-2*a);b=max(0.,min(1.,(1.18-z)/.22));b=b*b*(3-2*b);return a*b
    def Rf(th,z):
        r=float(np.interp(z,ZP,RP_));lump=1+.045*math.sin(2*th+ph[0])+.035*math.sin(3*th+ph[1]+z*1.3)+.02*math.sin(5*th+ph[2]-z*2)
        return r*lump*(1-.52*cav(th,z))
    def surf(name,zs,rfun,mat,grp,close=None,vscale=.5):
        """rings round Z at the heights zs(th) → a surface with the straw running down it (Tiled: u round, v down)"""
        bm=bmesh.new();lay=bm.loops.layers.uv.new('Tiled');R_=[]
        for i in range(len(zs)):
            ring=[]
            for k in range(NS):
                th=math.tau*k/NS;z=zs[i](th,k) if callable(zs[i]) else zs[i];r=rfun(th,z,i,k);ring.append(bm.verts.new((r*math.cos(th),r*math.sin(th),z)))
            R_.append(ring)
        du=rr.random();dv=rr.random()
        for i in range(len(zs)-1):
            for k in range(NS):
                q=(R_[i][k],R_[i][(k+1)%NS],R_[i+1][(k+1)%NS],R_[i+1][k]);f=bm.faces.new(q);f.smooth=True
                for l,(kk,ii) in zip(f.loops,((k,i),(k+1,i),(k+1,i+1),(k,i+1))):
                    v=R_[ii][kk%NS].co;l[lay].uv=(kk/NS*5.6/vscale*.5+du,-v.z/vscale+dv+.25*Vector((v.x,v.y)).length/vscale)
        if close:
            if 'top' in close:
                c=bm.verts.new((0,0,max(v.co.z for v in R_[0])+.03))
                for k in range(NS):bm.faces.new((c,R_[0][(k+1)%NS],R_[0][k]))
            if 'bottom' in close:bm.faces.new(list(R_[-1]))
        RC=[[v.co.copy() for v in ring] for ring in R_];return finish(name,bm,mat,grp,vscale,keep_uv=True),RC
    # the core: closed, a little inside the thatch
    surf(f'{pid}_Core',[2.02,1.90,1.70,1.45,1.15,.85,.55,.28,0.],lambda th,z,i,k:max(.03,Rf(th,z)-.035),OLD,'Body',close=('top','bottom'))
    CEL=[(.005,.03,.325,.97),(.338,.03,.658,.97),(.671,.03,.995,.97)];nc=[0]
    LAY=[(.60,.015),(.98,.44),(1.34,.84),(1.63,1.20),(1.87,1.50),(2.06,1.78)]
    for q,(zt,zb) in enumerate(LAY):
        jz=[rr.uniform(-.035,.025) for _ in range(NS)];jr=[rr.uniform(0,.045) for _ in range(NS)];low=q==0;tp=rr.uniform(0,6.28);ta=rr.uniform(.03,.07)   # each skirt sits a little askew
        def zrow(s):return (lambda th,k,s=s:zt+(zb-.07*(not low)-zt)*s+(jz[k]*s*s if not low else abs(jz[k])*.4*s*s)+(ta*math.sin(th+tp)+.025*math.sin(3*th+tp*2))*(s if low else 1.)*(0. if low else 1.))
        def rfun(th,z,i,k,q=q):s=i/4;return Rf(th,z)+.012-.075*(1-s)**2+(.075+.03*math.sin(2*th+tp))*s*s+jr[k]*s*s+(.034 if q%2 else 0)
        o,R_=surf(f'{pid}_Thatch{q}',[zrow(s) for s in (0,.25,.5,.75,1.)],rfun,HAY,'Body',vscale=.5)
        rim=list(R_[-1])
        for k in range(0,NS,2):   # the fringe under this rim
            a,b=rim[k],rim[(k+2)%NS];m=(a+b)/2;out=Vector((m.x,m.y,0)).normalized();hh=rr.uniform(.13,.21)
            dn=(out*(.10 if low else .05)+Vector((0,0,-1))*(.012 if low else 1.)).normalized()*(hh*(.6 if low else 1.))
            lo_a=a+dn;lo_b=b+dn;lo_a.z=max(lo_a.z,.004+.002*(k%4));lo_b.z=max(lo_b.z,.004+.002*(k%4))
            _surf(f'{pid}_Fringe{q}_{k:02d}',[[tuple(lo_a),tuple(lo_b)],[tuple(a),tuple(b)]],HAY,'Body',scale=.3,card=CEL[nc[0]%3]);nc[0]+=1
    # the cap: a small cone of straw tied round the pole, and the pole end
    _rod(f'{pid}_Pole',(0,0,1.85),(.012,.008,2.335),.034,M['cedar_b'],'Body',sides=9,scale=.2)
    jc=[rr.uniform(-.03,.03) for _ in range(NS)]
    surf(f'{pid}_Cap',[2.215,(lambda th,k:2.15+jc[k]*.3),(lambda th,k:2.05+jc[k])],lambda th,z,i,k:(.040,.14,.30+.04*math.sin(3*th+ph[3]))[i],HAY,'Body')
    _hoop2(f'{pid}_CapTie',[Vector((.047*math.cos(t),.047*math.sin(t),2.205)) for t in np.linspace(0,math.tau,18,endpoint=False)],.011,M['hemp'],'Body',sides=6)
    # Detail_: stray stalks standing out of the thatch (the standard tier hides them; the jagged rims and fringes stay)
    for k in range(36):
        th=rr.uniform(0,math.tau);z=rr.uniform(.25,1.85)
        if cav(th,z)>.2:continue
        r=Rf(th,z)+.02;p=Vector((r*math.cos(th),r*math.sin(th),z));out=Vector((math.cos(th),math.sin(th),0));L=rr.uniform(.16,.34);sd=Vector((-out.y,out.x,0))*rr.uniform(-.5,.5)
        _taper(f'{pid}_Stalk{k:02d}',[p-out*.22,p+out*L*.35+sd*L*.2-Vector((0,0,L*.25)),p+out*L*.55+sd*L*.45-Vector((0,0,L*.75))],[.0045,.0035,.0012],HAY,'Detail_Stalks',sides=3,scale=.1,up=(rr.uniform(-1,1),rr.uniform(-1,1),.4))
    if pulled:   # the hollow: bundles lying across it, loose straw in front
        d0=Vector((math.cos(TH0),math.sin(TH0),0));t0=Vector((-d0.y,d0.x,0))
        for k,(rad,tz,off,L) in enumerate(((.45,.115,-.09,.56),(.63,.11,.05,.52),(.52,.325,.0,.50),(.41,.50,-.04,.44),(.69,.30,.12,.40))):
            c=d0*rad+t0*off+Vector((0,0,tz));ax=(t0*math.cos(.25*(k-2))+d0*math.sin(.25*(k-2))).normalized();rb=.105+.008*math.sin(k*2.1)
            prof=[(0,rb*.92),(.06,rb),(.42,rb*.93),(.5,rb*.80),(.58,rb*.93),(.94,rb),(1,rb*.92)]
            _lathe(f'{pid}_Bundle{k}',prof,(c-ax*L/2,c+ax*L/2),HAY,'Body',NS=12,scale=.3)
            _ring(f'{pid}_BundleTie{k}',c,ax,rb*.80+.004,.006,M['hemp'],'Body',n=11)
        o=_blob(f'{pid}_Loose',(.62,.42,.09),seed+5,OLD,'Body',sub=3,scale=.4,bumps=7,amp=.12);o.data.transform(Matrix.Rotation(TH0,4,'Z'));o.data.transform(Matrix.Translation(d0*.80+Vector((0,0,-.012))))
        for k in range(14):
            a=TH0+rr.uniform(-.5,.5);r=rr.uniform(.6,.86);p=Vector((r*math.cos(a),r*math.sin(a),0.));dr=Vector((rr.uniform(-1,1),rr.uniform(-1,1),0)).normalized();L=rr.uniform(.22,.42)
            _taper(f'{pid}_LooseStalk{k:02d}',[p,p+dr*L*.5+Vector((0,0,.010)),p+dr*L+Vector((0,0,.003))],[.005,.0045,.002],HAY,'Detail_Stalks',sides=3,scale=.1,up=(rr.uniform(-1,1),rr.uniform(-1,1),1))
    def pattern(W_,H_):return _straw_fringe(W_,H_,[(.0,.333,2),(.333,.667,7),(.667,1.,9)])
    def paint(col,rough,pos,onrm,ao,cav_,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];pz=P[...,2]
        low=filled*np.clip((.75-pz)/.7,0,1)*np.clip(.35+noise,0,1)          # the lower thatch has been out longest: greyer and damp near the ground
        g=col.mean(2,keepdims=True);col=col*(1-.45*low[...,None])+low[...,None]*.45*(g*np.array([1.02,.98,.88])*.85)
        sun=filled*np.clip((pz-1.2)/.9,0,1)*np.clip(onrm[...,2],0,1);col=col*(1+.10*sun[...,None]*np.array([1,.95,.8]))
        return col,rough
    return {'paint':paint,'wear':.2,'grime':.7,'ao_k':.6,'uv_angle':66,'card':{'strip':.12,'pattern':pattern,'alpha':True},
            'collision':'none in the model; if the scene needs one, a capsule of radius 0.95 m and height 2.0 m',
            'notes':['a lopsided dome, not a smooth bun: six overlapping thatch skirts with rims jagged in the shape, a fringe of loose strands under every rim',
                     'the fringes are cards in the top 12 % of the atlas (alpha clip): turn on Mip Maps Preserve Coverage for the albedo in Unity',
                     'Detail_Stalks: stray stalks, off at the standard tier']+(['one side of the lower half is pulled away: the hollow shows five tied bundles, loose straw lies in front (the three-views drew this as a tied-back curtain; made as the work pack words it)'] if pulled else [])}
def VG04_01(M):return _haystack(M,'VG04_01',4401,False)
def VG04_02(M):return _haystack(M,'VG04_02',4402,True)
PROPS['VG04_01']=VG04_01;PROPS['VG04_02']=VG04_02
