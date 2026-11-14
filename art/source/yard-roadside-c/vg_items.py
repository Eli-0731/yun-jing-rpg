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
