# DP17 小石與碎石 (eight kinds) — exec'd by build_floor.py after floor_base.py.
# Stones: a noisy sphere (rounded) or a sphere cut by random planes (angular), sunk 30–40 % into the ground (the part
# under z = 0 is kept, so a stone set on uneven ground never floats); moss is a thin shell over the upward faces.
from mathutils import noise as _mn
import zlib as _zl

def _stone_sources(S):
    K.rng=np.random.default_rng(1701)   # D2 stone (V2–V6): cool grey to blue-grey, darker cracks, a few pale lichen flecks
    big=fbm(3,3);mid=fbm(14,3);fine=fbm(60,2);crack=np.clip((.34-fbm(70,2))*6,0,1)*np.clip((fbm(6,2)-.45)*3,0,1)
    lich=np.clip((fbm(40,3)-.74)*6,0,1);t=np.clip(.5+.45*(big-.5)+.35*(mid-.5)+.2*(fine-.5),0,1)
    col=lerp((.25,.25,.25),(.50,.50,.48),t)*(1-.4*crack[...,None])   # D2 V6: a warm mid grey with fine painted facets, not blue
    col=col*(1-.55*lich[...,None])+lich[...,None]*np.array([.52,.55,.48])*.55
    S['stone']=(col,1.1*mid+.5*big-1.2*crack,2.6,.82,0,0)
    S['stone_dark']=(col*.72,1.1*mid+.5*big-1.2*crack,2.6,.86,0,0)   # the wetter lower part, sunk in the soil
SRC_HOOKS.append(_stone_sources)

def _stone(name,c,size,M,grp,seed,round_=1.,cuts=0,sink=.35,moss=0.,moss_thr=.5,subdiv=4,lump=.12,taper=0.,lean=0.):
    """one stone of size (x, y, z) m centred at c (x, y): rounded (round_ 1) or cut flat by `cuts` random planes; the lowest
    `sink` of its height under the ground; moss: a 4 mm shell over the faces looking up (amount 0–1)"""
    """(Blender's icosphere: subdivisions 3 = 320 triangles, 4 = 1,280)"""
    r_=_rnd.Random(seed);c=Vector(c);sx,sy,sz=size
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=subdiv,radius=1.)
    off=Vector((r_.uniform(0,50),r_.uniform(0,50),r_.uniform(0,50)))
    planes=[(Vector((r_.uniform(-1,1),r_.uniform(-1,1),r_.uniform(-.3,1))).normalized(),r_.uniform(.45,.75)) for _ in range(cuts)]
    for v in bm.verts:
        p=v.co.copy();n=_mn.noise(p*1.3+off)*lump+_mn.noise(p*3.1+off)*lump*.35
        p=p*(1+n);p.z*=1.0
        for pn,d in planes:   # flat fracture faces
            k=p.dot(pn)
            if k>d:p-=pn*(k-d)*.97
        k=1-taper*max(0.,(p.z+1)/2)**1.3   # taper: narrower toward the top (a wedge / pointed stone)
        v.co=Vector((p.x*sx/2*k+lean*sx*max(0.,(p.z+1)/2)**2,p.y*sy/2*k,p.z*sz/2))
    lo=min(v.co.z for v in bm.verts);hi=max(v.co.z for v in bm.verts)
    for v in bm.verts:v.co+=Vector((c.x,c.y,-lo-(hi-lo)*sink))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.normal_update()
    for f in bm.faces:f.smooth=not any(abs(f.normal.dot(pn))>.985 for pn,_ in planes)   # the fracture faces stay flat-shaded: crisp edges
    top_z=hi-lo-(hi-lo)*sink;bm.verts.index_update()
    mossf=[]
    if moss>0:
        for f in bm.faces:
            cc=f.calc_center_median();q=_mn.noise(cc*9+off)
            q2=_mn.noise(cc*3.5+off*1.7)
            if f.normal.z+.35*q+.45*q2>moss_thr+(1-moss)*.45 and cc.z>top_z*.25:mossf.append(f)   # q2: large holes, so the moss sits in patches
    if mossf:
        bm2=bmesh.new();vm={}
        for f in mossf:
            vs=[]
            for v in f.verts:
                if v.index not in vm:vm[v.index]=bm2.verts.new(v.co.copy())
                vs.append(vm[v.index])
            bm2.faces.new(vs)
        bm2.normal_update();bnd={v for e in bm2.edges if e.is_boundary for v in e.verts}
        for _ in range(8):   # relax the patch outline along itself: no stair-step edge following the stone's triangles
            new={}
            for v in bnd:
                nb=[e.other_vert(v) for e in v.link_edges if e.is_boundary]
                if len(nb)==2:new[v]=v.co*.4+(nb[0].co+nb[1].co)*.3
            for v,co in new.items():v.co=co
        for v in bm2.verts:v.co+=v.normal*(.004+.003*max(0,_mn.noise(v.co*14+off)) if v not in bnd else -.003)
        for f in bm2.faces:f.smooth=True
        finish(name+'_moss',bm2,M['moss'],grp,scale=.15)
    o=finish(name,bm,M['stone'],grp,scale=max(sx,sy)*.9+.05)
    o.data.materials.append(M['stone_dark'])
    for i,p in enumerate(o.data.polygons):
        if p.center.z<.005:p.material_index=1
    return o

O_GROUND='footprint centre, z = 0 on the ground; the lower 30–40 % of each stone is under the ground'
def dp17_01(M):
    """圓小石 (DP17A-cand-4): one small rounded stone, 6 cm, half buried"""
    _stone('DP17_01',(0,0),(.062,.052,.045),M,'Body',17101,cuts=3,sink=.38,subdiv=3,lump=.10)
    return {'grime':.5,'wear':.6,'origin_text':O_GROUND}
def dp17_02(M):
    """角石一小群 (DP17B-cand-3): five small angular stones 3–8 cm, half buried, 0.2 m across"""
    r_=_rnd.Random(17201)
    for i,(x,y,s,h) in enumerate(((0,0,.07,.11),(-.065,.03,.05,.05),(.06,-.02,.045,.05),(.02,.06,.035,.035),(-.04,-.05,.03,.03))):
        _stone(f'DP17_02_s{i}',(x,y),(s,s*r_.uniform(.7,.9),h),M,'Body',17210+i,cuts=6,sink=.3,subdiv=3 if i==0 else 2,lump=.08,taper=.55 if i==0 else .3)
    return {'grime':.5,'wear':.6,'origin_text':O_GROUND}
def dp17_03(M):
    """扁平石 (DP17C-cand-2): a flat stone 0.15 m, 5 cm thick, half buried, thin moss on top"""
    _stone('DP17_03',(0,0),(.16,.12,.06),M,'Body',17301,cuts=4,sink=.4,moss=.55,moss_thr=.62,lump=.09)
    return {'grime':.5,'wear':.6,'origin_text':O_GROUND}
def dp17_04(M):
    """圓苔石 (DP17D-cand-1): a rounded stone 0.2 m, moss on top and one side"""
    _stone('DP17_04',(0,0),(.20,.17,.15),M,'Body',17401,cuts=3,sink=.35,moss=.55,moss_thr=.5,lump=.12)
    return {'grime':.5,'wear':.6,'origin_text':O_GROUND}
def dp17_05(M):
    """裂角石 (DP17E-cand-1): an angular broken stone 0.25 m with sharp edges, half buried"""
    _stone('DP17_05',(0,0),(.26,.16,.30),M,'Body',17501,cuts=7,sink=.25,lump=.06,taper=.75,lean=.12)
    return {'grime':.5,'wear':.7,'origin_text':O_GROUND}
def dp17_06(M):
    """兩顆一對 (DP17F-cand-1): two stones 0.25 and 0.15 m lying together, moss in the gap"""
    _stone('DP17_06_a',(-.03,0),(.25,.2,.18),M,'Body',17601,cuts=4,sink=.35,moss=.45,moss_thr=.55)
    _stone('DP17_06_b',(.15,-.02),(.15,.13,.11),M,'Body',17602,cuts=4,sink=.35,moss=.45,moss_thr=.55)
    _pad('DP17_06_gap',(.085,-.01,0),.05,.07,.02,M,'Body',17603,segs=14,depth=.01)
    return {'grime':.5,'wear':.6,'origin_text':O_GROUND}
def dp17_07(M):
    """苔帽圓石 (DP17G-cand-2): a rounded stone 0.3 m, 0.18 m tall, a cap of moss and lichen spots"""
    _stone('DP17_07',(0,0),(.30,.26,.24),M,'Body',17701,cuts=3,sink=.3,moss=.6,moss_thr=.5,lump=.11)
    return {'grime':.5,'wear':.6,'origin_text':O_GROUND}
def dp17_08(M):
    """大石 (DP17H-cand-1): a large stone 0.4 m, 0.22 m tall, one flat face, moss on top, lichen on the side"""
    _stone('DP17_08',(0,0),(.40,.33,.30),M,'Body',17801,cuts=4,sink=.3,moss=.5,moss_thr=.55,lump=.11)
    return {'grime':.5,'wear':.6,'origin_text':O_GROUND}

TABLE.update({'DP17_01':('PebbleRound',(.08,.08,.06),'standard'),'DP17_02':('PebbleCluster',(.24,.20,.10),'standard'),
 'DP17_03':('StoneFlatMossy',(.18,.15,.06),'standard'),'DP17_04':('StoneRoundMossy',(.24,.21,.14),'standard'),
 'DP17_05':('StoneAngular',(.28,.20,.26),'standard'),'DP17_06':('StonePair',(.45,.24,.16),'standard'),
 'DP17_07':('StoneMossCap',(.34,.30,.24),'standard'),'DP17_08':('StoneLarge',(.44,.38,.26),'standard')})
PROPS.update({'DP17_01':dp17_01,'DP17_02':dp17_02,'DP17_03':dp17_03,'DP17_04':dp17_04,'DP17_05':dp17_05,'DP17_06':dp17_06,'DP17_07':dp17_07,'DP17_08':dp17_08})
