"""Wolf inner-thigh cavity: vanilla vs UAP vs ours - shapes, body vertex differences, open holes of the body.
    python -I wolf_gap.py <vanilla nif> <uap nif> <our nif>"""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ms = {k: nif.Nif(p) for k, p in zip(('van', 'uap', 'ours'), sys.argv[1:4])}
for k, m in ms.items():
    print(k, [(s.name, s.count) for s in m.shapes()])
van = {s.name: s for s in ms['van'].shapes()}
for k in ('uap', 'ours'):
    for s in ms[k].shapes():
        if s.name in van and van[s.name].count == s.count:
            P, Q = np.array(van[s.name].positions()), np.array(s.positions())
            d = np.linalg.norm(P - Q, axis=1)
            moved = np.where(d > 0.05)[0]
            print(f'  {k} {s.name}: {len(moved)} vertices differ from vanilla (max {d.max():.2f})',
                  (Q[moved].min(0).round(1).tolist(), Q[moved].max(0).round(1).tolist()) if len(moved) else '')
        elif s.name in van:
            print(f'  {k} {s.name}: vertex count {s.count} vs vanilla {van[s.name].count}')
for k, m in ms.items():
    for s in m.shapes():
        if s.count > 2000:
            holes = nif.openings(s.positions(), s.triangles())
            print(k, s.name, 'holes (verts, centre, span):', [(h[0], np.round(h[1], 1).tolist(), np.round(h[2], 1).tolist())
                                                             for h in holes[:6]])
