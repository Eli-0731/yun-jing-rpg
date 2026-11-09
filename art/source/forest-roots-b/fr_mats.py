"""FR materials: old root bark, pale exposed root tips, forest earth. Hand-painted direction (large soft shifts, a few brush dabs),
baked to one atlas per asset like the rest of the B kits. Colours stay in the style guide's warm-brown range; greens at or below
about 0.12 linear albedo (studio note in the procedural-modelling memory).

bark() reads the per-vertex 'bark' attribute written by fr_parts.sweep: x = metres along the root, y = metres round it,
z = fissure 0..1 (1 = the floor of a deep crack, already cut into the mesh). Plates and the fine lines between them are laid out
in that along/round space, so they follow every root however it bends; moss, earth and wear come from the world position and normal.
"""
import ti_mats as tm
from mk_mats import dabs
from cr_mats import _p


def _sep(g, sock):
    s = g.node('ShaderNodeSeparateXYZ'); g.link(sock, s.inputs[0]); return s.outputs['X'], s.outputs['Y'], s.outputs['Z']


def _xyz(g, x, y, z):
    c = g.node('ShaderNodeCombineXYZ'); g._in(c.inputs[0], x); g._in(c.inputs[1], y); g._in(c.inputs[2], z); return c.outputs[0]


def bark(name, tone=1., moss=1., slot='Main', ground_h=.35):
    m, g = tm._new(name, slot)
    P, Zp, up = _p(g)
    s, a, F = _sep(g, g.attr('bark'))
    nx, ny, nz = _sep(g, g.geo('Normal'))
    k = lambda c, f=1.: tuple(min(1., v * tone * f) for v in c)
    dark, mid, light, worn = k((.03, .019, .012)), k((.07, .045, .026)), k((.13, .086, .05)), k((.2, .14, .088))
    # bark plates: long in the along direction, a few across
    plate_uv = _xyz(g, g.math('MULTIPLY', a, 3.2), g.math('MULTIPLY', s, .55), g.math('MULTIPLY', Zp, .2))
    big = g.noise(plate_uv, 1.0, 4, .55)
    d1 = dabs(g, _xyz(g, g.math('MULTIPLY', a, 2.), g.math('MULTIPLY', s, .5), 0.), 6.0)
    d2 = dabs(g, P, 24.0)
    t = g.math('ADD', g.math('MULTIPLY', big, .55), g.math('ADD', g.math('MULTIPLY', d1, .28), g.math('MULTIPLY', d2, .17)))
    col = g.ramp(t, [(.25, dark), (.48, mid), (.75, light)])
    # fine fissure lines between plates (thin, dark), long streaks of grey weathering on the plate faces
    # long wavy lines: where a noise stretched along the root crosses its middle value
    lines = g.noise(_xyz(g, g.math('MULTIPLY', a, 9.), g.math('MULTIPLY', s, .7), g.math('MULTIPLY', Zp, .2)), 1.0, 3, .5)
    fl = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', lines, .5)), .035, .0)
    col = g.mix(g.math('MULTIPLY', fl, .8), col, tuple(c * .4 for c in dark))
    streak = g.maprange(g.noise(_xyz(g, g.math('MULTIPLY', a, 14.), g.math('MULTIPLY', s, .9), 0.), 1.0, 3, .5), .55, .7)
    col = g.mix(g.math('MULTIPLY', streak, .35), col, k((.2, .17, .14)))
    # the deep cracks cut into the mesh: near black-brown at the floor, a warm lip on the plate edge beside them
    crack = g.maprange(F, .25, .8)
    col = g.mix(g.math('MULTIPLY', crack, .85), col, k((.02, .013, .009)))
    lip = g.math('MULTIPLY', g.maprange(F, .08, .22), g.maprange(F, .4, .25))
    col = g.mix(g.math('MULTIPLY', lip, .35), col, k((.24, .15, .08)))
    # smooth worn upper ridges: lighter, warmer, finer where the root faces up and the bark is not cracked
    wv = g.math('MULTIPLY', g.maprange(nz, .7, .97), g.maprange(F, .25, .05))
    wv = g.math('MULTIPLY', wv, g.maprange(g.noise(P, 2.2, 3, .5), .35, .6))
    col = g.mix(g.math('MULTIPLY', wv, .45), col, worn)
    # pale lichen flecks
    li = g.math('MULTIPLY', g.maprange(g.noise(P, 60.0, 3, .6), .62, .7), g.maprange(g.noise(P, 3.0, 2, .5), .5, .62))
    col = g.mix(g.math('MULTIPLY', li, .55), col, (.2, .2, .13))
    ao = g.ao(.08)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.32, .28, .3)), (1, (1, 1, 1))]))
    # earth grime up from the ground, wet-dark at the foot
    dirt = g.math('MULTIPLY', g.maprange(Zp, ground_h, .02), g.maprange(g.noise(P, 4.0, 3, .5), .25, .6))
    col = g.mix(g.math('MULTIPLY', dirt, .75), col, (.05, .034, .021))
    # moss: thick on the shaded back (+Y) and on top, thin on the front; broken by a big and a clumpy noise; also in the cracks low down
    side = g.math('ADD', g.math('MULTIPLY', g.maprange(ny, -.1, .7), .9), g.math('MULTIPLY', g.maprange(nz, .55, .95), .55))
    side = g.math('ADD', side, g.math('MULTIPLY', g.math('MULTIPLY', crack, g.maprange(Zp, 1.2, .2)), .35))
    bigm = g.noise(P, 1.6, 4, .55); fine = g.noise(P, 38.0, 3, .6); clump = g.maprange(g.noise(P, 80.0, 3, .65), .38, .56)
    mm = g.math('MULTIPLY', g.math('ADD', side, g.math('MULTIPLY', g.maprange(bigm, .38, .66), .7)), moss)
    mm = g.math('ADD', mm, g.math('MULTIPLY', g.math('ADD', g.math('MULTIPLY', fine, .5), g.math('MULTIPLY', clump, .5)), .45))
    mm = g.math('MULTIPLY', g.maprange(mm, 1.0, 1.18), g.maprange(wv, .5, .15))      # not on the worn tops
    mtone = g.ramp(g.math('ADD', g.math('MULTIPLY', fine, .6), g.math('MULTIPLY', bigm, .4)),
                   [(.3, (.02, .028, .009)), (.55, (.045, .062, .016)), (.82, (.1, .118, .03))])
    col = g.mix(mm, col, mtone)
    rough = g.math('SUBTRACT', .86, g.math('MULTIPLY', wv, .22))
    h = g.math('ADD', g.math('MULTIPLY', big, .5), g.math('ADD', g.math('MULTIPLY', fl, -.9), g.math('MULTIPLY', streak, .15)))
    h = g.math('ADD', h, g.math('ADD', g.math('MULTIPLY', crack, -.6), g.math('MULTIPLY', g.math('MULTIPLY', mm, fine), 1.2)))
    tm._finish(g, col, rough, 0.0, g.bump(h, .7, .008), spec=.25)
    return m


def root_tip(name, slot='Main'):
    """Pale exposed root tips and fine rootlets: cream-brown, streaked along the root, earthy at the end."""
    m, g = tm._new(name, slot)
    P, Zp, up = _p(g)
    s, a, F = _sep(g, g.attr('bark'))
    st = g.noise(_xyz(g, g.math('MULTIPLY', a, 30.), g.math('MULTIPLY', s, 1.5), 0.), 1.0, 3, .5)
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', st, .7), g.math('MULTIPLY', dabs(g, P, 30.0), .3)),
                 [(.25, (.13, .09, .055)), (.55, (.26, .19, .12)), (.85, (.37, .29, .19))])
    dirt = g.maprange(g.noise(P, 18.0, 3, .5), .5, .66)
    col = g.mix(g.math('MULTIPLY', dirt, .65), col, (.06, .04, .024))
    col = g.mix(g.math('MULTIPLY', g.maprange(Zp, .25, .02), .5), col, (.05, .034, .02))
    ao = g.ao(.03)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.45, .42, .4)), (1, (1, 1, 1))]))
    tm._finish(g, col, .8, 0.0, g.bump(st, .3, .001), spec=.25)
    return m


def forest_earth(name, slot='Main', moss=.8, trodden=0.):
    """Dark forest soil packed between the roots: humus, leaf-litter flecks, small stones showing, moss creeping over the upper slopes."""
    m, g = tm._new(name, slot)
    P, Zp, up = _p(g)
    big = g.noise(P, 2.6, 4, .58); fine = g.noise(P, 34.0, 4, .6); grit = g.noise(P, 150.0, 2, .5)
    t = g.math('ADD', g.math('MULTIPLY', big, .6), g.math('ADD', g.math('MULTIPLY', fine, .25), g.math('MULTIPLY', dabs(g, P, 14.0), .15)))
    col = g.ramp(t, [(.3, (.026, .018, .011)), (.55, (.05, .034, .02)), (.8, (.085, .06, .037))])
    # leaf litter: drifts of broken brown leaf, not dots (a fine noise thresholded inside a larger drift mask)
    lit = g.math('MULTIPLY', g.maprange(g.noise(P, 28.0, 4, .62), .52, .6), g.maprange(g.noise(P, 4.0, 3, .55), .45, .62))
    lc = g.ramp(g.noise(P, 70.0, 2, .5), [(.3, (.055, .033, .016)), (.7, (.11, .066, .028))])
    col = g.mix(g.math('MULTIPLY', lit, .7), col, lc)
    stones = g.math('MULTIPLY', g.maprange(g.noise(P, 60.0, 2, .5), .7, .74), .5)
    col = g.mix(stones, col, (.1, .095, .085))
    mv = g.math('MULTIPLY', g.maprange(up, .35, .8), g.maprange(g.noise(P, 3.0, 4, .6), .45, .58))
    mv = g.math('MULTIPLY', mv, moss)
    col = g.mix(g.math('MULTIPLY', mv, .85), col, g.ramp(fine, [(.35, (.025, .036, .01)), (.75, (.07, .09, .022))]))
    if trodden:   # packed by feet: darker, the litter pushed to the sides, a smoother sheen
        col = g.mix(trodden, col, g.ramp(big, [(.3, (.03, .022, .014)), (.7, (.06, .043, .027))]))
    ao = g.ao(.08)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.36, .33, .33)), (1, (1, 1, 1))]))
    h = g.math('ADD', g.math('MULTIPLY', fine, .7), g.math('ADD', g.math('MULTIPLY', grit, .3), g.math('MULTIPLY', lit, .3)))
    tm._finish(g, col, .9 - .15 * trodden, 0.0, g.bump(h, .6 - .3 * trodden, .006), spec=.2)
    return m


def heartwood(name, slot='Main'):
    """FR04 adzed walking surface and the sawn end: pale warm heartwood, adze scallops across the grain read from the 'adze'
    attribute (x = metres along the log, y = across), a darker foot-worn band down the middle, grime in the scallop floors."""
    m, g = tm._new(name, slot)
    P, Zp, up = _p(g)
    x, y, w = _sep(g, g.attr('adze'))
    grain = g.noise(_xyz(g, g.math('MULTIPLY', x, .6), g.math('MULTIPLY', y, 30.), g.math('MULTIPLY', Zp, 30.)), 1.0, 4, .5)
    fib = g.maprange(g.noise(_xyz(g, g.math('MULTIPLY', x, 1.2), g.math('MULTIPLY', y, 120.), g.math('MULTIPLY', Zp, 120.)), 1.0, 2, .5), .4, .62)
    # weathered hewn top: silver-brown, not fresh pale wood
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', grain, .7), g.math('MULTIPLY', dabs(g, P, 12.0), .3)),
                 [(.25, (.07, .056, .042)), (.55, (.12, .095, .068)), (.85, (.17, .14, .105))])
    col = g.mix(g.math('MULTIPLY', fib, .18), col, (.05, .038, .026))
    # adze bites: staggered dishes, each row's phase wandering across the width (no straight lines right across the log)
    bite = g.math('FRACT', g.math('ADD', g.math('MULTIPLY', x, 6.0), g.math('MULTIPLY', g.noise(_xyz(g, g.math('MULTIPLY', x, .8), g.math('MULTIPLY', y, 7.), 0.), 1.0, 2, .5), 1.6)))
    ridge = g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', bite, .5)), .42, .5)
    col = g.mix(g.math('MULTIPLY', ridge, .16), col, (.2, .17, .13))
    col = g.mix(g.math('MULTIPLY', g.maprange(g.math('ABSOLUTE', g.math('SUBTRACT', bite, .5)), .18, .0), .22), col, (.045, .034, .024))
    # the trodden line: darker, smoother, polished
    tr = g.math('MULTIPLY', g.maprange(g.math('ABSOLUTE', y), .2, .05), w)
    col = g.mix(g.math('MULTIPLY', tr, .5), col, (.085, .06, .036))
    # grey weathering at the edges of the cut face, moss creeping in from the bark
    edge = g.maprange(g.math('ABSOLUTE', y), .18, .3)
    col = g.mix(g.math('MULTIPLY', edge, .4), col, (.13, .12, .1))
    mo = g.math('MULTIPLY', g.maprange(g.math('ABSOLUTE', y), .24, .3), g.maprange(g.noise(P, 5.0, 3, .5), .45, .6))
    col = g.mix(g.math('MULTIPLY', mo, .8), col, (.04, .06, .015))
    ao = g.ao(.04)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.45, .4, .38)), (1, (1, 1, 1))]))
    rough = g.math('SUBTRACT', .8, g.math('MULTIPLY', tr, .2))
    h = g.math('ADD', g.math('MULTIPLY', ridge, .3), g.math('ADD', g.math('MULTIPLY', fib, .3), g.math('MULTIPLY', grain, .3)))
    tm._finish(g, col, rough, 0.0, g.bump(h, .5, .003), spec=.3)
    return m


def rings(name, slot='Main'):
    """FR04 sawn end: growth rings round the pith, radial checks, grey weathering towards the bark."""
    m, g = tm._new(name, slot)
    P, Zp, up = _p(g)
    x, y, w = _sep(g, g.attr('adze'))       # here x = radius from the pith (m), y = angle
    ring = g.wave(_xyz(g, g.math('MULTIPLY', x, 1.), 0., 0.), 22.0, 1.2, 'RINGS', 'X', 2)
    col = g.ramp(g.math('ADD', g.math('MULTIPLY', ring, .5), g.math('MULTIPLY', g.noise(P, 30.0, 3, .5), .5)),
                 [(.25, (.13, .085, .045)), (.6, (.25, .17, .09)), (.9, (.33, .235, .13))])
    chk = g.math('MULTIPLY', g.maprange(g.math('ABSOLUTE', g.math('SINE', g.math('MULTIPLY', y, 5.))), .06, .0), g.maprange(x, .05, .25))
    col = g.mix(g.math('MULTIPLY', chk, .85), col, (.03, .02, .012))
    col = g.mix(g.math('MULTIPLY', g.maprange(x, .25, .38), .5), col, (.16, .14, .11))
    ao = g.ao(.03)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.45, .4, .38)), (1, (1, 1, 1))]))
    tm._finish(g, col, .82, 0.0, g.bump(g.math('ADD', ring, g.math('MULTIPLY', chk, -1.)), .4, .002), spec=.3)
    return m
