# YP sources (read by build_yp.py after the shared ones; own seeds, so the shared ones keep their textures).
# E[name] = (albedo, height, normal strength, roughness, metallic, glow) — the same tuple as in build_vg.make_sources.
K.rng=np.random.default_rng(3501)   # YP06: a woven rush mat — flat strips over and under, 30 to a 0.5 m tile, straw gold going grey
_su=np.floor(X*30);_sv=np.floor(Y*30);_ch=((_su+_sv)%2)>0
_fu=np.abs(((X*30)%1)-.5)*2;_fv=np.abs(((Y*30)%1)-.5)*2
_hg=np.where(_ch,1-_fu**3,1-_fv**3)*.8+np.where(_ch,.3,0)
_ti=np.where(_ch,np.sin(_su*12.9898+3)*.5+.5,np.sin(_sv*78.233+1)*.5+.5)
_gp=np.clip((np.where(_ch,_fu,_fv)-.80)*5,0,1)
_fib=np.where(_ch,fbm(60,2,aniso=40).T,fbm(60,2,aniso=40))
E['mat']=(lerp((.47,.38,.20),(.78,.66,.39),np.clip(.42+.30*(_ti-.5)+.35*(fbm(4,3)-.5)+.18*(_fib-.5),0,1))*(1-.42*_gp[...,None]),_hg+.25*_fib+.15*fbm(40,2),1.5,.86,0,0)
K.rng=np.random.default_rng(3502)   # YP06: unhusked rice spread to dry — small golden grains lying every way, dark gaps between
_g1=np.clip((fbm(64,2,aniso=3.)-.5)*5+.5,0,1);_g2=np.clip((fbm(64,2,aniso=3.).T-.5)*5+.5,0,1);_gr=np.maximum(_g1,_g2)
E['grain']=(lerp((.56,.42,.15),(.90,.74,.36),np.clip(.25+.55*_gr+.30*(fbm(5,3)-.5),0,1))*(1-.16*np.clip((.34-_gr)*3,0,1))[...,None],1.4*_gr+.2*fbm(30,2),1.8,.80,0,0)
K.rng=np.random.default_rng(3503)   # YP07: old terracotta, and dark potting soil; herb leaves
E['terracotta']=(lerp((.48,.25,.14),(.74,.44,.27),np.clip(.5+.8*(fbm(4,3)-.5)+.2*(fbm(30,2)-.5),0,1))*(1-.14*np.clip((fbm(50,2)-.62)*4,0,1))[...,None],.45*fbm(60,2)+.3*fbm(14,3),1.1,.90,0,0)
_vn_=np.clip((fbm(36,2,aniso=14)-.5)*2+.5,0,1)
E['herb']=(lerp((.17,.33,.10),(.46,.62,.20),np.clip(.5+.8*(fbm(4,3)-.5)+.25*(_vn_-.5),0,1)),.6*_vn_,.9,.66,0,0)             # broad soft leaves, warm green
E['herb_dark']=(lerp((.13,.26,.12),(.32,.46,.20),np.clip(.5+.8*(fbm(5,3)-.5)+.2*(_vn_-.5),0,1)),.5*_vn_,.8,.72,0,0)       # small darker leaves
E['petal']=(lerp((.56,.44,.66),(.80,.70,.86),np.clip(.5+.7*(fbm(5,3)-.5),0,1)),.2*fbm(30,2),.4,.7,0,0)                     # small pale purple flowers
E['onion_white']=(lerp((.74,.76,.62),(.92,.93,.84),np.clip(.5+.6*(fbm(4,3,aniso=6)-.5),0,1)),.3*fbm(40,2,aniso=20),.5,.55,0,0)
K.rng=np.random.default_rng(3504)   # YP08: dried chillies (dark red, wrinkled), garlic skin, maize kernels in rows, dry husk
_wr=np.clip((fbm(40,2,aniso=12)-.5)*2.4+.5,0,1)
E['chilli_dry']=(lerp((.30,.05,.04),(.62,.14,.07),np.clip(.5+.7*(fbm(5,3)-.5)+.3*(_wr-.5),0,1)),1.0*_wr,1.4,.50,0,0)
E['garlic']=(lerp((.70,.66,.58),(.92,.89,.82),np.clip(.5+.6*(fbm(4,3)-.5),0,1))*(1-.10*np.clip((fbm(30,2,aniso=10)-.6)*4,0,1))[...,None]+np.clip((fbm(6,3)-.62)*2,0,1)[...,None]*np.array([.04,-.02,.05]),.3*fbm(40,2,aniso=14),.6,.62,0,0)
_ku=np.abs(((X*26)%1)-.5)*2;_kv=np.abs(((Y*20+.5*np.floor(X*26))%1)-.5)*2;_kh=np.clip(1-np.maximum(_ku,_kv)**3,0,1)
E['maize']=(lerp((.62,.40,.08),(.94,.72,.20),np.clip(.35+.5*_kh+.3*(fbm(5,3)-.5),0,1))*(1-.45*np.clip((.35-_kh)*3,0,1))[...,None],1.5*_kh,2.0,.50,0,0)
_hs=np.clip((fbm(50,2,aniso=40)-.5)*2+.5,0,1)
E['husk']=(lerp((.58,.48,.30),(.86,.76,.54),np.clip(.5+.6*(fbm(4,3,aniso=6)-.5)+.3*(_hs-.5),0,1)),.9*_hs,1.3,.86,0,0)
