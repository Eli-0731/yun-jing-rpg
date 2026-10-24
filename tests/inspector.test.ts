import { before, after, test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { JSDOM, VirtualConsole } from 'jsdom';
import { createApp } from '../services/api/src/app';
import { Database } from '../services/api/src/database';

let runtime: Awaited<ReturnType<typeof createApp>>, base: string, html: string, script: string;
before(async()=>{
  runtime=await createApp({mode:'local',host:'127.0.0.1',port:4310,speed:60},new Database());
  await runtime.app.listen(0,'127.0.0.1');base=await runtime.app.getUrl();
  html=await readFile('apps/inspector/index.html','utf8');script=await readFile('apps/inspector/app.js','utf8');
});
after(async()=>{await runtime.app.close();await runtime.game.db.close();});
async function wait(condition:()=>boolean,message='DOM condition') {
  const deadline=Date.now()+4000;
  while(!condition()){if(Date.now()>deadline)throw new Error(`Timed out: ${message}`);await new Promise(done=>setTimeout(done,10));}
}
function page(initial:Record<string,string>={}) {
  const errors:string[]=[];let inFlight=0;
  let transport:typeof fetch=(input,init)=>fetch(input,init);
  const virtualConsole=new VirtualConsole();virtualConsole.on('jsdomError',error=>errors.push(error.message));
  const dom=new JSDOM(html,{url:base,runScripts:'outside-only',virtualConsole});
  const window=dom.window, document=window.document;
  Object.defineProperty(window.crypto,'randomUUID',{value:randomUUID});
  window.fetch=(async(input:any,init:any)=>{inFlight++;try{return await transport(new URL(input,base),init);}finally{inFlight--;}}) as any;
  for(const [key,value]of Object.entries(initial))window.sessionStorage.setItem(key,value);
  window.eval(script);
  const element=(id:string)=>document.getElementById(id)!;
  const click=async(button:HTMLElement)=>{assert.ok(!(button as HTMLButtonElement).disabled,'Button enabled');button.click();await wait(()=>inFlight===0);await new Promise(done=>setTimeout(done,0));};
  const byText=(label:string)=>{const button=Array.from(document.querySelectorAll('button')).find(e=>e.textContent===label);assert.ok(button,`Missing button ${label}`);return button;};
  const login=async(eligible=true)=>{
    await wait(()=>!(element('sign-in') as HTMLButtonElement).disabled);(element('alias') as HTMLInputElement).value=`ui-${randomUUID().slice(0,8)}`;
    await click(element('sign-in'));assert.equal(element('game').hidden,false);
    if(eligible){
      // Test-only fixture: make this character ten days old without expiring its login token.
      // Production has no endpoint for changing these timestamps.
      const id=JSON.parse(window.sessionStorage.getItem('yunjing-session')!).playerId;
      const state=(await runtime.game.db.query<{state:any}>('SELECT state FROM players WHERE id=$1',[id])).rows[0].state;
      state.journey.createdAt-=10*86400000;state.journey.selectionAt-=10*86400000;
      await runtime.game.db.query('UPDATE players SET state=$2 WHERE id=$1',[id,JSON.stringify(state)]);await window.eval('refresh()');
    }
  };
  return {dom,window,document,errors,element,click,byText,login,setTransport:(value:typeof fetch)=>transport=value,ready:()=>wait(()=>!(element('sign-in') as HTMLButtonElement).disabled)};
}

test('介面邏輯：載入→出生→師承對話→領取手札→購買補給，全部接實際 HTTP API',async()=>{
  const p=page();try{
    await p.login();assert.match(p.element('guidance').textContent!,/測定/);await p.click(p.element('draw'));
    await p.click(p.byText('體修怎麼起步？'));assert.match(p.element('dialogue').textContent!,/沈岳/);
    await p.click(p.byText('法修怎麼起步？'));assert.match(p.element('dialogue').textContent!,/柳知微/);
    const quest=p.document.querySelector('[data-quest="meet-mentor"]')!;assert.match(quest.textContent!,/可領取/);
    await p.click(quest.querySelector('button')!);assert.match(p.element('chapter-progress').textContent!,/1 \/ 5/);
    const offers=p.element('offers');await p.click(offers.querySelectorAll('button')[2]);
    assert.match(p.element('wallet').textContent!,/6/);assert.match(p.element('inventory').textContent!,/青靈草/);
    const session=p.window.sessionStorage.getItem('yunjing-session')!;
    const restored=page({'yunjing-session':session});try{
      await wait(()=>!restored.element('game').hidden);
      assert.match(restored.element('chapter-progress').textContent!,/1 \/ 5/);assert.match(restored.element('wallet').textContent!,/6/);
      assert.deepEqual(restored.errors,[]);
    }finally{restored.dom.window.close();}
    assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});

test('介面邏輯：伺服器已入帳但回應遺失，重新載入重送同一請求只取得一份補給',async()=>{
  const p=page();try{
    await p.login();await p.click(p.element('draw'));
    let lost=false;
    p.setTransport(async(input,init)=>{
      const response=await fetch(input,init);
      if(String(input).endsWith('/v1/actions')&&!lost){lost=true;throw new Error('Simulated lost response after commit');}
      return response;
    });
    await p.click(p.element('offers').querySelectorAll('button')[2]);
    assert.equal(p.element('retry').hidden,false);assert.ok(p.window.sessionStorage.getItem('yunjing-pending'));
    await p.click(p.element('sign-out'));assert.equal(p.element('game').hidden,false);
    const restored=page({'yunjing-session':p.window.sessionStorage.getItem('yunjing-session')!,'yunjing-pending':p.window.sessionStorage.getItem('yunjing-pending')!});
    try{
      await wait(()=>!restored.element('game').hidden);await restored.click(restored.element('retry'));
      assert.equal(restored.window.sessionStorage.getItem('yunjing-pending'),null);assert.match(restored.element('wallet').textContent!,/6/);
      const token=JSON.parse(restored.window.sessionStorage.getItem('yunjing-session')!).token;
      const state=await(await fetch(`${base}/v1/me`,{headers:{Authorization:`Bearer ${token}`}})).json() as any;
      assert.equal(state.player.inventory.find((s:any)=>s.item==='qingling-herb').quantity,3);
      assert.deepEqual(restored.errors,[]);
    }finally{restored.dom.window.close();}
  }finally{p.dom.window.close();}
});

test('介面邏輯：服務端5xx及登入失效保留待確認操作，已明確拒絕的400才清除',async()=>{
  const p=page();try{
    await p.login();await p.click(p.element('draw'));
    p.setTransport(async(input,init)=>String(input).endsWith('/v1/actions')?new Response(JSON.stringify({message:'暫時故障'}),{status:503}):fetch(input,init));
    await p.click(p.element('offers').querySelectorAll('button')[2]);assert.equal(p.element('retry').hidden,false);
    p.setTransport(async(input,init)=>String(input).endsWith('/v1/actions')||String(input).endsWith('/v1/auth/refresh')?new Response(JSON.stringify({message:'登入失效'}),{status:401}):fetch(input,init));
    await p.click(p.element('retry'));assert.equal(p.element('retry').hidden,false);assert.ok(p.window.sessionStorage.getItem('yunjing-pending'));
    p.setTransport(async(input,init)=>String(input).endsWith('/v1/actions')?new Response(JSON.stringify({message:'補給已下架'}),{status:400}):fetch(input,init));
    await p.click(p.element('retry'));assert.equal(p.element('retry').hidden,true);assert.match(p.element('feedback').textContent!,/補給已下架/);
    assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});

test('灌溉介面：建池、選水路、拒絕超額、種植與照料接實際 HTTP，重登保留',async()=>{
  const p=page();let now=Date.now();const previous=runtime.game.options.now;runtime.game.options.now=()=>now;
  try{
    await p.login();await p.click(p.element('draw'));
    await p.click(p.byText('拜入玄岳 · 體修'));
    await p.click(p.byText('採集陣基石'));now+=15001;await p.click(p.byText('採集陣基石'));
    await p.click(p.element('estate').querySelector('button')!);
    assert.match(p.element('estate').textContent!,/已建成.*0\/2/);
    const select=p.element('irrigation-0') as HTMLSelectElement;
    select.value='abundant';select.dispatchEvent(new p.window.Event('change'));
    await wait(()=>p.element('estate').textContent!.includes('2/2'),'water assignment saved');
    const other=p.element('irrigation-1') as HTMLSelectElement;
    other.value='swift';other.dispatchEvent(new p.window.Event('change'));
    await wait(()=>other.value==='rain','rejected assignment reset');
    assert.ok(p.element('feedback').classList.contains('error'));
    await p.click(p.element('plots').querySelector('.plot button')!);
    await p.click(p.byText('採集野生青靈草'));await p.click(p.byText('施草肥 · 青靈草 ×1'));
    assert.match(p.element('plots').textContent!,/深灌養根 · 預計收成 5 株/);
    assert.match(p.element('plots').textContent!,/已照料/);
    assert.equal(p.document.querySelector('[data-before]'),null);
    const restored=page({'yunjing-session':p.window.sessionStorage.getItem('yunjing-session')!});
    try{
      await wait(()=>!restored.element('game').hidden);
      assert.match(restored.element('estate').textContent!,/2\/2/);
      assert.match(restored.element('plots').textContent!,/預計收成 5 株/);
      assert.deepEqual(restored.errors,[]);
    }finally{restored.dom.window.close();}
    assert.deepEqual(p.errors,[]);
  }finally{runtime.game.options.now=previous;p.dom.window.close();}
});

test('新入世介面：自動分配但不揭露，顯示十日等待、基礎武技可用、未入宗不顯示田地',async()=>{
  const p=page();try{
    await p.login(false);
    assert.match(p.element('birth').textContent!,/先天已確定/);assert.match(p.element('selection-status').textContent!,/離線也會計時/);
    assert.equal((p.element('draw') as HTMLButtonElement).disabled,true);
    assert.equal(p.element('plots').hidden,true);assert.match(p.element('housing-title').textContent!,/借住/);
    assert.equal((p.byText('拜入玄岳 · 體修') as HTMLButtonElement).disabled,true);
    await p.click(p.byText('練基礎武技'));assert.match(p.element('stats').textContent!,/體魄 [1-9]/);
    await p.click(p.element('offers').querySelectorAll('button')[2]);assert.match(p.element('wallet').textContent!,/6/);
    assert.match(p.element('birth').textContent!,/待廣場測定/);assert.deepEqual(p.errors,[]);
  }finally{p.dom.window.close();}
});
