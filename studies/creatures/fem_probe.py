"""Rear profile + belly line of a creature body: rays from inside the body outward.
    python -I fem_probe.py <body nif> <inside_y> <z0> <z1> <inside_z> <y0> <y1> [x]"""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

p, iy, z0, z1, iz, y0, y1 = sys.argv[1], *map(float, sys.argv[2:8])
xo = float(sys.argv[8]) if len(sys.argv) > 8 else 3.0
m = nif.Nif(p)
b = max(m.shapes(), key=lambda s: s.count)
B = np.array(b.positions())
T = np.array(b.triangles())
V0, V1, V2 = B[T[:, 0]], B[T[:, 1]], B[T[:, 2]]
E1, E2 = V1 - V0, V2 - V0


def ray(o, d):
    pp = np.cross(d, E2)
    det = (E1 * pp).sum(1)
    ok = np.abs(det) > 1e-9
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = o - V0
    u = (s * pp).sum(1) * inv
    q = np.cross(s, E1)
    v = (q * d).sum(1) * inv
    t = (E2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return None if not hit.any() else o + t[hit].min() * d


print('rear profile (x=0): z -> rear surface y')
for z in np.linspace(z0, z1, 11):
    h = ray(np.array([0, iy, z]), np.array([0, -1.0, 0]))
    print(f'   z {z:6.1f}: y {h[1]:7.2f}' if h is not None else f'   z {z:6.1f}: none')
print(f'belly (x=+-{xo}): y -> underside z')
for y in np.linspace(y0, y1, 9):
    a = ray(np.array([xo, y, iz]), np.array([0, 0, -1.0]))
    c = ray(np.array([0, y, iz]), np.array([0, 0, -1.0]))
    print(f'   y {y:6.1f}: z(x={xo}) {a[2] if a is not None else float("nan"):7.2f}  z(x=0) '
          f'{c[2] if c is not None else float("nan"):7.2f}')
