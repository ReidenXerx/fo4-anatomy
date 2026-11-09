"""Deathclaw: UAP's Base/Penis per morph (slices along y), body underside at the crotch, Base offset from the body.
    python -I dc_probe.py"""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

UAP = r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\Deathclaw\DeathclawPenis'
m = nif.Nif(UAP + '.nif')
tri = {s: {n: (mu, d) for n, mu, d in ms} for s, ms in tri_sync.read(UAP + '.tri')}
body = nif.Nif(r'D:\F4Output\creatures\dc\vanilla\deathclaw.nif')
B = np.array(body.shape('DeathclawFX:0').positions())
names, _ = body.skin(body.shape('DeathclawFX:0'))
print('body bones', names[:12])


def morphed(shape, P, name):
    Q = P.copy()
    if name:
        mu, d = tri[shape][name]
        for i, v in d.items():
            Q[i] += np.array(v, float) * mu
    return Q


for sn in ('Base', 'Penis'):
    s = m.shape(sn)
    P = np.array(s.positions())
    uv = np.array([s.uv(i) for i in range(s.count)])
    print(sn, 'uv range', uv.min(0).round(3), uv.max(0).round(3), 'tris', len(s.triangles()))
    for mn in [None] + list(tri[sn]):
        Q = morphed(sn, P, mn)
        moved = np.linalg.norm(Q - P, axis=1)
        print(f'  {mn or "rest"}: moved {int((moved > 0.05).sum())}/{len(P)} max {moved.max():.1f}')
        if mn in (None, 'Erection'):
            ys = np.linspace(Q[:, 1].min(), Q[:, 1].max(), 9)
            for a, b in zip(ys[:-1], ys[1:]):
                k = (Q[:, 1] >= a) & (Q[:, 1] <= b)
                if k.any():
                    c = Q[k].mean(0)
                    r = np.linalg.norm(Q[k][:, [0, 2]] - c[[0, 2]], axis=1).mean()
                    print(f'     y {a:6.1f}..{b:6.1f} n {k.sum():3d} centre x {c[0]:5.1f} z {c[2]:6.1f} r {r:4.1f}')
# body underside: lowest body z near x = 0 per y band (the belly / crotch line)
print('body underside (|x| < 2.5):')
for y in range(-40, 31, 5):
    k = (np.abs(B[:, 0]) < 2.5) & (np.abs(B[:, 1] - y) < 2.5) & (B[:, 2] > 80) & (B[:, 2] < 160)
    if k.any():
        print(f'   y {y:4d}: z min {B[k][:, 2].min():6.1f} (n {k.sum()})')
for x in (0, 4, 8, 12):
    k = (np.abs(B[:, 0] - x) < 2) & (np.abs(B[:, 1] + 5) < 4) & (B[:, 2] > 80) & (B[:, 2] < 160)
    if k.any():
        print(f'   x {x}: y~-5 z min {B[k][:, 2].min():6.1f}')
# UAP Base vs body: signed distance of Base verts to nearest body vertex
Pb = np.array(m.shape('Base').positions())
d = np.array([np.linalg.norm(B - p, axis=1).min() for p in Pb])
print('Base -> body nearest vertex: min %.2f mean %.2f max %.2f' % (d.min(), d.mean(), d.max()))
