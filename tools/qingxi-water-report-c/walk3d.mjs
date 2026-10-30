import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const $=id=>document.getElementById(id),canvas=$('view'),loader=new GLTFLoader(),base='../../art/exports/qingxi-water-report-c/variants/';
const scene=new THREE.Scene();scene.background=new THREE.Color('#d8ded2');
const camera=new THREE.PerspectiveCamera(58,innerWidth/innerHeight,.03,50);camera.rotation.order='YXZ';
let renderer;
try{renderer=new THREE.WebGLRenderer({canvas,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;}catch(e){$('load').textContent='此瀏覽器無法開啟 WebGL，請回村口查看模型圖片。';throw e;}
scene.add(new THREE.HemisphereLight(0xf2f0df,0x656e52,2.4));const sun=new THREE.DirectionalLight(0xfff4d9,3);sun.position.set(3,6,4);scene.add(sun);
const surround=new THREE.Mesh(new THREE.PlaneGeometry(30,30),new THREE.MeshStandardMaterial({color:0xabb59e,roughness:1}));surround.rotation.x=-Math.PI/2;surround.position.y=-.071;scene.add(surround);
let model,roots=[],colliders=[],labels=[],flagPairs=[],loaded=false,yaw=0,pitch=-.22,blocked=0,request=0;
const held=new Set(),params=new URLSearchParams(location.search);$('layout').value=['a','b'].includes(params.get('layout'))?params.get('layout'):'a';$('water').value=['dry','partial','restored'].includes(params.get('state'))?params.get('state'):'dry';
function view(which){held.clear();blocked=0;camera.position.set(1.05,1.7,which==='north'?-2.2:2.2);if(which==='route'){yaw=0;pitch=-.13;}else{camera.lookAt(-.45,.50,which==='north'?.1:-.1);yaw=camera.rotation.y;pitch=camera.rotation.x;}}
function makeLabel(root){const c=document.createElement('canvas');c.width=512;c.height=76;const g=c.getContext('2d');g.fillStyle='#f1eddd';g.fillRect(0,0,512,76);g.fillStyle='#254a3e';g.font='30px sans-serif';g.textAlign='center';g.fillText(root.name.replace(/_GroundOrigin.*/,''),256,49);const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),depthTest:false}));const box=new THREE.Box3().setFromObject(root);box.getCenter(sprite.position);sprite.position.y=box.max.y+.12;sprite.scale.set(.70,.104,1);sprite.visible=$('ids').getAttribute('aria-pressed')==='true';model.add(sprite);labels.push(sprite);}
function applyWater(){const name=$('water').value;let filled=0;
 model?.traverse(o=>{if(o.isMesh&&o.morphTargetDictionary&&o.name.startsWith('WaterSurface_C03')){o.morphTargetInfluences[o.morphTargetDictionary.HalfFull]=name==='partial'?1:0;o.morphTargetInfluences[o.morphTargetDictionary.Filled]=name==='restored'?1:0;filled++;}
  if(o.name.startsWith('StatusPivot'))o.rotation.x=name==='restored'?Math.PI:0;
  if(o.isMesh&&o.name.startsWith('SoilMoisturePatch_C05')){if(!o.userData.privateMaterial){o.material=o.material.clone();o.userData.privateMaterial=true;}o.material.color.set(name==='restored'?0x2b331f:name==='partial'?0x4a4226:0x734a29);}
 });for(const [work,done]of flagPairs){work.visible=name!=='restored';done.visible=name==='restored';}
 $('readout').dataset.water=name;$('readout').dataset.buckets=String(filled);
}
function dispose(object){object.traverse(o=>{if(o.geometry)o.geometry.dispose();const materials=Array.isArray(o.material)?o.material:o.material?[o.material]:[];for(const m of materials){for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}});}
async function loadLayout(){const token=++request;loaded=false;canvas.dataset.loaded='0';$('load').textContent='正在載入實際模型…';held.clear();
 try{const gltf=await loader.loadAsync(base+'VillageCorner-'+$('layout').value+'.glb');if(token!==request){dispose(gltf.scene);return;}
  if(model){scene.remove(model);dispose(model);}model=gltf.scene;scene.add(model);roots=[];labels=[];flagPairs=[];colliders=[];
  model.traverse(o=>{if(/_GroundOrigin/.test(o.name))roots.push(o);});
  for(const root of roots){colliders.push(new THREE.Box3().setFromObject(root));makeLabel(root);}
  const originals=roots.filter(o=>o.name.startsWith('C06_'));
  const complete=await Promise.all(originals.map(async root=>{const id=root.name.replace(/_GroundOrigin.*/,''),g=await loader.loadAsync(base+id+'-complete.glb');return {root,scene:g.scene,id};}));
  if(token!==request){complete.forEach(x=>dispose(x.scene));return;}
  for(const item of complete){const done=item.scene.children.find(o=>o.name.startsWith(item.id+'_GroundOrigin'));if(!done)throw Error('旗面狀態缺少原點');done.removeFromParent();done.position.copy(item.root.position);done.quaternion.copy(item.root.quaternion);done.scale.copy(item.root.scale);model.add(done);flagPairs.push([item.root,done]);}
  loaded=true;canvas.dataset.loaded=String(roots.length);$('load').textContent='已載入 '+roots.length+' 組物件 · 七個形體變體';view('home');applyWater();
 }catch(e){if(token===request){$('load').textContent='模型載入失敗，請確認已下載 LFS 資產並以本機伺服器開啟。';console.error(e);}}
}
function canStand(x,z){if(x< -1.34||x>1.34||z< -2.34||z>2.34)return false;return !colliders.some(b=>b.max.y>.04&&b.min.y<1.75&&x>b.min.x-.16&&x<b.max.x+.16&&z>b.min.z-.16&&z<b.max.z+.16);}
const keys={KeyW:'forward',ArrowUp:'forward',KeyS:'back',ArrowDown:'back',KeyA:'left',ArrowLeft:'left',KeyD:'right',ArrowRight:'right',KeyQ:'turnLeft',KeyE:'turnRight'};
addEventListener('keydown',e=>{if(['SELECT','BUTTON','A'].includes(document.activeElement?.tagName))return;if(keys[e.code]){held.add(keys[e.code]);e.preventDefault();}});addEventListener('keyup',e=>held.delete(keys[e.code]));addEventListener('blur',()=>held.clear());document.addEventListener('visibilitychange',()=>held.clear());
for(const button of document.querySelectorAll('#touch button')){const action=button.dataset.move||('turn'+(button.dataset.turn==='left'?'Left':'Right'));button.addEventListener('pointerdown',e=>{e.preventDefault();button.setPointerCapture(e.pointerId);held.add(action);button.classList.add('held');});for(const event of ['pointerup','pointercancel','lostpointercapture'])button.addEventListener(event,()=>{held.delete(action);button.classList.remove('held');});}
let drag;
canvas.addEventListener('pointerdown',e=>{canvas.focus();canvas.setPointerCapture(e.pointerId);drag=[e.clientX,e.clientY];});canvas.addEventListener('pointermove',e=>{if(drag){yaw-=(e.clientX-drag[0])*.004;pitch=THREE.MathUtils.clamp(pitch-(e.clientY-drag[1])*.004,-1.1,.8);drag=[e.clientX,e.clientY];}});for(const event of ['pointerup','pointercancel'])canvas.addEventListener(event,()=>drag=null);
$('home').onclick=()=>{view('home');canvas.focus();};$('north').onclick=()=>{view('north');canvas.focus();};$('route').onclick=()=>{view('route');canvas.focus();};$('ids').onclick=()=>{const visible=$('ids').getAttribute('aria-pressed')!=='true';$('ids').setAttribute('aria-pressed',String(visible));labels.forEach(s=>s.visible=visible);};$('layout').onchange=loadLayout;$('water').onchange=applyWater;
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
let previous=performance.now();function frame(now){const dt=Math.min((now-previous)/1000,.05);previous=now;if(loaded){yaw+=((held.has('turnLeft')?1:0)-(held.has('turnRight')?1:0))*dt*1.1;
 const f=(held.has('forward')?1:0)-(held.has('back')?1:0),r=(held.has('right')?1:0)-(held.has('left')?1:0),n=Math.max(1,Math.hypot(f,r)),step=1.2*dt/n;
 const dx=(-Math.sin(yaw)*f+Math.cos(yaw)*r)*step,dz=(-Math.cos(yaw)*f-Math.sin(yaw)*r)*step;
 if(dx){if(canStand(camera.position.x+dx,camera.position.z))camera.position.x+=dx;else blocked++;}if(dz){if(canStand(camera.position.x,camera.position.z+dz))camera.position.z+=dz;else blocked++;}
 camera.position.y=1.7;camera.rotation.set(pitch,yaw,0,'YXZ');const out=$('readout');out.value='眼高 1.70 m · 位置 '+camera.position.x.toFixed(2)+' / '+camera.position.z.toFixed(2)+' m';out.dataset.x=String(camera.position.x);out.dataset.z=String(camera.position.z);out.dataset.eye='1.7';out.dataset.blocked=String(blocked);
 }renderer.render(scene,camera);requestAnimationFrame(frame);}
view('home');requestAnimationFrame(frame);loadLayout();
