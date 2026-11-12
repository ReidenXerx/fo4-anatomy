"""Measure ilhamitaa24's breasts in the GAME frame, for smf_geom's breast generator (P0['breast']).
Her points go into game skin space with the torso mapping smf_transfer uses (pelvis-anchored, her left=+x -> game -x,
her front=-y -> game +y, scale = torso segment ratio / size normalisation). Then, per (x, z) bin of the front half:
the front-most y. The chest wall under the breasts is the front surface interpolated across the breast zone from
its rim (sternum + sides + above + below), and protrusion = front - wall. Reported: apex (x, z, protrusion), the
footprint (where protrusion > 15 % of the apex) extents and centre, the lower fold z, and sag = footprint centre z -
apex z.   python -I smf_breast_measure.py <sample.npz> <norm> <torso scale> [out png]"""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

d = np.load(sys.argv[1])
NORM, S = float(sys.argv[2]), float(sys.argv[3])
HB = {str(n): p for n, p in zip(d['bone_names'], d['bone_pos'])}
n = nif.Nif(r'D:\F4Output\creatures\sm\vanilla\supermutantbody.nif')
b = n.shape('SupermutantBodyNew:0')
names, xf = n.skin(b)
BONE = {nm: -np.linalg.solve(np.array(r).reshape(3, 3), np.array(t)) / sc for nm, (r, t, sc) in zip(names, xf)}
k = S / NORM
G = (d['P'] - HB['Hips']) * np.array([-k, -k, k]) + BONE['Pelvis']
front = G[(G[:, 1] > 0) & (np.abs(G[:, 0]) < 30) & (G[:, 2] > -50) & (G[:, 2] < -5)]
xs = np.arange(-24, 24.01, 1.0)
zs = np.arange(-48, -6.01, 1.0)
Y = np.full((len(zs), len(xs)), np.nan)
xi = np.round(front[:, 0] - xs[0]).astype(int)
zi = np.round(front[:, 2] - zs[0]).astype(int)
for i, j, y in zip(zi, xi, front[:, 1]):
    if 0 <= i < len(zs) and 0 <= j < len(xs) and not y <= Y[i, j]:
        Y[i, j] = y if np.isnan(Y[i, j]) else max(Y[i, j], y)
# chest wall: per row, linear between the sternum (x=0) and the side (|x|=22) front depth; per column between the
# rows above (z=-12) and below (z=-42) - the lower of the two estimates (breasts only ever add)
wall = np.full_like(Y, np.nan)
for i in range(len(zs)):
    y0, ys_ = Y[i, len(xs) // 2], np.nanmean([Y[i, 2], Y[i, -3]])
    for j, x in enumerate(xs):
        a = min(abs(x) / 22.0, 1.0)
        wall[i, j] = (1 - a) * y0 + a * ys_
top, bot = np.argmin(np.abs(zs + 12)), np.argmin(np.abs(zs + 42))
for j in range(len(xs)):
    for i in range(len(zs)):
        a = (zs[i] - zs[bot]) / (zs[top] - zs[bot])
        w2 = (1 - a) * Y[bot, j] + a * Y[top, j]
        wall[i, j] = np.nanmin([wall[i, j], w2])
prot = np.clip(Y - wall, 0, None)
for side, sel in (('right (+x)', xs > 2), ('left (-x)', xs < -2)):
    P_ = np.where(sel[None, :], prot, 0)
    P_ = np.nan_to_num(P_)
    i, j = np.unravel_index(np.argmax(P_), P_.shape)
    apex = (xs[j], zs[i], P_[i, j])
    m = P_ > 0.15 * apex[2]
    zz, xx = np.where(m)
    print(f'{side}: apex x {apex[0]:.1f} z {apex[1]:.1f} protrusion {apex[2]:.1f} | footprint x '
          f'{xs[xx].min():.0f}..{xs[xx].max():.0f} z {zs[zz].min():.0f}..{zs[zz].max():.0f} centre '
          f'({xs[xx].mean():.1f}, {zs[zz].mean():.1f}) | Rx {(xs[xx].max() - xs[xx].min()) / 2:.1f} Rz '
          f'{(zs[zz].max() - zs[zz].min()) / 2:.1f} | sag (centre z - apex z) {zs[zz].mean() - apex[1]:.1f}')
if len(sys.argv) > 4:
    from PIL import Image
    img = (np.nan_to_num(prot) / max(1e-6, np.nanmax(prot)) * 255).astype(np.uint8)[::-1]
    Image.fromarray(img).resize((len(xs) * 10, len(zs) * 10), Image.NEAREST).save(sys.argv[4])
