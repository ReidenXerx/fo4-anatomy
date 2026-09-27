"""The anal canal (A-50): a closed canal behind the anus, angled back toward the tailbone, away from the vagina.

The owner's photos (2026-09-28): with a penis in the vagina, the anus opened (her sphincter's answer, which he likes)
and through it the penis showed. Measured: the anus was a shallow cup (about 2 units) whose walls sat 1.7-2.3 units
from the vaginal path, and the penis collides as a tube of radius 2: there was no wall between the canals. (The
aim's paths, canal.py, deliberately follow the body's midline, and the anal one joined the vaginal one 3 units in.)

So the cup's floor is opened and a canal is stitched to it:
  - from the floor it bends about 45 degrees back, reaching y -3.1 by z -51.3 (3 units behind the vaginal path),
    then rises to about z -45.8; the buttock cleft's floor lies 5.5-6.7 units behind the vaginal path there, so the
    walls clear both the vaginal penis and the skin (measured, 2026-09-28);
  - the first ring IS the cup's opened floor (its vertices' positions, weights and slider data), so the canal opens
    with the anus; deeper rings hand over to Pelvis_Rear_skin;
  - its walls face inward and sample a mucosa patch (MUCOSA_UV, painted by mucosa.py into the genitals' own tile);
  - physics_design.ANUS_PATH, the engine's anal path, runs down its middle.
It is built relative to the floor it finds, so it also applies to a body BodySlide already built.
"""
import collections
import math
import struct

import nif

SHAPE = 'AnatomyGenitals'
ANUS_CENTRE, ANUS_AXIS = (0.0, -1.58, -54.07), (0.0, 0.45, 0.89)
# the centreline beyond the opening, as offsets from its centre (reference body: (0, -1.17, -53.54)); the targets
# (0, -2.7, -52.0), (0, -3.2, -51.0), (0, -3.4, -48.5), (0, -3.3, -45.8) and the cap's tip (0, -3.25, -45.0)
PATH_OFFSETS = ((0.0, -1.53, 1.54), (0.0, -2.03, 2.54), (0.0, -2.23, 5.04), (0.0, -2.13, 7.74), (0.0, -2.08, 8.54))
RADIUS = 1.0
FLOOR = 0.30          # the cup is opened from 30% of its depth: its floor sat 1.59 from the vaginal path
MUCOSA_UV = (0.3875, 0.7750, 0.4875, 0.8750)   # full-skin UV: inside the genitals' 1/4 tile, outside their island
PELVIS = 'Pelvis_Rear_skin'
LOOP_UVS = []


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _mul(a, k):
    return tuple(x * k for x in a)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    n = math.sqrt(_dot(a, a)) or 1.0
    return _mul(a, 1 / n)


def floor_loop(pos, tris):
    """(the cup-floor triangles to remove, the loop left around them as vertex indices in order)."""
    axis = _unit(ANUS_AXIS)
    cup = {i for i, p in enumerate(pos) if math.dist(p, ANUS_CENTRE) < 2.2}
    depth = {i: _dot(_sub(pos[i], ANUS_CENTRE), axis) for i in cup}
    top = max(depth.values())
    radial = {i: math.dist(pos[i], _add(ANUS_CENTRE, _mul(axis, depth[i]))) for i in cup}
    floor = {i for i in cup if depth[i] > FLOOR * top and radial[i] < 1.1}
    drop = [k for k, t in enumerate(tris) if all(v in floor for v in t)]
    if len(drop) < 4:
        raise ValueError(f'the cup has no floor to open ({len(drop)} triangles)')
    w = nif.weld(pos)
    dropset = set(drop)
    count_drop, count_kept = collections.Counter(), collections.Counter()
    rep = {}
    for k, (a, b, c) in enumerate(tris):
        counter = count_drop if k in dropset else count_kept
        for x, y in ((a, b), (b, c), (c, a)):
            counter[tuple(sorted((w[x], w[y])))] += 1
            rep.setdefault(w[x], x)
            rep.setdefault(w[y], y)
    rim = [e for e in count_drop if count_kept.get(e, 0) >= 1]
    adj = collections.defaultdict(list)
    for a, b in rim:
        adj[a].append(b)
        adj[b].append(a)
    if not adj or any(len(v) != 2 for v in adj.values()):
        raise ValueError(f'the opened floor is not one clean loop ({sorted(len(v) for v in adj.values())[-3:]})')
    start = next(iter(adj))
    loop, prev = [start], None
    while True:
        nxt = [v for v in adj[loop[-1]] if v != prev]
        prev = loop[-1]
        if nxt[0] == start:
            break
        loop.append(nxt[0])
        if len(loop) > len(adj):
            raise ValueError('the floor loop does not close')
    if len(loop) != len(adj) or len(loop) < 6:
        raise ValueError(f'the floor loop has {len(loop)} of {len(adj)} vertices')
    return drop, [rep[v] for v in loop]


def plan(nif_path):
    """Measure only: the floor to open and the canal's centreline, for a report before anything is written."""
    s = nif.Nif(nif_path).shape(SHAPE)
    pos, tris = s.positions(), s.triangles()
    drop, loop = floor_loop(pos, tris)
    centre = tuple(sum(pos[i][k] for i in loop) / len(loop) for k in range(3))
    return drop, loop, centre, [centre] + [_add(centre, o) for o in PATH_OFFSETS]


def build(nif_path, osd_path=None, osd_module=None, uv_map=None):
    """Open the cup's floor and stitch the canal onto it, in place; returns a report line. uv_map: for a body whose
    genitals already sample their tile (A-48), the full-skin UV -> tile UV mapping."""
    n = nif.Nif(nif_path)
    s = n.shape(SHAPE)
    pos, tris = s.positions(), s.triangles()
    bones, _ = n.skin(s)
    slot = {b: k for k, b in enumerate(bones)}
    if PELVIS not in slot:
        raise ValueError(f'the genitals\' skin has no {PELVIS}')
    drop, loop = floor_loop(pos, tris)
    centre = tuple(sum(pos[i][k] for i in loop) / len(loop) for k in range(3))
    path = [centre] + [_add(centre, o) for o in PATH_OFFSETS]
    samples = [(0, 0.0)] + [(seg, q) for seg in range(len(path) - 1) for q in (0.5, 1.0)]
    side = (1.0, 0.0, 0.0)
    up0 = _unit(_cross(_unit(_sub(path[1], path[0])), side))
    ang = [math.atan2(_dot(_sub(pos[i], centre), up0), _dot(_sub(pos[i], centre), side)) for i in loop]
    order = sorted(range(len(loop)), key=lambda j: ang[j])
    loop, ang = [loop[j] for j in order], [ang[j] for j in order]
    N = len(loop)
    r0 = sum(math.dist(pos[i], centre) for i in loop) / N
    weights0 = [dict((bones[sl], w) for sl, w in s.skin_weights(i)) for i in loop]
    global LOOP_UVS
    LOOP_UVS = [s.uv(i) for i in loop]                   # the rim's own texels: the mucosa's base tone
    u0, v0, u1, v1 = MUCOSA_UV

    new_pos, new_w, new_uv, rings = [], [], [], []
    for ring, (seg, q) in enumerate(samples[:-1]):          # the last sample is the cap's tip
        a, b = path[seg], path[seg + 1]
        c = _add(a, _mul(_sub(b, a), q)) if ring else centre
        up = _unit(_cross(_unit(_sub(b, a)), side))
        f = min(1.0, ring / 3)
        r = r0 + (RADIUS - r0) * max(0.0, min(1.0, (ring - 2) / 2))   # as narrow as the opening past the tight spot
        idx = []
        for j in range(N + 1):                              # N + 1: the texture's seam gets its own column
            jj = j % N
            p = pos[loop[jj]] if ring == 0 else \
                _add(c, _add(_mul(side, r * math.cos(ang[jj])), _mul(up, r * math.sin(ang[jj]))))
            w = {bn: (1 - f) * wt for bn, wt in weights0[jj].items()}
            w[PELVIS] = w.get(PELVIS, 0.0) + f
            idx.append(len(new_pos))
            new_pos.append(p)
            new_w.append(w)
            new_uv.append((u0 + (u1 - u0) * j / N, v0 + (v1 - v0) * ring / (len(samples) - 1)))

        rings.append(idx)
    tip_i = len(new_pos)
    new_pos.append(path[-1])
    new_w.append({PELVIS: 1.0})
    new_uv.append(((u0 + u1) / 2, v1))
    if uv_map is not None:
        new_uv = [uv_map(u, v) for u, v in new_uv]

    faces = []
    for ra, rb in zip(rings, rings[1:]):
        for j in range(N):
            faces += [(ra[j], rb[j], rb[j + 1]), (ra[j], rb[j + 1], ra[j + 1])]
    for j in range(N):
        faces.append((rings[-1][j], tip_i, rings[-1][j + 1]))
    # Seen from inside: which winding faces a viewer inside the cup, read off a kept cup triangle on the loop.
    loopset, dropset = set(loop), set(drop)
    ref = next(t for k, t in enumerate(tris) if k not in dropset and len(loopset & set(t)) >= 2)
    rn = _cross(_sub(pos[ref[1]], pos[ref[0]]), _sub(pos[ref[2]], pos[ref[0]]))
    rc = _mul(_add(_add(pos[ref[0]], pos[ref[1]]), pos[ref[2]]), 1 / 3)
    rh_inward = _dot(rn, _sub(_add(ANUS_CENTRE, _mul(_unit(ANUS_AXIS), 0.5)), rc)) > 0

    def oriented(tri):
        a, b, c = (new_pos[x] for x in tri)
        nrm = _cross(_sub(b, a), _sub(c, a))
        mid = _mul(_add(_add(a, b), c), 1 / 3)
        near = min(path, key=lambda p: math.dist(p, mid))
        return tri if (_dot(nrm, _sub(near, mid)) > 0) == rh_inward else (tri[0], tri[2], tri[1])
    faces = [oriented(t) for t in faces]

    vn = [(0.0, 0.0, 0.0)] * len(new_pos)                  # vertex normals pointing into the canal
    for a, b, c in faces:
        nrm = _cross(_sub(new_pos[b], new_pos[a]), _sub(new_pos[c], new_pos[a]))
        nrm = nrm if rh_inward else _mul(nrm, -1)
        for x in (a, b, c):
            vn[x] = _add(vn[x], nrm)
    vn = [_unit(v) for v in vn]

    def byte(x):
        return max(0, min(255, int(round((x + 1) * 127.5))))

    records = []
    template = bytes(s.record(loop[0]))
    for k, p in enumerate(new_pos):
        rec = bytearray(template)
        struct.pack_into('<3e', rec, 0, *p)
        struct.pack_into('<2e', rec, s.uv_at, *new_uv[k])
        rec[12:15] = bytes(byte(x) for x in vn[k])
        tng = _unit(_cross(side, vn[k])) if abs(_dot(side, vn[k])) < 0.99 else (0.0, 1.0, 0.0)
        rec[16:19] = bytes(byte(x) for x in tng)
        top4 = sorted(new_w[k].items(), key=lambda t: -t[1])[:4]
        total = sum(w for _, w in top4) or 1.0
        top4 = [(slot[b], w / total) for b, w in top4] + [(0, 0.0)] * (4 - len(top4))
        struct.pack_into('<4e', rec, s.skin_at, *(w for _, w in top4))
        struct.pack_into('<4B', rec, s.skin_at + 8, *(sl for sl, _ in top4))
        records.append(bytes(rec))

    base = s.count
    all_tris = [t for k, t in enumerate(tris) if k not in dropset] + [tuple(base + x for x in t) for t in faces]
    stride = s.stride
    vdata = bytes(n.b[s.data_at:s.data_at + s.count * stride]) + b''.join(records)
    tri_bytes = b''.join(struct.pack('<3H', *t) for t in all_tris)
    o, size = n.offsets[s.index]
    c = nif.Cursor(n.b, o)
    n._av(c)
    c.take('4f')
    c.take('i'), c.take('i'), c.take('i')
    c.take('Q')
    counts_at = c.o
    tail = bytes(n.b[s.data_at + s.count * stride + 6 * s.triangle_count:o + size])
    nverts = s.count + len(records)
    if nverts > 0xFFFF:
        raise ValueError('more than 65,535 vertices')
    blk = bytes(n.b[o:counts_at]) + struct.pack('<IHI', len(all_tris), nverts, len(vdata) + len(tri_bytes)) \
        + vdata + tri_bytes + tail
    out = n.with_edits(replace={s.index: blk})
    with open(nif_path, 'wb') as fh:                        # in place: a hardlinked copy stays one file
        fh.write(out)
    back = nif.Nif(nif_path).shape(SHAPE)
    if back.count != nverts or len(back.triangles()) != len(all_tris):
        raise ValueError('the rewritten shape does not read back')

    moved = 0
    if osd_path is not None and osd_module is not None:
        data = osd_module.read(osd_path)
        for key, diffs in data.items():
            if not key.startswith(SHAPE):
                continue
            d0 = [diffs.get(i, (0.0, 0.0, 0.0)) for i in loop]
            mean = tuple(sum(d[k] for d in d0) / N for k in range(3))
            for ring, idx in enumerate(rings):
                f = min(1.0, ring / 3)
                for j, vi in enumerate(idx):
                    d = _add(_mul(d0[j % N], 1 - f), _mul(mean, f))
                    if any(abs(x) > 1e-6 for x in d):
                        diffs[base + vi] = d
                        moved += 1
            if any(abs(x) > 1e-6 for x in mean):
                diffs[base + tip_i] = mean
        osd_module.write(osd_path, data)
    return (f'anal canal: the cup\'s floor opened ({len(drop)} triangles off, a loop of {N}), '
            f'{len(records)} vertices / {len(faces)} triangles added, {len(rings)} rings, '
            f'{math.dist(centre, path[-1]):.1f} deep; slider data on {moved} vertices (A-50)')


def paint_maps(tex_dir, tile, loop_in_tile=False):
    """Paint the mucosa (mucosa.py) into the genitals' three maps where MUCOSA_UV lands, its tone sampled from the texels
    the anus rim already shows (so the canal's entrance blends); tile = the atlas's (u0, v0, t), (0, 0, 1) for none."""
    import io
    from PIL import Image
    import mucosa
    u0t, v0t, t = tile

    def to_tile(u, v):
        return (u - u0t) / t, (v - v0t) / t
    a, b, c, d = MUCOSA_UV
    rect = to_tile(a, b) + to_tile(c, d)
    luv = LOOP_UVS if loop_in_tile else [to_tile(u, v) for u, v in LOOP_UVS]
    if not luv:
        raise ValueError('no canal was built in this run: nothing to paint')
    tones = []
    for name, kind in (('FemaleBody_d.dds', 'colour'), ('FemaleBody_n.dds', 'normal'), ('FemaleBody_s.dds', 'specular')):
        path = tex_dir / name
        data = path.read_bytes()
        img = Image.open(io.BytesIO(data)).convert('RGB')
        W, H = img.size
        px = [img.getpixel((min(W - 1, max(0, int(u * W))), min(H - 1, max(0, int(v * H))))) for u, v in luv]
        mean = tuple(int(sum(q[k] for q in px) / len(px)) for k in range(3))
        base = mean if kind == 'colour' else (mean[0], mean[1], 0) if kind == 'specular' else (0, 0, 0)
        out = mucosa.paint(data, rect, kind, base)
        if len(out) != len(data):
            raise ValueError(f'{name}: the painted map changed size')
        path.write_bytes(out)
        tones.append(f'{kind} {base}')
    return f'anal canal: mucosa painted at {tuple(round(x, 3) for x in rect)} of the maps ({"; ".join(tones)})'
