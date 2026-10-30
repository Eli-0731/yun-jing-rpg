// Records the 青溪見聞 demo (npm start first) through Chrome DevTools screencast, no extra packages. Usage: node record.mjs <outDir>; then encode with art/source/qingxi-sightings-c/encode_video.py
import {spawn} from 'node:child_process';import {mkdirSync,writeFileSync,rmSync} from 'node:fs';import path from 'node:path';
const out=path.resolve(process.argv[2]||'frames');rmSync(out,{recursive:true,force:true});mkdirSync(out,{recursive:true});
const W=1440,H=900,PORT=9333,URL='http://127.0.0.1:4331/tools/qingxi-sightings-c/';
const profile=path.join(path.dirname(out),'profile');rmSync(profile,{recursive:true,force:true});
const chrome=spawn(process.env.CHROME||'C:/Program Files/Google/Chrome/Application/chrome.exe',[`--remote-debugging-port=${PORT}`,'--headless=new',`--window-size=${W},${H}`,`--user-data-dir=${profile}`,'--no-first-run','--hide-scrollbars','--force-device-scale-factor=1','--lang=zh-TW','about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let targets;for(let i=0;i<50;i++){try{targets=await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();break;}catch{await sleep(200);}}
const ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
let id=0;const pend=new Map(),frames=[];
ws.onmessage=async e=>{const m=JSON.parse(e.data);
  if(m.id&&pend.has(m.id)){pend.get(m.id)(m);pend.delete(m.id);}
  if(m.method==='Page.screencastFrame'){const p=m.params;frames.push({t:p.metadata.timestamp,file:`f${String(frames.length).padStart(5,'0')}.jpg`});
    writeFileSync(path.join(out,frames.at(-1).file),Buffer.from(p.data,'base64'));send('Page.screencastFrameAck',{sessionId:p.sessionId});}};
function send(method,params={}){return new Promise((res,rej)=>{const i=++id;pend.set(i,m=>m.error?rej(new Error(method+': '+m.error.message)):res(m.result));ws.send(JSON.stringify({id:i,method,params}));});}
const js=async expr=>(await send('Runtime.evaluate',{expression:expr,awaitPromise:true,returnByValue:true})).result.value;
const keyCodes={w:87,a:65,s:83,d:68,f:70};
const key=(type,k)=>send('Input.dispatchKeyEvent',{type,key:k,code:'Key'+k.toUpperCase(),windowsVirtualKeyCode:keyCodes[k],text:type==='keyDown'?k:undefined});
const press=async k=>{await key('keyDown',k);await key('keyUp',k);};
async function click(sel){const r=await js(`(()=>{const b=document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect();return [b.x+b.width/2,b.y+b.height/2]})()`);
  for(const type of ['mouseMoved','mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:r[0],y:r[1],button:'left',clickCount:1});}
const caption=t=>js(`(()=>{let c=document.getElementById('__cap');if(!c){c=document.createElement('div');c.id='__cap';c.style.cssText='position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:2147483647;background:rgba(30,28,24,.82);color:#f6efe0;font:600 22px "Microsoft JhengHei",serif;letter-spacing:.08em;padding:8px 22px;border-radius:24px;pointer-events:none;transition:opacity .3s';}const card=document.getElementById('card');(card.open?card:document.documentElement).append(c);
  c.textContent=${JSON.stringify(t)};c.style.opacity=${t?1:0};})()`);
// walk with WASD until within r metres of (x,z); keys re-chosen as direction changes
async function walk(x,z,r=.6){let held=[];for(let i=0;i<2000;i++){const p=await js('__sightings.pos');const dx=x-p.x,dz=z-p.z,d=Math.hypot(dx,dz);if(d<r)break;
  const want=[];if(dz>r*.5)want.push('w');if(dz<-r*.5)want.push('s');if(dx>r*.5)want.push('d');if(dx<-r*.5)want.push('a');
  for(const k of held)if(!want.includes(k))await key('keyUp',k);for(const k of want)if(!held.includes(k))await key('keyDown',k);held=want;await sleep(30);}
  for(const k of held)await key('keyUp',k);}

await send('Page.enable');await send('Runtime.enable');
await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'light'}]});
await send('Emulation.setDeviceMetricsOverride',{width:W,height:H,deviceScaleFactor:1,mobile:false});
await send('Page.navigate',{url:URL});await sleep(2500);
await js(`localStorage.clear()`);await send('Page.reload');await sleep(3000);
if(await js('typeof __sightings')!=='object')throw new Error('demo did not load');
await js(`document.getElementById('map').focus()`);
await send('Page.startScreencast',{format:'jpeg',quality:88,maxWidth:W,maxHeight:H,everyNthFrame:1});
const T0=Date.now(),mark=[];const at=l=>mark.push([l,(Date.now()-T0)/1000]);
at('title');await caption('青溪見聞：鼇極．青溪河谷的十二則見聞');await sleep(3500);
at('walk1');await caption('官道上走一走，白圈內有東西就會亮起微光');await walk(6,-129);await sleep(600);await walk(-1.6,-134.2,.4);await sleep(900);
at('find1');await caption('走到腳邊，按 F 細看');await sleep(1600);await press('f');await sleep(800);
at('card1');await caption('紅印見聞卡：一段短文＋可以旋轉的道具');await sleep(5500);
await click('#card-close');await sleep(900);
at('walk2');await caption('順著官道往北');await walk(2.4,-112);await walk(2.2,-91.4,.4);await sleep(700);
at('find2');await caption('路邊一線枯草');await sleep(1200);await press('f');await sleep(800);
await caption('第二則見聞');await sleep(4500);await click('#card-close');await sleep(900);
at('night');await caption('時辰與天氣會改變能找到的東西');await click('input[name=time][value=night]');await sleep(1400);await click('#rain');await sleep(1400);
await click('input[name=time][value=day]');await click('#rain');await sleep(1000);
at('a3');await caption('西溪 A3：夜裡磨坊旁才有微光');await js(`__sightings.setArea('A3');__sightings.pos={x:-74,z:9};`);await click('input[name=time][value=night]');await sleep(700);
await walk(-86,10.5);await sleep(1300);await click('input[name=time][value=day]');await sleep(1100);
await caption('白天就看不見了');await sleep(1400);await click('input[name=time][value=night]');await sleep(500);
await walk(-89.9,13.6,.4);await sleep(500);await press('f');await sleep(800);await caption('第三則：磨坊的舊木齒');await sleep(4500);await click('#card-close');await sleep(800);
at('book');await caption('收藏頁：照找到的順序排好');await click('#tab-book');await sleep(3000);
await click('#book li:nth-child(1) button');await caption('點一下可以再翻開');await sleep(3500);await click('#card-close');await sleep(1200);
at('end');await caption('只存在本機；正式結果由伺服器決定');await sleep(2500);await caption('');await sleep(800);
await send('Page.stopScreencast');await sleep(500);
const found=await js('__sightings.state.found');
writeFileSync(path.join(out,'frames.json'),JSON.stringify({frames,marks:mark,found},null,1));
console.log('frames',frames.length,'seconds',((frames.at(-1).t-frames[0].t)).toFixed(1),'found',found,'marks',JSON.stringify(mark));
ws.close();chrome.kill();process.exit(0);
