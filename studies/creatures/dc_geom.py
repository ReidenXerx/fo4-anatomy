"""Our deathclaw genitals (Dudu 11-09, option B): a reptilian vent + an everting reptilian penis (male), the vent lips
alone (female). Same shape names / morph names as UAP's DeathclawPenis.nif so AAF tags keep working.
  Base   (male)  vent lips: raised scaly lens around a slit, laid ON the vanilla body surface (raycast), UVs + skin
                 weights interpolated from the body triangle under each vertex -> seamless deathclaw skin
  Penis  (male)  the slit floor (flesh lining) + a tapered, ribbed reptilian penis (ventral groove, two dorsal nub
                 rows, spade head). Rest = retracted inside the body (tip at the vent, like UAP's), Erection = everted
                 along UAP's erect centreline; Up/Down/Length/Adjust/Scale follow UAP's centrelines
  VulvaLips / VulvaInner (female): fuller lips, slightly parted, flesh floor; one 'Erection' morph (swell + part)
UAP's morph deltas are added on top of Erection in AAF, so ours = ours(E + M) - ours(E).
    python -I dc_geom.py <male.json> <female.json>"""
import json
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UAP = r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\Deathclaw\DeathclawPenis'
BODY = __import__('os').environ.get('DC_BODY', r'D:\F4Output\creatures\dc\vanilla\deathclaw.nif')  # Ivy: per body
LINING_V = (0.01, 0.09)          # texture rows of the flesh lining in our penis texture
SHAFT_V = (0.12, 0.995)

# ---------------------------------------------------------------- body surface
bm = nif.Nif(BODY)
bs = max(bm.shapes(), key=lambda x: x.count)               # the body: the largest shape (DeathclawFX:0 on vanilla)
BV = np.array(bs.positions())
BUV = np.array([bs.uv(i) for i in range(bs.count)])
BT = np.array(bs.triangles())
bnames, _ = bm.skin(bs)
BW = [[(bnames[b], w) for b, w in bs.skin_weights(i) if w > 0] for i in range(bs.count)]
c = BV[BT].mean(1)
keep = (np.abs(c[:, 0]) < 16) & (c[:, 1] > -30) & (c[:, 1] < 16) & (c[:, 2] > 80) & (c[:, 2] < 140)
T = BT[keep]
V0, V1, V2 = BV[T[:, 0]], BV[T[:, 1]], BV[T[:, 2]]
E1, E2 = V1 - V0, V2 - V0
print('body tris near the crotch', len(T))


def ray_up(x, y):
    """first hit of a ray straight up from below at (x, y): (point, tri row, barycentrics)"""
    return ray(np.array([x, y, 40.0]), np.array([0.0, 0.0, 1.0]))


def ray(o, d):
    """first hit of a ray o + t d (t > 0) on the body: (point, tri row, barycentrics)"""
    p = np.cross(d, E2)
    det = (E1 * p).sum(1)
    ok = np.abs(det) > 1e-9
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = o - V0
    u = (s * p).sum(1) * inv
    q = np.cross(s, E1)
    v = (q * d).sum(1) * inv
    t = (E2 * q).sum(1) * inv
    hit = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 0)
    if not hit.any():
        raise SystemExit(f'no body hit from {o.round(2)} along {d.round(2)}')
    k = np.where(hit)[0][np.argmin(t[hit])]
    return o + t[k] * d, k, np.array([1 - u[k] - v[k], u[k], v[k]])


def surf_z(x, y):
    return ray_up(x, y)[0][2]


# midline: arc length s <-> y
YS = np.arange(-20.0, 10.0, 0.05)
ZS = np.array([surf_z(0.0, y) for y in YS])
ZS = np.convolve(np.pad(ZS, 6, mode='edge'), np.ones(13) / 13, mode='valid')     # smooth the flat-shaded facets
SS = np.concatenate([[0], np.cumsum(np.hypot(np.diff(YS), np.diff(ZS)))])


def y_of_s(s):
    return float(np.interp(s, SS, YS))


FRAME = {}            # P0, n0 (outward), t0 (along the midline, up the belly), b0 = +x; set once the entry is known


def _hit(x, s):
    F = FRAME
    o = F['P0'] + s * F['t0'] + x * F['b0'] + 30.0 * F['n0']
    return ray(o, -F['n0'])[0]


def surface(x, s):
    """body surface point at local (x, s) (s along the belly midline from the entry, rays along the belly normal -
    the belly faces forward here, vertical rays graze it) + a smoothed outward normal (finite differences)"""
    p = _hit(x, s)
    e = 0.8
    ds = _hit(x, s + e) - _hit(x, s - e)
    dx = _hit(x + e, s) - _hit(x - e, s)
    n = np.cross(dx, ds)
    n /= np.linalg.norm(n)
    if n @ FRAME['n0'] < 0:
        n = -n
    return p, n


def body_sample_pt(p):
    """uv + bone weights of the body under 3D point p (ray along -n0)"""
    _, k, bc = ray(p + 6.0 * FRAME['n0'], -FRAME['n0'])
    return _sample(k, bc)


def body_sample(x, y):
    """uv + bone weights of the body under (x, y)"""
    _, k, bc = ray_up(x, y)
    return _sample(k, bc)


def _sample(k, bc):
    tri = T[k]
    uv = (BUV[tri] * bc[:, None]).sum(0)
    w = {}
    for vi, b in zip(tri, bc):
        for name, ww in BW[vi]:
            w[name] = w.get(name, 0.0) + ww * b
    tot = sum(w.values())
    return uv, {k2: v2 / tot for k2, v2 in w.items()}


for x in (-0.3, 0.3):
    print('body uv at x', x, [body_sample(x, y)[0].round(3).tolist() for y in (-10, -5, 0)])

# ---------------------------------------------------------------- UAP centrelines
um = nif.Nif(UAP + '.nif')
utri = {s: {n: (mu, d) for n, mu, d in ms} for s, ms in tri_sync.read(UAP + '.tri')}


def udelta(shape, P, name):
    D = np.zeros_like(P)
    mu, d = utri[shape][name]
    for i, v in d.items():
        D[i] = np.array(v, float) * mu
    return D


UP = np.array(um.shape('Penis').positions())
UE = UP + udelta('Penis', UP, 'Erection')
c0 = UE.mean(0)
ax = np.linalg.svd(UE - c0, full_matrices=False)[2][0]
ax = ax if ax[1] > 0 else -ax
proj = (UE - c0) @ ax
NB = 8
bins = np.minimum(((proj - proj.min()) / np.ptp(proj) * NB).astype(int), NB - 1)


def ucentre(Q):
    cs = np.array([Q[bins == b].mean(0) for b in range(NB)])
    rs = np.array([np.linalg.norm(Q[bins == b] - cs[b], axis=1).mean() for b in range(NB)])
    cs[:, 0] = 0.0
    return cs, rs


STATES = {'rest': UP, 'E': UE}
for n in ('Erection Up', 'Erection Down', 'Length', 'Penis Adjust', 'Scale'):
    STATES['E+' + n] = UE + udelta('Penis', UP, n)
CL = {k: ucentre(Q) for k, Q in STATES.items()}
RREF = CL['E'][1]

# where the erect penis leaves the body: walk the root axis back until it meets the belly
b0, b1 = CL['E'][0][0], CL['E'][0][1]
axis0 = (b1 - b0) / np.linalg.norm(b1 - b0)
for k in np.arange(-8, 12, 0.05):                   # from inside the body forward: first point below the belly
    p = b0 + k * axis0
    if p[2] < float(np.interp(p[1], YS, ZS)):
        break
ENTRY = p
S_E = float(np.interp(ENTRY[1], YS, SS))
slope = float(np.interp(ENTRY[1], YS, np.gradient(ZS, YS)))
print('entry', ENTRY.round(2), 'arc', round(S_E, 2), 'belly slope', round(slope, 2))
_n0 = np.array([0.0, slope, -1.0]) / np.hypot(slope, 1.0)
_t0 = np.cross(np.array([1.0, 0.0, 0.0]), _n0)
_t0 = _t0 if _t0[2] > 0 else -_t0
FRAME.update(P0=ray(ENTRY + 10.0 * _n0, -_n0)[0], n0=_n0, t0=_t0, b0=np.array([1.0, 0.0, 0.0]))
S_E = 0.0                                         # vent coordinates: s along t0 from the entry
print('frame n0', _n0.round(3), 't0', _t0.round(3), 'P0', FRAME['P0'].round(2))


# ---------------------------------------------------------------- the vent (lens of rings around a slit)
def vent(P, side_split=True):
    """P: dict a0 b0 L W H s_c (+ open(s) for Erection). Returns (rings param list) -> vertices for Base-like lips.
    Rings r in [0..1] (0 = slit edge), theta around; right half and left half carry their own midline copies."""
    NR, NA = 12, 26                      # per half: NA + 1 points (both midline ends)
    rs = np.linspace(0.0, 1.0, NR) ** 1.35
    th_r = np.linspace(0.0, np.pi, NA + 1)            # right half (x > 0): sin >= 0
    th_l = np.linspace(np.pi, 2 * np.pi, NA + 1)
    pts, idx = [], {}
    for half, ths in (('R', th_r), ('L', th_l)):
        for i, r in enumerate(rs):
            for j, th in enumerate(ths):
                idx[(half, i, j)] = len(pts)
                pts.append((half, r, th))
    tris = []
    for half in ('R', 'L'):
        for i in range(NR - 1):
            for j in range(NA):
                a, b = idx[(half, i, j)], idx[(half, i, j + 1)]
                cc, d = idx[(half, i + 1, j)], idx[(half, i + 1, j + 1)]
                tris += [(a, cc, b), (b, cc, d)]
    return pts, tris, NR, NA


def lip_height(r, H, rim=0.12):
    return rim + H * np.exp(-((r - 0.22) / 0.30) ** 2)


def vent_point(r, th, P, state):
    """(x, s, h) of a lip vertex in a given state"""
    a = P['a0'] + (P['L'] - P['a0']) * r
    b = P['b0'] + (P['W'] - P['b0']) * r
    s = P['s_c'] + a * np.cos(th)
    x = b * np.sin(th)
    h = lip_height(r, P['H'])
    k = state.get('scale', 1.0)
    if state.get('open'):
        o = state['open'](s) * (1 - r) ** 1.3
        x += np.sign(np.sin(th)) * o
        h += 0.35 * (1 - r) ** 2 * (1 if o > 0.05 else 0)
    if k != 1.0:
        s, x, h = P['s_c'] + (s - P['s_c']) * k, x * k, h * k
    return x, s, h


def _islands():
    """body UV islands: index connectivity (UV seams split vertices in the nif)"""
    par = np.arange(len(BV))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for a, b, cc in BT:
        for x_, y_ in ((a, b), (b, cc)):
            ra, rb = find(x_), find(y_)
            if ra != rb:
                par[ra] = rb
    return np.array([find(i) for i in range(len(BV))])


ISL = _islands()
T_ISL = ISL[T[:, 0]]
T_CEN = (V0 + V1 + V2) / 3


def island_uv(p, isl):
    """UV of point p on body island isl: nearest island triangle, barycentrics in its plane (extrapolates a little)"""
    cand = np.where(T_ISL == isl)[0]
    k = cand[np.argmin(np.linalg.norm(T_CEN[cand] - p, axis=1))]
    a = V0[k]
    e0, e1, e2 = V1[k] - a, V2[k] - a, p - a
    d00, d01, d11, d20, d21 = e0 @ e0, e0 @ e1, e1 @ e1, e2 @ e0, e2 @ e1
    den = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    uvs = BUV[T[k]]
    return ((1 - v - w) * uvs[0] + v * uvs[1] + w * uvs[2]).tolist()


def build_lips(P, states):
    pts, tris, NR, NA = vent(P)
    out = {}
    for name, st in states.items():
        V = []
        for half, r, th in pts:
            x, s, h = vent_point(r, th, P, st)
            p, _ = surface(x, s)
            V.append(p + h * surface(x, s)[1])
        out[name] = np.array(V)
    rest = out['rest']
    # the vent straddles a body UV-island seam (crotch island behind, belly plate in front): every lips triangle takes
    # the island under its centroid, a vertex shared by triangles of two islands is split (positions stay welded)
    tri_isl = []
    for t in tris:
        cen = rest[list(t)].mean(0)
        tri_isl.append(int(T_ISL[ray(cen + 6.0 * FRAME['n0'], -FRAME['n0'])[1]]))
    newid, order, ntris = {}, [], []
    for t, isl in zip(tris, tri_isl):
        nt = []
        for vi in t:
            if (vi, isl) not in newid:
                newid[(vi, isl)] = len(order)
                order.append((vi, isl))
            nt.append(newid[(vi, isl)])
        ntris.append(tuple(nt))
    src = [vi for vi, _ in order]
    out = {k: V[src] for k, V in out.items()}
    uv = [island_uv(rest[vi], isl) for vi, isl in order]
    wts = [body_sample_pt(rest[vi])[1] for vi in src]
    print('lips islands', sorted(set(tri_isl)), 'split', len(order) - len(pts), 'vertices')
    return [pts[vi] for vi in src], ntris, out, uv, wts, NR, NA, pts


def build_floor(P, states, ring0):
    """the slit floor: lens from the lips' slit-edge ring (shared positions) down to h = 0.15, closing on the slit
    line; flesh lining UVs (LINING_V rows). ring0: [(r, th)] of the slit-edge ring, right half then left half."""
    NF = 6
    fs = np.linspace(0.0, 1.0, NF)
    pts = []
    for f in fs:
        for half, th in ring0:
            pts.append((f, half, th))
    nring = len(ring0)
    tris = []
    for i in range(NF - 1):
        for j in range(nring - 1):
            if ring0[j][0] != ring0[j + 1][0]:
                continue
            a, b = i * nring + j, i * nring + j + 1
            cc, d = a + nring, b + nring
            tris += [(a, b, cc), (b, d, cc)]
    out = {}
    for name, st in states.items():
        V = []
        for f, half, th in pts:
            x, s, h = vent_point(0.0, th, P, st)
            shrink = 1 - 0.92 * f
            x = x * shrink
            s = P['s_c'] + (s - P['s_c']) * (1 - 0.18 * f)
            h = h * (1 - min(1.0, f / 0.35)) + 0.15 * min(1.0, f / 0.35)
            p, n = surface(x, s)
            V.append(p + h * n)
        out[name] = np.array(V)
    smin, smax = P['s_c'] - P['a0'], P['s_c'] + P['a0']
    uv = []
    for (f, half, th), p in zip(pts, out['rest']):
        s = P['s_c'] + P['a0'] * np.cos(th) * (1 - 0.18 * f)
        u = 0.5 + 0.42 * np.sin(th) * (1 - f)
        v = LINING_V[0] + (LINING_V[1] - LINING_V[0]) * (s - smin) / (smax - smin)
        uv.append([float(u), float(v)])
    return pts, tris, out, uv


# ---------------------------------------------------------------- the penis tube
NSEG, RING_STEP = 34, 0.34


def curve_for(state):
    cs, rs = CL[state]
    a0v = (cs[1] - cs[0]) / np.linalg.norm(cs[1] - cs[0])
    tipd = (cs[-1] - cs[-2]) / np.linalg.norm(cs[-1] - cs[-2])
    nodes = np.vstack([cs[0] - 5.0 * a0v, cs[0] - 2.0 * a0v, cs, cs[-1] + 2.4 * tipd])
    # Catmull-Rom, dense, then arc-length table
    P = np.vstack([2 * nodes[0] - nodes[1], nodes, 2 * nodes[-1] - nodes[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, 24, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    C = np.array(out)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))])
    return C, L, float(np.mean(rs / RREF))


def frame_along(C):
    """parallel-transport frames, 'up' starts toward the belly (+z) and dorsal = +up"""
    T_ = np.gradient(C, axis=0)
    T_ /= np.linalg.norm(T_, axis=1)[:, None]
    up = np.array([0.0, 0.0, 1.0])
    U = [up - (up @ T_[0]) * T_[0]]
    U[0] /= np.linalg.norm(U[0])
    for i in range(1, len(C)):
        u = U[-1] - (U[-1] @ T_[i]) * T_[i]
        U.append(u / np.linalg.norm(u))
    U = np.array(U)
    return T_, U, np.cross(T_, U)


def radius_profile(t):
    """base radius at fraction t (0 = inside end, 1 = tip point), in UAP-erect units"""
    xs = [0.0, 0.10, 0.18, 0.40, 0.62, 0.80, 0.86, 0.91, 0.955, 0.985, 1.0]
    ys = [3.5, 3.75, 3.7, 3.45, 2.95, 2.35, 2.6, 2.25, 1.45, 0.75, 0.0]
    return np.interp(t, xs, ys)


def tube(state, rest_shrink=1.0, inset=None):
    C, L, rk = curve_for(state)
    if state == 'E+Scale':
        rk = 1.33
    T_, U, X = frame_along(C)
    total = L[-1]
    nr = int(round(CL_LEN / RING_STEP))
    ts = np.linspace(0.0, 1.0, nr + 1)
    V = []
    for t in ts:
        li = t * total
        k = min(np.searchsorted(L, li), len(C) - 1)
        p, tt, uu, xx = C[k], T_[k], U[k], X[k]
        if inset is not None:
            p = p + inset
        base = radius_profile(t) * rk * rest_shrink
        ln = t * CL_LEN                                        # detail phase in E units (same for every state)
        for j in range(NSEG + 1):
            th = 2 * np.pi * j / NSEG                          # 0 = dorsal, pi = ventral
            r = base
            if 0.12 < t < 0.93:
                g = np.exp(-(((th - np.pi) / 0.30) ** 2))
                r *= 1 - 0.15 * g
                if t < 0.80:
                    rib = (0.5 + 0.5 * np.cos(2 * np.pi * ln / 2.3)) ** 3
                    r *= 1 + 0.07 * rib * (1 - g)
                for side in (-0.6, 0.6):
                    dth = (th - side + np.pi) % (2 * np.pi) - np.pi
                    if 0.2 < t < 0.78:
                        ph = ((ln + 1.15) % 2.3) - 1.15
                        r += 0.38 * (base / 3.5) * np.exp(-(ph / 0.42) ** 2 - (dth * base / 0.5) ** 2)
            sx, sz = np.sin(th), np.cos(th)
            fl = 1.0 + 0.18 * np.exp(-((t - 0.865) / 0.04) ** 2)      # spade head: wider sideways
            V.append(p + r * (sz * 0.9 * uu + sx * fl * xx))
    return np.array(V), ts


_C, _L, _ = curve_for('E')
CL_LEN = float(_L[-1])


def tube_topology(nrings):
    tris = []
    w = NSEG + 1
    for i in range(nrings - 1):
        for j in range(NSEG):
            a, b = i * w + j, i * w + j + 1
            cc, d = a + w, b + w
            tris += [(a, b, cc), (b, d, cc)]
    return tris


def welded_normals(V, tris):
    key = {}
    wid = np.array([key.setdefault(tuple(np.round(p, 4)), len(key)) for p in V])
    N = np.zeros((len(key), 3))
    for a, b, cc in tris:
        n = np.cross(V[b] - V[a], V[cc] - V[a])
        for i in (a, b, cc):
            N[wid[i]] += n
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]
    return N[wid]


def json_shape(V, tris, uv, weights, morphs):
    bones = sorted({b for w in weights for b in w})
    return {'verts': V.round(5).tolist(), 'tris': [list(map(int, t)) for t in tris], 'uv': uv,
            'normals': welded_normals(V, tris).round(5).tolist(),
            'weights': {b: [round(w.get(b, 0.0), 5) for w in weights] for b in bones},
            'morphs': {k: np.asarray(d).round(5).tolist() for k, d in morphs.items()}}


def flip_check(V, tris, label):
    """outward check: normals of a closed-ish surface vs its centroid"""
    N = welded_normals(V, tris)
    c = V.mean(0)
    print(label, 'outward fraction', round(float(((V - c) * N).sum(1).__gt__(0).mean()), 2))


# ================================================================ MALE
MALE = dict(a0=5.6, b0=0.35, L=8.6, W=4.6, H=1.35, s_c=S_E - 0.4)
R_ROOT = float(radius_profile(0.12)) + 0.35


def open_male(s):
    return max(0.0, R_ROOT * np.sqrt(max(0.0, 1 - ((s - S_E) / 6.0) ** 2)))


ADJ = CL['E+Penis Adjust'][0][0] - CL['E'][0][0]           # how far UAP's adjust moves the root
VSTATES = {'rest': {}, 'E': {'open': open_male}, 'E+Scale': {'open': open_male, 'scale': 1.3}}
pts, ltris, LIPS, luv, lw, NR, NA, pts0 = build_lips(MALE, VSTATES)
ring0 = [(half, th) for half, r, th in pts0 if r == 0.0]
fpts, ftris, FLOOR, fuv = build_floor(MALE, VSTATES, ring0)
# Penis Adjust: the lips + floor near the root follow the root (UAP's base does the same), rim stays
lip_adj = np.array([ADJ * (1 - r) ** 1.5 * np.exp(-((MALE['s_c'] + MALE['a0'] * np.cos(th) - S_E) / 5.0) ** 2)
                    for half, r, th in pts])
floor_adj = np.array([ADJ * np.exp(-((MALE['s_c'] + MALE['a0'] * np.cos(th) - S_E) / 5.0) ** 2)
                      for f, half, th in fpts])
fw = [body_sample_pt(np.array([max(abs(p[0]), 0.35) * (1 if half == 'R' else -1), p[1], p[2]]))[1]
      for (f, half, th), p in zip(fpts, FLOOR['rest'])]

# penis: rest = UAP's retracted centreline pulled 2.5 further into the body, 80 % thick
n_in = -surface(0.0, S_E)[1]
TUBES = {}
for st in CL:
    if st == 'rest':
        TUBES[st], ts = tube('rest', rest_shrink=0.8, inset=2.5 * n_in)
    else:
        TUBES[st], ts = tube(st)
ptris = tube_topology(len(ts))
nv_tube = len(TUBES['E'])
puv = []
for t in ts:
    for j in range(NSEG + 1):
        puv.append([j / NSEG, SHAFT_V[0] + (SHAFT_V[1] - SHAFT_V[0]) * float(t)])
# tip: close the last ring (radius 0 already) - nothing to add; the inside end stays open (hidden in the body)

# Base morphs (UAP names: Erection, Scale, Penis Adjust)
base_m = {'Erection': LIPS['E'] - LIPS['rest'], 'Scale': LIPS['E+Scale'] - LIPS['E'], 'Penis Adjust': lip_adj}
# Penis shape = floor (first) + tube
pen_rest = np.vstack([FLOOR['rest'], TUBES['rest']])
nf = len(FLOOR['rest'])


def pen_delta(state_from, state_to, floor_from=None, floor_to=None):
    fd = (FLOOR[floor_to] - FLOOR[floor_from]) if floor_to else np.zeros_like(FLOOR['rest'])
    return np.vstack([fd, TUBES[state_to] - TUBES[state_from]])


pen_m = {'Erection': pen_delta('rest', 'E', 'rest', 'E'),
         'Scale': pen_delta('E', 'E+Scale', 'E', 'E+Scale'),
         'Erection Up': pen_delta('E', 'E+Erection Up'),
         'Erection Down': pen_delta('E', 'E+Erection Down'),
         'Length': pen_delta('E', 'E+Length'),
         'Penis Adjust': np.vstack([floor_adj, TUBES['E+Penis Adjust'] - TUBES['E']])}
ptris_all = [tuple(int(i) for i in t) for t in ftris] + [(a + nf, b + nf, cc + nf) for a, b, cc in ptris]
pw = fw + [{'Pelvis': 1.0}] * nv_tube
male = {'Base': json_shape(LIPS['rest'], ltris, luv, lw, base_m),
        'Penis': json_shape(pen_rest, ptris_all, fuv + puv, pw, pen_m),
        '_info': {'entry': ENTRY.tolist(), 's_entry': S_E, 'len': CL_LEN}}
flip_check(TUBES['E'], ptris, 'penis tube (E)')
print('male: Base', len(LIPS['rest']), 'v', len(ltris), 't; Penis', len(pen_rest), 'v (floor', nf, ')', len(ptris_all), 't;',
      'erect length', round(CL_LEN, 1), 'root r', round(R_ROOT, 2))
for k, d in {**{'Base ' + a: b for a, b in base_m.items()}, **{'Penis ' + a: b for a, b in pen_m.items()}}.items():
    print(f'   {k:20s} max {np.linalg.norm(d, axis=1).max():5.2f}')
# lips vs body: the rim must sit just outside the skin
rim = LIPS['rest'][[i for i, (h, r, th) in enumerate(pts) if r == 1.0]]
print('rim height above body: min %.2f max %.2f' % tuple(
    (lambda d: (d.min(), d.max()))(np.array([(p - ray(p + 6.0 * FRAME['n0'], -FRAME['n0'])[0]) @ FRAME['n0']
                                         for p in rim]))))
NL = welded_normals(LIPS['rest'], ltris)
print('lips facing out of the body:', round(float(np.mean([NL[i] @ FRAME['n0'] > 0
                                                        for i, p in enumerate(LIPS['rest'])])), 2))
NF_ = welded_normals(FLOOR['rest'], [tuple(t) for t in ftris])
print('floor facing out of the body:', round(float(np.mean([NF_[i] @ FRAME['n0'] > 0
                                                         for i, p in enumerate(FLOOR['rest'])])), 2))
json.dump(male, open(sys.argv[1], 'w'))

# ================================================================ FEMALE
FEM = dict(a0=6.4, b0=0.85, L=10.0, W=5.4, H=1.9, s_c=S_E - 0.8)


def open_f(s):
    return 0.55 * np.sqrt(max(0.0, 1 - ((s - FEM['s_c']) / 6.6) ** 2))


FST = {'rest': {}, 'E': {'open': open_f, 'scale': 1.08}}
pts_f, ltris_f, LIPS_F, luv_f, lw_f, _, _, pts0f = build_lips(FEM, FST)
ring0f = [(half, th) for half, r, th in pts0f if r == 0.0]
fpts_f, ftris_f, FLOOR_F, fuv_f = build_floor(FEM, FST, ring0f)
fw_f = [body_sample_pt(np.array([max(abs(p[0]), 0.35) * (1 if half == 'R' else -1), p[1], p[2]]))[1]
        for (f, half, th), p in zip(fpts_f, FLOOR_F['rest'])]
female = {'VulvaLips': json_shape(LIPS_F['rest'], ltris_f, luv_f, lw_f, {'Erection': LIPS_F['E'] - LIPS_F['rest']}),
          'VulvaInner': json_shape(FLOOR_F['rest'], ftris_f, fuv_f, fw_f, {'Erection': FLOOR_F['E'] - FLOOR_F['rest']})}
print('female: lips', len(LIPS_F['rest']), 'inner', len(FLOOR_F['rest']))
json.dump(female, open(sys.argv[2], 'w'))
