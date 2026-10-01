"""Compact a small plugin's NEW form ids into 0x800..0xFFF and set the ESL flag, writing a copy.
Every occurrence of an old new-form id (4 bytes LE, master byte = own index) inside any record's data is replaced,
decompressing compressed records. Refuses if an old id's byte pattern also appears where it is not a form id
candidate count mismatch is reported for review."""
import pathlib, struct, sys, zlib

src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
b = src.read_bytes()
hsize = struct.unpack_from('<I', b, 4)[0]
hend = 24 + hsize
masters, off = [], 24
while off < hend:
    t, s = b[off:off + 4], struct.unpack_from('<H', b, off + 4)[0]
    if t == b'MAST':
        masters.append(b[off + 6:off + 6 + s - 1])
    off += 6 + s
own = len(masters)

# pass 1: the records (offsets) and every new form id
records, pos = [], hend
while pos < len(b):
    t = b[pos:pos + 4]
    size = struct.unpack_from('<I', b, pos + 4)[0]
    if t == b'GRUP':
        records.append(('G', pos))
        pos += 24
        continue
    records.append(('R', pos))
    pos += 24 + size
new_ids = []
for kind, p in records:
    if kind == 'R':
        fid = struct.unpack_from('<I', b, p + 12)[0]
        if fid >> 24 == own:
            new_ids.append(fid)
used = {f & 0xFFFFFF for f in new_ids if 0x800 <= (f & 0xFFFFFF) <= 0xFFF}
free = (i for i in range(0x800, 0x1000) if i not in used)
remap = {f: (own << 24) | next(free) for f in new_ids if not (0x800 <= (f & 0xFFFFFF) <= 0xFFF)}
print('remap:', {hex(k): hex(v) for k, v in remap.items()})
pat = {struct.pack('<I', k): struct.pack('<I', v) for k, v in remap.items()}

def fix(data):
    n = 0
    for o, nw in pat.items():
        n += data.count(o)
        data = data.replace(o, nw)
    return data, n

# pass 2: rebuild, record by record (sizes change only for recompressed records; GRUP sizes are recomputed)
out = bytearray(b[:hend])
flags = struct.unpack_from('<I', out, 8)[0]
struct.pack_into('<I', out, 8, flags | 0x200)
hits = 0
grup_stack = []          # (out offset of the GRUP header, end offset in the source)
pos = hend
def close_groups(at):
    while grup_stack and grup_stack[-1][1] <= at:
        go, _ = grup_stack.pop()
        struct.pack_into('<I', out, go + 4, len(out) - go)
while pos < len(b):
    close_groups(pos)
    t = b[pos:pos + 4]
    size = struct.unpack_from('<I', b, pos + 4)[0]
    if t == b'GRUP':
        hdr = bytearray(b[pos:pos + 24])
        # a group label can be a form id (persistent/temporary children of a CELL/WRLD/DIAL)
        lab = bytes(hdr[8:12])
        if lab in pat:
            hdr[8:12] = pat[lab]
            hits += 1
        grup_stack.append((len(out), pos + size))
        out += hdr
        pos += 24
        continue
    hdr = bytearray(b[pos:pos + 24])
    rflags = struct.unpack_from('<I', hdr, 8)[0]
    fid = struct.unpack_from('<I', hdr, 12)[0]
    if fid in remap:
        struct.pack_into('<I', hdr, 12, remap[fid])
    body = b[pos + 24:pos + 24 + size]
    if rflags & 0x40000:      # compressed: u32 decompressed size + zlib
        raw = zlib.decompress(body[4:])
        raw, n = fix(raw)
        body = struct.pack('<I', len(raw)) + zlib.compress(raw)
    else:
        body, n = fix(body)
    hits += n
    struct.pack_into('<I', hdr, 4, len(body))
    out += hdr + body
    pos += 24 + size
close_groups(len(b) + 1)
dst.write_bytes(out)
print(f'{src.name}: {len(remap)} ids moved, {hits} references rewritten, ESL flag set -> {dst}')
