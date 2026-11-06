/* Local fixtures, not an import from unmerged A/B work. B outcome aliases are provisional. */
(function(root){const fixtures=[
 {id:'no-clues',name:'尚無上游線索',observationIds:[],outcomeId:null},
 {id:'repair-pending',name:'發現破槽，尚未導水',observationIds:['cracked_sluice'],outcomeId:null},
 {id:'silt-cleared',name:'清淤後，部分供水',observationIds:['silt_buildup'],outcomeId:'clear_silt'},
 {id:'channel-restored',name:'舊槽修復，供水恢復',observationIds:['cracked_sluice','silt_buildup'],outcomeId:'restore_channel'},
 {id:'nursery-protected',name:'保護育幼區，村田部分供水',observationIds:['nursery_tracks'],outcomeId:'protect_nursery'},
 {id:'unknown-outcome',name:'收到尚未對照的工程結果',observationIds:['cracked_sluice'],outcomeId:'unmapped_fixture_result'}
 ];if(typeof module!=='undefined')module.exports=fixtures;else root.WaterReportFixtures=fixtures;})(typeof globalThis!=='undefined'?globalThis:this);
