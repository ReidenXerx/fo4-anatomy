"""Female super mutant (Dudu 11-11, option A): the female parts laid ON the vanilla SM body, and the body warp.
  FemBreastL/R     domes on the pecs: every vertex = the chest surface (raycast from inside, +y) + a smooth bulge
                   along +y; the rim (bulge 0) lies exactly on the skin; UVs + weights from the skin under it
  FemNippleL/R     small tips at the dome apex, dark flesh (MutantGlans material)
  FemVulvaLips     raised lips round a slit on the crotch (rays from inside the pelvis, forward-down)
  FemVulvaInner    the slit floor, flesh
The body itself (topology untouched: the dismember segments stay vanilla) gets a position-only warp: pecs pushed
under the domes (60 % of the bulge, only well inside the rim), waist pinched, hips widened. warp() is shared with
the armour refit, so every piece follows the same shape. Front = +y, up = +z (skin space, RAW).
    python -I smf_geom.py <body nif> <out geom json> [params json]"""
import json
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

P0 = {
    'breast': {'cx': 9.8, 'cz': -24.0, 'R': 8.6, 'h': 6.2, 'droop': 1.2, 'nipple_r': 0.75, 'nipple_h': 0.8},
    'waist': {'z': -42.0, 'sz': 6.0, 'k': 0.92},           # x scale at the waist (gaussian in z)
    'hips': {'z': -56.0, 'sz': 5.0, 'k': 1.06},
    'body_push': 0.6, 'body_push_r': 0.6,
    'vulva': {'origin': [0.0, 2.0, -50.0], 'dir': [0.0, 0.45, -0.89], 'prefer': [0.0, 1.0, 0.0], 'depth': 6.0,
              'a0': 2.0, 'b0': 0.42, 'L': 4.0, 'W': 3.0, 'H': 1.2},
}
LINING_V = (0.006, 0.034)
FLESH = ['Materials\\Anatomy\\Creatures\\MutantGlans.bgsm', 'textures\\Anatomy\\Creatures\\MutantGlans_d.dds',
         'textures\\Anatomy\\Creatures\\MutantGlans_n.dds', 'textures\\Actors\\Supermutant\\Supermutant_s.dds']


def bulge(x, z, p):
    """the breast displacement along +y at (x, z) (both sides); 0 at and beyond the rim"""
    b = p['breast']
    out = np.zeros(np.shape(x))
    for s in (1, -1):
        # the footprint is EXACTLY the dome's circle (its rim must lie on the skin); fullness lives in the profile:
        # a gentle upper slope (1-r^2)^2, a full lower curve (1-r^4)^1.3 (both tangent to the skin at the rim)
        r2 = np.clip(((x - s * b['cx']) ** 2 + (z - b['cz']) ** 2) / b['R'] ** 2, 0, 1)
        up = (1 - r2) ** 2
        low = (1 - r2 ** 2) ** 1.3
        wl = np.clip(0.5 - (z - b['cz']) / b['R'] * (0.6 + 0.2 * b['droop']), 0, 1)
        out = out + b['h'] * np.where(r2 < 1, (1 - wl) * up + wl * low, 0)
    return out


def warp(P, p, push=None):
    """the female shape as a field over skin space (body: push=body_push; armour: push=1.0 + its clearance)"""
    P = np.array(P, dtype=float)
    out = P.copy()
    w, h = p['waist'], p['hips']
    k = 1 + (w['k'] - 1) * np.exp(-((P[:, 2] - w['z']) / w['sz']) ** 2) \
        + (h['k'] - 1) * np.exp(-((P[:, 2] - h['z']) / h['sz']) ** 2)
    out[:, 0] = P[:, 0] * k
    front = P[:, 1] > 0
    bl = bulge(P[:, 0], P[:, 2], p)
    if push is None:                                          # the body: under the domes, only well inside the rim
        b = p['breast']
        inner = np.zeros(len(P), bool)
        for s in (1, -1):
            inner |= ((P[:, 0] - s * b['cx']) ** 2 + (P[:, 2] - b['cz']) ** 2) < (p['body_push_r'] * b['R']) ** 2
        out[:, 1] += np.where(front & inner, p['body_push'] * bl, 0)
    else:
        out[:, 1] += np.where(front, push * bl, 0)
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


def breasts(B, p, out):
    b = p['breast']
    NR, NA = 16, 40
    for side, s in (('R', 1), ('L', -1)):
        pts, tris, idx = [], [], {}
        rs = np.linspace(0, 1, NR) ** 0.85
        for i, r in enumerate(rs):
            for j in range(NA):
                th = 2 * np.pi * j / NA
                x = s * b['cx'] + r * b['R'] * np.cos(th)
                z = b['cz'] + r * b['R'] * np.sin(th) * 1.02
                h = B.ray(np.array([x, -6.0, z]), np.array([0, 1.0, 0]))
                if h is None:
                    raise SystemExit(f'no chest surface at x {x:.1f} z {z:.1f}')
                idx[(i, j)] = len(pts)
                pts.append(h[0] + np.array([0, float(bulge(np.array([x]), np.array([z]), p)[0]), 0]))
        for i in range(NR - 1):
            for j in range(NA):
                a, c = idx[(i, j)], idx[(i, (j + 1) % NA)]
                d, e = idx[(i + 1, j)], idx[(i + 1, (j + 1) % NA)]
                if i == 0:
                    tris.append((a, d, e))                 # the centre ring collapses to the apex row
                else:
                    tris += [(a, d, c), (c, d, e)]
        V = np.array(pts)

        def probe(q, B=B):
            return B.ray(np.array([q[0], -6.0, q[2]]), np.array([0, 1.0, 0]))
        Vs, ts, uv, w = split_by_island(B, V, tris, probe)
        out[f'FemBreast{side}'] = shape(Vs, ts, uv, w, outward=[0, 1, 0])
        # the nipple: a small rounded cone at the apex, a little below centre
        apex = V[idx[(0, 0)]]
        cz = apex[2] - b['droop'] * 0.4
        h0 = B.ray(np.array([s * b['cx'], -6.0, cz]), np.array([0, 1.0, 0]))[0]
        base = h0 + np.array([0, float(bulge(np.array([s * b['cx']]), np.array([cz]), p)[0]), 0])
        NS, NL = 14, 6
        nv, nt, nuv = [], [], []
        for i in range(NL):
            t = i / (NL - 1)
            rad = b['nipple_r'] * (1.5 - 0.5 * t) * (1 - t ** 3) ** 0.5
            for j in range(NS):
                a = 2 * np.pi * j / NS
                nv.append(base + np.array([rad * np.cos(a), -0.15 + (b['nipple_h'] + 0.15) * t, rad * np.sin(a)]))
                nuv.append([j / NS, LINING_V[0] + (LINING_V[1] - LINING_V[0]) * t])
        for i in range(NL - 1):
            for j in range(NS):
                a, c = i * NS + j, i * NS + (j + 1) % NS
                nt += [(a, a + NS, c), (c, a + NS, c + NS)]
        nv = np.array(nv)
        nw = [B.sample(*probe(q)[1:])[1] for q in nv]
        out[f'FemNipple{side}'] = shape(nv, nt, nuv, nw, mat=FLESH, outward=[0, 1, 0])


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


def clearance(B, p, out):
    """the warped body must stay under the domes: sample the dome footprint, compare the body's surface (warped
    vertices, same triangles) with the dome's along +y"""
    Vw = warp(B.V, p)
    V0, V1, V2 = Vw[B.T[:, 0]], Vw[B.T[:, 1]], Vw[B.T[:, 2]]
    E1, E2 = V1 - V0, V2 - V0
    worst = 1e9
    b = p['breast']
    for s in (1, -1):
        for x in np.linspace(s * b['cx'] - b['R'], s * b['cx'] + b['R'], 25):
            for z in np.linspace(b['cz'] - b['R'], b['cz'] + b['R'], 25):
                bl = float(bulge(np.array([x]), np.array([z]), p)[0])
                if bl <= 0.05:
                    continue
                h = B.ray(np.array([x, -6.0, z]), np.array([0, 1.0, 0]))
                if h is None:
                    continue
                dome = h[0][1] + bl
                o, d = np.array([x, -6.0, z]), np.array([0, 1.0, 0])
                pp = np.cross(d, E2)
                det = (E1 * pp).sum(1)
                ok = np.abs(det) > 1e-9
                inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
                ss = o - V0
                u = (ss * pp).sum(1) * inv
                q = np.cross(ss, E1)
                v = (q * d).sum(1) * inv
                t = (E2 * q).sum(1) * inv
                hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
                if hit.any():
                    body = o[1] + t[hit].min()
                    # the dome meets the skin at its rim by design: ask for clearance in proportion to the bulge
                    worst = min(worst, (dome - body) - min(0.15, 0.5 * bl))
    return worst


if __name__ == '__main__':
    p = dict(P0)
    if len(sys.argv) > 3:
        p.update(json.load(open(sys.argv[3])))
    B = Body(sys.argv[1])
    out = {}
    breasts(B, p, out)
    C, n0 = vulva(B, p, out)
    for push, rr in ((0.6, 0.6), (0.5, 0.55), (0.45, 0.5), (0.4, 0.45), (0.3, 0.4), (0.2, 0.35), (0.0, 0.0)):
        p['body_push'], p['body_push_r'] = push, rr        # the most the coarse pecs can rise without poking out
        gap = clearance(B, p, out)
        if gap >= 0.0:
            break
    json.dump(out, open(sys.argv[2], 'w'))
    json.dump(p, open(sys.argv[2].removesuffix('.json') + '.params.json', 'w'), indent=1)   # warp() reads these
    print('body push', p['body_push'], 'inside', p['body_push_r'], 'R')
    print('vulva at', C.round(2), 'normal', n0.round(2), '| shapes', {k: len(v['verts']) for k, v in out.items()},
          '| min dome-over-body gap', round(gap, 3))
    if gap < 0.0:
        raise SystemExit(f'the warped body pokes through the breasts (gap {gap:.3f})')
