const test=require('node:test'),assert=require('node:assert/strict');
const S=require('./state.js');
const list=S.merge(require('./sightings.json').sightings,require('./positions.json').positions);
const fortunes=require('./fortunes-c.json').fortunes;
const day={time:'day',afterRain:false},night={time:'night',afterRain:false},rain={time:'day',afterRain:true};
const at=s=>({x:s.pos.x,z:s.pos.z});
const byId=id=>list.find(s=>s.id===id);

test('12 sightings: A2 ×5, A3 ×5, HOME ×2, unique ids, all positioned',()=>{
  assert.equal(list.length,12);assert.equal(new Set(list.map(s=>s.id)).size,12);
  const n=a=>list.filter(s=>s.pos.area===a).length;assert.deepEqual([n('A2'),n('A3'),n('HOME')],[5,5,2]);
  for(const s of list)assert.ok(Number.isFinite(s.pos.x)&&Number.isFinite(s.pos.z),s.id);
});
test('card text stays within 10 / 60 characters',()=>{
  for(const s of list)assert.deepEqual(S.textProblems(s),[],s.id);
  assert.deepEqual(S.textProblems({id:'x',title:'一二三四五六七八九十一',passage:'字'.repeat(61)}).length,2);
});
test('the same sighting cannot be taken twice',()=>{
  const s=byId('A2-F01');let st=S.newState();
  const first=S.discover(st,list,s.id,'A2',at(s),day);assert.ok(first.ok);st=first.state;
  const again=S.discover(st,list,s.id,'A2',at(s),day);
  assert.equal(again.ok,false);assert.equal(again.duplicate,true);assert.equal(again.state,st);
  assert.deepEqual(S.collection(again.state,list).map(x=>x.id),['A2-F01']);
  assert.equal(S.visible(st,list,'A2',at(s),day).some(x=>x.id==='A2-F01'),false);
});
test('night-only sighting appears only at night',()=>{
  const s=byId('A3-F01');assert.equal(s.condition,'night');
  assert.equal(S.visible(S.newState(),list,'A3',at(s),day).some(x=>x.id===s.id),false);
  assert.equal(S.discover(S.newState(),list,s.id,'A3',at(s),day).reason,'condition');
  assert.equal(S.visible(S.newState(),list,'A3',at(s),night).some(x=>x.id===s.id),true);
  assert.ok(S.discover(S.newState(),list,s.id,'A3',at(s),night).ok);
});
test('after-rain sighting appears only after rain',()=>{
  const s=byId('A3-F04');assert.equal(s.condition,'after_rain');
  assert.equal(S.visible(S.newState(),list,'A3',at(s),night).some(x=>x.id===s.id),false);
  assert.ok(S.discover(S.newState(),list,s.id,'A3',at(s),rain).ok);
});
test('at most 3 conditional sightings',()=>{assert.ok(list.filter(s=>s.condition!=='any').length<=3);});
test('glow from 14 m, inspect from 2.5 m, other areas never show',()=>{
  const s=byId('A2-F03');
  assert.ok(S.visible(S.newState(),list,'A2',{x:s.pos.x+13.9,z:s.pos.z},day).some(x=>x.id===s.id));
  assert.equal(S.visible(S.newState(),list,'A2',{x:s.pos.x+14.1,z:s.pos.z},day).some(x=>x.id===s.id),false);
  assert.equal(S.inspectable(S.newState(),list,'A2',{x:s.pos.x+3,z:s.pos.z},day),null);
  assert.equal(S.discover(S.newState(),list,s.id,'A2',{x:s.pos.x+3,z:s.pos.z},day).reason,'too-far');
  assert.equal(S.inspectable(S.newState(),list,'A2',{x:s.pos.x+2,z:s.pos.z},day).id,s.id);
  assert.equal(S.visible(S.newState(),list,'A3',at(s),day).some(x=>x.id===s.id),false);
});
test('collection keeps the order things were found',()=>{
  let st=S.newState();
  for(const id of ['A3-F02','A2-F05','HOME-F01']){const s=byId(id);st=S.discover(st,list,id,s.pos.area,at(s),day).state;}
  assert.deepEqual(S.collection(st,list).map(s=>s.id),['A3-F02','A2-F05','HOME-F01']);
});
test('stored progress is cleaned: unknown ids and repeats dropped, bad JSON resets',()=>{
  assert.deepEqual(S.restore('{"found":["A2-F01","nope","A2-F01","A3-F05"]}',list).found,['A2-F01','A3-F05']);
  assert.deepEqual(S.restore('not json',list).found,[]);
});
test('fortunes data matches the sightings and uses lower-case item ids',()=>{
  assert.deepEqual(fortunes.map(f=>f.id),list.map(s=>s.id));
  for(const f of fortunes){assert.match(f.item,/^[a-z0-9]+(-[a-z0-9]+)*$/,f.id);assert.equal(f.title,byId(f.id).title);}
});
test('HOME positions lie inside the house (7 × 5 m) or the backyard (12 × 10 m)',()=>{
  for(const s of list.filter(s=>s.pos.area==='HOME')){
    const inHouse=Math.abs(s.pos.x)<=3.5&&s.pos.z>=-2.5&&s.pos.z<=2.5,inYard=Math.abs(s.pos.x)<=6&&s.pos.z>=2.5&&s.pos.z<=12.5;
    assert.ok(inHouse||inYard,s.id);
  }
});
