"""Fallout 4 .nif (20.2.0.7, Bethesda stream 130): read, and edit vertex records IN PLACE.

Structural edits (adding bones, blocks, strings) are Outfit Studio's job through its automation,
because its writer is the one BodySlide and the game were validated against. This module only
changes bytes whose size never changes: vertex positions and skin weights/indices. The file is
written back byte-for-byte otherwise, so a round trip with no edits is identical.

Layout from NifTools' nif.xml:

  header  "Gamebryo File Format, Version 20.2.0.7\\n", uint32 version, uint8 endian,
          uint32 user version, uint32 block count, BSStreamHeader (uint32 bs version, then author,
          process script, export script, max filepath as uint8-length strings), uint16 block-type
          count + uint32-length names, uint16 type index per block, uint32 size per block,
          uint32 string count + uint32 max length + uint32-length strings, uint32 group count + groups
  NiObjectNET   int32 name (string index), uint32 extra count + int32 refs, int32 controller
  NiAVObject    uint32 flags, float[3] translation, float[9] rotation, float scale, int32 collision
  NiNode        uint32 child count + int32 refs  (no effects list at stream 130)
  BSTriShape    NiAVObject, float[4] bound, int32 skin, int32 shader, int32 alpha, uint64 vertex desc,
                uint32 triangle count, uint16 vertex count, uint32 data size, vertex records,
                triangles (3 x uint16 each). BSSubIndexTriShape appends segment data after that.
  BSSkin::Instance  int32 skeleton root, int32 bone data, uint32 bone count + int32 node refs,
                    uint32 count + float[3] each
  BSSkin::BoneData  uint32 count + per bone: float[4] bound, float[9] rotation, float[3] translation,
                    float scale  (the SKIN-TO-BONE transform: v_bone = R v_skin + t)

  vertex desc: bits 0-3 record size / 4; 8-11 UV offset / 4; 16-19 normal; 20-23 tangent;
               24-27 colour; 28-31 skin data; bits 44.. attribute flags, where 1<<6 = skinned and
               1<<10 = full precision. Skin data = 4 half-float weights then 4 uint8 bone slots.
"""
import math
import pathlib
import struct

SHAPES = ('BSTriShape', 'BSSubIndexTriShape', 'BSMeshLODTriShape', 'BSDynamicTriShape')
VA_SKINNED = 1 << 6
VA_FULL = 1 << 10


class Cursor:
    def __init__(self, b, o=0):
        self.b, self.o = b, o

    def take(self, fmt):
        v = struct.unpack_from('<' + fmt, self.b, self.o)
        self.o += struct.calcsize('<' + fmt)
        return v if len(v) > 1 else v[0]

    def string8(self):
        n = self.take('B')
        s = self.b[self.o:self.o + n]
        self.o += n
        return s

    def string32(self):
        n = self.take('I')
        s = self.b[self.o:self.o + n]
        self.o += n
        return s.decode('latin1')


class Shape:
    """One tri-shape: where its vertex records live in the file and how to read them."""

    def __init__(self, nif, index, name, skin, desc, nv, ntri, data_at):
        self.nif, self.index, self.name, self.skin = nif, index, name, skin
        self.desc, self.count, self.triangle_count = desc, nv, ntri
        self.stride = (desc & 0xF) * 4
        self.flags = (desc >> 44) & 0xFFF
        self.full = bool(self.flags & VA_FULL)
        self.uv_at = ((desc >> 8) & 0xF) * 4
        self.skin_at = ((desc >> 28) & 0xF) * 4
        self.data_at = data_at                     # file offset of vertex 0

    def record(self, i):
        o = self.data_at + i * self.stride
        return bytes(self.nif.b[o:o + self.stride])

    def set_record(self, i, raw):
        if len(raw) != self.stride:
            raise ValueError('record size mismatch')
        o = self.data_at + i * self.stride
        self.nif.b[o:o + self.stride] = raw

    def position(self, i):
        return struct.unpack_from('<3f' if self.full else '<3e', self.nif.b, self.data_at + i * self.stride)

    def positions(self):
        return [self.position(i) for i in range(self.count)]

    def set_position(self, i, p):
        struct.pack_into('<3f' if self.full else '<3e', self.nif.b, self.data_at + i * self.stride, *p)

    def uv(self, i):
        return struct.unpack_from('<2e', self.nif.b, self.data_at + i * self.stride + self.uv_at)

    def skin_weights(self, i):
        """[(bone slot, weight), ...] with zero weights dropped."""
        if not self.flags & VA_SKINNED:
            return []
        o = self.data_at + i * self.stride + self.skin_at
        w = struct.unpack_from('<4e', self.nif.b, o)
        s = struct.unpack_from('<4B', self.nif.b, o + 8)
        return [(s[k], float(w[k])) for k in range(4) if w[k] > 0]

    def set_skin_weights(self, i, pairs):
        """At most 4 (slot, weight) pairs; weights are renormalised to sum to 1 and stored as halves."""
        if not self.flags & VA_SKINNED:
            raise ValueError(f'{self.name}: not skinned')
        pairs = sorted(((s, w) for s, w in pairs if w > 0), key=lambda sw: -sw[1])[:4]
        total = sum(w for _, w in pairs)
        if not pairs or total <= 0:
            raise ValueError(f'{self.name} vertex {i}: no weight left')
        pairs = [(s, w / total) for s, w in pairs] + [(0, 0.0)] * (4 - len(pairs))
        o = self.data_at + i * self.stride + self.skin_at
        struct.pack_into('<4e', self.nif.b, o, *(w for _, w in pairs))
        struct.pack_into('<4B', self.nif.b, o + 8, *(s for s, _ in pairs))

    def triangles(self):
        o = self.data_at + self.count * self.stride
        return [struct.unpack_from('<3H', self.nif.b, o + 6 * k) for k in range(self.triangle_count)]


class Nif:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.b = bytearray(self.path.read_bytes())
        c = Cursor(self.b, self.b.index(b'\n') + 1)
        version, _, _, nblocks = c.take('I'), c.take('B'), c.take('I'), c.take('I')
        if version != 0x14020007:
            raise ValueError(f'{path}: NIF version {version:#x}, expected 20.2.0.7')
        if c.take('I') != 130:
            raise ValueError(f'{path}: not a Fallout 4 NIF (Bethesda stream != 130)')
        for _ in range(4):
            c.string8()
        types = [c.string32() for _ in range(c.take('H'))]
        self.types = [types[c.take('H') & 0x7FFF] for _ in range(nblocks)]
        sizes = [c.take('I') for _ in range(nblocks)]
        n = c.take('I')
        c.take('I')
        self.strings = [c.string32() for _ in range(n)]
        for _ in range(c.take('I')):
            c.take('I')
        self.offsets = []
        o = c.o
        for s in sizes:
            self.offsets.append((o, s))
            o += s
        self.nodes = self._nodes()

    def string(self, index):
        return self.strings[index] if 0 <= index < len(self.strings) else None

    def _av(self, c):
        name = self.string(c.take('i'))
        for _ in range(c.take('I')):
            c.take('i')
        c.take('i')
        c.take('I')
        t = c.take('3f')
        r = c.take('9f')
        s = c.take('f')
        c.take('i')
        return name, t, r, s

    def _nodes(self):
        out = {}
        for i, k in enumerate(self.types):
            if k in ('NiNode', 'BSFadeNode', 'BSLeafAnimNode') or k == 'NiNode':
                o, _ = self.offsets[i]
                c = Cursor(self.b, o)
                name, t, r, s = self._av(c)
                kids = [c.take('i') for _ in range(c.take('I'))]
                out[i] = dict(name=name, t=t, r=r, s=s, kids=kids)
        return out

    def shapes(self):
        out = []
        for i, k in enumerate(self.types):
            if k not in SHAPES:
                continue
            o, _ = self.offsets[i]
            c = Cursor(self.b, o)
            name, *_ = self._av(c)
            c.take('4f')
            skin = c.take('i')
            c.take('i')
            c.take('i')
            desc = c.take('Q')
            ntri = c.take('I')
            nv = c.take('H')
            size = c.take('I')
            if size == 0:
                continue
            out.append(Shape(self, i, name, skin, desc, nv, ntri, c.o))
        return out

    def shape(self, name):
        for s in self.shapes():
            if s.name == name:
                return s
        raise KeyError(f'{self.path.name}: no shape {name!r}')

    def skin(self, shape):
        """(bone names in slot order, [(rotation 9, translation 3, scale)] skin-to-bone)."""
        if shape.skin < 0 or self.types[shape.skin] != 'BSSkin::Instance':
            return [], []
        o, _ = self.offsets[shape.skin]
        c = Cursor(self.b, o)
        c.take('i')
        data = c.take('i')
        refs = [c.take('i') for _ in range(c.take('I'))]
        names = [self.nodes[r]['name'] if r in self.nodes else None for r in refs]
        o, _ = self.offsets[data]
        c = Cursor(self.b, o)
        xf = []
        for _ in range(c.take('I')):
            c.take('4f')
            xf.append((c.take('9f'), c.take('3f'), c.take('f')))
        return names, xf

    def save(self, path):
        pathlib.Path(path).write_bytes(bytes(self.b))


def bone_origin(xf):
    """Where a bone sits in skin space, from its skin-to-bone transform (row-major rotation)."""
    r, t, s = xf
    m = (r[0:3], r[3:6], r[6:9])
    return tuple(-(m[0][i] * t[0] + m[1][i] * t[1] + m[2][i] * t[2]) / s for i in range(3))


def weld(positions, digits=3):
    """Vertex -> welded id, merging vertices that share a position (UV seams split them)."""
    key, out = {}, []
    for p in positions:
        out.append(key.setdefault(tuple(round(c, digits) for c in p), len(key)))
    return out


def openings(positions, triangles):
    """Real holes in a mesh: loops of edges used by exactly one triangle after welding.
    Returns [(vertex count, centre, span)] largest first."""
    import collections
    w = weld(positions)
    edges = collections.Counter()
    for a, b, c in triangles:
        a, b, c = w[a], w[b], w[c]
        for e in ((a, b), (b, c), (c, a)):
            if e[0] != e[1]:
                edges[tuple(sorted(e))] += 1
    first = {}
    for i, wid in enumerate(w):
        first.setdefault(wid, positions[i])
    adj = collections.defaultdict(set)
    for (a, b), n in edges.items():
        if n == 1:
            adj[a].add(b)
            adj[b].add(a)
    seen, loops = set(), []
    for s in adj:
        if s in seen:
            continue
        stack, comp = [s], []
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            comp.append(x)
            stack.extend(adj[x] - seen)
        ps = [first[i] for i in comp]
        centre = tuple(sum(p[j] for p in ps) / len(ps) for j in range(3))
        span = tuple(max(p[j] for p in ps) - min(p[j] for p in ps) for j in range(3))
        loops.append((len(comp), centre, span))
    return sorted(loops, key=lambda l: -l[0])


def dist(a, b):
    return math.dist(a, b)
