"""BodySlide slider data (.osd): read and write.

Layout, from BodySlide's DiffData.cpp (OSDataFile::Write / ReadOSDData):

    uint32  magic  "OSD\\0" written as a multi-char constant -> bytes 00 44 53 4F
    uint32  version (1)
    uint32  data count
    per data:  uint8 name length, name bytes ("<target><slider>", e.g. "CBBE2VaginaPenetrate")
               uint16 diff count
               diff count x { uint16 vertex index, float x, float y, float z }   (14 bytes, packed)

A diff count is uint16, so one slider can move at most 65,535 vertices.
"""
import pathlib
import struct

MAGIC = b'\x00DSO'
RECORD = struct.Struct('<H3f')


def read(path):
    """{data name: {vertex index: (dx, dy, dz)}} in file order."""
    b = pathlib.Path(path).read_bytes()
    if b[:4] != MAGIC:
        raise ValueError(f'{path}: not a BodySlide .osd (magic {b[:4]!r})')
    version, count = struct.unpack_from('<II', b, 4)
    if version != 1:
        raise ValueError(f'{path}: .osd version {version}, expected 1')
    o, out = 12, {}
    for _ in range(count):
        n = b[o]
        name = b[o + 1:o + 1 + n].decode('latin1')
        o += 1 + n
        k = struct.unpack_from('<H', b, o)[0]
        o += 2
        out[name] = {i: (x, y, z) for i, x, y, z in RECORD.iter_unpack(b[o:o + k * RECORD.size])}
        o += k * RECORD.size
    if o != len(b):
        raise ValueError(f'{path}: {len(b) - o} trailing bytes after {count} data blocks')
    return out


def write(path, data):
    """Write {name: {index: (dx, dy, dz)}}; zero diffs are dropped, indices sorted."""
    parts = [MAGIC, struct.pack('<II', 1, len(data))]
    for name, diffs in data.items():
        raw = name.encode('latin1')
        if len(raw) > 255:
            raise ValueError(f'slider data name too long: {name!r}')
        kept = sorted((i, d) for i, d in diffs.items() if d != (0.0, 0.0, 0.0))
        if len(kept) > 0xFFFF:
            raise ValueError(f'{name}: {len(kept)} diffs, the format holds 65,535')
        parts.append(struct.pack('<B', len(raw)) + raw + struct.pack('<H', len(kept)))
        parts.append(b''.join(RECORD.pack(i, *d) for i, d in kept))
    pathlib.Path(path).write_bytes(b''.join(parts))
