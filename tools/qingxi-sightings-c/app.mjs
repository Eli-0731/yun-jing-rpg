/* 青溪見聞 C · demo page. Eli-0731. Rules live in state.js (window.Sightings); this file only draws and handles input. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const S=window.Sightings,$=id=>document.getElementById(id);
const KEY='qingxi-sightings-c.v1';
const [sj,pj,a2,a3]=await Promise.all(['sightings.json','positions.json','../qingxi-terrain/blocks/A2.json','../qingxi-terrain/blocks/A3.json'].map(u=>fetch(u).then(r=>r.json())));
const list=S.merge(sj.sightings,pj.positions);
let state=S.newState();try{state=S.restore(localStorage.getItem(KEY),list);}catch{}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(state));}catch{}};
const env={time:'day',afterRain:false};

/* ---------- areas: bounds, start point, what to draw ---------- */
const HOME={bounds:{minX:-6.5,minZ:-3,sizeX:13,sizeZ:16},start:{x:0,z:-1.4},speed:2.4};
const AREAS={
  A2:{bounds:a2.bounds,start:{x:2,z:-140},speed:6,block:a2},
  A3:{bounds:a3.bounds,start:{x:-55,z:8},speed:6,block:a3},
  HOME
};
let area='A2',pos={...AREAS.A2.start};
const canvas=$('map'),ctx=canvas.getContext('2d');
function view(){
  const b=AREAS[area].bounds,w=canvas.clientWidth,h=canvas.clientHeight,dpr=Math.min(2,devicePixelRatio||1);
  if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);}
  const s=Math.min(canvas.width/b.sizeX,canvas.height/b.sizeZ),ox=(canvas.width-b.sizeX*s)/2,oy=(canvas.height-b.sizeZ*s)/2;
  // north (+z) is up
  return {s,X:x=>ox+(x-b.minX)*s,Y:z=>oy+(b.minZ+b.sizeZ-z)*s,dpr};
}
const night=()=>env.time==='night';
function drawBlock(v,blk){
  const nodes=Object.fromEntries(blk.nodes.map(n=>[n.id,n]));
  if(blk.creek){const c=blk.creek,p=c.points;ctx.strokeStyle=night()?'#2c4f5c':'#5f9aa8';ctx.lineWidth=c.width*v.s;ctx.lineCap='round';ctx.lineJoin='round';
    ctx.beginPath();for(let i=0;i<p.length;i+=2)(i?ctx.lineTo:ctx.moveTo).call(ctx,v.X(p[i]),v.Y(p[i+1]));ctx.stroke();}
  ctx.lineCap='round';
  for(const e of blk.edges){const a=nodes[e.from],b=nodes[e.to];if(!a||!b)continue;ctx.strokeStyle=night()?'#4a4536':'#c9b48a';ctx.lineWidth=e.width*v.s;
    ctx.beginPath();ctx.moveTo(v.X(a.x),v.Y(a.z));ctx.lineTo(v.X(b.x),v.Y(b.z));ctx.stroke();}
  for(const p of blk.pads){ctx.fillStyle=night()?'#3e3b30':'#b9a57c';ctx.fillRect(v.X(p.x-p.halfX),v.Y(p.z+p.halfZ),2*p.halfX*v.s,2*p.halfZ*v.s);}
  ctx.fillStyle=night()?'#2a2822':'#6b5a43';
  for(const p of blk.placements)ctx.fillRect(v.X(p.x)-1.2*v.s,v.Y(p.z)-1.2*v.s,2.4*v.s,2.4*v.s);
}
function drawHome(v){
  const r=(x0,z0,x1,z1,c)=>{ctx.fillStyle=c;ctx.fillRect(v.X(x0),v.Y(z1),(x1-x0)*v.s,(z1-z0)*v.s);};
  r(-6,2.5,6,12.5,night()?'#2f3a2a':'#8a9a64');                       // backyard
  r(-3.5,-2.5,3.5,2.5,night()?'#3d3226':'#a3855f');                   // house floor
  r(-4.1,5,-1.5,8.4,night()?'#3b2f22':'#6e5236');r(1.5,5,4.1,8.4,night()?'#3b2f22':'#6e5236');   // two fields
  r(-1.6,9.2,1.6,12.4,night()?'#3a3529':'#b19f78');                   // practice ground
  r(-.55,2.5,.55,12.5,night()?'#4a463b':'#c8bc9d');                  // gravel path
  ctx.strokeStyle=night()?'#14120e':'#3a2c1d';ctx.lineWidth=.18*v.s;ctx.strokeRect(v.X(-3.5),v.Y(2.5),7*v.s,5*v.s);
  ctx.fillStyle=night()?'#14120e':'#3a2c1d';ctx.font=`${.45*v.s}px serif`;ctx.fillText('屋內',v.X(-.4),v.Y(-1.8));ctx.fillText('後院',v.X(-.4),v.Y(11.8));
}
let t0=performance.now();
function draw(now){
  const v=view();ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle=area==='HOME'?(night()?'#1a1915':'#5f6b47'):(night()?'#1f2a28':'#7d8f5c');ctx.fillRect(0,0,canvas.width,canvas.height);
  if(area==='HOME')drawHome(v);else drawBlock(v,AREAS[area].block);
  if(env.afterRain){ctx.fillStyle='rgba(120,150,170,.12)';ctx.fillRect(0,0,canvas.width,canvas.height);}
  // glows: only what the rules say is visible from here
  const vis=S.visible(state,list,area,pos,env),pulse=.5+.5*Math.sin(now/380);
  for(const s of vis){const k=1-s.dist/S.RULES.glowRadius,rad=(.6+.5*pulse)*Math.max(.8,1.1*v.s/ (area==='HOME'?1.2:1));
    const g=ctx.createRadialGradient(v.X(s.pos.x),v.Y(s.pos.z),0,v.X(s.pos.x),v.Y(s.pos.z),Math.max(10*v.dpr,rad*v.s*.9));
    g.addColorStop(0,`rgba(255,240,180,${.35+.6*k})`);g.addColorStop(1,'rgba(255,240,180,0)');ctx.fillStyle=g;ctx.beginPath();ctx.arc(v.X(s.pos.x),v.Y(s.pos.z),Math.max(10*v.dpr,rad*v.s*.9),0,7);ctx.fill();}
  // the 14 m sense ring and the player
  ctx.strokeStyle='rgba(255,255,255,.18)';ctx.lineWidth=1*v.dpr;ctx.beginPath();ctx.arc(v.X(pos.x),v.Y(pos.z),S.RULES.glowRadius*v.s,0,7);ctx.stroke();
  ctx.fillStyle='#f6efe0';ctx.strokeStyle='#2b2a25';ctx.lineWidth=2*v.dpr;ctx.beginPath();ctx.arc(v.X(pos.x),v.Y(pos.z),Math.max(5*v.dpr,.45*v.s),0,7);ctx.fill();ctx.stroke();
  const near=S.inspectable(state,list,area,pos,env);$('inspect').disabled=!near;
  const hint=near?`腳邊有東西：按 F 細看`:vis.length?`附近有微光（${Math.round(vis[0].dist)} m）`:(area==='HOME'?'屋裡和後院都看看。':'走一走，草叢裡偶爾有微光。');
  if($('hint').textContent!==hint)$('hint').textContent=hint;
}

/* ---------- movement: keys, touch drag (virtual stick), click-to-walk ---------- */
const keys=new Set();let stick=null,target=null;
addEventListener('keydown',e=>{if($('card').open)return;const k=e.key.toLowerCase();
  if(['arrowup','arrowdown','arrowleft','arrowright','w','a','s','d'].includes(k)){keys.add(k);target=null;e.preventDefault();}
  if(k==='f'){inspect();e.preventDefault();}});
addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));
addEventListener('blur',()=>keys.clear());
canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);stick={x0:e.clientX,y0:e.clientY,x:e.clientX,y:e.clientY,moved:false};});
canvas.addEventListener('pointermove',e=>{if(!stick)return;stick.x=e.clientX;stick.y=e.clientY;if(Math.hypot(stick.x-stick.x0,stick.y-stick.y0)>8)stick.moved=true;});
canvas.addEventListener('pointerup',e=>{if(stick&&!stick.moved){const v=view(),r=canvas.getBoundingClientRect(),b=AREAS[area].bounds;
    const px=(e.clientX-r.left)*v.dpr,py=(e.clientY-r.top)*v.dpr;target={x:b.minX+(px-v.X(b.minX))/v.s,z:b.minZ+b.sizeZ-(py-v.Y(b.minZ+b.sizeZ))/v.s};}
  stick=null;});
function clamp(){const b=AREAS[area].bounds;pos.x=Math.min(b.minX+b.sizeX,Math.max(b.minX,pos.x));pos.z=Math.min(b.minZ+b.sizeZ,Math.max(b.minZ,pos.z));}
function step(dt){
  let dx=0,dz=0;
  if(keys.has('arrowleft')||keys.has('a'))dx--;if(keys.has('arrowright')||keys.has('d'))dx++;
  if(keys.has('arrowup')||keys.has('w'))dz++;if(keys.has('arrowdown')||keys.has('s'))dz--;
  if(stick&&stick.moved){dx=(stick.x-stick.x0)/60;dz=-(stick.y-stick.y0)/60;target=null;}
  if(target&&!dx&&!dz){const ex=target.x-pos.x,ez=target.z-pos.z,d=Math.hypot(ex,ez);if(d<.15)target=null;else{dx=ex/d;dz=ez/d;}}
  const m=Math.hypot(dx,dz);if(m>0){const sp=AREAS[area].speed*Math.min(1,m)/m;pos.x+=dx*sp*dt;pos.z+=dz*sp*dt;clamp();}
}
function frame(now){const dt=Math.min(.05,(now-t0)/1000);t0=now;if(!$('card').open)step(dt);draw(now);requestAnimationFrame(frame);}
requestAnimationFrame(frame);

/* ---------- inspecting, the red-seal card and the 3D look ---------- */
let renderer,scene,camera,controls,model,raf;
const loader=new GLTFLoader();
function viewer(id){
  const box=$('viewer');box.replaceChildren();cancelAnimationFrame(raf);
  renderer??=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(2,devicePixelRatio||1));
  box.append(renderer.domElement);const w=box.clientWidth||400,h=box.clientHeight||240;renderer.setSize(w,h);
  scene=new THREE.Scene();scene.add(new THREE.HemisphereLight(0xfff4e0,0x6a5a48,1.4));const sun=new THREE.DirectionalLight(0xffffff,2.2);sun.position.set(1,2,1.5);scene.add(sun);
  camera=new THREE.PerspectiveCamera(30,w/h,.01,10);controls=new OrbitControls(camera,renderer.domElement);controls.enablePan=false;controls.autoRotate=true;controls.autoRotateSpeed=1.6;
  loader.load(`../../art/exports/qingxi-sightings-c/${id}.glb`,g=>{model=g.scene;scene.add(model);
    const b=new THREE.Box3().setFromObject(model),c=b.getCenter(new THREE.Vector3()),r=b.getSize(new THREE.Vector3()).length();
    controls.target.copy(c);camera.position.set(c.x+r*.9,c.y+r*.6,c.z+r*1.3);camera.near=r/100;camera.far=r*20;camera.updateProjectionMatrix();});
  const loop=()=>{controls.update();renderer.render(scene,camera);raf=requestAnimationFrame(loop);};loop();
}
function openCard(s,fresh){
  $('card-title').textContent=s.title;$('card-text').textContent=s.passage;
  $('card-item').textContent=fresh?'收進乾坤袋（本機展示，不是正式物品）':`第 ${state.found.indexOf(s.id)+1} 則見聞 · 拖曳可旋轉`;
  $('card-close').textContent=fresh?'收進乾坤袋':'闔上';
  $('card').showModal();viewer(s.id);
}
$('card').addEventListener('close',()=>{cancelAnimationFrame(raf);canvas.focus();});
function inspect(){
  const near=S.inspectable(state,list,area,pos,env);if(!near)return;
  const r=S.discover(state,list,near.id,area,pos,env);if(!r.ok)return;
  state=r.state;save();renderBook();openCard(near,true);
}
$('inspect').addEventListener('click',inspect);

/* ---------- collection ---------- */
function renderBook(){
  const items=S.collection(state,list);$('count').textContent=`${items.length}／${list.length}`;$('empty').hidden=items.length>0;
  $('book').replaceChildren(...items.map(s=>{const li=document.createElement('li'),b=document.createElement('button'),img=document.createElement('img'),t=document.createElement('span');
    img.src=`../../art/previews/qingxi-sightings-c/${s.id}/${s.id}-style-threequarter.png`;img.alt='';img.loading='lazy';t.textContent=s.title;
    b.append(img,t);b.addEventListener('click',()=>openCard(s,false));li.append(b);return li;}));
}
$('reset').addEventListener('click',()=>{state=S.newState();save();renderBook();});

/* ---------- controls ---------- */
function tab(which){for(const [t,p] of [['tab-map','page-map'],['tab-book','page-book']]){const on=t===which;$(t).setAttribute('aria-selected',on);$(p).hidden=!on;}}
$('tab-map').addEventListener('click',()=>{tab('tab-map');canvas.focus();});$('tab-book').addEventListener('click',()=>tab('tab-book'));
$('area').addEventListener('change',e=>{area=e.target.value;pos={...AREAS[area].start};target=null;canvas.focus();});
for(const r of document.querySelectorAll('input[name=time]'))r.addEventListener('change',e=>{env.time=e.target.value;canvas.focus();});
$('rain').addEventListener('change',e=>{env.afterRain=e.target.checked;canvas.focus();});
canvas.tabIndex=0;renderBook();
window.__sightings={get state(){return state;},get pos(){return pos;},set pos(p){pos={...p};},setArea(a){$('area').value=a;$('area').dispatchEvent(new Event('change'));},env};
