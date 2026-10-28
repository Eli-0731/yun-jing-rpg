// Local data adapter: PR #31 gathering-kit yields -> alchemy material definitions.
//
// Source of truth for the gathered items is PR #31 (z1nnz/yun-jing-rpg, commit e6202d7,
// tools/gathering-point-demo/main.js, NODES[].local). That package is NOT copied here; only the
// three node ids, item names and local yields are mirrored below so the alchemy demo can run on its
// own. PR #31 was merged into main as assets only (0f1e023): the gathering demo and its NODES are not
// on main, so e6202d7 (which is in main's history) stays the pinned reference. When the gathering kit is wired to the server, replace PR31_NODES with the server inventory
// and keep `toMaterial()` as the single mapping point.
//
// Element / nature / purity / stability are alchemy-side design values proposed by this package.
// `serverItem` is the proposed id in packages/content; null means the core team has not assigned one.

export const PR31_SOURCE = Object.freeze({ repo: 'z1nnz/yun-jing-rpg', pr: 31, commit: 'e6202d7', file: 'tools/gathering-point-demo/main.js' });

const PR31_NODES = Object.freeze([
  { id: 'qinglan_01', asset: 'QX_SpiritHerb_Qinglan', name: '青溪蘭', local: { item: '青溪蘭花莖', qty: 1 } },
  { id: 'chilu_01', asset: 'QX_SpiritHerb_Chilu', name: '赤露參', local: { item: '赤露參漿果', qty: 3 } },
  { id: 'yumai_01', asset: 'QX_EmbeddedOre_Yumai', name: '嵌地玉脈石', local: { item: '玉脈晶', qty: 2 } },
]);

const ALCHEMY = Object.freeze({
  qinglan_01: { id: 'qinglan-stem', element: '木', nature: '溫', purity: 72, stability: 64, serverItem: 'qingling-herb',
    note: '花莖纖維長，切段後藥性最完整；浸泡可穩住藥性。' },
  chilu_01: { id: 'chilu-berry', element: '火', nature: '溫', purity: 66, stability: 50, serverItem: null,
    note: '漿汁濃，研碎出汁最多但容易焦；浸泡較穩。' },
  yumai_01: { id: 'yumai-crystal', element: '金', nature: '寒', purity: 80, stability: 84, serverItem: null,
    note: '質硬，只能研成粉才會溶入藥液；性寒，能壓火氣。' },
});

export function toMaterial(node) {
  const a = ALCHEMY[node.id];
  if (!a) throw new Error(`no alchemy mapping for PR #31 node ${node.id}`);
  return Object.freeze({ ...a, name: node.local.item, plant: node.name, sourceNode: node.id, sourceAsset: node.asset, gatherYield: node.local.qty });
}

export const MATERIALS = Object.freeze(Object.fromEntries(PR31_NODES.map(n => { const m = toMaterial(n); return [m.id, m]; })));

// Deterministic per-batch variation (no randomness): a batch id always yields the same purity/stability.
function hash(text) {
  let h = 2166136261;
  for (const c of text) { h ^= c.codePointAt(0); h = Math.imul(h, 16777619) >>> 0; }
  return h;
}

export function makeBatch(materialId, batchId, qty, bound = false) {
  const m = MATERIALS[materialId];
  if (!m) throw new Error(`unknown material ${materialId}`);
  const h = hash(batchId);
  return { batchId, material: materialId, qty, bound, purity: m.purity + (h % 9) - 4, stability: m.stability + ((h >>> 8) % 7) - 3 };
}

// Demo starting bag: equivalent to two PR #31 gathering rounds (local yields 1 / 3 / 2, doubled).
export function demoBag() {
  return [
    makeBatch('qinglan-stem', 'pr31-qinglan_01-r1', 2),
    makeBatch('chilu-berry', 'pr31-chilu_01-r1', 6),
    makeBatch('yumai-crystal', 'pr31-yumai_01-r1', 2),
  ];
}
