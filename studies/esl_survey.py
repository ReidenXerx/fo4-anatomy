"""Every active FULL plugin that adds armor (ARMO/ARMA): could it be light? Reads plugins.txt (AE profile) and Data."""
import os, pathlib, struct, collections
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
txt = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Fallout4' / 'plugins.txt'
active = [l[1:].strip() for l in txt.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('*')]

def scan(p):
    b = p.read_bytes()
    if b[:4] != b'TES4':
        return None
    hsize = struct.unpack_from('<I', b, 4)[0]
    flags = struct.unpack_from('<I', b, 8)[0]
    masters, off, end = 0, 24, 24 + hsize
    while off < end:
        t, s = b[off:off + 4], struct.unpack_from('<H', b, off + 4)[0]
        masters += t == b'MAST'
        off += 6 + s
    new = oor = 0
    kinds = collections.Counter()
    pos = end
    while pos < len(b):
        t = b[pos:pos + 4]
        size = struct.unpack_from('<I', b, pos + 4)[0]
        if t == b'GRUP':
            pos += 24
            continue
        fid = struct.unpack_from('<I', b, pos + 12)[0]
        if fid >> 24 == masters:
            new += 1
            kinds[t.decode('latin1')] += 1
            if not 0x800 <= (fid & 0xFFFFFF) <= 0xFFF:
                oor += 1
        pos += 24 + size
    return flags, new, oor, kinds

rows = []
for name in active:
    if not name.lower().endswith(('.esp', '.esm')):
        continue
    p = DATA / name
    if not p.exists():
        continue
    r = scan(p)
    if not r:
        continue
    flags, new, oor, kinds = r
    if flags & 0x200 or not (kinds['ARMO'] or kinds['ARMA']):
        continue
    other = new - kinds['ARMO'] - kinds['ARMA'] - kinds['COBJ'] - kinds['OMOD'] - kinds['KYWD'] - kinds['MSWP'] \
        - kinds['LVLI'] - kinds['TXST'] - kinds['FLST'] - kinds['GLOB'] - kinds['OTFT'] - kinds['INNR'] - kinds['MISC']
    verdict = ('flag only' if oor == 0 and new <= 2048 else 'compact' if new <= 2048 else 'too big (>2048 new)')
    rows.append((verdict, name, new, kinds['ARMO'], other, flags & 1))
for v in ('flag only', 'compact', 'too big (>2048 new)'):
    sel = [r for r in rows if r[0] == v]
    print(f'== {v}: {len(sel)}')
    for r in sel:
        print(f'   {r[1]:<60} new {r[2]:>5}  ARMO {r[3]:>4}  non-outfit records {r[4]:>4}  {"ESM" if r[5] else ""}')
print('full plugins with armor:', len(rows), 'of', len(active), 'active')
