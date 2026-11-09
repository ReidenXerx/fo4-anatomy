"""Shapes of nif A vs nif B by name: vertex count, max position / UV difference, weight difference by bone name,
and whether the triangle + segment bytes are identical.  python -I shape_vs.py <a.nif> <b.nif>"""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
A, B = nif.Nif(sys.argv[1]), nif.Nif(sys.argv[2])
bs = {s.name: s for s in B.shapes()}
for s in A.shapes():
    t = bs.get(s.name)
    if t is None:
        print(f'{s.name}: only in A')
        continue
    if s.count != t.count:
        print(f'{s.name}: count {s.count} vs {t.count}')
        continue
    dp = np.abs(np.array(s.positions()) - np.array(t.positions())).max()
    du = np.abs(np.array([s.uv(i) for i in range(s.count)]) - np.array([t.uv(i) for i in range(t.count)])).max()
    sa, sb = A.skin(s)[0], B.skin(t)[0]
    dw = 0.0
    for i in range(s.count):
        a = {sa[k]: w for k, w in s.skin_weights(i) if w > 1e-4}
        b = {sb[k]: w for k, w in t.skin_weights(i) if w > 1e-4}
        dw = max(dw, max([abs(a.get(n, 0) - b.get(n, 0)) for n in set(a) | set(b)] or [0]))
    ta = bytes(A.b[s.data_at + s.count * s.stride:sum(A.offsets[s.index])])
    tb = bytes(B.b[t.data_at + t.count * t.stride:sum(B.offsets[t.index])])
    print(f'{s.name}: dpos {dp:.4f} duv {du:.4f} dweight {dw:.4f} tris+segs identical {ta == tb}')
for n in bs:
    if n not in {s.name for s in A.shapes()}:
        print(f'{n}: only in B')
