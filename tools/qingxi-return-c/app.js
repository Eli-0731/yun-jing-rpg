(() => {
 'use strict';
 const R=QingxiReturn,KEY='qingxi-return-c-v1',$=id=>document.getElementById(id);
 const assets={C01:'回村背籠',C02:'低木分揀桌',C03:'收納竹匣',C04:'藥草布包'};
 let state=R.empty(),storageOK=true;
 try{state=R.restore(JSON.parse(localStorage.getItem(KEY)));}catch{storageOK=false;}
 const say=text=>{$('status').textContent=text+(storageOK?'':' 此瀏覽器無法保存，重載後可能重置。');};
 function save(){try{localStorage.setItem(KEY,JSON.stringify(state));}catch{storageOK=false;}}
 function act(action){const r=R.apply(state,action);state=r.state;save();render();say(r.message);if(action.type==='select')document.querySelector(`[data-sample="${state.selected}"]`)?.focus({preventScroll:true});document.querySelectorAll('[data-world]').forEach(b=>b.classList.toggle('active',b.dataset.world===r.feedback));}
 function render(){
  $('samples').replaceChildren();
  for(const [id,s] of Object.entries(R.samples)){
   const b=document.createElement('button');b.className='sample';b.dataset.sample=id;b.setAttribute('aria-pressed',state.selected===id?'true':'false');
   const symbol=document.createElement('span');symbol.className='symbol';symbol.textContent=s.symbol;
   const name=document.createElement('b');name.textContent=s.name;
   const sub=document.createElement('small');sub.textContent='1 份 · '+(R.destinations[state.placements[id]]||'待分揀');
   b.append(symbol,name,sub);b.addEventListener('click',()=>act({type:'select',sample:id}));$('samples').append(b);
  }
  const s=R.samples[state.selected];$('detail').textContent=s?`${s.name}｜從${s.source}帶回。${s.use}`:'先選一份你想整理的樣本。';
  const counts=R.summary(state);for(const [key,n] of Object.entries(counts)){const el=$('count-'+key);if(el)el.textContent=String(n);}
  $('journal').replaceChildren();
  for(const [id,sample] of Object.entries(R.samples)){
   const li=document.createElement('li');li.textContent=sample.name;
   const dest=document.createElement('span');dest.className='destination';dest.textContent=R.destinations[state.placements[id]]||'仍在分揀桌';
   const source=document.createElement('small');source.textContent=`從${sample.source}帶回 · 本機樣本 1 份`;
   li.append(dest,source);$('journal').append(li);
  }
  $('undo').disabled=!state.lastAction;
  $('history').replaceChildren();for(const e of state.journal){const li=document.createElement('li');li.textContent=`${e.kind==='undo'?'取消誤選':'整理'}：${R.samples[e.sample].name} → ${R.destinations[e.to]||'分揀桌'}`;$('history').append(li);}
 }
 for(const [id,name] of Object.entries(R.destinations)){
  const b=document.createElement('button');b.dataset.destination=id;b.textContent=name;
  const small=document.createElement('small');small.textContent=id==='save'?'收進竹匣，慢慢再看':'裝入布包，留待研究';b.append(small);
  b.addEventListener('click',()=>act({type:'move',destination:id}));$('destinations').append(b);
 }
 document.querySelectorAll('[data-world]').forEach(b=>b.addEventListener('click',()=>{if(b.dataset.world==='table'){if(!state.selected)act({type:'select',sample:'herb'});else{say('點選右側樣本可換一份；再選擇保存或留待煉製。');b.classList.add('active');}}else act({type:'move',destination:b.dataset.world});}));
 for(const [id,name] of Object.entries(assets)){
  const b=document.createElement('button');b.setAttribute('aria-label','查看'+name+'近景');
  const img=document.createElement('img');img.src=`previews/${id}-close.png`;img.alt=name+'實際渲染';const label=document.createElement('small');label.textContent=id+' '+name;b.append(img,label);
  b.addEventListener('click',()=>{$('preview-image').src=img.src;$('preview-title').textContent=id+' · '+name;$('preview').showModal();});$('assets').append(b);
 }
 $('undo').addEventListener('click',()=>act({type:'undo'}));
 $('reset').addEventListener('click',()=>{if(confirm('重新開始這台瀏覽器的樣本整理？')){state=R.empty();save();render();say('三份樣本已回到分揀桌。');}});
 $('contract').addEventListener('click',()=>{
  const data={schema:'qingxi-return-intent/v1',mode:'local-demo',revision:state.revision,intents:Object.entries(state.placements).filter(([,d])=>d!==null).map(([id,d])=>({sampleReference:id,destination:d,requiresServerValidation:true})),ui:{selectedSample:state.selected,canUndo:!!state.lastAction}};
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='qingxi-return-local-intents.json';a.click();URL.revokeObjectURL(url);say('已匯出本機意圖；正式物品身分、數量、距離與收據仍須服務端驗證。');
 });
 render();if(!storageOK)say('已開始新的本機展示。');
 if('serviceWorker'in navigator&&location.protocol!=='file:')navigator.serviceWorker.register('sw.js').catch(()=>say('離線快取未啟用，目前仍可在線操作。'));
})();
