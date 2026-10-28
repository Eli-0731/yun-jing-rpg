const test=require('node:test'),assert=require('node:assert/strict'),R=require('./state.js'),fixtures=require('./fixtures.js'),responseData=require('./response-data.json');
for(const c of responseData.testCases)test('規則案例：'+c.name,()=>{
 let state=R.transition(R.initial(),{type:'load',input:c.input}).state;
 for(const text of c.actions){const [type,choice]=text.split(':');state=R.transition(state,type==='select'?{type:'choose',choice}:{type:'cancel'}).state;}
 assert.equal(R.view(state).key,c.expectedState);assert.equal(state.choice,c.expectedChoice);assert.equal(state.input.outcomeId,c.input.outcomeId);
 if(c.expectedEvents!==undefined)assert.equal(state.events.length,c.expectedEvents);
 assert.equal(Object.hasOwn(state,'inventory'),false);assert.equal(Object.hasOwn(state,'contribution'),false);
});
test('all 18 scenario-choice pairs preserve upstream and allow cancel without rewards',()=>{
 for(const fixture of fixtures)for(const choice of Object.keys(R.choices)){
  let s=R.transition(R.initial(),{type:'load',input:fixture}).state;const before=JSON.stringify(s.input);s=R.transition(s,{type:'choose',choice}).state;
  for(let n=0;n<50;n++)s=R.transition(s,{type:'choose',choice}).state;
  assert.equal(s.events.length,1);assert.equal(JSON.stringify(s.input),before);s=R.transition(s,{type:'cancel'}).state;assert.equal(s.choice,null);assert.equal(JSON.stringify(s.input),before);
 }
});
test('unknown clue ids are ignored; unknown outcomes never inherit completed visuals',()=>{
 const input=R.normalize({observationIds:['cracked_sluice','cracked_sluice','reward','nursery_tracks'],outcomeId:'new_outcome',completed:true,water:100});
 assert.deepEqual(input.observationIds,['cracked_sluice','nursery_tracks']);const s=R.transition(R.initial(),{type:'load',input}).state;
 assert.equal(R.view(s).key,'unknown');assert.equal(R.view(s).complete,false);assert.equal(R.view(s).image,'dry');
});
test('bad imports are inert and a versioned save restores valid local choice',()=>{
 let s=R.transition(R.initial(),{type:'choose',choice:'protect_nursery'}).state;
 for(const input of [null,{},[],{observationIds:[],outcomeId:15},{observationIds:'oops',outcomeId:null}])assert.equal(R.transition(s,{type:'load',input}).state,s);
 assert.equal(R.restore(JSON.parse(JSON.stringify(s))).choice,'protect_nursery');assert.deepEqual(R.restore({version:2}),R.initial());
});
test('responses cover all five known contexts and the animal nursery',()=>{
 for(const key of ['none','pending','partial','restored','protected'])for(const choice of Object.keys(R.choices)){const text=responseData.responses[key][choice];assert.equal(typeof text,'string');assert.ok(text.length>=15);assert.doesNotMatch(text,/小苗|排行榜|靈石獎勵|已發放/);}
});
test('prototype property names remain unknown outcomes',()=>{
 for(const id of ['__proto__','constructor','toString','hasOwnProperty']){const s=R.transition(R.initial(),{type:'load',input:{observationIds:[],outcomeId:id}}).state;assert.equal(R.view(s).key,'unknown');assert.equal(R.view(s).complete,false);}
});
