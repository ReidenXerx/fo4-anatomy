"""The neck seam (A-37): the body's neck ring faces the way the head's does, so the join does not light up.

The owner's look (2026-09-26, Photo229/231): "rears on ... necks". The head (FemaleHeadHuman:
BaseFemaleHead.nif) and our body meet at a neck ring whose vertices coincide (0.008 apart), but the two
meshes' normals there are 31.7 deg apart at the median, 37.5 at worst (scratchpad garments/seamlight2.py).
The engine lights each side with its own normals, so the join shows as a line in any light. CBBE HeadRear
Absolute Fix covers the back of the head with a separate piece; the front of the neck keeps the line.

The head is the one to follow: every NPC's head is its own FaceGen mesh, while the body is ours. Per body
vertex within FADE of the neck ring:
  - its ring vertex's rotation is the one that turns the body's normal onto the head's (the head's normal at
    that point interpolated between its two nearest ring vertices);
  - it gets that rotation times (1 - distance / FADE), so the correction fades into the neck with no crease;
  - the WHOLE tangent frame turns (normal, tangent, bitangent: FO4 keeps the bitangent in the position's w,
    the normal's w and the tangent's w), so the normal maps keep reading the same way.
Welded copies (UV seams) move together. Positions, UVs and weights are not touched.

    python tools/neck_seam.py [--project <folder>] [--head <BaseFemaleHead.nif>]   # builder stage 4b
"""
import argparse
import collections
import math
import pathlib
import struct

import align_body as ab
import nif

FADE = 1.5                    # units down the neck over which the correction fades out
RING_DROP = 14.0              # the neck ring: open-edge vertices within this of the body's top
HEAD_RING = -9.0              # the head's neck ring: its open-edge vertices below this height
HEAD_MESH = 'Meshes/actors/character/characterassets/BaseFemaleHead.nif'


def border(shape):
    pos = shape.positions()
    wid = nif.weld(pos)
    e = collections.Counter()
    for t in shape.triangles():
        a, b, c = (wid[x] for x in t)
        for k in ((a, b), (b, c), (c, a)):
            e[tuple(sorted(k))] += 1
    bw = {w for k, v in e.items() if v == 1 for w in k}
    return [i for i, w in enumerate(wid) if w in bw], pos, wid


class Frame:
    """A vertex's normal, tangent and bitangent as stored (FO4 BSVertexData)."""

    def __init__(self, s, i):
        self.s, self.i = s, i
        o = s.data_at + i * s.stride
        self.o = o
        self.na = o + ((s.desc >> 16) & 0xF) * 4
        self.ta = o + ((s.desc >> 20) & 0xF) * 4
        nb = struct.unpack_from('<4B', s.nif.b, self.na)
        tb = struct.unpack_from('<4B', s.nif.b, self.ta)
        bx = struct.unpack_from('<f' if s.full else '<e', s.nif.b, o + (12 if s.full else 6))[0]
        f = lambda v: v / 255.0 * 2 - 1
        self.n = [f(x) for x in nb[:3]]
        self.t = [f(x) for x in tb[:3]]
        self.b = [bx, f(nb[3]), f(tb[3])]

    def write(self):
        q = lambda v: max(0, min(255, int(round((v + 1) / 2 * 255))))
        nb = [q(x) for x in self.n] + [q(self.b[1])]
        tb = [q(x) for x in self.t] + [q(self.b[2])]
        struct.pack_into('<4B', self.s.nif.b, self.na, *nb)
        struct.pack_into('<4B', self.s.nif.b, self.ta, *tb)
        struct.pack_into('<f' if self.s.full else '<e', self.s.nif.b, self.o + (12 if self.s.full else 6), self.b[0])


def unit(v):
    l = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / l for x in v]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def angle(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(unit(a), unit(b)))))))


def rotate(v, axis, rad):
    """Rodrigues: v turned by rad about the unit axis."""
    c, s = math.cos(rad), math.sin(rad)
    d = sum(a * b for a, b in zip(axis, v))
    k = cross(axis, v)
    return [v[i] * c + k[i] * s + axis[i] * d * (1 - c) for i in range(3)]


TOUCH = 0.05                  # a body ring point and a head (or rear-piece) vertex this close are one point


def partners(*paths):
    """(position, normal) of every vertex of the pieces the body's neck ring meets: the head's own neck
    ring, and CBBE HeadRear Absolute Fix's rear piece where it is installed (it, not the head, meets the
    back of the neck: 9 of the 11 back ring points coincide with it, measured)."""
    out = []
    for p in paths:
        if not p:
            continue
        n = nif.Nif(p)
        for s in n.shapes():
            idx, pos, _ = border(s)
            out += [(pos[i], unit(Frame(s, i).n)) for i in idx]
    return out


def target_normal(ring, p):
    """The normal of the piece vertex that coincides with p, or None: a body ring point that touches no
    piece (between the head and the rear piece) is left to its neighbours' fading share. An interpolated
    target once turned the back of the neck 97 deg toward a head 7 units away."""
    best = min(ring, key=lambda r: math.dist(r[0], p))
    return best[1] if math.dist(best[0], p) < TOUCH else None


def apply(nif_path, piece_paths, shape_name=ab.SHAPE):
    body = nif.Nif(nif_path)
    s = body.shape(shape_name)
    idx, pos, wid = border(s)
    top = max(p[2] for p in pos)
    ring = [i for i in idx if top - pos[i][2] < RING_DROP]
    pieces = partners(*piece_paths)
    if not ring or not pieces:
        raise SystemExit(f'neck seam: no neck ring (body {len(ring)} points, pieces {len(pieces)})')
    # each ring vertex a piece touches: the rotation that turns its normal onto the piece's
    fix, want, before = {}, {}, []
    for i in ring:
        w = target_normal(pieces, pos[i])
        if w is None:
            continue
        fr = Frame(s, i)
        a = angle(fr.n, w)
        want[i] = w
        before.append(a)
        axis = cross(unit(fr.n), w)
        if math.sqrt(sum(x * x for x in axis)) < 1e-6:
            continue
        fix[i] = (unit(axis), math.radians(a))
    if not want:
        raise SystemExit('neck seam: no body ring point touches the head or the rear piece')
    if max(before) <= 3.0:                              # already faces them (a second run, AnatomyRebuild)
        print(f'neck seam: the ring already faces the head (worst {max(before):.1f} deg): nothing to do')
        return 0
    # every vertex within FADE of a fixed ring point takes the nearest one's rotation, faded
    changed, done = 0, {}
    for j, p in enumerate(pos):
        g = wid[j]
        if g not in done:
            k = min(fix, key=lambda r: math.dist(pos[r], p)) if fix else None
            d = math.dist(pos[k], p) if k is not None else FADE
            done[g] = (fix[k][0], fix[k][1] * (1 - d / FADE)) if d < FADE else None
        rot = done[g]
        if not rot:
            continue
        fr = Frame(s, j)
        fr.n = unit(rotate(fr.n, rot[0], rot[1]))
        fr.t = unit(rotate(fr.t, rot[0], rot[1]))
        fr.b = unit(rotate(fr.b, rot[0], rot[1]))
        fr.write()
        changed += 1
    after = [angle(Frame(s, i).n, want[i]) for i in want]
    check(before, after)
    body.save(nif_path)
    before.sort()
    after.sort()
    print(f"4b. neck seam: {len(want)} of {len(ring)} neck-ring points touch the head or its rear piece and now "
          f"face their way (median {before[len(before) // 2]:.1f} -> {after[len(after) // 2]:.1f} deg, worst "
          f"{before[-1]:.1f} -> {after[-1]:.1f}); {changed} vertices within {FADE} take a fading share")
    return changed


def check(before, after):
    """The stage's proof: every touching ring point ends within 3 deg of its piece (8-bit normals)."""
    worst = max(after)
    if worst > 3.0:
        raise SystemExit(f'neck seam: a ring point still faces {worst:.1f} deg off its piece')


REAR_MESH = 'Meshes/Actors/Character/CharacterAssets/FaceParts/FemaleheadRear.nif'


def main():
    import zex_bones as zb
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--project', default=str(ab.OUT))
    ap.add_argument('--built', type=pathlib.Path, default=None,
                    help='a BUILT FemaleBody.nif to patch in place (restage does this after BodySlide: '
                         'BodySlide recalculates every normal, so ShapeData cannot carry the fix)')
    args = ap.parse_args([] if __name__ != '__main__' else None)
    import gamedata
    g = gamedata.Game(ab.DEFAULT_DATA)
    paths = []
    where = args.built.parent if args.built else pathlib.Path(args.project)
    for name, rel in (('_head.nif', HEAD_MESH), ('_headrear.nif', REAR_MESH)):
        try:
            raw = g.read(rel)
        except FileNotFoundError:
            continue                                     # no rear piece without CBBE HeadRear Absolute Fix
        tmp = where / name
        tmp.write_bytes(raw)
        paths.append(tmp)
    target = args.built or pathlib.Path(args.project) / 'ShapeData' / zb.OUT_FOLDER / f'{zb.OUT_FOLDER}.nif'
    try:
        apply(target, paths)
    finally:
        for p in paths:                                  # the head copies are not ours to ship
            p.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
