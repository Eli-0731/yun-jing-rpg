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
