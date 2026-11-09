"""Our canine genitals (dogs, wolves, FEV hound; replace UAP's on the same paths + shape names + morph names).
Designed in numpy in root space (every shape transform here is identity):
  penis  : pointed glans (pars longa), a bulbus knot near the root that swells in Erection, a closed root;
           own material (CaninePenis), UV u = around, v = root -> tip. Also carries the pink LINING of the sheath
           opening (rides with the sheath).
  sheath : furred tube under the belly, closed at the back, an opening lip at the front; the body's own material
           and UVs (taken from the body in Blender), so each dog/wolf keeps its own fur.
Rest and morphs follow UAP's measured tubes: per state, the centre + mean radius of UAP's penis (sheath) in bins along
the rest axis; our rings ride those centrelines, our radius scaled by UAP's radius ratio (and the knot by its own
bump in Erection). Fit to a target body: the whole set moves by the belly height difference between UAP's reference
body and the target body (raycast up at x = 0 along the sheath).
    python -I canine_geom.py <ref nif> <ref penis> <ref sheath> <ref tri|-> <target nif> <out json> [nomorph]"""
import json
import math
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ref_nif, ref_pen, ref_sh, ref_tri, target, out = sys.argv[1:7]
NOMORPH = len(sys.argv) > 7 and sys.argv[7] == 'nomorph'
MORPHS = ['Erection', 'Erection Up', 'Erection Down', 'Penis Adjust']
SEG = 20
NB = 12
GEN = ('penis', 'sheath', 'part', 'dick')

m = nif.Nif(ref_nif)
Pp = np.array(m.shape(ref_pen).positions())
Ps = np.array(m.shape(ref_sh).positions())
tri = {}
if ref_tri != '-':
    tri = {s: {n: (mu, d) for n, mu, d in ms} for s, ms in tri_sync.read(ref_tri)}


def morphed(P, shape, name):
    Q = P.copy()
    if name and name in tri.get(shape, {}):
        mu, d = tri[shape][name]
        for i, v in d.items():
            Q[i] += np.array(v, float) * mu
    return Q


# rest axis of UAP's penis (root -> tip = towards the opening, +y here)
c0 = Pp.mean(0)
ax = np.linalg.svd(Pp - c0, full_matrices=False)[2][0]
front = Ps.mean(0) - c0
if ax @ np.array([0, 1.0, 0]) < 0:
    ax = -ax


class Tube:
    """Bins one UAP shape along the rest axis; per state: centre + mean radius per bin, as functions of t in [0,1]."""

    def __init__(self, P, shape):
        self.P, self.shape = P, shape
        proj = (P - c0) @ ax
        self.lo, self.hi = proj.min(), proj.max()
        t = (proj - self.lo) / (self.hi - self.lo)
        self.bins = np.minimum((t * NB).astype(int), NB - 1)
        self.tc = np.array([(b + 0.5) / NB for b in range(NB)])

    def state(self, name):
        Q = morphed(self.P, self.shape, name)
        C = np.array([Q[self.bins == b].mean(0) for b in range(NB)])
        R = []
        for b in range(NB):
            q = Q[self.bins == b] - C[b]
            k = min(b + 1, NB - 1)
            j = max(b - 1, 0)
            T = C[k] - C[j]
            T /= np.linalg.norm(T)
            R.append(np.linalg.norm(q - np.outer(q @ T, T), axis=1).mean())
        return C, np.array(R)


def frame_at(C, t, tc):
    """centre, T, X, N on the binned centreline at t (linear between bin centres, extrapolated at the ends)."""
    k = int(np.clip(np.searchsorted(tc, t) - 1, 0, len(tc) - 2))
    f = (t - tc[k]) / (tc[k + 1] - tc[k])
    c = C[k] * (1 - f) + C[k + 1] * f
    T = C[k + 1] - C[k]
    T /= np.linalg.norm(T)
    X = np.array([1.0, 0, 0])
    N = np.cross(T, X)
    N /= np.linalg.norm(N)
    X = np.cross(N, T)
    return c, T, X, N


pen, sht = Tube(Pp, ref_pen), Tube(Ps, ref_sh)
states = [''] + ([] if NOMORPH else [n for n in MORPHS if n in tri.get(ref_pen, {})])
PS = {n: pen.state(n) for n in states}
SS = {n: sht.state(n) for n in states}
Rr = PS[''][1]
R_mid = float(np.median(Rr[int(NB * 0.3):int(NB * 0.65)]))
Sr = SS[''][1]
print('penis rest radius by bin', Rr.round(2), 'R_mid', round(R_mid, 2))
print('sheath rest radius by bin', Sr.round(2))
if 'Erection' in PS:
    print('penis erect radius by bin', PS['Erection'][1].round(2))


def smooth(a):
    return np.convolve(np.pad(a, 1, mode='edge'), [0.25, 0.5, 0.25], mode='valid')


def interp(arr, t):
    return float(np.interp(t, pen.tc, arr))


# ---------------------------------------------------------------- design profiles
def pen_profile(t):
    """our rest radius at t (x R_mid): rounded closed root, a slight bulb, shaft, long pointed glans"""
    if t < 0.06:
        return 0.55 + 0.5 * t / 0.06
    if t < 0.40:
        return 1.05 + 0.10 * math.exp(-((t - 0.22) / 0.08) ** 2)
    if t < 0.58:
        return 1.05 - 0.10 * (t - 0.40) / 0.18
    e = min((t - 0.58) / 0.42, 1.0)                                     # pars longa glandis: long taper to a point
    return max(0.95 * (1 - e ** 1.6) ** 0.8, 0.07)


def knot(t):
    return math.exp(-((t - 0.22) / 0.075) ** 2)


verts, uvs, tris_p, mor = [], [], [], {n: [] for n in states[1:]}
TS = list(np.linspace(0.0, 1.0, 46))


def ring_rows(make, n_rows, closed_start=None, closed_end=None):
    """generic tube: make(row, theta) -> (rest position, {state: position}, uv); returns rows of vertex indices"""
    rows = []
    for r in range(n_rows):
        row = []
        for s in range(SEG + 1):
            th = 2 * math.pi * s / SEG + math.pi / 2
            p0, ps, uv = make(r, th, s / SEG)
            verts.append(p0)
            uvs.append(uv)
            for n in mor:
                mor[n].append(ps[n] - p0)
            row.append(len(verts) - 1)
        rows.append(row)
    return rows


def quads(rows, out_tris, flip=False):
    for r in range(len(rows) - 1):
        for s in range(SEG):
            a, b, c, d = rows[r][s], rows[r][s + 1], rows[r + 1][s + 1], rows[r + 1][s]
            out_tris += ([(a, c, b), (a, d, c)] if flip else [(a, b, c), (a, c, d)])


def pen_vertex(t, th, rho_rest, state):
    C, R = PS[state]
    c, T, X, N = frame_at(C, t, pen.tc)
    ratio = np.clip(interp(smooth(R), t) / max(interp(smooth(Rr), t), 1e-3), 0.7, 2.6)
    rho = rho_rest * ratio * (1 + (0.50 * knot(t) if state == 'Erection' else 0.0))
    return c + rho * (math.cos(th) * X + math.sin(th) * N)


def pen_make(r, th, u):
    t = TS[r]
    rho = pen_profile(t) * R_mid * 0.95
    return pen_vertex(t, th, rho, ''), {n: pen_vertex(t, th, rho, n) for n in mor}, (u, 0.04 + 0.92 * t)


rows = ring_rows(pen_make, len(TS))
quads(rows, tris_p)
# root cap + tip point (fans)
for row, t, flip in ((rows[0], 0.0, True), (rows[-1], 1.0, False)):
    c = pen_vertex(t, 0, 0, '')
    verts.append(c)
    uvs.append((0.5, 0.04 + 0.92 * t))
    for n in mor:
        mor[n].append(pen_vertex(t, 0, 0, n) - c)
    ci = len(verts) - 1
    for s in range(SEG):
        tris_p.append((row[s], ci, row[s + 1]) if flip else (row[s], row[s + 1], ci))
n_pen_core = len(verts)


# ---------------------------------------------------------------- sheath (fur) + its opening lining (penis material)
def sh_vertex(t, th, rho_rest, state, axial=0.0):
    C, R = SS[state]
    c, T, X, N = frame_at(C, t, sht.tc)
    ratio = np.clip(float(np.interp(t, sht.tc, smooth(R))) / max(float(np.interp(t, sht.tc, smooth(Sr))), 1e-3),
                    0.7, 1.6)
    return c + T * axial + rho_rest * ratio * (math.cos(th) * X + math.sin(th) * N)


# where the penis tip sits at rest, in the sheath's own t (the opening goes just beyond it)
proj_tip = ((pen_vertex(1.0, 0, 0, '') - c0) @ ax - sht.lo) / (sht.hi - sht.lo)
t_open = float(np.clip(max(proj_tip + 0.02, 0.85), 0.80, 0.97))
r_open = R_mid * 0.75
SH_T = [0.0, 0.04, 0.10] + list(np.linspace(0.16, t_open - 0.10, 10)) + [t_open - 0.05, t_open]


def sh_profile(t):
    base = float(np.interp(t, sht.tc, smooth(Sr)))
    if t < 0.10:                                                        # closed rear, inside the belly
        return base * (0.35 + 6.5 * t)
    if t > t_open - 0.12:                                               # front: taper to the opening lip
        f = (t - (t_open - 0.12)) / 0.12
        return base * (1 - f) + (r_open * 1.55) * f
    return base * 1.0


s_verts0 = len(verts)
sverts, suvs, stris, smor = [], [], [], {n: [] for n in mor}
sh_rows = []
for r, t in enumerate(SH_T):
    row = []
    for s in range(SEG + 1):
        th = 2 * math.pi * s / SEG + math.pi / 2
        p0 = sh_vertex(t, th, sh_profile(t), '')
        sverts.append(p0)
        suvs.append((s / SEG, t))
        for n in smor:
            smor[n].append(sh_vertex(t, th, sh_profile(t), n) - p0)
        row.append(len(sverts) - 1)
    sh_rows.append(row)
# lip: from the outer front ring, roll inward to the opening
for axial, rr in ((0.12, r_open * 1.30), (0.10, r_open * 1.02)):
    row = []
    for s in range(SEG + 1):
        th = 2 * math.pi * s / SEG + math.pi / 2
        p0 = sh_vertex(t_open, th, rr, '', axial)
        sverts.append(p0)
        suvs.append((s / SEG, t_open))
        for n in smor:
            smor[n].append(sh_vertex(t_open, th, rr, n, axial) - p0)
        row.append(len(sverts) - 1)
    sh_rows.append(row)
for r in range(len(sh_rows) - 1):
    for s in range(SEG):
        a, b, c, d = sh_rows[r][s], sh_rows[r][s + 1], sh_rows[r + 1][s + 1], sh_rows[r + 1][s]
        stris += [(a, b, c), (a, c, d)]
cpt = sh_vertex(0.0, 0, 0, '')                                          # rear cap
sverts.append(cpt)
suvs.append((0.5, 0.0))
for n in smor:
    smor[n].append(sh_vertex(0.0, 0, 0, n) - cpt)
for s in range(SEG):
    stris.append((sh_rows[0][s], len(sverts) - 1, sh_rows[0][s + 1]))

# lining (penis material, in the penis shape): from the lip's inner edge back inside the sheath
lin_rows = []
for k, (axial, rr) in enumerate(((0.10, r_open * 1.02), (-0.30, r_open * 0.98), (-1.6, r_open * 0.96))):
    row = []
    for s in range(SEG + 1):
        th = 2 * math.pi * s / SEG + math.pi / 2
        p0 = sh_vertex(t_open, th, rr, '', axial)
        verts.append(p0)
        uvs.append((s / SEG, 0.02 + 0.01 * k))
        for n in mor:
            mor[n].append(sh_vertex(t_open, th, rr, n, axial) - p0)
        row.append(len(verts) - 1)
    lin_rows.append(row)
quads(lin_rows, tris_p, flip=True)                                      # faces inward (seen through the opening)

# ---------------------------------------------------------------- fit to the target body (belly height)


def bodies(nifobj):
    out = []
    for s in nifobj.shapes():
        if any(k in s.name.lower() for k in GEN) or 'cap' in s.name.lower() or 'eye' in s.name.lower():
            continue
        P = np.array(s.positions())
        T = np.array(s.triangles()) if hasattr(s, 'triangles') else None
        out.append((P, T))
    return out


def belly_z(nifobj, ys):
    """lowest surface above z=0 hit by vertical rays at x=0 for each y (Moller-Trumbore, vectorised per shape)"""
    res = []
    shapes = bodies(nifobj)
    for y in ys:
        o = np.array([0.0, y, 0.0])
        d = np.array([0.0, 0.0, 1.0])
        best = np.inf
        for P, T in shapes:
            if T is None or not len(T):
                continue
            v0, v1, v2 = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
            e1, e2 = v1 - v0, v2 - v0
            h = np.cross(d, e2)
            a = (e1 * h).sum(1)
            ok = np.abs(a) > 1e-9
            f = np.where(ok, 1 / np.where(ok, a, 1), 0)
            s_ = o - v0
            u = f * (s_ * h).sum(1)
            q = np.cross(s_, e1)
            v = f * (q @ d)
            tt = f * (e2 * q).sum(1)
            hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (tt > 1)
            if hit.any():
                best = min(best, tt[hit].min())
        res.append(best)
    return np.array(res)


def pelvis(nifobj):
    """bind origin of the pelvis bone (Dogmeat_Pelvis / Pelvis) from any shape's skin"""
    for s in nifobj.shapes():
        names, xf = nifobj.skin(s)
        for want in ('Dogmeat_Pelvis', 'Pelvis'):
            if want in names:
                rot, tr, sc = xf[names.index(want)]
                return -np.array(rot).reshape(3, 3).T @ np.array(tr) / sc
    raise SystemExit('no pelvis bone')


# along the body: keep UAP's place RELATIVE TO THE PELVIS (vicious dogs carry theirs 13.6 further forward than Dogmeat,
# where UAP's copy left the penis hanging behind the hind legs); height: the target's belly
tgt = nif.Nif(target)
dy = float(pelvis(tgt)[1] - pelvis(m)[1])
ys = np.linspace(Ps[:, 1].min() + 1, Ps[:, 1].max() - 1, 7)
zr = belly_z(m, ys)
zt = belly_z(tgt, ys + dy)
ok = np.isfinite(zr) & np.isfinite(zt)
dz = float(np.median((zt - zr)[ok])) if ok.any() else 0.0
print('pelvis dy', round(dy, 2), 'belly z ref', zr.round(2), 'target', zt.round(2), '-> dz', round(dz, 2))
shift = np.array([0.0, dy, dz])
result = {
    'penis': dict(verts=(np.array(verts) + shift).tolist(), uv=uvs, tris=tris_p,
                  morphs={n: np.array(v).tolist() for n, v in mor.items()}),
    'sheath': dict(verts=(np.array(sverts) + shift).tolist(), uv=suvs, tris=stris,
                   morphs={n: np.array(v).tolist() for n, v in smor.items()}),
    'dz': dz, 'states': states,
}
json.dump(result, open(out, 'w'))
for k in ('penis', 'sheath'):
    V = np.array(result[k]['verts'])
    line = f'{k}: {len(V)} verts {len(result[k]["tris"])} tris rest bbox {V.min(0).round(2)} {V.max(0).round(2)}'
    if 'Erection' in result[k]['morphs']:
        E = V + np.array(result[k]['morphs']['Erection'])
        line += f' erect bbox {E.min(0).round(2)} {E.max(0).round(2)}'
    print(line)
print('uap penis rest bbox', Pp.min(0).round(2), Pp.max(0).round(2), 'sheath', Ps.min(0).round(2), Ps.max(0).round(2))
