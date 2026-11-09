"""Our super mutant genitals (replace UAP's 'SM Penis' on supermutantbody.nif: same bones, same morph names).
In the SHAPE SPACE of UAP's SM Penis (t = 0):
  SM Penis       thick mutant shaft (three meandering raised veins, slight lumps) + a heavy two-lobed sack; the
                 super mutant BODY material (its material swaps apply), UVs unrolled into a veined skin window
  SM PenisGlans  a bulbous glans with a flared rim; own material (MutantGlans)
Weights: shaft rings blend smoothly along PrivatesBase -> Penis1 -> Penis2 -> Penis3 -> Penis4 (UAP's chain); the
sack on Balls1 (top) -> Balls2 (bottom), its very top on PrivatesBase. Rest + Erection/Up/Down follow UAP's measured
centrelines (Catmull-Rom through UAP's per-bone region means, cubic-smoothed; one swell ratio per state); the sack
takes UAP's nearest sack deltas.
    python -I sm_geom.py <out.json>"""
import json
import math
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UAP_NIF = r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\supermutant\characterassets\supermutantbody.nif'
UAP_TRI = r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\supermutant\characterassets\SupermutantBody.tri'
SKIN_UV = (0.656, 0.735, 0.773, 0.933)
MORPHS = ['Erection', 'Erection Up', 'Erection Down']
SEG = 28

m = nif.Nif(UAP_NIF)
sh = m.shape('SM Penis')
P = np.array(sh.positions())
bones, _ = m.skin(sh)
W = np.zeros((len(P), len(bones)))
for i in range(len(P)):
    for slot, w in sh.skin_weights(i):
        W[i, slot] += w
bi = {b: k for k, b in enumerate(bones)}
dom = W.argmax(1)
sack = np.where((dom == bi['Balls1']) | (dom == bi['Balls2']))[0]
reg = {k: np.where(dom == bi[k])[0] for k in ('Pelvis', 'Penis2', 'Penis3', 'Penis4')}
tri = {n: (mu, d) for n, mu, d in dict((s, ms) for s, ms in tri_sync.read(UAP_TRI))['SM Penis']}


def morphed(name):
    Q = P.copy()
    if name:
        mu, d = tri[name]
        for i, v in d.items():
            Q[i] += np.array(v, float) * mu
    return Q


d34 = P[reg['Penis4']].mean(0) - P[reg['Penis3']].mean(0)
tip_set = reg['Penis4'][np.argsort(P[reg['Penis4']] @ d34)[-14:]]
root_set = reg['Pelvis']


def nodes(Q):
    n = [Q[reg[k]].mean(0) for k in ('Penis2', 'Penis3', 'Penis4')]
    root = Q[root_set].mean(0)
    return np.array([root] + n + [Q[tip_set].mean(0)])            # s: 0 root, 1 P2, 2 P3, 3 P4, 4 tip


class Curve:
    def __init__(self, Q):
        n = nodes(Q)
        ext = np.vstack([2 * n[0] - n[1], n, 2 * n[-1] - n[-2]])
        self.s = np.linspace(0, 4, 401)
        pts = []
        for s in self.s:
            k = min(int(s), 3)
            t = s - k
            p0, p1, p2, p3 = ext[k], ext[k + 1], ext[k + 2], ext[k + 3]
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        pts = np.array(pts)
        self.p = np.stack([np.polyval(np.polyfit(self.s, pts[:, k], 3), self.s) for k in range(3)], -1)

    def at(self, s):
        s = min(max(s, 0.0), 4.0)
        k = min(int(s * 100), 399)
        f = s * 100 - k
        c = self.p[k] * (1 - f) + self.p[k + 1] * f
        T = self.p[min(k + 2, 400)] - self.p[max(k - 1, 0)]
        T /= np.linalg.norm(T)
        X = np.array([1.0, 0, 0])
        N = np.cross(T, X)
        N /= np.linalg.norm(N)
        X = np.cross(N, T)
        return c, T, X, N


curves = {'': Curve(P)}
for n in MORPHS:
    curves[n] = Curve(morphed(n))
shaft = np.where(~np.isin(np.arange(len(P)), sack))[0]


def mean_radius(Q, curve):
    r = []
    for i in shaft[::3]:
        best = np.argmin(np.linalg.norm(curve.p - Q[i], axis=1))
        r.append(np.linalg.norm(curve.p[best] - Q[i]))
    return float(np.median(r))


R_rest = mean_radius(P, curves[''])
ratio = {n: mean_radius(morphed(n), curves[n]) / R_rest for n in MORPHS}
ratio.update({'': 1.0, 'Erection Up': 1.0, 'Erection Down': 1.0})   # Up/Down only redirect (radius probe noisy)
R0 = R_rest * 0.95
print('R_rest', round(R_rest, 2), 'ratios', {k: round(v, 2) for k, v in ratio.items()})

CHAIN = [('PrivatesBase', 0.0), ('Penis1', 0.5), ('Penis2', 1.0), ('Penis3', 2.0), ('Penis4', 3.0)]


def chain_w(s):
    if s <= 0:
        return {'PrivatesBase': 1.0}
    for (a, sa), (b, sb) in zip(CHAIN, CHAIN[1:]):
        if s <= sb:
            f = (s - sa) / (sb - sa)
            return {a: 1 - f, b: f} if f > 1e-3 else {a: 1.0}
    return {'Penis4': 1.0}


VEINS = [(0.4, 0.0), (2.4, 1.7), (4.2, 3.1)]                      # (theta0, phase)


def profile(t):
    """shaft radius at t (0 root .. 0.84 rim) x R0, plus lumps"""
    base = 1.12 - 0.12 * min(t / 0.10, 1.0)
    return base * (1 - 0.06 * t) * (1 + 0.035 * math.sin(t * 17.0 + 0.6))


def vein(t, th):
    env = max(0.0, min((t - 0.06) / 0.08, 1.0, (0.80 - t) / 0.08))
    h = 0.0
    for th0, ph in VEINS:
        tv = th0 + 0.55 * math.sin(2 * math.pi * (1.4 * t + ph / 6.28))
        dth = abs(((th - tv + math.pi) % (2 * math.pi)) - math.pi)
        h = max(h, math.exp(-(dth / 0.13) ** 2))
    return 0.10 * env * h


T_RIM = 0.84
parts = {'SM Penis': dict(v=[], uv=[], w=[], f=[], m={n: [] for n in MORPHS}, pod=[]),
         'SM PenisGlans': dict(v=[], uv=[], w=[], f=[], m={n: [] for n in MORPHS}, pod=[])}


def place(state, s, th, rho):
    c, T, X, N = curves[state].at(s)
    return c + rho * ratio[state] * (math.cos(th) * X + math.sin(th) * N)


def tube(part, ts, rad, uvfn, flip=False):
    P_ = parts[part]
    rows = []
    for t in ts:
        row = []
        s = 4.0 * t
        for k in range(SEG + 1):
            th = 2 * math.pi * k / SEG + math.pi / 2
            r = rad(t, th) * R0
            p0 = place('', s, th, r)
            P_['v'].append(p0)
            P_['uv'].append(uvfn(t, k / SEG))
            P_['w'].append(chain_w(s))
            for n in MORPHS:
                P_['m'][n].append(place(n, s, th, r) - p0)
            P_['pod'].append(False)
            row.append(len(P_['v']) - 1)
        rows.append(row)
    for a in range(len(rows) - 1):
        for k in range(SEG):
            q = (rows[a][k], rows[a][k + 1], rows[a + 1][k + 1], rows[a + 1][k])
            P_['f'] += [(q[0], q[2], q[1]), (q[0], q[3], q[2])] if flip else [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
    return rows


u0, u1, v0, v1 = SKIN_UV
shaft_ts = list(np.linspace(-0.06, T_RIM, 34))
tube('SM Penis', shaft_ts, lambda t, th: profile(max(t, 0)) + vein(t, th),
     lambda t, u: (u0 + (u1 - u0) * u, v0 + (v1 - v0) * (t + 0.06) / (T_RIM + 0.06)))
# glans: rim flare then a bulbous dome to the tip (own texture: v 0 rim .. 1 tip)
gts = [T_RIM, T_RIM + 0.012, T_RIM + 0.03] + list(np.linspace(T_RIM + 0.05, 1.0, 9))


def glans_r(t, th):
    e = (t - T_RIM) / (1 - T_RIM)
    if e < 0.08:
        return profile(T_RIM) * (1.0 + 1.6 * e)
    if e < 0.22:
        return profile(T_RIM) * 1.13
    q = (e - 0.22) / 0.78
    return max(profile(T_RIM) * 1.13 * math.sqrt(max(1 - q ** 2.3, 0)), 0.05)


rows = tube('SM PenisGlans', gts, glans_r, lambda t, u: (u, (t - T_RIM) / (1 - T_RIM)))
G = parts['SM PenisGlans']                                          # tip point
c = place('', 4.0, 0, 0)
G['v'].append(c)
G['uv'].append((0.5, 1.0))
G['w'].append({'Penis4': 1.0})
for n in MORPHS:
    G['m'][n].append(place(n, 4.0, 0, 0) - c)
G['pod'].append(False)
for k in range(SEG):
    G['f'].append((rows[-1][k], rows[-1][k + 1], len(G['v']) - 1))

# sack: two-lobed, hanging, at UAP's sack
S = P[sack]
lo, hi = np.percentile(S, 3, axis=0), np.percentile(S, 97, axis=0)
ax = (hi - lo) / 2 * 1.02
cb = (hi + lo) / 2
SP = parts['SM Penis']
LAT, LON = 18, 36
grid = []
for i in range(LAT + 1):
    phi = math.pi * i / LAT
    row = []
    for j in range(LON + 1):
        lam = 2 * math.pi * j / LON
        d = np.array([math.sin(phi) * math.cos(lam), math.sin(phi) * math.sin(lam), math.cos(phi)])
        sag = 1.0 + 0.10 * max(0.0, -d[2])                         # heavier at the bottom
        crease = 1.0 - 0.20 * math.exp(-(d[0] / 0.12) ** 2) * math.sin(phi) ** 2
        p = cb + d * ax * sag * crease
        hgt = (cb[2] + ax[2] - p[2]) / (2 * ax[2])                 # 0 top .. 1 bottom
        if hgt < 0.15:
            f = hgt / 0.15
            w = {'PrivatesBase': 1 - f, 'Balls1': f} if f > 1e-3 else {'PrivatesBase': 1.0}
        else:
            f = min((hgt - 0.15) / 0.6, 1.0)
            w = {'Balls1': 1 - f, 'Balls2': f} if f < 1 else {'Balls2': 1.0}
        uu = 0.5 + 0.45 * (p[1] - cb[1]) / ax[1]
        vv = 0.5 - 0.45 * (p[2] - cb[2]) / ax[2]
        SP['v'].append(p)
        SP['uv'].append((u0 + (u1 - u0) * uu, v0 + (v1 - v0) * vv))
        SP['w'].append(w)
        SP['pod'].append(True)
        for n in MORPHS:
            SP['m'][n].append(None)
        row.append(len(SP['v']) - 1)
    grid.append(row)
for i in range(LAT):
    for j in range(LON):
        SP['f'] += [(grid[i][j], grid[i + 1][j], grid[i + 1][j + 1]), (grid[i][j], grid[i + 1][j + 1], grid[i][j + 1])]
for n in MORPHS:
    D = morphed(n)[sack] - S
    for k, isp in enumerate(SP['pod']):
        if isp:
            near = np.argsort(np.linalg.norm(S - SP['v'][k], axis=1))[:4]
            SP['m'][n][k] = D[near].mean(0)

out = {}
for name, pt in parts.items():
    V = np.array(pt['v'])
    out[name] = dict(verts=V.tolist(), uv=[list(map(float, u)) for u in pt['uv']], weights=pt['w'],
                     tris=pt['f'], morphs={n: np.array([list(x) for x in pt['m'][n]]).tolist() for n in MORPHS})
    E = V + np.array(out[name]['morphs']['Erection'])
    print(name, len(V), 'verts', len(pt['f']), 'tris', 'rest', V.min(0).round(1), V.max(0).round(1),
          'erect', E.min(0).round(1), E.max(0).round(1))
out['_uap_penis_bbox'] = [P.min(0).tolist(), P.max(0).tolist()]
json.dump(out, open(sys.argv[1], 'w'))
print('uap rest', P.min(0).round(1), P.max(0).round(1), 'uap erect', morphed('Erection').min(0).round(1),
      morphed('Erection').max(0).round(1))
