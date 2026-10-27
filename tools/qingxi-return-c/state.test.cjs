const test=require('node:test'),assert=require('node:assert/strict'),R=require('./state.js');
const run=(s,a)=>R.apply(s,a).state;
test('repeated clicks cannot duplicate a sample; totals are always three',()=>{
 let s=run(R.empty(),{type:'select',sample:'herb'});s=run(s,{type:'move',destination:'save'});const revision=s.revision;
 for(let i=0;i<100;i++)s=run(s,{type:'move',destination:'save'});
 assert.equal(s.revision,revision);assert.equal(s.journal.length,1);assert.deepEqual(R.summary(s),{table:2,save:1,alchemy:0});
 for(const id of Object.keys(R.samples))for(const d of Object.keys(R.destinations)){s=run(s,{type:'select',sample:id});s=run(s,{type:'move',destination:d});assert.equal(Object.values(R.summary(s)).reduce((a,b)=>a+b),3);}
});
test('one-step undo restores previous location; cannot undo twice',()=>{
 let s=run(R.empty(),{type:'select',sample:'ore'});s=run(s,{type:'move',destination:'save'});s=run(s,{type:'move',destination:'alchemy'});s=run(s,{type:'undo'});
 assert.equal(s.placements.ore,'save');assert.equal(s.lastAction,null);assert.equal(run(s,{type:'undo'}),s);
 s=run(s,{type:'move',destination:'alchemy'});s=R.restore(JSON.parse(JSON.stringify(s)));s=run(s,{type:'undo'});assert.equal(s.placements.ore,'save');
});
test('undo first placement returns sample to table and journal records cancellation',()=>{
 let s=run(R.empty(),{type:'select',sample:'seed'});s=run(s,{type:'move',destination:'alchemy'});s=run(s,{type:'undo'});
 assert.equal(s.placements.seed,null);assert.equal(s.journal.at(-1).kind,'undo');assert.equal(R.summary(s).table,3);
});
test('invalid actions and corrupt saves cannot invent assets or destinations',()=>{
 const s=R.empty();assert.equal(run(s,{type:'move',destination:'save'}),s);assert.equal(run(s,{type:'select',sample:'currency'}),s);
 const next=R.restore({version:1,selected:'herb',placements:{herb:'mint-money',ore:'save',seed:100,extra:'save'},lastAction:{sample:'herb',to:'alchemy',from:null},journal:[{sample:'unknown',to:'save',kind:'move'}],revision:-99});
 assert.deepEqual(next.placements,{herb:null,ore:'save',seed:null});assert.equal(next.lastAction,null);assert.equal(next.revision,0);assert.deepEqual(next.journal,[]);
 assert.deepEqual(R.restore(null),s);assert.deepEqual(R.restore({version:99}),s);
});
