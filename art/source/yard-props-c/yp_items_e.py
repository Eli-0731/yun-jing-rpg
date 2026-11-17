# YP08 shapes (the 11/14 120h pack, batch A), read by build_yp.py after yp_items_d.py (same namespace).
# Follows the three-view picked in art/references/YP08/prompt.txt. Blender: X = width, -Y = front, Z = up; the wall is the plane y = 0 behind it.

# ---------------- YP08 things hung to dry under the eaves: a sieve, chillies, garlic, maize (cand-4) ----------------
def YP08(M):
    """two wooden brackets nailed to the wall carry a bamboo pole; four wooden hooks hang on the pole, and from them a
    round bamboo sieve, a string of dried chillies, a plait of garlic and a bunch of maize cobs tied by their husks."""
    rr=random.Random(6801);WD,WB,HP,IR=M['cedar'],M['cedar_b'],M['hemp'],M['iron'];ZP=.800;YP=-.105;RP=.021
    for q,sx in enumerate((-1,1)):   # brackets: a back board on the wall, an arm, a brace
        x=sx*.70;box(f'YP08_Board{q}',(.092,.028,.27),(x,-.014,ZP+.005),WB if q else WD,'Body',bev=.004,segs=1,cuts=1,jit=.0015,seed=6810+q)
        _bar(f'YP08_Arm{q}',(x,-.020,ZP-.046),(x,-.185,ZP-.046),.046,.046,WD,'Body',up=(0,0,1),bev=.004,seed=6812+q,jit=.0012)
        _bar(f'YP08_Brace{q}',(x,-.022,ZP-.125),(x,-.150,ZP-.060),.034,.030,WB,'Body',up=(0,-1,1),bev=.003,seed=6814+q,jit=.001)
        for j,dz in enumerate((.10,-.105)):_nail(f'YP08_Nail{q}{j}',(x+rr.uniform(-.012,.012),-.028,ZP+.005+dz),(0,-1,0),IR)
        for j in range(4):_ring(f'YP08_Lash{q}{j}',(x-.012+.008*j,YP,ZP-.012),(1,0,0),.034,.0036,HP,'Body',n=13)   # the pole lashed down on the arm
    _bcane('YP08_Pole',(-.80,YP,ZP),(.80,YP+.004,ZP+.003),RP,RP*.9,M['bamboo'],'Body',gap=.27,sides=10,bow=-.006,ph=.3)
    def hook(k,x):
        """a forked twig hung over the pole: round the back and top, down the front, turned up at the end; returns the hanging point"""
        pts=[Vector((x,YP+.030*math.cos(t),ZP+.030*math.sin(t))) for t in np.linspace(-.5,math.pi+.25,8)]
        f=pts[-1];pts+=[f+Vector((0,-.004,-.035)),f+Vector((0,-.006,-.075)),f+Vector((0,-.022,-.098)),f+Vector((0,-.044,-.088)),f+Vector((0,-.052,-.066))]
        _taper(f'YP08_Hook{k}',pts,[.0075]*8+[.0085,.009,.0085,.0075,.006],M['hardwood'],'Body',sides=6,scale=.1);return f+Vector((0,-.024,-.090))
    # the sieve: a shallow woven dish seen from the front, two hoops, crossed slats on the back
    hp=hook(0,-.43);R=.255;cs=Vector((-.43,YP-.006,hp.z-.035-R))
    o=_lathe('YP08_Sieve',[(0,.002),(0,.200),(.25,.236),(1,R),(1,R-.007),(.30,.229),(.14,.192),(.14,.002)],(cs+Vector((0,.030,0)),cs+Vector((0,-.022,0))),M['weave'],'Body',NS=36,scale=.4,loop=True);jitter(o,.002,6820,freq=9)
    _lathe('YP08_SieveHoop',[(0,R-.007),(0,R+.009),(1,R+.009),(1,R-.007)],(cs+Vector((0,-.008,0)),cs+Vector((0,-.030,0))),M['bamboo_split'],'Body',NS=36,scale=.3,loop=True)
    for k in range(12):
        a=math.tau*(k+.5+rr.uniform(-.15,.15))/12;c=cs+Vector((R*math.cos(a),-.019,R*math.sin(a)));tg=Vector((-math.sin(a),0,math.cos(a)))
        for j in range(2):_ring(f'YP08_SieveLash{k}{j}',c+tg*(.007*(j-.5)),tg,.0175,.0024,M['cord_dark'],'Detail_Lashings',n=9)
    for q,a in enumerate((.5,.5+math.pi/2)):
        d=Vector((math.cos(a),0,math.sin(a)));_bar(f'YP08_SieveSlat{q}',cs+d*(-R+.03)+Vector((0,.034+.0032*q,0)),cs+d*(R-.03)+Vector((0,.034+.0032*q,0)),.022,.009,M['bamboo_split'],'Body',up=(0,1,0),bev=.002,seed=6822+q,jit=.0006)
    for j,sx in enumerate((-1,1)):
        e=cs+Vector((sx*.085,-.019,math.sqrt(R*R-.085**2)+.008));rope(f'YP08_SieveCord{j}',[e,e.lerp(hp,.5)+Vector((0,0,.004)),hp+Vector((sx*.004,0,.004))],.0042,HP,'Body')
    # the chilli string: dried chillies tied by their stalks all round a cord, pointing down and out
    hp=hook(1,-.105);top=hp+Vector((0,0,-.02));LC=.47;rope('YP08_ChilliCord',[hp+Vector((0,0,.004)),top,top+Vector((.004,0,-LC*.5)),top+Vector((-.003,0,-LC))],.0045,HP,'Body')
    for k in range(58):
        u=(k+rr.random())/58;a=k*2.4+rr.uniform(-.4,.4);out=Vector((math.cos(a),math.sin(a)*.8,0));b=top+Vector((0,0,-.02-LC*u))+out*.006
        L=rr.uniform(.075,.11)*(1-.25*u);dn=rr.uniform(.9,1.6);d=(out+Vector((0,0,-dn))).normalized();s=Vector((-out.y,out.x,0))*rr.uniform(-.5,.5);r=rr.uniform(.0085,.0115)
        pts=[b,b+d*L*.08,b+d*L*.35+s*L*.08,b+d*L*.70+s*L*.20+out*L*.05,b+d*L+s*L*.34+out*L*.14]
        _taper(f'YP08_Chilli{k:02d}',pts,[.0022,r*.95,r,r*.62,.0012],M['chilli_dry'],'Chillies',sides=5,scale=.07)
    # the garlic plait: bulbs in threes down a plait of their dry leaves
    hp=hook(2,.130);top=hp+Vector((0,0,-.015));LG=.34
    rope('YP08_GarlicPlait',[hp+Vector((0,0,.004)),top,top+Vector((.003,0,-LG*.5)),top+Vector((0,0,-LG)),top+Vector((.004,-.004,-LG-.05))],.0085,M['husk'],'Garlic',plies=3)
    for k in range(15):
        u=(k//3+.5)/5;a=(k%3)*math.tau/3+(k//3)*1.0+rr.uniform(-.25,.25)-math.pi/2;out=Vector((math.cos(a),math.sin(a)*.8,0));b=top+Vector((0,0,-.03-LG*u))+out*.008;sz=rr.uniform(.85,1.15)
        d=(out+Vector((0,0,-rr.uniform(.5,1.1)))).normalized()
        o=_lathe(f'YP08_Garlic{k:02d}',[(0,.004),(.12,.0065),(.30,.019*sz),(.58,.026*sz),(.82,.021*sz),(.95,.008),(1,.004)],(b,b+d*.058*sz),M['garlic'],'Garlic',NS=9,scale=.08)
        tip=b+d*.058*sz;_taper(f'YP08_GRoot{k:02d}',[tip-d*.006,tip+d*.006,tip+d*.014+out*.003],[.0042,.0034,.0008],M['hemp'],'Garlic',sides=5,scale=.05)   # the dried root tuft
    # the maize bunch: five cobs hanging tips down, their husks pulled back up, tied together and flaring above the tie
    hp=hook(3,.405);tie=hp+Vector((0,0,-.115));rope('YP08_MaizeCord',[hp+Vector((0,0,.004)),hp+Vector((0,0,-.05)),tie],.0045,HP,'Body')
    tube('YP08_MaizeTie',[tie+Vector((.0215*math.cos(q_),.0215*math.sin(q_),.004-.0042*q_/math.tau)) for q_ in np.linspace(0,4*math.tau,53)],.0034,HP,'Maize',sides=5,scale=.05)
    rr=random.Random(int(__import__('os').environ.get('YP_SEED',6850)))   # the maize bunch has its own draw
    for k in range(5):
        a=math.tau*k/5+.4;out=Vector((math.cos(a),math.sin(a)*.75,0));sp=rr.uniform(.12,.30);d=(Vector((0,0,-1))+out*sp).normalized();b=tie+Vector((0,0,-.045))+out*.022;Lc=rr.uniform(.17,.21)
        _lathe(f'YP08_Cob{k}',[(0,.010),(.06,.021),(.35,.0265),(.70,.023),(.92,.013),(1,.004)],(b,b+d*Lc),M['maize'],'Maize',NS=12,scale=.10)
        _taper(f'YP08_CobStalk{k}',[b+d*.012,b.lerp(tie,.5)+out*.006,tie+out*.013+Vector((0,0,.004*k-.008))],[.0075,.006,.0045],M['husk'],'Maize',sides=6,scale=.1)
    for k in range(13):   # the husk ends flaring above the tie, some hanging back down over the cobs
        a=math.tau*k/13+rr.uniform(-.2,.2);down=k%3==0;L=rr.uniform(.09,.13)
        _blade(f'YP08_Husk{k:02d}',tie+Vector((math.cos(a)*.015,math.sin(a)*.012,.002+.0023*k)),(math.cos(a),math.sin(a)*.75),L,rr.uniform(.030,.042),rr.uniform(.25,.6) if not down else rr.uniform(1.2,1.6),rr.uniform(.25,.6) if not down else rr.uniform(.9,1.3),
               lambda u:(.35+.65*math.sin(math.pi*min(1.,u*.9+.1))**.7)*(1 if u<.97 else .2),M['husk'],'Maize',nu=6,nv=2,cup=rr.uniform(.2,.5),twist=rr.uniform(-.8,.8))
    R_={}
    def paint(col,rough,pos,onrm,ao,cav,edge,noise,mid,filled,meta):
        P=((pos-np.array(meta['offset'][:]))/meta['scale_to_target']).astype(np.float32);px,py,pz=P[...,0],P[...,1],P[...,2];h=np.zeros(px.shape,np.float32)
        brk=filled*(np.abs(np.abs(px)-.70)<.06)*(py>-.20)*(col[...,0]>col[...,2]*1.3)*(pz>ZP-.16)
        col,rough=_wood_age(col,rough,h,P,brk,2,6830,edge,grey=.45,stain=.25)
        top=brk*np.clip((pz-ZP-.09)/.05,0,1)*np.clip((noise-.35)*3,0,1);col=col*(1-.5*top[...,None])+top[...,None]*.5*np.array([.24,.31,.12])   # moss on the board tops
        red=filled*(col[...,0]>col[...,1]*2.2);hl=red*np.clip((_fb(P,25.,6831,2)-.5)*3,0,1);col=col*(1+.25*hl[...,None]);dk=red*np.clip((_fb(P,18.,6832,2)-.55)*4,0,1);col=col*(1-.35*dk[...,None])   # chillies: some brighter, some dried dark
        sv=filled*(np.hypot(px-cs.x,pz-cs.z)<.27)*(np.abs(py-cs.y)<.05);gy=sv*np.clip((_fb(P,5.,6833,3)-.46)*3,0,1);col=col*(1-.30*gy[...,None])+gy[...,None]*.30*np.array([.44,.41,.35])
        R_['h']=h;return col,rough
    return {'paint':paint,'relief':lambda:R_['h'],'wear':.6,'grime':.8,'ao_k':.45,'uv_angle':60,
            'notes':['hangs on a wall: the wall is the plane behind the two back boards (the back of the model); the origin is the footprint centre under the lowest hanging tip, as for every item of this pack',
                     'two brackets (back board, arm, brace, nails as Detail_Nails) carry a bamboo pole lashed to the arms; four wooden hooks hang on the pole',
                     'the sieve: a shallow woven dish (weave in the texture and normal map), a split-bamboo hoop lashed at twelve places (Detail_Lashings), crossed slats on the back, hung by a cord from two points of the rim',
                     'the chilli string (group Chillies): 58 dried chillies, each a bent tapering tube, tied round a cord; the garlic plait (group Garlic): 15 bulbs, each with its dried root tuft, down a plait; the maize bunch (group Maize): five cobs, tips down, husks pulled up into a four-turn tie and flaring above it',
                     'painted: the weathered brackets with moss on top, chillies unevenly dark, grey patches on the sieve']}
PROPS['YP08']=YP08
