"""Feral body vs UAP's penis: shapes, bounds, centroid, genital bones, materials.  python -I feral_measure.py <nif>..."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

for p in sys.argv[1:]:
    m = nif.Nif(p)
    print(pathlib.Path(p).name, [s for s in m.strings if 'enis' in s or 'bgsm' in s.lower()][:8])
    for s in m.shapes():
        P = np.array(s.positions())
        o, _ = m.offsets[s.index]
        _, t, _, _ = m._av(nif.Cursor(m.b, o))
        bones, _ = m.skin(s)
        print(f'   {s.name} v{s.count} t{tuple(round(v, 2) for v in t)} min {P.min(0).round(2)} max {P.max(0).round(2)} '
              f'centroid {P.mean(0).round(2)} bones {[b for b in bones if b and any(k in b.lower() for k in ("enis", "pelvis", "alls", "genit"))]}')
