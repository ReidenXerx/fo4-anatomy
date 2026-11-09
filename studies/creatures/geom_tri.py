"""Write a BodySlide .tri for our exported shapes from the geometry json's morphs (exported vertex order checked
against the json positions, half-float tolerance).  python -I geom_tri.py <geom.json> <export.nif> <out.tri>"""
import json
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

G = json.load(open(sys.argv[1]))
m = nif.Nif(sys.argv[2])
shapes = []
for name, g in G.items():
    if name.startswith('_') or not g.get('morphs'):
        continue
    s = m.shape(name)
    Pe, Pg = np.array(s.positions()), np.array(g['verts'])
    if len(Pe) != len(Pg) or np.abs(Pe - Pg).max() > 0.1:            # half floats: 0.0625 steps above 128
        raise SystemExit(f'{name}: exported vertices differ from the json (order/space)')
    morphs = []
    for mname, D in g['morphs'].items():
        D = np.array(D, float)
        mx = np.abs(D).max()
        if mx < 1e-5:
            continue
        mult = mx / 32767.0
        q = np.round(D / mult).astype(int)
        morphs.append((mname, mult, {int(i): tuple(int(x) for x in q[i]) for i in range(len(q))
                                     if np.abs(D[i]).max() > 1e-4}))
    shapes.append((name, morphs))
    print(name, [(n, len(d)) for n, _, d in morphs])
tri_sync.write(sys.argv[3], shapes)
print('tri', sys.argv[3])
