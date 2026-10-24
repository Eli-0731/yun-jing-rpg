import chapter from '../../../packages/content/qingxi.json';
import { Birth, Journal, Player, QuestProgress } from '../../../packages/contracts/types';

export { chapter };
interface Objective { kind: string; keys?: string[]; target: number; label: string }
function progress(player: Player, birth: Birth | null, objective: Objective): number {
  switch (objective.kind) {
    case 'birth': return birth ? 1 : 0;
    case 'mentor': return chapter.mentors.filter(mentor => player.milestones.includes(`talked:${mentor.id}`)).length;
    case 'milestone': return (objective.keys ?? []).filter(key => player.milestones.includes(key)).length;
    case 'clues': return chapter.clues.filter(clue => player.clues.includes(clue.id)).length;
    case 'sect': return player.sect ? 1 : 0;
    case 'cultivation': return player.path === 'body' ? player.body : player.qi;
    case 'realm': return player.realm;
    default: throw new Error(`Unknown quest objective: ${objective.kind}`);
  }
}
export function buildJournal(player: Player, birth: Birth | null): Journal {
  const hidden=!!player.journey && player.journey.assessedAt===null;
  const quests: QuestProgress[] = chapter.quests.filter(quest => !quest.audience || (!hidden && quest.audience === birth?.tier)).map(quest => {
    const objectives = quest.objectives.map(objective => {
      const current = Math.min(objective.target, progress(player, birth, objective));
      return { label: player.journey && objective.kind==='birth'?'入世並領取煉氣訣':objective.label, current, target: objective.target, complete: current >= objective.target };
    });
    const blockedBy = quest.requires.filter(id => !player.milestones.includes(`quest:${id}`));
    const claimed = player.milestones.includes(`quest:${quest.id}`);
    return {
      id: quest.id, title: quest.title, description: quest.description, optional: quest.optional, hint: quest.hint,
      status: claimed ? 'claimed' : !birth || blockedBy.length ? 'locked' : objectives.every(x => x.complete) ? 'ready' : 'active',
      blockedBy, objectives, rewards: quest.rewards.map(reward => ({ ...reward, bound: true })),
    };
  });
  const required = quests.filter(quest => !quest.optional);
  const completed = required.filter(quest => quest.status === 'claimed').length;
  const next = quests.find(quest => quest.status === 'ready') ?? required.find(quest => quest.status === 'active');
  const guidance = hidden ? '先天已在創角時確定，滿十個現實日後到廣場測定。現在可練煉氣訣或基礎武技、採集與調查；靈田在入宗後取得。'
    : !birth ? '先測定先天天賦；同一修行身分只會分配一次。'
    : player.roots.length === 0 ? '目前沒有靈根，可先向沈岳學體修。後天開靈是可選方向，不是體修進境的門檻。'
    : player.sect ? `目前主修${player.path === 'body' ? '體魄' : '引氣'}；生產、調查與青溪工程可以同時準備。`
    : '你已能感應靈氣，可以選擇法修或體修。先聽兩位導師說明，再決定自己的方向。';
  return { chapterId: chapter.id, title: chapter.title, introduction: chapter.introduction, completed, total: required.length, finished: completed === required.length, nextQuestId: next?.id ?? null, guidance, quests };
}
