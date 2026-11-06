"""BM10 ground patches, second version (#69 follow-up): BM10_01 cushion moss, BM10_02 fallen red maple leaves, BM10_03
fallen golden ginkgo leaves; 1 m square each, ultra tier. References: art/references/BM10/v2/ (picks in prompt.txt).

- the colour is painted on a torus, so it repeats seamlessly on all four sides (the work pack's practice point; the
  3 x 3 repeat of every albedo is written to art/previews/modelling-basics-c/BM10/tiling/)
- the alpha gives the patch a rounded, lobed outline, so a single patch on the ground shows no square edge: the moss rim
  runs 0.34-0.49 m from the centre; for the leaves, a leaf is kept whole or dropped by where its centre lies, never cut
- moss: the mesh is a grid lifted into the painted cushions (up to 2.2 cm), thinning to nothing at the rim
- leaves: whole leaves drawn one over another in drifts, soil left transparent so the patch lies on any ground
blender -b --factory-startup -P build_bm10.py -- [BM10_01 BM10_02 BM10_03]"""
import bpy,math,json,random,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import foliage_kit as fk

SPEC={'BM10_01':dict(kind='moss',seed=1001,grid=(48,24,10)),'BM10_02':dict(kind='maple',seed=1002,grid=(16,8,4)),
      'BM10_03':dict(kind='ginkgo',seed=1003,grid=(16,8,4))}
R=2048
PRE=fk.ROOT/'art/previews/modelling-basics-c/BM10/tiling'

def grid_xy(n=R):
    c=(np.arange(n)+.5)/n;return np.meshgrid(c,c)   # x right, y down (image rows)

def outline(seed,lobes_h=None):
    """distance from the centre where the patch ends, as a function of angle: a rounded, lobed rim"""
    rng=np.random.default_rng(seed);ph=rng.uniform(0,math.tau,4)
    def rim(th):return .41+.035*np.sin(3*th+ph[0])+.025*np.sin(5*th+ph[1])+.015*np.sin(8*th+ph[2])+.01*np.sin(13*th+ph[3])
    return rim

def blobs(n,count,rmin,rmax,seed):
    """toroidal field of soft round cushions (0..1)"""
    rng=np.random.default_rng(seed);x,y=grid_xy(n);f=np.zeros((n,n),np.float32)
    for _ in range(count):
        cx,cy=rng.random(2);r=rng.uniform(rmin,rmax);dx=(x-cx+.5)%1-.5;dy=(y-cy+.5)%1-.5
        f=np.maximum(f,np.clip(1-(dx*dx+dy*dy)/(r*r),0,1)**.7*rng.uniform(.6,1))
    return f

def paint_moss(seed):
    x,y=grid_xy();cush=blobs(R,70,.05,.13,seed)
    fine=fk.noise(R,R,40,seed+1,3,wrap=True);mid=fk.noise(R,R,8,seed+2,3,wrap=True);big=fk.noise(R,R,3,seed+3,2,wrap=True)
    strand=fk.noise(R,R,160,seed+4,2,wrap=True)
    h=np.clip(cush*.8+.25*mid-.1,0,1)*(.85+.15*fine)
    top=np.array([.60,.66,.22]);side=np.array([.34,.47,.16]);deep=np.array([.15,.27,.18]);teal=np.array([.24,.40,.30])
    col=deep+(side-deep)*fk.smooth(.05,.35,h)[...,None];col=col+(top-col)*fk.smooth(.45,.9,h)[...,None]
    col=col*(1-.35*fk.smooth(.55,.85,big)[...,None])+teal*.35*fk.smooth(.55,.85,big)[...,None]   # cool patches in shade
    col*=(.86+.24*strand)[...,None]*(.94+.12*fine)[...,None]
    rng=np.random.default_rng(seed+5)
    for _ in range(420):   # sporophyte tips: tiny warm dots on the cushion tops
        cx,cy=rng.integers(R,size=2)
        if h[cy,cx]<.5:continue
        yy,xx=np.ogrid[-3:4,-3:4];m=(xx*xx+yy*yy)<=rng.integers(3,9)
        col[(cy+yy)%R,(cx+xx)%R]=np.where(m[...,None],np.array([.62,.36,.16])*rng.uniform(.8,1.1),col[(cy+yy)%R,(cx+xx)%R])
    rim=outline(seed+9);th=np.arctan2(y-.5,x-.5);rr=np.hypot(x-.5,y-.5)
    edge=rim(th)+.035*(h-.5)                            # a cushion near the rim pushes it out a little
    alpha=np.clip((np.minimum(edge,.49)-rr)*80,0,1)
    return col,alpha,h,np.clip(.55+.45*h,0,1),np.clip(.88-.1*h,0,1)

def leaf_mask(lx,ly,kind,size,rng):
    """one leaf in its own frame (petiole towards -y): returns coverage and vein mask"""
    r=np.hypot(lx,ly);th=np.arctan2(lx,ly)   # th = 0 along the leaf axis (+y)
    if kind=='maple':   # a palmate leaf: seven lance-shaped lobes from a small palm, the middle one longest, toothed edges
        cov=fk.smooth(0,.004,size*.26-r);vein=np.zeros_like(r)
        for ang,ln in ((0,1.),(.73,.9),(-.73,.9),(1.47,.72),(-1.47,.72),(2.2,.48),(-2.2,.48)):
            Lk=size*ln;x=lx*math.sin(ang)+ly*math.cos(ang);y=lx*math.cos(ang)-ly*math.sin(ang)
            u=np.clip(x/Lk,0,1);hw=size*.34*u**.3*(1-u)**.9*(1+.14*np.abs(np.sin(u*math.pi*9)))
            cov=np.maximum(cov,fk.smooth(0,.003,hw-np.abs(y))*(x>0)*(x<Lk))
            vein=np.maximum(vein,fk.smooth(.0012,.0004,np.abs(y))*(x>0)*(x<.85*Lk))
        vein=vein*.6
        stalk=fk.smooth(.0016,.0008,np.abs(lx))*(ly<0)*(ly>-size*.45);cov=np.maximum(cov,stalk)
    else:
        a=np.abs(th);inside=a<1.2;R0=size*(.94-.03*np.cos(th*16)**2)*(1-.2*np.exp(-(th/.06)**2))*(1-.25*fk.smooth(.9,1.2,a))   # a smooth fan, a shallow notch in the middle
        cov=fk.smooth(0,.006,R0-r)*inside*fk.smooth(.0,.012,r-size*.08)
        vein=(np.abs(np.sin(th*30))<.12)*inside*(r<R0)*.35
        stalk=fk.smooth(.0014,.0007,np.abs(lx))*(ly<size*.1)*(ly>-size*.45);cov=np.maximum(cov,stalk)
    return cov,vein

def paint_leaves(kind,seed):
    rng=np.random.default_rng(seed);x,y=grid_xy()
    rgb=np.zeros((R,R,3),np.float32);alpha=np.zeros((R,R),np.float32);h=np.zeros((R,R),np.float32);col_soil=np.array([.26,.18,.11])
    rgb[:]=col_soil*(.8+.4*fk.noise(R,R,30,seed+1,3,wrap=True))[...,None]   # the colour under the leaves (kept for the bleed and the tile proof)
    drift=fk.noise(R,R,4,seed+2,3,wrap=True);rim=outline(seed+9)
    pal=[(.72,.18,.10),(.80,.32,.12),(.60,.12,.10),(.84,.44,.16),(.52,.16,.10)] if kind=='maple' else [(.88,.64,.10),(.92,.72,.16),(.80,.54,.08),(.74,.50,.12),(.94,.78,.24)]
    n=300 if kind=='maple' else 560;placed=0;tries=0
    while placed<n and tries<20000:
        tries+=1;cx,cy=rng.random(2)
        if rng.random()>drift[int(cy*R)%R,int(cx*R)%R]**1.4*1.6:continue
        size=rng.uniform(.035,.06) if kind=='maple' else rng.uniform(.032,.05);ang=rng.uniform(0,math.tau);c=np.array(pal[rng.integers(len(pal))])*rng.uniform(.85,1.1)
        keep=np.hypot(cx-.5,cy-.5)+size*.9<rim(math.atan2(cy-.5,cx-.5))   # whole leaves only inside the outline
        pad=int(size*1.1*R)+2;ix,iy=int(cx*R),int(cy*R)
        yy,xx=np.mgrid[-pad:pad+1,-pad:pad+1];dx=xx/R;dy=-yy/R
        lx=dx*math.cos(ang)-dy*math.sin(ang);ly=dx*math.sin(ang)+dy*math.cos(ang)
        cov,vein=leaf_mask(lx,ly,kind,size,rng)
        if cov.max()<=0:continue
        mott=fk.noise(2*pad+1,2*pad+1,3,int(rng.integers(1e6)),2)   # soft blotches inside one leaf
        shade=(.88+.2*rng.random())*(.82+.3*mott)*(1-.18*np.clip(np.hypot(lx,ly)/size,0,1))
        lc=c[None,None,:]*shade[...,None];lc=lc+(np.array([.95,.75,.35])-lc)*(np.asarray(vein,np.float32)*.35)[...,None]
        if kind=='ginkgo':
            spots=fk.noise(2*pad+1,2*pad+1,4,int(rng.integers(1e6)),2)
            lc=lc*(1-.35*fk.smooth(.7,.9,spots)[...,None])+np.array([.45,.30,.12])*.35*fk.smooth(.7,.9,spots)[...,None]   # brown freckles
        else:
            dry=fk.smooth(.75,1.,np.hypot(lx,ly)/size)*rng.uniform(0,.6);lc=lc*(1-dry[...,None])+np.array([.40,.20,.10])*dry[...,None]
        ry=(iy+yy)%R;rx=(ix+xx)%R;m=cov>.02
        rgb[ry[m],rx[m]]=rgb[ry[m],rx[m]]*(1-cov[m,None])+lc[m]*cov[m,None]
        h[ry[m],rx[m]]=np.maximum(h[ry[m],rx[m]],(placed/n)*.4+.5+.1*vein[m])
        if keep:alpha[ry[m],rx[m]]=np.maximum(alpha[ry[m],rx[m]],cov[m])
        else:alpha[ry[m],rx[m]]=alpha[ry[m],rx[m]]*(1-cov[m])   # a dropped leaf lying over a kept one hides that part of it, as on the ground
        placed+=1
    rng2=np.random.default_rng(seed+5)
    for _ in range(12):   # a few thin twigs among the leaves
        cx,cy=rng2.random(2);ang=rng2.uniform(0,math.tau);L=rng2.uniform(.03,.07)
        if np.hypot(cx-.5,cy-.5)+L>rim(math.atan2(cy-.5,cx-.5)):continue
        for t in np.linspace(0,1,int(L*R)):
            px_=int((cx+math.cos(ang)*L*t)*R)%R;py_=int((cy+math.sin(ang)*L*t)*R)%R
            rgb[py_-1:py_+2,px_-1:px_+2]=np.array([.30,.20,.12]);alpha[py_-1:py_+2,px_-1:px_+2]=1;h[py_-1:py_+2,px_-1:px_+2]=.7
    return rgb,alpha,h,np.clip(.6+.4*h,0,1),np.full((R,R),.72,np.float32)

def textures(pid,kind,seed):
    col,alpha,h,ao,rough=paint_moss(seed) if kind=='moss' else paint_leaves(kind,seed)
    PRE.mkdir(parents=True,exist_ok=True)
    im=bpy.data.images.new(pid+'_tile',3*512,3*512);small=col[::4,::4]   # the colour repeated 3 x 3: the tile proof
    tile=np.tile(small,(3,3,1));im.pixels.foreach_set(np.ascontiguousarray(np.dstack([tile,np.ones(tile.shape[:2])])[::-1],dtype=np.float32).ravel())
    im.filepath_raw=str(PRE/f'{pid}-colour-3x3.png');im.file_format='PNG';im.save();bpy.data.images.remove(im)
    inner=float(np.mean(np.abs(col[1:]-col[:-1]))+np.mean(np.abs(col[:,1:]-col[:,:-1])))/2   # how much neighbouring pixels differ anyway
    across=float(np.mean(np.abs(col[0]-col[-1]))+np.mean(np.abs(col[:,0]-col[:,-1])))/2     # the same across the wrap-around edges
    seam=across/max(inner,1e-6)   # about 1: the edges join like any two neighbouring pixels
    return fk.save_maps(pid+'_Ground',col,alpha,h,rough,ao,strength=10 if kind=='moss' else 4,wrap=True,bleed_px=0),h,alpha,seam

def patch(n,h,alpha,lift,base):
    """1 m grid; vertices take the painted height where the patch is, nothing outside it"""
    m=fk.Mesh();N=h.shape[0]
    for j in range(n+1):
        for i in range(n+1):
            u,v=i/n,j/n;px=min(int(u*(N-1)),N-1);py=min(int((1-v)*(N-1)),N-1)
            k=max(1,N//n//2);a=alpha[max(py-k,0):py+k+1,max(px-k,0):px+k+1].mean();z=(base+lift*h[py,px])*min(1.,a*1.5)   # base: the low hollows stay above the ground
            m.add((u-.5,v-.5,z),(u,v))
    for j in range(n):
        for i in range(n):
            a=j*(n+1)+i;m.quad(a,a+1,a+n+2,a+n+1)
    return m

def run(pid):
    S=SPEC[pid];ref=fk.ROOT/'art/references/BM10/v2/prompt.txt'
    assert '選用：' in ref.read_text(encoding='utf-8') and len(list(ref.parent.glob('*-cand-*.png')))>=12,'three-views first'
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    sc=bpy.context.scene;root=bpy.data.objects.new(pid+'_GroundOrigin',None);sc.collection.objects.link(root);root['minTier']='ultra'
    maps,h,alpha,seam=textures(pid,S['kind'],S['seed']);mat=fk.material(pid+'_Ground',maps,True)
    lift=.022 if S['kind']=='moss' else .003
    obs=[]
    for lod,n in enumerate(S['grid']):
        o=patch(n,h,alpha,lift,.003 if S['kind']=='moss' else .001).build(f'{pid}_Ground_LOD{lod}',mat);o.parent=root;o.hide_render=lod>0;obs.append(o)
    lo,hi=fk.bounds([obs[0]])
    info={'id':pid,'dimensions_xyz_m':[round(float(v),6) for v in hi-lo],'body_dimensions_xyz_m':[round(float(v),6) for v in hi-lo],
          'target_axis':'x','target_m':1.0,'minTier':'ultra','detailObjects':[],'detailMeshes':[],
          'groups':{'Ground':{'material':pid+'_Ground','texture_px':R,'triangles':[fk.tri_count(o) for o in obs],'maps':['alb','nrm','maskurp','orm']}},
          'triangles_total':[fk.tri_count(o) for o in obs],'triangles_without_detail':[fk.tri_count(o) for o in obs],
          'reference':fk.rel(ref),'version':2,'tile_seam_ratio':round(seam,3),'tile_proof':fk.rel(PRE/f'{pid}-colour-3x3.png'),
          'origin':'patch centre, bottom z = 0','textures':{'Ground':{k:fk.rel(v) for k,v in maps.items()}},'collision':{},
          'notes':{'build':'second version (#69 follow-up), build_bm10.py: colour painted on a torus (repeats on all four sides); alpha gives a rounded, lobed outline'+(', moss cushions lifted into the mesh up to 2.2 cm' if S['kind']=='moss' else ', whole leaves only, soil transparent'),
                   'detail':'the whole patch is ultra-tier dressing; no Detail_ parts','material':'alpha-cut (0.45), both faces; Albedo sRGB, Normal tangent +Y, ORM = AO / roughness / metal, MaskURP = metal / AO / 0 / smoothness'}}
    fk.export(pid,root,[obs[0]],obs);fk.merge_model_info(info);print('BM10_DONE',json.dumps({k:info[k] for k in ('id','dimensions_xyz_m','triangles_total','tile_seam_ratio')}));return info

if __name__=='__main__':
    assert bpy.app.version[:3]==(4,5,3),'Blender 4.5.3'
    ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(SPEC)
    for pid in ids:run(pid)
