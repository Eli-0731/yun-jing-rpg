/* Eli-0731 / Codex */
(() => {
 'use strict';
 const R=WaterReportState,F=WaterReportFixtures,RESP=WaterReportResponses,KEY='qingxi-water-report-c-v1',$=id=>document.getElementById(id);
 const assetNames={C01:'村民議事矮桌',C02:'可翻面水情告示',C03_tall_01:'直身高桶',C03_low_02:'八角矮桶',C03_bail_03:'提梁鼓腹桶',C04:'竹製取水扁擔',C05_notch_01:'缺口木牌',C05_fork_02:'分叉柱腳木牌',C06_fork_01:'燕尾布旗',C06_slant_02:'斜切布旗',C07:'修渠手工具箱',C08:'共修紀錄石牌'};
 let state=R.initial(),storageOK=true;
 try{state=R.restore(JSON.parse(localStorage.getItem(KEY)));}catch{storageOK=false;}
 const say=t=>{$('status').textContent=t+(storageOK?'':' 此瀏覽器無法保存，重載後可能重置。');};
 function save(){try{localStorage.setItem(KEY,JSON.stringify(state));}catch{storageOK=false;}}
 function apply(action){const result=R.transition(state,action);state=result.state;save();render();say(result.message);}
 function render(){
  const v=R.view(state),layout=$('layout').value;$('scene').dataset.layout=layout;$('water-label').textContent=v.name;$('scene-image').src=`../../art/previews/qingxi-water-report-c/corner-${layout==='b'?'b-':''}${v.image}.png`;$('scene-image').alt=`青溪村角實際模型渲染：排列 ${layout.toUpperCase()}，${v.name}，${v.bucket}`;$('walk-link').href=`walk3d.html?layout=${layout}&state=${v.image}`;
  for(const [id,text]of [['board-status',v.board],['bucket-status',v.bucket],['flag-status',v.flag],['soil-status',v.field],['record-status',state.choice?R.choices[state.choice]:'未選擇']])$(id).textContent=text;
  $('observations').textContent=v.observationLabels.length?'已見線索：'+v.observationLabels.join('、'):'尚無已確認線索；仍可選擇任一回報方向。';
  $('outcome').textContent='工程結果：'+(v.upstreamOutcomeId||'尚未收到')+' · '+v.name;
  $('upstream-json').value=JSON.stringify(state.input,null,2);
  const current=F.find(f=>JSON.stringify(R.normalize(f))===JSON.stringify(state.input));$('fixture').value=current?current.id:'custom';
  for(const b of document.querySelectorAll('[data-choice]'))b.setAttribute('aria-pressed',String(b.dataset.choice===state.choice));
  $('response-title').textContent=state.choice?R.choices[state.choice]:'還沒決定，也可以先看看村角。';
  $('response-text').textContent=state.choice?(v.key==='unknown'?'尚無可確認的工程結果。你可以先把已有線索告知大家，或請工匠一起核對。':RESP[v.key][state.choice]):'沒找到全部線索也能回報，三種方向沒有必做順序。';
  $('cancel').disabled=state.choice===null;$('journal').replaceChildren();
  const choice=document.createElement('p');choice.textContent=state.choice?'我的決定：'+R.choices[state.choice]:'我的決定：尚未選擇';
  const input=document.createElement('small');input.textContent='依據：'+(v.observationLabels.join('、')||'尚無上游線索')+'；結果 '+(state.input.outcomeId||'尚未完成導水');
  const status=document.createElement('small');status.textContent='看到的水情：'+v.name+'。回報選擇不會自行改變水路。';$('journal').append(choice,input,status);
 }
 for(const f of F){const o=document.createElement('option');o.value=f.id;o.textContent=f.name;$('fixture').append(o);}const custom=document.createElement('option');custom.value='custom';custom.textContent='自訂資料';custom.disabled=true;$('fixture').append(custom);
 $('fixture').addEventListener('change',e=>{const f=F.find(f=>f.id===e.target.value);if(f)apply({type:'load',input:f});});
 $('load-input').addEventListener('click',()=>{try{apply({type:'load',input:JSON.parse($('upstream-json').value)});}catch{say('這段 JSON 讀不懂；請保留 observationIds 陣列與 outcomeId 字串或 null。');}});
 const subtitles={tell_shortage:'讓村裡先知道現況',inspect_crack:'把線索交給工匠確認',protect_nursery:'先留意溪畔動物'};
 for(const [id,name]of Object.entries(R.choices)){const b=document.createElement('button');b.dataset.choice=id;b.setAttribute('aria-pressed','false');b.textContent=name;const small=document.createElement('small');small.textContent=subtitles[id];b.append(small);b.addEventListener('click',()=>apply({type:'choose',choice:id}));$('choices').append(b);}
 $('cancel').addEventListener('click',()=>apply({type:'cancel'}));
 for(const b of document.querySelectorAll('[data-inspect]'))b.addEventListener('click',()=>{document.querySelectorAll('[data-inspect]').forEach(el=>el.classList.toggle('active',el===b));const v=R.view(state),id=b.dataset.inspect;const text={board:'告示：'+v.board+'。切換上游範例可比較缺水與恢復兩面。',bucket:'水桶：'+v.bucket+'。水量只依收到的範例結果改變。',flag:'施工布旗：'+v.flag+'；這是本機工程狀態展示。',soil:'村田土壤：'+v.field+'。濕度木牌不是 A 的水位尺。',record:'石牌只記這次的本機回報：'+(state.choice?R.choices[state.choice]:'尚未選擇')+'；沒有排行榜或貢獻分配。',table:'三個回報方向都可以選，缺線索也不用先做完固定清單。'};say(text[id]);if(id==='table')document.querySelector('[data-choice]')?.focus({preventScroll:false});});
 $('layout').addEventListener('change',render);
 for(const [id,name]of Object.entries(assetNames)){const b=document.createElement('button');b.setAttribute('aria-label','查看'+name+'近景');const img=document.createElement('img');img.src=`../../art/previews/qingxi-water-report-c/${id.includes('_')?'variants/':''}${id}-close.png`;img.alt=name+'實際模型';const label=document.createElement('small');label.textContent=id+' '+name;b.append(img,label);b.addEventListener('click',()=>{$('preview-image').src=img.src;$('preview-title').textContent=id+' · '+name;$('preview').showModal();});$('assets').append(b);}
 $('reset').addEventListener('click',()=>{if(confirm('清除此瀏覽器本包的回報決定，重新開始？')){state=R.initial();save();render();say('已重新開始，可以直接回報，也可以先換一份上游範例。');}});
 $('export').addEventListener('click',()=>{const data={schema:'qingxi-water-report-c/v1',mode:'local-demo',observationIds:state.input.observationIds,outcomeId:state.input.outcomeId,decision:state.choice,requiresServerValidation:true};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='qingxi-water-report-local.json';a.click();URL.revokeObjectURL(url);say('已匯出本機決定；沒有正式物品、貢獻或世界進度收據。');});
 render();if(!storageOK)say('已開始新的本機展示。');
 if('serviceWorker'in navigator&&location.protocol!=='file:')navigator.serviceWorker.register('sw.js').catch(()=>say('離線快取尚未啟用，目前仍可操作。'));
})();
