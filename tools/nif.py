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

    def remap_skin_slots(self, i, remap):
        """Point vertex i's influences at other bone slots ({old slot: new slot}); the weight bytes
        are not touched, so the vertex keeps its weights to the last bit (set_skin_weights would
        renormalise and re-round them: measured, 5 of 3,826 moved breast vertices changed)."""
        if not self.flags & VA_SKINNED:
            raise ValueError(f'{self.name}: not skinned')
        o = self.data_at + i * self.stride + self.skin_at + 8
        slots = struct.unpack_from('<4B', self.nif.b, o)
        struct.pack_into('<4B', self.nif.b, o, *(remap.get(s, s) for s in slots))

    def triangles(self):
        o = self.data_at + self.count * self.stride
        return [struct.unpack_from('<3H', self.nif.b, o + 6 * k) for k in range(self.triangle_count)]


class Nif:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.b = bytearray(self.path.read_bytes())
        c = Cursor(self.b, self.b.index(b'\n') + 1)
        version, _, _ = c.take('I'), c.take('B'), c.take('I')
        self.nblocks_at = c.o                    # uint32 block count
        nblocks = c.take('I')
        if version != 0x14020007:
            raise ValueError(f'{path}: NIF version {version:#x}, expected 20.2.0.7')
        if c.take('I') != 130:
            raise ValueError(f'{path}: not a Fallout 4 NIF (Bethesda stream != 130)')
        for _ in range(4):
            c.string8()
        self.type_count_at = c.o                 # uint16 block-type count, then the type names
        types = [c.string32() for _ in range(c.take('H'))]
        self.type_names = types
        self.type_index_at = c.o                 # uint16 per block (high bit a flag), then uint32 sizes
        self.type_index = [c.take('H') for _ in range(nblocks)]
        self.types = [types[t & 0x7FFF] for t in self.type_index]
        sizes = [c.take('I') for _ in range(nblocks)]
        self.strings_at = c.o                    # uint32 count, uint32 max length, the strings
        n = c.take('I')
        c.take('I')
        self.strings = [c.string32() for _ in range(n)]
        self.strings_end = c.o                   # the group list follows
        for _ in range(c.take('I')):
            c.take('I')
        self.data_at = c.o                       # first block
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

    def translate_skin_space(self, shape, d):
        """Move a skinned shape's whole skin space by d, changing nothing about how it deforms.

        Every vertex moves by d. Each bone's skin-to-bone transform v_bone = R v + t must keep
        mapping the moved vertex where it mapped the old one: R (v + d) + t' = R v + t, so
        t' = t - R d. The shape's bounding-sphere centre (shape space) moves by d. A bone's own
        bounding sphere is in bone space and stays. Fixed-size fields only: in place."""
        for i in range(shape.count):
            p = shape.position(i)
            shape.set_position(i, (p[0] + d[0], p[1] + d[1], p[2] + d[2]))
        o, _ = self.offsets[shape.index]
        c = Cursor(self.b, o)
        self._av(c)
        cx, cy, cz, r = struct.unpack_from('<4f', self.b, c.o)
        struct.pack_into('<4f', self.b, c.o, cx + d[0], cy + d[1], cz + d[2], r)
        o, _ = self.offsets[shape.skin]
        c = Cursor(self.b, o)
        c.take('i')
        data = c.take('i')
        o, _ = self.offsets[data]
        c = Cursor(self.b, o)
        for _ in range(c.take('I')):
            c.take('4f')
            rot = c.take('9f')
            at = c.o
            t = struct.unpack_from('<3f', self.b, at)
            rd = [sum(rot[3 * k + j] * d[j] for j in range(3)) for k in range(3)]   # row-major R d
            struct.pack_into('<3f', self.b, at, t[0] - rd[0], t[1] - rd[1], t[2] - rd[2])
            c.o = at + 12
            c.take('f')

    def with_bones(self, shape, bones):
        """New file bytes with `bones` added to `shape`'s skin (weights all zero; set them after).

        bones: [dict(name, node_rot, node_t, sphere, skin_rot, skin_t, scale)], where node_* is the
        bone node's transform as the file stores it (skeleton space for a flat BodySlide file),
        skin_* the skin-to-bone transform and sphere the bone-space bounding sphere (cx, cy, cz, r).

        Fallout 4, stream 130. Each bone is a new NiNode APPENDED after the last block, so no
        existing reference moves. The root NiNode (block 0) gains the child references, the
        BSSkin::Instance the bone references, the BSSkin::BoneData the entries, and the header the
        block count, type indices, sizes and names. The footer (root list) stays last. Every other
        byte is copied unchanged."""
        nb = len(self.offsets)
        root, inst = 0, shape.skin
        if self.types[root] not in ('NiNode', 'BSFadeNode'):
            raise ValueError('block 0 is not a node')
        o, size = self.offsets[inst]
        c = Cursor(self.b, o)
        c.take('i')
        data = c.take('i')
        n_old = c.take('I')
        refs_end = c.o + 4 * n_old
        c.o = refs_end
        if c.take('I') != 0:
            raise ValueError('BSSkin::Instance carries a per-bone vector list; not handled')
        # a bone node to copy the layout from: childless, no extra data, 76 bytes
        tmpl = next(i for i in self.nodes if i != root and not self.nodes[i]['kids']
                    and self.offsets[i][1] == 76)
        node_type = self.type_index[tmpl]
        new_strings = list(self.strings)
        new_blocks = []
        for k, bdef in enumerate(bones):
            if bdef['name'] in new_strings:
                raise ValueError(f'{bdef["name"]} is already a string in the file')
            new_strings.append(bdef['name'])
            to, _ = self.offsets[tmpl]
            blk = bytearray(self.b[to:to + 76])
            struct.pack_into('<i', blk, 0, len(new_strings) - 1)              # name
            struct.pack_into('<3f', blk, 16, *bdef['node_t'])                 # after name, extras 0, ctrl, flags
            struct.pack_into('<9f', blk, 28, *bdef['node_rot'])
            struct.pack_into('<f', blk, 64, 1.0)
            struct.pack_into('<I', blk, 72, 0)                                # children
            new_blocks.append(bytes(blk))
        new_refs = list(range(nb, nb + len(bones)))

        # root node: children count + refs grow
        ro, rs = self.offsets[root]
        rc = Cursor(self.b, ro)
        self._av(rc)
        kids_at = rc.o
        kids = rc.take('I')
        tail = ro + rs
        root_blk = (bytes(self.b[ro:kids_at]) + struct.pack('<I', kids + len(bones))
                    + bytes(self.b[kids_at + 4:kids_at + 4 + 4 * kids])
                    + b''.join(struct.pack('<i', r) for r in new_refs)
                    + bytes(self.b[kids_at + 4 + 4 * kids:tail]))
        # skin instance: bone count + refs grow
        inst_blk = (bytes(self.b[o:o + 8]) + struct.pack('<I', n_old + len(bones))
                    + bytes(self.b[o + 12:refs_end]) + b''.join(struct.pack('<i', r) for r in new_refs)
                    + bytes(self.b[refs_end:o + size]))
        # bone data: count + entries grow
        do, ds = self.offsets[data]
        (count,) = struct.unpack_from('<I', self.b, do)
        entries = b''.join(struct.pack('<4f9f3ff', *b['sphere'], *b['skin_rot'], *b['skin_t'], b['scale'])
                           for b in bones)
        data_blk = struct.pack('<I', count + len(bones)) + bytes(self.b[do + 4:do + ds]) + entries

        blocks = []
        for i, (bo, bs) in enumerate(self.offsets):
            blocks.append(root_blk if i == root else inst_blk if i == inst else data_blk if i == data
                          else bytes(self.b[bo:bo + bs]))
        blocks += new_blocks
        last_end = self.offsets[-1][0] + self.offsets[-1][1]
        footer = bytes(self.b[last_end:])

        raw = [s.encode('latin1') for s in new_strings]
        header = (bytes(self.b[:self.nblocks_at]) + struct.pack('<I', nb + len(bones))
                  + bytes(self.b[self.nblocks_at + 4:self.type_index_at])
                  + b''.join(struct.pack('<H', t) for t in self.type_index + [node_type] * len(bones))
                  + b''.join(struct.pack('<I', len(b)) for b in blocks)
                  + struct.pack('<II', len(raw), max(len(r) for r in raw))
                  + b''.join(struct.pack('<I', len(r)) + r for r in raw)
                  + bytes(self.b[self.strings_end:self.data_at]))
        return header + b''.join(blocks) + footer

    def with_nodes(self, parent, nodes):
        """New file bytes with NiNodes added as children of node block `parent` (a skeleton edit).

        nodes: [dict(name, t, r)], the LOCAL transform relative to the parent (translation 3,
        rotation 9 row-major); scale 1. Each node is a NiNode APPENDED after the last block, so no
        existing reference moves; it has no extra data, no controller, no collision object and no
        children. The parent's child list grows, the header gains the block count, type indices,
        sizes and names, and the footer (root list) stays last. Every other byte is copied."""
        nb = len(self.offsets)
        if parent not in self.nodes:
            raise ValueError(f'block {parent} is not a node')
        tmpl = next(i for i in self.nodes if self.types[i] == 'NiNode' and not self.nodes[i]['kids']
                    and self.offsets[i][1] == 76)
        node_type = self.type_index[tmpl]
        new_strings = list(self.strings)
        new_blocks = []
        for d in nodes:
            if d['name'] in new_strings:
                raise ValueError(f'{d["name"]} is already a string in the file')
            new_strings.append(d['name'])
            to, _ = self.offsets[tmpl]
            blk = bytearray(self.b[to:to + 76])
            struct.pack_into('<i', blk, 0, len(new_strings) - 1)              # name
            struct.pack_into('<I', blk, 4, 0)                                 # no extra data
            struct.pack_into('<i', blk, 8, -1)                                # no controller
            struct.pack_into('<3f', blk, 16, *d['t'])                         # flags (12) from the template
            struct.pack_into('<9f', blk, 28, *d['r'])
            struct.pack_into('<f', blk, 64, 1.0)
            struct.pack_into('<i', blk, 68, -1)                               # no collision object
            struct.pack_into('<I', blk, 72, 0)                                # no children
            new_blocks.append(bytes(blk))
        new_refs = list(range(nb, nb + len(nodes)))
        po, ps = self.offsets[parent]
        pc = Cursor(self.b, po)
        self._av(pc)
        kids_at = pc.o
        kids = pc.take('I')
        parent_blk = (bytes(self.b[po:kids_at]) + struct.pack('<I', kids + len(nodes))
                      + bytes(self.b[kids_at + 4:kids_at + 4 + 4 * kids])
                      + b''.join(struct.pack('<i', r) for r in new_refs)
                      + bytes(self.b[kids_at + 4 + 4 * kids:po + ps]))
        blocks = [parent_blk if i == parent else bytes(self.b[o:o + s]) for i, (o, s) in enumerate(self.offsets)]
        blocks += new_blocks
        last_end = self.offsets[-1][0] + self.offsets[-1][1]
        raw = [s.encode('latin1') for s in new_strings]
        header = (bytes(self.b[:self.nblocks_at]) + struct.pack('<I', nb + len(nodes))
                  + bytes(self.b[self.nblocks_at + 4:self.type_index_at])
                  + b''.join(struct.pack('<H', t) for t in self.type_index + [node_type] * len(nodes))
                  + b''.join(struct.pack('<I', len(b)) for b in blocks)
                  + struct.pack('<II', len(raw), max(len(r) for r in raw))
                  + b''.join(struct.pack('<I', len(r)) + r for r in raw)
                  + bytes(self.b[self.strings_end:self.data_at]))
        return header + b''.join(blocks) + bytes(self.b[last_end:])

    def with_blocks(self, replace, add_strings=()):
        """New file bytes with whole blocks replaced ({index: bytes}) and strings appended.

        The replacement bytes must already reference the RIGHT indices (blocks and strings of
        THIS file, with appended strings numbered after the existing ones); only sizes, the
        string table and the order of bytes are handled here. Block count and types stay."""
        strings = list(self.strings) + list(add_strings)
        blocks = [replace.get(i, bytes(self.b[o:o + s])) for i, (o, s) in enumerate(self.offsets)]
        last_end = self.offsets[-1][0] + self.offsets[-1][1]
        raw = [s.encode('latin1') for s in strings]
        header = (bytes(self.b[:self.type_index_at])
                  + b''.join(struct.pack('<H', t) for t in self.type_index)
                  + b''.join(struct.pack('<I', len(b)) for b in blocks)
                  + struct.pack('<II', len(raw), max(len(r) for r in raw))
                  + b''.join(struct.pack('<I', len(r)) + r for r in raw)
                  + bytes(self.b[self.strings_end:self.data_at]))
        return header + b''.join(blocks) + bytes(self.b[last_end:])

    def with_edits(self, replace=None, append=(), add_strings=()):
        """New file bytes: blocks replaced ({index: bytes}), blocks APPENDED ([(type name, bytes)],
        numbered from the current block count, so no existing reference moves), strings appended
        (numbered after the existing ones), and block types added to the type table when new. The
        bytes given must already carry the right references. The footer (root list) stays last."""
        replace = replace or {}
        types = list(self.type_names)
        type_index = list(self.type_index)
        for name, _ in append:
            if name not in types:
                types.append(name)
            type_index.append(types.index(name))
        blocks = [replace.get(i, bytes(self.b[o:o + s])) for i, (o, s) in enumerate(self.offsets)]
        blocks += [blk for _, blk in append]
        raw = [s.encode('latin1') for s in list(self.strings) + list(add_strings)]
        header = (bytes(self.b[:self.nblocks_at]) + struct.pack('<I', len(blocks))
                  + bytes(self.b[self.nblocks_at + 4:self.type_count_at])
                  + struct.pack('<H', len(types))
                  + b''.join(struct.pack('<I', len(t)) + t.encode('latin1') for t in types)
                  + b''.join(struct.pack('<H', t) for t in type_index)
                  + b''.join(struct.pack('<I', len(b)) for b in blocks)
                  + struct.pack('<II', len(raw), max(len(r) for r in raw))
                  + b''.join(struct.pack('<I', len(r)) + r for r in raw)
                  + bytes(self.b[self.strings_end:self.data_at]))
        last_end = self.offsets[-1][0] + self.offsets[-1][1]
        return header + b''.join(blocks) + bytes(self.b[last_end:])

    def extra_block(self, kind):
        """(offset, size) of the first block of that type, or None."""
        for i, k in enumerate(self.types):
            if k == kind:
                return self.offsets[i]
        return None

    def save(self, path):
        pathlib.Path(path).write_bytes(bytes(self.b))

    def save_renamed(self, path, renames):
        """Write a copy whose header string table has names replaced ({old: new}).

        Every block names things by INDEX into that table (NiObjectNET's name, extra data names,
        controller targets), so renaming a string renames everything that uses it and no block
        byte changes. A new name must not already be in the table: two entries with one name
        would split the nodes that use them."""
        missing = [o for o in renames if o not in self.strings]
        clash = [n for n in renames.values() if n in self.strings]
        if missing or clash:
            raise ValueError(f'rename: not in the table {missing}; already in the table {clash}')
        strings = [renames.get(s, s) for s in self.strings]
        raw = [s.encode('latin1') for s in strings]
        table = struct.pack('<II', len(raw), max(len(r) for r in raw))
        table += b''.join(struct.pack('<I', len(r)) + r for r in raw)
        pathlib.Path(path).write_bytes(bytes(self.b[:self.strings_at]) + table + bytes(self.b[self.strings_end:]))


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
