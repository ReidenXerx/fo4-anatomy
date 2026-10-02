"""Which active plugins (AE profile) also override the vanilla leveled lists and outfits EAC 2.1.1 edits directly?
A list two plugins edit keeps only the later one's version unless a merged/bashed patch carries both."""
import os
import pathlib
import struct
import sys

import plugin_compare as pc

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
EAC = sys.argv[1] if len(sys.argv) > 1 else r'D:\F4Output\eac21\x211\Eli_Armour_Compendium.esp'
txt = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Fallout4' / 'plugins.txt'
active = [l[1:].strip() for l in txt.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('*')]

masters, _, recs = pc.read(EAC)
want = {}                                       # vanilla (Fallout4.esm, index 0) fid -> edid
for t, f, e, c, d in recs:
    if t in ('LVLI', 'OTFT') and (f >> 24) < len(masters) and masters[f >> 24] == 'Fallout4.esm':
        want[f & 0xFFFFFF] = f'{t} {e}'


def overrides(path):
    b = path.read_bytes()
    if b[:4] != b'TES4':
        return []
    hsize = struct.unpack_from('<I', b, 4)[0]
    ms = [d[:-1].decode('latin1').lower() for t, d in pc.subrecords(b[24:24 + hsize]) if t == b'MAST']
    if 'fallout4.esm' not in ms:
        return []
    fo4 = ms.index('fallout4.esm')
    hits, pos = [], 24 + hsize
    while pos + 24 <= len(b):
        t = b[pos:pos + 4]
        size = struct.unpack_from('<I', b, pos + 4)[0]
        if t == b'GRUP':
            label = b[pos + 8:pos + 12]
            gtype = struct.unpack_from('<i', b, pos + 12)[0]
            if gtype == 0 and label not in (b'LVLI', b'OTFT'):
                pos += size                     # skip whole top groups we do not need
                continue
            pos += 24
            continue
        if t in (b'LVLI', b'OTFT'):
            fid = struct.unpack_from('<I', b, pos + 12)[0]
            if fid >> 24 == fo4 and (fid & 0xFFFFFF) in want:
                hits.append(want[fid & 0xFFFFFF])
        pos += 24 + size
    return hits


found = {}
for name in active:
    p = DATA / name
    if not p.exists() or name.lower() == 'eli_armour_compendium.esp':
        continue
    try:
        h = overrides(p)
    except Exception:
        continue
    for x in h:
        found.setdefault(x, []).append(name)
print(f'EAC 2.1.1 edits {len(want)} vanilla lists/outfits; {len(found)} of them are also edited by active plugins:')
for k, v in sorted(found.items()):
    print(f'  {k}: {", ".join(v[:6])}{" ..." if len(v) > 6 else ""}')
