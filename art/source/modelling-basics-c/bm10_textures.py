"""Deterministic authored foliage atlases and periodic ground materials. No photo sources.
PNG writer keeps exact data bytes; BM10 works on a torus before duplicating endpoint samples.
Run through build_bm09_bm10.py in Blender 4.5.3. No external Python dependencies.
"""
import math, struct, zlib
from pathlib import Path
import numpy as np

def png(path, a):
    a=np.rint(np.clip(a,0,1)*255).astype(np.uint8)
    h,w,c=a.shape
    def chunk(k,v): return struct.pack('!I',len(v))+k+v+struct.pack('!I',zlib.crc32(k+v)&0xffffffff)
    raw=b''.join(b'\0'+r.tobytes() for r in a[::-1])
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))

def extend(a):
    return np.concatenate([np.concatenate([a,a[:,:1]],axis=1),np.concatenate([a[:1],a[:1,:1]],axis=1)],axis=0)

def bleed(rgb,alpha,passes=48):
    """colour margin: transparent pixels take the colour of the nearest opaque ones, so filtered and mipmapped samples at
    an alpha edge never pick up a foreign colour (#69 review: no square outline near or at 40 m)"""
    rgb=rgb.copy();f=alpha>.5;rgb[~f]=0
    for _ in range(passes):
        acc=np.zeros_like(rgb);cnt=np.zeros(f.shape,np.float32)
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):acc+=np.roll(np.roll(rgb*f[...,None],dy,0),dx,1);cnt+=np.roll(np.roll(f,dy,0),dx,1)
        new=(~f)&(cnt>0);rgb[new]=acc[new]/cnt[new][:,None];f=f|new
        if f.all():break
    rgb[~f]=rgb[f].mean(0);return rgb

def edge_reach(x,y):
    """0..1, smooth and not periodic with the square: how far in from the patch edge the cover stops, so the outline wanders"""
    return .5+.25*np.sin(x*17.3+y*5.1+.4)*np.cos(y*13.7-x*3.3)+.25*np.sin((x+y)*9.1+1.3)

def material_maps(prefix, rgb, height, alpha, rough, ao, texdir, periodic=False, normal_strength=1.):
    n=height.shape[0]
    dx=(np.roll(height,-1,1)-np.roll(height,1,1))*n*.5*normal_strength
    dy=(np.roll(height,-1,0)-np.roll(height,1,0))*n*.5*normal_strength
    normal=np.dstack([-dx,-dy,np.ones_like(height)]);normal/=np.linalg.norm(normal,axis=2)[...,None]
    one=np.ones_like(height);zero=np.zeros_like(height)
    arrays={'Albedo':np.dstack([rgb,alpha]),'Normal':np.dstack([normal*.5+.5,one]),
            'MaskURP':np.dstack([zero,ao,zero,1-rough]),'ORM':np.dstack([ao,rough,zero,one])}
    paths={}
    for name,a in arrays.items():
        if periodic:a=extend(a)
        path=texdir/(prefix+'_'+name+'.png');png(path,a);paths[name]=str(path)
    return paths

def fern_atlas(prefix, size, texdir, dry=False, stem=False):
    y,x=np.mgrid[0:size,0:size].astype(np.float32)/size
    if stem:
        band=.5+.5*np.sin(x*math.tau*9+.4*np.sin(y*math.tau*2))
        rgb=np.empty((size,size,3),np.float32)
        rgb[:]=[.28,.34,.12];rgb+=band[...,None]*np.array([.13,.14,.045])
        base=np.clip((.28-y)/.28,0,1)[...,None];rgb=rgb*(1-base)+np.array([.28,.18,.09])*base
        return material_maps(prefix,rgb,band*.0001,np.ones_like(x),np.full_like(x,.78),np.ones_like(x),texdir,normal_strength=.25)
    # Eight padded blade variants, four columns by two rows. Distinct old/new tissue.
    cx=(x*4)%1;cy=(y*2)%1;idx=(x*4).astype(int)+4*(y*2).astype(int)
    u=(cx-.06)/.88;v=(cy-.05)/.90
    t=np.clip(v,0,1);side=np.abs(u-.5)*2
    profile=np.sin(np.pi*t)**.68*(.86+.14*np.cos(t*math.tau*11))
    # Broad pinnae with paired small lobes, a fine tapered terminal and petiole.
    inside=(side<profile)&(v>0)&(v<1)
    petiole=(side<.045)&(v>.005)&(v<.12)
    a=(inside|petiole).astype(np.float32)
    vein=np.exp(-(side/.035)**2)
    branch=np.exp(-(np.sin((t*13-side*.7)*math.pi)/.13)**2)*(side>.08)
    tone=.5+.22*np.cos(side*2.1)+.16*t+.05*np.sin(t*12+idx)
    shade=np.array([.16,.29,.105]);light=np.array([.43,.56,.22])
    rgb=shade+(light-shade)*tone[...,None]
    rgb*= (1+.09*(idx%4-1.5))[...,None]
    rgb+=vein[...,None]*np.array([.08,.07,.015])+branch[...,None]*.018
    brown=np.clip((t-.58)/.38,0,1)*(idx>=4)
    if dry:brown=np.ones_like(t)*.88
    rgb=rgb*(1-brown[...,None])+np.array([.43,.29,.115])*brown[...,None]*(.85+.15*t[...,None])
    edge=np.clip((side/np.maximum(profile,.01)-.82)*5,0,1)*inside
    rgb=rgb*(1-.16*edge[...,None])
    h=(vein*.00020+branch*.00004)*a
    return material_maps(prefix,rgb,h,a,np.full_like(t,.69 if not dry else .87),np.full_like(t,.98),texdir,normal_strength=.8)

def area(n,cx,cy,r):
    rad=int(math.ceil(r*n));ix=np.arange(int(cx*n)-rad,int(cx*n)+rad+1);iy=np.arange(int(cy*n)-rad,int(cy*n)+rad+1)
    xx,yy=np.meshgrid(ix/n-cx,iy/n-cy)
    return np.ix_(iy%n,ix%n),xx,yy

def moss(prefix,texdir):
    n=2047;rng=np.random.default_rng(1001)
    yy,xx=np.mgrid[0:n,0:n].astype(np.float32)/n
    h=np.zeros((n,n),np.float32);tone=np.zeros_like(h)
    # Interlocking cushions, elliptical and asymmetric, all wrapping on both axes.
    for k in range(78):
        cx,cy=rng.random(2);r=rng.uniform(.045,.105);idx,x,y=area(n,cx,cy,r*2)
        angle=rng.uniform(0,math.tau);u=x*np.cos(angle)+y*np.sin(angle);v=-x*np.sin(angle)+y*np.cos(angle)
        q=(u/r)**2+(v/(r*rng.uniform(.65,1.2)))**2
        mound=np.exp(-q*1.8)*rng.uniform(.006,.014)
        h[idx]=np.maximum(h[idx],mound)
    broad=.5+.18*np.sin(math.tau*(xx*2+yy)+.7*np.sin(yy*math.tau*3))+.12*np.cos(math.tau*(yy*3-xx))
    t=np.clip(.18+.48*h/.013+.25*broad,0,1)
    rgb=np.array([.14,.21,.075])+t[...,None]*np.array([.30,.32,.13])
    # Tiny leaf rosettes, structured biological marks, not uncorrelated pixel noise.
    for k in range(78000):
        cx,cy=rng.random(2);r=rng.uniform(.0022,.0044);idx,x,y=area(n,cx,cy,r*1.7)
        angle=rng.uniform(0,math.tau);u=x*np.cos(angle)+y*np.sin(angle);v=-x*np.sin(angle)+y*np.cos(angle)
        q=(u/(r*.34))**2+(v/r)**2;mask=np.clip((1-q)*3,0,1)
        center=h[int(cy*n)%n,int(cx*n)%n];col=np.array([.24,.34,.09])+(center/.014)*np.array([.23,.22,.09])
        col=col*rng.uniform(.78,1.20)*(1+.16*np.clip(v/r,-1,1)[...,None])
        rib=np.exp(-(u/(r*.12))**2)*mask
        rgb[idx]=rgb[idx]*(1-mask[...,None]*.88)+(col+rib[...,None]*.028)*mask[...,None]*.88
        h[idx]+=mask*.00035+rib*.00010
    # #69 review: the patch was opaque to its square edge. The cover is now a rounded, lobed mat whose rim runs 0.36-0.49 m
    # from the centre with the angle and bulges where a cushion sits, so neither near nor at 40 m is there a straight edge.
    dx_,dy_=xx-.5,yy-.5;rr=np.sqrt(dx_*dx_+dy_*dy_);th=np.arctan2(dy_,dx_)
    rim=.415+.035*np.sin(3*th+1.1)+.025*np.sin(5*th+2.3)+.015*np.sin(9*th+.4)+.03*(np.clip(h/.012,0,1)-.5)
    alpha=np.clip((np.minimum(rim,.49)-rr)*30,0,1)
    rough=.87+.06*(1-t);ao=.80+.20*np.clip(h/.006,0,1)
    return material_maps(prefix,bleed(rgb,alpha),h,alpha,rough,ao,texdir,True,normal_strength=1.15)

def polygon_mask(x,y,verts):
    inside=np.zeros(x.shape,bool)
    for i,(ax,ay) in enumerate(verts):
        bx,by=verts[(i+1)%len(verts)]
        inside^=((ay>y)!=(by>y))&(x<(bx-ax)*(y-ay)/(by-ay+1e-12)+ax)
    return inside

def segment_distance(x,y,ax,ay,bx,by):
    t=np.clip(((x-ax)*(bx-ax)+(y-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2+1e-12),0,1)
    return np.sqrt((x-ax-t*(bx-ax))**2+(y-ay-t*(by-ay))**2)

def leaves(prefix,texdir,kind):
    n=2047;rng=np.random.default_rng(1002 if kind=='maple' else 1003)
    h=np.zeros((n,n),np.float32);alpha=np.zeros_like(h);rough=np.full_like(h,.84);ao=np.ones_like(h)
    base=np.array([.49,.16,.105] if kind=='maple' else [.73,.49,.12]);rgb=np.zeros((n,n,3),np.float32)+base
    centers=rng.random((9,2));count=115 if kind=='maple' else 190
    # Five palmate lobes; dense, small serrations are modelled into the alpha boundary.
    angles=np.array([-115,-100,-80,-60,-40,-20,0,20,40,60,80,100,115])*np.pi/180
    radius=np.array([.18,.37,.70,.32,.97,.43,1.18,.43,.97,.32,.70,.37,.18])
    key=np.stack([np.sin(angles)*radius,np.cos(angles)*radius],axis=1)
    verts=[]
    for i,p in enumerate(key):
        q=key[(i+1)%len(key)];direction=q-p;normal=np.array([direction[1],-direction[0]]);normal/=max(np.linalg.norm(normal),1e-6)
        for j in range(5):verts.append(p+(q-p)*j/5+normal*(.025 if j%2 else 0))
    for k in range(count):
        if k%3:
            c=centers[k%len(centers)]+rng.normal(0,.14,2);cx,cy=c%1
        else:cx,cy=rng.random(2)
        r=rng.uniform(.029,.058) if kind=='maple' else rng.uniform(.024,.044)
        idx,x,y=area(n,cx,cy,r*1.7)
        # #69 review: leaves crossing the patch edge wrapped round and were cut straight along the square. Only leaves
        # wholly inside are drawn, and the margin wanders 2-9 cm, so the patch edge reads as scattered leaves.
        inside=min(cx,1-cx,cy,1-cy)>r*1.75+.02+.07*float(edge_reach(cx,cy))
        angle=rng.uniform(0,math.tau);u=(x*np.cos(angle)+y*np.sin(angle))/r;v=(-x*np.sin(angle)+y*np.cos(angle))/r
        if kind=='maple':
            mask=polygon_mask(u,v,verts)
            stem=segment_distance(u,v,0,-.04,.07,-.58)<.017
            mask|=stem;vein=np.zeros(u.shape,np.float32)
            for ang,L in zip([-80,-40,0,40,80],[.7,.97,1.18,.97,.7]):
                a=ang*math.pi/180;dx,dy=np.sin(a)*L,np.cos(a)*L
                vein=np.maximum(vein,np.exp(-(segment_distance(u,v,0,0,dx,dy)/.014)**2))
                for t in [.3,.48,.65,.8]:
                    for sign in [-1,1]:
                        ex=dx*t+sign*dy*.15;ey=dy*t-sign*dx*.15
                        dist=segment_distance(u,v,dx*(t-.11),dy*(t-.11),ex,ey)
                        vein=np.maximum(vein,.38*np.exp(-(dist/.008)**2))
            pigment=.5+.5*np.sin(u*4.3+k*.9)*np.cos(v*3.1-k)
            col=base*rng.uniform(.65,1.23)+np.array([.13,.085,.025])*pigment[...,None]
            senescent=np.clip((np.sin(u*7+k)+np.cos(v*5-k)-.45)/1.6,0,1)
            col=col*(1-senescent[...,None]*.5)+np.array([.42,.28,.12])*senescent[...,None]*.5
            col+=vein[...,None]*np.array([.065,.036,.014])
            relief=.0012*(.6+.4*np.sin(u*2+k))*np.clip(v+.3,0,1)+vein*.00022+.00035*np.sin(u*13+v*4+k)*np.cos(v*8+k)
        else:
            vv=v+.5;rr=np.sqrt(u*u+vv*vv);theta=np.arctan2(u,vv)
            limit=1.12-.17*np.exp(-(theta/.15)**2)+.025*np.sin(theta*28+k)
            mask=(np.abs(theta+.035*np.sin(rr*8+k))<1.12)&(rr<limit)&(rr>.04)
            mask|=(segment_distance(u,v,0,-.47,.05,-.94)<.018)
            veins=(.5+.5*np.cos(theta*49+rr*1.5))**16
            margin=np.clip((rr/(limit+.001)-.82)*4,0,1)
            col=base*rng.uniform(.70,1.13)+np.array([.10,.085,.016])*(.5+.5*np.cos(u*3+v*2+k))[...,None]
            col=col*(1-margin[...,None]*.18)+veins[...,None]*np.array([.027,.019,.006])
            green=np.clip((.35-rr)*1.3,0,.25)*(k%5==0);col=col*(1-green[...,None])+np.array([.35,.40,.10])*green[...,None]
            senescent=np.clip((np.sin(u*8+k)+np.cos(v*6-k)-.6)/1.4,0,1)
            col=col*(1-senescent[...,None]*.36)+np.array([.46,.29,.095])*senescent[...,None]*.36
            relief=.0011*(rr*.5+.5*np.sin(theta*3+k)**2)+veins*.00009+.00024*np.sin(theta*9+k)*rr
        # Several softly bounded age spots per leaf, with the strongest on older tissue.
        for spot in range(5):
            sx,sy=rng.uniform(-.65,.65),rng.uniform(.05,.85);sr=rng.uniform(.018,.065)
            blot=np.exp(-((u-sx)**2+(v-sy)**2)/(sr*sr)*2)*rng.uniform(.08,.32)
            col=col*(1-blot[...,None])+np.array([.24,.17,.075])*blot[...,None]
        # A few torn spots, not a speckled noise field.
        if k%7==0:mask&=~(((u-.23)**2+(v-.37)**2)<.0018)
        a=mask.astype(np.float32)*inside
        rgb[idx]=rgb[idx]*(1-a[...,None])+np.clip(col,0,1)*a[...,None]
        h[idx]=h[idx]*(1-a)+(relief+.0006)*a
        rough[idx]=rough[idx]*(1-a)+(.76+.08*rng.random())*a
        alpha[idx]=np.maximum(alpha[idx],a)
    # Subpixel antialias only, preserving the periodic construction.
    alpha=(alpha*4+np.roll(alpha,1,0)+np.roll(alpha,-1,0)+np.roll(alpha,1,1)+np.roll(alpha,-1,1))/8
    h=(h*4+np.roll(h,1,0)+np.roll(h,-1,0)+np.roll(h,1,1)+np.roll(h,-1,1))/8
    return material_maps(prefix,bleed(rgb,alpha),h,alpha,rough,ao,texdir,True,normal_strength=.52)
