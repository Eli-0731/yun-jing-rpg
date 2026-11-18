# C 路邊小物（wayside-c）WS01 路邊野花叢（黃、紫）. Every leaf, petal and floret is its own piece, no leaf cards (as YP13_02).

_lance=lambda u:(.10 if u<.08 else (.10+.90*math.sin(math.pi*min(1.,(u-.08)/.92*1.02))**.75)*(1+.16*math.sin(u*44.))*(1 if u<.98 else .15))   # narrow, deeply toothed

def _ws_paint(seed,green=True):
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);pz=P[...,2]
        lf=filled*(mid<.5)*(col[...,1]>col[...,0]*1.10)*(col[...,1]>col[...,2]*1.15)
        yl=lf*np.clip((_fb(P,12.,seed,2)-.58)*4,0,1);col=col*(1-.30*yl[...,None])+yl[...,None]*.30*np.array([.58,.60,.26])   # some leaves yellow-green
        dust=lf*np.clip((.10-pz)/.08,0,1)*np.clip(.3+noise,0,1);col=col*(1-.35*dust[...,None])+dust[...,None]*.35*np.array([.50,.44,.32])   # road dust on the low leaves
        soil=filled*(mid>.5);col=col*(1-.10*soil[...,None]);return col,rough
    return paint

# ---------------- WS01_01 roadside clump of small yellow wild chrysanthemums (cand-1) ----------------
def WS01_01(M):
    """a clump of thin branching stems with narrow toothed leaves; the stems fork at the top into stalks carrying small yellow
    daisy-like heads (thirteen ray petals round a golden disc), buds and a few faded heads; basal leaves round the foot"""
    rr=random.Random(int(__import__('os').environ.get('WS_SEED',9102)));nh=nb=nf=0
    for k in range(12):   # basal leaves
        a=k*2.39996+rr.uniform(-.2,.2);d=(math.cos(a),math.sin(a));L=rr.uniform(.09,.13)
        _blade(f'WS01_01_Base{k:02d}',Vector((d[0]*(.025+.005*k),d[1]*(.025+.005*k),.012+.003*k)),d,L,L*rr.uniform(.36,.44),.85+.03*k,rr.uniform(.25,.45),_lance,M['herb_dark'],'Body',nu=6,nv=2,cup=rr.uniform(.15,.3),twist=rr.uniform(-.3,.3))
    for k in range(22):
        a=k*2.39996+rr.uniform(-.2,.2);g=(k+.5)/22;cr=.02+.15*g**.7;Ht=rr.uniform(.32,.44)*(1.05-.25*g)
        f=_stemf(f'WS01_01_Stem{k:02d}',(cr*math.cos(a),cr*math.sin(a),.002),a,Ht,.12+.50*g+rr.uniform(-.08,.08),.0026,M['vine'],bow=rr.uniform(-.08,.08));a0=rr.uniform(0,math.tau)
        for i in range(8):   # alternate toothed leaves, smaller upwards
            u=.12+.74*i/7;la=a0+i*2.39996+rr.uniform(-.3,.3);L=.092*rr.uniform(.85,1.1)*(1-.50*i/7)
            _blade(f'WS01_01_L{k:02d}{i}',f(u),(math.cos(la),math.sin(la)),L,L*.46,rr.uniform(.85,1.25),rr.uniform(.2,.45),_lance,M['herb'],'Body',nu=5,nv=2,cup=.3,twist=rr.uniform(-.3,.3))
        top=f(1.);nfork=rr.choice((3,3,4))
        for j in range(nfork):
            fa=a0+math.tau*j/nfork+rr.uniform(-.3,.3);Lp=rr.uniform(.035,.075);o=Vector((math.cos(fa),math.sin(fa),0));e=top+o*Lp*.6+Vector((0,0,Lp))
            _taper(f'WS01_01_Ped{k:02d}{j}',[top+o*.003+Vector((0,0,-.002+.0015*j)),top.lerp(e,.5)+o*.006,e],[.0014,.0012,.0011],M['vine'],'Body',sides=4,scale=.05,up=(math.cos(fa+.6+.5*j),math.sin(fa+.6+.5*j),.4))
            q_=rr.random()
            if q_<.66:   # an open head: 13 ray petals, alternately tilted and stepped so no two lie in one plane, round a domed disc
                nh+=1;r=rr.uniform(.019,.025);p0=rr.uniform(0,6.28);tl=(o*.35+Vector((0,0,1))).normalized()
                for q in range(13):
                    pa=p0+math.tau*q/13;_blade(f'WS01_01_P{k:02d}{j}{q:02d}',e+Vector((math.cos(pa)*.0040,math.sin(pa)*.0040,.0006*q)),(math.cos(pa),math.sin(pa)),r,r*.34,1.20+.20*(q%2)+.02*q,rr.uniform(-.05,.12),lambda u_:.25+.75*math.sin(math.pi*min(1.,u_*.88+.06))**.6,M['pollen'],'Body',nu=3,nv=2,cup=.25,scale=.05)
                _taper(f'WS01_01_Disc{k:02d}{j}',[e+Vector((0,0,-.0025)),e+Vector((0,0,.0020)),e+Vector((0,0,.0052))],[.0072,.0068,.0014],M['maize'],'Body',sides=6,scale=.03)
            elif q_<.86:
                nb+=1;dn=(e-top).normalized();_taper(f'WS01_01_Bud{k:02d}{j}',[e-dn*.002,e+dn*.004,e+dn*.010],[.0015,.0045,.0010],M['herb_dark'],'Body',sides=5,scale=.04)
            else:   # a faded head: a brown seed disc, its petals gone
                nf+=1;_taper(f'WS01_01_Old{k:02d}{j}',[e+Vector((0,0,-.003)),e+Vector((0,0,.002)),e+Vector((0,0,.006))],[.0040,.0055,.0015],M['leaf_dry'],'Body',sides=6,scale=.03)
    _ws_base('WS01_01',M,rr,.36,.34,2,9130)
    return {'paint':_ws_paint(9140),'wear':.3,'grime':.4,'ao_k':.5,'uv_angle':60,
            'notes':[f'a roadside clump about 0.45 m high: 12 basal leaves, 22 thin stems with narrow toothed alternate leaves (176), each stem forking at the top: {nh} yellow heads (13 ray petals round a golden disc), {nb} buds, {nf} faded brown heads',
                     'every leaf and petal is its own piece, no leaf cards; road dust on the low leaves, some leaves yellow-green, painted',
                     'Detail_Base (a thin patch of dry earth and two small stones) is off at the standard tier; the stems start inside the earth patch; no collision; the paving slab of the three-view is left out']}
PROPS['WS01_01']=WS01_01

# ---------------- WS01_02 roadside clump of small purple self-heal (cand-3) ----------------
def WS01_02(M):
    """upright square stems with opposite oval leaves (each pair turned a quarter), ending in a short dense spike of
    green-purple bracts with small violet lipped flowers sticking out in rings; a few spent brown spikes; basal leaves"""
    rr=random.Random(int(__import__('os').environ.get('WS_SEED',9155)));ns=nsp=0
    for k in range(10):   # basal leaves lying out
        a=k*2.39996+rr.uniform(-.2,.2);d=(math.cos(a),math.sin(a));L=rr.uniform(.08,.11)
        _blade(f'WS01_02_Base{k:02d}',Vector((d[0]*(.022+.005*k),d[1]*(.022+.005*k),.012+.003*k)),d,L,L*rr.uniform(.48,.56),1.0+.03*k,rr.uniform(.2,.35),lambda u:_leaf_oval(u,.03),M['herb_dark'],'Body',nu=5,nv=2,cup=rr.uniform(.15,.3),twist=rr.uniform(-.3,.3))
    for k in range(14):
        a=k*2.39996+rr.uniform(-.2,.2);g=(k+.5)/14;cr=.015+.12*g**.7;Ht=rr.uniform(.20,.31)*(1.05-.25*g)
        f=_stemf(f'WS01_02_Stem{k:02d}',(cr*math.cos(a),cr*math.sin(a),.002),a,Ht,.06+.30*g+rr.uniform(-.05,.05),.0030,M['vine'],bow=rr.uniform(-.05,.05));a0=rr.uniform(0,math.tau)
        for i in range(5):   # opposite leaf pairs, each pair a quarter turn from the last
            u=.14+.58*i/4;L=.068*rr.uniform(.85,1.1)*(1-.35*i/4)
            for j in range(2):
                la=a0+i*math.pi/2+j*math.pi+rr.uniform(-.2,.2)
                _blade(f'WS01_02_L{k:02d}{i}{j}',f(u)+Vector((0,0,.0018*j)),(math.cos(la),math.sin(la)),L,L*.55,rr.uniform(.95,1.30)+.08*j,rr.uniform(.15,.35),lambda u_:_leaf_oval(u_,.03),M['herb'],'Body',nu=4,nv=2,cup=.3,twist=rr.uniform(-.25,.25))
        top=f(1.);dn=(top-f(.92)).normalized();spent=rr.random()<.2;Ls=rr.uniform(.050,.068)
        sp=[top-dn*.004,top+dn*Ls*.5,top+dn*Ls]
        _taper(f'WS01_02_Spike{k:02d}',sp,[.0080,.0095,.0050],M['leaf_dry'] if spent else M['herb_dark'],'Body',sides=6,scale=.03)
        if spent:nsp+=1;continue
        ns+=1;ax=dn.orthogonal().normalized()
        for w in range(4):   # rings of florets sticking out of the spike, each a lipped tube
            c=top+dn*Ls*(.15+.22*w)
            for q in range(4):
                pa=w*.78+q*math.pi/2+rr.uniform(-.2,.2);o=(Matrix.Rotation(pa,3,dn)@ax);o=(o+dn*.35).normalized()
                b=c+o*.0075;e=b+o*.014+dn*.004
                _taper(f'WS01_02_F{k:02d}{w}{q}',[b-o*.002,b+o*.004,e],[.0015,.0028,.0034],M['petal'],'Body',sides=4,scale=.03)
    _ws_base('WS01_02',M,rr,.32,.30,2,9160)
    return {'paint':_ws_paint(9170),'wear':.3,'grime':.4,'ao_k':.5,'uv_angle':60,
            'notes':[f'a roadside clump about 0.35 m high: 10 basal leaves, 14 upright stems with opposite oval leaves turned a quarter each pair (140), {ns} short spikes of green-purple bracts with four rings of violet lipped florets, {nsp} spent brown spikes',
                     'every leaf and floret is its own piece, no leaf cards; road dust on the low leaves, painted',
                     'Detail_Base (a thin patch of dry earth and two small stones) is off at the standard tier; the stems start inside the earth patch; no collision; the paving slab of the three-view is left out']}
PROPS['WS01_02']=WS01_02
