"""Nick Valentine body meshes: per shape vertex/tri counts, bounds, bones, and the crotch region (verts near the
pelvis below the hips) so we know where a penis goes and what covers it.
    python -I nick_probe.py <nif> [...]"""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
for path in sys.argv[1:]:
    m = nif.Nif(path)
    print('==', path)
    for s in m.shapes():
        p = np.array(s.positions())
        bones, _ = m.skin(s)
        print(f'  {s.name}: {s.count}v {s.triangle_count}t  min {p.min(0).round(1)} max {p.max(0).round(1)}'
              f'  bones {len(bones)}')
        print('    ', [b for b in bones if b and any(k in b.lower() for k in ('pelvis', 'penis', 'thigh', 'spine', 'butt', 'genital', 'balls'))])
        # crotch: |x| < 4, z between 60 and 75, front half
        c = p[(np.abs(p[:, 0]) < 4) & (p[:, 2] > 55) & (p[:, 2] < 75)]
        if len(c):
            print(f'     crotch band verts {len(c)}  y range {c[:, 1].min():.1f}..{c[:, 1].max():.1f}'
                  f'  z range {c[:, 2].min():.1f}..{c[:, 2].max():.1f}')
