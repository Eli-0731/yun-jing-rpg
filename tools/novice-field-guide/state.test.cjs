const test=require('node:test'), assert=require('node:assert/strict');
const G=require('./state.js');
test('three clues work in every order; changing a choice never duplicates a clue',()=>{
  const permutations=[['inn','creek','training'],['inn','training','creek'],['creek','inn','training'],['creek','training','inn'],['training','inn','creek'],['training','creek','inn']];
  for(const order of permutations){let s=G.empty();for(const id of order)s=G.choose(s,id,0);assert.equal(Object.keys(s.choices).length,3);s=G.choose(s,order[0],1);for(let i=0;i<100;i++)s=G.choose(s,order[0],1);assert.equal(Object.keys(s.choices).length,3);assert.equal(s.choices[order[0]],1);}
});
test('only known clues and valid choices survive reload',()=>{
  const s=G.restore({version:1,choices:{training:1,creek:-1,inn:'0',reward:999},player:{x:10000,y:-1}});
  assert.deepEqual(s.choices,{training:1});assert.deepEqual(s.player,{x:92,y:12});
  assert.deepEqual(G.restore({version:99}),G.empty());
});
test('invalid actions are inert and movement stays in map bounds',()=>{
  const s=G.empty();assert.equal(G.choose(s,'reward',0),s);assert.equal(G.choose(s,'inn',10),s);assert.equal(G.move(s,NaN,0),s);
  assert.deepEqual(G.move(s,-1000,1000).player,{x:8,y:88});assert.deepEqual(s,G.empty());
});
