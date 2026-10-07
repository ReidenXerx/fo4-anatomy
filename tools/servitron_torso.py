"""Servitron's breast torsos without their suit's shards over the breasts (the owner's photo, 2026-10-08: "could we remove
that breast clipping metal components of servitron?").

Each "Boobs" / "Robo-Boobs" torso is the suit's open variant (Torso2_GITS_Open, Torso3_GITS_Half_Open[_Metal],
Overalls_Softbody_Open) plus the breasts. The opening is ragged: 380-780 of the suit's vertices sit at or in front of
the breasts' surface (measured per 0.5-unit cell of the breasts' front view), so pieces of it cut across them. Here
every triangle of the suit with a vertex in front of the breasts (less than FRONT behind their surface) inside their
footprint is dropped; vertices stay (so the .osd and .tri keep their numbering), only the triangle list shrinks.
The metal caps (Torso*_UpperBodyCaps / Torso3_Assaultron) sit behind the breasts and are left alone.

    python tools/servitron_torso.py <in folder of torso .nif> <out folder>
"""
import collections
import pathlib
import shutil
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402

BREASTS = ('Boobs', 'Robo-Boobs')
SUITS = ('Torso2_GITS_Open', 'Torso3_GITS_Half_Open', 'Torso3_GITS_Half_Open_Metal', 'Overalls_Softbody_Open')
FRONT = 0.15
# the owner's second photo (10-08): shards still showed. They are the suit's plating (GITS_overalls_torso.bgsm reads as
# rusted metal), not the metal caps (those sit 2.7 to 17 units behind the breasts). After the cut above, hundreds of the
# suit's vertices still lay 0.15 to 1 unit behind the breasts' surface, and in game the breasts end up further back than
# in the file. Inside the breasts' outline the suit is never meant to be seen, so every suit triangle wholly inside it
# (shrunk by one cell, so no hole opens at its edge) and less than BEHIND behind the breasts goes too.
BEHIND = 2.0
CELL = 2.0                 # cells per unit


def front_surface(positions):
    cell = {}
    for p in positions:
        k = (round(p[0] * CELL), round(p[2] * CELL))
        cell[k] = max(cell.get(k, -1e9), p[1])
    return cell


def with_triangles(n, s, tris):
    """the shape's block with a new triangle list, its vertex data as it is"""
    o, size = n.offsets[s.index]
    c = nif.Cursor(n.b, o)
    n._av(c)
    c.take('4f')
    c.take('i'), c.take('i'), c.take('i')
    c.take('Q')
    counts_at = c.o
    vdata = bytes(n.b[s.data_at:s.data_at + s.count * s.stride])
    tail = bytes(n.b[s.data_at + s.count * s.stride + 6 * s.triangle_count:o + size])
    tri_bytes = b''.join(struct.pack('<3H', *t) for t in tris)
    blk = bytes(n.b[o:counts_at]) + struct.pack('<IHI', len(tris), s.count, len(vdata) + len(tri_bytes)) + vdata \
        + tri_bytes + tail
    return n.with_edits(replace={s.index: blk})


def trim(src, dst):
    shutil.copyfile(src, dst)
    n = nif.Nif(dst)
    shapes = {s.name: s for s in n.shapes()}
    b = next((shapes[k] for k in BREASTS if k in shapes), None)
    if b is None:
        return f'{pathlib.Path(src).name}: no breasts, left as it is'
    surface = front_surface(b.positions())
    inner = {k for k in surface if all((k[0] + a, k[1] + c) in surface for a in (-1, 0, 1) for c in (-1, 0, 1))}
    lines = []
    for name in [k for k in SUITS if k in shapes]:
        s = nif.Nif(dst).shape(name)
        pos, tris = s.positions(), s.triangles()

        def ahead(i):
            k = (round(pos[i][0] * CELL), round(pos[i][2] * CELL))
            return k in surface and pos[i][1] > surface[k] - FRONT
        def hidden(i):
            k = (round(pos[i][0] * CELL), round(pos[i][2] * CELL))
            return k in inner and pos[i][1] > surface[k] - BEHIND
        keep = [t for t in tris if not any(ahead(i) for i in t) and not all(hidden(i) for i in t)]
        n = nif.Nif(dst)
        pathlib.Path(dst).write_bytes(with_triangles(n, n.shape(name), keep))
        back = nif.Nif(dst).shape(name)
        if back.count != s.count or len(back.triangles()) != len(keep):
            raise ValueError(f'{name}: the trimmed shape does not read back')
        lines.append(f'{name} {len(tris) - len(keep)} of {len(tris)} triangles off')
    return f'{pathlib.Path(src).name}: ' + ('; '.join(lines) or 'no suit over the breasts')


def main():
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.glob('Torso*Boobs.nif')):
        print(trim(f, dst / f.name))
        osd = f.with_suffix('.osd')
        if osd.exists():
            shutil.copy2(osd, dst / osd.name)       # vertices unchanged: its slider data stands as it is


if __name__ == '__main__':
    main()


# ---- the suit follows the breasts' morphs (the owner's second photo: Silhouette's BodyGen lists ServitronRace, and
# under half its 365 women's templates the suit came out in front of the breasts, studies/servitron_bodygen_clip.py)
FOLLOW_FULL, FOLLOW_TO = 0.6, 1.6    # a suit vertex this near the breasts takes their morphs fully, fading out by here


def _follow_weights(suit_pos, breast_pos):
    """{suit vertex: (nearest breast vertex, share)} for suit vertices within FOLLOW_TO of the breasts"""
    import numpy as np
    B = np.array(breast_pos, np.float32)
    out = {}
    for i, p in enumerate(suit_pos):
        d2 = ((B - np.array(p, np.float32)) ** 2).sum(axis=1)
        j = int(d2.argmin())
        d = float(d2[j]) ** 0.5
        if d < FOLLOW_TO:
            out[i] = (j, 1.0 if d <= FOLLOW_FULL else 1.0 - (d - FOLLOW_FULL) / (FOLLOW_TO - FOLLOW_FULL))
    return out


def follow(sliders, weights, breast_morphs, suit_morphs):
    """the suit's morph of each slider the breasts have becomes, near them, the breasts' own (blended by share)"""
    changed = 0
    for name in breast_morphs:
        bd = sliders[breast_morphs[name]]
        sd = sliders.setdefault(suit_morphs(name), {})
        for i, (j, w) in weights.items():
            b = bd.get(j, (0.0, 0.0, 0.0))
            s = sd.get(i, (0.0, 0.0, 0.0))
            v = tuple(s[k] * (1 - w) + b[k] * w for k in range(3))
            if v != s:
                sd[i] = v
                changed += 1
    return changed


def follow_osd(nif_path, osd_in, osd_out):
    """the BodySlide slider data: breasts and suit by name (<shape><slider>)"""
    import osd as osd_mod
    n = nif.Nif(nif_path)
    shapes = {s.name: s for s in n.shapes()}
    breast = next(k for k in BREASTS if k in shapes)
    suit = next(k for k in SUITS if k in shapes)
    data = osd_mod.read(osd_in)
    w = _follow_weights(shapes[suit].positions(), shapes[breast].positions())
    names = {k[len(breast):]: k for k in data if k.startswith(breast)}
    c = follow(data, w, names, lambda nm: suit + nm)
    osd_mod.write(osd_out, data)
    return f'{pathlib.Path(nif_path).name}: {len(w)} suit vertices follow the breasts in {len(names)} sliders ({c} diffs)'


def read_tri(path):
    """([shape, [(morph, {vertex: delta})]], trailing bytes) of a BodySlide .tri"""
    b = pathlib.Path(path).read_bytes()
    o, shapes = 6, []
    for _ in range(struct.unpack_from('<H', b, 4)[0]):
        shape = b[o + 1:o + 1 + b[o]].decode('latin1')
        o += 1 + b[o]
        (count,) = struct.unpack_from('<H', b, o)
        o += 2
        morphs = []
        for _ in range(count):
            name = b[o + 1:o + 1 + b[o]].decode('latin1')
            o += 1 + b[o]
            mult, nv = struct.unpack_from('<fH', b, o)
            o += 6
            d = {}
            for k in range(nv):
                i, x, y, z = struct.unpack_from('<H3h', b, o + 8 * k)
                d[i] = (x * mult, y * mult, z * mult)
            o += 8 * nv
            morphs.append((name, d))
        shapes.append((shape, morphs))
    return shapes, b[o:]


def write_tri(path, shapes, trailing):
    out = bytearray(b'PIRT' + struct.pack('<H', len(shapes)))
    for shape, morphs in shapes:
        raw = shape.encode('latin1')
        out += bytes([len(raw)]) + raw + struct.pack('<H', len(morphs))
        for name, d in morphs:
            raw = name.encode('latin1')
            items = sorted((i, v) for i, v in d.items() if any(abs(c) > 1e-6 for c in v))
            big = max((abs(c) for _, v in items for c in v), default=0.0)
            mult = big / 32767.0 if big > 0 else 1.0
            out += bytes([len(raw)]) + raw + struct.pack('<fH', mult, len(items))
            out += b''.join(struct.pack('<H3h', i, *(int(round(c / mult)) for c in v)) for i, v in items)
    pathlib.Path(path).write_bytes(bytes(out) + trailing)


def follow_tri(nif_path, tri_path):
    """a built mesh's .tri (LooksMenu's morphs): breasts and suit by shape, morphs by name"""
    n = nif.Nif(nif_path)
    shapes = {s.name: s for s in n.shapes()}
    breast = next(k for k in BREASTS if k in shapes)
    suit = next(k for k in SUITS if k in shapes)
    tri, trailing = read_tri(tri_path)
    by = {shape: dict(morphs) for shape, morphs in tri}
    flat = {}
    for nm, d in by[breast].items():
        flat[('b', nm.rstrip('\0'))] = d
    for nm, d in by.get(suit, {}).items():
        flat[('s', nm.rstrip('\0'))] = d
    w = _follow_weights(shapes[suit].positions(), shapes[breast].positions())
    c = follow(flat, w, {nm: ('b', nm) for _, nm in [k for k in flat if k[0] == 'b']}, lambda nm: ('s', nm))
    rebuilt = []
    for shape, morphs in tri:
        if shape != suit:
            rebuilt.append((shape, morphs))
            continue
        names = [nm for nm, _ in morphs]
        new = [(nm, flat[('s', nm.rstrip('\0'))]) for nm in names]
        new += [(nm, d) for (k, nm), d in flat.items() if k == 's' and nm not in [x.rstrip('\0') for x in names]]
        rebuilt.append((shape, new))
    write_tri(tri_path, rebuilt, trailing)
    return f'{pathlib.Path(tri_path).name}: {len(w)} suit vertices follow the breasts ({c} deltas)'
