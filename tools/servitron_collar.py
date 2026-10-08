"""A socket collar where Servitron's rubber breasts meet its torso (the owner, 2026-10-08: "work additionally in seams where
tits connected to torso ... it will be visible imagine if it would be real robot, but it should looks proper and not
ugly").

Each "Boobs" breast is an open shell whose rim floats 0.2-2.3 units (median 1.6) in front of the suit (pushed behind the
breasts by servitron_torso.py): seen from the side, a ragged dark edge. Here each rim loop (welded positions; the mesh is
split at seams) is extruded back into the suit as a collar of RINGS: it leaves the rim, swells into a raised bead, dips
into a groove and flares out onto the suit, ending a little inside it, so the breast reads as a module seated in a
socket. The collar has its own strip of the breast texture (servitron_rubber.py paints a gasket there: STRIPS, in texture
space the breasts never use), its own tangent frames along that strip, the rim's skin weights, and morphs that blend from
the breast's own at the rim to the suit's at the far end, so it holds for any body shape (Silhouette's templates).

    python tools/servitron_collar.py <in torso .nif> <out .nif> [--tri in.tri out.tri] [--osd in.osd out.osd]
"""
import argparse
import collections
import math
import pathlib
import shutil
import struct
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402

BREAST = 'Boobs'
SUITS = ('Torso2_GITS_Open', 'Torso3_GITS_Half_Open', 'Torso3_GITS_Half_Open_Metal', 'Overalls_Softbody_Open')
STRIPS = ((0.05, 0.95, 0.10, 0.13), (0.05, 0.95, 0.15, 0.18))   # per rim (left breast first): u0, u1, v0, v1
# the profile, s from the rim (0) to the suit (1): (s, outward swell)
# slim (the fourth render: a wide flare folded over the ragged rim and the two collars crossed in the cleavage): it
# runs back into the suit, swelling only a little for the bead and the flange
# The flat-colour render (the fifth look): the zigzag under the breasts is the suit's own torn opening edge, which runs
# right along the rim (3.6-9 out from the breast's middle, median 5.4 like the rim). So the collar's outer part is a
# FLANGE lying on the suit, reaching past that edge wherever it runs (FLANGE_MIN..FLANGE_MAX past the rim) and tucking
# under at its end; the bead and the groove stay by the rim. Per ring: (texture s, kind, back, out):
#   bead/groove: back = share of the way from the rim to the suit's surface, out = units out from the rim
#   flange: on the suit (LIFT in front of it), out = share of the way from FLANGE_IN to the flange's reach
#   tuck: the flange's end, a little further out and TUCK behind the suit
RINGS = ((0.00, 'rim', 0.0, 0.0), (0.12, 'bead', 0.15, 0.04), (0.28, 'bead', 0.32, 0.09), (0.42, 'bead', 0.50, 0.12),
         (0.55, 'groove', 0.80, 0.16), (0.66, 'flange', 1.0, 0.0), (0.85, 'flange', 1.0, 0.5), (1.00, 'flange', 1.0, 1.0),
         (1.12, 'tuck', 1.0, 1.0))
# the fillet (the collar since the seventh look): per ring (texture s, place): place < 1 is units out from the rim
# within the bead and groove (BEAD_END), 0..1 beyond it a share of the way to the column's reach, > 1 the tuck
FILLET = ((0.00, 0.00), (0.12, 0.06), (0.28, 0.16), (0.42, 0.27), (0.55, 0.40), (0.66, 0.50),
          (0.80, 1.35), (0.92, 1.70), (1.00, 2.00), (1.12, 2.10))
BEAD_END = 0.5                       # units: the bead and the groove; beyond, the ease to the suit
BEAD_H, GROOVE_D = 0.10, 0.04
PROFILE = tuple((r[0], 0.0) for r in FILLET)  # servitron_rubber paints the gasket by these s


def fillet_d(place, reach):
    """units out from the rim for a ring's place"""
    if place <= BEAD_END:
        return place
    t = (place - 1.0) if place <= 2.0 else 1.0       # 1.0 .. 2.0 -> 0 .. 1 of the ease
    t = max(0.0, t)
    d = BEAD_END + (reach - BEAD_END) * t
    return d + (0.2 if place > 2.0 else 0.0)


def fillet_y(d, reach, y_rim, y_far):
    """the fillet's depth d units out: a smoothstep from the rim to the suit's depth, with the bead and the groove"""
    t = min(1.0, max(0.0, d / max(reach, 1e-6)))
    y = y_rim + (y_far - y_rim) * (t * t * (3 - 2 * t))
    if 0.04 <= d <= 0.36:
        y += BEAD_H * math.sin(math.pi * (d - 0.04) / 0.32)
    elif 0.38 <= d <= 0.48:
        y -= GROOVE_D
    return y
FLANGE_IN, FLANGE_MIN, FLANGE_MAX, FLANGE_PAST = 0.30, 0.6, 2.5, 0.35
LIFT, TUCK = 0.04, 0.20
# the sixth look: a flange ON the suit followed its uneven surface and read as a frilly ruff. So the flange is a BACKING:
# BACKING behind the suit, seen only through the suit's torn gaps, as a dark gasket filling them instead of a void
BACKING = 0.15
MID_GAP = 0.35                      # no collar point closer than this to the midline (x = 0): the cleavage
# the mesh's rim is ragged (the first render: the collar rippled along it); past the first ring the collar follows the rim
# smoothed along the loop, so the socket's line runs clean
SMOOTH_PASSES, SMOOTH_HALF = 6, 3
INTO = 0.25                         # the collar's end, this far behind the suit's surface
CELL = 2.0


def b2f(x):
    return x / 127.5 - 1.0


def f2b(x):
    return max(0, min(255, int(round((x + 1) * 127.5))))


def unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else v


def rims(s):
    """[[split vertex, ...] in loop order] per open rim, left breast first"""
    pos, tris = s.positions(), s.triangles()
    key = {}
    wid = [key.setdefault(tuple(round(x, 3) for x in p), len(key)) for p in pos]
    rep = {}
    for i, w in enumerate(wid):
        rep.setdefault(w, i)
    e = collections.Counter()
    for t in tris:
        a, b, c = (wid[i] for i in t)
        for x, y in ((a, b), (b, c), (c, a)):
            if x != y:
                e[tuple(sorted((x, y)))] += 1
    nxt = collections.defaultdict(list)
    for (a, b), k in e.items():
        if k == 1:
            nxt[a].append(b)
            nxt[b].append(a)
    if any(len(v) != 2 for v in nxt.values()):
        raise ValueError(f'{s.name}: its open edge is not clean loops')
    seen, loops = set(), []
    for s0 in nxt:
        if s0 in seen:
            continue
        loop = [s0]
        seen.add(s0)
        while True:
            q = next((x for x in nxt[loop[-1]] if x not in seen), None)
            if q is None:
                break
            loop.append(q)
            seen.add(q)
        loops.append([rep[w] for w in loop])
    if len(loops) != 2:
        raise ValueError(f'{s.name}: {len(loops)} open rims, not two breasts')
    loops.sort(key=lambda L: sum(pos[i][0] for i in L))
    return loops


RELAX = (0.6, 0.45, 0.3, 0.15)      # per row in from the rim: how far a vertex eases toward its neighbours' mean
RELAX_ITER = 12


def straighten(s, pos, rim_targets):
    """the rim vertices (every split copy) onto their smoothed places, and the rows behind them eased (Laplacian, the
    rim held) so the old teeth leave no fold; returns (positions, indices moved)"""
    key = {}
    wid = [key.setdefault(tuple(round(x, 3) for x in p), len(key)) for p in pos]
    groups = collections.defaultdict(list)
    for i, w in enumerate(wid):
        groups[w].append(i)
    adj = collections.defaultdict(set)
    for t in s.triangles():
        a, b, c = (wid[i] for i in t)
        adj[a] |= {b, c}
        adj[b] |= {a, c}
        adj[c] |= {a, b}
    W = {w: pos[g[0]].copy() for w, g in groups.items()}
    depth = {}
    for i, p in rim_targets:
        W[wid[i]] = np.array(p, np.float64)
        depth[wid[i]] = 0
    frontier = list(depth)
    for d in range(1, len(RELAX) + 1):
        nxt = []
        for w in frontier:
            for q in adj[w]:
                if q not in depth:
                    depth[q] = d
                    nxt.append(q)
        frontier = nxt
    for _ in range(RELAX_ITER):
        W.update({w: W[w] + RELAX[d - 1] * (np.mean([W[q] for q in adj[w]], axis=0) - W[w])
                  for w, d in depth.items() if d})
    out = pos.copy()
    moved = [i for w in depth for i in groups[w]]
    for i in moved:
        out[i] = W[wid[i]]
    return out, moved


def suit_front(suit):
    """per (x, z) cell the suit's frontmost y, from its drawn triangles' vertices"""
    pos = suit.positions()
    cell = {}
    for t in suit.triangles():
        for i in t:
            k = (round(pos[i][0] * CELL), round(pos[i][2] * CELL))
            cell[k] = max(cell.get(k, -1e9), pos[i][1])
    return cell


def build(src, dst, tri=None, osd=None):
    shutil.copyfile(src, dst)
    n = nif.Nif(dst)
    shapes = {s.name: s for s in n.shapes()}
    if BREAST not in shapes:
        return f'{pathlib.Path(src).name}: no rubber breasts, left as it is'
    s = shapes[BREAST]
    suit = next(shapes[k] for k in SUITS if k in shapes)
    if s.full or s.uv_at != 8:
        raise ValueError(f'{s.name}: an unexpected vertex layout')
    pos = np.array(s.positions(), np.float64)
    front = suit_front(suit)
    spos = np.array(suit.positions(), np.float64)
    # the suit's open edge (its torn chest opening, and its other borders): welded edges one triangle uses
    skey = {}
    swid = [skey.setdefault(tuple(round(x, 3) for x in p), len(skey)) for p in spos]
    se = collections.Counter()
    for t in suit.triangles():
        a_, b_, c_ = (swid[i] for i in t)
        for x, y in ((a_, b_), (b_, c_), (c_, a_)):
            if x != y:
                se[tuple(sorted((x, y)))] += 1
    first = {}
    for i, w in enumerate(swid):
        first.setdefault(w, i)
    border = np.array([spos[first[w]] for w in {v for e_, k in se.items() if k == 1 for v in e_}])
    loops = rims(s)
    base = s.count
    new_recs, new_from, faces = [], [], []          # new_from: (rim vertex, s, suit vertex) per new vertex
    fillets = []                                     # per breast: (centre, smoothed rim, outward, reach, far depth)
    rim_targets = []                                 # (rim vertex, its place on the smoothed line)
    for li, loop in enumerate(loops):
        u0, u1, v0, v1 = STRIPS[li]
        P = pos[loop]
        c = P.mean(axis=0)
        N = len(loop)
        # the loop's direction: counter-clockwise seen from the front (+y) for a consistent winding below
        area = sum((P[j][0] - c[0]) * (P[(j + 1) % N][2] - c[2]) - (P[(j + 1) % N][0] - c[0]) * (P[j][2] - c[2])
                   for j in range(N))
        if area < 0:
            loop, P = loop[::-1], P[::-1]
        Ps = P.copy()
        for _ in range(SMOOTH_PASSES):
            Ps = np.mean([np.roll(Ps, sh, axis=0) for sh in range(-SMOOTH_HALF, SMOOTH_HALF + 1)], axis=0)
        # the breast's own edge moves onto the smoothed line too (the owner's photo, 10-08: the edge "like stairs" - the
        # mesh's teeth stood out over the collar's start), so the collar starts where the breast ends
        rim_targets += list(zip(loop, Ps))
        P = Ps
        arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1))])
        total = arc[-1]
        # the suit's torn edge around this breast, as (angle, distance out) in the front view
        bang = np.arctan2(border[:, 2] - c[2], border[:, 0] - c[0])
        brad = np.hypot(border[:, 0] - c[0], border[:, 2] - c[2])
        reach = []
        for jj in range(N):
            r_rim = float(np.hypot(Ps[jj][0] - c[0], Ps[jj][2] - c[2]))
            a = math.atan2(Ps[jj][2] - c[2], Ps[jj][0] - c[0])
            d = np.abs((bang - a + math.pi) % (2 * math.pi) - math.pi)
            sel = brad[(d < math.radians(12)) & (brad < r_rim + FLANGE_MAX + 0.5)]
            r = (float(sel.max()) - r_rim + FLANGE_PAST) if len(sel) else FLANGE_MIN
            reach.append(min(FLANGE_MAX, max(FLANGE_MIN, r)))
        reach = np.array(reach)
        for _ in range(SMOOTH_PASSES):                   # a smooth flange edge, not a copy of the tear
            reach = np.mean([np.roll(reach, sh) for sh in range(-SMOOTH_HALF, SMOOTH_HALF + 1)], axis=0)

        def suit_y(x, z, fallback):
            k0 = (round(x * CELL), round(z * CELL))
            for r in range(4):
                ys = [front[(k0[0] + i, k0[1] + j)] for i in range(-r, r + 1) for j in range(-r, r + 1)
                      if (k0[0] + i, k0[1] + j) in front]
                if ys:
                    return max(ys)
            return fallback
        # the seventh look: anything that follows the suit's surface inherits its noise. So the collar is a FILLET shaped
        # from the smoothed rim alone: from the rim it rolls into a bead, dips into a groove, then eases back (smoothstep)
        # to the suit's depth sampled once per column just past its reach (smoothed round the loop), and tucks under it.
        # The suit's torn flaps in front of the fillet are taken away below (cover), so it is the one surface there.
        outs = np.array([unit(np.array([Ps[jj][0] - c[0], 0.0, Ps[jj][2] - c[2]])) for jj in range(N)])
        yfar = np.array([suit_y(*(Ps[jj] + outs[jj] * (reach[jj] + 0.4))[[0, 2]], Ps[jj][1] - 1.5) for jj in range(N)])
        for _ in range(SMOOTH_PASSES):
            yfar = np.mean([np.roll(yfar, sh) for sh in range(-SMOOTH_HALF, SMOOTH_HALF + 1)], axis=0)
        yfar = np.minimum(yfar, Ps[:, 1] - 0.2)
        fillets.append((c, Ps, outs, reach, yfar))
        rings = []
        for k, (sv, frac) in enumerate(FILLET):
            idx = []
            blend = min(1.0, k / 2.0)                     # ring 0 on the rim itself, then onto the smoothed line
            for j in range(N + 1):                       # the strip's seam gets its own column
                jj = j % N
                p0 = P[jj] * (1 - blend) + Ps[jj] * blend
                d = fillet_d(frac, reach[jj])
                q = p0 + outs[jj] * d
                y = fillet_y(d, reach[jj], Ps[jj][1], yfar[jj])
                if frac > 1.0:
                    y -= TUCK
                p = np.array([q[0], y if k else p0[1], q[2]])
                if abs(p[0]) < MID_GAP and abs(p0[0]) >= MID_GAP * 0.5:
                    p[0] = MID_GAP if p0[0] > 0 else -MID_GAP
                near = int(np.argmin(np.linalg.norm(spos - p, axis=1)))
                idx.append(len(new_recs))
                rec = bytearray(s.record(loop[jj]))
                struct.pack_into('<3e', rec, 0, *p)
                struct.pack_into('<2e', rec, s.uv_at, u0 + (u1 - u0) * arc[j] / total,
                                 v0 + (v1 - v0) * k / (len(FILLET) - 1))
                new_recs.append(rec)
                new_from.append((loop[jj], min(1.0, d / max(reach[jj], 1e-6)), near))
            rings.append(idx)
        for ra, rb in zip(rings, rings[1:]):
            for j in range(N):
                faces.append((base + ra[j], base + rb[j], base + rb[j + 1]))
                faces.append((base + ra[j], base + rb[j + 1], base + ra[j + 1]))
    pos, moved = straighten(s, pos, rim_targets)
    allpos = np.vstack([pos, np.array([struct.unpack_from('<3e', bytes(r), 0) for r in new_recs], np.float64)])
    # winding: every collar face looks away from its breast's middle (outward and forward)
    centres = [pos[L].mean(axis=0) for L in loops]

    def oriented(t):
        a, b, c_ = (allpos[x] for x in t)
        nrm = np.cross(b - a, c_ - a)
        mid = (a + b + c_) / 3
        cen = min(centres, key=lambda q: np.linalg.norm(q - mid))
        away = unit(np.array([mid[0] - cen[0], 0.0, mid[2] - cen[2]])) + np.array([0.0, 0.6, 0.0])
        return t if np.dot(nrm, away) > 0 else (t[0], t[2], t[1])
    faces = [oriented(t) for t in faces]
    vn = np.zeros_like(allpos)
    for t in faces:
        a, b, c_ = (allpos[x] for x in t)
        f = np.cross(b - a, c_ - a)
        for x in t:
            vn[x] += f
    # tangent frames from the strip's uvs: the game's tangent is dp/dv, its bitangent N x tangent
    uvs = {base + k: struct.unpack_from('<2e', bytes(r), s.uv_at) for k, r in enumerate(new_recs)}
    acc = collections.defaultdict(lambda: np.zeros(3))
    for a_, b_, c_ in faces:
        e1, e2 = allpos[b_] - allpos[a_], allpos[c_] - allpos[a_]
        du1, dv1 = uvs[b_][0] - uvs[a_][0], uvs[b_][1] - uvs[a_][1]
        du2, dv2 = uvs[c_][0] - uvs[a_][0], uvs[c_][1] - uvs[a_][1]
        det = du1 * dv2 - du2 * dv1
        if abs(det) < 1e-14:
            continue
        pv = (e2 * du1 - e1 * du2) / det
        for x in (a_, b_, c_):
            acc[x] += pv
    for k, rec in enumerate(new_recs):
        g = base + k
        nrm = unit(vn[g])
        t = acc[g] - nrm * np.dot(acc[g], nrm)
        t = unit(t) if np.linalg.norm(t) > 1e-9 else unit(np.cross(nrm, [1.0, 0.0, 0.0]))
        bt = unit(np.cross(nrm, t))
        rec[12:15] = bytes(f2b(x) for x in nrm)
        rec[16:19] = bytes(f2b(x) for x in t)
        struct.pack_into('<e', rec, 6, float(bt[0]))
        rec[15], rec[19] = f2b(bt[1]), f2b(bt[2])
    tris = s.triangles() + faces
    old = bytearray(n.b[s.data_at:s.data_at + s.count * s.stride])
    for i in moved:
        struct.pack_into('<3e', old, i * s.stride, *pos[i])
    vdata = bytes(old) + b''.join(bytes(r) for r in new_recs)
    tri_bytes = b''.join(struct.pack('<3H', *t) for t in tris)
    o, size = n.offsets[s.index]
    cur = nif.Cursor(n.b, o)
    n._av(cur)
    cur.take('4f')
    cur.take('i'), cur.take('i'), cur.take('i')
    cur.take('Q')
    counts_at = cur.o
    tail = bytes(n.b[s.data_at + s.count * s.stride + 6 * s.triangle_count:o + size])
    nv = base + len(new_recs)
    if nv > 0xFFFF:
        raise ValueError('more than 65,535 vertices')
    blk = bytes(n.b[o:counts_at]) + struct.pack('<IHI', len(tris), nv, len(vdata) + len(tri_bytes)) + vdata + tri_bytes \
        + tail
    pathlib.Path(dst).write_bytes(n.with_edits(replace={s.index: blk}))
    back = nif.Nif(dst).shape(BREAST)
    if back.count != nv or len(back.triangles()) != len(tris):
        raise ValueError('the collared shape does not read back')
    covered = cover(dst, suit.name, fillets)
    report = (f'{pathlib.Path(src).name}: a collar of {len(PROFILE)} rings on each of 2 rims ({len(new_recs)} vertices, '
              f'{len(faces)} triangles); {covered} of the suit\'s triangles under it taken away')
    if tri:
        report += '; ' + morph_tri(tri, suit.name, base, new_from)
    if osd:
        report += '; ' + morph_osd(osd, suit.name, base, new_from)
    return report


def cover(path, suit_name, fillets):
    """the suit's triangles the fillet covers (inside its band and in front of it, or within COVER of it) taken away:
    its torn flaps by the rim; vertices stay (the .osd/.tri numbering)"""
    import servitron_torso as st
    n = nif.Nif(path)
    s = n.shape(suit_name)
    pos, tris = np.array(s.positions()), s.triangles()

    def covered(p):
        for c, Ps, outs, reach, yfar in fillets:
            a = math.atan2(p[2] - c[2], p[0] - c[0])
            ang = np.arctan2(Ps[:, 2] - c[2], Ps[:, 0] - c[0])
            j = int(np.argmin(np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi)))
            d = math.hypot(p[0] - c[0], p[2] - c[2]) - math.hypot(Ps[j][0] - c[0], Ps[j][2] - c[2])
            if -1.5 < d < reach[j] - 0.1 and p[1] > fillet_y(max(d, 0.0), reach[j], Ps[j][1], yfar[j]) - COVER:
                return True
        return False
    flags = [covered(p) for p in pos]
    keep = [t for t in tris if not all(flags[i] for i in t)]
    pathlib.Path(path).write_bytes(st.with_triangles(n, s, keep))
    return len(tris) - len(keep)


COVER = 0.08


def morph_tri(paths, suit_name, base, new_from):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import servitron_torso as st
    tri, trailing = st.read_tri(paths[0])
    by = {shape: dict(m) for shape, m in tri}
    suit = {nm.rstrip('\0'): d for nm, d in by.get(suit_name, {}).items()}
    out, count = [], 0
    for shape, morphs in tri:
        if shape != BREAST:
            out.append((shape, morphs))
            continue
        new = []
        for nm, d in morphs:
            sd = suit.get(nm.rstrip('\0'), {})
            d = dict(d)
            for k, (rim, sv, near) in enumerate(new_from):
                a, b = d.get(rim, (0.0, 0.0, 0.0)), sd.get(near, (0.0, 0.0, 0.0))
                v = tuple(a[i] * (1 - sv) + b[i] * sv for i in range(3))
                if any(abs(x) > 1e-6 for x in v):
                    d[base + k] = v
                    count += 1
            new.append((nm, d))
        out.append((shape, new))
    st.write_tri(paths[1], out, trailing)
    return f'.tri: {count} collar morph deltas'


def morph_osd(paths, suit_name, base, new_from):
    import osd as osd_mod
    data = osd_mod.read(paths[0])
    count = 0
    for key in [k for k in data if k.startswith(BREAST)]:
        slider = key[len(BREAST):]
        d, sd = data[key], data.get(suit_name + slider, {})
        for k, (rim, sv, near) in enumerate(new_from):
            a, b = d.get(rim, (0.0, 0.0, 0.0)), sd.get(near, (0.0, 0.0, 0.0))
            v = tuple(a[i] * (1 - sv) + b[i] * sv for i in range(3))
            if any(abs(x) > 1e-6 for x in v):
                d[base + k] = v
                count += 1
    osd_mod.write(paths[1], data)
    return f'.osd: {count} collar diffs'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--tri', nargs=2)
    ap.add_argument('--osd', nargs=2)
    a = ap.parse_args()
    print(build(a.src, a.dst, a.tri, a.osd))


if __name__ == '__main__':
    main()
