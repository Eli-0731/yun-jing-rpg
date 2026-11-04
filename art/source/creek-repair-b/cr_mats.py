"""Materials for creek-repair-b: hand-painted direction (large soft shifts, a few brush dabs), baked to one atlas per asset.
Builds on ti_mats / mk_mats (copied unchanged from harvest-market-b). Colours start from the style guide table."""
import ti_mats as tm
import mk_mats as mm
from mk_mats import dabs


def _p(g):
    P = g.geo('Position'); sep = g.node('ShaderNodeSeparateXYZ'); g.link(P, sep.inputs[0])
    nz = g.node('ShaderNodeSeparateXYZ'); g.link(g.geo('Normal'), nz.inputs[0])
    return P, sep.outputs['Z'], nz.outputs['Z']


def _wet(g, col, Z, P, wet_z, amount=.62, drip=0., band_amt=.4):
    """Water mark: darker below the line, a greener band on it; drip stretches the edge into vertical runs."""
    if wet_z is None: return col, None
    wob = g.math('MULTIPLY', g.math('SUBTRACT', g.noise(P, 9.0, 2, .5), .5), .03)
    if drip:
        runs = g.noise(g.vmath('MULTIPLY', P, (1, 1, .04)), 34.0, 3, .55)
        wob = g.math('ADD', wob, g.math('MULTIPLY', g.math('SUBTRACT', runs, .5), drip))
    z = g.math('ADD', Z, wob)
    below = g.maprange(z, wet_z + .01, wet_z - .02)
    col = g.mul(g.math('MULTIPLY', below, amount), col, (.42, .4, .36))
    band = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', z, wet_z)), .03, .004)
    col = g.mix(g.math('MULTIPLY', band, band_amt), col, (.07, .09, .04))
    return col, below


def _moss(g, col, P, ao, up, Z, amount, low_z=.3):
    big = g.noise(P, 5.0, 3, .55); fine = g.noise(P, 42.0, 3, .6)
    m = g.math('ADD', g.math('MULTIPLY', g.math('SUBTRACT', 1.0, ao), 1.25),
               g.math('ADD', g.math('MULTIPLY', g.maprange(up, .6, .98), .13), g.math('MULTIPLY', g.maprange(Z, low_z, 0.), .3)))
    m = g.math('MULTIPLY', g.math('ADD', m, g.math('MULTIPLY', g.maprange(big, .38, .68), .62)), amount)
    clump = g.maprange(g.noise(P, 90.0, 3, .65), .36, .56)
    m = g.maprange(g.math('ADD', m, g.math('MULTIPLY', g.math('ADD', g.math('MULTIPLY', fine, .5), g.math('MULTIPLY', clump, .5)), .4)), .8, .94)
    tone = g.ramp(g.math('ADD', g.math('MULTIPLY', fine, .6), g.math('MULTIPLY', big, .4)),
                  [(.3, (.024, .027, .011)), (.55, (.05, .055, .019)), (.8, (.105, .1, .034))])
    return g.mix(m, col, tone), m, fine


def stone(name, light=(.37, .35, .3), dark=(.18, .17, .145), ochre=(.29, .25, .17), moss=.8, wet_z=None, crack=.7, lichen=.5, slot='Main'):
    # the game's sun and sky add up well over 1: these are the values that read as warm grey granite under them, not white
    light = tuple(c * .74 for c in light); dark = tuple(c * .76 for c in dark); ochre = tuple(c * .82 for c in ochre)
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    warp = g.vmath('ADD', P, g.vmath('MULTIPLY', g.noise(P, 14.0, 3, .55, out='Color'), (.05, .05, .05)))
    big = g.noise(P, 4.2, 4, .55); d1 = dabs(g, warp, 22.0); d2 = dabs(g, warp, 70.0)
    d0 = dabs(g, warp, 11.0)
    t = g.math('ADD', g.math('MULTIPLY', big, .46), g.math('ADD', g.math('ADD', g.math('MULTIPLY', d0, .2), g.math('MULTIPLY', d1, .2)), g.math('MULTIPLY', d2, .14)))
    mid = tuple((a + b) / 2 for a, b in zip(light, dark))
    col = g.ramp(t, [(.28, dark), (.46, mid), (.68, light)])
    col = g.mix(g.math('MULTIPLY', g.maprange(g.noise(P, 11.0, 4, .6), .48, .64), .62), col, ochre)
    fl = g.maprange(g.noise(P, 120.0, 2, .5), .58, .72)
    col = g.mix(g.math('MULTIPLY', fl, .3), col, tuple(c * 1.45 for c in light))
    pit = g.maprange(g.noise(P, 210.0, 3, .6), .62, .7)
    col = g.mix(g.math('MULTIPLY', pit, .42), col, tuple(c * .55 for c in dark))
    edges = g.voronoi(g.vmath('ADD', g.vmath('MULTIPLY', P, (1, 1, 1.25)), g.vmath('MULTIPLY', g.noise(P, 9.0, 3, .6, out='Color'), (.08, .08, .08))), 5.0)
    mask = g.maprange(g.noise(P, 6.0, 2, .5), .5, .6)
    crk = g.math('MULTIPLY', g.maprange(edges, .007, .0), mask)
    col = g.mix(g.math('MULTIPLY', crk, crack), col, tuple(c * .45 for c in dark))
    fw = g.vmath('ADD', g.vmath('MULTIPLY', P, (1, 1, 1.2)), g.vmath('MULTIPLY', g.noise(P, 26.0, 3, .6, out='Color'), (.03, .03, .03)))
    fe = g.voronoi(fw, 15.0)
    fmask = g.math('MULTIPLY', g.maprange(g.noise(P, 8.0, 2, .5), .4, .54), crack)
    fine_crk = g.math('MULTIPLY', g.maprange(fe, .006, .0), fmask)
    lip = g.math('MULTIPLY', g.maprange(fe, .022, .008), fmask)
    col = g.mix(g.math('MULTIPLY', lip, .3), col, tuple(c * 1.4 for c in light))
    col = g.mix(g.math('MULTIPLY', fine_crk, .85), col, tuple(c * .5 for c in dark))
    ao = g.ao(.06)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.3, .28, .32)), (1, (1, 1, 1))]))
    e = g.edge(.006)
    col = g.mix(g.math('MULTIPLY', e, .5), col, tuple(min(1, c * 1.45) for c in light))
    if lichen:
        li = g.math('MULTIPLY', g.maprange(g.noise(P, 78.0, 3, .6), .6, .68), g.maprange(g.noise(P, 3.5, 2, .5), .45, .6))
        col = g.mix(g.math('MULTIPLY', li, lichen), col, (.17, .17, .07))
    col, below = _wet(g, col, Z, P, wet_z)
    mh = None
    if moss:
        col, mm_, fine = _moss(g, col, P, ao, up, Z, moss)
        mh = g.math('MULTIPLY', mm_, g.math('ADD', .6, g.math('MULTIPLY', fine, .8)))
    rough = g.math('SUBTRACT', .82, g.math('MULTIPLY', e, .12)) if below is None else g.math('SUBTRACT', .84, g.math('MULTIPLY', below, .3))
    h = g.math('ADD', g.math('ADD', g.math('MULTIPLY', d2, .4), g.math('MULTIPLY', crk, -.9)), g.math('MULTIPLY', big, .5))
    h = g.math('ADD', h, g.math('ADD', g.math('MULTIPLY', d0, .55), g.math('ADD', g.math('MULTIPLY', fine_crk, -.8), g.math('MULTIPLY', pit, -.35))))
    if mh is not None: h = g.math('ADD', h, g.math('MULTIPLY', mh, .9))
    tm._finish(g, col, rough, 0.0, g.bump(h, .72, .006), spec=.28)
    return m


def wood(name, dark, light, slot='Main', wet_z=None, ground_h=.1, moss=False, polish=0., holes=0., grey=.3, moss_amt=.6):
    """Weathered timber on grain coordinates: long streaks, per-board tint, knots, worn edges. Optional water
    mark, ground grime, a hand-polished sheen (polish) and scattered old nail holes (holes)."""
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1, 1, 1))
    P, Z, up = _p(g)
    long = g.noise(g.vmath('MULTIPLY', co, (.35, 5, 5)), 1.6, 3, .5)
    streak = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.25, 22, 22)), 1.0, 2, .5), .35, .7)
    fibre = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.4, 70, 70)), 1.0, 2, .5), .4, .62)
    dab = dabs(g, g.vmath('MULTIPLY', co, (.5, 3, 3)), 9.0)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', long, .34), g.math('MULTIPLY', streak, .36)),
               g.math('ADD', g.math('MULTIPLY', r, .18), g.math('MULTIPLY', dab, .12)))
    mid = tuple((a + b) / 2 for a, b in zip(dark, light))
    col = g.ramp(t, [(.2, tuple(c * .7 for c in dark)), (.42, dark), (.62, mid), (.85, light)])
    col = g.mix(g.math('MULTIPLY', fibre, .2), col, tuple(c * .65 for c in dark))
    lines = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.22, 95, 95)), 1.0, 3, .55), .56, .66)
    col = g.mix(g.math('MULTIPLY', lines, .78), col, tuple(c * .42 for c in dark))
    fine_lines = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.3, 210, 210)), 1.0, 2, .5), .54, .66)
    col = g.mix(g.math('MULTIPLY', fine_lines, .45), col, tuple(c * .55 for c in dark))
    if grey:
        col = g.mix(g.math('MULTIPLY', g.maprange(g.noise(P, 1.8, 2, .5), .5, .72), grey), col, (.17, .16, .15))
    kn = g.math('MULTIPLY', g.maprange(g.voronoi(g.vmath('MULTIPLY', co, (1.2, 6, 6)), 1.0, 'F1', 'Distance'), .08, .02),
                g.maprange(g.noise(co, 3.0, 2, .5), .6, .7))
    col = g.mix(g.math('MULTIPLY', kn, .7), col, tuple(c * .45 for c in dark))
    hole = None
    if holes:
        hole = g.math('MULTIPLY', g.maprange(g.voronoi(P, 11.0, 'F1', 'Distance'), .06, .035), holes)
        col = g.mix(hole, col, (.018, .014, .012))
    col, below = _wet(g, col, Z, P, wet_z, .7, drip=.14, band_amt=.14)
    if ground_h: col = mm.ground(g, col, Z, P, ground_h, moss)
    ao = g.ao(.05)
    if moss:
        col, _, _ = _moss(g, col, P, ao, up, Z, moss_amt)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.3, .27, .28)), (1, (1, 1, 1))]))
    e = g.edge(.004)
    col = g.mix(g.math('MULTIPLY', e, .6), col, tuple(min(1, c * 1.55 + .04) for c in light))
    rough = g.math('SUBTRACT', .78, g.math('MULTIPLY', e, .15))
    if polish:
        rough = g.math('SUBTRACT', rough, polish)
        col = g.mix(polish * .8, col, tuple(min(1, c * 1.3) for c in light))
    h = g.math('ADD', g.math('ADD', g.math('MULTIPLY', streak, .6), g.math('MULTIPLY', kn, -.5)), g.math('SUBTRACT', g.math('MULTIPLY', fibre, .25), g.math('ADD', g.math('MULTIPLY', lines, .7), g.math('MULTIPLY', fine_lines, .3))))
    if hole is not None: h = g.math('SUBTRACT', h, g.math('MULTIPLY', hole, .8))
    tm._finish(g, col, rough, 0.0, g.bump(h, .42 - polish * .9, .0022), spec=.3)
    return m


def culm(name, green=(.06, .085, .02), straw=(.21, .16, .055), mud_h=.45, slot='Main'):
    """Bamboo culm on its 'bam' attribute: olive skin fading to straw, dark node rings with a waxy pale band, muddy feet."""
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1, 1, 1))
    P, Z, up = _p(g)
    B = g.attr('bam'); bs = g.node('ShaderNodeSeparateXYZ'); g.link(B, bs.inputs[0])
    dn, pr = bs.outputs['X'], bs.outputs['Z']
    streak = g.maprange(g.noise(g.vmath('MULTIPLY', co, (.3, 46, 46)), 1.0, 2, .5), .3, .7)
    blot = g.noise(g.vmath('MULTIPLY', co, (.9, 5, 5)), 2.0, 3, .5); dab = dabs(g, g.vmath('MULTIPLY', co, (.7, 9, 9)), 7.0)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', blot, .55), g.math('MULTIPLY', pr, .22)), g.math('MULTIPLY', dab, .23))
    mid = tuple((a + b) / 2 for a, b in zip(green, straw))
    col = g.ramp(t, [(.28, green), (.5, mid), (.74, straw)])
    col = g.mix(g.math('MULTIPLY', streak, .22), col, tuple(c * .65 for c in green))
    ring = g.maprange(dn, .009, .002)
    wax = g.maprange(dn, .05, .012)
    col = g.mix(g.math('MULTIPLY', wax, .2), col, (.2, .19, .12))
    col = g.mix(g.math('MULTIPLY', ring, .85), col, (.06, .042, .02))
    col = g.mix(g.math('MULTIPLY', g.maprange(g.noise(P, 18.0, 3, .5), .5, .64), .72), col, (.07, .05, .026))
    ao = g.ao(.03)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.3, .27, .28)), (1, (1, 1, 1))]))
    if mud_h:
        edge = g.math('ADD', Z, g.math('MULTIPLY', g.math('SUBTRACT', g.noise(P, 14.0, 3, .6), .5), .22))
        mud = g.maprange(edge, mud_h, mud_h * .25)
        col = g.mix(g.math('MULTIPLY', mud, .92), col, g.ramp(g.noise(P, 26.0, 3, .5), [(.35, (.05, .032, .018)), (.65, (.12, .08, .045))]))
        col, _, _ = _moss(g, col, P, ao, up, Z, .55, low_z=.2)
    e = g.edge(.003)
    col = g.mix(g.math('MULTIPLY', e, .45), col, tuple(min(1, c * 1.5) for c in straw))
    tm._finish(g, col, g.math('ADD', .5, g.math('MULTIPLY', blot, .2)), 0.0,
               g.bump(g.math('ADD', g.math('MULTIPLY', streak, .35), g.math('MULTIPLY', ring, -.6)), .25, .0012), spec=.38)
    return m


def canvas(name, base=(.4, .3, .165), stain=(.17, .1, .04), slot='Main', seams=(), faded=.4, dirt=.9):
    """Sun-faded canvas on 'cuv': pale washed centre, tea-brown water stains with soft blooms, darker hem, stitched seams."""
    base = tuple(c * .74 for c in base)      # same reason as stone(): it must still read as old cloth in full sun
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    C = g.attr('cuv'); cs = g.node('ShaderNodeSeparateXYZ'); g.link(C, cs.inputs[0])
    u, v = cs.outputs['X'], cs.outputs['Y']
    w1 = g.wave(P, 620.0, 1.0, 'BANDS', 'X', 1); w2 = g.wave(P, 620.0, 1.0, 'BANDS', 'Y', 1)
    big = g.noise(P, 1.4, 3, .5); d = dabs(g, P, 7.0); d2 = dabs(g, P, 24.0)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', big, .55), g.math('MULTIPLY', d, .3)), g.math('MULTIPLY', d2, .15))
    col = g.ramp(t, [(.3, tuple(c * .74 for c in base)), (.55, base), (.76, tuple(min(1, c * 1.2) for c in base))])
    if faded:
        col = g.mix(g.math('MULTIPLY', g.maprange(g.noise(P, 2.3, 3, .55), .5, .68), faded), col, tuple(min(1, c * 1.32 + .02) for c in base))
    if dirt:
        n = g.noise(P, 3.1, 5, .62)
        st = g.maprange(n, .56, .6)                                   # hard bloom edge of a dried water stain
        inner = g.maprange(n, .56, .72, .9, .3)
        col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', st, inner), dirt), col, stain)
        spots = g.math('MULTIPLY', g.maprange(g.noise(P, 26.0, 3, .55), .6, .68), .55)
        col = g.mix(spots, col, tuple(c * .8 for c in stain))
    du = g.math('MINIMUM', u, g.math('SUBTRACT', 1.0, u)); dv = g.math('MINIMUM', v, g.math('SUBTRACT', 1.0, v))
    hem = g.maprange(g.math('MINIMUM', du, dv), .035, .004)
    col = g.mix(g.math('MULTIPLY', hem, .55), col, tuple(c * .55 for c in stain))
    seam_h = None
    for s_u in seams:
        s = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', u, s_u)), .005, .001)
        col = g.mix(g.math('MULTIPLY', s, .55), col, tuple(c * .5 for c in stain))
        seam_h = g.math('ADD', seam_h, s) if seam_h is not None else s
    ao = g.ao(.08)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.42, .4, .44)), (1, (1, 1, 1))]))
    h = g.math('ADD', g.math('MULTIPLY', g.math('ADD', w1, w2), .4), g.math('MULTIPLY', d2, .3))
    if seam_h is not None: h = g.math('ADD', h, g.math('MULTIPLY', seam_h, 1.2))
    tm._finish(g, col, .92, 0.0, g.bump(h, .22, .0012), sheen=.4, spec=.2)
    return m


def tile(name, base=(.03, .042, .055), light=(.078, .096, .11), moss=.8, slot='Main'):
    m, g = tm._new(name, slot)
    co, r = tm._grain_coords(g, (1, 1, 1))
    P, Z, up = _p(g)
    n = g.noise(P, 7.0, 3, .5); d = dabs(g, P, 30.0)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', n, .5), g.math('MULTIPLY', d, .2)), g.math('MULTIPLY', r, .3))
    col = g.ramp(t, [(.3, tuple(c * .72 for c in base)), (.52, base), (.74, light)])
    streak = g.maprange(g.noise(g.vmath('MULTIPLY', co, (1.0, 26, 26)), 3.0, 2, .5), .55, .7)
    col = g.mix(g.math('MULTIPLY', streak, .3), col, (.11, .1, .08))      # lime and rain streaks
    ao = g.ao(.06)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.2, .2, .26)), (1, (1, 1, 1))]))
    e = g.edge(.004)
    col = g.mix(g.math('MULTIPLY', e, .5), col, tuple(min(1, c * 1.5 + .02) for c in light))
    if moss:
        col, _, _ = _moss(g, col, P, ao, up, g.val(9.0), moss)
    tm._finish(g, col, g.math('ADD', .6, g.math('MULTIPLY', n, .15)), 0.0, g.bump(g.math('ADD', d, g.math('MULTIPLY', n, .6)), .3, .002), spec=.3)
    return m


def paper(name, base=(.5, .35, .165), edge=(.2, .11, .04), age=.5, slot='Main'):
    """Blank aged paper on 'cuv': no marks that could read as writing, only soft foxing, a browned rim and fibres."""
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    C = g.attr('cuv'); cs = g.node('ShaderNodeSeparateXYZ'); g.link(C, cs.inputs[0])
    u, v = cs.outputs['X'], cs.outputs['Y']
    big = g.noise(P, 5.0, 3, .5); fib = g.noise(P, 240.0, 3, .6); d = g.noise(P, 26.0, 4, .6)
    t = g.math('ADD', g.math('MULTIPLY', big, .6), g.math('MULTIPLY', d, .4))
    col = g.ramp(t, [(.32, tuple(c * .84 for c in base)), (.6, base), (.76, tuple(min(1, c * 1.14) for c in base))])
    du = g.math('MINIMUM', u, g.math('SUBTRACT', 1.0, u)); dv = g.math('MINIMUM', v, g.math('SUBTRACT', 1.0, v))
    rim = g.math('ADD', g.math('MINIMUM', du, dv), g.math('MULTIPLY', g.math('SUBTRACT', g.noise(P, 22.0, 3, .5), .5), .05))
    col = g.mix(g.math('MULTIPLY', g.maprange(rim, .03 + .1 * age, .0), .85), col, edge)
    fox = g.math('MULTIPLY', g.maprange(g.noise(P, 18.0, 4, .6), .6, .66), age)
    col = g.mix(g.math('MULTIPLY', fox, .55), col, tuple(c * .9 for c in edge))
    col = g.mix(g.math('MULTIPLY', fib, .08), col, tuple(c * .7 for c in base))
    ao = g.ao(.02)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.5, .46, .44)), (1, (1, 1, 1))]))
    tm._finish(g, col, .9, 0.0, g.bump(g.math('ADD', fib, g.math('MULTIPLY', big, .8)), .16, .0009), sheen=.15, spec=.2)
    return m


def clay(name, body=(.2, .105, .05), glaze=(.11, .055, .028), slot='Main'):
    """Coarse clay bowl: dark treacle glaze ('gmask' 1), bare speckled body at the foot and rim ('gmask' 0)."""
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    n = g.noise(P, 34.0, 3, .5); d = g.noise(P, 90.0, 3, .55); sp = g.maprange(g.noise(P, 300.0, 2, .5), .62, .7)
    bodyc = g.mix(g.math('MULTIPLY', sp, .5), g.ramp(n, [(.3, tuple(c * .75 for c in body)), (.7, tuple(min(1, c * 1.25) for c in body))]), (.05, .03, .02))
    glz = g.ramp(g.math('ADD', g.math('MULTIPLY', n, .5), g.math('MULTIPLY', d, .5)), [(.3, tuple(c * .7 for c in glaze)), (.7, tuple(min(1, c * 1.5) for c in glaze))])
    mask = g.attr('gmask', 'Fac')
    col = g.mix(mask, bodyc, glz)
    ao = g.ao(.02)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.45, .42, .42)), (1, (1, 1, 1))]))
    e = g.edge(.0015)
    col = g.mix(g.math('MULTIPLY', e, .55), col, tuple(min(1, c * 1.6) for c in body))
    rgh = g.math('ADD', g.math('MULTIPLY', mask, .28), g.math('MULTIPLY', g.math('SUBTRACT', 1.0, mask), .8))
    tm._finish(g, col, rgh, 0.0, g.bump(g.math('ADD', n, sp), .2, .0006), spec=.42)
    return m


def porcelain(name, slot='Main', white=(.72, .71, .63), blue=(.05, .1, .24)):
    """The forgotten cup: cream glaze, plain blue bands (no pattern that could read as text), tea stain, crazing."""
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    B = g.attr('cupv', 'Fac')                     # 0 foot .. 1 rim
    n = g.noise(P, 40.0, 3, .5)
    col = g.ramp(n, [(.3, tuple(c * .9 for c in white)), (.7, white)])
    wob = g.math('MULTIPLY', g.math('SUBTRACT', g.noise(P, 60.0, 2, .5), .5), .08)
    bv = g.math('ADD', B, wob)
    band = g.math('MAXIMUM', g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', bv, .84)), .05, .02), g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', bv, .22)), .03, .012))
    col = g.mix(g.math('MULTIPLY', band, .85), col, blue)
    cr = g.maprange(g.voronoi(P, 90.0), .012, .0)
    col = g.mix(g.math('MULTIPLY', cr, g.math('MULTIPLY', g.maprange(g.noise(P, 12.0, 2, .5), .5, .6), .55)), col, (.2, .13, .07))
    ao = g.ao(.015)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.25, .15, .08)), (1, (1, 1, 1))]))     # old tea settled inside
    tm._finish(g, col, g.math('ADD', .22, g.math('MULTIPLY', n, .12)), 0.0, g.bump(cr, -.1, .0003), coat=.3, spec=.5)
    return m


def tea(name, slot='Main'):
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    n = g.noise(P, 12.0, 2, .5)
    col = g.ramp(n, [(.3, (.05, .022, .007)), (.7, (.1, .05, .015))])
    tm._finish(g, col, .12, 0.0, g.bump(n, .05, .001), spec=.5)
    return m


def thatch(name, dark=(.075, .055, .03), light=(.3, .235, .125), slot='Main'):
    """Straw laid from peak to eave: streaks run down the slope (around the Z axis), bundles in large soft patches."""
    m, g = tm._new(name, slot)
    P = g.geo('Position'); sep = g.node('ShaderNodeSeparateXYZ'); g.link(P, sep.inputs[0])
    X, Y, Z = sep.outputs['X'], sep.outputs['Y'], sep.outputs['Z']
    ang = g.math('ARCTAN2', Y, X)
    q = g.node('ShaderNodeCombineXYZ'); g.link(g.math('MULTIPLY', ang, 12.0), q.inputs[0]); g.link(g.math('MULTIPLY', Z, .55), q.inputs[1])
    Q = q.outputs[0]
    strand = g.noise(Q, 34.0, 4, .6); bundle = g.noise(Q, 6.0, 3, .55); big = g.noise(P, 1.6, 3, .5)
    t = g.math('ADD', g.math('ADD', g.math('MULTIPLY', strand, .5), g.math('MULTIPLY', bundle, .28)), g.math('MULTIPLY', big, .22))
    col = g.ramp(t, [(.3, tuple(c * .6 for c in dark)), (.46, dark), (.66, light)])
    grey = g.maprange(big, .45, .62)
    col = g.mix(g.math('MULTIPLY', grey, .3), col, (.17, .155, .12))
    ao = g.ao(.08)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.3, .28, .26)), (1, (1, 1, 1))]))
    tm._finish(g, col, .92, 0.0, g.bump(strand, .9, .012), spec=.12)
    return m


def fern(name, slot='Main'):
    """Lit green fronds: the moss ramp reads black on a thin leaf."""
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    n = g.noise(P, 34.0, 3, .6)
    col = g.ramp(n, [(.3, (.055, .1, .03)), (.55, (.13, .22, .06)), (.8, (.23, .34, .1))])
    tm._finish(g, col, .75, 0.0, g.bump(n, .4, .002), spec=.2)
    return m


def weed_leaf(name, base, mid, tip, slot='Main'):
    """Waterweed leaf on 'cuv': deep green where it leaves the stem, clear yellow-green along the blade, a touch of teal at the tip and rims."""
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    C = g.attr('cuv'); cs = g.node('ShaderNodeSeparateXYZ'); g.link(C, cs.inputs[0])
    u, v = cs.outputs['X'], cs.outputs['Y']
    col = g.ramp(v, [(.05, base), (.45, mid), (.78, mid), (1., tip)])
    rim = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', u, .5)), .32, .5)
    col = g.mix(g.math('MULTIPLY', rim, .22), col, tip)
    n = g.noise(P, 60.0, 2, .5)
    tm._finish(g, col, .62, 0.0, g.bump(n, .05, .001), spec=.12)
    return m


def moss_tuft(name, slot='Main', soft=False):
    if soft:
        m, g = tm._new(name, slot)
        P, Z, up = _p(g)
        n = g.noise(P, 34.0, 3, .6); d = dabs(g, P, 50.0)
        col = g.ramp(g.math('ADD', g.math('MULTIPLY', n, .6), g.math('MULTIPLY', d, .4)), [(.3, (.026, .036, .016)), (.55, (.06, .082, .032)), (.85, (.13, .15, .065))])
        ao = g.ao(.02)
        col = g.mul(1.0, col, g.ramp(ao, [(0, (.4, .42, .4)), (1, (1, 1, 1))]))
        tm._finish(g, col, .92, 0.0, g.bump(n, .6, .004), spec=.12)
        return m
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    n = g.noise(P, 60.0, 3, .6); d = dabs(g, P, 90.0)
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', n, .6), g.math('MULTIPLY', d, .4)), [(.3, (.016, .036, .009)), (.55, (.04, .075, .014)), (.85, (.11, .15, .03))])
    ao = g.ao(.02)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.35, .4, .35)), (1, (1, 1, 1))]))
    tm._finish(g, col, .9, 0.0, g.bump(n, .6, .003), spec=.15)
    return m


def lime_plaster(name, base=(.36, .3, .21), grime=(.15, .115, .075), lath=(.115, .08, .05), plinth=.6, slot='Main'):
    """Old lime wall, kept to the same tone as H01: uneven trowelled coats, rain streaks under the eaves, damp and dirt rising from the plinth, hairline cracks, a few spots where the coat fell off the lath."""
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    big = g.noise(P, 1.5, 4, .55); mid = g.noise(P, 7.0, 4, .55); fine = g.noise(P, 60.0, 3, .55)
    t = g.math('ADD', g.math('MULTIPLY', big, .6), g.math('MULTIPLY', mid, .4))
    col = g.ramp(t, [(.34, tuple(c * .74 for c in base)), (.52, base), (.7, tuple(min(1, c * 1.2) for c in base))])
    streak = g.math('MULTIPLY', g.maprange(g.wave(P, 7.0, 2.5, 'BANDS', 'X', 4), .55, .85), g.maprange(g.wave(P, 7.0, 2.5, 'BANDS', 'Y', 4), .4, .8, .5, 1.))
    col = g.mix(g.math('MULTIPLY', streak, .34), col, tuple(c * .62 for c in base))
    damp = g.maprange(g.math('ADD', Z, g.math('MULTIPLY', big, .5)), plinth + .25, plinth + .95, 1., 0.)
    col = g.mix(g.math('MULTIPLY', damp, .75), col, grime)
    crack = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', g.noise(P, 5.0, 3, .6), .5)), .004, .0, 0., 1.)
    col = g.mix(g.math('MULTIPLY', crack, .55), col, tuple(c * .5 for c in grime))
    fallen = g.maprange(g.noise(P, 2.6, 4, .6), .685, .7)
    col = g.mix(fallen, col, lath)
    ao = g.ao(.05)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.45, .43, .4)), (1, (1, 1, 1))]))
    tm._finish(g, col, .9, 0.0, g.bump(g.math('ADD', g.math('MULTIPLY', mid, .6), g.math('MULTIPLY', fine, .4)), .55, .01), spec=.15)
    return m


def packed_earth(name, dark=(.032, .022, .013), light=(.098, .066, .04), rough=.85, wet_top=.17, wet_low=.11, dry_low=.3, dry_top=.4, slot='Main'):
    """Banked ditch earth: wet and dark up to the water mark, layered where it was cut, sun-dried and paler along the top, small stones showing through."""
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    big = g.noise(P, 3.2, 4, .58); fine = g.noise(P, 42.0, 4, .6); grit = g.noise(P, 160.0, 2, .5)
    t = g.math('ADD', g.math('MULTIPLY', big, .65), g.math('MULTIPLY', fine, .35))
    col = g.ramp(t, [(.34, dark), (.68, light)])
    strata = g.wave(P, 16.0, 2.2, 'BANDS', 'Z', 3)
    col = g.mix(g.math('MULTIPLY', g.maprange(strata, .35, .75), .3), col, tuple(c * .62 for c in light))
    dry = g.maprange(Z, dry_low, dry_top)
    col = g.mix(g.math('MULTIPLY', dry, .55), col, tuple(min(1, c * 1.32 + .012) for c in light))
    wet = g.maprange(Z, wet_top, wet_low)
    wet_edge = g.math('MULTIPLY', wet, g.maprange(big, .3, .6, 1., .75))
    col = g.mix(g.math('MULTIPLY', wet_edge, .8), col, tuple(c * .62 for c in dark))
    stones = g.math('MULTIPLY', g.maprange(g.noise(P, 74.0, 2, .5), .7, .74), .45)
    col = g.mix(stones, col, (.085, .07, .05))
    ao = g.ao(.04)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.45, .42, .4)), (1, (1, 1, 1))]))
    tm._finish(g, col, g.maprange(Z, wet_low, wet_top, .38, rough), 0.0, g.bump(g.math('ADD', g.math('MULTIPLY', fine, .7), g.math('MULTIPLY', grit, .3)), .5, .006), spec=.4)
    return m


def mud(name, dark=(.022, .016, .01), light=(.09, .062, .036), rough=.7, slot='Main'):
    """Wet creek silt or packed earth: dark, lumpy, gleaming where it is wettest."""
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    big = g.noise(P, 3.2, 4, .58); fine = g.noise(P, 42.0, 4, .6); grit = g.noise(P, 160.0, 2, .5)
    t = g.math('ADD', g.math('MULTIPLY', big, .65), g.math('MULTIPLY', fine, .35))
    col = g.ramp(t, [(.34, dark), (.68, light)])
    col = g.mix(g.math('MULTIPLY', g.maprange(grit, .62, .7), .2), col, tuple(c * 1.4 for c in light))
    ao = g.ao(.04)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.45, .42, .4)), (1, (1, 1, 1))]))
    wet = g.maprange(big, .42, .62, rough, min(.95, rough + .4))
    tm._finish(g, col, wet, 0.0, g.bump(g.math('ADD', g.math('MULTIPLY', fine, .7), g.math('MULTIPLY', grit, .3)), .5, .006), spec=.45)
    return m
