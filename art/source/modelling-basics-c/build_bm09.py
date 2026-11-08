"""BM09 ferns, second version (#69 follow-up): BM09_01 a large wild fern 0.8 m tall with long arching fronds, BM09_02 a low
curly woodland fern 0.3 m tall with hooked frond tips and fiddleheads in the crown.
References: art/references/BM09/v2/ (four candidates each, picks and scores in prompt.txt).

Shape (work pack practice point: the direction and bend of the leaves)
- every frond is a rachis curve in its own vertical plane: it leaves the crown steep and bends over along its length; the
  innermost young fronds stand almost upright, the outer old ones arch out and hang, the low fern's tips hook inwards
- LOD0: each pinna is its own card, set along the rachis at 30 degrees towards the tip, drooping 15-35 degrees and arched
  down along its length; neighbouring cards on one side alternate their twist by +-11 degrees, so no two lie in one plane
- LOD1: half the pinnae, wider and with two segments; LOD2: one drooping ribbon on each side of the rachis, painted with a
  whole row of pinnae
- Detail_DryFronds: three broken brown fronds lying from the crown onto the ground
Textures are painted here (numpy): a pinna atlas (young, fresh, mature, old with brown tip), two half-frond ribbons, the
rachis, and a dry atlas. blender -b --factory-startup -P build_bm09.py -- [BM09_01 BM09_02]"""
import bpy,bmesh,math,json,random,sys
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import foliage_kit as fk
import meshfix

SPEC={'BM09_01':dict(H=.8,tier='standard',seed=901,fronds=18,L=1.0,pairs=(24,12),pin=.175,curl=0.,crozier=0,spread=1.,dry=3),
      'BM09_02':dict(H=.3,tier='high',seed=902,fronds=12,L=.42,pairs=(16,8),pin=.19,curl=1.,crozier=3,spread=1.15,dry=3)}

# ------------------------------------------------------------------ painting
PAL={'young':((.56,.68,.26),(.78,.84,.38)),'fresh':((.34,.52,.17),(.60,.72,.27)),'mature':((.24,.40,.19),(.44,.55,.22)),
     'old':((.24,.40,.19),(.44,.55,.22)),'dry':((.42,.29,.16),(.66,.50,.29))}
BROWN=np.array([.55,.36,.16]);BROWN2=np.array([.68,.50,.25]);RIM=np.array([.30,.21,.11])

def paint_pinna(H,W,kind,seed,A=.30):
    """one pinna, base at the bottom row, tip at the top: alternate pinnules angled 40 degrees towards the tip, a midrib.
    A is the card's width / length, so the lobes come out round on the card. Returns rgb, alpha, height."""
    rng=np.random.default_rng(seed)
    y=(np.arange(H)+.5)/H;x=(np.arange(W)+.5)/W
    T=(1-y)[:,None]*np.ones((1,W));X=((x*2-1)*A/2)[None,:]*np.ones((H,1))
    px=1./H*1.5
    env=lambda t:(np.clip(t/.16,0,1)**.6*.85+.15)*np.clip(1-t,0,1)**.55
    alpha=np.zeros((H,W),np.float32);hgt=np.zeros((H,W),np.float32);lobe_t=np.zeros((H,W),np.float32);lobe_x=np.zeros((H,W),np.float32)
    shade=np.ones((H,W),np.float32);N=11;phi=math.radians(40)
    for sg in (-1,1):
        for k in range(N):
            tk=(k+.25+.5*(sg>0))/N*.92+.03;L=env(tk)*A/2/math.cos(phi)*.98;w=.29/N
            ax=np.array([sg*math.cos(phi),math.sin(phi)]);ay=np.array([-ax[1],ax[0]])
            dx=X;dy=T-tk;lx=dx*ax[0]+dy*ax[1];ly=dx*ay[0]+dy*ay[1]
            u=np.clip(lx/max(L,1e-4),0,1.2)
            prof=w*np.sqrt(np.clip(1-u**2.4,0,1))*(1+.13*np.sin(u*math.pi*7+k))
            m=fk.smooth(-px,px,prof-np.abs(ly))*fk.smooth(-w,0,lx)*(u<1.05)
            new=m>alpha;alpha=np.maximum(alpha,m)
            dome=np.sqrt(np.clip(1-(ly/np.maximum(prof,1e-5))**2,0,1))*(.6+.4*(1-u))-.35*np.exp(-(ly/np.maximum(prof*.16,1e-5))**2)*(u<.9)
            hgt=np.where(new,dome,hgt);lobe_t=np.where(new,u,lobe_t);lobe_x=np.where(new,tk,lobe_x)
            shade=np.where(new,1+rng.uniform(-.08,.08),shade)
    rib=fk.smooth(-px,px,(.006*(1-T)+.003)-np.abs(X))*(T<.985)
    alpha=np.maximum(alpha,rib);hgt=np.maximum(hgt,rib*.8)
    base,tip=[np.array(c) for c in PAL[kind]]
    big=fk.noise(H,W,3,seed)
    col=base+(tip-base)*np.clip(lobe_t*.85+.25*(big-.5),0,1)[...,None]
    col*=(shade*(.9+.2*big))[...,None]
    edge=fk.smooth(.0,.25,1-np.clip(hgt,0,1))*(alpha>.5)
    col=col*(1-.10*edge[...,None])+np.array([.75,.72,.35])*.10*edge[...,None]   # sunlit rim on the pinnule edges
    col=np.where(rib[...,None]>.5,np.array([.40,.40,.18])*(.8+.3*T[...,None]),col)
    if kind in('old','dry'):
        n2=fk.noise(H,W,6,seed+1)
        tb=.48 if kind=='old' else -1
        b=fk.smooth(tb-.06,tb+.06,T+.16*(n2-.5))
        b=np.maximum(b,fk.smooth(.72,.95,lobe_t)*(n2>.55)) if kind=='old' else np.ones_like(b)
        br=BROWN+(BROWN2-BROWN)*n2[...,None]
        if kind=='dry':br=np.array(PAL['dry'][0])+(np.array(PAL['dry'][1])-np.array(PAL['dry'][0]))*np.clip(lobe_t+.3*(n2-.5),0,1)[...,None]
        line=fk.smooth(.0,.5,b)*fk.smooth(1.,.5,b)*(kind=='old')
        col=col*(1-b[...,None])+br*b[...,None];col=col*(1-.5*line[...,None])+RIM*.5*line[...,None]
        if kind=='dry':   # a few pinnules broken off
            gone=np.zeros_like(alpha)
            for k in rng.choice(np.arange(N*2),5,replace=False):gone+=(np.abs(lobe_x-((k%N)+.25+.5*(k//N))/N*.92-.03)<1e-4)*(rib<.5)
            alpha=alpha*(1-np.clip(gone,0,1))
    ao=np.clip(.65+.35*np.clip(hgt,0,1),0,1)
    return np.clip(col,0,1),alpha,hgt,ao

def paint_half(H,W,kind,seed,Ar=.38):
    """a whole row of pinnae for the LOD2 ribbon: the rachis is the left edge, each pinna runs out to the right and towards
    the tip (top); pinnule lobes along both its edges"""
    rng=np.random.default_rng(seed)
    y=(np.arange(H)+.5)/H;x=(np.arange(W)+.5)/W
    T=(1-y)[:,None]*np.ones((1,W));X=(x*Ar)[None,:]*np.ones((H,1))
    alpha=np.zeros((H,W),np.float32);hgt=np.zeros((H,W),np.float32);along=np.zeros((H,W),np.float32);shade=np.ones((H,W),np.float32)
    R=18;phi=math.radians(35);px=1.5/H
    for i in range(R):
        ti=(i+.5)/R*.96;L=Ar/math.cos(phi)*.97;w=.42/R
        ax=np.array([math.cos(phi),math.sin(phi)]);ay=np.array([-ax[1],ax[0]])
        dx=X;dy=T-ti;lx=dx*ax[0]+dy*ax[1];ly=dx*ay[0]+dy*ay[1];u=np.clip(lx/L,0,1.2)
        prof=w*np.clip(1-u**1.6,0,1)**.7*(.72+.28*np.abs(np.sin(u*math.pi*8)))
        m=fk.smooth(-px,px,prof-np.abs(ly))*fk.smooth(-w,0,lx)*(u<1.02)
        new=m>alpha;alpha=np.maximum(alpha,m)
        hgt=np.where(new,np.sqrt(np.clip(1-(ly/np.maximum(prof,1e-5))**2,0,1)),hgt);along=np.where(new,u,along);shade=np.where(new,1+rng.uniform(-.08,.08),shade)
    rib=fk.smooth(-px,px,.012-X);alpha=np.maximum(alpha,rib)
    base,tip=[np.array(c) for c in PAL['mature' if kind=='old' else kind]]
    big=fk.noise(H,W,3,seed)
    col=(base+(tip-base)*np.clip(along*.8+.25*(big-.5),0,1)[...,None])*(shade*(.9+.2*big))[...,None]
    col=np.where(rib[...,None]>.5,np.array([.40,.40,.18]),col)
    if kind in('old','dry'):
        n2=fk.noise(H,W,6,seed+1)
        b=fk.smooth(.45,.6,T+.18*(n2-.5)) if kind=='old' else np.ones_like(T)
        br=BROWN+(BROWN2-BROWN)*n2[...,None] if kind=='old' else np.array(PAL['dry'][0])+(np.array(PAL['dry'][1])-np.array(PAL['dry'][0]))*along[...,None]
        col=col*(1-b[...,None])+br*b[...,None]
    return np.clip(col,0,1),alpha,hgt,np.clip(.65+.35*hgt,0,1)

def atlases(pid,seed):
    """Fronds 2048: top half four pinna slots (young, fresh, mature, old), bottom half two half-frond ribbons (fresh, old).
    Detail_DryFronds 1024: dry pinna, dry ribbon, stem strip. Rachis 512: brown at the base, green further up, streaks."""
    S=2048;rgb=np.zeros((S,S,3),np.float32);a=np.zeros((S,S),np.float32);h=np.zeros((S,S),np.float32);ao=np.ones((S,S),np.float32)
    for i,k in enumerate(('young','fresh','mature','old')):
        c,al,hg,o=paint_pinna(1024,512,k,seed+10*i);rgb[:1024,i*512:(i+1)*512]=c;a[:1024,i*512:(i+1)*512]=al;h[:1024,i*512:(i+1)*512]=hg;ao[:1024,i*512:(i+1)*512]=o
    for j,k in enumerate(('fresh','old')):
        c,al,hg,o=paint_half(1024,1024,k,seed+50+j);rgb[1024:,j*1024:(j+1)*1024]=c;a[1024:,j*1024:(j+1)*1024]=al;h[1024:,j*1024:(j+1)*1024]=hg;ao[1024:,j*1024:(j+1)*1024]=o
    fr=fk.save_maps(pid+'_Fronds',rgb,a,h,np.full((S,S),.62,np.float32)-.1*h,ao,strength=8)
    D=1024;rgb=np.zeros((D,D,3),np.float32);a=np.zeros((D,D),np.float32);h=np.zeros((D,D),np.float32);ao=np.ones((D,D),np.float32)
    c,al,hg,o=paint_pinna(1024,512,'dry',seed+70);rgb[:,:512]=c;a[:,:512]=al;h[:,:512]=hg;ao[:,:512]=o
    c,al,hg,o=paint_half(1024,480,'dry',seed+71);rgb[:,512:992]=c;a[:,512:992]=al;h[:,512:992]=hg;ao[:,512:992]=o
    st=fk.noise(1024,32,4,seed+72);rgb[:,992:]=(np.array([.40,.28,.15])*(.8+.4*st[...,None]));a[:,992:]=1;h[:,992:]=st
    dr=fk.save_maps(pid+'_Detail_DryFronds',rgb,a,h,np.full((D,D),.75,np.float32),ao,strength=6)
    R=512;v=1-(np.arange(R)+.5)/R;streak=fk.noise(R,R,4,seed+80,3)
    stx=np.asarray(np.repeat(fk.noise(R,16,8,seed+81,2)[:, :, None],1,2))[...,0]
    stx=np.array([np.interp(np.linspace(0,15,R),np.arange(16),row) for row in stx])
    g=fk.smooth(.12,.45,v)[:,None]*np.ones((1,R))
    col=np.array([.42,.30,.17])*(1-g[...,None])+np.array([.40,.50,.21])*g[...,None]
    col=col*(.85+.25*stx[...,None])*(.92+.12*streak[...,None])
    rng=np.random.default_rng(seed+82)
    for _ in range(140):   # chaffy scales low on the stipe
        cy=int(R*(1-rng.uniform(0,.22)));cx=rng.integers(R);rr=rng.integers(2,5)
        yy,xx=np.ogrid[-cy:R-cy,-cx:R-cx];col[(yy*yy*.3+xx*xx)<rr*rr]=np.array([.22,.14,.08])
    ra=fk.save_maps(pid+'_Rachis',col,None,stx*.5+streak*.5,np.full((R,R),.7,np.float32),np.full((R,R),.9,np.float32),strength=3)
    return {'Fronds':fr,'Rachis':ra,'Detail_DryFronds':dr}

# UV rectangles (u0,v0,u1,v1), Blender v up; slot images were painted with the base at the bottom
PIN={'young':(0,.5,.25,1),'fresh':(.25,.5,.5,1),'mature':(.5,.5,.75,1),'old':(.75,.5,1,1)}
HALF={'fresh':(0,0,.5,.5),'old':(.5,0,1,.5)}
DRY_PIN=(0,0,.5,1);DRY_HALF=(.5,0,.96875,1);DRY_STEM=(.96875,0,1,1)

# ------------------------------------------------------------------ shape
def frond_curve(crown,az,L,th0,droop,curl,n,floor):
    """points of a rachis in the vertical plane at azimuth az: the angle above horizontal falls from th0 by droop along
    the length (faster near the tip), curl adds a hook at the tip. The droop is eased off until nothing dips under floor."""
    d=Vector((math.cos(az),math.sin(az),0));up=Vector((0,0,1))
    for _ in range(40):
        pts=[crown.copy()];p=crown.copy();ds=L/(n-1)
        for i in range(1,n):
            t=i/(n-1);ang=math.radians(th0-droop*t**1.5-(curl*190*fk.smooth(.78,1.,t) if curl else 0))
            p=p+(d*math.cos(ang)+up*math.sin(ang))*ds;pts.append(p.copy())
        if min(q.z for q in pts[2:])>=floor:break
        droop*=.92
    side=d.cross(up).normalized()
    return [q+side*.02*L*math.sin(math.pi*i/(n-1)) for i,q in enumerate(pts)]

def along(pts,t):
    f=t*(len(pts)-1);i=min(int(f),len(pts)-2);w=f-i;p=pts[i].lerp(pts[i+1],w);tg=(pts[i+1]-pts[i]).normalized();return p,tg

def pinna_card(mesh,base,d,wdir,Lp,A,segs,arch,uvr,flip):
    """a pinna card from base along d, width along wdir, bending down (arch) towards its tip"""
    u0,v0,u1,v1=uvr;down=Vector((0,0,-1));hw=Lp*A/2;idx=[]
    for j in range(segs+1):
        x=j/segs;c=base+d*Lp*x+down*arch*Lp*x*x
        vv=v0+(v1-v0)*x;a_=mesh.add(c-wdir*hw,((u1 if flip else u0),vv));b_=mesh.add(c+wdir*hw,((u0 if flip else u1),vv));idx.append((a_,b_))
    for j in range(segs):mesh.quad(idx[j][0],idx[j][1],idx[j+1][1],idx[j+1][0])

def ribbon(mesh,pts,t0,sg,Lfun,drop,segs,uvr):
    """LOD2: a strip from the rachis outwards on one side, drooping, its outer edge following the pinna lengths"""
    u0,v0,u1,v1=uvr;idx=[]
    for j in range(segs+1):
        t=t0+(1-t0)*j/segs;p,tg=along(pts,t);s,n=fk.frame(tg);out=(s*sg*math.cos(drop)-Vector((0,0,1))*math.sin(drop)).normalized()
        vv=v0+(v1-v0)*j/segs;idx.append((mesh.add(p,(u0,vv)),mesh.add(p+out*Lfun(t),(u1,vv))))
    for j in range(segs):
        a,b=idx[j];c,d=idx[j+1]
        if sg>0:mesh.quad(a,b,d,c)
        else:mesh.quad(a,c,d,b)

def plant(pid,lod):
    S=SPEC[pid];r=random.Random(S['seed']);L0=S['L'];N=S['fronds'];curly=S['curl']>0
    fr=fk.Mesh();ra=fk.Mesh();dr=fk.Mesh()
    pairs=S['pairs'][0] if lod==0 else S['pairs'][1];segs=3 if lod==0 else 2;sides=(6,4,3)[lod];npts=(22,12,6)[lod]
    order=sorted(range(N),key=lambda k:r.random())
    for k in range(N):
        age=(k/(N-1))**.8                                   # 0: young, upright, at the centre; 1: old, arching, outside
        az=k*math.radians(137.508)+r.uniform(-.15,.15)
        L=L0*(.78+.30*age)*r.uniform(.92,1.06)
        th0=(87-24*age) if not curly else (86-26*age)
        droop=(26+52*age) if not curly else (38+55*age)   # a vase: steep at the crown, only the tips arch over
        crown=Vector((math.cos(az),math.sin(az),0))*(.012+.02*age)*L0*S['spread']+Vector((0,0,-.012*L0))
        pts=frond_curve(crown,az,L,th0,droop,S['curl']*(.6+.4*age),max(npts,8) if lod<2 else npts,.06*L0)
        kind='young' if age<.15 else 'fresh' if age<.45 else 'mature' if age<.75 else 'old'
        r0=(.0062 if not curly else .0075)*L0*(1.1-.2*age)
        tube_pts=pts if lod<2 else pts[::max(1,len(pts)//6)]
        if (tube_pts[-1]-pts[-1]).length>1e-9:tube_pts=tube_pts+[pts[-1]]   # the tip once, never twice (a zero-length segment)
        fk.tube(ra,tube_pts,[r0*(1-.8*i/(len(tube_pts)-1)) for i in range(len(tube_pts))],sides,v_scale=1/L)
        t0=.14 if not curly else .12;Lmax=S['pin']*L
        def Lp(t,t0=t0,Lmax=Lmax):
            u=(t-t0)/(1-t0);e=(u/.35)**.5 if u<.35 else ((1-u)/.65)**.8
            return Lmax*max(.1,e)*(1-.35*fk.smooth(.8,1.,t)*(curly))
        if lod<2:
            twist=[1,-1]
            for i in range(pairs):
                for sg in (-1,1):
                    t=t0+(1-t0)*(i+.25+.5*(sg>0))/pairs
                    if t>.985:continue
                    p,tg=along(pts,t);s,n=fk.frame(tg)
                    f=math.radians(30);dr_=math.radians(15+20*age)
                    d=(s*sg*math.cos(f)+tg*math.sin(f));d=(d-n*math.tan(dr_)).normalized()
                    w=(tg-d*tg.dot(d)).normalized()
                    tw=math.radians(11*twist[i%2]*sg+r.uniform(-3,3));w=Matrix.Rotation(tw,3,d)@w
                    sl=('mature' if kind=='old' and t<.6 else kind) if not(kind=='mature' and t>.85 and r.random()<.35) else 'old'   # brown only towards the tip of an old frond
                    pinna_card(fr,p+d*r0*.4,d,w,Lp(t)*(1.0 if lod==0 else 1.12),.34 if lod==0 else .46,segs,.22+.15*age,PIN[sl],sg<0)
        else:
            for sg in (-1,1):ribbon(fr,pts,t0,sg,lambda t:Lp(t)*.95,math.radians(25+15*age),5,HALF['old' if kind in('old','mature') else 'fresh'])
    for k in range(S['crozier'] if lod<2 else min(1,S['crozier'])):   # fiddleheads: a stalk and a coil, in the crown
        az=k*2.1+.4;h=L0*(.20+.07*k);rc=.05*L0;d=Vector((math.cos(az),math.sin(az),0));side=d.cross(Vector((0,0,1)))
        base=d*.01*L0;pts=[base+Vector((0,0,-.01*L0))+d*.02*L0*(i/6)+Vector((0,0,h*i/6)) for i in range(7)]
        c=pts[-1]+d*rc;steps=(18,10,6)[lod]
        for i in range(1,steps+1):
            q=i/steps*1.5*math.tau;rr=rc*(1-.55*i/steps);pts.append(c+(-d*math.cos(q)+Vector((0,0,1))*math.sin(q))*rr)
        fk.tube(ra,pts,[.009*L0*(1-.5*i/(len(pts)-1)) for i in range(len(pts))],sides,v_scale=.3/L0)
    for k in range(S['dry']):   # broken dry fronds lying from the crown onto the ground
        az=k*2.4+1.1;L=L0*.38*r.uniform(.85,1.1);d=Vector((math.cos(az),math.sin(az),0))
        pts=[];n=(10,7,5)[lod]
        for i in range(n):
            t=i/(n-1);x=L*t;z=max(.004*L0,.12*L0*math.sin(math.pi*min(t/.5,1)*.5)*(1-t)*2)
            pts.append(d*(.05*L0+x)+Vector((0,0,z-(.012*L0 if i==0 else 0))))   # starts just outside the crown (sharing it, its stem lay along a stalk)
        fk.tube(dr,pts,[.004*L0*(1-.5*i/(n-1)) for i in range(n)],(5,4,3)[lod],v_scale=1/L,u0=DRY_STEM[0],u1=DRY_STEM[2])
        if lod<2:
            m=(10,5)[lod]
            for i in range(m):
                for sg in (-1,1):
                    t=.2+.75*(i+.25+.5*(sg>0))/m
                    if r.random()<.15:continue   # pinnae broken off
                    p,tg=along(pts,t);s,n_=fk.frame(tg);dd=(s*sg*.85+tg*.5);dd.z-=.35;dd.normalize()
                    w=(tg-dd*tg.dot(dd)).normalized();w=Matrix.Rotation(math.radians(12*sg*(1 if i%2 else -1)),3,dd)@w
                    pl=.26*L*(1-.55*t);bp=p+dd*.004*L0
                    if bp.z+dd.z*pl<.002*L0:dd.z=max(dd.z,(.002*L0-bp.z)/pl);dd.normalize()   # lies on the ground, not through it
                    pinna_card(dr,bp,dd,w,pl,.36,2,.1,DRY_PIN,sg<0)
        else:
            for sg in (-1,1):ribbon(dr,pts,.2,sg,lambda t,L=L:.17*L*(1-.5*t),math.radians(20),3,DRY_HALF)
    return {'Fronds':fr,'Rachis':ra,'Detail_DryFronds':dr}

# ------------------------------------------------------------------ build
def run(pid):
    S=SPEC[pid];ref=fk.ROOT/'art/references/BM09/v2/prompt.txt'
    assert '選用：' in ref.read_text(encoding='utf-8') and len(list(ref.parent.glob('*-cand-*.png')))>=8,'three-views first'
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    sc=bpy.context.scene;sc.unit_settings.system='METRIC'
    root=bpy.data.objects.new(pid+'_GroundOrigin',None);sc.collection.objects.link(root);root['minTier']=S['tier']
    maps=atlases(pid,S['seed']);mats={g:fk.material(f'{pid}_{g}',p,g!='Rachis') for g,p in maps.items()}
    groups={};lod0=[]
    for lod in range(3):
        for g,mesh in plant(pid,lod).items():
            o=mesh.build(f'{pid}_{g}_LOD{lod}',mats[g]);o.parent=root;o.hide_render=lod>0;groups.setdefault(g,[]).append(o)
            if lod==0:lod0.append(o)
    sep=[list(meshfix.separate_meshes([groups[g][l].data for g in groups],mode='tilt',tilt=15,passes=8,big=40)) for l in range(3)]
    body=[o for o in lod0 if '_Detail_' not in o.name];lo,hi=fk.bounds(body)
    f=S['H']/hi[2];   # the ground is z = 0 (stalk bases start under it and are pressed onto it)
    off=Vector((-(hi[0]+lo[0])/2,-(hi[1]+lo[1])/2,0))
    for obs in groups.values():
        for o in obs:
            for v in o.data.vertices:
                c=(v.co+off)*f
                if c.z<0:c.z=0.   # stalk bases sink into the soil: pressed onto the ground plane
                v.co=c
            o.data.update()
    for obs in groups.values():   # faces pressed flat onto the ground face straight down and are never seen
        for o in obs:
            bm=bmesh.new();bm.from_mesh(o.data);meshfix.drop_ground_bottoms(bm,z=.0005,keep_verts=False)
            bmesh.ops.dissolve_degenerate(bm,dist=1e-5,edges=bm.edges[:])   # slivers pressed flat onto the ground: Unity drops them, so model_info must not count them
            bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free()
    bpy.context.view_layer.update()
    lo,hi=fk.bounds(lod0);blo,bhi=fk.bounds(body)
    assert abs(float(bhi[2]-blo[2])-S['H'])<.005,(bhi[2]-blo[2])
    details=[g for g in groups if g.startswith('Detail_')]
    info={'id':pid,'dimensions_xyz_m':[round(float(v),6) for v in hi-lo],'body_dimensions_xyz_m':[round(float(v),6) for v in bhi-blo],
          'target_axis':'z','target_m':S['H'],'minTier':S['tier'],'detailObjects':details,'detailMeshes':[o.name for g in details for o in groups[g]],
          'groups':{g:{'material':f'{pid}_{g}','texture_px':{'Fronds':2048,'Rachis':512,'Detail_DryFronds':1024}[g],'triangles':[fk.tri_count(o) for o in obs],'maps':['alb','nrm','maskurp','orm']} for g,obs in groups.items()},
          'triangles_total':[sum(fk.tri_count(obs[l]) for obs in groups.values()) for l in range(3)],
          'triangles_without_detail':[sum(fk.tri_count(obs[l]) for g,obs in groups.items() if not g.startswith('Detail_')) for l in range(3)],
          'separated_pieces':sep,'reference':fk.rel(ref),'version':2,
          'origin':'crown centre, bottom z = 0, front = -Y (Blender) / -Z (FBX, Unity)',
          'textures':{g:{k:fk.rel(v) for k,v in p.items()} for g,p in maps.items()},'collision':{},
          'notes':{'build':'second version (#69 follow-up), build_bm09.py: rachis curves bending over with age; LOD0 pinna cards set 30 deg forward, drooping and arched, twist alternating +-11 deg; LOD1 half the pinnae; LOD2 drooping ribbons with a painted row of pinnae'+('; hooked frond tips and three fiddleheads' if S['curl'] else ''),
                   'detail':'Detail_DryFronds: three broken brown fronds lying from the crown onto the ground; hide on the standard tier',
                   'material':'alpha-cut, both faces (Fronds, Detail_DryFronds); Albedo sRGB, Normal tangent +Y, ORM = AO / roughness / metal, MaskURP = metal / AO / 0 / smoothness'}}
    root['detailObjects']=json.dumps(details)
    fk.export(pid,root,lod0,[o for obs in groups.values() for o in obs])
    fk.merge_model_info(info);print('BM09_DONE',json.dumps({k:info[k] for k in ('id','dimensions_xyz_m','triangles_total')}));return info

if __name__=='__main__':
    assert bpy.app.version[:3]==(4,5,3),'Blender 4.5.3'
    ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(SPEC)
    for pid in ids:run(pid)
