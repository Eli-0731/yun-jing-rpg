/* 青溪見聞 C · rules for the local demo. Eli-0731.
   Pure functions, no DOM: the page and the tests both use this file.
   Local demo only — the server's discover-fortune action decides real items (see README). */
(function(root){
const RULES={glowRadius:14,inspectRadius:2.5,titleMax:10,passageMax:60};
const CONDITIONS={any:'任何時候',night:'只在夜裡',after_rain:'只在雨後'};
function conditionMet(s,env){
  const c=s.condition||'any';
  if(c==='any')return true;
  if(c==='night')return env.time==='night';
  if(c==='after_rain')return !!env.afterRain;
  return false;   // unknown conditions stay hidden rather than leaking
}
function distance(a,b){return Math.hypot(a.x-b.x,a.z-b.z);}
function newState(){return {found:[]};}   // ids in the order they were found
function isFound(state,id){return state.found.includes(id);}
/* a sighting glows once the player is within 14 m, in the same area, the condition holds and it is not yet found */
function visible(state,list,area,pos,env){
  return list.filter(s=>s.pos.area===area&&!isFound(state,s.id)&&conditionMet(s,env)&&distance(pos,s.pos)<=RULES.glowRadius)
    .map(s=>({...s,dist:distance(pos,s.pos)})).sort((a,b)=>a.dist-b.dist);
}
function inspectable(state,list,area,pos,env){
  const v=visible(state,list,area,pos,env)[0];return v&&v.dist<=RULES.inspectRadius?v:null;
}
/* discover: grants the card once; a repeat returns duplicate:true and leaves the state untouched */
function discover(state,list,id,area,pos,env){
  const s=list.find(x=>x.id===id);
  if(!s)return {state,ok:false,reason:'unknown'};
  if(isFound(state,id))return {state,ok:false,duplicate:true,reason:'already-found'};
  if(s.pos.area!==area||distance(pos,s.pos)>RULES.inspectRadius)return {state,ok:false,reason:'too-far'};
  if(!conditionMet(s,env))return {state,ok:false,reason:'condition'};
  return {state:{found:[...state.found,id]},ok:true,card:{id:s.id,title:s.title,passage:s.passage,item:s.item}};
}
function collection(state,list){return state.found.map(id=>list.find(s=>s.id===id)).filter(Boolean);}
function textProblems(s){
  const p=[];
  if([...s.title].length>RULES.titleMax)p.push(`${s.id}: 標題 ${[...s.title].length} 字，超過 ${RULES.titleMax}`);
  if([...s.passage].length>RULES.passageMax)p.push(`${s.id}: 內文 ${[...s.passage].length} 字，超過 ${RULES.passageMax}`);
  return p;
}
/* join sightings.json + positions.json into the list the page uses */
function merge(sightings,positions){
  const pos=Object.fromEntries(positions.map(p=>[p.id,p]));
  return sightings.map(s=>{const p=pos[s.id];return {...s,pos:{area:p.area,x:p.x,z:p.z}};});
}
function restore(raw,list){   // tolerate missing / stale storage
  try{const d=JSON.parse(raw);if(!d||!Array.isArray(d.found))return newState();
    const ids=new Set(list.map(s=>s.id));const seen=new Set();return {found:d.found.filter(id=>ids.has(id)&&!seen.has(id)&&seen.add(id))};}
  catch{return newState();}
}
const api={RULES,CONDITIONS,conditionMet,distance,newState,isFound,visible,inspectable,discover,collection,textProblems,merge,restore};
if(typeof module!=='undefined')module.exports=api;else root.Sightings=api;
})(typeof globalThis!=='undefined'?globalThis:this);
