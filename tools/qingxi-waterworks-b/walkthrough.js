// Scripted player-view recording (?walk): fixed time step, every frame composited with the side panel and posted to
// serve.mjs (/__frame). Encode afterwards with scripts/encode-walkthrough.mjs.
// Inputs go through the real UI: panel buttons are clicked, keys are dispatched as keydown events, slots are picked
// by projecting their centre to the screen (a cursor ring is drawn where the click lands).
//   ?walk          full run: wrong tee -> undo -> direct route (wrong bend fixed) -> wrong direction refused ->
//                  restore_channel complete, complete pressed again -> bypass + protect_nursery -> desilt + clear_silt
//                  -> direct route again after desilting
//   ?walk=none&obs=none   no clues: try the direct route, preview lists unknown risks, result reveals them
//   ?walk=shots   still player-camera images (frames f09000+) for the previews folder, labelled with variant ids
const FPS = 12, DT = 1 / FPS;

export async function runWalkthrough(ctx) {
  const { tick, canvas, camera, b2t } = ctx;
  const out = document.createElement('canvas'); out.width = 1280; out.height = 720;
  const g = out.getContext('2d'); let n = 0;
  let cursor = null, cursorT = 0, caption = '', keyCap = '', keyT = 0;

  // panel painter (same approach as tools/qingxi-alchemy-b/walkthrough.js): element boxes and text runs at their
  // laid-out positions, so the recording shows exactly what the panel shows
  const opaque = c => c && c !== 'transparent' && !/rgba\(.*,\s*0\)$/.test(c);
  function box(el, clip) {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (cs.display === 'none' || cs.visibility === 'hidden' || r.bottom < clip.top || r.top > clip.bottom) return;
    if (el.tagName === 'SELECT') { g.fillStyle = '#fff'; g.fillRect(r.left, r.top, r.width, r.height); g.fillStyle = cs.color; g.font = `${cs.fontSize} ${cs.fontFamily}`; g.textBaseline = 'middle'; g.fillText(el.options[el.selectedIndex].text + ' ▾', r.left + 6, r.top + r.height / 2); return; }
    g.globalAlpha = +cs.opacity;
    const rad = Math.min(parseFloat(cs.borderTopLeftRadius) || 0, r.height / 2, r.width / 2);
    if (opaque(cs.backgroundColor)) { g.fillStyle = cs.backgroundColor; g.beginPath(); g.roundRect(r.left, r.top, r.width, r.height, rad); g.fill(); }
    if (parseFloat(cs.borderTopWidth) > 0 && opaque(cs.borderTopColor) && (el.tagName === 'BUTTON' || el.classList.contains('tile'))) {
      g.strokeStyle = cs.borderTopColor; g.lineWidth = 1; g.beginPath(); g.roundRect(r.left + .5, r.top + .5, r.width - 1, r.height - 1, rad); g.stroke();
    }
    for (const c of el.childNodes) {
      if (c.nodeType === 1) box(c, clip);
      else if (c.nodeType === 3 && c.textContent.trim()) text(c, cs, clip);
    }
    g.globalAlpha = 1;
  }
  function text(node, cs, clip) {
    g.fillStyle = cs.color; g.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`; g.textBaseline = 'middle';
    const s = node.textContent, rg = document.createRange(); let line = '', top = null, x0 = 0, mid = 0;
    const flush = () => { if (line.trim() && mid > clip.top && mid < clip.bottom) g.fillText(line, x0, mid); line = ''; };
    for (let i = 0; i < s.length; i++) {
      rg.setStart(node, i); rg.setEnd(node, i + 1);
      const r = rg.getClientRects()[0];
      if (!r || !r.width) continue;
      if (/\s/.test(s[i]) && (top === null || Math.abs(r.top - top) > r.height / 2)) continue;
      if (top === null || Math.abs(r.top - top) > r.height / 2) { flush(); top = r.top; x0 = r.left; mid = r.top + r.height / 2; }
      line += s[i];
    }
    flush();
  }
  function panel(id) {
    const el = document.getElementById(id);
    if (!el || el.hidden) return;
    const clip = el.getBoundingClientRect(), cs = getComputedStyle(el);
    g.save(); g.scale(out.width / innerWidth, out.height / innerHeight);
    g.shadowColor = 'rgba(0,0,0,.25)'; g.shadowBlur = 14; g.shadowOffsetY = 3; g.fillStyle = cs.backgroundColor;
    g.beginPath(); g.roundRect(clip.left, clip.top, clip.width, clip.height, parseFloat(cs.borderTopLeftRadius) || 0); g.fill();
    g.shadowColor = 'transparent';
    g.beginPath(); g.rect(clip.left, clip.top, clip.width, clip.height); g.clip();
    for (const c of el.childNodes) {
      if (c.nodeType === 1) box(c, clip);
      else if (c.nodeType === 3 && c.textContent.trim()) text(c, cs, clip);
    }
    g.restore();
  }
  async function frame(name = null) {
    tick(DT);
    const k = out.width / innerWidth, r = canvas.getBoundingClientRect();
    g.fillStyle = '#2b302c'; g.fillRect(0, 0, out.width, out.height);
    g.drawImage(canvas, r.left * k, r.top * k, r.width * k, r.height * k);
    ['side', 'mode', 'help', 'card', 'toast'].forEach(panel);
    g.save(); g.scale(k, k);
    if (cursor && cursorT > 0) {   // click ring
      const a = Math.min(1, cursorT / 0.4); g.strokeStyle = `rgba(255,210,74,${a})`; g.lineWidth = 3;
      g.beginPath(); g.arc(cursor[0], cursor[1], 14 + (1 - a) * 10, 0, Math.PI * 2); g.stroke();
      g.fillStyle = `rgba(255,210,74,${a * 0.5})`; g.beginPath(); g.arc(cursor[0], cursor[1], 6, 0, Math.PI * 2); g.fill();
      cursorT -= DT;
    }
    if (keyCap && keyT > 0) {   // key cap
      g.font = '700 18px "Microsoft JhengHei",sans-serif'; const w = g.measureText(keyCap).width + 28;
      g.fillStyle = 'rgba(30,30,30,.8)'; g.beginPath(); g.roundRect(r.left + 14, 52, w, 34, 8); g.fill();
      g.fillStyle = '#ffd24a'; g.textBaseline = 'middle'; g.fillText(keyCap, r.left + 28, 70); keyT -= DT;
    }
    if (caption) {
      g.font = '700 19px "Microsoft JhengHei",sans-serif'; const w = Math.min(r.width - 30, g.measureText(caption).width + 32);
      g.fillStyle = 'rgba(20,24,22,.78)'; g.beginPath(); g.roundRect(r.left + (r.width - w) / 2, r.bottom - 92, w, 38, 10); g.fill();
      g.fillStyle = '#fff'; g.textBaseline = 'middle'; g.textAlign = 'center'; g.fillText(caption, r.left + r.width / 2, r.bottom - 73); g.textAlign = 'left';
    }
    g.restore();
    g.fillStyle = 'rgba(0,0,0,.55)'; g.fillRect(8, out.height - 30, 70, 24); g.fillStyle = '#fff';
    g.font = '15px monospace'; g.textBaseline = 'alphabetic'; g.fillText(`${(n / FPS).toFixed(1)}s`, 14, out.height - 13);
    if (name !== null) { await fetch(`/__frame?n=${name}`, { method: 'POST', body: out.toDataURL('image/jpeg', 0.92) }); return; }
    await fetch(`/__frame?n=${n++}`, { method: 'POST', body: out.toDataURL('image/jpeg', 0.9) });
  }
  const hold = async s => { for (let i = 0; i < Math.round(s * FPS); i++) await frame(); };
  const settle = () => new Promise(r => setTimeout(r, 30));
  const side = document.getElementById('side');
  function show(sel) {   // scroll the side panel so this element is visible
    const el = document.querySelector(sel); if (!el) return;
    const r = el.getBoundingClientRect(), p = side.getBoundingClientRect();
    if (r.top < p.top + 4 || r.bottom > p.bottom - 4) side.scrollTop += r.top - p.top - 8;
  }
  async function click(sel, s = 0.7) {
    const el = document.querySelector(sel);
    if (!el) { console.warn('walkthrough: missing', sel); return; }
    el.scrollIntoView({ block: 'nearest' });
    const r = el.getBoundingClientRect(); cursor = [r.left + r.width / 2, r.top + r.height / 2]; cursorT = 0.6;
    el.click(); await settle(); await hold(s);
  }
  async function slot(id, s = 0.5) {
    const sl = ctx.S && window.demo.board.slots.find(x => x.id === id);
    const p = b2t(sl.pos[0] + sl.dir[0] * 0.45, sl.pos[1] + sl.dir[1] * 0.45, 0.3).project(camera), r = canvas.getBoundingClientRect();
    cursor = [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; cursorT = 0.6;
    await window.demo.act('select', { slot: id }); await hold(s);
  }
  async function key(k, label, s = 0.7, opts = {}) {
    keyCap = `按鍵 ${label}`; keyT = 1.2;
    dispatchEvent(new KeyboardEvent('keydown', { key: k, ...opts })); await settle(); await hold(s);
  }
  const say = t => { caption = t; };

  await hold(1.0);
  if (new URLSearchParams(location.search).get('walk') === 'shots') {
    const d = window.demo, { controls } = ctx;
    const build = async (steps, choice) => { await d.act('clear'); for (const [t, sl, v] of steps) await d.act(t === 'gate' ? 'gate' : t, t === 'gate' ? { slot: sl, open: v } : { slot: sl, piece: v }); if (choice) await d.act('choose', { choice }); };
    const aim = (pos, at) => { camera.position.copy(b2t(...pos)); controls.target.copy(b2t(...at)); controls.update(); };
    let i = 9000;
    const snap = async (cap, settleS = 1.5) => { say(cap); for (let k = 0; k < Math.round(settleS * FPS); k++) tick(DT); await frame(i++); };
    const ex = d.board.examples;
    await build(ex.restore_channel.steps, 'restore_channel'); await d.act('select', { slot: 'P5' });
    aim([1.8, -4.4, 11.6], [-0.5, 4.0, 0]); await snap('A 直通村田：P1 舊槽 → P2 B05 → P3 B02 → P4 舊槽＋B07 → P5／P6 B02', 3);
    aim([-1.55, 2.75, 1.1], [-0.3, 3.62, 0.12]); await snap('近看：P3 B02 接 P4 舊槽 B02-V02、西牆 B07 補石；接縫無縫無疊');
    await build(ex.protect_nursery.steps, 'protect_nursery'); await d.act('select', { slot: 'L4' });
    aim([1.8, -4.4, 11.6], [-0.5, 4.0, 0]); await snap('B 繞過育幼區：B03-V04 → B02 → B03 → B02-V03 → B05 → B03-V02 → B02 → B03-V03', 3);
    aim([0.9, -0.6, 3.0], [-1.4, 2.0, 0.2]); await snap('近看：P2 B03-V04 左彎接 L1 B02、L2 B03 右彎轉北');
    aim([1.2, 3.6, 3.2], [-1.2, 5.6, 0.2]); await snap('近看：L5 B03-V02 寬弧 → L6 B02 → L7 B03-V03 斜角彎接村田進水口');
    await build(ex.clear_silt.steps, 'clear_silt'); await d.act('select', { slot: 'R1' });
    aim([1.8, -4.4, 11.6], [-0.5, 4.0, 0]); await snap('C 先清淤：P2 B04-V02 分流，西側 L1 B02 → L2 B02-V05 進回流溝，東側 R1 B05 關閘', 3);
    aim([1.8, -0.4, 2.9], [-0.6, 1.8, 0.2]); await snap('近看：B04-V02 圓缽三通兩側接口對準 L1 與 R1');
    await build([['place', 'P2', 'B04'], ['place', 'L1', 'B02'], ['place', 'L2', 'B02-V05'], ['place', 'R1', 'B05']], null); await d.act('select', { slot: 'P2' });
    aim([1.8, -0.4, 2.9], [-0.4, 1.8, 0.2]); await snap('錯接：P2 放 B04（窄三通），out_left／out_right 各差 25 cm，水漫出', 2);
    await d.act('clear'); await d.act('select', { slot: 'P2' });
    aim([1.8, -4.4, 11.6], [-0.5, 4.0, 0]); await snap('起始：只有 B01 取水基座與舊槽 P1、P4；白框是可放段件的槽位', 2);
    document.title = 'WALK_DONE shots'; console.log(document.title); return;
  }
  if (new URLSearchParams(location.search).get('walk') === 'none') {
    say('沒有上游線索也能試：畫面標出未知風險');
    await slot('P2'); await click('[data-piece="B05"]', 0.4);
    for (const id of ['P3', 'P5', 'P6']) { await slot(id, 0.3); await click('[data-piece="B02"]', 0.3); }
    await slot('P2', 0.2); await key('g', 'G 開閘', 1.0); await key('w', 'W 修回舊渠', 0.6);
    show('.iss.unk'); await hold(3.0);
    say('完工後才發現：淤積、破槽漏水、育幼區足跡'); await key('Enter', 'Enter 完工', 4.5);
    document.title = `WALK_DONE ${n} frames ${(n / FPS).toFixed(1)}s`; console.log(document.title); return;
  }

  // ---- 1. wrong tee: both outlets 25 cm short, named and explained; undo
  say('點槽位 P2，放三通 B04：兩個出水口都差 25 cm');
  await slot('P2'); await click('[data-piece="B04"]', 0.3); show('#status .iss'); await hold(3.2);
  say('Ctrl+Z 撤回'); await key('z', 'Ctrl+Z 撤回', 1.0, { ctrlKey: true });
  // ---- 2. direct route, with a wrong bend fixed on the way
  say('直通村田：P2 放閘板 B05'); show('#slot'); await click('[data-piece="B05"]', 0.6);
  say('方向鍵到 P3，按 5 放彎槽 B03：出水口朝東落空'); await key('ArrowUp', '↑', 0.3); await key('5', '5', 0.3); show('#status .iss'); await hold(2.6);
  say('Ctrl+Z 撤回，改按 1 放直槽 B02'); await key('z', 'Ctrl+Z', 0.4, { ctrlKey: true }); show('#slot'); await key('1', '1', 0.6);
  say('P4 是舊槽：按 1 用石鞍 B07 補裂縫'); await key('ArrowUp', '↑', 0.4); await key('1', '1 補石', 1.0);
  say('P5、P6 接直槽到村田'); await key('ArrowUp', '↑', 0.2); await key('1', '1', 0.3); await key('ArrowUp', '↑', 0.2); await key('1', '1', 0.6);
  say('回到 P2 按 G 開閘：水一路流到村田'); await slot('P2', 0.2); await key('g', 'G 開閘', 3.0);
  say('選「保護育幼區」：流水離育幼區只有 50 cm，不能完工'); show('#dir'); await key('e', 'E 保護育幼區', 0.4); await key('Enter', 'Enter 完工', 2.8);
  say('改選「修回舊渠」，完工'); await key('w', 'W 修回舊渠', 0.6); await key('Enter', 'Enter 完工', 4.5);
  say('再按一次完工：同一請求回傳原收據，材料不再扣'); await click('#card [data-act="complete"]', 3.0);
  await click('#card [data-act="closecard"]', 0.5);
  // ---- 3. bypass route + protect_nursery
  say('清空重排：改走西側繞過育幼區'); await click('[data-act="clear"]', 0.6);
  const bypass = [['P2', 'B03-V04'], ['L1', 'B02'], ['L2', 'B03'], ['L3', 'B02-V03'], ['L4', 'B05'], ['L5', 'B03-V02'], ['L6', 'B02'], ['L7', 'B03-V03']];
  for (const [s, p] of bypass) { await slot(s, 0.2); show('#slot'); await click(`[data-piece="${p}"]`, 0.35); }
  say('L4 閘板按 G 開閘，選「保護育幼區」完工'); await slot('L4', 0.2); await key('g', 'G 開閘', 2.2); await key('e', 'E 保護育幼區', 0.6); await key('Enter', 'Enter 完工', 5.5);
  await click('#card [data-act="closecard"]', 0.4);
  // ---- 4. desilt with a temporary diversion
  say('先清淤：P2 放圓缽三通，西側導進回流溝，東側閘板關著');
  await click('[data-act="clear"]', 0.4);
  for (const [s, p] of [['P2', 'B04-V02'], ['L1', 'B02'], ['L2', 'B02-V05'], ['R1', 'B05']]) { await slot(s, 0.2); show('#slot'); await click(`[data-piece="${p}"]`, 0.4); }
  await hold(1.5); await key('q', 'Q 先清淤', 0.6); await key('Enter', 'Enter 完工', 4.5);
  await click('#card [data-act="closecard"]', 0.4);
  // ---- 5. direct route again after desilting: the field gets most of the water
  say('清淤之後再走直通路線：村田進水大幅提高');
  await click('[data-act="clear"]', 0.3);
  for (const [s, p] of [['P2', 'B05'], ['P3', 'B02'], ['P5', 'B02'], ['P6', 'B02']]) { await slot(s, 0.15); await click(`[data-piece="${p}"]`, 0.25); }
  await slot('P4', 0.15); await click('[data-piece="B07"]', 0.3);
  await slot('P2', 0.15); await key('g', 'G 開閘', 2.0); await key('w', 'W 修回舊渠', 0.4); await key('Enter', 'Enter 完工', 5.0);
  say(''); await hold(0.5);
  document.title = `WALK_DONE ${n} frames ${(n / FPS).toFixed(1)}s`;
  console.log(document.title);
}
