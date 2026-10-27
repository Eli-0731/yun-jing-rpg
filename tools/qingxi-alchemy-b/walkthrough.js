// Scripted player-view walkthrough (?walk): fixed time step, every frame composited with the HUD and posted to
// serve.mjs (/__frame). Encode afterwards with art/source/qingxi-alchemy-b/encode_walkthrough.py.
// Round 1: known recipe (one wrong pick first, to show the feedback), claim pressed three times.
// Round 2: research variant with strong fire -> failure reason and partial return.
const FPS = 12, DT = 1 / FPS;

export async function runWalkthrough(ctx) {
  const { tick, act, card, player, layout, b2t, canvas } = ctx;
  const out = document.createElement('canvas'); out.width = 1280; out.height = 720;
  const g = out.getContext('2d'); let n = 0;
  const station = role => layout.stations.find(s => s.role === role);

  // Paint a HUD panel from its live layout: element boxes (panel, buttons, meters, notices) and every text run at its
  // laid-out position, so selected buttons, done steps and meters read the same as on screen.
  const opaque = c => c && c !== 'transparent' && !/rgba\(.*,\s*0\)$/.test(c);
  function box(el, clip) {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (cs.display === 'none' || cs.visibility === 'hidden' || r.bottom < clip.top || r.top > clip.bottom) return;
    g.globalAlpha = +cs.opacity;
    const rad = Math.min(parseFloat(cs.borderTopLeftRadius) || 0, r.height / 2, r.width / 2);
    if (opaque(cs.backgroundColor)) { g.fillStyle = cs.backgroundColor; g.beginPath(); g.roundRect(r.left, r.top, r.width, r.height, rad); g.fill(); }
    if (parseFloat(cs.borderTopWidth) > 0 && opaque(cs.borderTopColor) && el.tagName === 'BUTTON') {
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
    for (let i = 0; i < s.length; i++) {            // group characters by laid-out line (handles wrapping)
      rg.setStart(node, i); rg.setEnd(node, i + 1);
      const r = rg.getClientRects()[0];
      if (!r || !r.width) continue;
      if (/\s/.test(s[i]) && (top === null || Math.abs(r.top - top) > r.height / 2)) continue;   // no leading blanks
      if (top === null || Math.abs(r.top - top) > r.height / 2) { flush(); top = r.top; x0 = r.left; mid = r.top + r.height / 2; }
      line += s[i];
    }
    flush();
  }
  function panel(id) {
    const el = document.getElementById(id);
    if (!el || el.hidden) return;
    const clip = el.getBoundingClientRect();
    g.save(); g.scale(out.width / innerWidth, out.height / innerHeight);
    g.shadowColor = 'rgba(0,0,0,.25)'; g.shadowBlur = 14; g.shadowOffsetY = 3;
    const cs = getComputedStyle(el); g.fillStyle = cs.backgroundColor;
    g.beginPath(); g.roundRect(clip.left, clip.top, clip.width, clip.height, parseFloat(cs.borderTopLeftRadius) || 0); g.fill();
    g.shadowColor = 'transparent';
    g.beginPath(); g.rect(clip.left, clip.top, clip.width, clip.height); g.clip();
    for (const c of el.childNodes) {
      if (c.nodeType === 1) box(c, clip);
      else if (c.nodeType === 3 && c.textContent.trim()) text(c, cs, clip);
    }
    g.restore();
  }
  async function frame() {
    tick(DT);
    g.drawImage(canvas, 0, 0, out.width, out.height);
    ['mode', 'steps', 'preview', 'card', 'prompt', 'toast'].forEach(panel);
    g.fillStyle = 'rgba(0,0,0,.55)'; g.fillRect(out.width - 92, out.height - 30, 86, 24); g.fillStyle = '#fff';
    g.font = '15px monospace'; g.fillText(`${(n / FPS).toFixed(1)}s`, out.width - 84, out.height - 25);
    await fetch(`/__frame?n=${n++}`, { method: 'POST', body: out.toDataURL('image/jpeg', 0.88) });
  }
  const hold = async s => { for (let i = 0; i < Math.round(s * FPS); i++) await frame(); };
  async function walkTo(role) {
    ctx.target = b2t(station(role).approach);
    for (let i = 0; i < FPS * 20 && ctx.target; i++) await frame();
    card(role); await hold(0.8);
  }
  const press = async (a, v, slot, s = 1.1) => { act(a, v, slot); await hold(s); };

  await hold(1.5);
  // ---- round 1: known recipe
  await walkTo('identify');
  for (const b of ctx.S.bag.map(x => x.batchId)) await press('identify', b);
  await walkTo('recipe');
  await press('recipe', 'body-bath');
  await press('pick', 'pr31-qinglan_01-r1', 'main', 0.6);
  await press('pick', 'pr31-yumai_01-r1', 'aux', 0.6);
  await press('lock', null, null, 2.6);                       // wrong material -> specific feedback
  await press('pick', 'pr31-chilu_01-r1', 'aux', 0.6);
  await press('lock', null, null, 1.4);
  await walkTo('water'); await press('water');
  await walkTo('process');
  await press('process', 'slice', 'main'); await press('process', 'soak', 'aux');
  await walkTo('fuel'); await press('fuel');
  await walkTo('refine');
  await press('fire', 'strong', null, 1.2); await press('fire', 'medium', null, 1.6);   // preview reacts to the choice
  await walkTo('filter');
  await press('collect', 'direct', null, 1.0); await press('collect', 'filter', null, 1.0);
  await press('brew', null, null, 2.2);
  await walkTo('collect');
  await press('claim', null, null, 1.6); await press('claim', null, null, 1.4); await press('claim', null, null, 1.6);   // repeats do not add
  await press('again', null, null, 0.8);
  // ---- round 2: research variant, strong fire fails with a reason and a partial return
  await walkTo('recipe');
  await press('recipe', 'body-bath:breath');
  await press('pick', 'pr31-chilu_01-r1', 'main', 0.5); await press('pick', 'pr31-yumai_01-r1', 'aux', 0.5);
  await press('lock', null, null, 1.2);
  await walkTo('water'); await press('water', null, null, 0.6);
  await walkTo('process');
  await press('process', 'soak', 'main', 0.7); await press('process', 'grind', 'aux', 0.9);
  await walkTo('fuel'); await press('fuel', null, null, 0.6);
  await walkTo('refine'); await press('fire', 'strong', null, 1.4);
  await walkTo('filter'); await press('collect', 'filter', null, 0.8);
  await press('brew', null, null, 4.0);
  await walkTo('collect'); await hold(2.5);
  document.title = `WALK_DONE ${n} frames ${(n / FPS).toFixed(1)}s`;
  console.log(document.title);
}
