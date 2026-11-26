"""Materials for harvest-market-b (MK01–MK04): hand-painted direction, baked to one atlas per asset.

Builds on ti_mats (copied unchanged from tea-brewing-b). New here:
  weave()     split-bamboo weave driven by a per-part 'wuv' attribute (u around / across, v along), so curved
              basket walls and flat sieve floors both read as even strips;
  leaf()      qingling herb leaf driven by a per-part 'leaf' attribute (x across -1..1, y base→tip 0..1);
              top grade glows at the tip (Glow slot → Emission map, Unity _Glow 0–1), low grade yellows and spots.
Studio note (procedural-modeling memory): greens and stone stay at or below ~0.12 linear albedo.
"""
import math
import ti_mats as tm


def dabs(g, P, scale):
    """Painterly dabs: one random value per Voronoi cell, so tone shifts in flat brush patches."""
    bw = g.node('ShaderNodeRGBToBW'); g.link(g.voronoi(P, scale, 'F1', 'Color'), bw.inputs[0])
    return bw.outputs[0]


def ground(g, col, Z, P, h=.12, moss=True):
    """Earth grime rising from the ground and a touch of moss right at the foot."""
    dirt = g.math('MULTIPLY', g.maprange(Z, h, 0.0), g.maprange(g.noise(P, 5.0, 3, .5), .3, .6))
    col = g.mix(g.math('MULTIPLY', dirt, .6), col, (.07, .05, .032))
    if moss:
        m = g.math('MULTIPLY', g.maprange(Z, .03, 0.0), g.maprange(g.noise(P, 9.0, 3, .5), .45, .6))
        col = g.mix(g.math('MULTIPLY', m, .8), col, (.06, .09, .025))
    return col


def _zsep(g):
    P = g.geo('Position'); sep = g.node('ShaderNodeSeparateXYZ'); g.link(P, sep.inputs[0]); return P, sep


def painted_wood(name, dark, light, slot='Main', ground_h=.12, polish=0.0, chalk=None, moss=True):
    """Weathered timber: long soft streaks along the grain, per-board tint, knots, warm worn edges, grime from the
    ground. polish > 0 adds a hand-worn sheen band (steelyard beam). chalk = (centre xyz, radius) dusts chalk."""
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1.0, 1.0, 1.0))
    P, sep = _zsep(g)
    long = g.noise(g.vmath('MULTIPLY', co, (.35, 5.0, 5.0)), 1.6, 3, .5)
    streak = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.25, 22.0, 22.0)), 1.0, 2, .5), .35, .7)
    fibre = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.4, 70.0, 70.0)), 1.0, 2, .5), .4, .62)
    dab = dabs(g, g.vmath('MULTIPLY', co, (.5, 3.0, 3.0)), 9.0)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', long, .45), g.math('MULTIPLY', streak, .25)),
               g.math('ADD', g.math('MULTIPLY', r, .18), g.math('MULTIPLY', dab, .12)))
    mid = tuple((a + b) / 2 for a, b in zip(dark, light))
    col = g.ramp(t, [(.2, tuple(c * .72 for c in dark)), (.42, dark), (.62, mid), (.85, light)])
    col = g.mix(g.math('MULTIPLY', fibre, .12), col, tuple(c * .7 for c in dark))
    grey = g.maprange(g.noise(P, 1.8, 2, .5), .5, .72)                       # sun-bleached grey patches
    col = g.mix(g.math('MULTIPLY', grey, .3), col, (.2, .185, .16))
    knot = g.math('MULTIPLY', g.maprange(g.voronoi(g.vmath('MULTIPLY', co, (1.2, 6.0, 6.0)), 1.0, 'F1', 'Distance'), .08, .02),
                  g.maprange(g.noise(co, 3.0, 2, .5), .6, .7))
    col = g.mix(g.math('MULTIPLY', knot, .7), col, tuple(c * .5 for c in dark))
    if chalk:
        c, rad = chalk
        cc = g.node('ShaderNodeCombineXYZ')
        for i in range(3): cc.inputs[i].default_value = c[i]
        d = g.vmath('LENGTH', g.vmath('MULTIPLY', g.vmath('SUBTRACT', P, cc.outputs[0]), (1.0, 1.0, 1.4)))
        smear = g.math('MULTIPLY', g.maprange(d, rad, rad * .3), g.maprange(g.noise(g.vmath('MULTIPLY', P, (6, 6, 1.2)), 9.0, 3, .6), .45, .7))
        col = g.mix(g.math('MULTIPLY', smear, .28), col, (.3, .29, .27))
    if ground_h: col = ground(g, col, sep.outputs['Z'], P, ground_h, moss)
    ao = g.ao(.05)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.32, .28, .26)), (1, (1, 1, 1))]))
    e = g.edge(.004)
    col = g.mix(g.math('MULTIPLY', e, .6), col, tuple(min(1, c * 1.5 + .04) for c in light))
    rough = g.math('SUBTRACT', .78, g.math('MULTIPLY', e, .15))
    if polish:
        rough = g.math('SUBTRACT', rough, polish)
        col = g.mix(polish * .8, col, tuple(min(1, c * 1.25) for c in mid))
    nrm = g.bump(g.math('ADD', g.math('ADD', g.math('MULTIPLY', streak, .6), g.math('MULTIPLY', knot, -.5)),
                        g.math('MULTIPLY', fibre, .25)), .2, .0015)
    tm._finish(g, col, rough, 0.0, nrm, spec=.3)
    return m


def bamboo(name, green=(.07, .08, .022), straw=(.22, .14, .045), slot='Main', ground_h=.0):
    """Split bamboo: straw-yellow skin with green streaks, node rings, dark split ends, glossy worn edges."""
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1.0, 1.0, 1.0))
    P, sep = _zsep(g)
    streak = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.3, 40.0, 40.0)), 1.0, 2, .5), .3, .7)
    blot = g.noise(g.vmath('MULTIPLY', co, (.8, 4, 4)), 2.0, 3, .5)
    t = g.math('ADD', g.math('MULTIPLY', blot, .6), g.math('MULTIPLY', r, .4))
    col = g.ramp(t, [(.25, green), (.55, tuple((a + b) / 2 for a, b in zip(green, straw))), (.8, straw)])
    col = g.mix(g.math('MULTIPLY', streak, .25), col, tuple(c * .7 for c in straw))
    u = g.node('ShaderNodeSeparateXYZ'); g.link(co, u.inputs[0])
    node = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', g.math('FRACT', g.math('MULTIPLY', u.outputs['X'], 5.5)), .5)), .02, .0)
    col = g.mix(g.math('MULTIPLY', node, .7), col, tuple(c * .45 for c in straw))
    if ground_h: col = ground(g, col, sep.outputs['Z'], P, ground_h)
    ao = g.ao(.03)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.36, .32, .28)), (1, (1, 1, 1))]))
    e = g.edge(.0025)
    col = g.mix(g.math('MULTIPLY', e, .5), col, tuple(min(1, c * 1.45 + .03) for c in straw))
    tm._finish(g, col, g.math('SUBTRACT', .58, g.math('MULTIPLY', e, .12)), 0.0,
               g.bump(g.math('ADD', g.math('MULTIPLY', streak, .5), g.math('MULTIPLY', node, .8)), .25, .0012), spec=.35)
    return m


def weave(name, light, dark, slot='Main', reed=.011, block=.033, ground_h=.0, sweat=None, patch=None, xscale=1.0, green_cast=.35, plain=False,
          wobble=0.0, strip_var=.3):
    """Split-bamboo basket weave on the part's own 'wuv' coordinates: blocks of flat strips alternating
    direction, dark gaps, per-strip tone, strips dipping at block edges. sweat = dark band centre z."""
    m, g = tm._new(name, slot)
    W = g.attr('wuv'); sw = g.node('ShaderNodeSeparateXYZ'); g.link(W, sw.inputs[0])
    X, Y = sw.outputs['X'], sw.outputs['Y']
    if xscale != 1.0: X = g.math('MULTIPLY', X, xscale)   # < 1: wider cells along X (plain weave, flat wefts)
    P, sep = _zsep(g)
    if wobble:   # hand-woven: the block grid wanders a few mm instead of running dead straight
        X = g.math('ADD', X, g.math('MULTIPLY', g.math('SUBTRACT', g.noise(W, 9.0, 2, .5), .5), wobble))
        Y = g.math('ADD', Y, g.math('MULTIPLY', g.math('SUBTRACT', g.noise(g.vmath('ADD', W, (3.1, 7.7, 1.3)), 9.0, 2, .5), .5), wobble))
    if plain:
        # plain weave: flat wefts (rows reed tall) pass over and under narrower warps (cells block wide)
        i = g.math('FLOOR', g.math('DIVIDE', X, block)); j = g.math('FLOOR', g.math('DIVIDE', Y, reed))
        par = g.math('MULTIPLY', g.math('FRACT', g.math('MULTIPLY', g.math('ADD', i, j), .5)), 2.0)
        fx = g.math('FRACT', g.math('DIVIDE', X, block)); fy = g.math('FRACT', g.math('DIVIDE', Y, reed))
        edge = g.maprange(g.math('MINIMUM', fx, g.math('SUBTRACT', 1.0, fx)), 0.0, .22)
        weft = g.math('MULTIPLY', g.math('POWER', g.math('SINE', g.math('MULTIPLY', g.maprange(fy, .04, .96), math.pi)), .3),
                      g.math('ADD', .5, g.math('MULTIPLY', edge, .5)))
        warp = g.math('MULTIPLY', g.math('POWER', g.math('SINE', g.math('MULTIPLY', g.maprange(fx, .36, .64), math.pi)), .4), .8)
        h = g.math('ADD', weft, g.math('MULTIPLY', g.math('SUBTRACT', warp, weft), par))
        rid = g.math('ADD', j, g.math('MULTIPLY', par, g.math('ADD', g.math('SUBTRACT', i, j), 517.0)))
        wn = g.node('ShaderNodeTexWhiteNoise', noise_dimensions='1D'); g.link(rid, wn.inputs['W']); rv = wn.outputs['Value']
    else:
        bx = g.math('FLOOR', g.math('DIVIDE', X, block)); by = g.math('FLOOR', g.math('DIVIDE', Y, block))
        par = g.math('MULTIPLY', g.math('FRACT', g.math('MULTIPLY', g.math('ADD', bx, by), .5)), 2.0)
        across = g.math('ADD', Y, g.math('MULTIPLY', g.math('SUBTRACT', X, Y), par))
        along = g.math('ADD', X, g.math('MULTIPLY', g.math('SUBTRACT', Y, X), par))
        s = g.math('FRACT', g.math('DIVIDE', across, reed))
        prof = g.math('POWER', g.math('SINE', g.math('MULTIPLY', s, math.pi)), .35)
        rid = g.math('ADD', g.math('ADD', g.math('FLOOR', g.math('DIVIDE', across, reed)), g.math('MULTIPLY', par, 517.0)),
                     g.math('MULTIPLY', g.math('FLOOR', g.math('DIVIDE', along, block)), 37.0))
        wn = g.node('ShaderNodeTexWhiteNoise', noise_dimensions='1D'); g.link(rid, wn.inputs['W']); rv = wn.outputs['Value']
        fa = g.math('FRACT', g.math('DIVIDE', along, block))
        dip = g.maprange(g.math('MINIMUM', fa, g.math('SUBTRACT', 1.0, fa)), 0.0, .18)
        h = g.math('MULTIPLY', prof, g.math('ADD', .4, g.math('MULTIPLY', dip, .6)))
    n = g.noise(P, 4.0, 4, .55); fine = g.noise(W, 220.0, 3, .6)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', h, .5), g.math('MULTIPLY', rv, strip_var)), g.math('MULTIPLY', n, .2))
    col = g.ramp(t, [(.12, tuple(c * .45 for c in dark)), (.42, dark), (.8, light)])
    col = g.mix(g.math('MULTIPLY', fine, .15), col, tuple(c * .8 for c in dark))
    green = g.maprange(g.noise(P, 2.5, 3, .5), .5, .68)                      # some strips keep a green cast
    col = g.mix(g.math('MULTIPLY', green, green_cast), col, (.13, .14, .06))
    if sweat is not None:
        band = g.math('MULTIPLY', g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', sep.outputs['Z'], sweat)), .14, .02),
                      g.maprange(g.noise(P, 5.0, 3, .5), .3, .6))
        col = g.mix(g.math('MULTIPLY', band, .5), col, tuple(c * .55 for c in dark))
    if ground_h: col = ground(g, col, sep.outputs['Z'], P, ground_h)
    ao = g.ao(.025)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.36, .32, .28)), (1, (1, 1, 1))]))
    tm._finish(g, col, g.math('ADD', .66, g.math('MULTIPLY', fine, .1)), 0.0, g.bump(h, .5, .0016), sheen=.12, spec=.3)
    return m


def hemp(name, base=(.2, .11, .035), slot='Main', twist=140.0, ground_h=.0):
    """Twisted hemp cord: diagonal ply grooves along the grain axis, fuzz, darker in the grooves."""
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1.0, 1.0, 1.0))
    P, sep = _zsep(g)
    cs = g.node('ShaderNodeSeparateXYZ'); g.link(co, cs.inputs[0])
    ang = g.math('ARCTAN2', cs.outputs['Y'], cs.outputs['Z'])
    ply = g.math('SINE', g.math('ADD', g.math('MULTIPLY', cs.outputs['X'], twist), g.math('MULTIPLY', ang, 3.0)))
    ply = g.maprange(ply, -1.0, 1.0)
    fuzz = g.noise(g.vmath('MULTIPLY', P, (1, 1, 1)), 400.0, 3, .7)
    n = g.noise(P, 6.0, 3, .5)
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', ply, .55), g.math('MULTIPLY', n, .45)),
                 [(.15, tuple(c * .45 for c in base)), (.55, base), (.9, tuple(min(1, c * 1.25) for c in base))])
    col = g.mix(g.math('MULTIPLY', fuzz, .1), col, tuple(min(1, c * 1.3) for c in base))
    if ground_h: col = ground(g, col, sep.outputs['Z'], P, ground_h, False)
    ao = g.ao(.02)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.4, .36, .32)), (1, (1, 1, 1))]))
    tm._finish(g, col, .86, 0.0, g.bump(g.math('ADD', ply, g.math('MULTIPLY', fuzz, .3)), .55, .0008), sheen=.3, spec=.2)
    return m


def brass(name, slot='Main', base=(.42, .27, .085), patina=(.09, .13, .085), amt=.35):
    return tm.metal(name, base, patina, slot=slot, rough=.32, patina_amt=amt, patina_scale=22.0, crevice=1.8)


def bronze_coin(name, slot='Main'):
    """Old bronze cash: dark bronze field, green patina pooled in the recesses and the hole, bright worn rims."""
    return tm.metal(name, (.28, .16, .06), (.08, .16, .1), slot=slot, rough=.4, patina_amt=.75, patina_scale=40.0, crevice=2.4)


def cast_iron(name, slot='Main'):
    """Cast-iron counterweight: warm near-black, hammered dimples, rust mottling, bright worn edges."""
    m, g = tm._new(name, slot)
    P = g.geo('Position')
    n = g.noise(P, 26.0, 3, .5); dab = dabs(g, P, 120.0)
    ham = g.voronoi(P, 260.0, 'F1', 'Distance')
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', n, .6), g.math('MULTIPLY', dab, .4)),
                 [(.3, (.03, .028, .027)), (.6, (.055, .05, .046)), (.85, (.09, .08, .07))])
    rust = g.math('MULTIPLY', g.maprange(g.noise(P, 36.0, 4, .55), .52, .68), g.math('SUBTRACT', 1.0, g.ao(.012)))
    rust = g.math('MAXIMUM', rust, g.maprange(g.noise(P, 55.0, 3, .5), .62, .7))
    col = g.mix(g.math('MULTIPLY', rust, .9), col, (.2, .085, .036))
    col = g.mix(g.math('MULTIPLY', g.maprange(ham, .05, .25), .22), col, (.08, .072, .066))
    e = g.edge(.0018)
    col = g.mix(g.math('MULTIPLY', e, .7), col, (.2, .17, .14))
    tm._finish(g, col, g.math('ADD', .74, g.math('MULTIPLY', rust, .16)), g.math('SUBTRACT', .06, g.math('MULTIPLY', rust, .06)),
               g.bump(ham, .4, .0006), spec=.4)
    return m


def cloth(name, base, slot='Main', weave_=700.0, dirt=.3, ground_h=.0, worn=.0, coarse=1.):
    """Cotton / indigo: fine weave bump, slubs, soft fold shading from AO, faded worn highlights."""
    m, g = tm._new(name, slot)
    P, sep = _zsep(g)
    w1 = g.wave(P, weave_, 1.0, 'BANDS', 'X', 1); w2 = g.wave(P, weave_, 1.0, 'BANDS', 'Z', 1)
    slub = g.noise(g.vmath('MULTIPLY', P, (2, 2, 30)), 16.0, 4, .6)
    n = g.noise(P, 9.0, 4, .55); dab = dabs(g, P, 40.0)
    col = g.ramp(g.math('ADD', g.math('ADD', g.math('MULTIPLY', slub, .4), g.math('MULTIPLY', n, .4)), g.math('MULTIPLY', dab, .2)),
                 [(.3, tuple(c * .78 for c in base)), (.72, tuple(min(1, c * 1.12) for c in base))])
    if worn:
        fade = g.maprange(g.noise(P, 14.0, 3, .5), .55, .72)
        col = g.mix(g.math('MULTIPLY', fade, worn), col, tuple(min(1, c * 1.9 + .05) for c in base))
    ao = g.ao(.03)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.42, .4, .42)), (1, (1, 1, 1))]))
    col = g.mul(dirt, col, g.ramp(g.noise(P, 6.0, 3, .5), [(.4, (.7, .66, .6)), (.7, (1, 1, 1))]))
    if ground_h: col = ground(g, col, sep.outputs['Z'], P, ground_h, False)
    e = g.edge(.003)
    col = g.mix(g.math('MULTIPLY', e, .35), col, tuple(min(1, c * 1.7 + .04) for c in base))
    h = g.math('ADD', g.math('MULTIPLY', g.math('ADD', w1, w2), .5), g.math('MULTIPLY', slub, .4))
    tm._finish(g, col, g.math('ADD', .86, g.math('MULTIPLY', n, .06)), 0.0, g.bump(h, min(1., .14 * coarse), .0006 * coarse), sheen=.45, spec=.25)
    return m


def soil(name, slot='Main'):
    m, g = tm._new(name, slot)
    P = g.geo('Position')
    n = g.noise(P, 60.0, 4, .6); grain = g.voronoi(P, 300.0, 'F1', 'Distance'); dab = dabs(g, P, 90.0)
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', n, .6), g.math('MULTIPLY', dab, .4)),
                 [(.25, (.025, .017, .01)), (.55, (.05, .034, .02)), (.85, (.085, .062, .038))])
    col = g.mix(g.math('MULTIPLY', g.maprange(grain, .2, .05), .3), col, (.11, .09, .065))
    tm._finish(g, col, .95, 0.0, g.bump(g.math('ADD', n, g.math('MULTIPLY', grain, -.6)), .7, .0015), spec=.15)
    return m


def root(name, slot='Main'):
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1.0, 1.0, 1.0))
    P, sep = _zsep(g)
    n = g.noise(g.vmath('MULTIPLY', co, (.4, 30, 30)), 8.0, 3, .5)
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', n, .7), g.math('MULTIPLY', r, .3)),
                 [(.2, (.09, .06, .035)), (.6, (.2, .145, .085)), (.9, (.3, .23, .14))])
    dirt = g.maprange(g.noise(P, 40.0, 3, .5), .45, .62)
    col = g.mix(g.math('MULTIPLY', dirt, .7), col, (.05, .035, .02))
    tm._finish(g, col, .85, 0.0, g.bump(n, .3, .0005), spec=.2)
    return m


def stem(name, slot='Main'):
    """Herb stem: fresh green going pale and purplish-brown at the base, faint lengthwise ribs."""
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1.0, 1.0, 1.0))
    P, sep = _zsep(g)
    ribs = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.3, 160, 160)), 1.0, 2, .5), .4, .65)
    L = g.attr('leaf'); ls = g.node('ShaderNodeSeparateXYZ'); g.link(L, ls.inputs[0])
    v = ls.outputs['Y']
    col = g.ramp(v, [(0, (.08, .04, .025)), (.25, (.04, .06, .015)), (.7, (.025, .075, .014)), (1, (.045, .1, .02))])
    col = g.mix(g.math('MULTIPLY', ribs, .25), col, (.07, .11, .03))
    ao = g.ao(.015)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.4, .4, .38)), (1, (1, 1, 1))]))
    tm._finish(g, col, .6, 0.0, g.bump(ribs, .2, .0004), spec=.35)
    return m


GRADE_LOOK = {
    # base / mid / tip green, sheen, yellowing, spots
    'top': dict(base=(.014, .05, .011), mid=(.032, .1, .017), tip=(.07, .17, .032), yellow=0.0, spots=0.0),
    'mid': dict(base=(.014, .046, .011), mid=(.03, .092, .016), tip=(.065, .15, .028), yellow=0.0, spots=0.0),
    'low': dict(base=(.02, .04, .01), mid=(.04, .065, .014), tip=(.08, .08, .02), yellow=.9, spots=.8),
}


def leaf(name, grade, slot='Main'):
    """Qingling herb leaf on its 'leaf' attribute (x across -1..1, y base→tip). Midrib and paired side veins,
    painterly tone patches, darker serrated rim. Top: a soft cyan glow creeping into the tip (emission, scaled
    by EMIT_STRENGTH = Unity _Glow). Low: yellow-brown edges and rust spots (holes are cut in the mesh)."""
    L = GRADE_LOOK[grade]
    m, g = tm._new(name, slot)
    A = g.attr('leaf'); ls = g.node('ShaderNodeSeparateXYZ'); g.link(A, ls.inputs[0])
    u, v = ls.outputs['X'], ls.outputs['Y']; au = g.math('ABSOLUTE', u)
    P = g.geo('Position')
    dab = dabs(g, P, 160.0); n = g.noise(P, 40.0, 3, .5)
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', v, .75), g.math('ADD', g.math('MULTIPLY', dab, .15), g.math('MULTIPLY', n, .1))),
                 [(.0, L['base']), (.45, L['mid']), (.95, L['tip'])])
    rib = g.maprange(au, .09, .02)
    veins = g.math('MULTIPLY', g.maprange(g.math('ABSOLUTE', g.math('SINE', g.math('MULTIPLY', g.math('SUBTRACT', v, g.math('MULTIPLY', au, .35)), 52.0))), .12, .0),
                   g.maprange(au, .1, .25))
    veins = g.math('MULTIPLY', veins, g.maprange(au, .9, .6))
    col = g.mix(g.math('MULTIPLY', rib, .6), col, (.09, .15, .035))
    col = g.mix(g.math('MULTIPLY', veins, .3), col, (.05, .11, .025))
    col = g.mix(g.math('MULTIPLY', g.maprange(au, .85, 1.0), .2), col, tuple(c * .75 for c in L['base']))   # darker rim
    emit = None
    if grade == 'top':
        gl = g.math('MULTIPLY', g.maprange(v, .7, .97), g.math('ADD', .35, g.math('MULTIPLY', g.maprange(au, .5, .95), .65)))   # tips, strongest on the serrated rim
        col = g.mix(g.math('MULTIPLY', gl, .35), col, (.2, .62, .55))
        emit = g.mul(1.0, g.rgb((.22, .95, .85)), g.ramp(gl, [(0, (0, 0, 0)), (1, (1, 1, 1))]))
    if L['yellow']:
        yel = g.math('ADD', g.maprange(au, .45, 1.0), g.math('MULTIPLY', g.maprange(v, .55, 1.0), .5))
        yel = g.math('MULTIPLY', g.math('ADD', yel, g.math('MULTIPLY', g.noise(P, 30.0, 3, .6), .5)), .7)
        col = g.mix(g.math('MULTIPLY', g.maprange(yel, .35, .9), L['yellow']), col, (.3, .2, .03))
        spot = g.math('MULTIPLY', g.maprange(g.voronoi(P, 140.0, 'F1', 'Distance'), .16, .07), g.maprange(g.noise(P, 18.0, 2, .5), .45, .6))
        col = g.mix(g.math('MULTIPLY', spot, L['spots']), col, (.13, .07, .02))
    ao = g.ao(.02)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.74, .76, .7)), (1, (1, 1, 1))]))
    h = g.math('ADD', g.math('MULTIPLY', rib, -.6), g.math('MULTIPLY', veins, -.35))
    tm._finish(g, col, g.math('ADD', .62, g.math('MULTIPLY', n, .1)), 0.0, g.bump(h, .3, .0004), emit=emit, sheen=0.0, spec=.22)
    return m
