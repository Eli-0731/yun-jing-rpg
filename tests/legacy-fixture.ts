import { randomUUID } from 'node:crypto';
import { Game } from '../services/api/src/game';
import { Player } from '../packages/contracts/types';

// A genuine pre-v0.4 row: regression tests must keep covering existing saves.
// This helper is never imported by runtime code and exposes no HTTP shortcut.
export async function legacyPlayer(game:Game,subject:string,name:string) {
  const id=randomUUID();
  const player:Player={id,name,realm:0,path:'body',sect:'',body:0,qi:0,roots:[],apertures:0,
    inventory:[{item:'qingling-seed',quantity:3,bound:false,potency:100},{item:'lotus-seed',quantity:2,bound:false,potency:100},{item:'spirit-stone',quantity:10,bound:false,potency:100}],
    plots:[],jobs:[],clues:[],milestones:[],cooldowns:{},contribution:0};
  await game.db.query('INSERT INTO players(id,subject,state) VALUES($1,$2,$3)',[id,subject,JSON.stringify(player)]);
  return id;
}
