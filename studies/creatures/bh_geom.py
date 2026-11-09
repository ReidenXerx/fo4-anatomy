"""Our behemoth genitals (replace UAP's 'Behemoth_Penis1' in UAP's nude behemoth body: same shape name, same morph
names; UAP's is Pelvis-only and morph-driven, so is ours). Shape space of UAP's Behemoth_Penis1 (t = 0):
  Behemoth_Penis1      thick veined mutant shaft + a heavy two-lobed sack, behemoth lower-body material (swaps apply),
                       UVs unrolled into a veined skin window
  Behemoth_PenisGlans  bulbous glans, MutantGlans material
UAP's sack = its vertices the Erection morph barely moves; its shaft = the rest. The shaft centreline per state =
Catmull-Rom through the means of 5 bins along the rest shaft axis (+ tip), cubic-smoothed; one swell ratio per state
(Erection only); the sack takes UAP's nearest sack deltas.  python -I bh_geom.py <out.json>"""
import json
import math
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UAP_NIF = r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\supermutantbehemoth\characterassets\supermutantbehemoth.nif'
UAP_TRI = r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\supermutantbehemoth\characterassets\SuperMutantBehemoth.tri'
NAME, GLANS = 'Behemoth_Penis1', 'Behemoth_PenisGlans'
SKIN_UV = (0.62, 0.72, 0.60, 0.78)
MORPHS = ['Erection', 'Erection Up', 'Erection Down', 'Penis Adjust']
SEG, NB = 32, 5

m = nif.Nif(UAP_NIF)
P = np.array(m.shape(NAME).positions())
tri = {n: (mu, d) for n, mu, d in dict((s, ms) for s, ms in tri_sync.read(UAP_TRI))[NAME]}


def morphed(name):
    Q = P.copy()
    if name:
        mu, d = tri[name]
        for i, v in d.items():
            Q[i] += np.array(v, float) * mu
    return Q


dE = np.linalg.norm(morphed('Erection') - P, axis=1)
sack = np.where(dE < 0.15 * dE.max())[0]
shaft = np.where(dE >= 0.15 * dE.max())[0]
c0 = P[shaft].mean(0)
ax = np.linalg.svd(P[shaft] - c0, full_matrices=False)[2][0]
if (P[shaft] - c0) @ ax @ np.ones(len(shaft)) < 0:
    pass
proj = (P[shaft] - c0) @ ax
# root end = the end nearer the sack
if np.linalg.norm(P[shaft][proj.argmin()] - P[sack].mean(0)) > np.linalg.norm(P[shaft][proj.argmax()] - P[sack].mean(0)):
    ax, proj = -ax, -proj
bins = np.minimum(((proj - proj.min()) / np.ptp(proj) * NB).astype(int), NB - 1)
# the low-motion set also holds UAP's penis BASE and pubic blend (above the root): the sack is only what hangs BELOW
# the root (Dudu 11-09: "isnt behemoth penis upside down?" - the sack sat over the penis)
root_z = float(P[shaft][np.argmin(proj)][2])
base = sack[P[sack][:, 2] >= root_z - 1.0]
sack = sack[P[sack][:, 2] < root_z - 1.0]
# UAP's penis hangs from the PUBIS (top of that low-motion base, ~z 135): the shaft runs pubis -> base mid -> the
# moving part; Erection only lifts the lower half (Dudu 11-09: still "upside down", "doesn't connect to ballsack")
bz = P[base][:, 2]
top = base[bz >= np.percentile(bz, 85)]
PUBIS = P[top].mean(0)
PUBIS[0] = 0.0
END_A = P[shaft][np.argmin(proj)]
BASE_MID = 0.5 * (PUBIS + END_A)
BASE_MID[0] = 0.0
print('sack below root', len(sack), 'root z', round(root_z, 1), 'pubis', PUBIS.round(1), 'base mid', BASE_MID.round(1))
tip_set = shaft[np.argsort(proj)[-14:]]
print('shaft', len(shaft), 'sack', len(sack), 'axis', ax.round(2), 'length', round(float(np.ptp(proj)), 1))


def nodes(Q):
    """pubis + base mid (fixed in every state: UAP's base does not move) + 5 shaft bins + tip"""
    return np.array([PUBIS, BASE_MID] + [Q[shaft[bins == b]].mean(0) for b in range(NB)] + [Q[tip_set].mean(0)])


REST_ROOT = None


class Curve:
    def __init__(self, Q):
        n = nodes(Q)
        if REST_ROOT is not None:                       # every state starts at the REST root: stays on the body
            n[0] = REST_ROOT
        K = len(n) - 1
        ext = np.vstack([2 * n[0] - n[1], n, 2 * n[-1] - n[-2]])
        self.s = np.linspace(0, K, 100 * K + 1)
        pts = []
        for s in self.s:
            k = min(int(s), K - 1)
            t = s - k
            p0, p1, p2, p3 = ext[k], ext[k + 1], ext[k + 2], ext[k + 3]
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        pts = np.array(pts)
        self.K = K
        self.p = np.stack([np.polyval(np.polyfit(self.s, pts[:, k], 3), self.s) for k in range(3)], -1)

    def at(self, t):                                        # t in [0, 1] along the shaft (extrapolated a little)
        s = t * self.K
        sc = min(max(s, 0.0), self.K)
        i = min(int(sc * 100), len(self.p) - 2)
        f = sc * 100 - i
        c = self.p[i] * (1 - f) + self.p[i + 1] * f
        T = self.p[min(i + 2, len(self.p) - 1)] - self.p[max(i - 1, 0)]
        T /= np.linalg.norm(T)
        c = c + T * (s - sc) * np.linalg.norm(self.p[-1] - self.p[0]) / self.K * 0
        X = np.array([1.0, 0, 0])
        N = np.cross(T, X)
        N /= np.linalg.norm(N)
        X = np.cross(N, T)
        return c, T, X, N


curves = {'': Curve(P)}
REST_ROOT = nodes(P)[0]
for n in MORPHS:
    curves[n] = Curve(morphed(n))


def mean_radius(Q, curve):
    r = [np.linalg.norm(curve.p - Q[i], axis=1).min() for i in shaft[::2]]
    return float(np.median(r))


R_rest = mean_radius(P, curves[''])
ratio = {n: 1.0 for n in [''] + MORPHS}
ratio['Erection'] = float(np.clip(mean_radius(morphed('Erection'), curves['Erection']) / R_rest, 0.8, 1.6))
R0 = R_rest * 0.95
print('R_rest', round(R_rest, 2), 'erect ratio', round(ratio['Erection'], 2))
VEINS = [(0.4, 0.0), (2.5, 1.7), (4.3, 3.1), (5.6, 4.4)]
T_RIM = 0.84


def profile(t):
    base = 1.12 - 0.12 * min(max(t, 0) / 0.10, 1.0)
    return base * (1 - 0.06 * t) * (1 + 0.04 * math.sin(t * 15.0 + 0.6))


def vein(t, th):
    env = max(0.0, min((t - 0.06) / 0.08, 1.0, (0.80 - t) / 0.08))
    h = 0.0
    for th0, ph in VEINS:
        tv = th0 + 0.5 * math.sin(2 * math.pi * (1.3 * t + ph / 6.28))
        dth = abs(((th - tv + math.pi) % (2 * math.pi)) - math.pi)
        h = max(h, math.exp(-(dth / 0.12) ** 2))
    return 0.09 * env * h


parts = {NAME: dict(v=[], uv=[], f=[], m={n: [] for n in MORPHS}, pod=[]),
         GLANS: dict(v=[], uv=[], f=[], m={n: [] for n in MORPHS}, pod=[])}


def place(state, t, th, rho):
    c, T, X, N = curves[state].at(t)
    return c + rho * ratio[state] * (math.cos(th) * X + math.sin(th) * N)


def tube(part, ts, rad, uvfn):
    Pp = parts[part]
    rows = []
    for t in ts:
        row = []
        for k in range(SEG + 1):
            th = 2 * math.pi * k / SEG + math.pi / 2
            r = rad(t, th) * R0
            p0 = place('', t, th, r)
            Pp['v'].append(p0)
            Pp['uv'].append(uvfn(t, k / SEG))
            # the root stays on the body: morphs fade in over the first fifth (UAP's bin-0 centre moves forward in
            # Erection, which floated our root off the body)
            a = 1.0                                           # (root anchoring is done by the curves' shared root node)
            for n in MORPHS:
                Pp['m'][n].append((place(n, t, th, r) - p0) * a)
            Pp['pod'].append(False)
            row.append(len(Pp['v']) - 1)
        rows.append(row)
    for a in range(len(rows) - 1):
        for k in range(SEG):
            q = (rows[a][k], rows[a][k + 1], rows[a + 1][k + 1], rows[a + 1][k])
            Pp['f'] += [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
    return rows


u0, u1, v0, v1 = SKIN_UV
tube(NAME, list(np.linspace(-0.04, T_RIM, 34)), lambda t, th: profile(t) + vein(t, th),
     lambda t, u: (u0 + (u1 - u0) * u, v0 + (v1 - v0) * (t + 0.04) / (T_RIM + 0.04)))


def glans_r(t, th):
    e = (t - T_RIM) / (1 - T_RIM)
    if e < 0.08:
        return profile(T_RIM) * (1.0 + 1.6 * e)
    if e < 0.22:
        return profile(T_RIM) * 1.13
    q = (e - 0.22) / 0.78
    return max(profile(T_RIM) * 1.13 * math.sqrt(max(1 - q ** 2.3, 0)), 0.05)


rows = tube(GLANS, [T_RIM, T_RIM + 0.012, T_RIM + 0.03] + list(np.linspace(T_RIM + 0.05, 1.0, 9)), glans_r,
            lambda t, u: (u, (t - T_RIM) / (1 - T_RIM)))
Gp = parts[GLANS]
c = place('', 1.0, 0, 0)
Gp['v'].append(c)
Gp['uv'].append((0.5, 1.0))
for n in MORPHS:
    Gp['m'][n].append(place(n, 1.0, 0, 0) - c)
Gp['pod'].append(False)
for k in range(SEG):
    Gp['f'].append((rows[-1][k], rows[-1][k + 1], len(Gp['v']) - 1))

S = P[sack]
lo, hi = np.percentile(S, 3, axis=0), np.percentile(S, 97, axis=0)
axs = (hi - lo) / 2 * 1.0
cb = (hi + lo) / 2
cb[0] = 0.0                                                   # symmetric about the body's centre line
axs[0] = float(np.percentile(np.abs(S[:, 0]), 92))
# the sack hangs from the shaft base: its top reaches up into the base, its front into the shaft (no gap)
top_z = max(cb[2] + axs[2], BASE_MID[2])
bot_z = cb[2] - axs[2]
cb[2], axs[2] = (top_z + bot_z) / 2, (top_z - bot_z) / 2
front_y = max(cb[1] + axs[1], BASE_MID[1] - R0 * 0.3)
back_y = cb[1] - axs[1]
cb[1], axs[1] = (front_y + back_y) / 2, (front_y - back_y) / 2
SP = parts[NAME]
LAT, LON = 20, 40
grid = []
for i in range(LAT + 1):
    phi = math.pi * i / LAT
    row = []
    for j in range(LON + 1):
        lam = 2 * math.pi * j / LON
        d = np.array([math.sin(phi) * math.cos(lam), math.sin(phi) * math.sin(lam), math.cos(phi)])
        sag = 1.0 + 0.10 * max(0.0, -d[2])
        crease = 1.0 - 0.20 * math.exp(-(d[0] / 0.12) ** 2) * math.sin(phi) ** 2
        p = cb + d * axs * sag * crease
        uu = 0.5 + 0.45 * (p[1] - cb[1]) / axs[1]
        vv = 0.5 - 0.45 * (p[2] - cb[2]) / axs[2]
        SP['v'].append(p)
        SP['uv'].append((u0 + (u1 - u0) * uu, v0 + (v1 - v0) * vv))
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
    out[name] = dict(verts=V.tolist(), uv=[list(map(float, u)) for u in pt['uv']],
                     weights=[{'Pelvis': 1.0}] * len(V), tris=pt['f'],
                     morphs={n: np.array([list(x) for x in pt['m'][n]]).tolist() for n in MORPHS})
    E = V + np.array(out[name]['morphs']['Erection'])
    print(name, len(V), 'verts', 'rest', V.min(0).round(1), V.max(0).round(1), 'erect', E.min(0).round(1),
          E.max(0).round(1))
out['_uap_penis_bbox'] = [P.min(0).tolist(), P.max(0).tolist()]
json.dump(out, open(sys.argv[1], 'w'))
print('uap rest', P.min(0).round(1), P.max(0).round(1), 'erect', morphed('Erection').min(0).round(1),
      morphed('Erection').max(0).round(1))
