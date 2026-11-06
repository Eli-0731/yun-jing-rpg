(function (root) {
  'use strict';
  const clues = Object.freeze({
    training: { title: '演武棚 · 舊劍痕', source: '演武棚外的木牌', x: 26, y: 28, image: 'Q02', text: '木牌上留下三道深淺不同的痕跡。守棚人說：「先看清腳下，再決定怎樣修行。凡骨也能從體修開始。」', options: ['記下身法的提示', '留意引氣呼吸'] },
    creek: { title: '溪畔 · 採藥記號', source: '溪邊的竹製標記', x: 76, y: 35, image: 'Q03', text: '三葉記號指向淺灘。採藥人留下話：「先辨葉脈，再看水勢。今天不採，也能把路記住。」', options: ['記下安全的淺灘', '先觀察草葉'] },
    inn: { title: '客舍 · 行路留言', source: '客舍外的留言板', x: 66, y: 76, image: 'Q04', text: '行路人寫道：「青溪沒有替你排好的第一天。往山間、往溪邊，或者在客舍歇一歇，都由你自己決定。」', options: ['記下遠行的方向', '留待歇腳時再讀'] }
  });
  function empty() { return { version: 1, choices: {}, player: { x: 44, y: 77 } }; }
  function restore(value) {
    const next = empty();
    if (!value || value.version !== 1) return next;
    for (const [key, clue] of Object.entries(clues)) {
      const choice = value.choices?.[key];
      if (Number.isInteger(choice) && choice >= 0 && choice < clue.options.length) next.choices[key] = choice;
    }
    if (Number.isFinite(value.player?.x) && Number.isFinite(value.player?.y)) {
      next.player = { x: Math.max(8, Math.min(92, value.player.x)), y: Math.max(12, Math.min(88, value.player.y)) };
    }
    return next;
  }
  function choose(state, id, option) {
    if (!clues[id] || !Number.isInteger(option) || option < 0 || option >= clues[id].options.length) return state;
    return { ...state, choices: { ...state.choices, [id]: option } };
  }
  function move(state, dx, dy) {
    if (!Number.isFinite(dx) || !Number.isFinite(dy)) return state;
    return { ...state, player: { x: Math.max(8, Math.min(92, state.player.x + dx)), y: Math.max(12, Math.min(88, state.player.y + dy)) } };
  }
  const api = { clues, empty, restore, choose, move };
  if (typeof module !== 'undefined') module.exports = api;
  else root.QingxiGuide = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
