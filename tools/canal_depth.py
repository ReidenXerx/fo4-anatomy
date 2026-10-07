"""The vaginal canal, deeper (the owner, 2026-10-07: "deeper canal + end").

Measured (studies/canal_end.py, the lab body): Nahka's tube runs 0.5 .. 5.6 units along VAGINA_AXIS and narrows to a
closed tip (mean radius ~0.5, a collapsed tube), while the engine's VAGINA_PATH, which the penis aim follows, runs to
14.3: a full stroke went ~8.6 units past the geometry, inside the body. Here the tube is continued along that path:
  - the tip's triangles (deeper than CUT) are dropped; its vertices stay, unused, so no index moves (slider data,
    the .tri and every later stage keep their numbering);
  - from the open loop left at CUT, rings follow VAGINA_PATH to END at the loop's own radius, the last CAP rings
    shrink to a rounded end, closed by a tip vertex;
  - weights blend from the loop's own (Pelvis_skin) to the old tip's (Spine1_skin / Pelvis_skin / Belly_skin), as
    the tube's deepest part was weighted;
  - each new vertex's slider data is its loop vertex's, fading to the loop's mean (as A-50's anal canal does);
  - UVs and tangents come later: vaginal_canal.py (stage 6c) unwraps the whole, longer tube.
Run before vaginal_canal.build, after the genitals have their own shape (stage 5) and the anal canal (6b).
"""
import collections
import math
import struct

import nif
import physics_design as pd

SHAPE = 'AnatomyGenitals'
CUT = 4.3            # depth along VAGINA_AXIS: the tube is kept to here (slice 5 of 8 on the lab body)
JOIN = 7.8           # depth along VAGINA_AXIS where the new part has joined VAGINA_PATH
END = 12.5           # the new end: this far along VAGINA_PATH from its entrance point (the path reaches 14.5)
STEP = 1.0           # ring spacing along the path
CAP = 3              # rings that shrink into the rounded end
CLEAR = 1.6          # the new part's least distance to any drawn skin (the shaft's radius 1.55, physics_design)
FLOOR = 0.5          # vaginal_canal.FLOOR: the tube starts this deep


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
    m = math.sqrt(_dot(a, a)) or 1.0
    return _mul(a, 1.0 / m)


def depth_of(p):
    return _dot(_sub(p, pd.VAGINA_CENTRE), pd.VAGINA_AXIS)


def _tube(pos, tris):
    """the canal's vertices: flooded from its deepest front vertex, as vaginal_canal.find_tube does"""
    adj = collections.defaultdict(set)
    for t in tris:
        for a in t:
            adj[a].update(t)
    used = {i for t in tris for i in t}
    seed = max((i for i in used if pos[i][1] > -0.5), key=lambda i: depth_of(pos[i]))
    seen, stack = {seed}, [seed]
    while stack:
        for q in adj[stack.pop()]:
            if q not in seen and depth_of(pos[q]) > FLOOR:
                seen.add(q)
                stack.append(q)
    return seen


def _centreline(p0, t0):
    """[(arc length, point, tangent)] every STEP from p0 (excluded) to the end: a curve leaving the tube's end along
    its own direction t0 and meeting VAGINA_PATH where the path is JOIN deep, then the path itself, to END along it.
    The tube sits ~2 units in front of the path (the body's midline, which curves back toward her middle), and runs
    toward her front: straight on, it would leave through the mons; jumping onto the path, it would kink."""
    path = list(pd.VAGINA_PATH)
    cum = [0.0]
    for a, b in zip(path, path[1:]):
        cum.append(cum[-1] + math.dist(a, b))

    def at(L):
        for k in range(len(path) - 1):
            if L <= cum[k + 1] or k == len(path) - 2:
                q = (L - cum[k]) / max(1e-9, cum[k + 1] - cum[k])
                return _add(path[k], _mul(_sub(path[k + 1], path[k]), q)), _unit(_sub(path[k + 1], path[k]))
    Lj = next(x * 0.05 for x in range(int(cum[-1] / 0.05) + 1) if depth_of(at(x * 0.05)[0]) >= JOIN)
    p1, t1 = at(Lj)
    k = math.dist(p0, p1)
    dense = []
    for i in range(201):                                   # cubic Hermite p0,t0 -> p1,t1
        u = i / 200
        h00, h10, h01, h11 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u, -2 * u**3 + 3 * u**2, u**3 - u**2
        dense.append(tuple(h00 * p0[j] + h10 * k * t0[j] + h01 * p1[j] + h11 * k * t1[j] for j in range(3)))
    L = Lj
    while L < END:
        L = min(END, L + 0.05)
        dense.append(at(L)[0])
    arc = [0.0]
    for a, b in zip(dense, dense[1:]):
        arc.append(arc[-1] + math.dist(a, b))
    out, want = [], STEP
    for i in range(1, len(dense)):
        if arc[i] >= want or i == len(dense) - 1:
            tng = _unit(_sub(dense[min(i + 1, len(dense) - 1)], dense[i - 1]))
            out.append((arc[i], dense[i], tng))
            want = arc[i] + STEP
    if arc[-1] - out[-2][0] < 0.5 * STEP:                 # no sliver ring just before the end
        del out[-2]
    return out


def build(nif_path, osd_path=None, osd_module=None):
    """Continue the canal along VAGINA_PATH to END, in place; a report line."""
    n = nif.Nif(nif_path)
    s = n.shape(SHAPE)
    pos, tris = s.positions(), s.triangles()
    bones, _ = n.skin(s)
    slot = {b: k for k, b in enumerate(bones)}
    tube = _tube(pos, tris)
    dmax = max(depth_of(pos[i]) for i in tube)
    if dmax > CUT + 4.0:
        return f'canal depth: already {dmax:.1f} deep, left as it is'
    tip = {i for i in tube if depth_of(pos[i]) > CUT}
    if not 10 <= len(tip) <= 120:
        raise ValueError(f'canal depth: {len(tip)} tip vertices past {CUT}: not the canal this was built for')
    drop = {k for k, t in enumerate(tris) if any(i in tip for i in t)}
    kept = [t for k, t in enumerate(tris) if k not in drop]
    # the open loop the cut leaves: tube edges used once by the kept triangles and away from the entrance
    edges = collections.Counter()
    for t in kept:
        if all(i in tube for i in t):
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                edges[tuple(sorted((a, b)))] += 1
    nxt = collections.defaultdict(list)
    for (a, b), c in edges.items():
        if c == 1 and depth_of(pos[a]) > CUT - 1.5 and depth_of(pos[b]) > CUT - 1.5:
            nxt[a].append(b)
            nxt[b].append(a)
    if not 6 <= len(nxt) <= 40 or any(len(v) != 2 for v in nxt.values()):
        raise ValueError(f"canal depth: the cut's edge is not one clean loop ({len(nxt)} vertices)")
    loop = [min(nxt)]                                     # walked along its own edges: the cut need not be star-shaped
    while len(loop) < len(nxt):
        loop.append(next(q for q in nxt[loop[-1]] if q not in loop[-2:]))
    if loop[0] not in nxt[loop[-1]]:
        raise ValueError("canal depth: the cut's edge is more than one loop")
    centre = tuple(sum(pos[i][k] for i in loop) / len(loop) for k in range(3))
    r0 = sum(math.dist(pos[i], centre) for i in loop) / len(loop)
    inner = [i for i in tube if CUT - 1.5 < depth_of(pos[i]) < CUT - 0.5 and i not in tip]
    c_in = tuple(sum(pos[i][k] for i in inner) / len(inner) for k in range(3))
    pts = _centreline(centre, _unit(_sub(centre, c_in)))
    side = (1.0, 0.0, 0.0)
    t0 = pts[0][2]
    up0 = _unit(_cross(t0, side))
    flat = [(_dot(_sub(pos[i], centre), side), _dot(_sub(pos[i], centre), up0)) for i in loop]
    if sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(flat, flat[1:] + flat[:1])) < 0:
        loop.reverse()                                     # counter-clockwise in (side, up), as the rings are laid
    N = len(loop)
    arc = [0.0]
    for a, b in zip(loop, loop[1:]):
        arc.append(arc[-1] + math.dist(pos[a], pos[b]))
    total = arc[-1] + math.dist(pos[loop[-1]], pos[loop[0]])
    a0 = math.atan2(_dot(_sub(pos[loop[0]], centre), up0), _dot(_sub(pos[loop[0]], centre), side))
    ang = {i: a0 + 2 * math.pi * arc[j] / total for j, i in enumerate(loop)}   # spaced as the cut's edge is
    w_loop = [dict((bones[sl], w) for sl, w in s.skin_weights(i)) for i in loop]
    deep = collections.Counter()
    for i in tip:
        for sl, w in s.skin_weights(i):
            deep[bones[sl]] += w / len(tip)

    new_pos, new_w, new_c, rings = [], [], [], [loop]
    nring = len(pts) - 1                                   # the last point is the tip
    for k, (L, c, tng) in enumerate(pts[:-1]):
        up = _unit(_cross(tng, side))
        f = (k + 1) / max(1, nring)                        # 0 at the loop -> 1 at the end
        shrink = 1.0 if k < nring - CAP else math.cos(0.5 * math.pi * (k - (nring - CAP) + 1) / (CAP + 1))
        r = r0 * shrink
        idx = []
        for j, i in enumerate(loop):
            a = ang[i]
            idx.append(len(new_pos))
            new_pos.append(_add(c, _add(_mul(side, r * math.cos(a)), _mul(up, r * math.sin(a)))))
            w = {b: (1 - f) * x for b, x in w_loop[j].items()}
            for b, x in deep.items():
                w[b] = w.get(b, 0.0) + f * x
            new_w.append(w)
            new_c.append(c)
        rings.append(idx)
    tip_i = len(new_pos)
    new_pos.append(pts[-1][1])
    new_w.append(dict(deep))
    new_c.append(pts[-2][1])

    base = s.count
    gid = lambda r, j: r[j] if r is loop else base + r[j]      # global index of ring r's j-th vertex
    faces = []
    for ra, rb in zip(rings, rings[1:]):
        for j in range(N):
            j2 = (j + 1) % N
            faces += [(gid(ra, j), gid(rb, j), gid(rb, j2)), (gid(ra, j), gid(rb, j2), gid(ra, j2))]
    for j in range(N):
        faces.append((gid(rings[-1], j), base + tip_i, gid(rings[-1], (j + 1) % N)))

    allpos = pos + new_pos
    # the winding of the kept tube: a kept triangle on the loop, its normal against the way into the canal
    loopset = set(loop)
    ref = next(t for t in kept if len(loopset & set(t)) >= 2 and all(i in tube for i in t))
    rn = _cross(_sub(pos[ref[1]], pos[ref[0]]), _sub(pos[ref[2]], pos[ref[0]]))
    rmid = _mul(_add(_add(pos[ref[0]], pos[ref[1]]), pos[ref[2]]), 1 / 3)
    toward_axis = _sub(centre, rmid)
    inward = _dot(rn, toward_axis) > 0                    # the kept tube's normals point INTO the canal?

    def oriented(t):
        a, b, c = (allpos[x] for x in t)
        nrm = _cross(_sub(b, a), _sub(c, a))
        mid = _mul(_add(_add(a, b), c), 1 / 3)
        near = min((p for _, p, _ in pts), key=lambda p: math.dist(p, mid))
        return t if (_dot(nrm, _sub(near, mid)) > 0) == inward else (t[0], t[2], t[1])
    faces = [oriented(t) for t in faces]

    vn = collections.defaultdict(lambda: (0.0, 0.0, 0.0))
    for a, b, c in faces:
        nrm = _cross(_sub(allpos[b], allpos[a]), _sub(allpos[c], allpos[a]))
        for x in (a, b, c):
            vn[x] = _add(vn[x], nrm)

    def byte(x):
        return max(0, min(255, int(round((x + 1) * 127.5))))

    # the stored normals' own facing (into the canal or out of it), read off the loop's records
    stored_in = sum(_dot(tuple(b / 127.5 - 1 for b in s.record(i)[12:15]), _sub(centre, pos[i])) for i in loop) > 0
    records = []
    for k, p in enumerate(new_pos):
        j = k % N if k < tip_i else 0
        rec = bytearray(s.record(loop[j]))                  # the loop vertex's record: its UV, colour, layout
        struct.pack_into('<3e', rec, 0, *p)
        nrm = _unit(vn[base + k])
        if (_dot(nrm, _sub(new_c[k], p)) > 0) != stored_in:
            nrm = _mul(nrm, -1)
        rec[12:15] = bytes(byte(x) for x in nrm)
        top4 = sorted(new_w[k].items(), key=lambda t: -t[1])[:4]
        total = sum(w for _, w in top4) or 1.0
        top4 = [(slot[b], w / total) for b, w in top4] + [(0, 0.0)] * (4 - len(top4))
        struct.pack_into('<4e', rec, s.skin_at, *(w for _, w in top4))
        struct.pack_into('<4B', rec, s.skin_at + 8, *(sl for sl, _ in top4))
        records.append(bytes(rec))

    all_tris = kept + faces
    # guards against faults met on the lab body (an angle-sorted loop left a hole; the CBBE shape's orphaned copy of
    # the tube read as skin 0.06 away): the seam is closed, and the new part keeps CLEAR of every DRAWN skin
    seam = collections.Counter()
    for t in all_tris:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            if a >= base or b >= base or (a in loopset and b in loopset):
                seam[tuple(sorted((a, b)))] += 1
    if any(c != 2 for c in seam.values()):
        raise ValueError(f'canal depth: {sum(c != 2 for c in seam.values())} open edges where the new part joins')
    lo = [min(p[k] for p in new_pos) - 2 * CLEAR for k in range(3)]   # wide enough to report the real gap
    hi = [max(p[k] for p in new_pos) + 2 * CLEAR for k in range(3)]
    skin = [pos[i] for t in kept if not all(i in tube for i in t) for i in t]
    for sh in n.shapes():
        if sh.name != SHAPE:
            sp = sh.positions()
            skin += [sp[i] for t in sh.triangles() for i in t]
    skin = [q for q in set(skin) if all(lo[k] <= q[k] <= hi[k] for k in range(3))]
    gap = min((math.dist(p, q) for p in new_pos for q in skin), default=math.inf)
    if gap < CLEAR:
        raise ValueError(f'canal depth: the new part comes {gap:.2f} from the skin (under {CLEAR})')
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
    with open(nif_path, 'wb') as fh:                       # in place: a hardlinked copy stays one file
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
            for k in range(len(new_pos)):
                f = min(1.0, (k // N + 1) / 3) if k < tip_i else 1.0
                d = _add(_mul(d0[k % N], 1 - f), _mul(mean, f)) if k < tip_i else mean
                if any(abs(x) > 1e-6 for x in d):
                    diffs[base + k] = d
                    moved += 1
        osd_module.write(osd_path, data)
    return (f'canal depth: the tip past {CUT} cut ({len(drop)} triangles, a loop of {N}, radius {r0:.2f}), '
            f'{len(records)} vertices / {len(faces)} triangles added along VAGINA_PATH, now {END:.1f} deep with a '
            f'rounded end, {gap:.1f} from the skin at its nearest; slider data on {moved} vertices')


WRAP_FROM, WRAP_FULL = 1.0, 2.0    # depth along VAGINA_AXIS: no wrap weight at the entrance (the lips' own), full past here


def wrap_weights(nif_path):
    """The canal's wall onto the wrap rings (physics_design.CANAL_BONES, the owner's 'walls wrap the penis'), in place:
    each canal vertex to the two rings around its place and the two spokes around its angle (bilinear, 4 weights),
    fading in from WRAP_FROM to WRAP_FULL deep so the entrance keeps the lips' weights; each ring bone's bounding
    sphere refitted to what it now carries. A report line."""
    n = nif.Nif(nif_path)
    s = n.shape(SHAPE)
    bones, xf = n.skin(s)
    slot = {b: k for k, b in enumerate(bones)}
    missing = [b for b in pd.CANAL_BONES if b not in slot]
    if missing:
        raise ValueError(f'canal wrap: {len(missing)} ring bones are not in the genitals\' skin (stage 3 adds them)')
    pos, tris = s.positions(), s.triangles()
    tube = _tube(pos, tris)
    rings = [pd.canal_frame(k) for k in range(len(pd.CANAL_RINGS))]
    K, S = len(rings), pd.CANAL_SPOKES

    def place(p):
        """(ring position as a float 0..K-1, spoke position as a float 0..S)"""
        best = None
        for k in range(K - 1):
            a, b = rings[k][0], rings[k + 1][0]
            ab = _sub(b, a)
            f = _dot(_sub(p, a), ab) / _dot(ab, ab)
            q = min(1.0, max(0.0, f))
            d = math.dist(p, _add(a, _mul(ab, q)))
            if best is None or d < best[0]:
                best = (d, k + (f if k == 0 or k == K - 2 else q))
        r = min(K - 1.0, max(0.0, best[1]))
        k0 = min(K - 2, int(r))
        f = r - k0
        c = _add(_mul(rings[k0][0], 1 - f), _mul(rings[k0 + 1][0], f))
        side = rings[k0][1]
        up = _unit(_add(_mul(rings[k0][2], 1 - f), _mul(rings[k0 + 1][2], f)))
        d = _sub(p, c)
        a = math.atan2(_dot(d, up), _dot(d, side)) % (2 * math.pi)
        return r, a / (2 * math.pi) * S

    carried = collections.defaultdict(list)
    count = 0
    for i in sorted(tube):
        depth = depth_of(pos[i])
        fade = min(1.0, max(0.0, (depth - WRAP_FROM) / (WRAP_FULL - WRAP_FROM)))
        if fade <= 0.0:
            continue
        r, sp = place(pos[i])
        k0 = min(K - 2, int(r))
        f = r - k0
        j0 = int(sp) % S
        g = sp - int(sp)
        wrap = {}
        for k, wk in ((k0, 1 - f), (k0 + 1, f)):
            for j, wj in ((j0, 1 - g), ((j0 + 1) % S, g)):
                if wk * wj > 0:
                    b = pd.canal_bone(k, j)
                    wrap[b] = wrap.get(b, 0.0) + fade * wk * wj
        own = [(bones[sl], w * (1 - fade)) for sl, w in s.skin_weights(i)]
        pairs = sorted(list(wrap.items()) + own, key=lambda t: -t[1])[:4]
        s.set_skin_weights(i, [(slot[b], w) for b, w in pairs])
        count += 1
        for sl, _ in s.skin_weights(i):
            if bones[sl] in pd.CANAL_BONES:
                carried[bones[sl]].append(i)
    # each ring bone's bounding sphere (bone space) around the vertices it carries; the skin data's per-bone record
    # is sphere 4f, rotation 9f, translation 3f, scale f after a count
    o, _ = n.offsets[s.skin]
    c = nif.Cursor(n.b, o)
    c.take('i')
    data = c.take('i')
    do, _ = n.offsets[data]
    for b, vs in carried.items():
        rot, t, sc = xf[slot[b]]
        bp = [tuple(sum(rot[3 * r + k] * pos[v][k] for k in range(3)) * sc + t[r] for r in range(3)) for v in vs]
        ctr = tuple(sum(p[k] for p in bp) / len(bp) for k in range(3))
        rad = max(math.dist(ctr, p) for p in bp)
        struct.pack_into('<4f', n.b, do + 4 + slot[b] * 68, *ctr, rad)
    n.save(nif_path)
    back = nif.Nif(nif_path).shape(SHAPE)
    if [back.skin_weights(i) for i in tube] != [s.skin_weights(i) for i in tube]:
        raise ValueError('canal wrap: the weights do not read back')
    used = sum(1 for b in pd.CANAL_BONES if carried.get(b))
    return (f'canal wrap: {count} canal vertices onto {used} of {len(pd.CANAL_BONES)} ring bones '
            f'({K} rings x {S} spokes), fading in from {WRAP_FROM} to {WRAP_FULL} deep')
