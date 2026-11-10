"""All ray hits (t, point, shape) from inside the rump backwards at the vulva height, per species.
    python -I fem_hits.py <name>..."""
import json
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
C = 'D:\\F4Output\\creatures\\'
SPECIES = {'fevhound': (C + 'canine\\vanilla\\fevhound.nif',), 'yaoguai': (C + 'yg\\vanilla\\yaoguai.nif',),
           'yaoguaishaggy': (C + 'yg\\vanilla\\yaoguaishaggy.nif',), 'molerat': (C + 'mr\\vanilla\\molerat.nif',),
           'viciousdog': (C + 'canine\\vanilla\\viciousdog.nif',)}


def hits(B, T, o, d):
    V0, V1, V2 = B[T[:, 0]], B[T[:, 1]], B[T[:, 2]]
    E1, E2 = V1 - V0, V2 - V0
    p = np.cross(d, E2)
    det = (E1 * p).sum(1)
    ok = np.abs(det) > 1e-9
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = o - V0
    u = (s * p).sum(1) * inv
    q = np.cross(s, E1)
    v = (q * d).sum(1) * inv
    t = (E2 * q).sum(1) * inv
    h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return sorted((round(float(t[k]), 2), round(float(np.sign(det[k])), 0)) for k in np.where(h)[0])


F = r'D:\F4Output\creatures\fem'
for n in sys.argv[1:]:
    P = json.load(open(f'{F}\\{n}.json'))['vulva']
    m = nif.Nif(str(SPECIES[n][0]))
    for s in m.shapes():
        B = np.array(s.positions())
        T = np.array(s.triangles())
        for dz in (-2, 0, 2):
            for x in (0, 1.0):
                o = np.array([x, P['inside_y'], P['z'] + dz])
                hh = hits(B, T, o, np.array([0, -1.0, 0]))
                if hh:
                    print(n, s.name, 'x', x, 'z', round(P['z'] + dz, 1), 'y hits', [(round(o[1] - t, 1), sg) for t, sg in hh])
