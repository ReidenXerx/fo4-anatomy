"""Where a deeper vaginal canal (tools/canal_depth.py) sits: its ring centres, its lowest y, and its nearest approach to
the anal canal (y < -0.5 part of the genitals) and to the body's outer skin (every other shape).

    python studies/canal_clearance.py <Anatomy.nif> [first new vertex]
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import nif  # noqa: E402
import physics_design as pd  # noqa: E402
import canal_depth as cd  # noqa: E402

n = nif.Nif(sys.argv[1])
s = n.shape(cd.SHAPE)
pos, tris = s.positions(), s.triangles()
tube = cd._tube(pos, tris)
first = int(sys.argv[2]) if len(sys.argv) > 2 else None
new = sorted(i for i in tube if first is not None and i >= first)
old = sorted(i for i in tube if first is None or i < first)
print(f'tube {len(tube)} vertices ({len(old)} old, {len(new)} new)')
print('path:', [tuple(round(x, 2) for x in p) for p in pd.VAGINA_PATH])
for label, vs in (('old', old), ('new', new)):
    if not vs:
        continue
    by = sorted(vs, key=lambda i: cd.depth_of(pos[i]))
    for k in range(0, len(by), max(1, len(by) // 8)):
        grp = by[k:k + max(1, len(by) // 8)]
        c = tuple(sum(pos[i][j] for i in grp) / len(grp) for j in range(3))
        print(f'  {label} depth {cd.depth_of(pos[grp[0]]):5.2f}: centre {tuple(round(x, 2) for x in c)}, '
              f'min y {min(pos[i][1] for i in grp):.2f}')
used = {i for t in tris for i in t}
anal = [i for i in used if i not in tube and pos[i][1] < -0.5]
canal = new or old
d = min((math.dist(pos[a], pos[b]), a, b) for a in canal for b in anal)
print(f'nearest the anal side: {d[0]:.2f} (canal {d[1]} at {tuple(round(x, 2) for x in pos[d[1]])}, '
      f'other {d[2]} at {tuple(round(x, 2) for x in pos[d[2]])}, depth {cd.depth_of(pos[d[1]]):.2f})')
for sh in n.shapes():
    if sh.name == cd.SHAPE:
        continue
    sp = sh.positions()
    d = min((math.dist(pos[a], q), a) for a in canal for q in sp)
    print(f'nearest {sh.name}: {d[0]:.2f} (canal vertex depth {cd.depth_of(pos[d[1]]):.2f})')
