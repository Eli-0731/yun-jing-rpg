# LV07–LV12 shapes, read by build_lv.py after lv_items.py (helpers from lv_items, creekside wl_kit / wl_items / fi_items).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = width, -Y = front, Z = up.

def _cyl_cutter(name,c,ax,r,L,segs=12):
    """a round bar used only to cut (boolean): centre c, along ax, radius r, length L"""
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=segs,radius1=r,radius2=r,depth=L)
    q=Vector((0,0,1)).rotation_difference(Vector(ax).normalized()).to_matrix().to_4x4()
    for v in bm.verts:v.co=q@v.co+Vector(c)
    o=finish(name,bm,list(bpy.data.materials)[0],'cut');parts.remove(o);return o
def _smooth_prof(prof,sub=3):
    """Catmull-Rom through the profile points, `sub` new points per span (a lathe from a few points showed its facets)"""
    P=[Vector(p) for p in prof];out=[]
    for i in range(len(P)-1):
        p0,p1,p2,p3=P[max(i-1,0)],P[i],P[i+1],P[min(i+2,len(P)-1)]
        for k in range(sub+1):
            t=k/(sub+1);out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    out.append(P[-1]);return [(max(0.,p.x) if i else 0.,p.y) for i,p in enumerate(out)]
def _half_shell(name,prof,t,c,NS,mat,grp,scale=.25):
    """half of a thin shell of revolution about the vertical line (0, c): prof = [(r, z)] from the bottom pole (r = 0) up to
    the top; the half kept is y >= c (the back), the cut faces -Y. Inner surface = the profile moved in along its normal
    by t. Closed: the two cut edges and the top end are faces of thickness t."""
    P=[Vector((r,z)) for r,z in prof];inn=[]
    for i,p in enumerate(P):
        a=P[max(i-1,0)];b=P[min(i+1,len(P)-1)];d=(b-a).normalized();n=Vector((d.y,-d.x))   # outward normal of the profile
        q=p-n*t;inn.append(Vector((max(0.,q.x) if i else 0.,q.y)))
    bm=bmesh.new()
    def ring(r,z):
        if r<1e-6:v=bm.verts.new((0,c,z));return [v]*(NS+1)
        return [bm.verts.new((r*math.cos(math.pi*k/NS),c+r*math.sin(math.pi*k/NS),z)) for k in range(NS+1)]
    O=[ring(p.x,p.y) for p in P];I=[ring(p.x,p.y) for p in inn]
    def quad(a,b,c_,d):
        vs=[];[vs.append(v) for v in (a,b,c_,d) if v not in vs]
        if len(vs)>=3:bm.faces.new(vs)
    for i in range(len(P)-1):
        for k in range(NS):
            quad(O[i][k],O[i][k+1],O[i+1][k+1],O[i+1][k]);quad(I[i][k],I[i+1][k],I[i+1][k+1],I[i][k+1])
        quad(O[i][0],O[i+1][0],I[i+1][0],I[i][0]);quad(O[i][NS],I[i][NS],I[i+1][NS],O[i+1][NS])   # the two cut edges
    for k in range(NS):quad(O[-1][k],I[-1][k],I[-1][k+1],O[-1][k+1])   # the cut-off top end
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,scale)

# ---------------- LV07 gourd water ladle on a wooden peg hook (cand-1) ----------------
def LV07(M):
    """a square board of four planks (grooves between them, the top edge uneven), two iron nails; a short round peg
    driven in slanting up; the ladle — a pear-shaped gourd cut in half lengthways, the cut facing front so the darker
    inside shows — hangs from a hemp loop over the peg, knotted, the loop through a hole in the top of the neck;
    three stitches over a crack in the rim; water stains run down the board under the peg.
    Hung on a wall: the bottom of the ladle is z = 0 and the board's back (y = 0.022) is flat against the wall."""
    BW,BT,B0,B1=.30,.022,.245,.50
    top=[(.15,B1-.006),(.078,B1-.004),(.074,B1-.001),(.0,B1),(-.004,B1-.009),(-.074,B1-.007),(-.078,B1-.002),(-.15,B1-.004)]
    board=_plate('LV07_Board',[(-.15,B0+.004),(-.075,B0),(.0,B0+.003),(.076,B0+.001),(.15,B0+.005)]+top,0.,BT,M['cedar_b'],'Body',bev=.0025,jit=.0009,seed=701)
    for k,x in enumerate((-.075,.0,.076)):   # the joints between the planks
        _boolean(board,_cutter(f'LV07_Groove{k}',(.0035,.008,.30),(x,-.002,(B0+B1)/2)))
    for k,x in enumerate((-.112,.112)):   # two nail heads
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=.0085,location=(x,.0005,.462+.006*k));o=bpy.context.object;o.scale=(1,.55,1);bpy.ops.object.transform_apply(scale=True)
        bm=bmesh.new();bm.from_mesh(o.data);bpy.data.objects.remove(o);finish(f'LV07_Nail{k}',bm,M['iron'],'Body',.05)
    # the peg, slanting up out of the board; its end shows end grain
    pa=Vector((0,.012,.392));pd=Vector((0,-1,.30)).normalized();pb=pa+pd*.122
    _lathe('LV07_Peg',[(0,.0195),(.7,.0190),(.93,.0182),(1,.0160)],(pa,pb),M['cedar'],'Body',NS=16,scale=.1)
    # the ladle: half a pear-shaped gourd, cut face to the front
    c=-.128
    prof=[(0,0),(.022,.004),(.048,.013),(.072,.028),(.092,.050),(.106,.078),(.112,.108),(.110,.135),(.102,.162),(.086,.188),(.064,.212),
          (.045,.234),(.034,.256),(.028,.280),(.026,.305),(.025,.325),(.024,.342)]
    lad=_half_shell('LV07_Gourd',_smooth_prof(prof),.0042,c,30,M['gourd'],'Body')
    rn=.025;yh=c+rn;zh=.322
    _boolean(lad,_cyl_cutter('LV07_Hole',(0,yh,zh),(0,1,0),.0072,.03))
    # hemp loop: through the hole, up to a knot, then over the peg
    pk=pa+pd*((yh-pa.y)/pd.y);zk=.362;rr=.0034
    lp=[Vector((.0055,yh,zk+.004)),Vector((.0175,yh,pk.z-.024))]
    lp+=[Vector(((.019+rr+.0006)*math.cos(a),yh,pk.z+(.019+rr+.0006)*math.sin(a))) for a in np.linspace(-.35,math.pi+.35,13)]
    lp+=[Vector((-.0175,yh,pk.z-.024)),Vector((-.0055,yh,zk+.004))]
    tube('LV07_LoopPeg',lp,rr,M['hemp'],'Body',sides=6,scale=.06)
    hr=.0098   # the loop through the hole: down the inside of the neck, through, up the outside
    hp=[Vector((0,yh-hr*.55,zk-.004)),Vector((0,yh-hr,zh+hr+.012))]+[Vector((0,yh-hr*math.cos(a),zh+hr-hr*math.sin(a))) for a in np.linspace(0,math.pi,9)]+[Vector((0,yh+hr,zh+hr+.012)),Vector((0,yh+hr*.55,zk-.004))]
    tube('LV07_LoopHole',hp,rr,M['hemp'],'Body',sides=6,scale=.06)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.0095,location=(0,yh,zk));o=bpy.context.object;o.scale=(1.15,1.1,1.25);bpy.ops.object.transform_apply(scale=True)
    bm=bmesh.new();bm.from_mesh(o.data);bpy.data.objects.remove(o);finish('LV07_Knot',bm,M['hemp'],'Body',.05)
    tube('LV07_KnotTail',[Vector((.004,yh-.003,zk-.004)),Vector((.012,yh-.006,zk-.016)),Vector((.015,yh-.006,zk-.03))],.0026,M['hemp'],'Detail_Tail',sides=5,scale=.05)
    # three stitches over a crack in the rim (right side, low on the bowl)
    rofz=lambda z:float(np.interp(z,[p[1] for p in prof],[p[0] for p in prof]))
    for k,z in enumerate((.052,.066,.080)):
        r_=rofz(z)
        pts=[Vector(((r_-.0058),c+.007,z)),Vector((r_-.0045,c-.0022,z+.0008)),Vector((r_-.0005,c-.0026,z+.0012)),Vector((r_+.0018,c+.007,z+.0016))]
        tube(f'LV07_Stitch{k}',pts,.0011,M['hemp'],'Detail_Stitches',sides=4,scale=.03)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        # inside of the gourd: darker, browner, a little smoother
        rad=np.stack([px,py-c],-1);rl=np.linalg.norm(rad,axis=-1)+1e-6
        inner=filled*(pz<.345)*(py>c-.001)*(py<c+.115)*np.clip(-(onrm[...,0]*px+onrm[...,1]*(py-c))/rl*3,0,1)*(np.abs(px)<.115)
        col=col*(1-.50*inner[...,None])+inner[...,None]*np.array([.12,.04,.01]);rough=np.clip(rough-.08*inner,0,1)
        # water stains running down the board under the peg (front face)
        fr=filled*(py<.004)*(py>-.006)*(onrm[...,1]<-.6)*(pz>B0)*(pz<.40)
        sx=np.sin(px*95+1.3)*.5+.5+.35*np.sin(px*230+.7)
        st=fr*np.clip((sx-.45)*3,0,1)*np.clip(1-np.abs(px)/.09,0,1)*np.clip((.39-pz)/.03,0,1)*np.clip(1-(.37-pz)/.17+.3*(noise-.5),0,1)
        col=col*(1-.55*st[...,None])+st[...,None]*np.array([.0,.01,.02]);rough=np.clip(rough-.15*st,0,1)
        mo=filled*(pz>B1-.03)*np.clip((noise-.45)*3,0,1)*np.clip((pz-(B1-.03))/.02,0,1)   # moss along the top edge
        side=filled*(np.abs(px)>.13)*(pz>B0)*np.clip((noise-.6)*3,0,1)
        g=np.clip(mo+.6*side,0,1);col=col*(1-.6*g[...,None])+g[...,None]*np.array([.16,.22,.06])
        return col,rough
    return {'paint':paint,'wear':.9,'grime':.7,'uv_angle':50,'notes':['a board of four planks with two nails and a slanting peg; hung on a wall: the ladle bottom is z = 0, the board back (y = 0.022) is flat to the wall',
            'the ladle is half a pear-shaped gourd (shell 4 mm), the cut facing front; the inside is painted darker; a hemp loop goes through a hole in the neck, is knotted and hangs over the peg',
            'water stains under the peg are painted; Detail_Tail: the knot tail; Detail_Stitches: three stitches over a crack in the rim']}
PROPS['LV07']=LV07

def _band(name,P,mat,grp,t=.005,scale=.5,seed=0):
    """a thin layer with thickness from a grid P[i][j] (i across, j down), its own tiled UV: U = distance across, V = height,
    so the straw strands of the source (stretched along V) hang straight down"""
    bm=bmesh.new();P=[[Vector(p) for p in row] for row in P];nu,nv=len(P),len(P[0]);top=[];bot=[];uvv={}
    r_=random.Random(seed);du,dv=r_.random(),r_.random()
    su=[0.]
    for i in range(1,nu):su.append(su[-1]+(P[i][nv//2]-P[i-1][nv//2]).length)
    for i in range(nu):
        tr=[];br=[]
        for j in range(nv):
            a=P[min(i+1,nu-1)][j]-P[max(i-1,0)][j];b=P[i][min(j+1,nv-1)]-P[i][max(j-1,0)];n=a.cross(b).normalized()
            v1=bm.verts.new(P[i][j]+n*t/2);v2=bm.verts.new(P[i][j]-n*t/2);tr.append(v1);br.append(v2)
            uv=(su[i]/scale+du,P[i][j].z/scale+dv);uvv[v1]=uv;uvv[v2]=(uv[0]+.37,uv[1])
        top.append(tr);bot.append(br)
    for i in range(nu-1):
        for j in range(nv-1):
            bm.faces.new((top[i][j],top[i+1][j],top[i+1][j+1],top[i][j+1]));bm.faces.new((bot[i][j+1],bot[i+1][j+1],bot[i+1][j],bot[i][j]))
    for i in range(nu-1):
        bm.faces.new((bot[i][0],bot[i+1][0],top[i+1][0],top[i][0]));bm.faces.new((top[i][nv-1],top[i+1][nv-1],bot[i+1][nv-1],bot[i][nv-1]))
    for j in range(nv-1):
        bm.faces.new((top[0][j],top[0][j+1],bot[0][j+1],bot[0][j]));bm.faces.new((bot[nu-1][j],bot[nu-1][j+1],top[nu-1][j+1],top[nu-1][j]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);lay=bm.loops.layers.uv.new('Tiled')
    for f in bm.faces:
        f.smooth=True
        for l in f.loops:l[lay].uv=uvv[l.vert]
    return finish(name,bm,mat,grp,scale,keep_uv=True)
def _rsq_loop(c,half,rc,z,n=6):
    """a rounded-square loop round a square post (centre c, half width half, corner radius rc) at height z"""
    pts=[]
    for k,(sx,sy) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1))):
        a0=math.pi/2*k
        for a in np.linspace(a0,a0+math.pi/2,n):pts.append(Vector((c[0]+sx*(half-rc)+rc*math.cos(a),c[1]+sy*(half-rc)+rc*math.sin(a),z)))
    return pts+[pts[0]+(pts[1]-pts[0])*.5]

# ---------------- LV08 rain hat and straw rain cape on a standing peg rack (cand-2) ----------------
def LV08(M):
    """a square post standing in a base (two feet along Y, a cross beam on them); two short pegs near the top, the worn
    one paler; a conical woven-bamboo rain hat sits on the post top (rim frayed, a knob at the apex); the rain cape hangs
    from a hemp collar tied round the post: five layers of straw, each covering the top of the one below, wider going
    down, the lower edges ragged, open down the front so the post shows; a bow and two cords with tassels at the throat;
    a hemp binding low on the post. The work pack's depth limit (0.4 m) keeps the hat 0.40 m across (cand-2: ~0.6)."""
    PH=.0375;rr=random.Random(808)
    for k,x in enumerate((-.27,.27)):box(f'LV08_Foot{k}',(.085,.34,.075),(x,0,.0375),M['cedar'],'Body',bev=.006,jit=.0015,seed=810+k)
    box('LV08_Beam',(.64,.085,.075),(0,0,.1095),M['cedar_b'],'Body',bev=.006,jit=.0015,seed=812)
    for k,y in enumerate((-.0695,.0695)):box(f'LV08_Wedge{k}',(.075,.065,.05),(0,y,.168),M['cedar'],'Body',bev=.005,jit=.001,seed=814+k)   # wedges either side of the post foot
    ZT=1.5336   # the post's corners just touch the inside of the hat cone
    box('LV08_Post',(2*PH,2*PH,ZT-.14),(0,0,(ZT+.14)/2),M['cedar_b'],'Body',bev=.005,cuts=6,jit=.0012,seed=816)
    for k,z in enumerate((.405,.428,.451)):tube(f'LV08_Bind{k}',_rsq_loop((0,0),PH+.0062,.010,z),.0058,M['hemp'],'Body',sides=6,scale=.06)
    for k,sx in enumerate((-1,1)):   # pegs, slanting up; the right one worn pale and smooth
        a=Vector((sx*.02,0,1.235));b=Vector((sx*.135,0,1.262))
        _lathe(f'LV08_Peg{k}',[(0,.0175),(.85,.0165),(1,.0140)],(a,b),M['cedar_new'] if sx>0 else M['cedar'],'Body',NS=12,scale=.1)
    # the hat: a shallow cone shell resting on the post top
    hp=[(1.585,.006),(1.56,.037),(1.53,.078),(1.50,.120),(1.47,.161),(1.452,.186),(1.443,.198),(1.437,.2015),(1.434,.198),(1.439,.189),(1.465,.150),(1.50,.103),(1.535,.054),(1.573,.006)]
    _lathe('LV08_Hat',[((z-1.43)/.17,r*.94) for z,r in hp],(Vector((0,0,1.43)),Vector((0,0,1.60))),M['weave'],'Body',NS=56,scale=.25,loop=True)
    _lathe('LV08_HatKnob',[(0,.0105),(.35,.0125),(.75,.010),(1,0)],(Vector((0,0,1.575)),Vector((0,0,1.60))),M['bamboo_old'],'Body',NS=12,scale=.05)
    for k in range(46):   # frayed strips at the rim (Detail_)
        th=math.tau*(k+rr.uniform(-.3,.3))/46;L=rr.uniform(.010,.026);u=Vector((math.cos(th),math.sin(th),0))
        p0=u*.1815+Vector((0,0,1.4368));pts=[p0,p0+u*(.006+L*.22)+Vector((0,0,-.004)),p0+u*(.007+L*.34)+Vector((0,0,-L*.8))]
        _taper(f'LV08_Fray{k:02d}',pts,[.0024,.0018,.0005],M['bamboo_split'],'Detail_Fringe',sides=3,scale=.04,up=Vector((0,0,1)))
    # the cape: five straw layers round an elliptic cone, open at the front
    ZS=[.26,.60,.95,1.05,1.10,1.135];XS=[.330,.282,.215,.172,.118,.062];YS=[.140,.132,.118,.104,.084,.058]   # broad shoulders, then hanging straight-ish
    def RX(z):return float(np.interp(z,ZS,XS))
    def RY(z):return float(np.interp(z,ZS,YS))
    LY=[(1.135,.915),(1.005,.755),(.87,.595),(.725,.435),(.575,.268)]
    for L,(zt,zb) in enumerate(LY):
        NT=86;cols=[]
        th0=.20+.07*(1.135-zt)/.86
        jag=[rr.uniform(0,.055)*(1 if rr.random()>.25 else .3) for _ in range(NT)]
        for i in range(NT):
            th=th0+(math.tau-2*th0)*i/(NT-1);row=[]
            for j in range(6):
                u=j/5;z=zt-(zt-zb)*u-(jag[i] if j==5 else jag[i]*.35 if j==4 else 0)
                off=.046*max(0.,(u-.62)/.38)**1.4+.004*math.sin(5*th+L*1.7)*u-.0056*L   # each layer a thickness inside the one above: their tops touch, the lower halves flare out over the next
                ex,ey=math.sin(th)*(RX(z)+off),-math.cos(th)*(RY(z)+off)
                if L==0:   # the top of the first layer is gathered round the square post (its inside face on the post)
                    hq=PH+.0031;sq=hq/max(abs(math.sin(th)),abs(math.cos(th)));b_=min(1.,max(0.,(u-.12)/.3));b_=b_*b_*(3-2*b_)
                    ex,ey=ex*b_+math.sin(th)*sq*(1-b_),ey*b_-math.cos(th)*sq*(1-b_)
                row.append((ex,ey,z))
            cols.append(row)
        _band(f'LV08_Cape{L}',cols,M['cape'],'Body',t=.005,seed=820+L)
    # collar: hemp rope tied round the cape's top, a bow at the throat and two cords with tassels
    zc=1.127;cy=PH+.0172   # the rope just resting on the gathered straw (sunk into it, its flat ply faces lay along the straw)
    cp=_rsq_loop((0,0),cy,.016,zc,n=8)[:-1]
    rope('LV08_Collar',cp[3:]+cp[:3],.0105,M['hemp'],'Body')   # tied tight round the gathered top, the ends at the throat
    kp=Vector((0,-cy-.0115,zc-.004))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.014,location=kp);o=bpy.context.object;o.scale=(1.2,1,1.1);bpy.ops.object.transform_apply(scale=True)
    bm=bmesh.new();bm.from_mesh(o.data);bpy.data.objects.remove(o);finish('LV08_Knot',bm,M['hemp'],'Body',.05)
    for k,sx in enumerate((-1,1)):
        lp=[kp+Vector((sx*.008,0,.002))]+[kp+Vector((sx*(.028+.022*math.sin(a)),-.004,.012*math.sin(2*a)+.004)) for a in np.linspace(.4,math.pi-.4,7)]+[kp+Vector((sx*.008,-.002,-.004))]
        tube(f'LV08_Bow{k}',lp,.0052,M['hemp'],'Body',sides=6,scale=.05)
        ends=[kp+Vector((sx*.006,-.004,-.008)),kp+Vector((sx*.013,-.012,-.06)),kp+Vector((sx*.018,-.019,-.12)),kp+Vector((sx*.022,-.024,-.165))]
        tube(f'LV08_Cord{k}',ends,.0050,M['hemp'],'Body',sides=6,scale=.05)
        e=ends[-1];_lathe(f'LV08_Tassel{k}',[(0,.0065),(.25,.0095),(1,.013)],(e+Vector((0,0,.006)),e+Vector((0,0,-.05))),M['hemp'],'Body',NS=10,scale=.05)
    patches=[(-1.15,.80,.30,.06,(.36,.38,.42)),(.95,.52,.26,.055,(.44,.33,.25)),(2.75,.98,.22,.05,(.40,.36,.33)),(3.6,.40,.24,.06,(.34,.37,.40))]
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        rx=np.interp(pz,ZS,XS);ry=np.interp(pz,ZS,YS)
        th=np.arctan2(px/rx,-py/ry);onc=filled*(pz>.26)*(pz<1.14)*((px/rx)**2+(py/ry)**2>1.05)
        for tc,zc_,w,h,cc in patches:   # cloth patches sewn on the cape, a darker stitched border
            tc=math.atan2(math.sin(tc),math.cos(tc));d=np.abs(np.arctan2(np.sin(th-tc),np.cos(th-tc)))
            m_=onc*(d<w)*(np.abs(pz-zc_)<h);b=m_*((d>w-.03)|(np.abs(pz-zc_)>h-.007))
            col=np.where(m_[...,None]>0,np.array(cc)*(.85+.3*noise[...,None]),col);col=col*(1-.35*b[...,None])
        hat=filled*(pz>1.47)*(pz<1.53)*(np.arctan2(py,px)>.5)*(np.arctan2(py,px)<1.1)   # a patch on the hat
        col=np.where(hat[...,None]>0,np.array([.38,.39,.40])*(.85+.3*noise[...,None]),col)
        mo=filled*np.clip((.10-pz)/.08,0,1)*np.clip((noise-.45)*3,0,1)   # moss and earth on the feet
        col=col*(1-.3*mo[...,None])+mo[...,None]*np.array([.10,.14,.04])
        worn=filled*(px>.04)*(pz>1.22)*(pz<1.30)*(np.abs(py)<.02)   # the worn peg: polished
        rough=np.clip(rough-.15*worn,0,1)
        return col,rough
    return {'paint':paint,'wear':.9,'grime':.8,'uv_angle':50,'notes':['a square post on a base of two feet and a cross beam; two pegs near the top, the right one worn pale; a hemp binding low on the post',
            'the hat (0.40 m across: the depth limit is 0.4 m) is a cone shell resting on the post top; the weave is in the texture; Detail_Fringe: frayed strips at the rim',
            'the cape: five straw layers round an elliptic cone, each over the top of the next, ragged lower edges, open at the front; collar rope, bow, cords and tassels; cloth patches painted']}
PROPS['LV08']=LV08

# ---------------- LV09 empty bamboo birdcage hanging from a short pole in a stone base (cand-4) ----------------
def LV09(M):
    """a rough stone block with the bamboo pole set into it; a short arm lashed across the pole top and a brace under it;
    from the arm a hemp loop holds a bamboo ring, the ring through an eye on the cage's top knob. The cage: a dark wooden
    base ring and floor, 36 thin bamboo bars round it, curving in at the top into a dome under the knob, three hoops;
    a small door at the front stands open on its hinge. An old cloth wound round the pole's middle. Empty: no bird."""
    rr=random.Random(909)
    PX=-.09;CX=.07   # pole and cage centres (x): stone, pole and cage fit the 0.4 m width
    # stone base: a rough block, flat underneath, the pole set into its top
    bm=box_bm((.2,.18,.165),(0,0,.0825));bmesh.ops.subdivide_edges(bm,edges=bm.edges,cuts=4,use_grid_fill=True)
    bmesh.ops.bevel(bm,geom=[e for e in bm.edges if e.is_boundary or len(e.link_faces)==2 and e.calc_face_angle(0)>.5],offset=.022,segments=2,affect='EDGES')
    pl=[(Vector((rr.uniform(-1,1),rr.uniform(-1,1),rr.uniform(-.2,1))).normalized(),rr.uniform(.0,.018)) for _ in range(9)]   # chipped facets
    for v in bm.verts:
        x,y,z=v.co;t=z/.165;sc=1-.17*t*t
        n=.010*math.sin(31*x+1.2)*math.sin(27*y+.4)+.007*math.sin(43*z+21*x)
        p_=Vector((x*sc*(1+n*4),y*sc*(1+n*4),z*(1+.4*n) if z>.001 else 0.))
        for nv,d in pl:   # flatten into a few planes, as split rock
            c_=Vector((0,0,.08));h=(p_-c_).dot(nv)-(.095-d)
            if h>0 and p_.z>.004:p_-=nv*h*.8
        v.co=p_+Vector((PX,0,0))
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.001)
    for f in bm.faces:f.smooth=False
    finish('LV09_Stone',bm,M['stone'],'Body',.3)
    # pole, arm and brace (bamboo with nodes), lashed with hemp
    ZA=1.122
    _cane('LV09_Pole',[(PX,0,.09),(PX,0,.6),(PX+.002,0,1.172)],[.0235,.0222,.0205],M['bamboo'],'Body',nodes=(.19,.47,.72,.96,1.07))
    _cane('LV09_Arm',[(PX-.03,0,ZA),(CX+.06,0,ZA)],[.0165,.0150],M['bamboo'],'Body',nodes=(.045,.19))
    _cane('LV09_Brace',[(PX+.012,0,.975),(CX-.075,0,ZA-.008)],[.0095,.0088],M['bamboo'],'Body',nodes=(.09,))
    for k,z in enumerate((ZA-.032,ZA+.03,.985)):_ring(f'LV09_PoleLash{k}',(PX,0,z),(0,0,1),.0247,.0036,M['hemp'],'Body',n=19)
    for k,x in enumerate((PX+.04,)):_ring(f'LV09_ArmLash{k}',(x,0,ZA),(1,0,0),.0193,.0036,M['hemp'],'Body',n=19)
    # cloth wound round the pole's middle, one end hanging
    _lathe('LV09_Cloth',[(0,.0236),(.08,.0262),(.5,.0268),(.92,.0262),(1,.0236)],(Vector((PX,0,.52)),Vector((PX,0,.585))),M['linen_b'],'Body',NS=16,scale=.1)
    rows=[[(PX+.024*math.cos(a),.024*math.sin(a)-.002,z) for a in (-1.9,-1.55,-1.2)] for z in (.555,.535,.505,.48)]
    for i,row in enumerate(rows):rows[i]=[(x+(.0005+.0035*i)*math.cos(-1.55),y+(.0005+.0035*i)*math.sin(-1.55),z) for x,y,z in row]
    _sheet('LV09_ClothEnd',rows,None,None,M['linen_b'],'Detail_Cloth',t=.0018)
    # hemp loop round the arm, the bamboo ring through it, the ring through the eye on the cage knob
    zb=ZA-.047;lp=[]
    lp+=[Vector((CX,-.010,zb+.012)),Vector((CX,-.0205,ZA))]+[Vector((CX,-.0205*math.cos(a),ZA+.0205*math.sin(a))) for a in np.linspace(.3,math.pi-.3,7)]+[Vector((CX,.0205,ZA)),Vector((CX,.010,zb+.012))]
    lp+=[Vector((CX,.0101*math.cos(a),zb+.0101-.0101*math.sin(a)+.0)) for a in np.linspace(.15,math.pi-.15,7)]
    lp+=[lp[0]+(lp[1]-lp[0])*.25]
    tube('LV09_Loop',lp,.0034,M['hemp'],'Body',sides=6,scale=.05)
    zr=zb+.0072-.024   # ring centre: its top wire rests on the bottom of the loop (0.3 mm: the cage's weight pulls them together)
    tube('LV09_Ring',[Vector((CX+.024*math.sin(a),0,zr+.024*math.cos(a))) for a in np.linspace(0,math.tau,29)],.0035,M['bamboo_split'],'Body',sides=6,scale=.05)
    ze=zr-.024-.0041   # the eye on the knob: the ring's bottom wire runs through it, the eye's top wire resting on it
    tube('LV09_Eye',[Vector((CX,.0105*math.sin(a),ze+.0105*math.cos(a))) for a in np.linspace(0,math.tau,21)],.0026,M['iron'],'Body',sides=6,scale=.04)
    ZK=ze-.0105-.001;ZD=ZK-.034   # knob top, dome top
    _lathe('LV09_Knob',[(0,.036),(.12,.038),(.35,.030),(.65,.017),(1,.009)],(Vector((CX,0,ZD-.012)),Vector((CX,0,ZK))),M['cedar_b'],'Body',NS=14,scale=.05)
    # the cage
    R=.112;Z1=ZD-.088;Z0=Z1-.285;ZB=Z0-.05
    _lathe('LV09_Base',[(0,R+.010),(.15,R+.012),(.85,R+.012),(1,R+.009),(1,R-.010),(0,R-.010)],(Vector((CX,0,ZB)),Vector((CX,0,Z0))),M['cedar_b'],'Body',NS=40,scale=.2,loop=True)
    _lathe('LV09_Floor',[(0,R-.0095),(1,R-.0095),(1,0)],(Vector((CX,0,Z0-.022)),Vector((CX,0,Z0-.016))),M['cedar'],'Body',NS=40,scale=.2)
    DOOR=-math.pi/2;dw=.30;NB=36
    for k in range(NB):
        th=math.tau*k/NB+math.pi/NB*0;d=abs(math.atan2(math.sin(th-DOOR),math.cos(th-DOOR)))
        c,s=math.cos(th),math.sin(th)
        pts=[Vector((CX+R*c,R*s,Z0-.012))]
        if d<dw-.02:pts.append(Vector((CX+R*c,R*s,Z0+.156)))   # above the doorway only
        else:pts.append(Vector((CX+R*c,R*s,Z0+.02)))
        pts+=[Vector((CX+(.030+(R-.030)*math.cos(t))*c,(.030+(R-.030)*math.cos(t))*s,Z1+(ZD-Z1)*math.sin(t))) for t in np.linspace(0,math.pi/2,9)]
        pts[-1]=pts[-1]+Vector((0,0,-.004))
        if d<dw-.02:pts=pts[1:]   # starts on the door's top hoop
        tube(f'LV09_Bar{k:02d}',pts,.0022,M['bamboo'],'Bars',sides=5,scale=.04)
    for k,z in enumerate((Z0+.075,Z0+.156,Z1)):   # hoops; the lower one stops at the doorway
        a0,a1=(DOOR+dw,DOOR+math.tau-dw) if k==0 else (.1,math.tau+.05)   # a short split where the hoop's ends meet
        hp=[Vector((CX+(R+.0042)*math.cos(a),(R+.0042)*math.sin(a),z)) for a in np.linspace(a0,a1,61)]
        tube(f'LV09_Hoop{k}',hp,.0029,M['bamboo_split'],'Bars',sides=5,scale=.05)
    for k,sg in enumerate((-1,1)):   # door posts
        th=DOOR+sg*dw;tube(f'LV09_DoorPost{k}',[Vector((CX+R*math.cos(th),R*math.sin(th),Z0-.012)),Vector((CX+R*math.cos(th),R*math.sin(th),Z0+.160))],.0031,M['bamboo_split'],'Bars',sides=6,scale=.05)
    # the door: a small frame with three bars, swung open outwards about the left post
    th=DOOR-dw;hg=Vector((CX+(R+.006)*math.cos(th),(R+.006)*math.sin(th),0));w=2*R*math.sin(dw)-.006
    op=math.radians(78);dd=Vector((math.cos(-op),math.sin(-op),0))   # door plane direction from the hinge (closed: +X)
    def dp(u,z):return hg+dd*u+Vector((0,0,z))
    zq0,zq1=Z0+.006,Z0+.150
    tube('LV09_DoorFrame',[dp(.004,zq0),dp(w,zq0),dp(w,zq1),dp(.004,zq1),dp(.004,zq0+.004)],.0026,M['bamboo_split'],'Bars',sides=5,scale=.04)
    for j in range(3):tube(f'LV09_DoorBar{j}',[dp(w*(j+1)/4,zq0),dp(w*(j+1)/4,zq1)],.0019,M['bamboo'],'Bars',sides=5,scale=.04)
    for k,z in enumerate((zq0+.02,zq1-.02)):   # hinge rings: thin hemp round the post and the frame
        _ring(f'LV09_Hinge{k}',hg+Vector((-.003*math.cos(th)+.001,-.003*math.sin(th),z)),(0,0,1),.0058,.0014,M['hemp'],'Body',n=13)
    def card_mesh():   # LOD2: the bars as one cylinder and dome of 18 sides with the bars painted on (alpha): decimated, 4 mm bars broke up
        NS_=18;cv=[];cf=[];cu=[];zs=[(Z0-.01,0.)]+[(Z1+(ZD-Z1)*math.sin(t),.72+.28*t/(math.pi/2)) for t in np.linspace(0,math.pi/2,4)]
        rs=[R]+[.030+(R-.030)*math.cos(t) for t in np.linspace(0,math.pi/2,4)]
        for (z,v),r in zip(zs,rs):
            for k in range(NS_+1):a=math.tau*k/NS_;cv.append((CX+r*math.cos(a),r*math.sin(a),z))
        for i in range(len(zs)-1):
            for k in range(NS_):
                a,b=i*(NS_+1)+k,(i+1)*(NS_+1)+k;cf.append((a,a+1,b+1,b));cu.append(((k/NS_,zs[i][1]),((k+1)/NS_,zs[i][1]),((k+1)/NS_,zs[i+1][1]),(k/NS_,zs[i+1][1])))
        def pattern(W_,H_):
            u=(np.arange(W_)[None,:]+.5)/W_;v=(np.arange(H_)[:,None]+.5)/H_
            bars=(np.abs(((u*NB)%1)-.5)>.5-.11).astype(np.float32)*np.ones_like(v)
            hz=[(Z0+.075-Z0+.01)/(Z1-Z0+.01)*.72,(Z0+.156-Z0+.01)/(Z1-Z0+.01)*.72,.72]
            hoops=np.zeros_like(bars)
            for h in hz:hoops=np.maximum(hoops,(np.abs(v-h)<.022).astype(np.float32)*np.ones_like(u))
            a=np.clip(bars+hoops,0,1);col=np.array([.62,.50,.28])*(.85+.15*bars[...,None]);return col*np.ones((H_,W_,1)),a
        return {'drop':['Bars'],'strip':.12,'verts':cv,'faces':cf,'uvs':cu,'pattern':pattern}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        st=filled*(pz<.175)*(np.hypot(px-PX,py)<.13)
        mo=st*np.clip((pz-.11)/.05,0,1)*np.clip((noise-.4)*3,0,1)   # moss on the stone's top, earth at its foot
        col=col*(1-.35*mo[...,None])+mo[...,None]*np.array([.10,.15,.04])
        ft=st*np.clip((.04-pz)/.04,0,1);col=col*(1-.3*ft[...,None])
        ring=filled*(np.abs(pz-zr)<.03)*(np.abs(px-CX)<.03)*(np.abs(py)<.008);rough=np.clip(rough-.15*ring,0,1)   # the ring rubbed smooth
        return col,rough
    return {'paint':paint,'wear':.8,'grime':.7,'uv_angle':50,'lod_ratios':{'Body':(.5,.25),'Bars':(.7,.1)},'card':card_mesh(),
            'notes':['a rough stone block, a bamboo pole set in it, an arm lashed across its top with a brace; an old cloth round the pole (Detail_Cloth: its hanging end)',
                     'a hemp loop on the arm holds a bamboo ring; the ring runs through an iron eye on the cage knob (loop, ring and eye interlock, not touching: about 1 mm)',
                     'the cage: dark base ring and floor, 36 bars curving into a dome, three hoops, the door open on its hinge; LOD2 shows the bars painted on a cylinder and dome (alpha clip)']}
PROPS['LV09']=LV09

# ---------------- LV10 a pair of straw sandals and a pair of wooden clogs (cand-1) ----------------
def LV10(M):
    """left: a pair of straw sandals — a flat oval sole with a thick braided rim, a dark cloth thong from the toe knot to
    both sides, the braid and the flattened, darker heel in the texture; right: a pair of wooden clogs — a pale old board
    with rounded corners on two teeth, the same dark cloth thong, mud on the teeth. Each shoe is its own piece, the pairs
    set down a little askew. Real sizes: sandal 0.24 m long, clog 0.225 m long, teeth 3.4 cm high."""
    rr=random.Random(1010)
    def place(n0,cx,cy,rot):
        T=Matrix.Translation((cx,cy,0))@Matrix.Rotation(rot,4,'Z')
        for o in parts[n0:]:
            if o["grp"]!='cut':o.data.transform(T)
    def soleline(a,bf,bh,n=36,ex=2.6):
        pts=[]
        for k in range(n):
            t=math.tau*k/n;c,s=math.cos(t),math.sin(t);y=a*math.copysign(abs(s)**(2/ex),s);b=bh+(bf-bh)*(.5-.5*y/a)
            pts.append((b*math.copysign(abs(c)**(2/ex),c),y))
        return pts
    def flat(name,outline,z0,z1,mat,grp,bev,seed):   # an outline in X–Y extruded along Z (via _plate, turned up)
        o=_plate(name,[(x,-y) for x,y in outline],z0,z1,mat,grp,bev=bev,jit=.0006,seed=seed);o.data.transform(Matrix.Rotation(math.pi/2,4,'X'));return o
    def thong(tag,side_z,knot,peak,anchors,post_z):
        kp=Vector(knot)
        for k,sx in enumerate((-1,1)):   # two straps from the knot to the sides, padded cloth over a cord
            ax,ay=anchors;pts=[Vector((sx*ax,ay,side_z-.004)),Vector((sx*ax*.96,ay-.004,side_z+.012)),Vector((sx*peak[0],peak[1],peak[2])),Vector((sx*.012,kp.y+.012,kp.z+.002)),kp+Vector((sx*.003,.002,0))]
            tube(f'{tag}_Strap{k}',pts,.0062,M['cloth_dark'],'Body',sides=7,scale=.05)
        tube(f'{tag}_Post',[kp,kp+Vector((0,-.002,-.012)),Vector((0,kp.y-.003,post_z))],.0052,M['cloth_dark'],'Body',sides=7,scale=.05)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.0095,location=kp);o=bpy.context.object;o.scale=(1.25,1.1,.9);bpy.ops.object.transform_apply(scale=True)
        bm=bmesh.new();bm.from_mesh(o.data);bpy.data.objects.remove(o);finish(f'{tag}_Knot',bm,M['cloth_dark'],'Body',.04)
        for j in range(4):   # frayed threads at the knot (Detail_)
            d=Vector((rr.uniform(-1,1),rr.uniform(-1,-.2),rr.uniform(-.2,.6))).normalized()
            _taper(f'{tag}_Fray{j}',[kp+d*.006,kp+d*.014,kp+d*.021+Vector((0,0,-.004))],[.0012,.0009,.0003],M['cloth_dark'],'Detail_Frays',sides=3,scale=.03)
    SH=[]
    # straw sandals
    for k,(cx,cy,rot) in enumerate(((-.146,.010,.05),(-.048,-.004,-.035))):
        n0=len(parts);ol=soleline(.12,.048,.041)
        flat(f'LV10_Sandal{k}_Sole',ol,0.,.0105,M['straw'],'Body',bev=.003,seed=1011+k)
        inset=[]
        for i,(x,y) in enumerate(ol):   # the rim's centre line: the outline moved in by the rope's radius
            xa,ya=ol[i-1];xb,yb=ol[(i+1)%len(ol)];tx,ty=xb-xa,yb-ya;l=math.hypot(tx,ty);inset.append((x-ty/l*.0074,y+tx/l*.0074))
        rp=[Vector((x,y,.0098+.0006*math.sin(7*i))) for i,(x,y) in enumerate(inset)];rp=rp+[rp[0]+(rp[1]-rp[0])*.6]
        rope(f'LV10_Sandal{k}_Rim',rp,.0078,M['straw'],'Body')
        thong(f'LV10_Sandal{k}',.0105,(0,-.070,.032),(.031,-.018,.036),(.032,.012),.004)
        place(n0,cx,cy,rot);SH.append(('s',cx,cy,rot))
    # wooden clogs on two teeth
    for k,(cx,cy,rot) in enumerate(((.051,-.012,.03),(.146,.006,-.045))):
        n0=len(parts);ol=soleline(.1125,.045,.043,ex=4.)
        flat(f'LV10_Clog{k}_Board',ol,.033,.052,M['stumpwood'],'Body',bev=.003,seed=1021+k)
        for j,y in enumerate((-.056,.054)):box(f'LV10_Clog{k}_Tooth{j}',(.080,.021,.0345),(0,y,.0172),M['stumpwood'],'Body',bev=.002,jit=.0006,seed=1031+2*k+j)
        thong(f'LV10_Clog{k}',.052,(0,-.066,.073),(.029,-.016,.080),(.034,.016),.040)
        place(n0,cx,cy,rot);SH.append(('c',cx,cy,rot))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=(pos-np.array(meta['offset'][:]))/meta['scale_to_target'];px,py,pz=P[...,0],P[...,1],P[...,2]
        for kind,cx,cy,rot in SH:
            c_,s_=math.cos(-rot),math.sin(-rot);lx=(px-cx)*c_-(py-cy)*s_;ly=(px-cx)*s_+(py-cy)*c_
            on=filled*(np.abs(lx)<.06)*(np.abs(ly)<.125)
            if kind=='s':   # the sole's braid (herringbone rows across), the heel and ball pressed flat and darker
                top=on*(pz<.0125)*(onrm[...,2]>.6)
                br=.5+.5*np.sin(math.tau*(ly*70+np.abs(lx)*48));br2=.5+.5*np.sin(math.tau*lx*26)
                col=col*(1-(.30*np.clip((.35-br)*3,0,1)+.10*br2)[...,None]*top[...,None])
                pr=top*(np.exp(-((ly-.06)/.035)**2)+.8*np.exp(-((ly+.05)/.03)**2))*np.clip(1-np.abs(lx)/.04,0,1)
                col=col*(1-.28*pr[...,None]);rough=np.clip(rough-.15*pr,0,1)
            else:   # mud on the teeth and the board's underside; the foot's dark print on top
                mud=on*np.clip((.036-pz)/.03,0,1)*np.clip(.6+(noise-.5)*1.5,0,1)
                col=col*(1-.55*mud[...,None])+mud[...,None]*np.array([.10,.07,.04]);rough=np.clip(rough+.1*mud,0,1)
                pr=on*(pz>.05)*(onrm[...,2]>.7)*(np.exp(-((ly-.05)/.03)**2)+.7*np.exp(-((ly+.04)/.03)**2))*np.clip(1-np.abs(lx)/.04,0,1)
                col=col*(1-.25*pr[...,None])
        return col,rough
    return {'paint':paint,'wear':1.0,'grime':.8,'uv_angle':50,'notes':['two straw sandals (0.24 m) and two wooden clogs (0.225 m, teeth 3.4 cm), each its own piece, set down a little askew',
            'the sandal sole is a flat plate with a braided rope rim; the braid, the pressed heel and ball are painted; clog mud and foot print painted',
            'thongs: two padded cloth straps from a toe knot to the sides and a post into the sole; Detail_Frays: frayed threads at the knots']}
PROPS['LV10']=LV10
