"""The vaginal canal's lining (A-54): Nahka's canal walls become wet mucosa with transverse rugae, blended into the vulva.

Measured (2026-09-30, the Anatomy-dev body): the canal is a clean tube inside the genitals' shape, 198 vertices and 368
triangles deeper than 0.5 along physics_design.VAGINA_AXIS, opening onto the vulva through a ring of 26 vertices. Its
UVs are collapsed: every tube vertex samples the one texel (0.2383, 0.8320) of the genitals' tile, so its 16 square
units of wall show a single colour and repainting its "footprint" could never draw a fold (the design's texture-only
plan). So the canal gets its own UVs, as the anal canal did (A-50):
  - the entrance ring is split: the vulva keeps the ring's vertices, the canal gets copies (same position, normal,
    weights and slider data), so the new UVs never stretch a vulva triangle across the texture. No shape changes;
  - the canal is unwrapped into PATCH_UV (inside the genitals' 1/4 tile, clear of their island and of the anal canal's
    patch): v = the distance down the wall from the entrance, u = the angle around the canal's own centre, mirrored
    (0 the front wall, 1 the back wall, both sides alike), so the unwrap needs no seam;
  - tangents follow the new UVs (the game's 'tangent' field is dp/dv, its bitangent dp/du, measured on CBBE);
  - mucosa.paint(folds='across') paints the patch, toned from the texel the ring samples: its entrance row IS that
    texel's colour and specular, the rugae and the wetness fading in over the first 15%, so the entrance has no line.
Works on the BodySlide source or on a body BodySlide already built (the canal is found by its shape, not by index).
"""
import collections
import heapq
import math
import struct

import nif
from physics_design import VAGINA_CENTRE, VAGINA_AXIS

SHAPE = 'AnatomyGenitals'
FLOOR = 0.5           # depth along VAGINA_AXIS: at 0.25 the flood leaks onto the vulva (1535 vertices), at 0.5 it is the tube
PATCH_UV = (0.3875, 0.8875, 0.4375, 0.9875)    # full-skin UV: inside the genitals' 1/4 tile, below the anal patch
BINS = 10             # the canal's centreline, from this many slices down its wall
WET = (72, 140)       # the specular (strength, gloss) past the entrance; the introitus is about (51, 23)
RING_UVS = []         # the texels the entrance ring samples on the vulva side: the patch's tone
NEW_FROM = {}         # the last build's added vertices: {new index: the ring vertex it copies}


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    n = math.sqrt(_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-12 else (0.0, 0.0, 0.0)


def find_tube(pos, tris):
    """(tube vertices, tube triangle indices, entrance ring): the canal flooded from its deepest front vertex."""
    depth = [_dot(_sub(p, VAGINA_CENTRE), VAGINA_AXIS) for p in pos]
    adj = collections.defaultdict(set)
    for t in tris:
        for a in t:
            adj[a].update(t)
    seed = max((i for i in range(len(pos)) if pos[i][1] > -0.5), key=lambda i: depth[i])   # front of the anal canal
    seen, stack = {seed}, [seed]
    while stack:
        for q in adj[stack.pop()]:
            if q not in seen and depth[q] > FLOOR:
                seen.add(q)
                stack.append(q)
    tube_t = [k for k, t in enumerate(tris) if all(i in seen for i in t)]
    inside = {i for k in tube_t for i in tris[k]}
    outside = {i for k, t in enumerate(tris) if not all(i in seen for i in t) for i in t}
    ring = sorted(inside & outside)
    if not 100 <= len(inside) <= 600 or not 12 <= len(ring) <= 60:
        raise ValueError(f'vaginal canal: {len(inside)} vertices / a ring of {len(ring)}: not the canal this was built for')
    if any(pos[i][1] < -0.5 for i in inside):
        raise ValueError('vaginal canal: the flood reached the anal canal')
    return sorted(inside), tube_t, ring


def unwrap(pos, tris, tube, tube_t, ring):
    """{vertex: (s, t)}: t the distance down the wall from the ring (0..1), s the mirrored angle (0 front, 1 back)."""
    tube_set = set(tube)
    nbr = collections.defaultdict(set)
    for k in tube_t:
        for a in tris[k]:
            nbr[a].update(x for x in tris[k] if x != a)
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
    if set(dist) != tube_set:
        raise ValueError('vaginal canal: part of the tube is not reached from its entrance')
    deepest = max(dist.values())
    bins = [[] for _ in range(BINS)]
    for i in tube:
        bins[min(BINS - 1, int(dist[i] / deepest * BINS))].append(i)
    centres = [tuple(sum(pos[i][k] for i in b) / len(b) for k in range(3)) if b else None for b in bins]
    for k in range(BINS):                                   # an empty slice takes its neighbour's centre
        if centres[k] is None:
            centres[k] = next(c for c in centres[k::-1] + centres[k:] if c is not None)
    st = {}
    for k, b in enumerate(bins):
        axis = _unit(_sub(centres[min(BINS - 1, k + 1)], centres[max(0, k - 1)]))
        front = _unit(_sub((0.0, 1.0, 0.0), tuple(axis[j] * axis[1] for j in range(3))))  # +y (the belly) across the axis
        for i in b:
            d = _sub(pos[i], centres[k])
            d = _unit(_sub(d, tuple(axis[j] * _dot(d, axis) for j in range(3))))
            st[i] = (math.acos(max(-1.0, min(1.0, _dot(d, front)))) / math.pi, dist[i] / deepest)
    return st


def _tangents(pos, uvs, faces, normals):
    """{vertex: (tangent, bitangent)} in the game's convention: tangent = dp/dv, bitangent = N x tangent."""
    acc = collections.defaultdict(lambda: [0.0, 0.0, 0.0])
    for a, b, c in faces:
        e1, e2 = _sub(pos[b], pos[a]), _sub(pos[c], pos[a])
        du1, dv1 = uvs[b][0] - uvs[a][0], uvs[b][1] - uvs[a][1]
        du2, dv2 = uvs[c][0] - uvs[a][0], uvs[c][1] - uvs[a][1]
        det = du1 * dv2 - du2 * dv1
        if abs(det) < 1e-14:
            continue
        pv = tuple((e2[k] * du1 - e1[k] * du2) / det for k in range(3))
        for x in (a, b, c):
            for k in range(3):
                acc[x][k] += pv[k]
    nbr = collections.defaultdict(set)
    for f in faces:
        for x in f:
            nbr[x].update(f)
    todo = set(normals)
    while todo:                                             # a vertex on UV-flat triangles only (the ring's own)
        for x in [x for x in todo if x not in acc]:         # borrows its neighbours' dp/dv
            got = [acc[y] for y in nbr[x] if y in acc]
            if got:
                acc[x] = [sum(g[k] for g in got) for k in range(3)]
        done = {x for x in todo if x in acc}
        if not done:
            raise ValueError(f'vaginal canal: {len(todo)} vertices have no tangent from the new UVs')
        todo -= done
    out = {}
    for x in normals:
        tv, n = acc[x], normals[x]
        t = _unit(_sub(tuple(tv), tuple(n[k] * _dot(tv, n) for k in range(3))))
        out[x] = (t, _unit(_cross(n, t)))
    return out


def build(nif_path, osd_path=None, osd_module=None, uv_map=None):
    """Split the canal's entrance ring and give the canal its own UVs, in place; a report line. uv_map: for a body whose
    genitals already sample their tile (A-48), the full-skin UV -> tile UV mapping. Returns the new vertices'
    sources as {new index: old index} in NEW_FROM (for the slider data, the .tri)."""
    global RING_UVS, NEW_FROM
    n = nif.Nif(nif_path)
    s = n.shape(SHAPE)
    pos, tris = s.positions(), s.triangles()
    tube, tube_t, ring = find_tube(pos, tris)
    RING_UVS = [s.uv(i) for i in ring]
    pu0, pv0, pu1, pv1 = PATCH_UV if uv_map is None else uv_map(*PATCH_UV[:2]) + uv_map(*PATCH_UV[2:])
    tube_tset = set(tube_t)
    for k, t in enumerate(tris):                            # the patch must be texels nothing else samples
        if k in tube_tset:
            continue
        us, vs = [s.uv(i)[0] for i in t], [s.uv(i)[1] for i in t]
        if max(us) > pu0 and min(us) < pu1 and max(vs) > pv0 and min(vs) < pv1:
            raise ValueError(f'vaginal canal: triangle {k} already samples the patch {PATCH_UV}')
    st = unwrap(pos, tris, tube, tube_t, ring)

    base = s.count
    copy = {r: base + j for j, r in enumerate(ring)}         # the canal's side of the entrance
    NEW_FROM = {v: r for r, v in copy.items()}
    new_tris = [tuple(copy.get(i, i) for i in t) if k in tube_tset else t for k, t in enumerate(tris)]
    count = base + len(ring)
    src = list(range(base)) + ring
    all_pos = pos + [pos[r] for r in ring]
    uvs = [s.uv(i) for i in range(base)] + [None] * len(ring)
    canal = [i for i in tube if i not in copy] + [copy[r] for r in ring]
    for v in canal:
        a, b = st[src[v]]
        uvs[v] = (pu0 + (pu1 - pu0) * a, pv0 + (pv1 - pv0) * b)

    def f2b(x):
        return max(0, min(255, int(round((x + 1) * 127.5))))

    def b2f(x):
        return x / 127.5 - 1.0
    recs = [bytearray(s.record(src[v])) for v in range(count)]
    normals = {v: _unit(tuple(b2f(x) for x in recs[v][12:15])) for v in canal}
    frames = _tangents(all_pos, uvs, [new_tris[k] for k in tube_t], normals)
    for v in canal:
        rec = recs[v]
        struct.pack_into('<2e', rec, s.uv_at, *uvs[v])
        if v not in frames:
            raise ValueError(f'vaginal canal: vertex {v} has no tangent from its new UVs')
        t, b = frames[v]
        rec[16:19] = bytes(f2b(x) for x in t)
        struct.pack_into('<e', rec, 6, b[0])                 # bitangent x rides in the position's 4th half
        rec[15], rec[19] = f2b(b[1]), f2b(b[2])

    vdata = b''.join(bytes(r) for r in recs)
    tri_bytes = b''.join(struct.pack('<3H', *t) for t in new_tris)
    o, size = n.offsets[s.index]
    c = nif.Cursor(n.b, o)
    n._av(c)
    c.take('4f')
    c.take('i'), c.take('i'), c.take('i')
    c.take('Q')
    counts_at = c.o
    tail = bytes(n.b[s.data_at + s.count * s.stride + 6 * s.triangle_count:o + size])
    if count > 0xFFFF:
        raise ValueError('more than 65,535 vertices')
    blk = bytes(n.b[o:counts_at]) + struct.pack('<IHI', len(new_tris), count, len(vdata) + len(tri_bytes)) \
        + vdata + tri_bytes + tail
    out = n.with_edits(replace={s.index: blk})
    with open(nif_path, 'wb') as fh:                         # in place: a hardlinked copy stays one file
        fh.write(out)
    back = nif.Nif(nif_path).shape(SHAPE)
    if back.count != count or back.triangles() != new_tris or back.positions() != all_pos:
        raise ValueError('the rewritten shape does not read back')

    moved = 0
    if osd_path is not None and osd_module is not None:
        data = osd_module.read(osd_path)
        for key, diffs in data.items():
            if key.startswith(SHAPE):
                for v, r in NEW_FROM.items():
                    if r in diffs:
                        diffs[v] = diffs[r]
                        moved += 1
        osd_module.write(osd_path, data)
    return (f'vaginal canal: {len(tube)} vertices / {len(tube_t)} triangles unwrapped into the patch, the entrance ring '
            f'of {len(ring)} split ({len(ring)} vertices added), slider data on {moved} copies (A-54)')


def paint_maps(tex_dir, tile, ring_in_tile=False):
    """Paint the rugae mucosa (mucosa.py, folds='across') into the genitals' three maps where PATCH_UV lands, toned from
    the texels the entrance ring samples; tile = the atlas's (u0, v0, t), (0, 0, 1) for none."""
    import io
    from PIL import Image
    import mucosa
    u0t, v0t, t = tile

    def to_tile(u, v):
        return (u - u0t) / t, (v - v0t) / t
    a, b, c, d = PATCH_UV
    rect = to_tile(a, b) + to_tile(c, d)
    ruv = RING_UVS if ring_in_tile else [to_tile(u, v) for u, v in RING_UVS]
    if not ruv:
        raise ValueError('no vaginal canal was built in this run: nothing to paint')
    tones = []
    for name, kind in (('FemaleBody_d.dds', 'colour'), ('FemaleBody_n.dds', 'normal'), ('FemaleBody_s.dds', 'specular')):
        path = tex_dir / name
        data = path.read_bytes()
        img = Image.open(io.BytesIO(data)).convert('RGB')
        W, H = img.size
        px = [img.getpixel((min(W - 1, max(0, int(u * W))), min(H - 1, max(0, int(v * H))))) for u, v in ruv]
        mean = tuple(int(round(sum(q[k] for q in px) / len(px))) for k in range(3))
        base = mean if kind == 'colour' else (mean[0], mean[1], 0) if kind == 'specular' else (0, 0, 0)
        out = mucosa.paint(data, rect, kind, base, folds='across', wet=WET)
        if len(out) != len(data):
            raise ValueError(f'{name}: the painted map changed size')
        path.write_bytes(out)
        tones.append(f'{kind} {base}')
    return f'vaginal canal: rugae mucosa painted at {tuple(round(x, 3) for x in rect)} of the maps ({"; ".join(tones)})'
