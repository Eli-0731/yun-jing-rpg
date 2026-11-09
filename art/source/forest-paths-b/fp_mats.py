"""FP forest-path materials. Hand-painted direction like the FR kit (large soft shifts, a few brush dabs), baked to one atlas per
piece. Greens stay at or below about 0.12-0.2 linear albedo, soil in the style guide's warm-brown range.

path_earth() reads the per-vertex 'pth' attribute written by fp_parts.slab: x = metres along the path centre line from the piece's
start, y = metres across it (0 = centre, + = left of the walking direction), z = height above the piece's ground. Every pattern is
laid out in (along, across) with the along coordinate wrapped round a circle of the piece's length, so the texture on the two end
lines is the same and any piece meets any other (FP01 straight, FP02 curves, FP03 slope ...) without a colour seam.
"""
import math
import ti_mats as tm
from mk_mats import dabs
from cr_mats import _p, weed_leaf


def _sep(g, sock):
    s = g.node('ShaderNodeSeparateXYZ'); g.link(sock, s.inputs[0]); return s.outputs['X'], s.outputs['Y'], s.outputs['Z']


def _xyz(g, x, y, z):
    c = g.node('ShaderNodeCombineXYZ'); g._in(c.inputs[0], x); g._in(c.inputs[1], y); g._in(c.inputs[2], z); return c.outputs[0]


def path_coords(g, length, stretch=1.):
    """(along, across) on a cylinder: along wrapped with period length, so both end lines read the same pattern."""
    s, t, z = _sep(g, g.attr('pth'))
    ang = g.math('MULTIPLY', s, math.tau / length); rad = length / math.tau * stretch
    # 'pth' across is the logical t of fp_parts (the old 1.6 m section); the noise runs on metres across (fp_parts.widen)
    at = g.math('ABSOLUTE', t)
    wm = g.math('ADD', g.math('MULTIPLY', g.math('MINIMUM', at, .38), .58 / .38), g.math('MAXIMUM', g.math('SUBTRACT', at, .38), 0.))
    Q = _xyz(g, g.math('MULTIPLY', g.math('COSINE', ang), rad), g.math('MULTIPLY', g.math('SINE', ang), rad), g.math('MULTIPLY', g.math('SIGN', t), wm))
    return Q, s, t, z


def path_earth(name, length, slot='Main'):
    """Packed dark-brown forest soil. Tread (|across| < 0.38 m): trodden smooth and a little paler, long scuffs running with the path,
    the worn centre line palest and least rough. Banks: loose humus with broken leaf litter, small grit, moss creeping in from the
    outer edge and over the bank crests."""
    m, g = tm._new(name, slot)
    Q, s, t, z = path_coords(g, length)
    Qs = g.vmath('MULTIPLY', Q, (.22, .22, 4.5))                        # stretched along the path: scuffs and wear streaks
    at = g.math('ABSOLUTE', t)
    big = g.noise(Q, 1.6, 4, .58); fine = g.noise(Q, 30.0, 4, .6); grit = g.noise(Q, 140.0, 2, .5)
    streak = g.math('ADD', g.math('MULTIPLY', g.noise(Qs, 9.0, 3, .55), .45), g.math('MULTIPLY', g.noise(Q, 9.0, 3, .6), .55))
    base = g.math('ADD', g.math('MULTIPLY', big, .6), g.math('ADD', g.math('MULTIPLY', fine, .25), g.math('MULTIPLY', dabs(g, Q, 12.0), .15)))
    col = g.ramp(base, [(.3, (.032, .018, .01)), (.55, (.058, .032, .017)), (.8, (.09, .052, .027))])
    # tread: packed, warmer and paler, scuffed lengthways
    tread = g.maprange(at, .42, .3)
    tc = g.ramp(g.math('ADD', g.math('MULTIPLY', streak, .55), g.math('MULTIPLY', big, .45)),
                [(.3, (.07, .036, .018)), (.55, (.1, .053, .026)), (.78, (.13, .072, .036))])
    col = g.mix(g.math('MULTIPLY', tread, .9), col, tc)
    # the worn centre line: palest, smoothest, a few darker damp foot-hollows along it
    centre = g.math('MULTIPLY', g.maprange(at, .16, .04), g.maprange(g.noise(Qs, 3.0, 2, .5), .3, .5))
    col = g.mix(g.math('MULTIPLY', centre, .5), col, (.15, .088, .046))
    hollow = g.math('MULTIPLY', g.maprange(g.noise(Q, 7.0, 2, .5), .62, .7), g.maprange(at, .3, .15))
    col = g.mix(g.math('MULTIPLY', hollow, .5), col, (.04, .022, .012))
    # crumbs and clods: dark specks and small pale crusts all over the packed soil
    clod = g.noise(Q, 70.0, 2, .5)
    col = g.mix(g.math('MULTIPLY', g.maprange(clod, .62, .68), .55), col, (.03, .017, .009))
    col = g.mix(g.math('MULTIPLY', g.maprange(clod, .36, .31), .35), col, (.16, .1, .055))
    # leaf litter crumbs on the banks and drifting onto the tread edges
    lit = g.math('MULTIPLY', g.maprange(g.noise(Q, 26.0, 4, .62), .5, .6), g.maprange(g.noise(Q, 3.4, 3, .55), .42, .6))
    lit = g.math('MULTIPLY', lit, g.maprange(at, .22, .45))
    lc = g.ramp(g.noise(Q, 60.0, 2, .5), [(.3, (.07, .036, .015)), (.7, (.16, .08, .028))])
    col = g.mix(g.math('MULTIPLY', lit, .75), col, lc)
    # grit and pea stones, kicked to the sides
    stones = g.math('MULTIPLY', g.maprange(g.noise(Q, 55.0, 2, .5), .7, .74), g.maprange(at, .1, .35, .25, .6))
    col = g.mix(stones, col, (.12, .112, .1))
    # moss creeping in from the outer edges and over the bank crests
    mv = g.math('MULTIPLY', g.maprange(at, .5, .72), g.maprange(g.noise(Q, 2.6, 4, .6), .36, .55))
    mv = g.math('MAXIMUM', mv, g.math('MULTIPLY', g.maprange(at, .72, .8), g.maprange(g.noise(Q, 4.5, 3, .6), .4, .56)))
    col = g.mix(g.math('MULTIPLY', mv, .9), col, g.ramp(fine, [(.35, (.028, .04, .012)), (.75, (.075, .1, .025))]))
    # a tall end (FP03 / FP05 top) is a cut through the bank: 'h' there is minus the depth below the tread. Under a 3 cm crust the
    # soil turns into a profile of level bands: black humus, brown loam, then paler clay with small stones, the bands wavering a little
    d = g.math('ADD', g.math('MULTIPLY', z, -1.), g.math('MULTIPLY', g.math('SUBTRACT', big, .5), .16))
    prof = g.ramp(d, [(.06, (.016, .01, .006)), (.2, (.022, .013, .008)), (.3, (.04, .024, .013)), (.6, (.05, .031, .017)),
                      (.75, (.075, .05, .027)), (1.2, (.085, .058, .032))])
    Ql = _xyz(g, g.math('MULTIPLY', t, 1.5), g.math('MULTIPLY', d, 14.), g.math('MULTIPLY', s, .3))     # thin level lenses
    lens = g.maprange(g.noise(Ql, 2.2, 3, .55), .45, .65)
    prof = g.mix(g.math('MULTIPLY', lens, .35), prof, g.mul(1.0, prof, (.6, .6, .6)))
    prof = g.mix(g.math('MULTIPLY', g.maprange(fine, .35, .7), .3), prof, g.mul(1.0, prof, (.75, .75, .75)))
    pebble = g.math('MULTIPLY', g.maprange(g.noise(Q, 22.0, 2, .5), .7, .74), g.maprange(d, .3, .5))
    prof = g.mix(g.math('MULTIPLY', pebble, .8), prof, (.055, .05, .043))
    cut = g.maprange(z, -.02, -.07)
    col = g.mix(cut, col, prof)
    # baked occlusion fades out over the last 0.25 m of each end: what lies near one end of this piece (a leaf, a fern) would
    # otherwise darken that end only, and the two ends would no longer match
    end = g.maprange(g.math('MINIMUM', s, g.math('SUBTRACT', length, s)), .25, .06)
    ao = g.math('MAXIMUM', g.ao(.07), end)
    col = g.mul(1.0, col, g.ramp(ao, [(0, (.42, .38, .37)), (1, (1, 1, 1))]))
    rough = g.math('SUBTRACT', .93, g.math('ADD', g.math('MULTIPLY', tread, .1), g.math('MULTIPLY', centre, .08)))
    h = g.math('ADD', g.math('MULTIPLY', fine, .55), g.math('ADD', g.math('MULTIPLY', grit, .3), g.math('ADD', g.math('MULTIPLY', lit, .35),
            g.math('MULTIPLY', g.math('MULTIPLY', streak, tread), .4))))
    tm._finish(g, col, rough, 0.0, g.bump(h, .55, .005), spec=.22)
    return m


def fern_leaf(name, old=False, slot='Main'):
    """Fern pinnae on 'cuv' (v = position along the frond 0..1): deep green at the stalk, clear green along the frond, yellow-green
    at the tip; old fronds tan to brown at the tip."""
    if old:
        return weed_leaf(name, (.04, .06, .015), (.12, .14, .035), (.2, .12, .04), slot=slot)
    return weed_leaf(name, (.025, .055, .012), (.07, .125, .028), (.15, .2, .045), slot=slot)


def fern_stem(name, slot='Main'):
    m, g = tm._new(name, slot)
    P, Z, up = _p(g)
    n = g.noise(P, 40.0, 2, .5)
    col = g.ramp(n, [(.3, (.05, .04, .016)), (.7, (.085, .075, .028))])
    tm._finish(g, col, .6, 0.0, None, spec=.2)
    return m


def fallen_leaf(name, tone, slot='Main'):
    """A dry fallen leaf: tone 'orange' (maple), 'brown' or 'yellow'; darker at the stalk and in the veins, paler at the edge."""
    C = {'orange': ((.13, .045, .014), (.3, .11, .025), (.36, .18, .045)),
         'brown': ((.06, .032, .014), (.12, .066, .028), (.17, .1, .045)),
         'yellow': ((.16, .09, .02), (.3, .19, .04), (.34, .25, .07))}[tone]
    return weed_leaf(name, *C, slot=slot)
