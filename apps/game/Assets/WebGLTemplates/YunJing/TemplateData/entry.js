/* YunJing entry layer (Claude Code), on top of Codex's shell.js:
 * - lore cards that turn every 8 s while loading (tap for the next one);
 * - a mist veil the player can brush away with a finger or the mouse, slowly closing again;
 * - an ink bloom from the jade dot into the game when entering.
 * Everything is optional: if a feature is missing the plain shell still works. */
(() => {
  'use strict';
  const shell = document.getElementById('yj-shell');
  const content = shell && shell.querySelector('.yj-content');
  if (!shell || !content) return;
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------------------------------------------------------------- lore cards
  const cards = [
    ['青溪村', '村中古樹據說比村子還老，樹下的石台被坐得發亮。'],
    ['新手提示', '靈根要到第十日才會顯現。在那之前，凡骨也能練武、採藥、煉丹。'],
    ['古林', '溪水從北邊的古林流來，最近卻越來越淺，沒人知道上游出了什麼事。'],
    ['新手提示', '靠近發光的東西按 F。很多機緣不會標在地圖上。'],
    ['公共演武區', '氣勁木樁吸氣時按住、呼氣時放開；身法木樁看清木臂往哪邊擺。'],
    ['垂直山城', '抬頭看北方的石峰。第十日，你要爬上去測出自己的資質。'],
    ['坊市', '藥攤收新鮮的青心草。曬乾了，藥性就變了。'],
    ['新手提示', '離線的時候，時間一樣在走。回來看看田裡長了什麼。'],
    ['裂靈湖', '傳說湖底有一道會發光的裂縫，每隔七日，裂縫會開一次。'],
    ['借住處', '客棧主人留了一張床給你。累了就回來睡，醒來氣血會滿。'],
  ];
  const card = document.createElement('aside');
  card.className = 'yj-lore';
  card.setAttribute('aria-live', 'polite');
  card.innerHTML = '<b></b><span></span>';
  content.appendChild(card);
  let index = Math.floor(Math.random() * cards.length), timer = 0;
  const show = () => {
    const [title, text] = cards[index % cards.length];
    card.classList.remove('yj-lore-in');
    void card.offsetWidth;
    card.firstChild.textContent = title; card.lastChild.textContent = text;
    card.classList.add('yj-lore-in');
    index++;
  };
  const cycle = () => { clearInterval(timer); show(); timer = setInterval(show, 8000); };
  card.addEventListener('click', cycle);
  cycle();
  const enter = document.getElementById('yj-enter');
  // Cards stop when the game is ready, so the call to enter is the only thing that moves.
  new MutationObserver(() => { if (!enter.hidden) { clearInterval(timer); card.classList.add('yj-lore-done'); } })
    .observe(enter, { attributes: true, attributeFilter: ['hidden'] });

  // ---------------------------------------------------------------- mist veil, brushed away by the player
  const veil = document.createElement('canvas');
  veil.className = 'yj-veil';
  shell.insertBefore(veil, content);
  const g = veil.getContext('2d');
  let w = 0, h = 0, last = 0;
  const fit = () => {
    const scale = Math.min(devicePixelRatio || 1, 1.5);
    w = veil.width = Math.round(innerWidth * scale / 2); h = veil.height = Math.round(innerHeight * scale / 2);
    g.fillStyle = 'rgba(238,242,242,1)'; g.fillRect(0, 0, w, h);
  };
  fit(); addEventListener('resize', fit);
  const brush = (x, y) => {
    const r = Math.max(w, h) * .09, px = x / innerWidth * w, py = y / innerHeight * h;
    const grad = g.createRadialGradient(px, py, 0, px, py, r);
    grad.addColorStop(0, 'rgba(0,0,0,.55)'); grad.addColorStop(1, 'rgba(0,0,0,0)');
    g.globalCompositeOperation = 'destination-out'; g.fillStyle = grad; g.fillRect(px - r, py - r, r * 2, r * 2);
    g.globalCompositeOperation = 'source-over';
  };
  shell.addEventListener('pointermove', e => { if (e.pointerType !== 'mouse' || e.buttons || !matchMedia('(pointer: coarse)').matches) brush(e.clientX, e.clientY); });
  shell.addEventListener('pointerdown', e => brush(e.clientX, e.clientY));
  // The veil slowly closes again (about 3 s), so the brushed path fades like mist settling.
  const settle = t => {
    if (!shell.classList.contains('yj-vanish')) {
      if (t - last > 120) { g.fillStyle = 'rgba(238,242,242,.06)'; g.fillRect(0, 0, w, h); last = t; }
      requestAnimationFrame(settle);
    }
  };
  if (!calm) requestAnimationFrame(settle);

  // ---------------------------------------------------------------- ink bloom into the game
  const bloom = document.createElement('div');
  bloom.className = 'yj-bloom';
  document.body.appendChild(bloom);
  new MutationObserver(() => {
    if (!shell.classList.contains('yj-vanish') || bloom.classList.contains('yj-bloom-run')) return;
    const dot = enter.getBoundingClientRect();
    bloom.style.setProperty('--x', `${dot.left + 18}px`); bloom.style.setProperty('--y', `${dot.top + dot.height / 2}px`);
    bloom.classList.add('yj-bloom-run');
    setTimeout(() => bloom.remove(), 1400);
  }).observe(shell, { attributes: true, attributeFilter: ['class'] });
})();
