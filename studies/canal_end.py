"""How the vaginal canal ends today (the owner's 'deeper canal + soft end', 2026-10-07): the tube's depth range along
VAGINA_AXIS, its radius slice by slice, and whether the far end is closed (no boundary edges) or open. Also: how
far the engine's VAGINA_PATH runs past the tube's end, and which bones the deepest vertices are weighted to.

    python studies/canal_end.py [Anatomy.nif]      (default: the lab's built project)
"""
import collections
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import nif  # noqa: E402
import physics_design as pd  # noqa: E402
import vaginal_canal as vc  # noqa: E402

path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else r'D:\F4Output\AnatomyLab\BodySlide\ShapeData\Anatomy\Anatomy.nif')
n = nif.Nif(path)
s = n.shape(vc.SHAPE)
pos, tris = s.positions(), s.triangles()
try:
    tube, tube_t, ring = vc.find_tube(pos, tris)
except ValueError:
    # a built body: A-54 already split the entrance ring, so the tube is its own island. Flood it directly.
    d_all = [vc._dot(vc._sub(p, pd.VAGINA_CENTRE), pd.VAGINA_AXIS) for p in pos]
    adj = collections.defaultdict(set)
    for t in tris:
        for a in t:
            adj[a].update(t)
    seed = max((i for i in range(len(pos)) if pos[i][1] > -0.5), key=lambda i: d_all[i])
    seen, stack = {seed}, [seed]
    while stack:
        for q in adj[stack.pop()]:
            if q not in seen:
                seen.add(q)
                stack.append(q)
    tube = sorted(seen)
    tube_t = [k for k, t in enumerate(tris) if all(i in seen for i in t)]
    ring = []
depth = {i: vc._dot(vc._sub(pos[i], pd.VAGINA_CENTRE), pd.VAGINA_AXIS) for i in tube}
dmin, dmax = min(depth.values()), max(depth.values())
print(f'{path.name}: tube {len(tube)} vertices, {len(tube_t)} triangles, entrance ring {len(ring)}')
print(f'depth along VAGINA_AXIS: {dmin:.2f} .. {dmax:.2f}')

# boundary edges of the tube's triangles: the entrance ring, and an open far end if any
edges = collections.Counter()
for k in tube_t:
    t = tris[k]
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        edges[tuple(sorted((a, b)))] += 1
boundary = [e for e, c in edges.items() if c == 1]
bverts = {v for e in boundary for v in e}
far = [v for v in bverts if v not in ring]
print(f'boundary vertices {len(bverts)} ({len(far)} not on the entrance ring):',
      'the far end is OPEN' if far else 'the far end is CLOSED')

# radius by slice: distance from the slice's centroid
bins = collections.defaultdict(list)
for i in tube:
    bins[int((depth[i] - dmin) / max(1e-6, dmax - dmin) * 8)].append(i)
for b in sorted(bins):
    vs = bins[b]
    c = [sum(pos[i][k] for i in vs) / len(vs) for k in range(3)]
    r = sum(math.dist(pos[i], c) for i in vs) / len(vs)
    print(f'  slice {b}: {len(vs):3d} vertices, depth {min(depth[i] for i in vs):5.2f}..{max(depth[i] for i in vs):5.2f}, '
          f'mean radius {r:.2f}, centre {tuple(round(x, 2) for x in c)}')

# how far the engine's path goes past the tube
pdepth = [vc._dot(vc._sub(p, pd.VAGINA_CENTRE), pd.VAGINA_AXIS) for p in pd.VAGINA_PATH]
print('VAGINA_PATH depths:', [round(d, 2) for d in pdepth], '-> past the tube end by', round(max(pdepth) - dmax, 2))

# the deepest vertices' bones
deepest = sorted(tube, key=lambda i: -depth[i])[:12]
names, _ = n.skin(s)
for label, group in (('entrance', sorted(tube, key=lambda i: depth[i])[:20]), ('middle', [i for i in tube if 2.5 < depth[i] < 3.5]),
                     ('deepest', deepest)):
    w = collections.Counter()
    for i in group:
        for slot, wt in s.skin_weights(i):
            w[names[slot]] += wt / len(group)
    print(f'{label} vertices ({len(group)}) weighted to:', [(b, round(v, 2)) for b, v in w.most_common(5)])
