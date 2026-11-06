(function(root){
 'use strict';
 const observations=Object.freeze({cracked_sluice:'舊槽裂痕',silt_buildup:'溪底淤積',nursery_tracks:'育幼區足跡'});
 const choices=Object.freeze({tell_shortage:'先告知缺水',inspect_crack:'請工匠看破槽',protect_nursery:'先保護育幼區'});
 const outcomes=Object.freeze({clear_silt:'partial',restore_channel:'restored',protect_nursery:'protected'});
 const visualStates=Object.freeze({none:{name:'缺水原因尚待確認',image:'dry',board:'缺水',bucket:'接近空桶',flag:'待協調',field:'偏乾',complete:false},pending:{name:'已有線索，導水尚未完成',image:'dry',board:'缺水',bucket:'接近空桶',flag:'工程進行中',field:'偏乾',complete:false},partial:{name:'部分供水恢復',image:'partial',board:'部分恢復',bucket:'半桶水',flag:'仍需後續工程',field:'部分回潤',complete:false},restored:{name:'收到供水恢復的本機結果',image:'restored',board:'供水恢復',bucket:'水位提高',flag:'工程成果展示',field:'回潤',complete:true},protected:{name:'育幼區保留水流，村田部分供水',image:'partial',board:'支流保留',bucket:'半桶水',flag:'保護方案展示',field:'村田部分回潤',complete:false},unknown:{name:'尚無可確認的工程結果',image:'dry',board:'待核對',bucket:'水量待確認',flag:'結果待核對',field:'待確認',complete:false}});
 function normalize(input){
  if(!input||typeof input!=='object'||Array.isArray(input))throw Error('請提供含 observationIds 與 outcomeId 的資料。');
  if(!Array.isArray(input.observationIds)||input.observationIds.length>100)throw Error('observationIds 必須是最多 100 筆的陣列。');
  if(input.outcomeId!==null&&(typeof input.outcomeId!=='string'||input.outcomeId.length>100))throw Error('outcomeId 必須是字串或 null。');
  const known=[...new Set(input.observationIds.filter(x=>typeof x==='string'&&Object.hasOwn(observations,x)))].sort();
  return {observationIds:known,outcomeId:input.outcomeId};
 }
 function classify(input){return input.outcomeId===null?(input.observationIds.length?'pending':'none'):(Object.hasOwn(outcomes,input.outcomeId)?outcomes[input.outcomeId]:'unknown');}
 const initial=()=>({version:1,input:{observationIds:[],outcomeId:null},choice:null,events:[],revision:0});
 function restore(raw){
  const s=initial();if(!raw||raw.version!==1)return s;
  try{s.input=normalize(raw.input);}catch{return s;}
  if(Object.hasOwn(choices,raw.choice))s.choice=raw.choice;
  if(Number.isSafeInteger(raw.revision)&&raw.revision>=0)s.revision=raw.revision;
  if(Array.isArray(raw.events))s.events=raw.events.filter(e=>e&&['choose','cancel'].includes(e.type)&&(e.choice===null||Object.hasOwn(choices,e.choice))).slice(-20).map(e=>({type:e.type,choice:e.choice}));
  return s;
 }
 function transition(state,action){
  if(action?.type==='load'){
   try{const input=normalize(action.input);return {state:{...initial(),input,revision:state.revision+1},message:'已載入本機線索與工程結果範例，請自由選擇回報方向。'};}catch(e){return {state,message:e.message};}
  }
  if(action?.type==='choose'){
   if(!Object.hasOwn(choices,action.choice))return {state,message:'請選擇畫面上的三種回報之一。'};
   if(state.choice===action.choice)return {state,message:'這個決定已記下，沒有新增物品、貢獻或重複紀錄。'};
   return {state:{...state,choice:action.choice,revision:state.revision+1,events:[...state.events,{type:'choose',choice:action.choice}].slice(-20)},message:'手札已改為「'+choices[action.choice]+'」。工程結果依收到的範例顯示。'};
  }
  if(action?.type==='cancel'){
   if(state.choice===null)return {state,message:'目前尚未選擇，可以先看看告示或水桶。'};
   return {state:{...state,choice:null,revision:state.revision+1,events:[...state.events,{type:'cancel',choice:null}].slice(-20)},message:'已取消這次回報選擇；線索與工程結果保持原樣。'};
  }
  return {state,message:'可以查看告示，或自由選擇一個回報方向。'};
 }
 function view(state){const key=classify(state.input);return {key,...visualStates[key],choice:state.choice,observationLabels:state.input.observationIds.map(x=>observations[x]),upstreamOutcomeId:state.input.outcomeId};}
 const api={observations,choices,visualStates,normalize,classify,initial,restore,transition,view};if(typeof module!=='undefined')module.exports=api;else root.WaterReportState=api;
})(typeof globalThis!=='undefined'?globalThis:this);
