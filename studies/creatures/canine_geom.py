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
FLAGS = set(sys.argv[7:])
NOMORPH = 'nomorph' in FLAGS
NOKNOT = 'noknot' in FLAGS          # bears: no bulbus glandis
SACK = 'sack' in FLAGS              # the 'sheath' reference shape is UAP's BALLS: also build our furred scrotum there
NOSHEATH = 'nosheath' in FLAGS      # no sheath shipped (radstag): skip the pink opening lining in the penis shape
SACK_UV = next((tuple(float(x) for x in f.split('=')[1].split(',')) for f in FLAGS if f.startswith('sackuv=')), None)
MORPHS = ['Erection', 'Erection Up', 'Erection Down', 'Penis Adjust']
SEG = 20
NB = 12
GEN = ('penis', 'sheath', 'part', 'dick', 'balls')     # UAP's balls are not body (the belly raycast hit them)

m = nif.Nif(ref_nif)
FULL_P = np.array(m.shape(ref_pen).positions())
FULL_S = np.array(m.shape(ref_sh).positions())
tri = {}
if ref_tri != '-':
    tri = {s: {n: (mu, d) for n, mu, d in ms} for s, ms in tri_sync.read(ref_tri)}
if ref_pen == ref_sh:
    # ONE UAP shape holds everything (radstag): the part Erection moves = the penis, the rest = sheath/scrotum
    mu_, d_ = tri[ref_pen]['Erection']
    dE = np.zeros(len(FULL_P))
    for i_, v_ in d_.items():
        dE[i_] = np.linalg.norm(np.array(v_, float) * mu_)
    PEN_IDX = np.where(dE >= 0.15 * dE.max())[0]
    SH_IDX = np.where(dE < 0.15 * dE.max())[0]
    print('one-shape split: penis', len(PEN_IDX), 'static', len(SH_IDX))
else:
    PEN_IDX, SH_IDX = np.arange(len(FULL_P)), np.arange(len(FULL_S))
Pp, Ps = FULL_P[PEN_IDX], FULL_S[SH_IDX]


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
if abs(ax[2]) > 0.7:                 # hangs (radstag): root = the UPPER end at the belly, so the axis points down
    if ax[2] > 0:
        ax = -ax
elif ax @ np.array([0, 1.0, 0]) < 0:  # lies along the belly (dogs): root -> tip points forward
    ax = -ax


class Tube:
    """Bins one UAP shape along the rest axis; per state: centre + mean radius per bin, as functions of t in [0,1]."""

    def __init__(self, P, shape, full, idx):
        self.P, self.shape, self.full, self.idx = P, shape, full, idx
        proj = (P - c0) @ ax
        self.lo, self.hi = proj.min(), proj.max()
        t = (proj - self.lo) / (self.hi - self.lo)
        self.bins = np.minimum((t * NB).astype(int), NB - 1)
        self.tc = np.array([(b + 0.5) / NB for b in range(NB)])

    def state(self, name):
        Q = morphed(self.full, self.shape, name)[self.idx]
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


pen, sht = Tube(Pp, ref_pen, FULL_P, PEN_IDX), Tube(Ps, ref_sh, FULL_S, SH_IDX)
states = [''] + ([] if NOMORPH else [n for n in MORPHS if n in tri.get(ref_pen, {})])
PS = {n: pen.state(n) for n in states}
SS = {n: sht.state(n) for n in states}
Rr = PS[''][1]
# smooth: UAP's bins zig-zag and its radius varies bump to bump; fit each state's centreline with a cubic in t and
# use ONE swell ratio per state (median over the shaft bins) so our surface stays clean (FEV came out faceted)
for n in list(PS):
    C, R = PS[n]
    tc = pen.tc
    Cs = np.stack([np.polyval(np.polyfit(tc, C[:, k], 3), tc) for k in range(3)], -1)
    ratio = float(np.median(R[2:10] / np.maximum(Rr[2:10], 1e-3)))
    PS[n] = (Cs, Rr * ratio)
if NOSHEATH:                         # no sheath to hide the root: every state keeps the REST root on the body
    C_rest = PS[''][0]
    for n in list(PS):
        if n:
            Cs, Rs = PS[n]
            Cs = Cs.copy()
            Cs[0] = C_rest[0]
            Cs[1] = 0.5 * (Cs[1] + C_rest[1])
            PS[n] = (Cs, Rs)
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
        return 1.05 + (0.0 if NOKNOT else 0.10) * math.exp(-((t - 0.22) / 0.08) ** 2)
    if t < 0.58:
        return 1.05 - 0.10 * (t - 0.40) / 0.18
    e = min((t - 0.58) / 0.42, 1.0)                                     # pars longa glandis: long taper to a point
    return max(0.95 * (1 - e ** 1.6) ** 0.8, 0.07)


def knot(t):
    return 0.0 if NOKNOT else math.exp(-((t - 0.22) / 0.075) ** 2)


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
# The sheath RIDES OUR PENIS: sheath param ts (0 rear cap .. 1 opening) maps to the penis' t; at rest it covers
# root..just past the tip, in Erection it pulls back behind the knot. Its radius = the penis' local radius in that
# state (an envelope over a short stretch) x 1.18 + a margin, so nothing pokes through in any state. Closed rear cap,
# a rolled lip snug on the penis at the opening, and a pink lining hugging the penis just inside it.
# UV: each sheath vertex carries a SAMPLE point on the belly: its own y, x = 0.4 + its arc distance from the
# underside line, so Blender projects belly fur unrolled around the tube (no stretched streaks).
TS0 = -0.12
T_OPEN = 1.02
T_OPEN_E = 0.10


def pen_radius(t, state):
    tt = min(max(t, 0.0), 1.0)
    _, R = PS[state]
    ratio = np.clip(interp(smooth(R), tt) / max(interp(smooth(Rr), tt), 1e-3), 0.7, 2.6)
    return pen_profile(tt) * R_mid * 0.95 * ratio * (1 + (0.50 * knot(tt) if state == 'Erection' else 0.0))


def sheath_t(ts, state):
    top = T_OPEN_E if state == 'Erection' else T_OPEN
    return TS0 + (top - TS0) * ts


def env(t, state, span=0.05):
    return max(pen_radius(t + d, state) for d in np.linspace(-span, span, 5))


def sh_radius(ts, state):
    r = env(sheath_t(ts, state), state) * 1.18 + 0.35 * R_mid
    if ts < 0.14:
        r *= 0.30 + 0.70 * (ts / 0.14) ** 0.5
    return r


def lip_radius(state):
    return env(sheath_t(1.0, state), state, 0.03) * 1.06 + 0.04


def on_pen(t, th, r, state, axial=0.0):
    C, _ = PS[state]
    c, T, X, N = frame_at(C, t, pen.tc)
    return c + T * axial + r * (math.cos(th) * X + math.sin(th) * N)


def angdist(th):
    return abs(((th - math.pi / 2 + math.pi) % (2 * math.pi)) - math.pi)


# rows: (ts, radius(state) fn, axial)
SH_ROWS = [(ts, (lambda st, ts=ts: sh_radius(ts, st)), 0.0) for ts in
           [0.0, 0.03, 0.07, 0.14] + list(np.linspace(0.2, 0.92, 10)) + [0.97, 1.0]]
SH_ROWS += [(1.0, (lambda st: 0.5 * (sh_radius(1.0, st) + lip_radius(st))), 0.07),
            (1.0, lip_radius, 0.03)]
sverts, suvs, stris, smor, ssample, sh_meta = [], [], [], {n: [] for n in mor}, [], []
sh_rows = []
for ts, rfn, axial in SH_ROWS:
    row = []
    for s in range(SEG + 1):
        th = 2 * math.pi * s / SEG + math.pi / 2
        p0 = on_pen(sheath_t(ts, ''), th, rfn(''), '', axial)
        sverts.append(p0)
        suvs.append((s / SEG, ts))
        ssample.append((0.4 + rfn('') * angdist(th), float(p0[1])))
        sh_meta.append((ts, math.sin(th), axial))
        wgt = min(max(ts / 0.85, 0.0), 1.0)
        wgt = wgt * wgt * (3 - 2 * wgt)                     # rear stays on the belly, the opening rides the penis
        for n in smor:
            smor[n].append((on_pen(sheath_t(ts, n), th, rfn(n), n, axial) - p0) * wgt)
        row.append(len(sverts) - 1)
    sh_rows.append(row)
for r in range(len(sh_rows) - 1):
    for s in range(SEG):
        a, b, c, d = sh_rows[r][s], sh_rows[r][s + 1], sh_rows[r + 1][s + 1], sh_rows[r + 1][s]
        stris += [(a, b, c), (a, c, d)]
cpt = on_pen(sheath_t(0.0, ''), 0, 0, '')                                 # rear cap point
sverts.append(cpt)
sh_meta.append((0.0, -1.0, 0.0))
suvs.append((0.5, 0.0))
ssample.append((0.4, float(cpt[1])))
for n in smor:
    smor[n].append(np.zeros(3))                              # the rear cap stays on the belly (weight 0)
for s in range(SEG):
    stris.append((sh_rows[0][s], len(sverts) - 1, sh_rows[0][s + 1]))

# lining (penis material, in the penis shape): from the lip's inner edge back inside, hugging the penis
lin_rows = []
for k, (ts, axial) in enumerate(() if NOSHEATH else ((1.0, 0.03), (0.96, 0.0), (0.88, 0.0))):
    row = []
    for s in range(SEG + 1):
        th = 2 * math.pi * s / SEG + math.pi / 2
        rf = (lambda st: lip_radius(st)) if k == 0 else (lambda st, ts=ts: env(sheath_t(ts, st), st, 0.03) * 1.06 + 0.04)
        p0 = on_pen(sheath_t(ts, ''), th, rf(''), '', axial)
        verts.append(p0)
        uvs.append((s / SEG, 0.02 + 0.01 * k))
        for n in mor:
            mor[n].append(on_pen(sheath_t(ts, n), th, rf(n), n, axial) - p0)
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
# join the sheath to THIS belly along its length: top-side vertices (sin < 0: N points down) of the rings short of
# the opening are raised into the belly (0.5 inside) where the belly is higher (vicious dogs' arched belly left a gap)
S_arr = np.array(sverts) + shift
ring_y = sorted({round(float(p[1]), 1) for p in S_arr})
bz = dict(zip(ring_y, belly_z(tgt, np.array(ring_y))))
raised = 0
for i, (ts, sn, axial) in enumerate(sh_meta):
    if ts > 0.85 or axial != 0.0 or sn > -0.15:
        continue
    zb = bz.get(round(float(S_arr[i][1]), 1), np.inf)
    if not np.isfinite(zb):
        continue
    w = min((-sn - 0.15) / 0.55, 1.0)
    w = w * w * (3 - 2 * w)
    need = zb + 0.5 - S_arr[i][2]
    if need > 0:
        S_arr[i][2] += w * need
        raised += 1
print('sheath vertices raised to the belly', raised)
sverts = list(S_arr - shift)
result = {
    'penis': dict(verts=(np.array(verts) + shift).tolist(), uv=uvs, tris=tris_p,
                  morphs={n: np.array(v).tolist() for n, v in mor.items()}),
    'sheath': dict(verts=(np.array(sverts) + shift).tolist(), uv=suvs, tris=stris,
                   sample=[(x, y + float(shift[1])) for x, y in ssample],
                   morphs={n: np.array(v).tolist() for n, v in smor.items()}),
    'dz': dz, 'states': states,
}
if SACK:
    # furred two-lobed scrotum at UAP's balls (the ref 'sheath' shape), fur UVs projected from the body above it
    lo, hi = np.percentile(Ps, 3, axis=0), np.percentile(Ps, 97, axis=0)
    axs = (hi - lo) / 2 * 1.08
    cb = (hi + lo) / 2
    cb[0] = 0.0
    LAT, LON = 16, 32
    kv, kuv, ksm, kgrid = [], [], [], []
    kmor = {n: [] for n in states[1:]}
    Dm = {n: morphed(FULL_S, ref_sh, n)[SH_IDX] - Ps for n in states[1:]}
    for i in range(LAT + 1):
        phi = math.pi * i / LAT
        row = []
        for j in range(LON + 1):
            lam = 2 * math.pi * j / LON
            d = np.array([math.sin(phi) * math.cos(lam), math.sin(phi) * math.sin(lam), math.cos(phi)])
            sag = 1.0 + 0.12 * max(0.0, -d[2])
            crease = 1.0 - 0.18 * math.exp(-(d[0] / 0.12) ** 2) * math.sin(phi) ** 2
            p = cb + d * axs * sag * crease
            kv.append(p + shift)
            if SACK_UV:                                    # planar side projection into a plain fur window
                a0, a1, b0, b1 = SACK_UV                   # wrap-around in the window (seam at the back)
                kuv.append((a0 + (a1 - a0) * j / LON, b0 + (b1 - b0) * i / LAT))
            else:
                kuv.append((j / LON, i / LAT))
            ksm.append((abs(float(p[0])) + 0.4, float(p[1] + shift[1])))
            near = np.argsort(np.linalg.norm(Ps - p, axis=1))[:4]
            for n in kmor:
                kmor[n].append(Dm[n][near].mean(0))
            row.append(len(kv) - 1)
        kgrid.append(row)
    ktris = []
    for i in range(LAT):
        for j in range(LON):
            a, b, c, d_ = kgrid[i][j], kgrid[i + 1][j], kgrid[i + 1][j + 1], kgrid[i][j + 1]
            ktris += [(a, b, c), (a, c, d_)]
    result['sack'] = dict(verts=np.array(kv).tolist(), uv=kuv, tris=ktris, sample=ksm, planar=bool(SACK_UV),
                          morphs={n: np.array(v).tolist() for n, v in kmor.items()})
    print('sack', len(kv), 'verts at', cb.round(1), 'half', axs.round(1))
json.dump(result, open(out, 'w'))
for k in ('penis', 'sheath'):
    V = np.array(result[k]['verts'])
    line = f'{k}: {len(V)} verts {len(result[k]["tris"])} tris rest bbox {V.min(0).round(2)} {V.max(0).round(2)}'
    if 'Erection' in result[k]['morphs']:
        E = V + np.array(result[k]['morphs']['Erection'])
        line += f' erect bbox {E.min(0).round(2)} {E.max(0).round(2)}'
    print(line)
print('uap penis rest bbox', Pp.min(0).round(2), Pp.max(0).round(2), 'sheath', Ps.min(0).round(2), Ps.max(0).round(2))
