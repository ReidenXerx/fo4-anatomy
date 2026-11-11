"""Female super mutant (Dudu 11-11; shape from ilhamitaa24's reference, #management 1570130682473095240): the female
parts laid ON the vanilla SM body, and the body's silhouette warp.
  FemBreastL/R     heavy hanging breasts: a footprint on the chest (rim exactly on the skin), a height profile off it
                   (long gentle upper slope, full lower pole), then SAG: every point drops in proportion to how far it
                   stands off the chest, so the lower pole hangs below its own rim and folds onto the belly; a little
                   outward spread. UVs + weights from the skin at each point's ROOT (its footprint position).
  FemNippleL/R     tips just below the hanging apex, along the surface normal, dark flesh (MutantGlans material)
  FemVulvaLips     raised lips round a slit on the crotch (rays from inside the pelvis, forward-down)
  FemVulvaInner    the slit floor, flesh
The body (topology untouched: the dismember segments stay vanilla) and every shape above get the same position-only
warp(): soft belly forward, hips wider, thick thighs and calves (radial about each leg's axis), big glutes. The armour
refit uses warp() too, plus the breast SHIELD (bulge(): how far the breasts stand off the skin, cleavage and the
fall under the breasts filled the way a plate would drape). Front = +y, up = +z (skin space, RAW).
    python -I smf_geom.py <body nif> <out geom json> [params json]"""
import json
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

P0 = {
    'breast': {'cx': 8.1, 'cz': -24.5, 'Rx': 8.2, 'Rz': 10.5, 'h': 10.5, 'sag': 7.5, 'sag_p': 0.8, 'spread': 2.2,
               'nipple_r': 1.0, 'nipple_h': 1.1, 'nipple_at': 0.22},
    'hips': {'z': -58.0, 'sz': 7.0, 'k': 1.18},             # x scale (gaussian in z)
    # thigh/calf thickness: radial scale about each leg's axis, k by z (piecewise linear); axis measured in main
    'legs': {'zk': [-55.0, -63.0, -72.0, -86.0, -93.0, -100.0, -108.0, -116.0],
             'kk': [1.0, 1.16, 1.26, 1.24, 1.10, 1.16, 1.10, 1.0]},
    'belly': {'z': -47.0, 'sz': 8.0, 'sx': 12.0, 'd': 3.2},  # forward push, front skin only
    'glutes': {'z': -61.0, 'sz': 7.0, 'x': 9.0, 'sx': 7.5, 'd': 4.6},   # backward push, each cheek
    'vulva': {'origin': [0.0, 2.0, -50.0], 'dir': [0.0, 0.45, -0.89], 'prefer': [0.0, 1.0, 0.0], 'depth': 6.0,
              'a0': 2.0, 'b0': 0.42, 'L': 4.0, 'W': 3.0, 'H': 1.2},
}
LINING_V = (0.006, 0.034)
FLESH = ['Materials\\Anatomy\\Creatures\\MutantGlans.bgsm', 'textures\\Anatomy\\Creatures\\MutantGlans_d.dds',
         'textures\\Anatomy\\Creatures\\MutantGlans_n.dds', 'textures\\Actors\\Supermutant\\Supermutant_s.dds']


def bulge(x, z, p):
    """the breast shield along +y at (x, z): bilinear in the grid main() measured (0 outside it)"""
    g = p['shield']
    xs, zs, H = np.array(g['xs']), np.array(g['zs']), np.array(g['H'])
    x, z = np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(z, float))
    fx = (x - xs[0]) / (xs[1] - xs[0])
    fz = (z - zs[0]) / (zs[1] - zs[0])
    ok = (fx >= 0) & (fx <= len(xs) - 1) & (fz >= 0) & (fz <= len(zs) - 1)
    i = np.clip(np.floor(fx).astype(int), 0, len(xs) - 2)
    j = np.clip(np.floor(fz).astype(int), 0, len(zs) - 2)
    a, b = np.clip(fx - i, 0, 1), np.clip(fz - j, 0, 1)
    v = (H[j, i] * (1 - a) * (1 - b) + H[j, i + 1] * a * (1 - b) + H[j + 1, i] * (1 - a) * b
         + H[j + 1, i + 1] * a * b)
    return np.where(ok, v, 0.0)


def smooth01(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def warp(P, p):
    """the female silhouette as a displacement field over skin space (body, our shapes and the armour alike)"""
    P = np.array(P, dtype=float)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    out = P.copy()
    L = p['legs']
    kl = np.interp(z, L['zk'], L['kk'], left=1.0, right=1.0)
    f = 1 + (kl - 1) * smooth01((np.abs(x) - 2.5) / 4.0)         # the inner thigh grows less, the crotch not at all
    ax = np.sign(x) * np.interp(z, L['az'], L['ax'])
    ay = np.interp(z, L['az'], L['ay'])
    out[:, 0] = ax + (x - ax) * f
    out[:, 1] = ay + (y - ay) * f
    h = p['hips']
    out[:, 0] *= 1 + (h['k'] - 1) * np.exp(-((z - h['z']) / h['sz']) ** 2)
    b = p['belly']
    out[:, 1] += b['d'] * np.exp(-((z - b['z']) / b['sz']) ** 2 - (x / b['sx']) ** 2) * smooth01(y / 8.0)
    g = p['glutes']
    for s in (1, -1):
        out[:, 1] -= g['d'] * np.exp(-((z - g['z']) / g['sz']) ** 2 - ((x - s * g['x']) / g['sx']) ** 2) \
            * smooth01((-y - 2.0) / 8.0)
    return out


class Body:
    def __init__(self, path):
        m = nif.Nif(path)
        s = max(m.shapes(), key=lambda q: q.count)
        self.V = np.array(s.positions())
        self.UV = np.array([s.uv(i) for i in range(s.count)])
        self.T = np.array(s.triangles())
        names, _ = m.skin(s)
        self.W = [[(names[b], w) for b, w in s.skin_weights(i) if w > 0] for i in range(s.count)]
        self.V0, V1, V2 = self.V[self.T[:, 0]], self.V[self.T[:, 1]], self.V[self.T[:, 2]]
        self.E1, self.E2 = V1 - self.V0, V2 - self.V0
        par = np.arange(len(self.V))

        def find(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a
        for a_, b_, c_ in self.T:
            for x_, y_ in ((a_, b_), (b_, c_)):
                ra, rb = find(x_), find(y_)
                if ra != rb:
                    par[ra] = rb
        self.TISL = np.array([find(i) for i in range(len(self.V))])[self.T[:, 0]]

    def ray(self, o, d):
        p = np.cross(d, self.E2)
        det = (self.E1 * p).sum(1)
        ok = np.abs(det) > 1e-9
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        s = o - self.V0
        u = (s * p).sum(1) * inv
        q = np.cross(s, self.E1)
        v = (q * d).sum(1) * inv
        t = (self.E2 * q).sum(1) * inv
        hit = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 0)
        if not hit.any():
            return None
        k = np.where(hit)[0][np.argmin(t[hit])]
        return o + t[k] * d, k, np.array([1 - u[k] - v[k], u[k], v[k]])

    def sample(self, k, bc):
        tri = self.T[k]
        uv = (self.UV[tri] * bc[:, None]).sum(0)
        w = {}
        for vi, b in zip(tri, bc):
            for n, ww in self.W[vi]:
                w[n] = w.get(n, 0.0) + ww * b
        tot = sum(w.values())
        return uv, {a: b / tot for a, b in w.items()}


def normals(V, tris):
    key = {}
    wid = np.array([key.setdefault(tuple(np.round(p, 4)), len(key)) for p in V])
    N = np.zeros((len(key), 3))
    for a, b, c in tris:
        n = np.cross(V[b] - V[a], V[c] - V[a])
        for i in (a, b, c):
            N[wid[i]] += n
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]
    return N[wid]


def shape(V, tris, uv, w, mat=None, outward=None):
    V = np.asarray(V)
    tris = [list(map(int, t)) for t in tris]
    if outward is not None and (normals(V, tris) @ np.asarray(outward)).mean() < 0:
        tris = [[a, c, b] for a, b, c in tris]
    bones = sorted({b for x in w for b in x})
    out = {'verts': V.round(5).tolist(), 'tris': tris, 'uv': [list(map(float, u)) for u in uv],
           'normals': normals(V, tris).round(5).tolist(),
           'weights': {b: [round(x.get(b, 0.0), 5) for x in w] for b in bones}, 'morphs': {}}
    if mat:
        out['mat'] = mat
    return out


def split_by_island(B, V, tris, probe):
    """every triangle takes the skin island under its centroid; its vertices take that island's UV (probe hit)"""
    newid, order, nt = {}, [], []
    for t in tris:
        h = probe(V[list(t)].mean(0))
        isl = int(B.TISL[h[1]]) if h else -1
        row = []
        for vi in t:
            if (vi, isl) not in newid:
                newid[(vi, isl)] = len(order)
                order.append((vi, isl))
            row.append(newid[(vi, isl)])
        nt.append(row)
    uv, w = [], []
    for vi, isl in order:
        h = probe(V[vi])
        if h:
            u_, w_ = B.sample(h[1], h[2])
            uv.append(u_.tolist())
            w.append(w_)
        else:
            uv.append([0.5, 0.5])
            w.append({'Chest_skin': 1.0})
    return V[[vi for vi, _ in order]], nt, uv, w


def vulva(B, p, out):
    vp = p['vulva']
    d = np.array(vp['dir'], float)
    d /= np.linalg.norm(d)
    o = np.array(vp['origin'], float)
    hit = B.ray(o, d)
    if hit is None:
        raise SystemExit('no crotch surface along the vulva ray')
    C = hit[0]
    e = 0.6
    side = np.array([1.0, 0, 0])
    up = np.cross(d, side)
    up /= np.linalg.norm(up)

    def at(a, b):
        return B.ray(o + a * up + b * side, d)[0]
    n0 = np.cross(at(e, 0) - at(-e, 0), at(0, e) - at(0, -e))
    n0 /= np.linalg.norm(n0)
    if n0 @ d < 0:
        n0 = -n0
    t0 = np.cross(n0, side)
    t0 = t0 if t0 @ np.array(vp['prefer']) > 0 else -t0
    depth = vp['depth']

    def surf(x, s_):
        org = C + s_ * t0 + x * side - depth * n0
        h = B.ray(org, n0)
        if h is None:
            raise SystemExit(f'no crotch surface at x {x:.2f} s {s_:.2f}')
        q = [B.ray(C + (s_ + a) * t0 + (x + b) * side - depth * n0, n0)[0] for a, b in ((e, 0), (-e, 0), (0, e), (0, -e))]
        n = np.cross(q[2] - q[3], q[0] - q[1])
        n /= np.linalg.norm(n)
        return h[0], (n if n @ n0 > 0 else -n)

    def probe(q):
        return B.ray(q - depth * n0, n0)
    NR, NA = 10, 22
    rs = np.linspace(0.0, 1.0, NR) ** 1.35
    pts, idx = [], {}
    for half, ths in (('R', np.linspace(0, np.pi, NA + 1)), ('L', np.linspace(np.pi, 2 * np.pi, NA + 1))):
        for i, r in enumerate(rs):
            for j, th in enumerate(ths):
                idx[(half, i, j)] = len(pts)
                pts.append((half, r, th))
    tris = []
    for half in ('R', 'L'):
        for i in range(NR - 1):
            for j in range(NA):
                a, b = idx[(half, i, j)], idx[(half, i, j + 1)]
                c, dd = idx[(half, i + 1, j)], idx[(half, i + 1, j + 1)]
                tris += [(a, b, c), (b, dd, c)]
    V = []
    for half, r, th in pts:
        a = vp['a0'] + (vp['L'] - vp['a0']) * r
        b = vp['b0'] + (vp['W'] - vp['b0']) * r
        s_, x = a * np.cos(th), b * np.sin(th)
        h = 0.06 * vp['H'] + vp['H'] * np.exp(-((r - 0.25) / 0.30) ** 2)
        q, n = surf(x, s_)
        V.append(q + h * n)
    V = np.array(V)
    Vs, ts, uv, w = split_by_island(B, V, tris, probe)
    out['FemVulvaLips'] = shape(Vs, ts, uv, w, outward=n0)
    ring = [(half, th) for half, r, th in pts if r == 0.0]
    NF = 5
    fpts, ftris = [], []
    for k, f in enumerate(np.linspace(0, 1, NF)):
        for half, th in ring:
            fpts.append((f, half, th))
    nr = len(ring)
    for i in range(NF - 1):
        for j in range(nr - 1):
            if ring[j][0] != ring[j + 1][0]:
                continue
            a, b = i * nr + j, i * nr + j + 1
            ftris += [(a, b + nr, b), (a, a + nr, b + nr)]
    FV, fuv = [], []
    for f, half, th in fpts:
        s_ = vp['a0'] * np.cos(th) * (1 - 0.15 * f)
        x = vp['b0'] * np.sin(th) * (1 - 0.95 * f)
        h0 = 0.06 * vp['H'] + vp['H'] * np.exp(-((0.0 - 0.25) / 0.30) ** 2)
        h = h0 * (1 - min(1.0, f / 0.4)) + 0.08 * min(1.0, f / 0.4)
        q, n = surf(x, s_)
        FV.append(q + h * n)
        fuv.append([0.5 + 0.45 * np.sin(th) * (1 - f), LINING_V[0] + (LINING_V[1] - LINING_V[0]) * (0.5 + 0.5 * np.cos(th))])
    FV = np.array(FV)
    fw = [B.sample(*probe(q)[1:])[1] if probe(q) else {'Pelvis_skin': 1.0} for q in FV]
    out['FemVulvaInner'] = shape(FV, ftris, fuv, fw, mat=FLESH, outward=n0)
    return C, n0


class Tris(Body):
    """any triangle soup with Body's ray()"""
    def __init__(self, V, T):
        self.V, self.T = np.asarray(V, float), np.asarray(T, int)
        self.V0 = self.V[self.T[:, 0]]
        self.E1, self.E2 = self.V[self.T[:, 1]] - self.V0, self.V[self.T[:, 2]] - self.V0


def breast_point(B, p, s, r, th):
    """(root on the chest, final point, normalised height) for footprint polar coords (r, th) on side s"""
    b = p['breast']
    xr = s * b['cx'] + r * b['Rx'] * np.cos(th)
    zr = b['cz'] + r * b['Rz'] * np.sin(th)
    hit = B.ray(np.array([xr, -6.0, zr]), np.array([0, 1.0, 0]))
    if hit is None:
        raise SystemExit(f'no chest surface at x {xr:.1f} z {zr:.1f}')
    r2 = r * r
    up = (1 - r2) ** 2                                   # long gentle upper slope, tangent to the chest at the rim
    low = (1 - r2 * r2) ** 1.3                           # full lower pole
    wl = np.clip(0.5 - 0.9 * r * np.sin(th), 0, 1)
    hn = (1 - wl) * up + wl * low
    q = hit[0] + np.array([s * b['spread'] * hn, b['h'] * hn, -b['sag'] * hn ** b['sag_p']])
    return hit[0], q, hn


def breasts(B, p, out):
    b = p['breast']
    NR, NA = 24, 56
    meshes = []
    for side, s in (('R', 1), ('L', -1)):
        roots, pts, tris, idx = [], [], [], {}
        rs = np.linspace(0, 1, NR) ** 0.8
        for i, r in enumerate(rs):
            for j in range(NA):
                th = 2 * np.pi * j / NA
                root, q, _ = breast_point(B, p, s, r, th)
                idx[(i, j)] = len(pts)
                roots.append(root)
                pts.append(q)
        for i in range(NR - 1):
            for j in range(NA):
                a, c = idx[(i, j)], idx[(i, (j + 1) % NA)]
                d, e = idx[(i + 1, j)], idx[(i + 1, (j + 1) % NA)]
                if i == 0:
                    tris.append((a, d, e))                 # the centre ring collapses to the apex row
                else:
                    tris += [(a, d, c), (c, d, e)]
        RV = np.hstack([np.array(roots), np.array(pts)])  # cols 0-2: root (probed for UV/weights), 3-5: the point

        def probe(q, B=B):
            return B.ray(np.array([q[0], -6.0, q[2]]), np.array([0, 1.0, 0]))
        Vs, ts, uv, w = split_by_island(B, RV, tris, probe)
        out[f'FemBreast{side}'] = shape(Vs[:, 3:], ts, uv, w, outward=[0, 1, 0])
        meshes.append((np.array(pts), np.array(tris)))
        # the nipple: below the hanging apex, along the surface normal there
        th0 = -np.pi / 2
        r0 = b['nipple_at']
        root0, base, _ = breast_point(B, p, s, r0, th0)
        e = 0.05
        du = breast_point(B, p, s, r0 + e, th0)[1] - breast_point(B, p, s, r0 - e, th0)[1]
        dv = breast_point(B, p, s, r0, th0 + e / max(r0, 0.1))[1] - breast_point(B, p, s, r0, th0 - e / max(r0, 0.1))[1]
        n = np.cross(du, dv)
        n /= np.linalg.norm(n)
        if n[1] < 0:
            n = -n
        t1 = np.cross(n, [1.0, 0, 0])
        t1 /= np.linalg.norm(t1)
        t2 = np.cross(n, t1)
        NS, NL = 16, 7
        nv, nt, nuv = [], [], []
        for i in range(NL):
            t = i / (NL - 1)
            rad = b['nipple_r'] * (1.8 - 0.8 * t) * (1 - t ** 3) ** 0.5
            for j in range(NS):
                a = 2 * np.pi * j / NS
                nv.append(base + n * (-0.25 + (b['nipple_h'] + 0.25) * t) + rad * (np.cos(a) * t1 + np.sin(a) * t2))
                nuv.append([j / NS, LINING_V[0] + (LINING_V[1] - LINING_V[0]) * t])
        for i in range(NL - 1):
            for j in range(NS):
                a, c = i * NS + j, i * NS + (j + 1) % NS
                nt += [(a, a + NS, c), (c, a + NS, c + NS)]
        nv = np.array(nv)
        h0 = probe(root0)
        nw = [B.sample(*h0[1:])[1]] * len(nv)              # the nipple rides with its root
        out[f'FemNipple{side}'] = shape(nv, nt, nuv, nw, mat=FLESH, outward=n)
        meshes.append((nv, np.array(nt)))
    return meshes


def shield(B, meshes, step=0.5):
    """how far the breasts stand off the chest along +y on an (x, z) grid, draped the way a plate lies over them:
    the cleavage filled, and a slope off the bottom and the sides instead of a tuck under"""
    V = np.vstack([m[0] for m in meshes])
    off = np.cumsum([0] + [len(m[0]) for m in meshes])[:-1]
    T = np.vstack([m[1] + o for m, o in zip(meshes, off)])
    M = Tris(V, T)
    xs = np.arange(-27.0, 27.0 + 1e-6, step)
    zs = np.arange(-56.0, -6.0 + 1e-6, step)
    H = np.zeros((len(zs), len(xs)))
    lo, hi = V.min(0), V.max(0)
    for j, z in enumerate(zs):
        if not lo[2] - 1 <= z <= hi[2] + 1:
            continue
        for i, x in enumerate(xs):
            if not lo[0] - 1 <= x <= hi[0] + 1:
                continue
            f = M.ray(np.array([x, 80.0, z]), np.array([0, -1.0, 0]))
            if f is None:
                continue
            sk = B.ray(np.array([x, -6.0, z]), np.array([0, 1.0, 0]))
            if sk is None:
                continue
            H[j, i] = max(0.0, f[0][1] - sk[0][1])
    left = np.maximum.accumulate(H, axis=1)
    right = np.maximum.accumulate(H[:, ::-1], axis=1)[:, ::-1]
    H = np.minimum(left, right)                          # cleavage bridged
    for j in range(len(zs) - 2, -1, -1):                 # downward: 0.6 per unit off the bottom of the breasts
        H[j] = np.maximum(H[j], H[j + 1] - 0.6 * step)
    for j in range(1, len(zs)):                          # upward: 1.2 per unit (the top is tangent anyway)
        H[j] = np.maximum(H[j], H[j - 1] - 1.2 * step)
    mid = len(xs) // 2
    for i in range(mid + 1, len(xs)):                    # sideways: 1.0 per unit outward
        H[:, i] = np.maximum(H[:, i], H[:, i - 1] - step)
    for i in range(mid - 1, -1, -1):
        H[:, i] = np.maximum(H[:, i], H[:, i + 1] - step)
    return {'xs': xs.round(3).tolist(), 'zs': zs.round(3).tolist(), 'H': H.round(3).tolist()}


def leg_axis(B):
    """each leg's centre (x > 0 side; mirrored) by z: the middle of the leg's slice (arms excluded)"""
    arm = np.array([any(k in max(w, key=lambda t: t[1])[0] for k in ('Arm', 'Hand', 'Finger', 'Clav'))
                    for w in B.W])
    az, ax, ay = [], [], []
    for z in np.arange(-116.0, -66.0 + 1e-6, 2.0):
        sel = (np.abs(B.V[:, 2] - z) < 2.5) & (B.V[:, 0] > 1.0) & ~arm
        if sel.sum() < 4:
            continue
        S = B.V[sel]
        az.append(float(z))
        ax.append(float((S[:, 0].min() + S[:, 0].max()) / 2))
        ay.append(float((S[:, 1].min() + S[:, 1].max()) / 2))
    az.append(-54.0)                                     # up to the hip joint (RLeg_Thigh origin)
    ax.append(11.2)
    ay.append(-1.0)

    def calm(a):                                         # slices catch the buttock crease: 5-median, 3-mean
        a = np.array(a)
        m = np.array([np.median(a[max(0, i - 2):i + 3]) for i in range(len(a))])
        return [float(np.mean(m[max(0, i - 1):i + 2])) for i in range(len(m))]
    return az, calm(ax), calm(ay)


def inside_count(B, V, tol=0.3):
    """points of a shape more than tol behind the skin along +y (hidden inside the body)"""
    n = 0
    for q in V:
        h = B.ray(np.array([q[0], -6.0, q[2]]), np.array([0, 1.0, 0]))
        if h is not None and q[1] < h[0][1] - tol:
            n += 1
    return n


if __name__ == '__main__':
    p = dict(P0)
    if len(sys.argv) > 3:
        p.update(json.load(open(sys.argv[3])))
    B = Body(sys.argv[1])
    out = {}
    meshes = breasts(B, p, out)
    C, n0 = vulva(B, p, out)
    az, ax, ay = leg_axis(B)
    p['legs'] = dict(p['legs'], az=az, ax=ax, ay=ay)
    p['shield'] = shield(B, meshes)
    json.dump(out, open(sys.argv[2], 'w'))
    json.dump(p, open(sys.argv[2].removesuffix('.json') + '.params.json', 'w'))   # warp()/bulge() read these
    H = np.array(p['shield']['H'])
    print('leg axis', [(z, round(x, 1), round(y, 1)) for z, x, y in zip(az, ax, ay)][::5])
    print('vulva at', C.round(2), 'normal', n0.round(2), '| shapes', {k: len(v['verts']) for k, v in out.items()})
    print('shield max', H.max().round(2), '| breast points hidden in the body',
          {k: inside_count(B, np.array(v['verts'])) for k, v in out.items() if k.startswith('FemBreast')})
