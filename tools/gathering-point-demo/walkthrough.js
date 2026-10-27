// 自動走查：開 index.html?walk=1（serve.py 要加 --capture）會依序走完全段並存截圖。
// 遠景 → 近景觀察 → 採集後 → 未再生原因 → 岔口選路 → 涉水受阻 → 踏板 → 礦石 → 再生。
export async function run(d) {
  const shots = [];
  const shot = async name => { const s = await d.capture(name); shots.push(`${name}:${s}`); };
  d.view([16, 1.6, 7], [2, 2.2, -2.6]); d.advance(.1); await shot('01_far_landmark_from_14m');
  d.view([30, 1.6, 6], [12, .5, -1.1]); d.advance(.1); await shot('02_far_herbs_from_path');
  d.view(null); d.cam('side');
  d.teleport(1.2); d.advance(.5); await shot('03_start_safe_landmark');
  d.teleport(11.4); d.advance(.6, 1); d.press('e'); d.advance(1.2); await shot('04_qinglan_near_observe_pre');
  d.press('e'); d.advance(1.5); await shot('05_qinglan_post');
  d.press('e'); d.advance(.2); await shot('06_qinglan_not_respawned_reason');
  d.teleport(23.4); d.advance(.6, 1); d.press('e'); d.advance(1.2); await shot('07_chilu_near_observe_pre');
  d.press('e'); d.advance(1.5); await shot('08_chilu_post');
  d.cam('side'); d.teleport(37.5); d.advance(1.5, 1); await shot('09_fork_must_choose');
  d.press('s'); d.advance(2.0, 1); await shot('10_wade_blocked');
  d.press('w'); d.advance(.8); d.advance(1.0, 1); await shot('11_on_planks');
  d.view([42.2, 1.6, 3.2], [42.2, .1, 0]); d.advance(.1); await shot('12_planks_near');
  d.view(null); d.cam('side');
  d.teleport(50.4); d.advance(.6, 1); d.press('e'); d.advance(1.2); await shot('13_ore_near_observe_pre');
  d.press('e'); d.advance(1.5); await shot('14_ore_post');
  d.press('e'); d.advance(.2); await shot('15_ore_not_respawned_reason');
  d.skip(310); d.advance(.5); await shot('16_ore_respawned');
  return {shots, state: d.state()};
}
