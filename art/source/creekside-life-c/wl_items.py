# WL01–WL05 shapes, read by build_wl.py (exec'd into its namespace: M = source materials, helpers from wl_kit).
# Every item follows the three-view picked in art/references/<ID>/prompt.txt. Blender: X = length, -Y = front, Z = up.

def _cutter(name,size,center):
    """a box used only to cut (boolean) — built through finish() so the cut faces get the tiled UV too, then taken out of parts"""
    o=finish(name,box_bm(size,center),list(bpy.data.materials)[0],'cut');parts.remove(o);return o
def _boolean(o,cutter):
    m=o.modifiers.new('cut','BOOLEAN');m.operation='DIFFERENCE';m.object=cutter;m.solver='EXACT';apply(o,m);bpy.data.objects.remove(cutter)
def _lash(name,c,along,across,w,h,M,grp,r=.0024,turns=3):
    """cord lashing an X over a strip: `turns` crossings, each an arc from one side of the strip over its top to the other,
    the ends tucked into the board below (the cord goes round underneath)"""
    a=Vector(along).normalized();s=Vector(across).normalized();c=Vector(c);out=[]
    for k in range(turns):
        sh=(k-(turns-1)/2)*r*2.3
        for sgn in (1,-1):
            p0=c+a*(-w*.5+sh)*sgn+s*(-w*.75)+Vector((0,0,-.004));p1=c+a*(w*.5+sh)*sgn+s*(w*.75)+Vector((0,0,-.004))
            pts=[p0.lerp(p1,t)+Vector((0,0,(h+r)*math.sin(math.pi*min(1,max(0,(t-.08)/.84)))+.004*math.sin(math.pi*t))) for t in np.linspace(0,1,11)]
            out.append(tube(f'{name}_{k}_{"ab"[sgn>0]}',pts,r,M['hemp'],grp,sides=6,scale=.08))
    return out

# ---------------- WL01 old ribbed washing board (cand-4) ----------------
def WL01(M):
    """two side rails hold the rubbing board; a worn flat at the head end, 13 round ribs, one rib replaced by a flat
    lashed slat, a handle slot in the head bar, three battens underneath. Lies flat, ribs up, head at +X."""
    L,W=.70,.40;rw=.036;rh=.074;inner=W/2-rw            # rails 3.6 cm wide, 7.4 cm tall: only a little above the rib crowns, as in cand-4
    pz0,pz1=.034,.058                                    # rubbing panel: 2.4 cm thick, its face at 5.8 cm
    for sgn,seed in ((-1,11),(1,12)):                    # side rails, slightly irregular, worn round on top
        o=box(f'WL01_Rail{"LR"[sgn>0]}',(L,rw,rh),(0,sgn*(W/2-rw/2),rh/2),M['cedar_b'],'Body',bev=.013,segs=3,cuts=0,jit=.0025,seed=seed)   # no cuts: the 13 mm bevel on a 36 mm rail overlapped the cut lines and folded the rail ends
    # panel with a worn hollow at the head end (the board is rubbed there, flat ribs further down)
    px0,px1=-L/2+.05,L/2-.075
    pan=finish('WL01_Panel',box_bm((px1-px0,2*inner+.02,pz1-pz0),((px0+px1)/2,0,(pz0+pz1)/2)),M['cedar'],'Body')
    subdiv(pan,10);me=pan.data
    for v in me.vertices:
        if v.co.z>pz1-1e-4:
            u=(v.co.x-.18)/.085;w_=v.co.y/(inner*.92)
            v.co.z-=.0045*max(0,1-u*u-w_*w_)               # shallow oval hollow, 4.5 mm at its centre
    bevel(pan,.003,2)
    # ribs: half-round, slightly flattened where the hands rub most (middle), a little sag across the width
    xs=[-.268+i*.0305 for i in range(13)];slat_i=2
    for i,x in enumerate(xs):
        if i==slat_i:continue
        r=.0125*(1-.12*math.exp(-((x+.05)/.12)**2))     # middle ribs worn lower
        pts=[Vector((x+.0015*math.sin(t*3+i),y,pz1-.003-.0018*(1-(y/inner)**2))) for t,y in enumerate(np.linspace(-inner-.008,inner+.008,9))]
        o=tube(f'WL01_Rib{i:02d}',pts,r,M['cedar_rib'],'Body',sides=12,scale=.25)
        sc_=o.data;[setattr(v,'co',Vector((v.co.x,v.co.y,pz1-.003+(v.co.z-(pz1-.003))*.85))) for v in sc_.vertices]   # a little flatter than round
    # the repaired slat: a fresher flat board where one rib broke, lashed at both ends
    sx=xs[slat_i];box('WL01_RepairSlat',(.034,2*inner-.01,.013),(sx,0,pz1+.004),M['cedar_new'],'Body',bev=.003,segs=2,cuts=2,jit=.0006,seed=14)
    for sgn in (-1,1):_lash(f'WL01_Lash{"LR"[sgn>0]}',(sx,sgn*(inner-.045),pz1+.0105),(1,0,0),(0,1,0),.03,.0,M,'Detail_Lashing')
    # head bar with the handle slot, foot bar at the other end
    hx0,hx1=L/2-.085,L/2-.006;   # ends 6 mm inside the rail ends (flush ends were coplanar)
    head=box('WL01_Head',(hx1-hx0,2*inner+.02,.042),((hx0+hx1)/2,0,pz0+.021),M['cedar_b'],'Body',bev=.007,segs=3,cuts=0,jit=0,seed=15)
    _boolean(head,_cutter('WL01_Slot',(.034,.12,.2),((hx0+hx1)/2+.004,0,.06)))   # bevel first, then cut: a bevel after the boolean left slivers in the slot
    box('WL01_Foot',(.046,2*inner+.02,.064),(-L/2+.029,0,.003+.032),M['cedar_b'],'Body',bev=.006,segs=3,cuts=2,jit=.0008,seed=16)
    for i,x in enumerate((-.24,-.02,.20)):              # battens under the panel (lifted 3 mm: rails and foot carry it)
        box(f'WL01_Batten{i}',(.05,2*inner+.012,pz0+.004-.003),(x,0,.003+(pz0+.004-.003)/2),M['cedar_b'],'Body',bev=.004,segs=2,jit=.0005,seed=20+i)
    for sgn in (-1,1):                                   # wooden pegs through the rails into the battens and the bars
        for x in (-.325,-.24,-.02,.20,.33):
            tube(f'WL01_Peg{"LR"[sgn>0]}{x:+.2f}',[Vector((x,sgn*(W/2-rw/2),rh-.006)),Vector((x,sgn*(W/2-rw/2),rh+.0018))],.0055,M['endgrain'],'Detail_Pegs',sides=8,scale=.05)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        px,py,pz=pos[...,0],pos[...,1],pos[...,2]
        # damp lower end (the foot stands in the water when it is used): darker and cooler, smoother, a soft tide line
        dx=-.17+.035*(noise-.5)+.02*np.sin(py*31);dm=np.clip((dx-px)/.12,0,1)*filled
        col=col*(1-.34*dm[...,None])*(1-.06*dm[...,None]*np.array([1,.2,-.8]));rough=np.clip(rough-.15*dm,0,1)
        # a little moss only in the corners of the foot end, where rails meet the foot bar
        mo=np.clip((-.27-px)/.06,0,1)*np.clip((np.abs(py)-.12)/.05,0,1)*np.clip(cav*1.5+.3,0,1)*np.clip((noise-.45)*4,0,1)*np.clip((onrm[...,2]-.3)/.4,0,1)*filled   # only on faces that look up
        col=col*(1-.45*mo[...,None])+mo[...,None]*np.array([.22,.30,.14])*.45
        # rubbed face: the hollow and the rib crowns are hand-polished, a touch paler and smoother
        up=np.clip((onrm[...,2]-.6)/.3,0,1);rub=up*np.clip((pz-.055)/.02,0,1)*(np.abs(py)<.14)*filled
        col=col*(1+.10*rub[...,None]);rough=np.clip(rough-.10*rub,0,1)
        return col,rough
    return {'paint':paint,'wear':1.1,'grime':1.0,'notes':['lies flat with the ribs up; the reference stands it upright',
            'reference cand-4 is about 2.1 : 1 long; built to the work pack 0.70 × 0.40 m',
            'Detail_Lashing: cord on the repaired slat; Detail_Pegs: peg heads on the rails']}
PROPS['WL01']=WL01

# ---------------- WL02 laundry beating paddle (cand-3) ----------------
def _loft(name,stations,M,mat,grp,N=28,cap0='flat',cap1='round',end_mat=None):
    """a solid lofted along X through cross-sections (x, width, height, zc, p): a superellipse of exponent p
    (4 = boxy head, 2 = round handle). cap0: the x-min end is a flat end-grain face (fan) with its own material;
    cap1: the x-max end closes in a rounded dome."""
    bm=bmesh.new();rings=[]
    def ring(x,w,h,zc,p,sc=1.):
        out=[]
        for k in range(N):
            a=math.tau*k/N;c,s=math.cos(a),math.sin(a)
            y=w/2*sc*math.copysign(abs(c)**(2/p),c);z=zc+h/2*sc*math.copysign(abs(s)**(2/p),s)
            out.append(bm.verts.new((x,y,z)))
        return out
    x0,w0,h0,z0,p0=stations[0]
    rings.append(ring(x0-.004,w0,h0,z0,p0,.9))           # the end face stands 4 mm proud of the last section, its edge rounded over
    for st in stations:rings.append(ring(*st))
    x1,w1,h1,z1,p1=stations[-1]
    for t in (.35,.65,.88):                              # rounded end of the grip
        rings.append(ring(x1+t*w1*.35,w1,h1,z1,p1,math.sqrt(max(1-t*t,.05))))
    rings.sort(key=lambda r:r[0].co.x)
    for a,b in zip(rings,rings[1:]):
        for k in range(N):bm.faces.new((a[k],a[(k+1)%N],b[(k+1)%N],b[k]))
    c0=bm.verts.new((rings[0][0].co.x-.001,0,z0));ends=[bm.faces.new((c0,rings[0][(k+1)%N],rings[0][k])) for k in range(N)]
    c1=bm.verts.new((rings[-1][0].co.x+.004,0,z1));[bm.faces.new((c1,rings[-1][k],rings[-1][(k+1)%N])) for k in range(N)]
    for f in bm.faces:f.smooth=True
    for f in ends:f.smooth=False
    o=finish(name,bm,mat,grp)
    if end_mat:   # end-grain material on the flat striking end
        o.data.materials.append(end_mat)
        uv=o.data.uv_layers['Tiled'].data;zc=stations[0][3]
        for p in o.data.polygons:
            if p.normal.x<-.8:
                p.material_index=1
                for li in p.loop_indices:   # rings round a pith just below the face (a board cut beside the heart, as in cand-3)
                    co=o.data.vertices[o.data.loops[li].vertex_index].co;uv[li].uv=(.43+(co.y+.025)/.5,.52+(co.z-zc+.055)/.5)
    return o
def WL02(M):
    """a cedar beating paddle lying flat: a thick rounded head (thickest at the striking end, showing end grain),
    shoulders narrowing into a round neck bound with hemp, a grip with two finger swells, a flattened knob with a hole and a hanging cord"""
    st=[]   # x, width, height, z-centre, exponent
    for x in np.linspace(0,.46,40):
        if x<.27:   # head: a little wider and thicker towards the striking end, rounded shoulders
            t=x/.27;w=.128+.022*math.sin(min(1,t/.18)*math.pi/2)-.10*max(0,(t-.70)/.30)**1.6
            h=.062-.026*t;p=4.2-2.0*max(0,(t-.6)/.4)
        elif x<.31:t=(x-.27)/.04;w=.05-.014*t;h=.036;p=2.2   # neck, under the binding
        elif x<.415:   # grip: two finger swells
            t=(x-.31)/.105;w=.036+.006*math.sin(t*math.tau*1.0-math.pi/2)**2*(1 if t<.95 else 0);h=w*.95;p=2.0
        else:   # flattened knob with the hole
            t=(x-.415)/.045;w=.036+.016*math.sin(min(1,t*1.4)*math.pi/2);h=.034;p=2.6
        st.append((float(x),w,h,0.,p))
    body=_loft('WL02_Paddle',st,M,M['cedar'],'Body',end_mat=M['endgrain'])
    jitter(body,.0007,seed=31,freq=40)
    _boolean(body,_cutter('WL02_Hole',(.016,.016,.2),(.438,0,0)))
    # hemp binding round the neck
    for i in range(6):
        x=.279+i*.0058;r=.0212+.0010*math.sin(i*1.7)   # starts 9 mm past the shoulder (touching it was coplanar)
        pts=[Vector((x+.0008*math.sin(a*2),r*math.cos(a),r*math.sin(a))) for a in np.linspace(0,math.tau,17)]
        tube(f'WL02_Bind{i}',pts,.0029,M['hemp'],'Body',sides=6,scale=.06)
    # cord through the hole: a loop round the knob, a knot and a frayed tail lying on the ground beside it
    loop=[Vector((.438+.016*math.cos(a),.0,.0+.024*math.sin(a))) for a in np.linspace(-math.pi/2,math.pi*1.5,20)]
    loop=[p+Vector((0,.006*math.sin(i*.8),0)) for i,p in enumerate(loop)]
    loop_o=tube('WL02_CordLoop',loop,.0032,M['hemp'],'Detail_Cord',sides=6,scale=.06)
    # lying flat: tilt so the striking end and the knob both rest on the ground
    for o in parts:o.data.transform(Matrix.Rotation(math.radians(1.8),4,'Y'))
    g=min(v.co.z for o in parts if o['grp']=='Body' for v in o.data.vertices)   # the ground under the paddle
    lz=min(v.co.z for v in loop_o.data.vertices)
    tail=[Vector((.446,-.008,lz+.002)),Vector((.44,-.03,g+.0034)),Vector((.425,-.045,g+.0032)),Vector((.405,-.052,g+.0032)),Vector((.385,-.056,g+.0033))]   # tail lies back along the grip, inside the 0.45 × 0.15 m footprint
    tube('WL02_CordTail',tail,.0032,M['hemp'],'Detail_Cord',sides=6,scale=.06)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=.0075,location=(.44,-.03,g+.006));k=bpy.context.object;k.scale=(1.2,1,.8)
    bpy.ops.object.transform_apply(scale=True);bm=bmesh.new();bm.from_mesh(k.data);bpy.data.objects.remove(k);finish('WL02_Knot',bm,M['hemp'],'Detail_Cord',.06)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        px,py,pz=pos[...,0],pos[...,1],pos[...,2]
        # hand-polished grip: smoother, a touch darker and warmer (oil from hands); striking end paler where it hits the cloth
        grip=np.clip((px-(.31+meta['offset'][0]))/.02,0,1)*np.clip(((.42+meta['offset'][0])-px)/.02,0,1)*filled
        col=col*(1-.08*grip[...,None])*(1+.04*grip[...,None]*np.array([1,.6,.2]));rough=np.clip(rough-.18*grip,0,1)
        strike=np.clip(((.05+meta['offset'][0])-px)/.05,0,1)*filled;col=col*(1+.08*strike[...,None]);rough=np.clip(rough-.06*strike,0,1)
        return col,rough
    return {'paint':paint,'wear':1.2,'notes':['lies flat on its broad face, tilted 1.8 degrees so the striking end and the knob both touch the ground',
            'end grain on the flat striking end uses its own source texture (rings round an off-centre pith, radial checks)',
            'Detail_Cord: the hanging cord loop, knot and tail; the neck binding is part of the body']}
PROPS['WL02']=WL02

# ---------------- WL03 rolled coarse linen (cand-3) ----------------
def WL03(M):
    """a folded linen sheet (1.8 cm thick: coarse cloth folded double) rolled four turns along X, the roll squashed
    under its own weight into a low oval, layers telescoping a little at the ends, the outer edge lifting as a loose
    flap, one loose hemp cord round it with a knot and two hanging ends"""
    turns,r0,step,t=4.0,.036,.0205,.018;N=32                  # samples per turn
    L=.60;ns=13;us=np.linspace(0,1,ns)
    rng=random.Random(303);xoff=[(rng.uniform(-.012,.012),rng.uniform(-.012,.012)) for _ in range(int(turns)+2)]
    def shape(r,th,u,outer_end=0.):
        d=.0045*math.sin(5*th+2.2*u+.7*math.sin(3*u))+.004*math.sin(2*th+3.1*u)+.007*math.sin(th+5.5*u+1)*math.sin(math.pi*u)**.5   # 2π-periodic: neighbouring turns move together; a long diagonal fold
        rr=r+d+outer_end;y=rr*math.cos(th)*1.13;z=rr*math.sin(th)*.92
        if z<-.085:z=-.085+(z+.085)*.28                       # the bottom flattened where it rests on the ground
        return y,z
    th_all=np.linspace(0,math.tau*turns,int(N*turns)+1)
    bm=bmesh.new();cols=[]                                   # one column of vertices per point of the band outline
    outline=[('o',th) for th in th_all]+[('i',th) for th in th_all[::-1]]
    for kind,th in outline:
        turn=int(th/math.tau);x0,x1=-L/2+xoff[turn][0],L/2+xoff[turn][1]
        r=r0+step*th/math.tau-(t if kind=='i' else 0)
        lift=.012*max(0,(th-math.tau*(turns-.35))/(math.tau*.35))**2 if kind=='o' else .012*max(0,(th-math.tau*(turns-.35))/(math.tau*.35))**2   # loose outer flap
        col=[]
        for u in us:
            y,z=shape(r,th,u,lift);col.append(bm.verts.new((x0+(x1-x0)*u,y,z)))
        cols.append(col)
    n=len(cols)
    for a in range(n):
        A,B=cols[a],cols[(a+1)%n]
        for k in range(ns-1):bm.faces.new((A[k],B[k],B[k+1],A[k+1]))
    m=len(th_all);caps=[]
    for k in (0,ns-1):                                       # end faces: a strip across the cloth's thickness all along the spiral
        for j in range(m-1):                                 # (each turn ends at its own x, so one flat cap would not lie in a plane)
            caps.append(bm.faces.new((cols[j][k],cols[j+1][k],cols[n-2-j][k],cols[n-1-j][k])))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=f not in caps
    roll=finish('WL03_Roll',bm,M['linen'],'Body')
    # one loose cord round the roll, a little off the cloth on top, pressed into it underneath
    R_out=r0+step*turns
    cx=.07;cord=[]
    for th in np.linspace(0,math.tau+.25,35):   # runs on past its start so the two cut ends do not meet face to face
        y,z=shape(R_out,th,(cx+L/2)/L)
        k=1+(.075 if z>-.06 else -.03);cord.append(Vector((cx+.004*math.sin(th*3),y*k,z*k+(.004 if z>0 else 0))))
    tube('WL03_Cord',cord,.0045,M['hemp'],'Body',sides=6,scale=.06)
    ky,kz=shape(R_out,math.radians(70),(cx+L/2)/L)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=7,radius=.011,location=(cx,ky*1.08,kz*1.08+.006));k=bpy.context.object;k.scale=(1,1.2,.8)
    bpy.ops.object.transform_apply(scale=True);bm=bmesh.new();bm.from_mesh(k.data);bpy.data.objects.remove(k);finish('WL03_Knot',bm,M['hemp'],'Body',.06)
    for i,(dy,dx) in enumerate(((-.02,.012),(-.03,-.01))):     # two ends hanging from the knot down the front of the roll
        p0=Vector((cx+dx*.35,ky*1.08+dy*.15,kz*1.08+.004));pts=[p0]   # starts inside the knot, each end from its own point
        for s_ in np.linspace(.2,1,6):
            th=math.radians(70)-s_*math.radians(60);y,z=shape(R_out+.016,th,(cx+L/2)/L);pts.append(Vector((cx+dx*s_,y*1.07+dy*s_*.2,z*1.07)))
        tube(f'WL03_CordEnd{i}',pts,.004,M['hemp'],'Detail_CordEnds',sides=6,scale=.06)
    # a few loose threads at the frayed outer edge
    th=math.tau*turns-.05;rng=random.Random(9)
    for i in range(9):
        x=-L/2+.05+i*.06+rng.uniform(-.02,.02);u=(x+L/2)/L;y,z=shape(R_out-.004,th,u,.012)
        p0=Vector((x,y,z));d=Vector((rng.uniform(-.2,.2),math.cos(th+.6)*.5,math.sin(th+.6)*.5-.6)).normalized()
        tube(f'WL03_Thread{i}',[p0,p0+d*.012,p0+d*.024+Vector((0,0,-.004))],.0011,M['linen'],'Detail_Fray',sides=4,scale=.05,caps=False)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        px,py,pz=pos[...,0],pos[...,1],pos[...,2];x0=meta['offset'][0]-L/2
        # the damp corner: one end, lower half, darker and cooler with a soft tide line
        dm=np.clip(((x0+.17+.04*(noise-.5))-px)/.08,0,1)*np.clip(((.10+.03*noise)-pz)/.05,0,1)*filled
        col=col*(1-.30*dm[...,None])*(1-.05*dm[...,None]*np.array([1,.3,-.6]));rough=np.clip(rough-.10*dm,0,1)
        return col,rough
    return {'paint':paint,'wear':.5,'grime':.7,'uv_angle':40,'notes':['a folded sheet rolled four turns; the end faces show the layers',
            'Detail_CordEnds: the two hanging cord ends; Detail_Fray: loose threads on the outer edge; the cord loop and knot are part of the body']}
PROPS['WL03']=WL03

# ---------------- WL04 two folded stacks of washed linen (cand-12) ----------------
def _layer(name,w,d,h,c,M,mat,grp,seed,rot=0.,sag=.004):
    """one folded cloth layer: a slab with its edges rounded over like a fold, a slight sag in the middle,
    uneven corners. Bevel first, then subdivide only the long edges (cuts through the 2–4 cm thickness folded the bevel)."""
    o=finish(name,box_bm((w,d,h)),mat,grp);bevel(o,h*.32,3,angle=40)
    bm=bmesh.new();bm.from_mesh(o.data)
    long=[e for e in bm.edges if e.calc_length()>.045]
    if long:bmesh.ops.subdivide_edges(bm,edges=long,cuts=3,use_grid_fill=True)
    bm.to_mesh(o.data);bm.free()
    r=random.Random(seed);ph=[r.uniform(0,6) for _ in range(6)]
    for v in o.data.vertices:
        x,y,z=v.co;u,vv=x/(w/2),y/(d/2)
        if z>0:v.co.z-=sag*max(0,1-u*u)*max(0,1-vv*vv)        # top sags where nothing holds it up
        v.co.z-=.007*max(0,abs(u)-.78)/.22+.003*max(0,abs(vv)-.8)/.2   # the edges hang down a little over the layer below (front/back less: they cut into the layer under it)
        v.co.z+=.0025*math.sin(3.1*u+ph[0])*math.sin(2.3*vv+ph[1])*(1 if z>0 else .3)
        v.co.x+=.006*math.sin(2*vv+ph[2])*abs(u)**3; v.co.y+=.006*math.sin(2*u+ph[3])*abs(vv)**3   # corners not square
    o.data.transform(Matrix.Rotation(rot,4,'Z'));o.data.transform(Matrix.Translation(c));return o
def _sheet(name,pts_u,pts_v,M,mat,grp,t=.004):
    """a thin draped cloth flap with thickness: a grid of points P[i][j] (rows across the flap), offset ±t/2 along its normal"""
    bm=bmesh.new();P=[[Vector(p) for p in row] for row in pts_u];nu,nv=len(P),len(P[0]);top=[];bot=[]
    for i in range(nu):
        tr=[];br=[]
        for j in range(nv):
            a=P[min(i+1,nu-1)][j]-P[max(i-1,0)][j];b=P[i][min(j+1,nv-1)]-P[i][max(j-1,0)];n=a.cross(b).normalized()
            tr.append(bm.verts.new(P[i][j]+n*t/2));br.append(bm.verts.new(P[i][j]-n*t/2))
        top.append(tr);bot.append(br)
    for i in range(nu-1):
        for j in range(nv-1):
            bm.faces.new((top[i][j],top[i+1][j],top[i+1][j+1],top[i][j+1]));bm.faces.new((bot[i][j+1],bot[i+1][j+1],bot[i+1][j],bot[i][j]))
    for i in range(nu-1):
        bm.faces.new((bot[i][0],bot[i+1][0],top[i+1][0],top[i][0]));bm.faces.new((top[i][nv-1],top[i+1][nv-1],bot[i+1][nv-1],bot[i][nv-1]))
    for j in range(nv-1):
        bm.faces.new((top[0][j],top[0][j+1],bot[0][j+1],bot[0][j]));bm.faces.new((bot[nu-1][j],bot[nu-1][j+1],top[nu-1][j+1],top[nu-1][j]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    return finish(name,bm,mat,grp,.5)
def WL04(M):
    """two piles side by side, 5 cm apart: the left one taller with one muted blue cloth in it, the right one lower and all
    natural linen with a patch on top; every layer is a folded slab with rounded fold edges; the lower layers damp"""
    piles=[(-.16,[('linen_b',.046,.46),('linen',.042,.45),('linen_blue',.040,.44),('linen',.040,.45),('linen_b',.038,.44),('linen',.036,.43)],1),
           (.16,[('linen',.046,.43),('linen_b',.042,.42),('linen',.040,.42),('linen_b',.036,.41),('linen',.034,.40)],2)]
    tops={}
    for px,layers,pi in piles:
        z=0;r=random.Random(40+pi)
        for li,(mat,h,d) in enumerate(layers):
            w=.27-.006*li+r.uniform(-.01,.01);c=(px+r.uniform(-.012,.012),r.uniform(-.007,.007),z+h/2)
            _layer(f'WL04_P{pi}L{li}',w,d-.006*li+r.uniform(-.008,.004),h,c,M,M[mat],'Body',seed=100*pi+li,rot=math.radians(r.uniform(-4,4)),sag=.003+.002*li/len(layers))
            z+=h-.004                                      # each layer sinks 4 mm into the one below (flat on flat would be coplanar)
        tops[pi]=(px,z,parts[-1])
    # a corner of the left pile's top cloth folded back and hanging over the front edge
    def surf(o,x,y,r=.03):   # the real height of a top layer near (x, y): it sags and its edges hang
        near=sorted(o.data.vertices,key=lambda v:(v.co.x-x)**2+(v.co.y-y)**2)[:8]   # the 8 nearest vertices (the grid is a few cm apart)
        return max(v.co.z for v in near)
    px,zt,top=tops[1];zt=surf(top,px-.07,-.16)-.006;rows=[]   # the folded corner starts 9 mm inside the top cloth, 3 cm in from its front edge
    for i,s in enumerate(np.linspace(0,1,7)):
        row=[]
        for j,tt in enumerate(np.linspace(0,1,5)):
            x=px-.125+.11*tt*(1-.45*s);a=s*math.pi*.55   # a triangle-ish corner, narrowing as it falls
            y=-.17-.05*math.sin(a);zz=zt-.003+.05*(math.cos(a)-1)
            row.append((x+.004*math.sin(j*2+s*4),y-.012*s+.003*math.sin(i*1.7),zz+.002*math.sin(j*3.1)))
        rows.append(row)
    _sheet('WL04_Flap',rows,None,M,M['linen'],'Detail_Flap')
    # the patched corner on the right pile's top
    px,zt,top=tops[2];zt=surf(top,px+.07,-.12,.045);bm=box_bm((.07,.06,.006),(px+.07,-.12,zt))   # 3 mm proud of the highest point under it
    o=finish('WL04_Patch',bm,M['linen_b'],'Detail_Patch',.3)
    o.data.transform(Matrix.Translation((-(px+.07),.12,0))@Matrix.Identity(4));o.data.transform(Matrix.Rotation(math.radians(12),4,'Z'));o.data.transform(Matrix.Translation((px+.07,-.12,0)))
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        px,py,pz=pos[...,0],pos[...,1],pos[...,2]
        # damp lower layers: a darker, cooler band up from the ground with an uneven tide line, a little green-brown at the very bottom
        dm=np.clip(((.075+.03*(noise-.5)+.012*np.sin(px*40+py*23))-pz)/.03,0,1)*filled
        col=col*(1-.28*dm[...,None])*(1-.05*dm[...,None]*np.array([1,.3,-.5]));rough=np.clip(rough-.08*dm,0,1)
        bot=np.clip((.018-pz)/.018,0,1)*np.clip((noise-.4)*3,0,1)*filled;col=col*(1-.35*bot[...,None])+bot[...,None]*np.array([.25,.27,.15])*.35
        # damp darker edges where the cloth folds over (cavities between layers)
        col=col*(1-.18*cav[...,None]);return col,rough
    return {'paint':paint,'wear':.3,'grime':.9,'uv_angle':40,'ao_k':.3,'notes':['two separate piles 5 cm apart (left 6 layers with the blue cloth, right 5 layers)',
            'each layer sinks 4 mm into the one below so no two faces lie flat on each other',
            'Detail_Flap: the corner folded back over the front edge; Detail_Patch: the patch on the right pile']}
PROPS['WL04']=WL04

# ---------------- WL05 stone dish with a laundry-ash cake (cand-4) ----------------
def WL05(M):
    """one oval fieldstone carved into a shallow dish: walls flaring out, an uneven rim worn low on one side, a recess
    about 5 cm deep; a pressed ash cake in it; an old crack down the front held by two iron staples; a few ash crumbs"""
    A,B,NS=.19,.14,72;rng=random.Random(505);ph=[rng.uniform(0,6) for _ in range(8)]
    prof=[(0,0),(.55,0),(.86,0),(.93,.012),(.985,.045),(1.,.072),(.985,.084),(.94,.090),(.88,.088),(.83,.072),(.79,.050),(.75,.036),(.62,.031),(.35,.030),(0,.030)]
    rim_i=(5,6,7,8)                                          # the rim rows get the uneven height
    def irr(th):return 1+.035*math.sin(2*th+ph[0])+.02*math.sin(3*th+ph[1])+.012*math.sin(7*th+ph[2])   # not a perfect oval
    def rimz(th):return .007*math.sin(2*th+ph[3])+.004*math.sin(5*th+ph[4])-.012*math.exp(-((math.atan2(math.sin(th-1.1),math.cos(th-1.1)))/.45)**2)   # worn low on one side
    bm=bmesh.new();rings=[]
    for i,(r,z) in enumerate(prof):
        if r==0:rings.append(None);continue
        ring=[]
        for k in range(NS):
            th=math.tau*k/NS;f=irr(th);zz=z+(rimz(th) if i in rim_i else 0)*(1 if i!=5 else .7)
            ring.append(bm.verts.new((r*A*f*math.cos(th),r*B*f*math.sin(th),zz)))
        rings.append(ring)
    c0=bm.verts.new((0,0,0));c1=bm.verts.new((0,0,.030))
    seq=rings[1:-1]
    for k in range(NS):bm.faces.new((c0,seq[0][(k+1)%NS],seq[0][k]))
    for a,b in zip(seq,seq[1:]):
        for k in range(NS):bm.faces.new((a[k],a[(k+1)%NS],b[(k+1)%NS],b[k]))
    for k in range(NS):bm.faces.new((c1,seq[-1][k],seq[-1][(k+1)%NS]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    dish=finish('WL05_Dish',bm,M['stone'],'Body',.4);jitter(dish,.0032,seed=54,freq=18);jitter(dish,.0016,seed=55,freq=60)   # broad chisel bumps, then small ones
    # the ash cake: a pressed round cake, a little domed, sitting in the recess (3 mm into the floor)
    bm=bmesh.new();cr=[];NC=40
    for i,(rr,zz) in enumerate(((.0,.027),(.92,.027),(1.,.042),(.99,.076),(.93,.088),(.6,.094),(0,.095))):   # top a little above the rim, as in cand-4
        if rr==0:cr.append(None);continue
        cr.append([bm.verts.new((rr*.088*math.cos(math.tau*k/NC)*(1+.03*math.sin(3*math.tau*k/NC+1)),rr*.078*math.sin(math.tau*k/NC),zz+.002*math.sin(4*math.tau*k/NC))) for k in range(NC)])
    a0=bm.verts.new((0,0,.027));a1=bm.verts.new((0,0,.095));seq=cr[1:-1]
    for k in range(NC):bm.faces.new((a0,seq[0][(k+1)%NC],seq[0][k]))
    for a,b in zip(seq,seq[1:]):
        for k in range(NC):bm.faces.new((a[k],a[(k+1)%NC],b[(k+1)%NC],b[k]))
    for k in range(NC):bm.faces.new((a1,seq[-1][k],seq[-1][(k+1)%NC]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    for f in bm.faces:f.smooth=True
    cake=finish('WL05_AshCake',bm,M['ash'],'Body',.3);cake.data.transform(Matrix.Translation((.012,.006,0)));jitter(cake,.0012,seed=56,freq=70)
    # two iron staples across the old crack on the front wall (-Y)
    for i,zc in enumerate((.030,.058)):
        th=-math.pi/2+.18;f=irr(th);rr=(.985 if zc>.05 else .95)
        p=Vector((rr*A*f*math.cos(th),rr*B*f*math.sin(th),zc));n=Vector((math.cos(th)/A,math.sin(th)/B,0)).normalized();t_=Vector((-n.y,n.x,0))
        pts=[p-t_*.016-n*.006,p-t_*.016+n*.004,p+t_*.016+n*.004,p+t_*.016-n*.006]
        tube(f'WL05_Staple{i}',pts,.0028,M['iron'],'Detail_Staples',sides=6,scale=.05)
    # ash crumbs in the recess, round the cake
    for i,(x,y,r_) in enumerate(((-.085,.03,.007),(-.07,-.05,.006),(.095,-.035,.0055),(.08,.055,.005),(-.03,.075,.0045))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r_,location=(x,y,.031+r_*.25));k=bpy.context.object;k.scale=(1.2,1,.55);bpy.ops.object.transform_apply(scale=True)
        bm=bmesh.new();bm.from_mesh(k.data);bpy.data.objects.remove(k);finish(f'WL05_Crumb{i}',bm,M['ash'],'Detail_Crumbs',.2)
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        o_=meta['offset'];px,py,pz=pos[...,0]-o_[0],pos[...,1]-o_[1],pos[...,2]-o_[2]
        rn=np.sqrt((px/A)**2+(py/B)**2);up=np.clip((onrm[...,2]-.5)/.4,0,1)
        # wet ring on the recess floor round the cake: darker and glossy; a pale tide line at its outer edge
        floor=up*np.clip((.045-pz)/.008,0,1)*np.clip((rn-.30)/.05,0,1)*filled
        wet=floor*np.clip((.66-rn+.03*(noise-.5))/.05,0,1);col=col*(1-.38*wet[...,None])*(1-.06*wet[...,None]*np.array([1,.3,-.6]));rough=np.clip(rough-.35*wet,0,1)
        tide=floor*np.exp(-((rn-.69-.02*(noise-.5))/.018)**2);col=col*(1-tide[...,None]*.1)+tide[...,None]*np.array([.62,.61,.58])*.25
        # ash traces: pale grey smears on the floor and lower inner wall
        ash=np.clip((pz<.06)*(rn<.86)*(rn>.3),0,1)*np.clip((noise-.55)*3,0,1)*filled*(1-wet);col=col*(1-.4*ash[...,None])+ash[...,None]*np.array([.62,.61,.58])*.4
        # dry cracks on the ash cake top (thin dark lines from near the middle)
        cake_top=(pz>.07)*(rn<.5)*filled;ang=np.arctan2(py,px);cl=np.zeros_like(pz)
        for a0 in (.4,2.2,3.6,5.1):cl=np.maximum(cl,np.exp(-((np.angle(np.exp(1j*(ang-a0-.15*np.sin(rn*30))))*np.maximum(rn,.05))/.003)**2)*np.clip((rn-.06)/.05,0,1))
        col=col*(1-.45*(cl*cake_top)[...,None])
        # the old crack down the front wall, under the staples
        th=-math.pi/2+.18;cx_,cy_=A*math.cos(th),B*math.sin(th);crack=np.exp(-(((px-cx_)*math.sin(th)-(py-cy_)*math.cos(th)+.004*np.sin(pz*300))/.0025)**2)*(np.abs(np.arctan2(py,px)-th)<.5)*(rn>.85)*filled
        col=col*(1-.55*crack[...,None]);return col,rough
    return {'paint':paint,'wear':1.3,'grime':1.0,'uv_angle':50,'notes':['carved from one fieldstone, the same warm-grey stone as BM05/BM06',
            'the wet ring, the ash traces, the cake cracks and the wall crack are painted; the staples and crumbs are Detail_ meshes']}
PROPS['WL05']=WL05
