"""Servitron's MALE abdomen (the owner's poll, 2026-10-08: "1 + 2" - the abdomen decides the robot's sex, and we build a
male module): our rigged rubber abdomen (tools/servitron.py) with the vagina closed, the anus kept, and a robotic latex
penis with balls of our own making (no other author's mesh), rigged to the skeleton's own penis chain (Penis_00..05,
Penis_Balls_01/02: ZeX's names, which Servitron Physics Fix's skeleton has), so the Anatomy Engine's aim and AAF's
animations drive it like a man's.

Made in the zero-slider BodySlide files (rig/ShapeData), next to the original set:
- the vaginal ring shape becomes the penis (renamed AnatServitronPenis: the engine tells a male Servitron by it), its
  skin gains the penis bones; the vaginal canal shape keeps its vertices and draws nothing;
- the shell's vaginal opening is capped (a shallow dome off its rim, the rim's weights, UVs and slider diffs);
- the penis's base flange starts inside the body and takes the shell's slider diffs there, fading out along the shaft,
  so any body shape keeps it seated; the shaft itself is rigid between its bones;
- a slider set "Servitron Abdomen <X> Rubber Male" (osp) whose data files are this nif's own .osd.

    python tools/servitron_male.py <rig ShapeData folder> <out ShapeData folder>   -> both rubber abdomens' male versions
"""
import collections
import math
import pathlib
import re
import shutil
import struct
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402
import osd as osd_mod  # noqa: E402
import physics_design as pd  # noqa: E402
import servitron as srv  # noqa: E402
import zex_bones as zb  # noqa: E402

PENIS = 'AnatServitronPenis'
CHAIN = ['Penis_00', 'Penis_01', 'Penis_02', 'Penis_03', 'Penis_04', 'Penis_05']
BALLS = ['Penis_Balls_01', 'Penis_Balls_02']
SIDES = 24                                    # around the shaft
TIP = 2.4                                     # the glans runs this far past Penis_05
INSIDE = 2.6                                  # the base flange starts this deep in the body (the preset moves the skin ~1)
SEAT = 1.6                                    # the first units take the shell's slider diffs, fading to none
# radius along the shaft, s = units from Penis_00 (negative: inside): a flange, a bead where it leaves the body, a
# shaft with a groove at each joint (the robot's segments), a crowned glans and a rounded tip
def radius(s, length):
    tip = length + TIP
    if s < -1.2:
        return 2.35
    if s < 0.0:
        return 2.35 - 0.35 * (s + 1.2) / 1.2
    if s < 0.6:
        return 2.0 - 0.45 * (s / 0.6)
    glans0 = tip - 3.6
    if s < glans0:
        return 1.5
    if s < glans0 + 0.5:
        return 1.5 + 0.32 * (s - glans0) / 0.5
    t = (s - glans0 - 0.5) / (tip - glans0 - 0.5)
    return max(0.0, 1.82 * math.sqrt(max(0.0, 1.0 - t ** 2.2)))


GROOVE_W, GROOVE_D = 0.28, 0.12
BALL_R = 1.25
STEP = 0.25                                   # along the shaft


def unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else v


def f2b(x):
    return max(0, min(255, int(round((x + 1) * 127.5))))


def chain_points():
    world = zb.skeleton_world(srv.SKELETON)
    off = np.array(pd.SKIN_OFFSET)
    pts = [np.array(world[b][1]) + off for b in CHAIN]
    balls = [np.array(world[b][1]) + off for b in BALLS]
    return pts, balls, world


def penis_mesh(pts, balls):
    """[(pos, normal, (u, v), [(bone, w)])], triangles; u/v in 0..1 of the penis's own strip"""
    seg = [float(np.linalg.norm(pts[k + 1] - pts[k])) for k in range(len(pts) - 1)]
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    length = float(cum[-1])
    d0, d1 = unit(pts[1] - pts[0]), unit(pts[-1] - pts[-2])

    def at(s):                                 # the centreline point and direction s units along
        if s <= 0:
            return pts[0] + d0 * s, d0
        if s >= length:
            return pts[-1] + d1 * (s - length), d1
        k = int(np.searchsorted(cum, s) - 1)
        t = (s - cum[k]) / seg[k]
        return pts[k] + (pts[k + 1] - pts[k]) * t, unit(pts[k + 1] - pts[k])

    def weights(s):
        if s <= 0:                             # the flange: the body's pelvis holding it, Penis_00 lifting it
            t = min(1.0, -s / INSIDE)
            return [('Pelvis_skin', 0.3 + 0.7 * t), (CHAIN[0], 0.7 - 0.7 * t)]
        if s >= length:
            return [(CHAIN[-1], 1.0)]
        k = int(np.searchsorted(cum, s) - 1)
        t = (s - cum[k]) / seg[k]
        return [(CHAIN[k], 1.0 - t), (CHAIN[k + 1], t)]

    up = np.array([0.0, 0.0, 1.0])
    verts, tris = [], []
    s_list = list(np.arange(-INSIDE, length + TIP, STEP)) + [length + TIP]
    total = s_list[-1] - s_list[0]
    rings = []
    for s in s_list:
        c, d = at(s)
        side = unit(np.cross(d, up))
        upp = unit(np.cross(side, d))
        r = radius(s, length)
        for kk in range(1, len(pts) - 1):      # a groove at each inner joint
            if abs(s - cum[kk]) < GROOVE_W:
                r -= GROOVE_D * (1.0 - abs(s - cum[kk]) / GROOVE_W)
        ring = []
        for j in range(SIDES + 1):
            a = 2 * math.pi * j / SIDES
            nrm = side * math.cos(a) + upp * math.sin(a)
            ring.append(len(verts))
            verts.append((c + nrm * max(r, 0.0), nrm, (j / SIDES, (s - s_list[0]) / total), weights(s)))
        rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        for j in range(SIDES):
            tris.append((ra[j], rb[j], rb[j + 1]))
            tris.append((ra[j], rb[j + 1], ra[j + 1]))
    # the balls: two spheres side by side, hung from the balls bones
    top, bottom = balls
    centre = (top + bottom) / 2 + np.array([0.0, -0.4, 0.0])
    for sx in (-1.0, 1.0):
        bc = centre + np.array([sx * 1.05, 0.0, 0.0])
        base = len(verts)
        n_lat, n_lon = 10, SIDES
        for i in range(n_lat + 1):
            th = math.pi * i / n_lat
            for j in range(n_lon + 1):
                ph = 2 * math.pi * j / n_lon
                nrm = np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)])
                p = bc + nrm * BALL_R * np.array([0.9, 1.0, 1.15])
                t = min(1.0, max(0.0, (top[2] - p[2]) / max(1e-6, top[2] - bottom[2])))
                verts.append((p, nrm, (0.5 + 0.5 * j / n_lon * 0.5, 0.5 + 0.5 * i / n_lat * 0.5),
                              [(BALLS[0], 1.0 - t), (BALLS[1], t)]))
        for i in range(n_lat):
            for j in range(n_lon):
                a, b = base + i * (n_lon + 1) + j, base + (i + 1) * (n_lon + 1) + j
                tris.append((a, b, b + 1))
                tris.append((a, b + 1, a + 1))
    return verts, tris, length


def rebuild(n, s, records, tris, sphere=None):
    """the shape's vertex and triangle data replaced (its segment data kept); new file bytes"""
    o, size = n.offsets[s.index]
    cur = nif.Cursor(n.b, o)
    n._av(cur)
    sph_at = cur.o
    cur.take('4f')
    cur.take('i'), cur.take('i'), cur.take('i')
    cur.take('Q')
    counts_at = cur.o
    tail = bytes(n.b[s.data_at + s.count * s.stride + 6 * s.triangle_count:o + size])
    vdata = b''.join(bytes(r) for r in records)
    tdata = b''.join(struct.pack('<3H', *t) for t in tris)
    head = bytearray(n.b[o:counts_at])
    if sphere is not None:
        struct.pack_into('<4f', head, sph_at - o, *sphere)
    blk = bytes(head) + struct.pack('<IHI', len(tris), len(records), len(vdata) + len(tdata)) + vdata + tdata + tail
    return n.with_edits(replace={s.index: blk})


def set_record(rec, s, pos, nrm, uv, wts, slots, tangent):
    struct.pack_into('<3e', rec, 0, *pos)
    struct.pack_into('<2e', rec, s.uv_at, *uv)
    nrm = unit(np.asarray(nrm, float))
    t = unit(np.asarray(tangent, float) - nrm * float(np.dot(tangent, nrm)))
    bt = unit(np.cross(nrm, t))
    rec[12:15] = bytes(f2b(x) for x in nrm)
    rec[16:19] = bytes(f2b(x) for x in t)
    struct.pack_into('<e', rec, 6, float(bt[0]))
    rec[15], rec[19] = f2b(bt[1]), f2b(bt[2])
    pairs = sorted(((slots[b], w) for b, w in wts if w > 0), key=lambda p: -p[1])[:4]
    tot = sum(w for _, w in pairs) or 1.0
    pairs = [(sl, w / tot) for sl, w in pairs] + [(0, 0.0)] * (4 - len(pairs))
    struct.pack_into('<4e', rec, s.skin_at, *[w for _, w in pairs])
    struct.pack_into('<4B', rec, s.skin_at + 8, *[sl for sl, _ in pairs])


def rim_loop(s, centre):
    """the shell's open rim nearest `centre` (welded positions): [split vertex in loop order]"""
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
    return min(loops, key=lambda L: float(np.linalg.norm(np.mean([pos[i] for i in L], axis=0) - centre)))


def build(src, dst, src_osd, dst_osd):
    shutil.copyfile(src, dst)
    n = nif.Nif(dst)
    names = {s.name for s in n.shapes()}
    shell = next(sh for sh in srv.SHELLS if sh in names)
    ring, canal = shell + '_VRing2', shell + '_VInsides'
    data = osd_mod.read(src_osd)
    lines = []
    # 1. the vaginal opening capped: a shallow dome off its rim, two rings in
    s = n.shape(shell)
    o = srv.OPENINGS['vagina']
    centre, axis = np.array(o['centre']), np.array(o['axis'])
    loop = rim_loop(s, centre)
    P = np.array([s.positions()[i] for i in loop])
    c = P.mean(axis=0)
    out = -unit(axis)                                         # the opening faces out of the body
    recs, new_from, cap_tris = [], [], []
    base = s.count
    rings_idx = [list(loop)]
    for k, frac in enumerate((0.6, 0.25)):
        idx = []
        for j, i in enumerate(loop):
            p = c + (P[j] - c) * frac + out * 0.18 * (1 - frac ** 2)
            rec = bytearray(s.record(i))
            struct.pack_into('<3e', rec, 0, *p)
            u0, v0 = s.uv(i)
            uc = np.mean([s.uv(x) for x in loop], axis=0)
            struct.pack_into('<2e', rec, s.uv_at, *(uc + (np.array([u0, v0]) - uc) * frac))
            idx.append(base + len(recs))
            recs.append(rec)
            new_from.append(i)
        rings_idx.append(idx)
    rec = bytearray(s.record(loop[0]))
    struct.pack_into('<3e', rec, 0, *(c + out * 0.18))
    struct.pack_into('<2e', rec, s.uv_at, *np.mean([s.uv(x) for x in loop], axis=0))
    apex = base + len(recs)
    recs.append(rec)
    new_from.append(loop[0])
    N = len(loop)
    for ra, rb in zip(rings_idx, rings_idx[1:]):
        for j in range(N):
            cap_tris += [(ra[j], rb[j], rb[(j + 1) % N]), (ra[j], rb[(j + 1) % N], ra[(j + 1) % N])]
    cap_tris += [(rings_idx[-1][j], apex, rings_idx[-1][(j + 1) % N]) for j in range(N)]
    allp = np.vstack([np.array(s.positions()), np.array([struct.unpack_from('<3e', bytes(r), 0) for r in recs])])
    cap_tris = [t if np.dot(np.cross(allp[t[1]] - allp[t[0]], allp[t[2]] - allp[t[0]]), out) > 0 else (t[0], t[2], t[1])
                for t in cap_tris]
    for r in recs:                                            # the cap's normal: out of the body
        r[12:15] = bytes(f2b(x) for x in out)
    old = bytearray(n.b[s.data_at:s.data_at + s.count * s.stride])
    n2 = rebuild(n, s, [old[i * s.stride:(i + 1) * s.stride] for i in range(s.count)] + recs,
                 s.triangles() + cap_tris)
    pathlib.Path(dst).write_bytes(n2)
    n = nif.Nif(dst)
    for key in [k for k in data if k.startswith(shell) and k[len(shell):len(shell) + 1] not in ('_',)]:
        d = data[key]
        for k, i in enumerate(new_from):
            if i in d:
                d[base + k] = d[i]
    lines.append(f'vagina capped: {len(recs)} vertices, {len(cap_tris)} triangles off its rim of {N}')
    # 2. the canal draws nothing (its vertices, and their slider data, stay)
    cs = n.shape(canal)
    keep = bytearray(n.b[cs.data_at:cs.data_at + cs.count * cs.stride])
    pathlib.Path(dst).write_bytes(rebuild(n, cs, [keep[i * cs.stride:(i + 1) * cs.stride] for i in range(cs.count)], []))
    n = nif.Nif(dst)
    # 3. the ring becomes the penis: its skin gains the chain, its geometry is ours
    pts, balls, world = chain_points()
    defs = []
    off = pd.SKIN_OFFSET
    for b in CHAIN + BALLS:
        wr, wt, _ = world[b]
        rt = zb.transpose(wr)
        st = [-v for v in zb.apply(rt, [off[i] + wt[i] for i in range(3)])]
        defs.append(dict(name=b, node_rot=zb.flat(wr), node_t=tuple(wt), sphere=(0.0, 0.0, 0.0, 0.0),
                         skin_rot=zb.flat(rt), skin_t=tuple(st), scale=1.0))
    rs = n.shape(ring)
    have = set(n.skin(rs)[0])
    pathlib.Path(dst).write_bytes(n.with_bones(rs, [d for d in defs if d['name'] not in have]))
    n = nif.Nif(dst)
    rs = n.shape(ring)
    bones = n.skin(rs)[0]
    slots = {b: k for k, b in enumerate(bones)}
    verts, tris, length = penis_mesh(pts, balls)
    # the penis's UVs: a small plain square of the shell's own rubber (its front belly), so it is the same rubber
    sh = n.shape(shell)
    belly = [sh.uv(i) for i, p in enumerate(sh.positions()) if p[1] > 3.0 and -48.5 < p[2] < -44.5 and abs(p[0]) < 3]
    bu = np.array(belly) if belly else np.array([[0.5, 0.5]])
    lo, hi = bu.min(axis=0), bu.max(axis=0)
    template = bytearray(rs.record(0))
    pos_all = np.array([v[0] for v in verts])
    sph_c = pos_all.mean(axis=0)
    sph = (*sph_c, float(np.max(np.linalg.norm(pos_all - sph_c, axis=1))))
    records = []
    shell_pos = np.array(sh.positions())
    for p, nrm, (u, v), w in verts:
        rec = bytearray(template)
        uv = (lo[0] + (hi[0] - lo[0]) * u, lo[1] + (hi[1] - lo[1]) * v)
        set_record(rec, rs, p, nrm, uv, w, slots, np.cross(nrm, [0.0, 0.0, 1.0]) + np.array([1e-3, 0, 0]))
        records.append(rec)
    pathlib.Path(dst).write_bytes(rebuild(n, rs, records, tris, sphere=sph))
    n = nif.Nif(dst)
    rs = n.shape(ring)
    srv.refit_spheres(n, rs, set(CHAIN + BALLS + ['Pelvis_skin']))
    n.save(dst)
    lines.append(f'penis: {len(verts)} vertices, {len(tris)} triangles, shaft {length:.1f} + glans {TIP}, '
                 f'{len(CHAIN)} chain bones + {len(BALLS)} balls bones')
    # its slider data: the base takes the shell's (nearest vertex), fading out by SEAT units along the shaft
    near = {}
    for k, (p, *_rest) in enumerate(verts[:len(verts)]):
        s_along = float(np.dot(p - pts[0], unit(pts[1] - pts[0])))
        if s_along < SEAT and k < (len(verts) - 2 * 11 * (SIDES + 1)):
            near[k] = (int(np.argmin(np.linalg.norm(shell_pos[:s.count] - p, axis=1))),
                       1.0 if s_along <= 0 else max(0.0, 1.0 - s_along / SEAT))
    for key in [k for k in list(data) if k.startswith(ring)]:
        slider = key[len(ring):]
        sd = data.get(shell + slider, {})
        data[PENIS + slider] = {k: tuple(x * f for x in sd[i]) for k, (i, f) in near.items() if i in sd}
        del data[key]
    # the ring's name -> AnatServitronPenis (every block names it by index: the table entry is the whole rename)
    nif.Nif(dst).save_renamed(dst, {ring: PENIS})
    osd_mod.write(dst_osd, data)
    return lines


def osp_set(src_osp, set_name, male_file):
    """the original set's text with a new name, source, output, the ring renamed and the data in the male .osd"""
    t = pathlib.Path(src_osp).read_text(encoding='utf-8', errors='replace')
    m = re.search(rf'<SliderSet name="{re.escape(set_name)}".*?</SliderSet>', t, re.S)
    s = m.group(0)
    stem = set_name.replace('Servitron ', '')
    shell = 'Abdomen_' + stem.split(' ')[1] + '_Rubber'
    s = s.replace(f'<SliderSet name="{set_name}"', f'<SliderSet name="{set_name} Male"')
    s = s.replace(f'<SourceFile>{stem}.nif</SourceFile>', f'<SourceFile>{male_file}.nif</SourceFile>')
    s = s.replace(f'>{stem}</OutputFile>', f'>{male_file}</OutputFile>')
    s = s.replace(f'{stem}.osd\\', f'{male_file}.osd\\')
    s = s.replace(shell + '_VRing2', PENIS)
    return s


def main():
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    sets = []
    for stem in ('Abdomen GITS Rubber', 'Abdomen Wetsuit Rubber'):
        male = stem + ' Male'
        for line in build(src / f'{stem}.nif', out / f'{male}.nif', src / f'{stem}.osd', out / f'{male}.osd'):
            print(f'{male}: {line}')
        sets.append(osp_set(srv.BS_SRC / 'SliderSets' / 'Servitron.osp', f'Servitron {stem}', male))
    osp = out.parent.parent / 'SliderSets' / 'AnatomyServitronMale.osp'
    osp.parent.mkdir(parents=True, exist_ok=True)
    osp.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<SliderSetInfo version="1">\n    ' + '\n    '.join(sets)
                   + '\n</SliderSetInfo>\n', encoding='utf-8')
    print('slider sets ->', osp)


if __name__ == '__main__':
    main()
