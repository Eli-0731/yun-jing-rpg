"""Lay TE02_Hedge / TE02_HedgeShort / TE02_HedgeEnd along a planting-ridge polyline (used by the showcase and the diorama).

A run is a stretch of ridge with nothing in the way. It gets a HedgeEnd at each end (rounded tip pointing out of the run) and
2 m / 1 m open segments in between. When the lengths do not add up exactly the segments are pulled slightly together, so
neighbours overlap a few centimetres instead of leaving a gap. Each segment sits on the chord between its two arc positions,
its local +X along the run. Returns placements (id, x, y, yaw_deg) and the joints between two open ends (x, y, yaw_deg).
"""
import math

END, SEG, SHORT = 'TE02_HedgeEnd', 'TE02_Hedge', 'TE02_HedgeShort'


def _at(pts, cum, a):
    a = max(0., min(cum[-1], a))
    for i in range(1, len(cum)):
        if cum[i] >= a:
            t = (a - cum[i - 1]) / max(cum[i] - cum[i - 1], 1e-9)
            return (pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t)
    return pts[-1]


def _pose(pts, cum, a0, a1):
    p0, p1 = _at(pts, cum, a0), _at(pts, cum, a1)
    return ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))


def runs(samples):
    """samples: [(x, y, ok)] in order along the row -> list of point lists, one per stretch of ok samples."""
    out, cur = [], []
    for x, y, ok in samples:
        if ok: cur.append((x, y))
        elif cur: out.append(cur); cur = []
    if cur: out.append(cur)
    return out


def hedge_run(pts, min_len=1.6):
    cum = [0.]
    for i in range(1, len(pts)): cum.append(cum[-1] + math.dist(pts[i - 1], pts[i]))
    A = cum[-1]; place, joints = [], []
    if A < min_len: return place, joints
    mid = max(0., A - 2.)
    n2 = int(mid // 2.); rest = mid - 2. * n2
    n1 = 0 if rest < .15 else (1 if rest <= 1.15 else 2)
    if n1 == 2: n2, n1 = n2 + 1, 0
    lens = [2.] * n2 + [1.] * n1
    # spread the short pieces through the run instead of bunching them at one end
    if n1 and n2: lens = [2.] * (n2 // 2) + [1.] + [2.] * (n2 - n2 // 2)
    total = sum(lens); f = min(1., mid / total) if total else 1.
    # start end (rounded tip pointing back along the run), segments, finish end
    (cx, cy), yaw = _pose(pts, cum, 0., min(1., A / 2))
    place.append((END, cx, cy, yaw + 180.))
    a = 1. if A >= 2. else A / 2
    for L in lens:
        b = a + L * f
        (cx, cy), yaw = _pose(pts, cum, a, b)
        joints.append((*_at(pts, cum, a), yaw))
        place.append((SEG if L == 2. else SHORT, cx, cy, yaw)); a = b
    (cx, cy), yaw = _pose(pts, cum, max(A - 1., A / 2), A)
    joints.append((*_at(pts, cum, max(A - 1., A / 2)), yaw))
    place.append((END, cx, cy, yaw))
    return place, joints
