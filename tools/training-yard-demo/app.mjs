import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RhythmSession } from './rhythm.mjs';
const $=id=>document.getElementById(id),canvas=$('world');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.8));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;
const scene=new THREE.Scene();scene.background=new THREE.Color('#bbc8b2');scene.fog=new THREE.Fog('#bbc8b2',25,62);
scene.add(new THREE.HemisphereLight(0xe4edda,0x544832,2.2));
const sun=new THREE.DirectionalLight(0xffe4b4,3.2);sun.position.set(-6,10,6);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-12,right:12,top:12,bottom:-12,near:.5,far:35});sun.shadow.bias=-.0004;scene.add(sun);
const camera=new THREE.PerspectiveCamera(60,1,.05,90);camera.position.set(0,1.70,7.2);let yaw=0,pitch=-.02;
function soilTexture(base,seed){const c=document.createElement('canvas');c.width=c.height=256;const p=c.getContext('2d'),d=p.createImageData(256,256);let n=seed;for(let i=0;i<256*256;i++){n=(1664525*n+1013904223)>>>0;const grain=((n>>>22)/1023-.5)*25;for(let k=0;k<3;k++)d.data[i*4+k]=Math.max(0,Math.min(255,base[k]+grain));d.data[i*4+3]=255;}p.putImageData(d,0,0);const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(22,22);t.colorSpace=THREE.SRGBColorSpace;return t;}
const ground=new THREE.Mesh(new THREE.PlaneGeometry(90,90),new THREE.MeshStandardMaterial({map:soilTexture([120,128,92],27),roughness:1}));ground.rotation.x=-Math.PI/2;ground.position.y=-.012;ground.receiveShadow=true;scene.add(ground);
const trailTexture=soilTexture([168,155,123],117);trailTexture.repeat.set(2,8);
const path=new THREE.Mesh(new THREE.PlaneGeometry(3.4,13),new THREE.MeshStandardMaterial({map:trailTexture,roughness:1}));path.rotation.x=-Math.PI/2;path.position.set(0,-.006,5.5);path.receiveShadow=true;scene.add(path);
// Distant low relief and meadow texture belong only to this local viewing scene.
for(let layer=0;layer<3;layer++){const vertices=[],indices=[],z=-22-layer*7;for(let i=0;i<=64;i++){const xx=-40+i*1.25;const rise=1.2+layer*.9+1.5*Math.sin(i*.18+layer)+.9*Math.sin(i*.47+layer*1.7);vertices.push(xx,-.02,z,xx,rise,z);}for(let i=0;i<64;i++){const a=i*2;indices.push(a,a+1,a+2,a+1,a+3,a+2);}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.setIndex(indices);g.computeVertexNormals();const m=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color:[0x74836f,0x83927f,0x9aa995][layer],side:THREE.DoubleSide}));scene.add(m);}
const meadowGeometry=new THREE.ConeGeometry(.08,.26,3),meadowMaterial=new THREE.MeshStandardMaterial({color:0x6a7950,roughness:1,side:THREE.DoubleSide});const meadow=new THREE.InstancedMesh(meadowGeometry,meadowMaterial,400);const dummy=new THREE.Object3D();let planted=0;for(let i=0;i<1500&&planted<400;i++){const a=i*12.9898,b=i*78.233,x=(Math.sin(a)*43758.5453%1)*17,z=(Math.sin(b)*9317.251%1)*19+3;if(Math.abs(x)<2.2&&z>0&&z<12)continue;if(Math.abs(x)<3.6&&z>-2&&z<3)continue;dummy.position.set(x,.10,z);dummy.rotation.y=i*2.399;dummy.scale.setScalar(.6+.6*Math.abs(Math.sin(i*1.71)));dummy.updateMatrix();meadow.setMatrixAt(planted++,dummy.matrix);}meadow.count=planted;scene.add(meadow);
const placements={'training-shelter':[0,0,0],'qi-striking-post':[-1.55,.12,-.35],'agility-post':[1.55,.12,-.35],'weapon-rack':[2,.12,-1.55],'engraved-training-stone':[-1.45,.12,-1.45],'training-banner':[-3,0,2.1]};
const loader=new GLTFLoader();const models={};let loaded=0,ready=false;
await Promise.all(Object.entries(placements).map(async([id,pos])=>{try{const g=await loader.loadAsync('/assets/'+id+'.glb');g.scene.position.set(...pos);g.scene.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});scene.add(g.scene);models[id]=g.scene;loaded++;$('load').textContent=`實際模型 ${loaded}/6 載入完成`;}catch(e){$('load').textContent=`模型載入失敗：${id}，請檢查 GLB`;console.error(e);}}));
ready=loaded===6;
const stations=[{id:'qi-striking-post',name:'氣勁木樁',mode:'qi',x:-1.55,z:-.35},{id:'agility-post',name:'身法木樁',mode:'body',x:1.55,z:-.35}];
const obstacles=[...[-2.4,2.4].flatMap(x=>[-1.8,1.8].map(z=>({x,z,r:.46}))),...stations.map(s=>({...s,r:.52})),{x:2,z:-1.55,r:.70},{x:-1.45,z:-1.45,r:.92},{x:-3,z:2.1,r:.43}];
const keys=new Set();let near=null,session=null,currentMode=null,drag=null,last=performance.now(),resultCount=0;
function faceStation(mode){const target=stations.find(s=>s.mode===mode);const dx=target.x-camera.position.x,dz=target.z-camera.position.z;yaw=Math.atan2(-dx,-dz);pitch=-.08;}
function open(){if(!ready||!near)return;faceStation(near.mode);$('practice').hidden=false;$('station').textContent=near.name;$('explain').textContent=near.mode==='qi'?'繩墊與渦紋引導吸吐：按住吸氣、放開吐氣。':'看紅布臂的來勢：在提示到達中線時按格擋。';$('qi').disabled=$('roots').value==='no';$('exercise').hidden=true;session=null;document.body.classList.add('practicing');keys.clear();}
function close(){session=null;$('practice').hidden=true;document.body.classList.remove('practicing');keys.clear();}
function begin(mode){if(mode==='qi'&&$('roots').value==='no')return;faceStation(mode);$('station').textContent=stations.find(s=>s.mode===mode).name;$('explain').textContent=mode==='qi'?'繩墊與渦紋引導吸吐：按住吸氣、放開吐氣。':'看紅布臂的來勢：在提示到達中線時按格擋。';currentMode=mode;session=new RhythmSession(mode,{hasRoots:$('roots').value!=='no',start:performance.now()/1000});resultCount=0;$('exercise').hidden=false;$('retry').hidden=true;$('action').disabled=false;$('feedback').textContent='準備好後跟隨節奏';$('action').textContent=mode==='qi'?'按住吸氣 · 放開吐氣':'按下格擋';$('breath').style.display=mode==='qi'?'grid':'none';if(document.activeElement instanceof HTMLElement)document.activeElement.blur();}
function act(kind,repeat=false){if(!session||session.done)return;session.input(kind,performance.now()/1000,{repeat});}
$('qi').onclick=()=>begin('qi');$('body').onclick=()=>begin('body');$('retry').onclick=()=>begin(currentMode);$('close').onclick=close;$('interact').onclick=open;
$('action').onpointerdown=e=>{e.preventDefault();e.currentTarget.setPointerCapture(e.pointerId);act('press');};$('action').onpointerup=e=>{e.preventDefault();act('release');};$('action').onpointercancel=()=>act('release');
$('reset').onclick=()=>{close();camera.position.set(0,1.7,7.2);yaw=0;pitch=-.02;};$('roots').onchange=()=>{if(!$('practice').hidden){close();open();}};
const alias={ArrowUp:'KeyW',ArrowDown:'KeyS',ArrowLeft:'KeyA',ArrowRight:'KeyD'};
addEventListener('keydown',e=>{if(['SELECT','INPUT'].includes(e.target.tagName))return;const k=alias[e.code]||e.code;if(['KeyW','KeyA','KeyS','KeyD','Space','KeyE','Escape'].includes(k))e.preventDefault();if(k==='KeyE'&&!e.repeat)open();else if(k==='Escape')close();else if(k==='Space')act('press',e.repeat);else keys.add(k);});
addEventListener('keyup',e=>{keys.delete(alias[e.code]||e.code);if(e.code==='Space'){e.preventDefault();act('release');}});addEventListener('blur',()=>{keys.clear();if(session&&!session.done)close();});
document.querySelectorAll('[data-key]').forEach(b=>{b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(b.dataset.key);};b.onpointerup=b.onpointercancel=()=>keys.delete(b.dataset.key);});
document.querySelectorAll('[data-look]').forEach(b=>{b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add('Look'+b.dataset.look);};b.onpointerup=b.onpointercancel=()=>keys.delete('Look'+b.dataset.look);});
canvas.onpointerdown=e=>{if(!$('practice').hidden)return;drag={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(!drag)return;yaw-=(e.clientX-drag.x)*.004;pitch=Math.max(-.7,Math.min(.7,pitch-(e.clientY-drag.y)*.003));drag={x:e.clientX,y:e.clientY};};canvas.onpointerup=canvas.onpointercancel=()=>drag=null;
function walk(dx,dz){const x=THREE.MathUtils.clamp(camera.position.x+dx,-7,7),z=THREE.MathUtils.clamp(camera.position.z+dz,-4,10);if(!obstacles.some(o=>Math.hypot(x-o.x,z-o.z)<o.r+.19)){camera.position.x=x;camera.position.z=z;}}
function resize(){renderer.setSize(innerWidth,innerHeight,false);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();}addEventListener('resize',resize);resize();
function loop(now){const dt=Math.min((now-last)/1000,.04);last=now;
 if($('practice').hidden&&ready){if(keys.has('Look-1'))yaw+=dt*1.4;if(keys.has('Look1'))yaw-=dt*1.4;let f=(keys.has('KeyW')?1:0)-(keys.has('KeyS')?1:0),r=(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0);const l=Math.hypot(f,r)||1;f/=l;r/=l;walk((-Math.sin(yaw)*f+Math.cos(yaw)*r)*dt*2.5,0);walk(0,(-Math.cos(yaw)*f-Math.sin(yaw)*r)*dt*2.5);}
 const x=camera.position.x,z=camera.position.z;let floor=Math.abs(x)<3.2&&Math.abs(z)<2.4?.12:0;if(Math.abs(x)<1.7&&z>=2.4&&z<=3)floor=.12*(3-z)/.6;camera.position.y=1.7+floor;
 camera.rotation.set(pitch,yaw,0,'YXZ');near=stations.find(o=>Math.hypot(x-o.x,z-o.z)<2.0)||null;
 $('prompt').textContent=near?`靠近${near.name} · E / 互動 開始練習`:'沿石坡走進棚下，靠近木樁';
 if(session){const clock=performance.now()/1000;const state=session.advance(clock);$('progress').textContent=`節奏 ${state.completed}/${state.total} · 成功 ${state.successes} 次`;
  if(state.results.length>resultCount){const result=state.results.at(-1);$('feedback').textContent=result.result==='precise'?'節奏準確':result.result==='good'?'跟上了節奏':result.reason;resultCount=state.results.length;}
  if(state.done){$('cue').textContent='本輪練習結束';$('retry').hidden=false;$('action').disabled=true;$('feedback').textContent=`成功 ${state.successes}/${state.total} · 只記本輪表現，不增加修為`;}
  else{const remain=state.next.at-(clock-session.start);$('cue').textContent=state.next.label;const t=THREE.MathUtils.clamp(.5-remain/2,0,1);$('marker').style.left=`${t*100}%`;$('breath').firstElementChild.style.transform=`scale(${session.held?1.0+Math.min(1.0,(2.4-Math.max(0,remain))/2.4):1.0})`;}
 }
 renderer.render(scene,camera);requestAnimationFrame(loop);
}requestAnimationFrame(loop);
