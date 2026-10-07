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
    lines = []
    for name in [k for k in SUITS if k in shapes]:
        s = nif.Nif(dst).shape(name)
        pos, tris = s.positions(), s.triangles()

        def ahead(i):
            k = (round(pos[i][0] * CELL), round(pos[i][2] * CELL))
            return k in surface and pos[i][1] > surface[k] - FRONT
        keep = [t for t in tris if not any(ahead(i) for i in t)]
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
