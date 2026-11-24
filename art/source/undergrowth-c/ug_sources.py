# UG leaf sources (read by build_ug.make_sources after the shared and YP ones; own seeds). Each is one leaf drawn over the whole
# 0–1 square in the leaf space of ug_shapes.py, so a leaf mesh with keep_uv lines up with its own veins and edge.
# E[name] = (albedo, height, normal strength, roughness, metallic, glow).
K.rng=np.random.default_rng(8201)
# UG02 heart leaf: dark blue-green, wet, a pale main vein and five pairs of curving side veins from the base, the edge a little darker
_x,_y=leaf_grid(HEART,K.R);_ins=inside(HEART,_x,_y)
_v=np.clip(1-np.abs(_y)/(.010+.010*(1-_x)),0,1)*(_x>0)*(_x<.97)           # main vein, tapering
for _a,_c in ((.35,.25),(.70,.30),(1.15,.22),(1.75,.15),(2.35,.10)):        # side veins: angle from the midrib at the base, curve towards the tip
    for _s in (1,-1):
        _t=np.linspace(0,1,9);_px=np.cos(_a*(1-_t*.55))*_t*(.95-.25*_a/2.4);_py=_s*np.sin(_a*(1-_t*.55))*_t*(.42+.05*_a)
        _d,_p=poly_dist(_x,_y,list(zip(_px,_py)));_v=np.maximum(_v,np.clip(1-_d/(.007*(1.2-_p)),0,1)*(1-_p*.6))
_fn=fbm(6,3);_e=np.clip(1-np.abs(_y)/.42,0,1)
_alb=lerp((.105,.205,.175),(.215,.335,.265),np.clip(.45+.55*(_fn-.5)+.25*_e,0,1))
_alb=_alb*(1-.55*_v[...,None])+_v[...,None]*.55*np.array([.48,.58,.42])
E['ug_heart_red']=(np.clip(_alb*np.array([2.3,.95,.55])+np.array([.04,0,0]),0,1),.8*_v,1.2,.55,0,0)   # a few turning red-brown (UG06)
# 2026-11-25: the green moved from blue-green to a deep moss green and the roughness raised .40 → .62 (in URP the old leaf read
# teal and glossy: smoothness .60 mirrored the grey-blue sky); the red-brown leaves above keep the old base
_alb=lerp((.110,.210,.120),(.230,.345,.180),np.clip(.45+.55*(_fn-.5)+.25*_e,0,1))
_alb=_alb*(1-.55*_v[...,None])+_v[...,None]*.55*np.array([.50,.58,.38])
E['ug_heart']=(_alb,.8*_v-.25*np.clip(1-_e*2.5,0,1),1.2,.62,0,0)
# UG01 fern pinna (a five-vertex pinna: stalk at v = 0, tip at v = 1, edges at u = 0 / 1): blue-green, a paler midrib, toothed darker edge
_u=X+0*Y;_w=Y+0*X;_m=np.clip(1-np.abs(_u-.5)/.035,0,1)*(_w<.95)
_tooth=np.clip(np.sin(_w*math.pi*26)*.5+.5,0,1)*np.clip(np.abs(_u-.5)*2-.55,0,1)*2
_alb=lerp((.150,.280,.150),(.290,.440,.220),np.clip(.5+.6*(fbm(5,3)-.5)+.25*_w,0,1))*(1-.30*_tooth[...,None])   # 2026-11-25: less blue (was .15,.29,.21 → .29,.45,.32)
_sv=np.clip(1-np.abs(((_w*14+np.abs(_u-.5)*6)%1)-.5)/.08,0,1)*np.clip(np.abs(_u-.5)*4,0,1)*.4   # faint side veins
_alb=_alb*(1+.30*_m[...,None]+.12*_sv[...,None])
E['ug_pinna']=(_alb,.6*_m+.3*_sv-.3*_tooth,1.0,.72,0,0)   # roughness .55 → .72 (it read glossy in URP)
# old fronds: dull withered grey-brown, close to the soil and litter (a saturated russet read as orange dashes at distance)
E['ug_pinna_dead']=(lerp((.15,.12,.085),(.33,.27,.19),np.clip(.5+.7*(fbm(5,3)-.5)+.15*_w,0,1))*(1-.30*_tooth[...,None]),.6*_m-.3*_tooth,1.0,.90,0,0)
# fern stalk and crown: dark brown-green, scaly
E['ug_rachis']=(lerp((.10,.12,.07),(.24,.24,.12),np.clip(.5+.7*(fbm(5,3,aniso=12)-.5),0,1)),.6*fbm(30,2,aniso=10),1.0,.70,0,0)
E['ug_scale']=(lerp((.18,.10,.05),(.40,.24,.12),np.clip(.5+.8*(fbm(12,3)-.5),0,1)),.9*fbm(40,2),1.4,.80,0,0)
# UG03 strap leaf (u across, v along): glossy dark green, a dark sunken midrib, fine parallel side veins
_m=np.clip(1-np.abs(_u-.5)/.03,0,1)
_sv=np.clip(1-np.abs(((_w*40+np.abs(_u-.5)*9)%1)-.5)/.10,0,1)*.35
_alb=lerp((.08,.17,.07),(.21,.33,.14),np.clip(.5+.6*(fbm(5,3,aniso=4)-.5)+.2*np.abs(_u-.5),0,1))
_alb=_alb*(1-.45*_m[...,None])*(1+.10*_sv[...,None])+_m[...,None]*np.array([.06,.03,.02])
E['ug_strap']=(_alb,-.7*_m+.25*_sv,1.0,.38,0,0)
E['ug_strap_dead']=(lerp((.40,.34,.12),(.62,.54,.24),np.clip(.5+.7*(fbm(5,3,aniso=4)-.5),0,1))*(1-.35*_m[...,None]-.4*np.clip((fbm(14,3)-.62)*4,0,1)[...,None]),-.5*_m,1.0,.75,0,0)
# UG04 palmate leaf: dark green, pale veins running out to each lobe
_x,_y=leaf_grid(PALM,K.R);_a=np.arctan2(_y,_x);_r=np.hypot(_x,_y);_v=np.zeros(_x.shape)
for _k in range(5):
    _ang=math.radians(150)-(_k+.5)*math.radians(300)/5
    _d,_p=poly_dist(_x,_y,[(0,0),(math.cos(_ang)*.9,math.sin(_ang)*.9)]);_v=np.maximum(_v,np.clip(1-_d/(.012*(1.1-_p)),0,1))
_alb=lerp((.10,.20,.09),(.22,.34,.15),np.clip(.5+.6*(fbm(6,3)-.5)+.2*_r,0,1))*(1+.45*_v[...,None])
E['ug_palm']=(_alb,.6*_v,1.0,.60,0,0)
# UG04 petal: white, a faint greenish-pink base, fine veins along the petal
_x,_y=leaf_grid(PETAL,K.R);_vv=np.clip(1-np.abs(((np.arctan2(_y,_x+.05)*9)%1)-.5)/.12,0,1)*.25
_alb=lerp((.80,.80,.74),(.95,.95,.91),np.clip(.6+.5*(fbm(5,3)-.5),0,1))*(1-.06*_vv[...,None])
_alb=_alb*(1-np.clip(.25-_x,0,.25)[...,None]*np.array([.6,.2,.4]))
E['ug_petal']=(_alb,.2*_vv,.5,.55,0,0)
E['ug_stem']=(lerp((.16,.22,.10),(.30,.36,.16),np.clip(.5+.6*(fbm(5,3,aniso=10)-.5),0,1)),.3*fbm(30,2,aniso=10),.6,.65,0,0)
E['ug_redstem']=(lerp((.26,.13,.10),(.42,.30,.18),np.clip(.5+.7*(fbm(5,3,aniso=10)-.5),0,1)),.3*fbm(30,2,aniso=10),.6,.55,0,0)
# UG05 dead leaves: dry russet / ochre with darker veins and spots (the colour of each leaf is varied again in the paint step)
for _nm,_P in (('ug_oval',OVAL),('ug_oak',OAK)):
    _x,_y=leaf_grid(_P,K.R);_m=np.clip(1-np.abs(_y)/.012,0,1)*(_x>0)*(_x<.96)
    _sv=np.clip(1-np.abs(((_x*7-np.abs(_y)*5)%1)-.5)/.07,0,1)*np.clip(np.abs(_y)*8,0,1)*.6
    _sp=np.clip((fbm(18,3)-.66)*5,0,1)
    _alb=lerp((.36,.20,.09),(.66,.44,.20),np.clip(.5+.7*(fbm(4,3)-.5),0,1))*(1-.35*_m[...,None]-.22*_sv[...,None]-.4*_sp[...,None])
    E[_nm]=(_alb,.6*_m+.35*_sv-.3*_sp,1.2,.82,0,0)
E['ug_litter']=(lerp((.10,.07,.04),(.30,.20,.11),np.clip(.5+.9*(fbm(8,3)-.5),0,1)),.8*fbm(20,3),1.6,.92,0,0)
