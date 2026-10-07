"""Where the canal's wrap rings go (the owner's 'walls wrap the penis', 2026-10-07): the built canal's centreline by
distance down its wall from the entrance (as vaginal_canal.unwrap measures it), and at each wanted distance the
centre, the axis and the mean radius. Prints physics_design.CANAL_RINGS.

    python studies/canal_rings.py <Anatomy.nif (after stage 6c)> [distances...]
"""
import collections
import heapq
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import nif  # noqa: E402
import canal_depth as cd  # noqa: E402

n = nif.Nif(sys.argv[1])
want = [float(x) for x in sys.argv[2:]] or [2.0, 4.5, 7.0, 9.5, 11.5]
s = n.shape(cd.SHAPE)
pos, tris = s.positions(), s.triangles()
tube = cd._tube(pos, tris)
tube_t = [t for t in tris if all(i in tube for i in t)]
edges = collections.Counter()
nbr = collections.defaultdict(set)
for t in tube_t:
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        edges[tuple(sorted((a, b)))] += 1
        nbr[a].add(b)
        nbr[b].add(a)
ring = {v for e, c in edges.items() if c == 1 for v in e}          # the split entrance: the tube's only open edge
dist = {i: 0.0 for i in ring}
heap = [(0.0, i) for i in ring]
while heap:
    d, a = heapq.heappop(heap)
    if d > dist[a]:
        continue
    for b in nbr[a]:
        nd = d + math.dist(pos[a], pos[b])
        if nd < dist.get(b, math.inf):
            dist[b] = nd
            heapq.heappush(heap, (nd, b))
print(f'tube {len(tube)} vertices, entrance {len(ring)}, deepest {max(dist.values()):.2f} down the wall')
out = []
for L in want:
    band = [i for i in tube if abs(dist[i] - L) < 0.6]
    c = tuple(sum(pos[i][k] for i in band) / len(band) for k in range(3))
    ahead = [i for i in tube if abs(dist[i] - (L + 1.0)) < 0.6]
    behind = [i for i in tube if abs(dist[i] - (L - 1.0)) < 0.6]
    ca = tuple(sum(pos[i][k] for i in ahead) / len(ahead) for k in range(3))
    cb = tuple(sum(pos[i][k] for i in behind) / len(behind) for k in range(3))
    ax = cd._unit(cd._sub(ca, cb))
    r = sum(math.dist(pos[i], c) for i in band) / len(band)
    print(f'  {L:5.1f}: {len(band):3d} vertices, centre {tuple(round(x, 3) for x in c)}, axis '
          f'{tuple(round(x, 3) for x in ax)}, radius {r:.2f}, depth along VAGINA_AXIS {cd.depth_of(c):.2f}')
    out.append((tuple(round(x, 3) for x in c), tuple(round(x, 3) for x in ax), round(r, 2)))
print('CANAL_RINGS = (' + ',\n               '.join(f'({c}, {a}, {r})' for c, a, r in out) + ')')
