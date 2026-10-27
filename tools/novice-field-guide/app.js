/* Original UI and local-only interaction: Eli-0731 / Codex. No API calls. */
(() => {
  'use strict';
  const G = QingxiGuide, KEY = 'qingxi-c-field-guide-v1';
  let state = G.empty(), storageAvailable = true;
  const $ = id => document.getElementById(id);
  const status = text => { $('status').textContent = text; };
  try { state = G.restore(JSON.parse(localStorage.getItem(KEY))); } catch { storageAvailable = false; }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch { storageAvailable = false; }
    if (!storageAvailable) status('此瀏覽器無法保存；目前仍可探索，重新整理後紀錄可能不保留。');
  }
  function render() {
    $('player').style.left = state.player.x + '%'; $('player').style.top = state.player.y + '%';
    const count = Object.keys(state.choices).length;
    $('progress').textContent = `已發現 ${count} / 3 條線索 · 只保存在此瀏覽器`;
    $('entries').replaceChildren();
    for (const [id, option] of Object.entries(state.choices)) {
      const entry = document.createElement('article'); entry.className = 'entry';
      const h = document.createElement('h3'); h.textContent = G.clues[id].title;
      const p = document.createElement('p'); p.textContent = `${G.clues[id].source} → ${G.clues[id].options[option]}`;
      entry.append(h, p); $('entries').append(entry);
    }
    document.querySelectorAll('.map [data-place]').forEach(b => b.classList.toggle('visited', Object.hasOwn(state.choices, b.dataset.place)));
    $('lore').hidden = count !== 3;
  }
  function open(id) {
    const board = id === 'board', clue = G.clues[id];
    if (!board && !clue) return;
    const pos = board ? { x: 27, y: 76 } : clue;
    state = { ...state, player: { x: pos.x + 9, y: pos.y + 8 } }; save(); render();
    $('event-title').textContent = board ? '村口告示 · 三條可選的路' : clue.title;
    $('event-text').textContent = board ? '想練功，就往演武棚；想看看草木，就沿溪走；想聽行路人的話，就到客舍。沒有必做順序，也沒有正式獎勵。帶回任何一條線索，都能在這裡翻看。' : clue.text;
    $('event-image').src = `previews/${board ? 'Q01' : clue.image}-close.png`;
    $('options').replaceChildren();
    if (board) {
      const p = document.createElement('p');
      p.textContent = Object.keys(state.choices).length ? Object.entries(state.choices).map(([k,v]) => G.clues[k].title + '：' + G.clues[k].options[v]).join('；') : '目前還沒有紀錄。先選一條感興趣的路吧。';
      $('options').append(p);
    } else clue.options.forEach((text, i) => {
      const b = document.createElement('button'); b.textContent = text;
      b.addEventListener('click', () => { state = G.choose(state, id, i); save(); render(); $('event').close(); status(`手札已記下：${clue.title}，${text}。可繼續探索，或回村口看告示。`); });
      $('options').append(b);
    });
    $('event').showModal();
  }
  document.querySelectorAll('[data-place]').forEach(b => b.addEventListener('click', () => open(b.dataset.place)));
  function move(dx, dy) { state = G.move(state, dx, dy); save(); render(); }
  function interact() {
    const places = { ...G.clues, board: { x: 27, y: 76 } };
    const nearest = Object.entries(places).map(([id,p]) => [id, Math.hypot(p.x-state.player.x,p.y-state.player.y)]).sort((a,b)=>a[1]-b[1])[0];
    if (nearest[1] <= 20) open(nearest[0]); else status('再靠近一塊木牌，或直接點選地標走訪。');
  }
  document.querySelectorAll('[data-move]').forEach(b => b.addEventListener('click', () => move(...b.dataset.move.split(',').map(Number))));
  $('interact').addEventListener('click', interact);
  document.addEventListener('keydown', e => {
    if ($('event').open || /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
    const key = e.key.toLowerCase(), dirs = { arrowup:[0,-3],w:[0,-3],arrowdown:[0,3],s:[0,3],arrowleft:[-3,0],a:[-3,0],arrowright:[3,0],d:[3,0] };
    if (dirs[key]) { e.preventDefault(); move(...dirs[key]); }
    if (key === 'e') { e.preventDefault(); interact(); }
  });
  $('reset').addEventListener('click', () => { if (confirm('清除這台瀏覽器的三條探索紀錄？')) { state = G.empty(); save(); render(); status('手札已清空。這次也可以換一條路。'); } });
  render();
  if (!storageAvailable) status('無法讀取本機紀錄，已開始新的探索。');
  if ('serviceWorker' in navigator && location.protocol !== 'file:') navigator.serviceWorker.register('sw.js').catch(() => status('離線快取未啟用；目前仍可在線探索。'));
})();
