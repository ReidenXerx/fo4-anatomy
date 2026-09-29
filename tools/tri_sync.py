"""Give a built body's .tri (BodySlide's PIRT, LooksMenu's morphs) the vertices a canal step added after BodySlide built it.

A .tri stores each morph sparsely, as (vertex, delta) pairs, and its deltas ARE the BodySlide source's slider diffs
(measured 2026-09-30 on Anatomy-dev: equal to 0.0001 wherever both have the vertex). A canal step (anal_canal.py A-50,
vaginal_canal.py A-54) appends vertices to a body that was already built, so its .tri has no entries for them and every
genital morph (VaginaPenetrate, AnusPenetrate, VaginaSize...) would leave them behind: a crack at the canal's entrance.
BodySlide writes them itself on the next build; this fills them in for a staged body until then, from the osd.

    python tools/tri_sync.py <FemaleBody.tri> <Anatomy.osd> [--shape AnatomyGenitals] [--from 2495]
"""
import argparse
import pathlib
import struct

import osd

SHAPE = 'AnatomyGenitals'


def read(path):
    """[(shape, [(morph, mult, {vertex: (x, y, z) int16})])] in file order."""
    b = pathlib.Path(path).read_bytes()
    if b[:4] != b'PIRT':
        raise ValueError(f'{path}: not a BodySlide .tri')
    o, out = 6, []
    for _ in range(struct.unpack_from('<H', b, 4)[0]):
        shape = b[o + 1:o + 1 + b[o]].decode('latin1')
        o += 1 + b[o]
        morphs = []
        (nm,) = struct.unpack_from('<H', b, o)
        o += 2
        for _ in range(nm):
            name = b[o + 1:o + 1 + b[o]].decode('latin1')
            o += 1 + b[o]
            mult, count = struct.unpack_from('<fH', b, o)
            o += 6
            d = {}
            for k in range(count):
                idx, x, y, z = struct.unpack_from('<H3h', b, o + 8 * k)
                d[idx] = (x, y, z)
            o += 8 * count
            morphs.append((name, mult, d))
        out.append((shape, morphs))
    if b[o:] != b'\x00\x00':                                # the UV morphs' section: a body has none
        raise ValueError(f'{path}: {len(b) - o} bytes after the last morph, not an empty UV section')
    return out


def write(path, shapes):
    out = bytearray(b'PIRT' + struct.pack('<H', len(shapes)))
    for shape, morphs in shapes:
        s = shape.encode('latin1')
        out += bytes([len(s)]) + s + struct.pack('<H', len(morphs))
        for name, mult, d in morphs:
            if len(d) > 0xFFFF:
                raise ValueError(f'{shape}/{name}: more than 65,535 vertices')
            m = name.encode('latin1')
            out += bytes([len(m)]) + m + struct.pack('<fH', mult, len(d))
            for idx in sorted(d):
                out += struct.pack('<H3h', idx, *d[idx])
    out += b'\x00\x00'
    pathlib.Path(path).write_bytes(out)


def sync(tri_path, osd_path, shape=SHAPE, first=0):
    """Add the osd's diffs for vertices >= first that the .tri lacks, per morph of shape; writes in place, a report."""
    shapes = read(tri_path)
    data = osd.read(osd_path)
    added = rescaled = 0
    for sh, morphs in shapes:
        if sh != shape:
            continue
        for k, (name, mult, d) in enumerate(morphs):
            diffs = data.get(shape + name, {})
            new = {i: v for i, v in diffs.items() if i >= first and i not in d and any(abs(c) > 1e-6 for c in v)}
            if not new:
                continue
            peak = max(abs(c) for v in new.values() for c in v)
            if peak / mult > 32767:                         # the new deltas outgrow the scale: requantise the morph
                real = {i: tuple(c * mult for c in v) for i, v in d.items()}
                mult = max(peak, max((abs(c) for v in real.values() for c in v), default=0.0)) / 32767
                d = {i: tuple(int(round(c / mult)) for c in v) for i, v in real.items()}
                rescaled += 1
            for i, v in new.items():
                d[i] = tuple(int(round(c / mult)) for c in v)
            added += len(new)
            morphs[k] = (name, mult, d)
    write(tri_path, shapes)
    back = read(tri_path)
    if [(s, [n for n, _, _ in m]) for s, m in back] != [(s, [n for n, _, _ in m]) for s, m in shapes]:
        raise ValueError('the rewritten .tri does not read back')
    return f'tri_sync: {added} entries added to {shape} from the osd ({rescaled} morphs requantised)'


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('tri', type=pathlib.Path)
    ap.add_argument('osd', type=pathlib.Path)
    ap.add_argument('--shape', default=SHAPE)
    ap.add_argument('--from', dest='first', type=int, default=0)
    a = ap.parse_args()
    print(sync(a.tri, a.osd, a.shape, a.first))
