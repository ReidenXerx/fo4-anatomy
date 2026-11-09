"""Fallout4.esm: every ARMA whose EDID names a ghoul (full subrecords) + the MSWPs they use, and BGSM paths with 'ghoul'.
    python -I ghoul_arma_dump.py"""
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pl = esl.Plugin(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Fallout4.esm'))


def subs(d):
    o = 0
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        yield t, d[o + 6:o + 6 + n]
        o += 6 + n


def show(r, body):
    out = [f'{r[2]} {r[3]:08X}']
    for t, v in subs(body):
        tt = t.decode('latin1')
        if len(v) > 1 and all(32 <= c < 127 for c in v[:-1]) and v[-1] == 0:
            out.append(f'   {tt} "{v[:-1].decode()}"')
        elif len(v) == 4:
            out.append(f'   {tt} {struct.unpack("<I", v)[0]:08X}')
        else:
            out.append(f'   {tt} [{len(v)}]')
    print('\n'.join(out))


want_mswp = set()
for r in pl.records:
    if r[0] != 'R' or r[2] != 'ARMA':
        continue
    body = pl.body(r)
    edid = next((v for t, v in subs(body) if t == b'EDID'), b'')
    if b'ghoul' in edid.lower() and b'feral' not in edid.lower():
        show(r, body)
        for t, v in subs(body):
            if t in (b'MO2S', b'MO3S', b'MO4S', b'MO5S'):
                want_mswp.add(struct.unpack('<I', v)[0])
for r in pl.records:
    if r[0] == 'R' and r[2] == 'MSWP' and r[3] in want_mswp:
        show(r, pl.body(r))
