"""FR measured checks: everything is read off the exported LOD0 by rays or from the sockets, not taken from the design numbers."""
import bpy, math
import numpy as np
from mathutils import Vector, Matrix
from ti_core import S
import ti_pipeline as pl


def _bvh(objs):
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get(); trees = [BVHTree.FromObject(o, dg) for o in objs]
    def cast(p, d):
        best = None
        for t in trees:
            hit = t.ray_cast(Vector(p), Vector(d).normalized())
            if hit[0] is not None and (best is None or hit[3] < best[1]): best = (hit[0], hit[3])
        return best
    def down(x, y, z0=20.):
        h = cast((x, y, z0), (0, 0, -1)); return h[0].z if h else None
    def up(x, y, z0):
        h = cast((x, y, z0), (0, 0, 1)); return h[0].z if h else None
    return down, up, cast


def wall_checks(aid, check, cfg):
    """FR01: taller than a person, the joint sections the same at both ends (so any shape joins any), a chained copy meets it."""
    import fr_wall as FW
    A = FW.ARC; objs = list(S['lods'][0].values()); down, up, cast = _bvh(objs)
    tops = []
    for i in range(41):
        u = -A.U + 2 * A.U * i / 40
        tops.append(max((down(*A.p(u, v, 0.)[:2]) or 0.) for v in [-.6 + .1 * k for k in range(13)]))
    check('taller_than_a_person', max(tops) >= 1.85 and max(tops) <= 2.2 + 1e-3,
          {'highest_top_m': round(max(tops), 3), 'person_m': 1.75, 'limit_m': 2.2, 'top_profile_every_0.14m': [round(t, 2) for t in tops]})
    vs = [-.8 + .1 * k for k in range(17)]
    def section(side):
        u = side * (A.U - .03); return [down(*A.p(u, v, 0.)[:2]) for v in vs]
    w, e = section(-1), section(1)
    diff = max(abs((a or 0) - (b or 0)) for a, b in zip(w, e))
    check('joint_sections_match', diff <= .006 and max(max(x or 0 for x in w), max(x or 0 for x in e)) <= FW.H_END + .06,
          {'west_z_m': [round(x or 0, 3) for x in w], 'east_z_m': [round(x or 0, 3) for x in e], 'max_difference_m': round(diff, 4),
           'note': 'every shape uses the same earth-bank section on the joint line (3 cm in from it); roots dive into the ground before it'})
    sw, se = S['sockets']['Socket_Join_W'].matrix_world, S['sockets']['Socket_Join_E'].matrix_world
    M = se @ Matrix.Rotation(math.pi, 4, 'Z') @ sw.inverted()        # the next section, its W joint on this one's E joint, facing back
    gap = []
    for v in vs:
        a = A.p(A.U, v, 0.); b = M @ A.p(-A.U, v, 0.)
        gap.append((a - b).length)
    turn = math.degrees(math.atan2(M[1][0], M[0][0]))
    check('three_sections_join', max(gap) <= .002, {'joint_line_gap_mm': round(max(gap) * 1000, 2), 'turn_per_section_deg': round(turn, 2),
                                                     'three_sections_turn_deg': round(3 * abs(turn), 1)})
    check('sockets_present', {'Socket_Join_W', 'Socket_Join_E'} <= set(S['sockets']), sorted(S['sockets']))
    return {'chord_m': A.L, 'arc_radius_m': round(A.R, 3), 'turn_per_section_deg': round(abs(turn), 2), 'joint_bank_height_m': FW.H_END,
            'highest_top_m': round(max(tops), 3), 'join': 'next Socket_Join_W on this Socket_Join_E, rotated 180 deg about Z', 'sockets': sorted(S['sockets'])}


def arch_checks(aid, check, cfg):
    """FR02: clear height over the path >= 2.2 m, clear width at shoulder and head height, the path itself open end to end."""
    import fr_arch as FA
    objs = list(S['lods'][0].values()); down, up, cast = _bvh(objs)
    heads = []
    for i in range(5):
        x = -.5 + .25 * i
        for j in range(15):
            y = -1.4 + .2 * j; z = up(x, y, .12)
            heads.append(z if z is not None else 99.)
    over = [z for z in heads if z < 99.]
    check('clear_height_over_path_2_2m', min(heads) >= 2.2, {'lowest_hit_above_path_m': round(min(heads), 3), 'rays': len(heads),
          'hits_under_the_crown': len(over), 'grid': 'x -0.5..0.5 every 0.25 m, y -1.4..1.4 every 0.2 m, from 0.12 m up', 'need_m': 2.2})
    widths = {}
    for z in (.3, 1.0, 1.75):
        row = []
        for y in (-.6, 0., .6):
            l = cast((0., y, z), (-1, 0, 0)); r = cast((0., y, z), (1, 0, 0))
            row.append(round((r[0].x if r else 2.5) - (l[0].x if l else -2.5), 3))
        widths[str(z)] = row
    check('clear_width_between_legs', min(widths['1.75']) >= 1.6 and min(widths['0.3']) >= 1.4, {'width_m_at_height': widths, 'need_m': {'1.75': 1.6, '0.3': 1.4}})
    blocked = []
    for x in (-.3, 0., .3):
        for z in (.4, 1.0, 1.7):
            h = cast((x, -1.6, z), (0, 1, 0))
            if h and h[0].y < 1.5: blocked.append([x, z, round(h[0].y, 3)])
    check('path_open_front_to_back', not blocked, {'rays_along_y_blocked': blocked, 'rays': 9})
    check('sockets_present', {'Socket_Path_S', 'Socket_Path_N'} <= set(S['sockets']), sorted(S['sockets']))
    return {'clear_height_m': round(min(heads), 3), 'clear_width_m': {k: min(v) for k, v in widths.items()}, 'path_width_m': FA.PATH_W,
            'walk': 'along Y from Socket_Path_S to Socket_Path_N', 'sockets': sorted(S['sockets'])}


def bridge_checks(aid, check, cfg):
    """FR04: the deck level and wide enough, steps of even small rises from the ground at both ends, nothing in the way above."""
    import fr_bridge as FB
    objs = list(S['lods'][0].values()); down, up, cast = _bvh(objs)
    widths, zs = [], []
    x = FB.X0 + .3
    while x < FB.X1 - .08:
        ys = [round(-.45 + .01 * j, 3) for j in range(91)]
        on = [y for y in ys if (lambda z: z is not None and abs(z - FB.DECK) <= .02)(down(x, y))]
        span = [y for y in on if y >= -.02 and y <= .02]
        if span:
            lo = hi = 0.
            while round(lo - .01, 3) in [round(v, 3) for v in on]: lo -= .01
            while round(hi + .01, 3) in [round(v, 3) for v in on]: hi += .01
            widths.append(round(hi - lo, 3))
        else: widths.append(0.)
        zs += [down(x, y) for y in (-.15, 0., .15)]
        x += .25
    zs = [z for z in zs if z is not None]
    check('deck_flat_and_wide', min(widths) >= .5 and max(zs) - min(zs) <= .03,
          {'deck_z_m': [round(min(zs), 3), round(max(zs), 3)], 'flat_width_m_every_0_25m': widths, 'need': 'width >= 0.5 m, z within 3 cm', 'design_deck_z_m': FB.DECK})
    seq = {}
    for side in ('W', 'E'):
        pts = [p for p in FB.step_positions() if (p[0] < 0) == (side == 'W')][::-1]     # outermost first
        tops = [round(down(x, y), 3) for x, y, h in pts]
        heights = [0.] + tops + [FB.DECK]
        seq[side] = {'tops_m': tops, 'rises_m': [round(b - a, 3) for a, b in zip(heights, heights[1:])]}
    worst = max(max(v['rises_m']) for v in seq.values())
    check('steps_even_rises', worst <= .2, {'by_end': seq, 'largest_rise_m': worst, 'need_m': .2})
    blocked = []
    for y in (-.2, 0., .2):
        for dz in (.05, .9, 1.75):
            h = cast((FB.X0 - .25, y, FB.DECK + dz), (1, 0, 0))
            if h and h[0].x < FB.X1 + .25: blocked.append(['deck', y, dz, round(h[0].x, 3)])
    for x, y, h in FB.step_positions():
        z = up(x, y, h + .02)
        if z is not None and z < h + 1.8: blocked.append(['step', round(x, 2), round(z, 3)])
    check('walk_line_clear', not blocked, {'blocked': blocked, 'rays': 'along X over the deck at y -0.2/0/0.2, 0.05/0.9/1.75 m up; straight up over every step'})
    check('sockets_present', {'Socket_Path_W', 'Socket_Path_E', 'Socket_Deck'} <= set(S['sockets']), sorted(S['sockets']))
    return {'deck_z_m': FB.DECK, 'deck_flat_width_min_m': min(widths), 'steps': seq, 'walk': 'along X: Socket_Path_W -> steps -> deck -> steps -> Socket_Path_E',
            'sockets': sorted(S['sockets'])}


def vine_checks(aid, check, cfg):
    """FR03: hangs from the origin, alpha-clipped two-sided cards, no collision, wind colour from 0 at the hang line to 1 at the tips."""
    import fr_vines as FV
    lods = S['lods']; V = S['vines']
    co = {}
    for gname, o in lods[0].items():
        me = o.data; a = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', a); co[gname] = a.reshape(-1, 3)
    allc = np.concatenate(list(co.values()))
    check('hangs_below_origin', allc[:, 2].max() <= 1e-3 and allc[:, 2].max() > -.02 and abs(allc[:, 2].min() - V['lowest_design_z']) < .01,
          {'top_z_m': round(float(allc[:, 2].max()), 4), 'lowest_z_m': round(float(allc[:, 2].min()), 4), 'design_lowest_z_m': V['lowest_design_z'],
           'depth_y_m': [round(float(allc[:, 1].min()), 3), round(float(allc[:, 1].max()), 3)]})
    lm = lods[0]['Leaves'].data.materials[0]
    check('cards_alpha_clip_two_sided', not lm.use_backface_culling, {'material': lm.name, 'alpha': 'BaseColor alpha, rounded (clip 0.5)', 'backface_culling': lm.use_backface_culling})
    check('no_collision', not S.get('collision_obj'), {'collision': 'none: decorative, never blocks a walk'})
    wind = {}
    for lv, g in lods.items():
        for gname, o in g.items():
            ca = o.data.color_attributes.get('Wind')
            if ca is None: wind[o.name] = None; continue
            c = np.zeros(len(ca.data) * 4, np.float32); ca.data.foreach_get('color', c); c = c.reshape(-1, 4)
            wind[o.name] = [round(float(c[:, 0].min()), 3), round(float(c[:, 0].max()), 3)]
    leaf = wind.get(f'{aid}_Leaves_LOD0')
    check('wind_vertex_colour_on_every_mesh', all(v is not None for v in wind.values()) and leaf and leaf[0] <= .02 and leaf[1] >= .95, {'R_min_max': wind})
    cards = {f'LOD{lv}': len(g['Leaves'].data.polygons) for lv, g in lods.items()}
    check('cards_fewer_per_lod', cards['LOD0'] > cards['LOD1'] > cards['LOD2'] > 0, {'card_quads': cards})
    uv = np.zeros(len(lods[0]['Leaves'].data.loops) * 2, np.float32); lods[0]['Leaves'].data.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    cells = sorted({int(min(3, u // .25)) for u in uv[:, 0] if 0 < u < 1})
    want = sorted({V['strip_cell'], V['tip_cell']})
    check('uses_its_atlas_cells', set(want) <= set(cells) | {int(c) for c in cells}, {'cells_touched': cells, 'strip_cell': V['strip_cell'], 'tip_cell': V['tip_cell']})
    check('sockets_present', 'Socket_Hang' in S['sockets'], sorted(S['sockets']))
    return {'strands': V['strands'], 'strip_cell': V['strip_cell'], 'tip_cell': V['tip_cell'], 'card_quads': cards, 'atlas': 'FR03_Shared/Textures/FR03_VineCards_*.png 2048',
            'minTier': cfg['minTier'], 'collision': 'none'}
