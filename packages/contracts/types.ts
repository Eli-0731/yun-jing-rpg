export type Talent = 'mortal' | 'ordinary' | 'gifted' | 'prodigy' | 'chosen';
export interface Birth {
  tier: Talent; label: string; roots: string[]; apertures: number;
  constitution: string; efficiency: number; version: string; createdAt: number;
}
export interface Stack { item: string; quantity: number; bound: boolean; potency: number }
export interface Plot { index: number; crop: string; plantedAt: number; readyAt: number; bound: boolean; plantingId?: string; mode?: string; harvestYield?: number; tended?: boolean }
export interface Estate { cistern: boolean; bound: boolean; modes: string[] }
export interface CraftJob { id: string; recipe: string; readyAt: number; bound: boolean; potency: number; claimed: boolean }
export interface Journey {
  version: 1; createdAt: number; selectionAt: number; assessedAt: number | null;
  manual: 'qi-primer'; housing: 'lodging' | 'cave';
}
export interface Player {
  id: string; name: string; realm: number; path: string; sect: string;
  body: number; qi: number; roots: string[]; apertures: number;
  inventory: Stack[]; plots: Plot[]; jobs: CraftJob[]; clues: string[];
  milestones: string[]; cooldowns: Record<string, number>; contribution: number;
  estate?: Estate;
  journey?: Journey;
}
export interface World {
  channel: number; required: number; waterQuality: number; sanctuary: boolean;
  history: { player: string; action: string; at: number }[];
}
export interface QuestProgress {
  id: string; title: string; description: string; optional: boolean; hint: string;
  status: 'locked' | 'active' | 'ready' | 'claimed'; blockedBy: string[];
  objectives: { label: string; current: number; target: number; complete: boolean }[];
  rewards: { item: string; quantity: number; bound: boolean }[];
}
export interface Journal {
  chapterId: string; title: string; introduction: string; completed: number; total: number;
  finished: boolean; nextQuestId: string | null; guidance: string; quests: QuestProgress[];
}
// Null means undisclosed, not "no spiritual root" / "zero apertures".
export type PublicPlayer = Omit<Player, 'roots' | 'apertures'> & { roots: string[] | null; apertures: number | null };
export interface Snapshot { player: PublicPlayer; birth: Birth | null; birthAssigned: boolean; world: World; serverTime: number; version: number; contentVersion: string; speed: number; journal: Journal }
export interface Action { kind: string; [key: string]: unknown }
export interface HuntDeath {
  deathId: string;
  roomId: string;
  spawnId: string;
  enemyId: string;
  occurredAt: number;
  participants: string[];
}
export interface HuntReward { playerId: string; items: { item: string; quantity: number }[] }
export interface HuntReceipt { deathId: string; roomId: string; spawnId: string; rewards: HuntReward[] }
