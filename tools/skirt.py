"""Skirt bones (roadmap 5, the owner 2026-10-01): hanging cloth that the legs push instead of passing through.

fo4-refit R-18 measured that weights alone cannot do it (linear blend skinning does not drape: following the legs moves
the clipping, 10-30% at best). So the engine adds a RING of skirt bones under Pelvis_skin at run time, as it adds the
genital bones (the women's skeleton has none), and moves them with its own small solver; Anatomy Tailor weights each
garment's hanging cloth to them. One file, three parts, the engine's C++ (fo4-ocbpc Skirt.cpp) mirroring the second:

1. THE RING (design): COLUMNS columns around the hips, LEVELS levels below the crotch. Each bone rests just outside the
   legs' convex outline at its level (MARGIN out), so cloth moves as soon as a leg reaches the ring and never later.
   Measured from a reference body in the skeleton's bind pose; written into the engine's [Bones] / [BonesMale].
2. THE SOLVER (run time): per frame, every bone swings (Verlet, damped) toward its rest under the pelvis, keeps its
   column's lengths and its neighbours' spacing, and is pushed out of the legs' capsules (thigh, calf). The push goes
   to the side the column faces (its outward direction plus a little world-up, across the leg's axis), never simply
   "away from the axis": an AAF scene snaps into its pose, a leg lands on top of a bone, and the nearest way out is the
   wrong one -- cloth behind the knee, the leg through it.
3. THE WEIGHTS (Tailor): a garment vertex below the crotch and off the skin (hanging, not a fitted trouser leg) takes
   a share of the skirt bones: bilinear between the two columns around its angle and the two levels around its
   height, ramping in from TOP above the crotch over RAMP, smoothed over the garment's edges. No skirt bones, no change:
   a garment without hanging cloth gets no skirt variant.

    python tools/skirt.py design                  # measure both rings, print physics_design's SKIRT_* constants
"""
import math
import pathlib
import struct
import sys

import numpy as np

COLUMNS = 12                              # every 30 degrees; column 0 at the front (+y), then toward +x
LEVELS = (2.0, 12.0, 24.0, 36.0, 50.0)    # below the crotch: hips, mid thigh, above the knee, the calf, the shin
MARGIN = 0.8                              # the ring this far outside the legs' outline
PREFIX = 'AnatSkirt_'
NEAR = 1.0                                # a garment vertex this close to the skin is fitted, not hanging
TOP, RAMP = 4.0, 8.0                      # the share starts TOP above the crotch and is full RAMP below that
SMOOTH = 8                                # passes over the garment's edges
SOLVER = dict(damping=0.12, stiffness=(0.5, 0.3, 0.22, 0.17, 0.14), iterations=3, margin=0.6, hold=4.0,
              stretch=1.05, squash=0.9, spread=1.6, hintUp=0.5, reset=60.0, step=1.0 / 60.0, maxStep=2.0,
              gravity=0.1, deep=0.75, cross=0.5, away=0.2)


def name(c, l):
    return f'{PREFIX}{c:02d}_{l}'


def names():
    return [name(c, l) for c in range(COLUMNS) for l in range(len(LEVELS))]


# ---------------------------------------------------------------- transforms (zex_bones' (r9, t, s): p' = R s p + t)
def m4(r9, t, s):
    m = np.eye(4)
    m[:3, :3] = np.array(r9, float).reshape(3, 3) * s
    m[:3, 3] = t
    return m


def shape_world(n, s, skel_world):
    """a skinned shape's vertices in the skeleton's bind pose: bone bind world @ skin-to-bone, through any bone of the
    shape the skeleton has (the placement is one for all of a shape's bones)"""
    bones, xf = n.skin(s)
    for b, (r, t, sc) in zip(bones, xf):
        if b in skel_world:
            place = m4(*skel_world[b]) @ m4(r, t, sc)
            p = np.array(s.positions(), float)
            return p @ place[:3, :3].T + place[:3, 3], place
    raise ValueError(f'{s.name}: none of its {len(bones)} bones is in the skeleton')


# ---------------------------------------------------------------- 1. the ring
def _hull(pts):
    pts = sorted(set(map(tuple, np.round(pts, 4))))
    if len(pts) < 3:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return np.array(lo[:-1] + hi[:-1])


def _ray_hull(c, d, hull):
    """distance from c along d (2D) to the hull's boundary (c inside)"""
    best = 0.0
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        e = b - a
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-9:
            continue
        w = a - c
        t = (w[0] * e[1] - w[1] * e[0]) / den
        u = (w[0] * d[1] - w[1] * d[0]) / den
        if t > 0 and -1e-6 <= u <= 1 + 1e-6:
            best = max(best, t)
    return best


def column_dir(c):
    a = 2 * math.pi * c / COLUMNS
    return np.array([math.sin(a), math.cos(a)])


def design(body_nif, shape_name, skel_path):
    """{bone: rest offset in Pelvis_skin's frame}, the legs' capsule radii, the crotch height (world), for a body"""
    import nif
    import zex_bones as zb
    w = zb.skeleton_world(skel_path)
    n = nif.Nif(body_nif)
    s = n.shape(shape_name)
    P, _ = shape_world(n, s, w)
    joints = {k: np.array(w[k][1], float) for k in ('LLeg_Thigh', 'LLeg_Calf', 'LLeg_Foot',
                                                    'RLeg_Thigh', 'RLeg_Calf', 'RLeg_Foot')}
    segs = [(f'{sd}Leg_Thigh', f'{sd}Leg_Calf') for sd in 'LR'] + [(f'{sd}Leg_Calf', f'{sd}Leg_Foot') for sd in 'LR']
    # the leg vertices: nearest to a leg segment and below the hips; their distance to that segment's axis
    dist, tpar, which = [], [], []
    for a, b in segs:
        A, B = joints[a], joints[b]
        u = B - A
        L2 = u @ u
        t = np.clip(((P - A) @ u) / L2, 0, 1)
        C = A + t[:, None] * u
        dist.append(np.linalg.norm(P - C, axis=1))
        tpar.append(t)
    dist, tpar = np.array(dist), np.array(tpar)
    k = dist.argmin(0)
    best = dist[k, np.arange(len(P))]
    tk = tpar[k, np.arange(len(P))]
    # the crotch: the lowest point of the body on the midline, between front and back (the perineum); below it the
    # legs part and there is no body at x = 0
    hip = joints['LLeg_Thigh'][2]
    # a man's penis and scrotum hang on the midline below the crotch: not the body's outline
    sbones, _ = n.skin(s)
    genital = np.array([any(w_ > 0.02 and any(g in sbones[sl].lower() for g in ('penis', 'scrot', 'balls'))
                            for sl, w_ in s.skin_weights(i)) for i in range(s.count)])
    P = np.where(genital[:, None], np.nan, P)
    # the perineum: just behind the hip joints' line (y 0), where neither sex has genitals hanging
    under = (np.abs(P[:, 0]) < 0.3) & (P[:, 1] > -4.0) & (P[:, 1] < 0.0) & (P[:, 2] < hip + 2.0) & \
        (P[:, 2] > joints['LLeg_Calf'][2])
    crotch = float(np.nanmin(P[under, 2]))
    legs = (P[:, 2] < hip) & (best < 12.0)
    radii = {}
    for kind, idx in (('thigh', (0, 1)), ('calf', (2, 3))):
        sel = legs & np.isin(k, idx)
        top = sel & (tk > 0.1) & (tk < 0.25)
        bot = sel & (tk > 0.75) & (tk < 0.9)
        radii[kind] = (float(np.percentile(best[top], 90)), float(np.percentile(best[bot], 90)))
    # the ring
    pr, pt, ps = w['Pelvis_skin']
    Pw = m4(pr, pt, ps)
    inv = np.linalg.inv(Pw)
    rest = {}
    for l, depth in enumerate(LEVELS):
        z = crotch - depth
        band = P[legs & (np.abs(P[:, 2] - z) < 1.5)][:, :2]
        if len(band) < 10:
            raise ValueError(f'level {l} ({depth} below the crotch): {len(band)} leg vertices')
        hull = _hull(band)
        centre = np.array([0.0, band[:, 1].mean()])
        for c in range(COLUMNS):
            d = column_dir(c)
            r = _ray_hull(centre, d, hull) + MARGIN
            p = np.array([centre[0] + d[0] * r, centre[1] + d[1] * r, z, 1.0])
            rest[name(c, l)] = (inv @ p)[:3]
    return rest, radii, crotch


# ---------------------------------------------------------------- 2. the solver (fo4-ocbpc Skirt.cpp mirrors this)
def _closest_segments(p0, p1, q0, q1):
    """closest points between segments p0-p1 and q0-q1"""
    d1, d2, r = p1 - p0, q1 - q0, p0 - q0
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    if a <= 1e-12:
        s_, t_ = 0.0, np.clip(f / e, 0, 1) if e > 1e-12 else 0.0
    else:
        c = d1 @ r
        if e <= 1e-12:
            t_, s_ = 0.0, np.clip(-c / a, 0, 1)
        else:
            b = d1 @ d2
            den = a * e - b * b
            s_ = np.clip((b * f - c * e) / den, 0, 1) if den > 1e-12 else 0.0
            t_ = (b * s_ + f) / e
            if t_ < 0:
                t_, s_ = 0.0, np.clip(-c / a, 0, 1)
            elif t_ > 1:
                t_, s_ = 1.0, np.clip((b - c) / a, 0, 1)
    return p0 + d1 * s_, q0 + d2 * t_


class Solver:
    """rest: {bone: Pelvis_skin-local rest}; radii: {'thigh': (hip, knee), 'calf': (knee, ankle)}; clear: (bones, 4)
    each bone's clearance from each leg capsule (clearances()): a leg's cross-section is not round, so a capsule sized
    to the leg reaches past the ring on its narrow sides, and a bone at rest would be pushed while standing still.

    It runs in Pelvis_skin's frame: the pelvis carries the cloth, so a run or a snapped scene start never makes it fly,
    and a step can be limited (maxStep) without lagging behind the body. That limit is what keeps a bone from crossing a
    whole leg in one frame (the first try: cloth rode up onto the thighs of a sit, then the spring toward rest pulled
    it through them). Columns keep their length both ways (stretch, squash): cloth on a raised thigh drapes forward
    over the knee instead of bunching on the lap. A little gravity hangs it down in front of the shins."""

    def __init__(self, rest, radii, clear, params=SOLVER):
        self.k = params
        self.nl = len(LEVELS)
        self.rest = np.array([rest[name(c, l)] for c in range(COLUMNS) for l in range(self.nl)], float)
        self.radii = radii
        self.clear = np.asarray(clear, float)
        self.p = None
        self.prev = None
        self.world = None
        # outward per bone, in Pelvis_skin's frame: from its level's centre (the ring's mean) to it
        out = np.zeros_like(self.rest)
        for l in range(self.nl):
            idx = [c * self.nl + l for c in range(COLUMNS)]
            ctr = self.rest[idx].mean(0)
            for i in idx:
                v = self.rest[i] - ctr
                out[i] = v / (np.linalg.norm(v) or 1.0)
        self.out_local = out
        self.chain = np.array([np.linalg.norm(self.rest[c * self.nl + l] - self.rest[c * self.nl + l - 1])
                               if l else 0.0 for c in range(COLUMNS) for l in range(self.nl)])
        self.ring = np.array([np.linalg.norm(self.rest[((c + 1) % COLUMNS) * self.nl + l] - self.rest[c * self.nl + l])
                              for c in range(COLUMNS) for l in range(self.nl)])
        self.stiff = np.repeat(np.array(params['stiffness'])[None, :], COLUMNS, 0).reshape(-1)

    def capsules(self, joints):
        """joints: world positions of {L,R}Leg_{Thigh,Calf,Foot} -> [(a, b, ra, rb)] (L thigh, L calf, R thigh, R calf)"""
        out = []
        for sd in 'LR':
            th, ca, fo = joints[f'{sd}Leg_Thigh'], joints[f'{sd}Leg_Calf'], joints[f'{sd}Leg_Foot']
            out.append((np.asarray(th, float), np.asarray(ca, float), *self.radii['thigh']))
            out.append((np.asarray(ca, float), np.asarray(fo, float), *self.radii['calf']))
        return out

    def step(self, pelvis, joints, dt):
        """pelvis: 4x4 world of Pelvis_skin; joints: leg joints (world). Advances by dt seconds; returns world points."""
        k = self.k
        inv = np.linalg.inv(pelvis)
        scale = float(np.linalg.norm(pelvis[:3, 0])) or 1.0
        if self.p is None or np.abs(self.p - self.rest).max() > k['reset']:
            self.p, self.prev = self.rest.copy(), self.rest.copy()
        caps = [(inv[:3, :3] @ a + inv[:3, 3], inv[:3, :3] @ b + inv[:3, 3]) for a, b, _, _ in self.capsules(joints)]
        up = inv[:3, :3] @ np.array([0.0, 0.0, 1.0])
        up /= np.linalg.norm(up)
        hint = self.out_local + k['hintUp'] * up
        steps = max(1, min(4, int(round(dt / k['step']))))
        for _ in range(steps):
            v = (self.p - self.prev) * (1.0 - k['damping'])
            self.prev = self.p.copy()
            p = self.p + v - up * (k['gravity'] / scale)
            p += (self.rest - p) * self.stiff[:, None]
            move = p - self.prev
            n = np.linalg.norm(move, axis=1)
            lim = k['maxStep'] / scale
            over = n > lim
            p[over] = self.prev[over] + move[over] * (lim / n[over])[:, None]
            self.p = p
            for _ in range(k['iterations']):
                self._constrain(caps, hint, scale)
        self.world = self.p @ pelvis[:3, :3].T + pelvis[:3, 3]
        return self.world

    def _constrain(self, caps, hint, scale):
        k, nl = self.k, self.nl
        p = self.p
        # the top level stays near its rest (the waist holds the cloth)
        for c in range(COLUMNS):
            i = c * nl
            d = p[i] - self.rest[i]
            n = np.linalg.norm(d)
            if n > k['hold'] / scale:
                p[i] = self.rest[i] + d * (k['hold'] / scale / n)
        # columns keep their length: no stretch, and no bunching (squash)
        for c in range(COLUMNS):
            for l in range(1, nl):
                i, j = c * nl + l, c * nl + l - 1
                d = p[i] - p[j]
                n = np.linalg.norm(d)
                hi, lo = self.chain[i] * k['stretch'], self.chain[i] * k['squash']
                if n > hi:
                    p[i] = p[j] + d * (hi / n)
                elif n < lo:
                    dirv = d / n if n > 1e-6 else (self.rest[i] - self.rest[j]) / (self.chain[i] or 1.0)
                    p[i] = p[j] + dirv * lo
        # neighbours do not tear apart
        for c in range(COLUMNS):
            for l in range(nl):
                i, j = c * nl + l, ((c + 1) % COLUMNS) * nl + l
                d = p[j] - p[i]
                n = np.linalg.norm(d)
                lim = self.ring[i] * k['spread']
                if n > lim:
                    corr = d * (0.5 * (n - lim) / n)
                    p[i] += corr
                    p[j] -= corr
        # the legs. A bone a leg merely touches goes straight out (radially); one a leg LANDED on (deeper than `deep` of
        # the clearance: a scene snapped into its pose) goes to its column's side -- outward plus a little up, across
        # the leg -- since straight out may be the wrong side. And a column never passes THROUGH a leg: when the
        # segment from a bone to the one above it crosses a capsule, the lower bone goes to the column's side, so a
        # snapped sit drapes the cloth over the thighs instead of leaving it under them.
        for ci, (a, b) in enumerate(caps):
            u = b - a
            L = np.linalg.norm(u)
            u = u / L
            rad = self.clear[:, ci] / scale

            def side(i, cp, d, dn):
                h = hint[i] - (hint[i] @ u) * u
                hn = np.linalg.norm(h)
                if hn > 0.1:
                    return h / hn
                return d / dn if dn > 1e-6 else None

            t = np.clip((p - a) @ u, 0, L)
            cpt = a + t[:, None] * u
            d = p - cpt
            dn = np.linalg.norm(d, axis=1)
            for i in np.where(dn < rad)[0]:
                hs = side(i, cpt[i], d[i], dn[i])
                if dn[i] > k['deep'] * rad[i] and (hs is None or (d[i] / dn[i]) @ hs > -k['away']):
                    dirv = d[i] / dn[i]                  # touched: straight out, unless that is the far side
                else:
                    dirv = hs
                    if dirv is None:
                        continue
                p[i] = cpt[i] + dirv * rad[i]
            for c in range(COLUMNS):
                for l in range(1, nl):
                    i, j = c * nl + l, c * nl + l - 1
                    lim = self.clear[i, 4 + ci] / scale
                    if lim <= 0:
                        continue
                    q, cp = _closest_segments(p[j], p[i], a, b)
                    dd = q - cp
                    dl = np.linalg.norm(dd)
                    if dl >= k['cross'] * lim:
                        continue                         # only a segment the leg's axis really passes through
                    # crossing: the lower bone over to the column's side of the leg, at its own clearance
                    tt = np.clip((p[i] - a) @ u, 0, L)
                    ci_pt = a + tt * u
                    dirv = side(i, ci_pt, p[i] - ci_pt, np.linalg.norm(p[i] - ci_pt))
                    if dirv is None:
                        continue
                    if (p[i] - ci_pt) @ dirv >= rad[i]:
                        continue                         # already on that side and clear: the segment grazes
                    p[i] = ci_pt + dirv * rad[i]

    def offsets(self, pelvis=None):
        """each bone's offset from its rest, in Pelvis_skin's frame (what the engine adds to the node's local)"""
        return self.p - self.rest


KNEE_LEVEL = 3                            # follow mode: levels from this one down ride the calf, the rest the thigh


def follow_table(rest, skel_world):
    """FOLLOW mode (the owner, 2026-10-03: trade natural cloth for no clipping; fo4-refit studies/skirt_follow.py):
    every skirt node copies its legs rigidly instead of swinging. Per node: (segment 0 thigh / 1 calf, its share of
    the left leg, its rest point in the left leg segment's bind frame (3), in the right one's (3)). Points in a leg's
    own frame are physical, so the engine places them with that leg's live transform whatever its matrix layout, and
    blends the two legs by the share (the side columns take one leg, the front and back ones between the legs both).
    The leg bones' bind frames agree across the skeletons players load (vanilla vs DFS: 0.02 degrees)."""
    P = m4(*skel_world['Pelvis_skin'])
    Pinv = np.linalg.inv(P)
    leg = {(sd, seg): np.linalg.inv(m4(*skel_world[f'{sd}Leg_{seg}'])) for sd in 'LR' for seg in ('Thigh', 'Calf')}
    # the side: along the line from the right hip joint to the left one, in Pelvis_skin's frame (its z, not x)
    hl = (Pinv @ m4(*skel_world['LLeg_Thigh'])[:, 3])[:3]
    hr = (Pinv @ m4(*skel_world['RLeg_Thigh'])[:, 3])[:3]
    across = hl - hr
    out = {}
    for c in range(COLUMNS):
        for l in range(len(LEVELS)):
            n = name(c, l)
            r = np.asarray(rest[n], float)
            w = P @ np.r_[r, 1.0]
            seg = 'Calf' if l >= KNEE_LEVEL else 'Thigh'
            t = float(np.clip((r - hr) @ across / (across @ across), 0.0, 1.0))
            out[n] = (1 if seg == 'Calf' else 0, t * t * (3 - 2 * t),
                      *(leg['L', seg] @ w)[:3], *(leg['R', seg] @ w)[:3])
    return out


def follow_points(table, rest_names, world):
    """the engine's FOLLOW rule, for the offline renders: each node's Pelvis_skin-local point from the live leg
    transforms (world: lower-case bone name -> 4x4 world)"""
    Pinv = np.linalg.inv(world['pelvis_skin'])
    out = []
    for n in rest_names:
        seg, wl, *q = table[n]
        s = 'calf' if seg else 'thigh'
        pl = Pinv @ world[f'lleg_{s}'] @ np.r_[q[0:3], 1.0]
        pr = Pinv @ world[f'rleg_{s}'] @ np.r_[q[3:6], 1.0]
        out.append(wl * pl[:3] + (1 - wl) * pr[:3])
    return np.array(out)


def clearances(rest, radii, pelvis_bind, joints_bind, params=SOLVER):
    """(bones, 4): each bone's clearance from each leg capsule (L thigh, L calf, R thigh, R calf, Solver.capsules'
    order): the capsule's radius plus the margin, but never more than the bone's own distance from it at rest; then
    (columns 4-7) the same for the segment from the bone up to the one above it (a segment can pass closer to a leg
    than either end, so a crossing test with the bones' clearances fires at rest)"""
    nl = len(LEVELS)
    R = np.array([rest[name(c, l)] for c in range(COLUMNS) for l in range(nl)], float)
    W = R @ pelvis_bind[:3, :3].T + pelvis_bind[:3, 3]
    caps = Solver(rest, radii, np.zeros((len(R), 4)), params).capsules(joints_bind)
    out = np.full((len(R), 8), 1e6)
    for ci, (a, b, ra, rb) in enumerate(caps):
        u = b - a
        L = np.linalg.norm(u)
        u = u / L
        t = np.clip((W - a) @ u, 0, L)
        d = np.linalg.norm(W - (a + t[:, None] * u), axis=1)
        out[:, ci] = np.minimum(ra + (rb - ra) * (t / L) + params['margin'], d - 0.05)
        for c in range(COLUMNS):
            for l in range(1, nl):
                i, j = c * nl + l, c * nl + l - 1
                q, cp = _closest_segments(W[j], W[i], a, b)
                out[i, 4 + ci] = min(out[i, ci], out[j, ci], np.linalg.norm(q - cp) - 0.05)
    return out


# ---------------------------------------------------------------- 3. the weights
def _knn1(src, dst):
    """distance from each dst point to its nearest src point (chunked brute force on numpy)"""
    out = np.full(len(dst), np.inf)
    if len(src) == 0 or len(dst) == 0:
        return out
    b = np.asarray(src, np.float32)
    bb = (b * b).sum(1)
    for s in range(0, len(dst), 1024):
        q = np.asarray(dst[s:s + 1024], np.float32)
        d2 = (q * q).sum(1)[:, None] + bb[None, :] - 2.0 * (q @ b.T)
        out[s:s + 1024] = np.sqrt(np.maximum(d2.min(1), 0.0))
    return out


def skirt_weights(G, tri, B, rest_world, crotch, follows=None):
    """G: garment vertices (world bind); tri: its triangles; B: body vertices (world bind); rest_world: (COLUMNS, NL, 3)
    world rests; crotch: world z. -> (f (N,), idx (N,4) into names(), w (N,4)) -- the skirt part of each vertex's
    weights; f is the share it takes (0: none). follows (N,): the share of the vertex's own weights on leg bones. Cloth
    its author already weighted to the legs keeps that much of them: the R-18 coats did, and clipped 1-7%; replacing
    those weights with the skirt (which moves only where a leg reaches a node) made it 40-80% (studies/legs_skirt.py,
    2026-10-01). The skirt is for the panels that follow nothing but the pelvis."""
    nl = len(LEVELS)
    N = len(G)
    f = np.zeros(N)
    # only cloth below the ramp's top can take a share: test those, against the body from just above it down
    low = np.where(G[:, 2] < crotch + TOP)[0]
    hang = np.zeros(N, bool)
    hang[low] = _knn1(B[B[:, 2] < crotch + TOP + 3.0], G[low]) > NEAR
    zs = rest_world[0, :, 2]                       # level heights (descending)
    f = np.clip((crotch + TOP - G[:, 2]) / RAMP, 0.0, 1.0) * hang
    if follows is not None:
        f = f * np.clip(1.0 - np.asarray(follows, float), 0.0, 1.0)
    # smooth over the garment's edges, so a fitted vertex beside a hanging one does not tear
    e = np.r_[tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]
    e = np.r_[e, e[:, ::-1]]
    deg = np.bincount(e[:, 0], minlength=N).astype(float)
    for _ in range(SMOOTH):
        acc = np.bincount(e[:, 0], weights=f[e[:, 1]], minlength=N)
        f = 0.5 * f + 0.5 * np.where(deg > 0, acc / np.maximum(deg, 1), f)
    idx = np.zeros((N, 4), int)
    w = np.zeros((N, 4))
    centres = rest_world.mean(0)                   # (NL, 3) each level's centre
    for v in np.where(f > 0.005)[0]:
        q = G[v]
        # levels around its height
        if q[2] >= zs[0]:
            l0, l1, tl = 0, 0, 0.0
        elif q[2] <= zs[-1]:
            l0, l1, tl = nl - 1, nl - 1, 0.0
        else:
            l0 = int(np.where(zs >= q[2])[0][-1])
            l1 = l0 + 1
            tl = (zs[l0] - q[2]) / (zs[l0] - zs[l1])
        ctr = centres[l0] * (1 - tl) + centres[l1] * tl
        a = math.atan2(q[0] - ctr[0], q[1] - ctr[1]) % (2 * math.pi)
        x = a / (2 * math.pi) * COLUMNS
        c0 = int(math.floor(x)) % COLUMNS
        c1 = (c0 + 1) % COLUMNS
        tc = x - math.floor(x)
        cand = {}
        for c, wc in ((c0, 1 - tc), (c1, tc)):
            for l, wl in ((l0, 1 - tl), (l1, tl)):
                if wc * wl > 0:
                    j = c * nl + l
                    cand[j] = cand.get(j, 0.0) + wc * wl
        top = sorted(cand.items(), key=lambda t: -t[1])[:4]
        tot = sum(x for _, x in top)
        for k, (j, x) in enumerate(top):
            idx[v, k], w[v, k] = j, x / tot
    return f, idx, w


# ---------------------------------------------------------------- the reference bodies
def _reference(sex):
    import gamedata
    import align_body as ab
    root = pathlib.Path(__file__).resolve().parent.parent
    data = ab.DEFAULT_DATA
    game = gamedata.Game(data)
    work = pathlib.Path(r'D:\F4Output\skirt')
    work.mkdir(parents=True, exist_ok=True)
    if sex == 'women':
        skel = work / 'female_skeleton.nif'
        skel.write_bytes(game.read('Meshes/Actors/Character/CharacterAssets/female/skeleton.nif'))
        return root / 'build/project/ShapeData/Anatomy/Anatomy.nif', 'CBBE', skel
    skel = work / 'male_skeleton.nif'
    skel.write_bytes(game.read('Meshes/Actors/Character/CharacterAssets/skeleton.nif'))
    body = work / 'BodyTalk4-Nude.nif'
    body.write_bytes(game.read('Tools/BodySlide/ShapeData/BodyTalk4/BodyTalk4-Nude.nif'))
    return body, 'BaseMaleBody:0', skel


def main():
    if sys.argv[1:2] != ['design']:
        print(__doc__)
        return
    out = ['"""The skirt rings (roadmap 5), measured by `python tools/skirt.py design --write`: do not edit by hand.',
           'Rests are offsets in Pelvis_skin\'s frame (the engine\'s [Bones] / [BonesMale]); crotch is world z in the',
           'skeleton\'s bind pose; radii are the legs\' capsules (90th percentile of the skin\'s distance to the bone)."""', '']
    for sex, var in (('women', 'SKIRT'), ('men', 'SKIRT_M')):
        body, shape, skel = _reference(sex)
        rest, radii, crotch = design(body, shape, skel)
        out.append(f'# {sex}: {body.name} on {skel.name}; crotch at z {crotch:.2f}; legs (90th percentile) thigh '
                   f'{radii["thigh"][0]:.2f} -> {radii["thigh"][1]:.2f}, calf {radii["calf"][0]:.2f} -> '
                   f'{radii["calf"][1]:.2f}')
        out.append(f'{var}_RADII = dict(thigh=({radii["thigh"][0]:.2f}, {radii["thigh"][1]:.2f}), '
                   f'calf=({radii["calf"][0]:.2f}, {radii["calf"][1]:.2f}))')
        out.append(f'{var}_CROTCH = {crotch:.3f}')
        out.append(f'{var}_BONES = {{')
        out += [f"    '{k}': ({v[0]:.4f}, {v[1]:.4f}, {v[2]:.4f})," for k, v in rest.items()]
        out += ['}', '']
        # each bone's clearances from the legs in this skeleton's bind pose (Solver, the engine's [SkirtClear*])
        import zex_bones as zb
        w = zb.skeleton_world(skel)
        joints = {k: np.array(w[k][1], float) for k in ('LLeg_Thigh', 'LLeg_Calf', 'LLeg_Foot',
                                                        'RLeg_Thigh', 'RLeg_Calf', 'RLeg_Foot')}
        clear = clearances(rest, radii, m4(*w['Pelvis_skin']), joints)
        out.append(f'{var}_CLEAR = {{')
        out += [f"    '{k}': ({', '.join(f'{x:.3f}' for x in clear[i])})," for i, k in enumerate(names())]
        out += ['}', '']
    text = '\n'.join(out)
    if '--write' in sys.argv:
        (pathlib.Path(__file__).resolve().parent / 'skirt_rest.py').write_text(text, encoding='utf-8')
        print('wrote tools/skirt_rest.py')
    print('\n'.join(l for l in out if not l.startswith("    '")))


if __name__ == '__main__':
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    main()
