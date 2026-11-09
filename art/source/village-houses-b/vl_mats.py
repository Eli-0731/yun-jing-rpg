"""village-houses-b materials: the StarterHouse palette moved onto the style-spec colours (modeling-style-spec-v1 section 2) and given
the three conditions. Procedural, baked to the house atlases like every other kit.

plaster()   lime coat over mud brick: trowelled coats, rain streaks under the eaves, damp from the plinth, hairline cracks, coat fallen
            off in blobs (peel) showing the brick courses, fresher lime patches (repair), rust runs from nails (rust attribute).
"""
import ti_mats as tm
import cr_mats as cm
from cr_mats import _p, _moss
from mk_mats import dabs

# style spec section 2 (sRGB -> linear)
LIME = ((.693, .624, .509), (.578, .503, .381))        # #D9CFBD, #C8BCA6
WOOD = ((.102, .042, .016), (.195, .085, .034), (.043, .019, .008))   # #5A3A22, #7A5234, #3B2617
WOOD_GREY = (.155, .127, .098)                          # #6E6458
STONE = ((.111, .147, .144), (.061, .084, .078), (.202, .242, .231))  # #5E6B6A, #46524F, #7C8784
EARTH = ((.262, .144, .065), (.392, .235, .117))        # #8C6A48, #A88560


def plaster(name, peel=.3, repair=0., grime=.6, moss=0., damp=1., seed=(0., 0., 0.), blacken=0., slot='Main', tone=1.):
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    Ps = g.vmath('ADD', P, seed)
    base = tuple(c * tone for c in LIME[0]); low = tuple(c * tone for c in LIME[1])
    big = g.noise(Ps, 1.4, 4, .55); mid = g.noise(Ps, 6.5, 4, .55); fine = g.noise(Ps, 55.0, 3, .55)
    d = dabs(g, Ps, 7.0)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', big, .5), g.math('MULTIPLY', mid, .3)), g.math('MULTIPLY', d, .2))
    col = g.ramp(t, [(.3, tuple(c * .9 for c in low)), (.5, low), (.66, base), (.8, tuple(min(1, c * 1.05) for c in base))])
    # rain runs from under the eave and the window sills
    runs = g.noise(g.vmath('MULTIPLY', Ps, (9., 9., .5)), 3.0, 3, .5)
    streak = g.math('MULTIPLY', g.maprange(runs, .52, .68), g.maprange(Z, 2.0, 3.3))
    col = g.mix(g.math('MULTIPLY', streak, .32 * grime), col, (.29, .25, .19))
    # damp and splash rising from the plinth
    dampm = g.maprange(g.math('ADD', Z, g.math('MULTIPLY', big, .45)), 1.25, .62, 0., 1.)
    col = g.mix(g.math('MULTIPLY', dampm, .55 * damp), col, (.2, .17, .12))
    if repair:      # newer lime: brighter, cooler, smoother, in trowel-sized patches with a faint edge
        pm = g.noise(g.vmath('ADD', Ps, (17.3, 4.1, 9.7)), 1.1, 3, .5)
        patch = g.maprange(pm, .62 - .1 * repair, .64 - .1 * repair)
        rim = g.math('MULTIPLY', g.maprange(pm, .6 - .1 * repair, .625 - .1 * repair), g.math('SUBTRACT', 1., patch))
        col = g.mix(g.math('MULTIPLY', patch, .8), col, (.74, .71, .64))
        col = g.mix(g.math('MULTIPLY', rim, .35), col, (.42, .37, .29))
    # hairline cracks
    crack = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', g.noise(Ps, 3.2, 3, .6), .5)), .008, .0, 0., 1.)
    crack = g.math('MULTIPLY', crack, g.maprange(g.noise(Ps, 1.1, 2, .5), .45, .6))
    col = g.mix(g.math('MULTIPLY', crack, .8), col, (.17, .14, .1))
    # coat fallen off: mud brick in running bond (u = x + y along either wall, v = z)
    peelm = None; h = g.math('ADD', g.math('MULTIPLY', mid, .5), g.math('MULTIPLY', fine, .3))
    if peel:
        sep = g.node('ShaderNodeSeparateXYZ'); g.link(P, sep.inputs[0])
        uvb = g.node('ShaderNodeCombineXYZ'); g.link(g.math('ADD', sep.outputs['X'], sep.outputs['Y']), uvb.inputs[0]); g.link(Z, uvb.inputs[1])
        br = g.node('ShaderNodeTexBrick'); g.link(uvb.outputs[0], br.inputs['Vector'])
        br.offset = .5; br.squash = 1.
        br.inputs['Scale'].default_value = 1.; br.inputs['Brick Width'].default_value = .3; br.inputs['Row Height'].default_value = .1
        br.inputs['Mortar Size'].default_value = .012; br.inputs['Mortar Smooth'].default_value = .3; br.inputs['Bias'].default_value = 0.
        br.inputs['Color1'].default_value = (*EARTH[0], 1); br.inputs['Color2'].default_value = (*EARTH[1], 1)
        br.inputs['Mortar'].default_value = (.09, .06, .035, 1)
        brick = g.mix(g.math('MULTIPLY', g.maprange(g.noise(P, 18., 3, .6), .3, .7), .5), br.outputs['Color'], (.16, .09, .045))
        mortar = br.outputs['Fac']
        pn = g.math('ADD', g.noise(g.vmath('ADD', Ps, (3.1, 7.7, 1.9)), 1.6, 4, .6), g.math('MULTIPLY', g.noise(Ps, 9., 3, .6), .18))
        bias = g.math('ADD', g.math('MULTIPLY', g.maprange(Z, 2.2, .7), .08), .0)      # more fallen low down, where the damp is
        pv = g.math('ADD', pn, bias)
        thr = .78 - .22 * peel
        peelm = g.maprange(pv, thr, thr + .012)
        rimm = g.math('MULTIPLY', g.maprange(pv, thr - .03, thr), g.math('SUBTRACT', 1., peelm))
        col = g.mix(g.math('MULTIPLY', rimm, .5), col, (.3, .24, .16))                  # broken coat edge, dirty
        col = g.mix(peelm, col, brick)
        h = g.math('ADD', g.math('MULTIPLY', g.math('SUBTRACT', 1., peelm), 1.2), g.math('MULTIPLY', g.math('SUBTRACT', 1., mortar), g.math('MULTIPLY', peelm, -.5)))
        h = g.math('ADD', h, g.math('MULTIPLY', fine, .25))
    # rust runs under the nails (attribute 'rust' on the nailed plaster)
    rs = g.attr('rust', 'Fac')
    rr = g.math('MULTIPLY', rs, g.maprange(g.noise(g.vmath('MULTIPLY', P, (40., 40., 2.)), 1.0, 2, .5), .35, .6))
    col = g.mix(g.math('MULTIPLY', rr, .8), col, (.16, .06, .02))
    if blacken:
        bl = g.maprange(g.noise(Ps, 2.3, 3, .55), .4, .65)
        col = g.mix(g.math('MULTIPLY', bl, blacken), col, (.14, .13, .1))
    ao = g.ao(.06)
    if moss:
        col, _, _ = _moss(g, col, P, ao, up, Z, moss, low_z=.9)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.48, .45, .46)), (1, (1, 1, 1))]))
    tm._finish(g, col, g.math('ADD', .86, g.math('MULTIPLY', fine, .08)), 0.0, g.bump(h, .5, .006), spec=.15)
    return m


def boards(name, slot='Main'):
    """Nailed-up planks: grey sun-bleached boards with rust runs under each nail ('rust' attribute)."""
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1, 1, 1))
    P, Z, up = _p(g)
    long = g.noise(g.vmath('MULTIPLY', co, (.35, 6, 6)), 1.6, 3, .5)
    lines = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.22, 90, 90)), 1.0, 3, .55), .55, .66)
    t = g.math('ADD', g.math('MULTIPLY', long, .6), g.math('MULTIPLY', r, .4))
    col = g.ramp(t, [(.2, (.07, .058, .046)), (.5, WOOD_GREY), (.8, (.25, .215, .17))])
    col = g.mix(g.math('MULTIPLY', lines, .7), col, (.05, .04, .032))
    rs = g.attr('rust', 'Fac')
    rr = g.math('MULTIPLY', rs, g.maprange(g.noise(g.vmath('MULTIPLY', P, (50., 50., 3.)), 1.0, 2, .5), .3, .6))
    col = g.mix(g.math('MULTIPLY', rr, .85), col, (.15, .055, .018))
    ao = g.ao(.04)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.35, .32, .32)), (1, (1, 1, 1))]))
    e = g.edge(.004)
    col = g.mix(g.math('MULTIPLY', e, .5), col, (.33, .3, .25))
    tm._finish(g, col, .85, 0.0, g.bump(g.math('ADD', long, g.math('MULTIPLY', lines, -.8)), .45, .002), spec=.25)
    return m


def iron(name, slot='Main'):
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    n = g.noise(P, 60., 3, .6)
    col = g.ramp(n, [(.3, (.025, .02, .018)), (.6, (.07, .035, .02)), (.8, (.15, .065, .025))])
    tm._finish(g, col, .75, .55, g.bump(n, .3, .0008), spec=.4)
    return m


def palette(cond):
    """cond: 'abandoned' | 'moved_in' | 'collapsed'."""
    P = {}
    peel = {'abandoned': .62, 'moved_in': .03, 'collapsed': .5}[cond]
    P['plaster'] = plaster('Lime_Plaster', peel=peel, repair=.8 if cond == 'moved_in' else 0., grime={'abandoned': .9, 'moved_in': .55, 'collapsed': 1.}[cond],
                           moss=.35 if cond == 'collapsed' else 0., blacken=.35 if cond == 'collapsed' else 0., seed=(0., 0., 0.))
    P['plaster_in'] = plaster('Lime_Plaster_Inside', peel=.35, grime=.8, damp=1.3, moss=.25 if cond == 'collapsed' else 0., blacken=.45 if cond == 'collapsed' else .1,
                              seed=(5.3, 1.7, 0.), tone=.8)
    grey = {'abandoned': .75, 'moved_in': .35, 'collapsed': .6}[cond]
    dark, light = WOOD[2], WOOD[1]
    if cond == 'collapsed': dark, light = (.03, .016, .009), (.11, .06, .03)
    P['timber'] = cm.wood('Frame_Timber', dark, light, grey=grey, ground_h=.12, moss=cond == 'collapsed', moss_amt=.5)
    P['plank'] = cm.wood('Porch_Plank', WOOD[0], (.26, .14, .06), grey=grey * .9, ground_h=0., polish=.05 if cond == 'moved_in' else 0.)
    P['door'] = cm.wood('Door_Board', WOOD[2], WOOD[0], grey=grey, ground_h=0.)
    P['stone'] = [cm.stone(f'Plinth_Stone_{i}', light=l, dark=d, ochre=(.2, .19, .15), moss=m_, lichen=.6, crack=.5)
                  for i, (l, d, m_) in enumerate(((STONE[2], STONE[1], .7 if cond != 'moved_in' else .35), (STONE[0], STONE[1], .9 if cond != 'moved_in' else .45)))]
    P['mortar'] = tm.plain('Plinth_Mortar', (.05, .048, .042), rough=.9, noise=.3)
    P['paper'] = cm.paper('Window_Paper', base=(.78, .74, .62) if cond == 'moved_in' else (.42, .33, .19), edge=(.5, .44, .33) if cond == 'moved_in' else (.17, .1, .045),
                          age=.12 if cond == 'moved_in' else .8)
    P['tile'] = cm.tile('Ridge_Tile', base=STONE[1], light=STONE[0], moss=.9 if cond != 'moved_in' else .45)
    P['brass'] = __import__('mk_mats').brass('Door_Brass')
    P['clay'] = cm.clay('Clay_Jar', body=(.2, .11, .06), glaze=(.075, .04, .022))
    P['iron'] = iron('Nail_Iron')
    P['boards'] = boards('Nailed_Board')
    P['moss'] = cm.moss_tuft('Roof_Moss', soft=True)
    P['grass'] = cm.weed_leaf('Eave_Grass', (.03, .06, .02), (.1, .17, .045), (.2, .24, .07))
    P['dry'] = cm.weed_leaf('Dry_Grass', (.1, .075, .03), (.25, .19, .08), (.4, .31, .14))
    P['leaf'] = cm.weed_leaf('Fallen_Leaf', (.09, .045, .015), (.22, .12, .04), (.36, .22, .08))     # dull brown, a few still ochre
    P['earth'] = cm.packed_earth('Rubble_Earth', dark=(.07, .055, .04), light=(.22, .165, .105), moss=.35)      # mud-brick dust greyed with lime
    return P
