"""Female creature genitals (Dudu 11-10): a vulva on the rear midline below the tail root and (where lore-fitting)
teats along the belly, laid ON the vanilla body: every vertex placed by raycasts against the body, UVs and skin
weights taken from the body triangle under it (seamless skin, body-island split as for the deathclaw vent).
  FemVulvaLips   raised lips round a vertical slit, body material
  FemVulvaInner  the slit floor, flesh (CaninePenis' lining rows, v < 0.04)
  FemTeats       pairs of small rounded teats on the belly, body material
Rays for the rear start INSIDE the body and go out, so a tail behind the rump never catches them.
    python -I fem_geom.py <body nif> <out.json> <params json>
params: {"vulva": {"z": <height>, "a0": slit half-length, "b0": half-opening, "L": lens half-length, "W": half-width,
         "H": lip height, "depth": inside start}, "teats": [[y, x, r, h], ...]}"""
import json
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

body_nif, out_json, params = sys.argv[1], sys.argv[2], json.loads(open(sys.argv[3]).read())
bm = nif.Nif(body_nif)
bs = max(bm.shapes(), key=lambda s: s.count)
BV = np.array(bs.positions())
BUV = np.array([bs.uv(i) for i in range(bs.count)])
BT = np.array(bs.triangles())
names, _ = bm.skin(bs)
BW = [[(names[b], w) for b, w in bs.skin_weights(i) if w > 0] for i in range(bs.count)]
V0, V1, V2 = BV[BT[:, 0]], BV[BT[:, 1]], BV[BT[:, 2]]
E1, E2 = V1 - V0, V2 - V0
LINING_V = (0.006, 0.034)


def ray(o, d, first=True):
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
        return None
    k = np.where(hit)[0][np.argmin(t[hit])]
    return o + t[k] * d, k, np.array([1 - u[k] - v[k], u[k], v[k]])


def sample(k, bc):
    tri = BT[k]
    uv = (BUV[tri] * bc[:, None]).sum(0)
    w = {}
    for vi, b in zip(tri, bc):
        for n, ww in BW[vi]:
            w[n] = w.get(n, 0.0) + ww * b
    tot = sum(w.values())
    return uv, {a: b / tot for a, b in w.items()}


# body UV islands (index connectivity)
par = np.arange(len(BV))


def find(a):
    while par[a] != a:
        par[a] = par[par[a]]
        a = par[a]
    return a


for a_, b_, c_ in BT:
    for x_, y_ in ((a_, b_), (b_, c_)):
        ra, rb = find(x_), find(y_)
        if ra != rb:
            par[ra] = rb
ISL = np.array([find(i) for i in range(len(BV))])
T_ISL = ISL[BT[:, 0]]
T_CEN = (V0 + V1 + V2) / 3


def island_uv(p, isl):
    cand = np.where(T_ISL == isl)[0]
    k = cand[np.argmin(np.linalg.norm(T_CEN[cand] - p, axis=1))]
    a = V0[k]
    e0, e1, e2 = V1[k] - a, V2[k] - a, p - a
    d00, d01, d11, d20, d21 = e0 @ e0, e0 @ e1, e1 @ e1, e2 @ e0, e2 @ e1
    den = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    uvs = BUV[BT[k]]
    return ((1 - v - w) * uvs[0] + v * uvs[1] + w * uvs[2]).tolist()


def split_islands(V, tris, pts, probe):
    """every triangle takes the body island under its centroid; shared vertices across islands are split"""
    tri_isl = []
    for t in tris:
        hit = probe(V[list(t)].mean(0))
        tri_isl.append(int(T_ISL[hit[1]]) if hit else -1)
    newid, order, ntris = {}, [], []
    for t, isl in zip(tris, tri_isl):
        nt = []
        for vi in t:
            if (vi, isl) not in newid:
                newid[(vi, isl)] = len(order)
                order.append((vi, isl))
            nt.append(newid[(vi, isl)])
        ntris.append(nt)
    src = [vi for vi, _ in order]
    uv = []
    for vi, isl in order:                     # the UV of the skin right under the vertex; nearest-triangle
        hit = probe(V[vi])                    # extrapolation only off the island (it wanders on dense meshes)
        if hit and isl >= 0 and T_ISL[hit[1]] == isl:
            uv.append(sample(hit[1], hit[2])[0].tolist())
        else:
            uv.append(island_uv(V[vi], isl) if isl >= 0 else [0.5, 0.5])
    return V[src], ntris, uv, src


def weights_at(V, probe):
    out = []
    for p in V:
        hit = probe(p)
        out.append(sample(hit[1], hit[2])[1] if hit else {'Pelvis': 1.0})
    return out


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


def shape(V, tris, uv, w, mat=None):
    bones = sorted({b for x in w for b in x})
    out = {'verts': np.asarray(V).round(5).tolist(), 'tris': [list(map(int, t)) for t in tris], 'uv': uv,
           'normals': normals(np.asarray(V), tris).round(5).tolist(),
           'weights': {b: [round(x.get(b, 0.0), 5) for x in w] for b in bones}, 'morphs': {}}
    if mat:
        out['mat'] = mat
    return out


OUT = {}
# ---------------------------------------------------------------- the vulva on the rear midline
vp = params['vulva']
depth = vp.get('depth', 12.0)
pelvis_y = vp['inside_y']                                  # a y well inside the rump at that height
hit = ray(np.array([0.0, pelvis_y, vp['z']]), np.array([0.0, -1.0, 0.0]))
if hit is None:
    raise SystemExit('no rump surface behind the pelvis at that height')
P0 = hit[0]
e = 0.6


def rear_pt(x, z):
    h = ray(np.array([x, pelvis_y, z]), np.array([0.0, -1.0, 0.0]))
    return h[0] if h else None


dz = rear_pt(0, vp['z'] + e) - rear_pt(0, vp['z'] - e)
dx = rear_pt(e, vp['z']) - rear_pt(-e, vp['z'])
n0 = np.cross(dz, dx)
n0 /= np.linalg.norm(n0)
if n0[1] > 0:
    n0 = -n0                                               # outward = backwards (-y)
t0 = np.cross(n0, np.array([1.0, 0.0, 0.0]))
t0 = t0 if t0[2] > 0 else -t0
b0 = np.array([1.0, 0.0, 0.0])


def surf(x, s):
    o = P0 + s * t0 + x * b0 - depth * n0
    h = ray(o, n0)
    if h is None:
        raise SystemExit(f'no surface at x {x:.2f} s {s:.2f}')
    p = h[0]
    q1 = ray(P0 + (s + e) * t0 + x * b0 - depth * n0, n0)[0]
    q2 = ray(P0 + (s - e) * t0 + x * b0 - depth * n0, n0)[0]
    q3 = ray(P0 + s * t0 + (x + e) * b0 - depth * n0, n0)[0]
    q4 = ray(P0 + s * t0 + (x - e) * b0 - depth * n0, n0)[0]
    n = np.cross(q3 - q4, q1 - q2)
    n /= np.linalg.norm(n)
    return p, (n if n @ n0 > 0 else -n)


def probe_rear(p):
    return ray(p - depth * n0, n0)


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
            c, d = idx[(half, i + 1, j)], idx[(half, i + 1, j + 1)]
            tris += [(a, b, c), (b, d, c)]
V = []
for half, r, th in pts:
    a = vp['a0'] + (vp['L'] - vp['a0']) * r
    b = vp['b0'] + (vp['W'] - vp['b0']) * r
    s, x = a * np.cos(th), b * np.sin(th)
    h = 0.06 * vp['H'] + vp['H'] * np.exp(-((r - 0.25) / 0.30) ** 2)
    p, n = surf(x, s)
    V.append(p + h * n)
V = np.array(V)
Vs, ts, uv, src = split_islands(V, tris, pts, probe_rear)
OUT['FemVulvaLips'] = shape(Vs, ts, uv, weights_at(Vs, probe_rear))
# the floor: the slit-edge ring stepping down to just above the skin, closing on the slit line
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
    s = vp['a0'] * np.cos(th) * (1 - 0.15 * f)
    x = vp['b0'] * np.sin(th) * (1 - 0.95 * f)
    h0 = 0.06 * vp['H'] + vp['H'] * np.exp(-((0.0 - 0.25) / 0.30) ** 2)
    h = h0 * (1 - min(1.0, f / 0.4)) + 0.08 * min(1.0, f / 0.4)
    p, n = surf(x, s)
    FV.append(p + h * n)
    fuv.append([0.5 + 0.45 * np.sin(th) * (1 - f), LINING_V[0] + (LINING_V[1] - LINING_V[0]) * (0.5 + 0.5 * np.cos(th))])
FV = np.array(FV)
# orientation: faces must look out of the body
if (normals(FV, ftris) @ n0).mean() < 0:
    ftris = [(a, c, b) for a, b, c in ftris]
if (normals(Vs, ts) @ n0).mean() < 0:
    OUT['FemVulvaLips']['tris'] = [[a, c, b] for a, b, c in ts]
    OUT['FemVulvaLips']['normals'] = normals(Vs, [(a, c, b) for a, b, c in ts]).round(5).tolist()
OUT['FemVulvaInner'] = shape(FV, ftris, fuv, weights_at(FV, probe_rear),
                             mat=['Materials\\Anatomy\\Creatures\\CaninePenis.bgsm',
                                  'textures\\Anatomy\\Creatures\\CaninePenis_d.dds',
                                  'textures\\Anatomy\\Creatures\\CaninePenis_n.dds',
                                  'textures\\Anatomy\\Creatures\\CaninePenis_s.dds'])
print('vulva at', P0.round(2), 'normal', n0.round(2), 'lips', len(Vs), 'inner', len(FV))

# ---------------------------------------------------------------- teats on the belly
teats = params.get('teats', [])
if teats:
    TV, TT, inside_z = [], [], params.get('teat_inside_z')
    TIPV, TIPT, TIPUV = [], [], []
    for y, x, r, hh in teats:
        h0 = ray(np.array([x, y, inside_z]), np.array([0.0, 0.0, -1.0]))      # from inside the belly, down and out
        if h0 is None:
            raise SystemExit(f'no belly under teat ({x}, {y})')
        base = h0[0]
        q = [ray(np.array([x + ex, y + ey, inside_z]), np.array([0.0, 0.0, -1.0]))[0]
             for ex, ey in ((0.4, 0), (-0.4, 0), (0, 0.4), (0, -0.4))]
        nn = np.cross(q[0] - q[1], q[2] - q[3])
        nn /= np.linalg.norm(nn)
        nn = nn if nn[2] < 0 else -nn                       # outward = down
        u = np.cross(nn, [0.0, 1.0, 0.0])
        u /= np.linalg.norm(u)
        w = np.cross(nn, u)
        NS, NL, SPLIT = 12, 8, 3                                   # rings 0..SPLIT skin, SPLIT.. the flesh tip
        ring_pts = []
        for i in range(NL):
            t = i / (NL - 1)
            rad = r * (1.6 - 0.6 * t) * (1 - t ** 4) ** 0.5 if t < 1 else 0.0  # broad base, rounded tip
            hgt = -0.25 * r + (hh + 0.25 * r) * t                               # starts just under the skin
            ring_pts.append([base + nn * hgt + rad * (np.cos(2 * np.pi * j / NS) * u + np.sin(2 * np.pi * j / NS) * w)
                             for j in range(NS)])
        for lo, hi, dst_v, dst_t in ((0, SPLIT, TV, TT), (SPLIT, NL - 1, TIPV, TIPT)):
            start = len(dst_v)
            for i in range(lo, hi + 1):
                dst_v.extend(ring_pts[i])
                if dst_v is TIPV:
                    for j in range(NS):
                        TIPUV.append([j / NS, LINING_V[0] + (LINING_V[1] - LINING_V[0]) * (i - lo) / (hi - lo)])
            for i in range(hi - lo):
                for j in range(NS):
                    a, b = start + i * NS + j, start + i * NS + (j + 1) % NS
                    c, d = a + NS, b + NS
                    dst_t += [(a, c, b), (b, c, d)]
    TV = np.array(TV)

    def probe_belly(p):
        return ray(np.array([p[0], p[1], inside_z]), np.array([0.0, 0.0, -1.0]))
    if (normals(TV, TT)[:, 2]).mean() > 0:
        TT = [(a, c, b) for a, b, c in TT]
    Ts, tts, tuv, _ = split_islands(TV, TT, None, probe_belly)
    OUT['FemTeats'] = shape(Ts, tts, tuv, weights_at(Ts, probe_belly))
    TIPV = np.array(TIPV)
    if (normals(TIPV, TIPT)[:, 2]).mean() > 0:
        TIPT = [(a, c, b) for a, b, c in TIPT]
    OUT['FemTeatTips'] = shape(TIPV, TIPT, TIPUV, weights_at(TIPV, probe_belly),
                               mat=['Materials\\Anatomy\\Creatures\\CaninePenis.bgsm',
                                    'textures\\Anatomy\\Creatures\\CaninePenis_d.dds',
                                    'textures\\Anatomy\\Creatures\\CaninePenis_n.dds',
                                    'textures\\Anatomy\\Creatures\\CaninePenis_s.dds'])
    print('teats', len(teats), 'verts', len(Ts))
json.dump(OUT, open(out_json, 'w'))
