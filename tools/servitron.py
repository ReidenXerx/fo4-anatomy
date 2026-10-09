"""Servitron's own genitals, made to work (Nexus 32801; the owner's poll 2026-10-08: "its own, made to work").

Its rubber abdomens (Abdomen GITS Rubber, Abdomen Wetsuit Rubber: the same rings and canals, measured identical) carry
a vaginal and an anal ring (..._VRing2, ..._ARing2), each with a canal (..._VInsides, ..._AInsides), all weighted to
Pelvis and the thighs: nothing opens, moves or holds a shaft. On a copy of each file (BodySlide's ShapeData .nif with
its .osd, or a game mesh):
  1. bones: the rings' stretch children (physics_design.SRV_STRETCH_BONES) and the vaginal canal's wrap rings
     (SRV_CANAL_BONES) join the skins, bound where the fork's [Bones] creates them (bone_table: Servitron's Pelvis_skin
     is bound exactly where CBBE's is, proven on each file below);
  2. deeper canals: each canal is cut CUT deep (a clean loop of its own edges, walked on welded positions: the mesh is
     split at its seams); its sculpted end moves, unchanged, to the end of its path (SRV_VAGINA_PATH / SRV_ANUS_PATH),
     and rings of the canal's own cross-section, turned along the path, bridge the gap;
  3. weights: each ring onto its four ring bones by angle; the shell round each hole and each canal's first units
     follow them, fading; the vaginal canal onto its wrap rings from WRAP_FROM to WRAP_FULL along it;
  4. each new bone's bounding sphere; the .osd gives every new vertex its source vertex's slider data.

    python tools/servitron.py <in.nif> <out.nif> [--osd in.osd out.osd] [--measure]
"""
import argparse
import collections
import math
import pathlib
import shutil
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402
import physics_design as pd  # noqa: E402
import zex_bones as zb  # noqa: E402

SKELETON = pathlib.Path(r'D:\F4Output\servitron\x\fix\meshes\Servitron\skeleton.nif')   # Servitron Physics Fix's
SHELLS = ('Abdomen_GITS_Rubber', 'Abdomen_Wetsuit_Rubber')
def _zero(p, shift):
    """a built-body point (physics_design.SRV_*) where it lies in the zero-slider BodySlide files"""
    return tuple(round(a - b, 4) for a, b in zip(p, shift))


# in the zero-slider files' space: the built positions less what Servitron's preset does to each opening
OPENINGS = {
    'vagina': dict(ring='_VRing2', canal='_VInsides', centre=_zero(pd.SRV_VAGINA_CENTRE, pd.SRV_VAGINA_SHIFT),
                   axis=pd.SRV_VAGINA_AXIS, path=[_zero(p, pd.SRV_VAGINA_SHIFT) for p in pd.SRV_VAGINA_PATH],
                   bones='AnatSrvVag', cut=3.0, end=12.5, wrap=True, shift=pd.SRV_VAGINA_SHIFT),
    'anus': dict(ring='_ARing2', canal='_AInsides', centre=_zero(pd.SRV_ANUS_CENTRE, pd.SRV_ANUS_SHIFT),
                 axis=pd.SRV_ANUS_AXIS, path=[_zero(p, pd.SRV_ANUS_SHIFT) for p in pd.SRV_ANUS_PATH],
                 bones='AnatSrvAnus', cut=2.3, end=9.0, wrap=False, shift=pd.SRV_ANUS_SHIFT),
}
STEP = 1.0                 # bridge ring spacing along the path
JOIN = 2.5                 # the bridge leaves the cut along the canal's own direction and meets the path this much deeper
RING_FADE = 1.5            # a canal's first units (and the shell within this of its ring) follow the ring bones, fading
# The suit round each ring: fully on the ring bones out to SHELL_FULL (past the ring's outer edge, 1.85 / 1.70), then
# fading to its own weights over SHELL_REACH more. The ring itself moves whole (RING_EDGE_SHARE 1), so the SUIT takes the
# stretch, not the ring (the owner, 2026-10-09: opened, the rings "look ugly like stretched texture" - with the edge at
# 25% the lip passed it at full open and 185 of the vaginal ring's 576 triangles folded over; studies/servitron_ring_open.py).
# The 10-08 tear (a whole ring on our bones, the suit beside it back on the thighs within 1 unit) cannot come back: the
# suit under and beside the ring is on the same bones as the ring
SHELL_FULL, SHELL_REACH = 2.0, 2.5
PERINEUM_BLEND = 0.4       # between the two rings: the suit hands over from one ring's bones to the other's over this
WRAP_FROM, WRAP_FULL = 1.0, 2.0
RING_ANGLES = {'R': 0.0, 'F': 90.0, 'L': 180.0, 'B': 270.0}    # around each opening: +x, belly, -x, back


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    m = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1.0 / m)


def rotation(a, b):
    """3x3 rows turning unit a onto unit b the shortest way (Rodrigues)"""
    v, c = cross(a, b), dot(a, b)
    if c < -0.9999:
        raise ValueError('a half turn: no unique rotation')
    k = 1.0 / (1.0 + c)
    vx = ((0.0, -v[2], v[1]), (v[2], 0.0, -v[0]), (-v[1], v[0], 0.0))
    vx2 = [[sum(vx[i][m] * vx[m][j] for m in range(3)) for j in range(3)] for i in range(3)]
    return [[(1.0 if i == j else 0.0) + vx[i][j] + k * vx2[i][j] for j in range(3)] for i in range(3)]


def apply(r, v):
    return tuple(sum(r[i][j] * v[j] for j in range(3)) for i in range(3))


def frame(axis):
    """(side, up) across an axis: side the body's x, up toward the belly"""
    side = (1.0, 0.0, 0.0)
    return side, unit(cross(axis, side))


# ---- 1. bones -------------------------------------------------------------------------------------------------------

def bone_defs(names):
    """with_bones' dicts for our nodes, bound where the fork's [Bones] puts them under Servitron's Pelvis_skin"""
    import physics_config
    world = zb.skeleton_world(SKELETON)
    identity = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    ours = {pd.PARENT: world[pd.PARENT]}
    for name, parent, local in physics_config.bone_table(world[pd.PARENT]):
        ours[name] = zb.compose(ours[parent], (identity, list(local), 1.0))
    off = pd.SKIN_OFFSET
    out = []
    for name in names:
        wr, wt, _ = ours[name]
        rt = zb.transpose(wr)
        st = [-v for v in zb.apply(rt, [off[i] + wt[i] for i in range(3)])]
        out.append(dict(name=name, node_rot=zb.flat(wr), node_t=tuple(wt), sphere=(0.0, 0.0, 0.0, 0.0),
                        skin_rot=zb.flat(rt), skin_t=tuple(st), scale=1.0))
    return out, ours


def prove_pelvis(n, s, ours):
    """the file's own Pelvis_skin skin transform, recomputed from Servitron's skeleton and our skin offset"""
    bones, xf = n.skin(s)
    if 'Pelvis_skin' not in bones:
        raise ValueError(f'{s.name}: not skinned to Pelvis_skin')
    rot, t, _ = xf[bones.index('Pelvis_skin')]
    wr, wt, _ = ours['Pelvis_skin']
    rt = zb.transpose(wr)
    st = [-v for v in zb.apply(rt, [pd.SKIN_OFFSET[i] + wt[i] for i in range(3)])]
    err = max(max(abs(a - b) for a, b in zip(zb.flat(rt), rot)), max(abs(a - b) for a, b in zip(st, t)))
    if err > 0.01:
        raise ValueError(f'{s.name}: its Pelvis_skin is bound {err:.3f} off ours: not the Servitron measured here')
    return err


# ---- 2. deeper canals -----------------------------------------------------------------------------------------------

def centreline(p0, t0, path, end_len):
    """dense points from p0 along t0, meeting `path` where it is JOIN deeper (along t0), then the path to end_len of
    its own length: [(arc, point, tangent)] every 0.05"""
    cum = [0.0]
    for a, b in zip(path, path[1:]):
        cum.append(cum[-1] + math.dist(a, b))

    def at(L):
        for k in range(len(path) - 1):
            if L <= cum[k + 1] or k == len(path) - 2:
                q = (L - cum[k]) / max(1e-9, cum[k + 1] - cum[k])
                return add(path[k], mul(sub(path[k + 1], path[k]), q)), unit(sub(path[k + 1], path[k]))
    Lj = next(x * 0.05 for x in range(int(cum[-1] / 0.05) + 1) if dot(sub(at(x * 0.05)[0], p0), t0) >= JOIN)
    p1, t1 = at(Lj)
    k = math.dist(p0, p1)
    dense = []
    for i in range(201):
        u = i / 200
        h = (2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2)
        dense.append(tuple(h[0] * p0[j] + h[1] * k * t0[j] + h[2] * p1[j] + h[3] * k * t1[j] for j in range(3)))
    L = Lj
    while L < end_len:
        L = min(end_len, L + 0.05)
        dense.append(at(L)[0])
    out, arc = [], 0.0
    for i, p in enumerate(dense):
        if i:
            arc += math.dist(dense[i - 1], p)
        tng = unit(sub(dense[min(i + 1, len(dense) - 1)], dense[max(i - 1, 0)]))
        out.append((arc, p, tng))
    return out


def deepen(n, shape_name, o):
    """cut the canal o['cut'] deep, move its end to the path's end, bridge; returns (new file bytes, report,
    {new vertex: source vertex}, the centreline)"""
    s = n.shape(shape_name)
    if s.full or s.uv_at != 8:
        raise ValueError(f'{shape_name}: an unexpected vertex layout (full {s.full}, uv at {s.uv_at})')
    pos, tris = s.positions(), s.triangles()
    c, ax = o['centre'], o['axis']
    dep = [dot(sub(p, c), ax) for p in pos]
    key = {}
    wid = []
    for p in pos:
        wid.append(key.setdefault(tuple(round(x, 3) for x in p), len(key)))
    cut = o['cut']
    cap_t = [k for k, t in enumerate(tris) if any(dep[i] > cut for i in t)]
    capset = set(cap_t)
    kept_t = [k for k in range(len(tris)) if k not in capset]
    edges = collections.Counter()
    for k in kept_t:
        a, b, d = (wid[i] for i in tris[k])
        for x, y in ((a, b), (b, d), (d, a)):
            if x != y:
                edges[tuple(sorted((x, y)))] += 1
    wpos = {}
    for i, p in enumerate(pos):
        wpos.setdefault(wid[i], p)
    nxt = collections.defaultdict(list)
    for (a, b), cnt in edges.items():
        if cnt == 1 and dot(sub(wpos[a], c), ax) > cut - 1.2 and dot(sub(wpos[b], c), ax) > cut - 1.2:
            nxt[a].append(b)
            nxt[b].append(a)
    if not 8 <= len(nxt) <= 80 or any(len(v) != 2 for v in nxt.values()):
        raise ValueError(f'{shape_name}: the cut at {cut} is not one clean loop ({len(nxt)} vertices)')
    loop = [min(nxt)]
    while len(loop) < len(nxt):
        loop.append(next(q for q in nxt[loop[-1]] if q not in loop[-2:]))
    if loop[0] not in nxt[loop[-1]]:
        raise ValueError(f'{shape_name}: the cut is more than one loop')
    O = tuple(sum(wpos[w][k] for w in loop) / len(loop) for k in range(3))
    inner = [p for p, d in zip(pos, dep) if cut - 1.2 < d < cut - 0.4]
    A0 = unit(sub(O, tuple(sum(p[k] for p in inner) / len(inner) for k in range(3))))
    side, up = frame(A0)
    flat = [(dot(sub(wpos[w], O), side), dot(sub(wpos[w], O), up)) for w in loop]
    if sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(flat, flat[1:] + flat[:1])) < 0:
        loop.reverse()
    N = len(loop)
    loopset = set(loop)
    kept_used = collections.defaultdict(list)
    for k in kept_t:
        for i in tris[k]:
            kept_used[wid[i]].append(i)
    cap_used = collections.defaultdict(set)
    for k in cap_t:
        for i in tris[k]:
            if wid[i] in loopset:
                cap_used[wid[i]].add(i)
    kept_rep = [kept_used[w][0] for w in loop]
    cap_verts = {i for k in cap_t for i in tris[k] if wid[i] not in loopset}
    if any(i in {j for k in kept_t for j in tris[k]} for i in cap_verts):
        raise ValueError(f'{shape_name}: a vertex of the end is also in the kept canal')
    cap_len = max(dep[i] for i in cap_verts) - cut
    line = centreline(O, A0, o['path'], o['end'])
    L_t = line[-1][0] - cap_len
    tgt = min(line, key=lambda q: abs(q[0] - L_t))
    R_t = rotation(A0, tgt[2])

    def moved(p, r, at):
        return add(at, apply(r, sub(p, O)))

    def b2f(x):
        return x / 127.5 - 1.0

    def f2b(x):
        return max(0, min(255, int(round((x + 1) * 127.5))))

    def turned(rec, r, p):
        """a vertex record at p with its normal, tangent and bitangent turned by r"""
        rec = bytearray(rec)
        nrm = apply(r, tuple(b2f(x) for x in rec[12:15]))
        tng = apply(r, tuple(b2f(x) for x in rec[16:19]))
        bit = apply(r, (struct.unpack_from('<e', rec, 6)[0], b2f(rec[15]), b2f(rec[19])))
        struct.pack_into('<3e', rec, 0, *p)
        struct.pack_into('<e', rec, 6, bit[0])
        rec[12:15] = bytes(f2b(x) for x in nrm)
        rec[16:19] = bytes(f2b(x) for x in tng)
        rec[15], rec[19] = f2b(bit[1]), f2b(bit[2])
        return bytes(rec)

    records = [bytearray(s.record(i)) for i in range(s.count)]
    for i in cap_verts:                                         # the end, moved in place
        records[i] = bytearray(turned(records[i], R_t, moved(pos[i], R_t, tgt[1])))
    new_recs, new_from = [], {}
    base = s.count
    copy_of = {}
    for w in loop:                                              # the end's side of the cut: copies, moved with it
        for i in sorted(cap_used[w]):
            copy_of[i] = base + len(new_recs)
            new_from[copy_of[i]] = i
            new_recs.append(turned(records[i], R_t, moved(pos[i], R_t, tgt[1])))
    rings = [kept_rep]
    for arc, p, tng in line:
        if not (STEP * 0.5 < arc < L_t - STEP * 0.5) or arc < len(rings) * STEP - 1e-6:
            continue
        r = rotation(A0, tng)
        idx = []
        for j, w in enumerate(loop):
            src = kept_rep[j]
            idx.append(base + len(new_recs))
            new_from[idx[-1]] = src
            new_recs.append(turned(records[src], r, moved(wpos[w], r, p)))
        rings.append(idx)
    rings.append([copy_of[min(cap_used[w])] for w in loop])
    cap_tris = [tuple(copy_of.get(i, i) for i in tris[k]) for k in cap_t]
    faces = []
    for ra, rb in zip(rings, rings[1:]):
        for j in range(N):
            j2 = (j + 1) % N
            faces += [(ra[j], rb[j], rb[j2]), (ra[j], rb[j2], ra[j2])]
    allpos = [tuple(struct.unpack_from('<3e', bytes(r), 0)) for r in records] + \
             [tuple(struct.unpack_from('<3e', r, 0)) for r in new_recs]
    # the kept canal's winding, read off a kept triangle on the cut: the new faces match it
    ref = next(tris[k] for k in kept_t if sum(wid[i] in loopset for i in tris[k]) >= 2)
    rn = cross(sub(pos[ref[1]], pos[ref[0]]), sub(pos[ref[2]], pos[ref[0]]))
    rmid = mul(add(add(pos[ref[0]], pos[ref[1]]), pos[ref[2]]), 1 / 3)
    inward = dot(rn, sub(O, rmid)) > 0

    def oriented(t):
        a, b, d = (allpos[x] for x in t)
        nrm = cross(sub(b, a), sub(d, a))
        mid = mul(add(add(a, b), d), 1 / 3)
        near = min(line, key=lambda q: math.dist(q[1], mid))[1]
        return t if (dot(nrm, sub(near, mid)) > 0) == inward else (t[0], t[2], t[1])
    faces = [oriented(t) for t in faces]
    all_tris = [tris[k] for k in kept_t] + cap_tris + faces
    vdata = b''.join(bytes(r) for r in records) + b''.join(new_recs)
    tri_bytes = b''.join(struct.pack('<3H', *t) for t in all_tris)
    ob, size = n.offsets[s.index]
    cur = nif.Cursor(n.b, ob)
    n._av(cur)
    cur.take('4f')
    cur.take('i'), cur.take('i'), cur.take('i')
    cur.take('Q')
    counts_at = cur.o
    tail = bytes(n.b[s.data_at + s.count * s.stride + 6 * s.triangle_count:ob + size])
    nverts = s.count + len(new_recs)
    if nverts > 0xFFFF:
        raise ValueError('more than 65,535 vertices')
    blk = bytes(n.b[ob:counts_at]) + struct.pack('<IHI', len(all_tris), nverts, len(vdata) + len(tri_bytes)) \
        + vdata + tri_bytes + tail
    out = n.with_edits(replace={s.index: blk})
    seam = collections.Counter()
    for t in faces:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            seam[tuple(sorted((a, b)))] += 1
    inner_edges = sum(1 for e, cnt in seam.items() if cnt != 2)
    if inner_edges != 2 * N:                                     # the bridge's only open edges: its two end loops
        raise ValueError(f'{shape_name}: the bridge has {inner_edges} open edges, not {2 * N}')
    # the canal's whole centreline from its entrance: straight in to the cut, then the bridge's line (distances along
    # it are what the weights and the rings measure)
    lead = math.dist(c, O)
    full = [(k * 0.05, add(c, mul(sub(O, c), k * 0.05 / lead)), unit(sub(O, c))) for k in range(int(lead / 0.05))]
    line = full + [(arc + lead, p, tng) for arc, p, tng in line]
    report = (f'{shape_name}: cut {cut} deep (a loop of {N}), its end ({len(cap_verts)} vertices, {cap_len:.2f} long) '
              f'moved {math.dist(O, tgt[1]):.1f} along the path to {line[-1][0]:.1f}, {len(rings) - 2} bridge rings '
              f'({len(new_recs)} vertices, {len(faces)} triangles)')
    return out, report, new_from, line


# ---- 3. weights ---------------------------------------------------------------------------------------------------------

def ring_pairs(p, o):
    """[(ring bone, share)] around the opening by angle: the two nearest of four, linearly"""
    side, up = frame(o['axis'])
    d = sub(p, o['centre'])
    a = math.degrees(math.atan2(dot(d, up), dot(d, side))) % 360.0
    out = []
    for tag, at in RING_ANGLES.items():
        gap = min(abs(a - at), 360.0 - abs(a - at))
        if gap < 90.0:
            out.append((pd.SRV_STRETCH_BONES[f"{o['bones']}_{tag}"], 1.0 - gap / 90.0))
    return out


RING_LIP, RING_EDGE, RING_EDGE_SHARE = 1.05, 1.85, 1.0      # radial: the whole ring on ours (was 25% at the edge: SHELL_FULL)


def ring_share(p, o):
    """how much of a ring vertex our ring bones carry: 1 at the lip, RING_EDGE_SHARE at its outer edge, smoothly"""
    d = sub(p, o['centre'])
    along = dot(d, o['axis'])
    r = math.sqrt(max(0.0, dot(d, d) - along * along))
    t = min(1.0, max(0.0, (r - RING_LIP) / (RING_EDGE - RING_LIP)))
    t = t * t * (3 - 2 * t)
    return 1.0 - (1.0 - RING_EDGE_SHARE) * t


def arc_of(p, line):
    """how far along the canal's centreline (its entrance first) a point lies"""
    q = min(line, key=lambda x: math.dist(x[1], p))
    return q[0]


def weigh(n, s, wants):
    """set each vertex's weights: wants {vertex: [(bone, w)]} take their share, the vertex's own make room"""
    bones, _ = n.skin(s)
    slot = {b: k for k, b in enumerate(bones)}
    for i, add_w in wants.items():
        total = min(1.0, sum(w for _, w in add_w))
        if total <= 0:
            continue
        own = [(bones[sl], w * (1.0 - total)) for sl, w in s.skin_weights(i)]
        merged = collections.defaultdict(float)
        for b, w in list(add_w) + own:
            merged[b] += w
        pairs = sorted(merged.items(), key=lambda t: -t[1])[:4]
        s.set_skin_weights(i, [(slot[b], w) for b, w in pairs])


def refit_spheres(n, s, names):
    bones, xf = n.skin(s)
    pos = s.positions()
    carried = collections.defaultdict(list)
    for i in range(s.count):
        for sl, w in s.skin_weights(i):
            if bones[sl] in names and w > 0:
                carried[bones[sl]].append(i)
    o, _ = n.offsets[s.skin]
    cur = nif.Cursor(n.b, o)
    cur.take('i')
    data = cur.take('i')
    do, _ = n.offsets[data]
    for b, vs in carried.items():
        rot, t, sc = xf[bones.index(b)]
        bp = [tuple(sum(rot[3 * r + k] * pos[v][k] for k in range(3)) * sc + t[r] for r in range(3)) for v in vs]
        ctr = tuple(sum(p[k] for p in bp) / len(bp) for k in range(3))
        struct.pack_into('<4f', n.b, do + 4 + bones.index(b) * 68, *ctr, max(math.dist(ctr, p) for p in bp))
    return {b: len(v) for b, v in carried.items()}


# ---- the whole -------------------------------------------------------------------------------------------------------

def build(src, dst, osd=None, measure=False):
    """src .nif -> dst .nif (and osd (in, out) .osd); returns report lines"""
    shutil.copyfile(src, dst)
    n = nif.Nif(dst)
    shell = next((sh for sh in SHELLS if any(s.name == sh for s in n.shapes())), None)
    if shell is None:
        raise ValueError(f'{pathlib.Path(src).name}: not one of the rubber abdomens {SHELLS}')
    lines = []
    new_bones = list(pd.SRV_STRETCH_BONES.values()) + list(pd.SRV_CANAL_BONES)
    defs, ours = bone_defs(new_bones)
    targets = [shell] + [shell + o[k] for o in OPENINGS.values() for k in ('ring', 'canal')]
    for name in targets:
        err = prove_pelvis(n, n.shape(name), ours)
        pathlib.Path(dst).write_bytes(n.with_bones(n.shape(name), defs))
        n = nif.Nif(dst)
    lines.append(f'bones: {len(new_bones)} added to {len(targets)} shapes (Pelvis_skin bound as ours to {err:.4f})')
    import osd as osd_mod
    data = osd_mod.read(osd[0]) if osd else None
    lines_by = {}
    for nm, o in OPENINGS.items():
        cname = shell + o['canal']
        out, report, new_from, line = deepen(n, cname, o)
        pathlib.Path(dst).write_bytes(out)
        n = nif.Nif(dst)
        lines.append(report)
        lines_by[nm] = line
        if data is not None:
            for key_, diffs in data.items():
                if key_.startswith(cname):
                    for v, srcv in new_from.items():
                        if srcv in diffs:
                            diffs[v] = diffs[srcv]
    if measure:
        lines.append(measure_rings(n.shape(shell + OPENINGS['vagina']['canal']), lines_by['vagina']))
    # weights
    for nm, o in OPENINGS.items():
        ring = n.shape(shell + o['ring'])
        # the ring's own lip opens on our bones; its outer edge, where the shell meets it, keeps most of its own weights
        # (pelvis, thighs, butt): fully on ours it stayed with the pelvis while the shell around it spread with the
        # thighs, and the shell tore into flaps beside it in a scene (the owner's photos, 2026-10-08)
        weigh(n, ring, {i: [(b, x * ring_share(p, o)) for b, x in ring_pairs(p, o)] for i, p in enumerate(ring.positions())})
        canal = n.shape(shell + o['canal'])
        line = lines_by[nm]
        want = {}
        for i, p in enumerate(canal.positions()):
            a = arc_of(p, line)
            w = [(b, x * max(0.0, 1.0 - a / RING_FADE)) for b, x in ring_pairs(p, o)]
            if o['wrap'] and pd.SRV_CANAL_RINGS:
                w += wrap_pairs(p, a)
            if w:
                want[i] = w
        weigh(n, canal, want)
    # the suit: both openings in ONE pass (they lie 3.6 apart, so their reaches overlap on the perineum, and a second
    # weigh would shrink the first one's share there)
    # weigh would shrink the first one's share there). Where both reach (the perineum: the rings' edges lie 0.09 apart),
    # the suit follows the NEARER ring, blended over PERINEUM_BLEND across the midline: split evenly, the strip beside a
    # ring that opens alone moved half as far as its edge (0.8 apart, studies/servitron_ring_open.py)
    sh = n.shape(shell)
    want = {}
    for i, p in enumerate(sh.positions()):
        shares = []
        for nm, o in OPENINGS.items():
            d = sub(p, o['centre'])
            along = dot(d, o['axis'])
            across = math.sqrt(max(0.0, dot(d, d) - along * along))
            gap = math.hypot(along, max(0.0, across - SHELL_FULL))
            t = 0.0
            if gap < SHELL_REACH:
                t = 1.0 - gap / SHELL_REACH
                t = t * t * (3 - 2 * t)
            shares.append((t, math.hypot(along, across), o))
        if not any(t for t, _, _ in shares):
            continue
        (tv, dv, ov), (ta, da, oa) = shares
        s = min(1.0, max(0.0, 0.5 + (dv - da) / (2 * PERINEUM_BLEND)))      # 0 nearer the vagina, 1 nearer the anus
        s = s * s * (3 - 2 * s)
        want[i] = ([(b, x * tv * (1 - s)) for b, x in ring_pairs(p, ov)] +
                   [(b, x * ta * s) for b, x in ring_pairs(p, oa)])
    weigh(n, sh, want)
    used = {}
    for name in targets:
        used.update({k: used.get(k, 0) + v for k, v in refit_spheres(n, n.shape(name), set(new_bones)).items()})
    n.save(dst)
    lines.append(f'weights: {len(used)} of {len(new_bones)} new bones carry vertices '
                 f'({sum(1 for b in pd.SRV_STRETCH_BONES.values() if used.get(b))} ring, '
                 f'{sum(1 for b in pd.SRV_CANAL_BONES if used.get(b))} canal)')
    if data is not None:
        osd_mod.write(osd[1], data)
    return lines


def wrap_pairs(p, a):
    """the vaginal canal's wrap rings: the two rings around its place and the two spokes around its angle"""
    rings = [(_zero(c, pd.SRV_VAGINA_SHIFT), a) for c, a in pd.SRV_CANAL_RINGS]   # in the zero-slider files
    K, S = len(rings), pd.CANAL_SPOKES
    fade = min(1.0, max(0.0, (a - WRAP_FROM) / (WRAP_FULL - WRAP_FROM)))
    if fade <= 0:
        return []
    best = None
    for k in range(K - 1):
        c0, c1 = rings[k][0], rings[k + 1][0]
        seg = sub(c1, c0)
        f = dot(sub(p, c0), seg) / dot(seg, seg)
        q = min(1.0, max(0.0, f))
        d = math.dist(p, add(c0, mul(seg, q)))
        if best is None or d < best[0]:
            best = (d, k + (f if k in (0, K - 2) else q))
    r = min(K - 1.0, max(0.0, best[1]))
    k0 = min(K - 2, int(r))
    f = r - k0
    c = add(mul(rings[k0][0], 1 - f), mul(rings[k0 + 1][0], f))
    ax = unit(add(mul(unit(rings[k0][1]), 1 - f), mul(unit(rings[k0 + 1][1]), f)))
    side, up = frame(ax)
    d = sub(p, c)
    sp = (math.atan2(dot(d, up), dot(d, side)) % (2 * math.pi)) / (2 * math.pi) * S
    j0, g = int(sp) % S, sp - int(sp)
    out = []
    for kk, wk in ((k0, 1 - f), (k0 + 1, f)):
        for j, wj in ((j0, 1 - g), ((j0 + 1) % S, g)):
            if wk * wj > 0:
                out.append((f'{pd.SRV_CANAL_PREFIX}{kk + 1}_{j}', fade * wk * wj))
    return out


def measure_rings(s, line, at=(1.5, 4.0, 6.5, 9.0, 10.8, 11.7)):
    """SRV_CANAL_RINGS: the deepened canal's centre and axis at each distance along it (x on the midline)"""
    pos = s.positions()
    arcs = [arc_of(p, line) for p in pos]
    rows = []
    for L in at:
        band = [p for p, a in zip(pos, arcs) if abs(a - L) < 0.5]
        ahead = [p for p, a in zip(pos, arcs) if abs(a - (L + 0.8)) < 0.4]
        behind = [p for p, a in zip(pos, arcs) if abs(a - (L - 0.8)) < 0.4]
        if not band or not ahead or not behind:
            raise ValueError(f'the canal has no vertices around {L} along it')
        cen = lambda ps: tuple(sum(p[k] for p in ps) / len(ps) for k in range(3))
        c = add(cen(band), pd.SRV_VAGINA_SHIFT)           # where the built body has it
        ax = unit(sub(cen(ahead), cen(behind)))
        rows.append(((0.0, round(c[1], 3), round(c[2], 3)), (0.0, round(ax[1], 3), round(ax[2], 3))))
    return 'SRV_CANAL_RINGS = (' + ',\n                   '.join(str(r) for r in rows) + ')'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--osd', nargs=2)
    ap.add_argument('--measure', action='store_true')
    a = ap.parse_args()
    for line in build(a.src, a.dst, a.osd, a.measure):
        print(line)


if __name__ == '__main__':
    main()


SET_NAMES = ('Servitron Abdomen GITS Rubber', 'Servitron Abdomen Wetsuit Rubber')
BS_SRC = pathlib.Path(r'D:\F4Output\servitron\x\bs\Data\tools\BodySlide')    # Servitron's own BodySlide files


def bodyslide(rig_shapedata, target, preset='Servitron', sets=SET_NAMES):
    """the two rigged rubber abdomens built by the LAB's BodySlide at `preset` (with their .tri) into target; Servitron's
    set, preset and the rest of its ShapeData go in beside them for the run, and the LAB is put back after"""
    import garments
    import prebuilt_bodies as pb
    lab = pb.LAB
    swap = ['SliderSets/Servitron.osp', 'SliderPresets/Servitron.xml', 'ShapeData/Servitron', 'SliderGroups/AnatSrvBuild.xml',
            'SliderSets/Servitron Bunny.osp', 'SliderSets/Servitron French Maid.osp',
            'ShapeData/Servitron Bunny', 'ShapeData/Servitron French Maid']   # the outfits' own projects (the owner saw
                                                                              # their sets fail without them, 10-08)
    backup = target.parent / f'lab_backup_{target.name}'
    shutil.rmtree(backup, ignore_errors=True)
    for rel in swap:
        if (lab / rel).exists():
            (backup / rel).parent.mkdir(parents=True, exist_ok=True)
            (shutil.copytree if (lab / rel).is_dir() else shutil.copy2)(lab / rel, backup / rel)
    try:
        for rel in swap[:2] + swap[4:]:
            (lab / rel).parent.mkdir(parents=True, exist_ok=True)
            if (BS_SRC / rel).is_dir():
                shutil.rmtree(lab / rel, ignore_errors=True)
                shutil.copytree(BS_SRC / rel, lab / rel)
            else:
                shutil.copy2(BS_SRC / rel, lab / rel)
        shutil.rmtree(lab / swap[2], ignore_errors=True)
        shutil.copytree(BS_SRC / swap[2], lab / swap[2])
        for f in rig_shapedata.iterdir():
            shutil.copy2(f, lab / swap[2] / f.name)
        (lab / swap[3]).write_text('<?xml version="1.0" encoding="UTF-8"?>\n<SliderGroups>\n    <Group name="AnatSrvBuild">\n'
                                   + ''.join(f'        <Member name="{s}"/>\n' for s in sets)
                                   + '    </Group>\n</SliderGroups>\n', encoding='utf-8')
        shutil.rmtree(target, ignore_errors=True)
        rr, answered = garments.run_bodyslide([str(lab / 'BodySlide.exe'), '--groupbuild', 'AnatSrvBuild', '--targetdir',
                                               str(target), '--preset', preset, '--trimorphs'], lab, 1800)
        return f'BodySlide {len(sets)} sets at "{preset}": exit {rr.returncode} {answered or ""}'
    finally:
        for rel in swap:
            p = lab / rel
            if p.exists():
                (shutil.rmtree if p.is_dir() else pathlib.Path.unlink)(p)
            if (backup / rel).exists():
                (shutil.copytree if (backup / rel).is_dir() else shutil.copy2)(backup / rel, p)
