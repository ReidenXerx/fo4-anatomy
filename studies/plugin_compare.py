"""Compare Fallout 4 plugins record by record: what each adds, what it overrides in its masters, where (cells,
worldspaces), and whether one version keeps another's form ids. Written for the Eli's Armour Compendium 1.5 -> 2.1.1
question (the owner, 2026-10-02): do 2.1's records keep 1.5's ids (saves), and does 2.1 still carry what 4estGimp's
Edit fixed in 1.5 (worldspace edits that break precombines, direct edits of vanilla leveled lists)?

    python studies/plugin_compare.py <plugin.esp> [<plugin.esp> ...]     # the first is the reference for ids
"""
import collections
import pathlib
import struct
import sys
import zlib


def subrecords(data):
    out, pos = [], 0
    big = None
    while pos + 6 <= len(data):
        t = data[pos:pos + 4]
        size = struct.unpack_from('<H', data, pos + 4)[0]
        pos += 6
        if t == b'XXXX':
            big = struct.unpack_from('<I', data, pos)[0]
            pos += size
            continue
        if big is not None:
            size, big = big, None
        out.append((t, data[pos:pos + size]))
        pos += size
    return out


def read(path):
    b = pathlib.Path(path).read_bytes()
    assert b[:4] == b'TES4'
    hsize = struct.unpack_from('<I', b, 4)[0]
    flags = struct.unpack_from('<I', b, 8)[0]
    masters = [d[:-1].decode('latin1') for t, d in subrecords(b[24:24 + hsize]) if t == b'MAST']
    recs = []                                  # (type, fid, edid, context, data)
    stack = []                                 # (end offset, group label/type)
    pos = 24 + hsize
    while pos < len(b):
        while stack and pos >= stack[-1][0]:
            stack.pop()
        t = b[pos:pos + 4]
        size = struct.unpack_from('<I', b, pos + 4)[0]
        if t == b'GRUP':
            gtype = struct.unpack_from('<i', b, pos + 12)[0]
            label = b[pos + 8:pos + 12]
            stack.append((pos + size, gtype, label))
            pos += 24
            continue
        rflags = struct.unpack_from('<I', b, pos + 8)[0]
        fid = struct.unpack_from('<I', b, pos + 12)[0]
        data = b[pos + 24:pos + 24 + size]
        if rflags & 0x40000:
            try:
                data = zlib.decompress(data[4:])
            except zlib.error:
                data = b''
        edid = next((d[:-1].decode('latin1', 'replace') for st, d in subrecords(data) if st == b'EDID'), '')
        top = stack[0][2].decode('latin1') if stack else ''
        recs.append((t.decode('latin1'), fid, edid, top, data))
        pos += 24 + size
    return masters, flags, recs


def owner(fid, masters, name):
    i = fid >> 24
    return masters[i] if i < len(masters) else name


def report(path, ref=None):
    name = pathlib.Path(path).name
    masters, flags, recs = read(path)
    print(f'=== {path}\n  masters: {masters}; flags {flags:#x}; records {len(recs)}')
    new = collections.Counter(t for t, f, e, c, d in recs if owner(f, masters, name) == name)
    ovr = collections.Counter((t, owner(f, masters, name)) for t, f, e, c, d in recs if owner(f, masters, name) != name)
    print('  new by type:', dict(new.most_common(14)))
    print('  overrides by type/master:', dict(ovr.most_common(14)))
    cells = [r for r in recs if r[3] in ('CELL', 'WRLD')]
    placed = collections.Counter((r[0], r[3], 'override' if owner(r[1], masters, name) != name else 'new') for r in cells)
    print('  in cells/worldspaces:', dict(placed.most_common(10)))
    vanilla_ll = [r for r in recs if r[0] == 'LVLI' and owner(r[1], masters, name) != name]
    print(f'  vanilla leveled lists edited directly: {len(vanilla_ll)}', [r[2] for r in vanilla_ll[:12]])
    ids = {r[2]: r[1] & 0xFFFFFF for r in recs if r[2] and owner(r[1], masters, name) == name}
    if ref:
        same = sum(1 for e, f in ref.items() if ids.get(e) == f)
        moved = [(e, f'{f:06X}->{ids[e]:06X}') for e, f in ref.items() if e in ids and ids[e] != f]
        gone = [e for e in ref if e not in ids]
        added = [e for e in ids if e not in ref]
        print(f'  against the reference: {same} records keep their id, {len(moved)} renumbered, {len(gone)} gone, '
              f'{len(added)} new')
        print('    renumbered:', moved[:8])
        print('    gone:', gone[:12])
    return ids


if __name__ == '__main__':
    ref = None
    for i, p in enumerate(sys.argv[1:]):
        ids = report(p, ref)
        if i == 0:
            ref = ids
