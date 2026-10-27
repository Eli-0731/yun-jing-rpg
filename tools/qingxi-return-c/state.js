/* Local demonstration only. Immutable sample definitions are never persisted as inventory. */
(function(root){
 'use strict';
 const samples=Object.freeze({
  herb:Object.freeze({name:'青靈草樣本',source:'溪畔淺灘',use:'辨識葉脈，或留作配伍觀察。',symbol:'草'}),
  ore:Object.freeze({name:'溪石礦樣本',source:'溪路石壁',use:'觀察石紋，或留待工坊辨材。',symbol:'石'}),
  seed:Object.freeze({name:'露珠草種樣本',source:'村外草坡',use:'保存作為種植觀察樣本。',symbol:'種'})
 });
 const destinations=Object.freeze({save:'保存',alchemy:'留待煉製'});
 const validDestination=x=>x===null||Object.hasOwn(destinations,x);
 const empty=()=>({version:1,selected:null,placements:{herb:null,ore:null,seed:null},lastAction:null,journal:[],revision:0});
 function restore(raw){
  const s=empty();if(!raw||raw.version!==1)return s;
  for(const id of Object.keys(samples))if(validDestination(raw.placements?.[id]))s.placements[id]=raw.placements[id];
  if(Object.hasOwn(samples,raw.selected))s.selected=raw.selected;
  if(Number.isSafeInteger(raw.revision)&&raw.revision>=0)s.revision=raw.revision;
  if(Array.isArray(raw.journal))s.journal=raw.journal.filter(e=>e&&Object.hasOwn(samples,e.sample)&&validDestination(e.to)&&['move','undo'].includes(e.kind)).slice(-30).map(e=>({sample:e.sample,to:e.to,kind:e.kind}));
  const a=raw.lastAction;
  if(a&&Object.hasOwn(samples,a.sample)&&validDestination(a.from)&&Object.hasOwn(destinations,a.to)&&a.from!==a.to&&s.placements[a.sample]===a.to)s.lastAction={sample:a.sample,from:a.from,to:a.to};
  return s;
 }
 function apply(s,action){
  const result=(state,message,feedback=null)=>({state,message,feedback});
  if(action?.type==='select'){
   if(!Object.hasOwn(samples,action.sample))return result(s,'找不到這份樣本，請重新選擇。');
   return result({...s,selected:action.sample},`已選取${samples[action.sample].name}；接著選一個去向。`,'table');
  }
  if(action?.type==='move'){
   if(!s.selected)return result(s,'先在桌上選一份樣本，再決定放到哪裡。','table');
   if(!Object.hasOwn(destinations,action.destination))return result(s,'這個去向尚未開放。');
   const from=s.placements[s.selected],to=action.destination;
   if(from===to)return result(s,`這份樣本已在「${destinations[to]}」，沒有新增數量。`,to);
   const a={sample:s.selected,from,to};
   return result({...s,placements:{...s.placements,[s.selected]:to},lastAction:a,revision:s.revision+1,journal:[...s.journal,{sample:s.selected,to,kind:'move'}].slice(-30)},`${samples[s.selected].name}已選「${destinations[to]}」。`,to);
  }
  if(action?.type==='undo'){
   const a=s.lastAction;if(!a)return result(s,'目前沒有可以取消的選擇。');
   return result({...s,placements:{...s.placements,[a.sample]:a.from},lastAction:null,revision:s.revision+1,journal:[...s.journal,{sample:a.sample,to:a.from,kind:'undo'}].slice(-30)},`已取消${samples[a.sample].name}的最近選擇，回到${a.from===null?'分揀桌':destinations[a.from]}。`,'table');
  }
  return result(s,'請選取樣本或去向。');
 }
 function summary(s){return Object.fromEntries([['table',Object.values(s.placements).filter(x=>x===null).length],...Object.keys(destinations).map(d=>[d,Object.values(s.placements).filter(x=>x===d).length])]);}
 const api={samples,destinations,empty,restore,apply,summary};if(typeof module!=='undefined')module.exports=api;else root.QingxiReturn=api;
})(typeof globalThis!=='undefined'?globalThis:this);
