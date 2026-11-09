"""UAP canine genitals per deployed mesh: rest + morphed bboxes of the penis and sheath (shape space), principal axis,
radius profile, and the body's surface near them.
    python -I canine_probe.py <rel nif under Data/meshes> [...]"""
import pathlib
import re
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes')
for rel in sys.argv[1:]:
    m = nif.Nif(D / rel)
    tri = {}
    t = re.findall(rb'BODYTRI.{0,8}?([ -~]{5,}\.tri)', m.b, re.S)
    if t:
        tri = {s: {n: (mu, d) for n, mu, d in ms} for s, ms in tri_sync.read(D / t[0].decode().replace('\\', '/'))}
    print('==', rel)
    for s in m.shapes():
        P = np.array(s.positions())
        if not re.search(r'penis|part|dick', s.name, re.I):
            print(f'   {s.name}: {s.count}v bbox {P.min(0).round(1)} {P.max(0).round(1)}')
            continue
        c = P.mean(0)
        u, sv, vt = np.linalg.svd(P - c, full_matrices=False)
        ax = vt[0]
        proj = (P - c) @ ax
        print(f'   {s.name}: {s.count}v centre {c.round(2)} axis {ax.round(2)} length {np.ptp(proj):.2f} '
              f'bbox {P.min(0).round(2)} {P.max(0).round(2)}')
        for k in range(5):
            sel = (proj >= np.quantile(proj, k / 5)) & (proj <= np.quantile(proj, (k + 1) / 5))
            q = P[sel]
            r = np.linalg.norm((q - c) - np.outer((q - c) @ ax, ax), axis=1)
            print(f'      slice {k}: mean radius {r.mean():.2f} max {r.max():.2f} centre {q.mean(0).round(2)}')
        for name, (mu, d) in tri.get(s.name, {}).items():
            Q = P.copy()
            for i, v in d.items():
                Q[i] += np.array(v, float) * mu
            print(f'      {name:14s}: bbox {Q.min(0).round(2)} {Q.max(0).round(2)} centre {Q.mean(0).round(2)}')
