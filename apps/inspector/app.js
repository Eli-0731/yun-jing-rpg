const $ = id => document.getElementById(id);
let credentials = JSON.parse(sessionStorage.getItem('yunjing-session') || 'null');
let snapshot, definitions, pending = JSON.parse(sessionStorage.getItem('yunjing-pending') || 'null'), busy = false, receivedAt = 0;
let viewKey = '', refreshing = false, sessionGeneration = 0;
function storePending(value) { pending=value; if(value)sessionStorage.setItem('yunjing-pending',JSON.stringify(value));else sessionStorage.removeItem('yunjing-pending');$('retry').hidden=!value; }
if(pending&&!pending.actorId&&credentials?.playerId)storePending({...pending,actorId:credentials.playerId});
const labels = { 'built:cistern':'建成蓄水池', tended:'照料靈植', gathered:'第一次採集', planted:'播下靈種', harvested:'第一次收成', practiced:'開始修行', bathed:'完成藥浴', awakened:'後天開靈', 'project-reward':'青溪共同成果', 'first-breakthrough':'啟蒙試煉完成', 'crafted:body-bath':'掌握淬體藥浴', 'crafted:water-purifier':'掌握淨水藥劑', 'resolved:ecology':'恢復水質', 'resolved:coexist':'與靈獸共存' };
const feedback = (message, error=false) => { $('feedback').textContent=message; $('feedback').classList.toggle('error',error); };
function storeSession(value) { credentials=value; sessionGeneration++; if(value) sessionStorage.setItem('yunjing-session',JSON.stringify(value)); else sessionStorage.removeItem('yunjing-session'); }
async function request(path, body, retryAuth=true) {
  const response = await fetch(`/v1/${path}`,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(credentials?{Authorization:`Bearer ${credentials.token}`}:{})},body:body===undefined?undefined:JSON.stringify(body)});
  const value=await response.json();
  if(response.status===401 && retryAuth && credentials?.refreshToken && path!=='auth/refresh') { const renewed=await request('auth/refresh',{refreshToken:credentials.refreshToken},false); storeSession(renewed); return request(path,body,false); }
  if(!response.ok) { const error=new Error(value.message||'操作未完成'); error.confirmed=response.status>=400&&response.status<500&&response.status!==401; error.status=response.status; throw error; }
  return value;
}
function button(label, action) { const element=document.createElement('button'); element.textContent=label; element.onclick=()=>perform(action); return element; }
function line(parent,label,value) { const row=document.createElement('div'); row.className='item'; const name=document.createElement('span'); name.textContent=label; const amount=document.createElement('b'); amount.textContent=value; row.append(name,amount); parent.append(row); }
function seconds(readyAt) { return Math.max(0,Math.ceil((readyAt-snapshot.serverTime-(Date.now()-receivedAt))/1000)); }
function itemLabel(id) { return definitions.items.find(item=>item.id===id)?.label || id; }
function paragraph(text, className='') { const p=document.createElement('p');p.textContent=text;p.className=className;return p; }
function renderJourney() {
  const journey=snapshot?.player.journey;$('journey-section').hidden=!journey;
  if(!journey)return;
  const remaining=seconds(journey.selectionAt),days=Math.floor(remaining/86400),hours=Math.floor(remaining%86400/3600),minutes=Math.floor(remaining%3600/60);
  $('selection-status').textContent=journey.assessedAt!==null?'已完成廣場測資，可選擇目前開放的宗門。':remaining?`距選比資格還有 ${days} 天 ${hours} 小時 ${minutes} 分鐘；離線也會計時。`:'已取得選比資格，可前往廣場測定確切資質。';
  $('draw').textContent='前往廣場測資';$('draw').hidden=journey.assessedAt!==null;$('draw').disabled=remaining>0;
}
function renderStudy() {
  const state=snapshot.player.study||{focus:null,progressMs:{},mastered:[]};
  const hidden=!!snapshot.player.journey&&snapshot.player.journey.assessedAt===null;
  const active=definitions.study.techniques.find(item=>item.id===state.focus);
  $('study-summary').textContent=active?`目前專注：${active.label}${hidden?'。廣場測資後顯示完整進度。':'；離線時間持續累積。'}`:'可自由選擇第一門技藝。';
  $('techniques').replaceChildren();
  for(const technique of definitions.study.techniques) {
    const row=document.createElement('div');row.className='item';
    const title=document.createElement('span');title.textContent=`${technique.label} · 基準 ${technique.days} 日 · ${technique.effect}`;
    const mastered=state.mastered.includes(technique.id);
    const progress=state.progressMs[technique.id]||0;
    row.append(title);
    if(mastered) row.append(paragraph('已入門'));
    else {
      if(!hidden)row.append(paragraph(`研習進度：${(progress/86400000).toFixed(1)} / ${technique.days} 基準日`,'hint'));
      const focus=button(state.focus===technique.id?'研習中':'專注研習',{kind:'focus-technique',technique:technique.id});
      focus.disabled=state.focus===technique.id;row.append(focus);
      if(!hidden&&progress>=technique.days*86400000)row.append(button('確認入門',{kind:'claim-technique',technique:technique.id}));
    }
    $('techniques').append(row);
  }
}
function renderJournal() {
  const journal=snapshot.journal;
  if(!journal){$('guidance').textContent='正在讀取修行手札…';return;}
  $('chapter-title').textContent=journal.title;$('chapter-description').textContent=journal.introduction;$('guidance').textContent=journal.guidance;
  $('chapter-progress').textContent=journal.finished?'本章主要目標已完成，可繼續探索支線與經營洞府。':`主要目標 ${journal.completed} / ${journal.total} · 支線不影響主線完成`;
  const expanded=new Set(Array.from($('quests').querySelectorAll('details[open]')).map(element=>element.dataset.quest));
  const focused=document.activeElement?.closest('[data-quest]')?.dataset.quest;
  $('quests').replaceChildren();
  const statuses={locked:'前置未完成',active:'進行中',ready:'可領取',claimed:'已領取'};
  for(const quest of journal.quests) {
    const row=document.createElement('details');row.dataset.quest=quest.id;row.className=`quest ${quest.status}`;row.open=expanded.has(quest.id)||quest.id===journal.nextQuestId;
    const summary=document.createElement('summary');summary.textContent=`${quest.optional?'支線 · ':''}${quest.title} — ${statuses[quest.status]}`;row.append(summary,paragraph(quest.description));
    const objectives=document.createElement('ul');
    for(const objective of quest.objectives){const entry=document.createElement('li');entry.textContent=`${objective.complete?'✓':'○'} ${objective.label} ${objective.current}/${objective.target}`;objectives.append(entry);}
    row.append(objectives,paragraph(quest.hint,'hint'));
    if(quest.blockedBy.length) row.append(paragraph(`先領取：${quest.blockedBy.map(id=>journal.quests.find(q=>q.id===id)?.title||id).join('、')}`,'hint'));
    row.append(paragraph(`個人成果：${quest.rewards.map(reward=>`${itemLabel(reward.item)} ×${reward.quantity}`).join('、')}（綁定／每個身分一次）`,'reward'));
    const claim=button(quest.status==='claimed'?'成果已收下':'領取手札成果',{kind:'claim-quest',quest:quest.id});claim.disabled=quest.status!=='ready';row.append(claim);$('quests').append(row);
  }
  if(focused) $('quests').querySelector(`[data-quest="${focused}"] summary`)?.focus({preventScroll:true});
}
function setupMentors() {
  for(const mentor of definitions.chapter.mentors) {
    const card=document.createElement('div');card.className='mentor';const title=document.createElement('h3');title.textContent=`${mentor.name} · ${mentor.title}`;
    card.append(title,paragraph(mentor.introduction));const buttons=document.createElement('div');buttons.className='buttons';
    for(const topic of mentor.topics){const element=document.createElement('button');element.textContent=topic.label;element.onclick=async()=>{
      if(await perform({kind:'talk',mentor:mentor.id,topic:topic.id})){$('dialogue').hidden=false;$('dialogue').textContent=`${mentor.name}：${topic.text}`;}
    };buttons.append(element);}
    card.append(buttons);$('mentors').append(card);
  }
  $('merchant-name').textContent=`${definitions.chapter.merchant.name} · ${definitions.chapter.merchant.title}`;
  $('merchant-description').textContent=definitions.chapter.merchant.description;
}
function renderMerchant() {
  const balance=snapshot.player.inventory.filter(item=>item.item==='spirit-stone').reduce((sum,item)=>sum+item.quantity,0);
  $('wallet').textContent=`可用靈石：${balance}`;$('offers').replaceChildren();
  for(const offer of definitions.chapter.merchant.offers){const row=document.createElement('div');row.className='item';const name=document.createElement('span');name.textContent=`${itemLabel(offer.item)} ×${offer.quantity}`;const buy=button(`購買 · ${offer.price} 靈石`,{kind:'buy',offer:offer.id,packs:1});buy.setAttribute('aria-label',`購買${itemLabel(offer.item)} ${offer.quantity}份，${offer.price}靈石`);buy.disabled=!(snapshot.birthAssigned??snapshot.birth)||balance<offer.price;row.append(name,buy);$('offers').append(row);}
}
function render() {
  if(!snapshot)return;
  const key=JSON.stringify([snapshot.player,snapshot.birth,snapshot.world,snapshot.journal]);
  if(key===viewKey)return;viewKey=key;
  const p=snapshot.player; $('login').hidden=true; $('game').hidden=false;
  $('name').textContent=`${p.name} · ${p.realm ? '啟蒙試煉已完成':'修行初始'}`;
  $('birth').textContent=snapshot.birth?`${snapshot.birth.label} / 先天靈根：${snapshot.birth.roots.join('、')||'無'} / 當前靈根：${p.roots?.join('、')||'無'} / 靈竅 ${p.apertures}`:snapshot.birthAssigned?'先天已確定 · 確切資質待廣場測定':'先測定天賦，再開始你的修行。';
  $('draw').hidden=!!snapshot.birth;$('draw').disabled=false;$('draw').textContent='測定先天天賦 · 僅一次';renderJourney();renderStudy();
  const hasCave=!p.journey||p.journey.housing==='cave';
  $('housing-title').textContent=hasCave?'洞府 · 四畦靈田':'聚落借住小屋';
  $('housing-hint').textContent=hasCave?'已取得種植空間；成熟不會枯萎，離線也會生長。':'正式洞府與靈田於入宗後取得。目前可修習煉氣訣、武技與採集。';
  $('plots').hidden=!hasCave;$('estate').hidden=!hasCave;
  document.querySelectorAll('[data-action]').forEach(element=>{const action=JSON.parse(element.dataset.action);if(action.kind==='enroll')element.disabled=!!p.journey&&(p.journey.assessedAt===null||!!p.sect&&p.sect!==action.sect);});
  $('stats').textContent=`體魄 ${p.body} · 引氣 ${p.qi} · ${definitions.sects.find(x=>x.id===p.sect)?.label||'尚未拜師'}`;
  const estate=p.estate||{cistern:false,bound:false,modes:['rain','rain','rain','rain']};
  const usedWater=estate.modes.reduce((sum,id)=>sum+definitions.estate.modes.find(mode=>mode.id===id).water,0);
  $('estate').replaceChildren(paragraph(estate.cistern?`蓄水池已建成 · 已配置供水 ${usedWater}/${definitions.estate.cistern.capacity}${estate.bound?' · 灌溉產物綁定':''}`:'建造蓄水池，選擇兩畦細流催生，或一畦深灌養根。','guidance'));
  if(!estate.cistern){const costs=definitions.estate.cistern.cost.map(cost=>`${itemLabel(cost.item)} ×${cost.quantity}`).join('、');const build=button(`建造蓄水池 · ${costs}`,{kind:'build-cistern'});build.disabled=!snapshot.birth;$('estate').append(build);}
  $('estate').append(paragraph('水路配置占用供水額度，只能在空田調整；採收不會自動釋出配置。','hint'));
  $('plots').replaceChildren();
  for(let i=0;i<4;i++) {
    const plot=p.plots.find(x=>x.index===i), box=document.createElement('div'); box.className='plot';
    const symbol=document.createElement('div'); symbol.className='sprout'; symbol.textContent=plot?'❧':'·';
    const title=document.createElement('strong'); title.textContent=plot?definitions.crops.find(x=>x.id===plot.crop).label:`靈田 ${i+1}`; box.append(symbol,title);
    if(plot) {
      const status=document.createElement('p'); status.dataset.ready=plot.readyAt;status.textContent=seconds(plot.readyAt)>0?`${seconds(plot.readyAt)} 秒後成熟`:'已成熟，隨時可收成';
      const mode=definitions.estate.modes.find(mode=>mode.id===(plot.mode||'rain'));
      box.append(paragraph(`${mode.label} · 預計收成 ${plot.harvestYield??definitions.crops.find(c=>c.id===plot.crop).yield} 株${plot.bound?' · 綁定':''}`,'hint'),status,button('收成',{kind:'harvest',plot:i}));
      if(plot.plantingId&&!plot.tended){const tend=button('施草肥 · 青靈草 ×1',{kind:'tend-plot',plot:i,plantingId:plot.plantingId});tend.dataset.before=plot.readyAt;tend.disabled=seconds(plot.readyAt)===0;box.append(tend);}
      if(plot.tended)box.append(paragraph('已照料 · 這一茬增產 1 株','hint'));
    }
    else {
      const label=document.createElement('label');label.textContent='水路配置';label.htmlFor=`irrigation-${i}`;const select=document.createElement('select');select.id=label.htmlFor;
      for(const mode of definitions.estate.modes){const option=document.createElement('option');option.value=mode.id;option.textContent=`${mode.label} · 供水 ${mode.water}`;option.selected=estate.modes[i]===mode.id;select.append(option);}
      select.disabled=!snapshot.birth;const selectedMode=definitions.estate.modes.find(m=>m.id===estate.modes[i]);
      select.onchange=async()=>{const changed=await perform({kind:'configure-irrigation',plot:i,mode:select.value});if(!changed)select.value=estate.modes[i];};
      box.append(label,select,paragraph(selectedMode.description,'hint'));
      for(const crop of definitions.crops) box.append(button(`種${crop.label}`,{kind:'plant',plot:i,crop:crop.id}));
    }
    $('plots').append(box);
  }
  $('channel').value=snapshot.world.channel;
  $('world').textContent=`水渠 ${snapshot.world.channel}/${snapshot.world.required} · 水質 ${snapshot.world.waterQuality} · 靈獸棲地${snapshot.world.sanctuary?'已安置':'待調查'}`;
  $('investigation').replaceChildren();
  for(const [clue,label] of [['broken-array','破裂陣基'],['dry-lotus','枯萎水蓮'],['beast-nest','靈獸巢穴']]) $('investigation').append(button(`${p.clues.includes(clue)?'✓ ':''}${label}`,{kind:'investigate',clue}));
  $('history').replaceChildren(); for(const event of snapshot.world.history.slice(-6).reverse()) {const row=document.createElement('li');row.textContent=`${event.player} · ${event.action}`;$('history').append(row);}
  $('inventory').replaceChildren();for(const item of p.inventory)line($('inventory'),`${definitions.items.find(x=>x.id===item.item)?.label||item.item}${item.bound?' · 綁定':''}${item.potency>100?' · 上品':''}`,item.quantity);
  $('jobs').replaceChildren();for(const job of p.jobs.filter(x=>!x.claimed)){const row=document.createElement('div');row.className='job';const name=document.createElement('span');name.dataset.jobReady=job.readyAt;name.dataset.label=definitions.recipes.find(x=>x.id===job.recipe).label;name.textContent=`${name.dataset.label} · ${seconds(job.readyAt)?`${seconds(job.readyAt)}秒`:'已完成'}`;row.append(name,button('領取',{kind:'claim-craft',job:job.id}));$('jobs').append(row);}
  $('milestones').replaceChildren();for(const mark of p.milestones){if(mark.startsWith('topic:'))continue;const chip=document.createElement('span');chip.className='milestone';chip.textContent=mark.startsWith('quest:')?`完成：${definitions.chapter.quests.find(q=>`quest:${q.id}`===mark)?.title||mark}`:mark.startsWith('talked:')?`結識${definitions.chapter.mentors.find(m=>`talked:${m.id}`===mark)?.name||''}`:mark==='purchased-supplies'?'採買補給':labels[mark]||mark;$('milestones').append(chip);}
  $('clue-notes').replaceChildren();for(const clue of definitions.chapter.clues.filter(clue=>p.clues.includes(clue.id))){const note=document.createElement('details');const title=document.createElement('summary');title.textContent=clue.label;note.append(title,paragraph(clue.description));$('clue-notes').append(note);}
  renderJournal();renderMerchant();
}
async function refresh() {
  if(refreshing)return;refreshing=true;
  const playerId=credentials?.playerId, generation=sessionGeneration;
  try{const value=await request('me');if(credentials?.playerId!==playerId||sessionGeneration!==generation)return;if(snapshot&&snapshot.player.id===value.player.id&&snapshot.version>value.version)return;snapshot=value;receivedAt=Date.now();render();}
  finally{refreshing=false;}
}
async function perform(action, retry=false) {
  if(busy)return;
  if(pending&&!retry){feedback('前一筆操作尚未確認，請先按重試。',true);return;}
  if(pending?.actorId&&pending.actorId!==credentials?.playerId){feedback('待確認操作屬於另一個修行身分，請用原身分重新登入。',true);return;}
  busy=true;if(!pending)storePending({requestId:crypto.randomUUID(),action,actorId:credentials.playerId});
  try {snapshot=await request('actions',pending);receivedAt=Date.now();storePending(null);feedback('已保存。');render();if(!snapshot.journal)await refresh();return true;}
  catch(error){if(error.confirmed)storePending(null);feedback(error.message,true);}
  finally{busy=false;$('retry').hidden=!pending;}
}
$('sign-in').onclick=async()=>{try{const session=await request('auth/local',{alias:$('alias').value.trim()});if(pending?.actorId&&pending.actorId!==session.playerId){feedback('有尚未確認的操作，請輸入原本的測試身分。',true);return;}storeSession(session);await refresh();feedback('已進入青溪。你的修行進度會保存在本機服務端。');}catch(error){feedback(error.message,true);}};
$('sign-out').onclick=()=>{if(busy||pending){feedback('先確認目前操作結果，再切換身分。',true);return;}storeSession(null);snapshot=null;viewKey='';$('dialogue').hidden=true;$('quests').replaceChildren();$('login').hidden=false;$('game').hidden=true;$('retry').hidden=true;feedback('輸入另一個測試身分即可進入。');};
$('draw').onclick=()=>perform({kind:snapshot?.player.journey?'appraise':'birth'});$('retry').onclick=()=>perform(pending.action,true);
document.querySelectorAll('[data-action]').forEach(element=>element.onclick=()=>perform(JSON.parse(element.dataset.action)));
(async()=>{try{const health=await request('health');definitions=await request('content');setupMentors();$('mode').textContent=`${health.mode==='local'?'本機驗證':'測試服務'} · 生長 ${health.speed}×`;$('sign-in').disabled=health.mode!=='local';if(health.mode!=='local'){feedback('正式登入請由遊戲客戶端開啟瀏覽器驗證。');}if(credentials)await refresh();}catch(error){feedback(error.message,true);}})();
setInterval(()=>{if(snapshot&&!busy&&!pending)refresh().catch(error=>feedback(error.message,true));},5000);
$('retry').hidden=!pending;
setInterval(()=>{if(snapshot)document.querySelectorAll('[data-ready]').forEach(element=>{const remaining=seconds(Number(element.dataset.ready));element.textContent=remaining?`${remaining} 秒後成熟`:'已成熟，隨時可收成';});},1000);
setInterval(()=>{if(snapshot)document.querySelectorAll('[data-job-ready]').forEach(element=>{const remaining=seconds(Number(element.dataset.jobReady));element.textContent=`${element.dataset.label} · ${remaining?`${remaining}秒`:'已完成'}`;});},1000);
setInterval(()=>{if(snapshot)document.querySelectorAll('[data-before]').forEach(element=>{element.disabled=seconds(Number(element.dataset.before))===0;});},1000);
setInterval(()=>{if(snapshot)renderJourney();},1000);
