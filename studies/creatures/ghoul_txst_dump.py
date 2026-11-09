"""The ghoul skin TXSTs as the game resolves them (winning record in the owner's load order): the four on the ghoul
ARMAs (NAM0/NAM1) and every HDPT whose model is a ghoul head / rear head, with its TNAM TXST.
    python -I ghoul_txst_dump.py"""
import os
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
txt = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Fallout4' / 'plugins.txt'
order = ['Fallout4.esm', 'DLCRobot.esm', 'DLCworkshop01.esm', 'DLCCoast.esm', 'DLCworkshop02.esm', 'DLCworkshop03.esm',
         'DLCNukaWorld.esm']
order += [l[1:].strip() for l in txt.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('*')]


def subs(d):
    o = 0
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        yield t, d[o + 6:o + 6 + n]
        o += 6 + n


def fmt(sl):
    out = []
    for t, v in sl:
        tt = t.decode('latin1')
        if len(v) > 1 and all(32 <= c < 127 for c in v[:-1]) and v[-1] == 0:
            out.append(f'{tt}="{v[:-1].decode()}"')
        elif len(v) == 4:
            out.append(f'{tt}={struct.unpack("<I", v)[0]:08X}')
        else:
            out.append(f'{tt}[{len(v)}]')
    return ' '.join(out)


win = {}
for name in order:
    p = DATA / name
    if not p.exists():
        continue
    try:
        pl = esl.Plugin(p)
    except Exception:                                                               # noqa: BLE001
        continue
    masters = [m.lower() for m in pl.masters]
    for r in pl.records:
        if r[0] != 'R' or r[2] not in ('TXST', 'HDPT'):
            continue
        mi = r[3] >> 24
        owner = masters[mi] if mi < len(masters) else name.lower()
        try:
            win[(r[2], owner, r[3] & 0xFFFFFF)] = (name, list(subs(pl.body(r))), masters)
        except Exception:                                                           # noqa: BLE001
            pass
for fid in (0x0518FC, 0x0F6E5B, 0x04A833, 0x0F6E5D):
    k = ('TXST', 'fallout4.esm', fid)
    print(f'TXST {fid:06X} [{win[k][0]}] {fmt(win[k][1])}')
print('HDPTs with a ghoul model:')
for (typ, owner, lid), (pn, sl, masters) in sorted(win.items()):
    if typ != 'HDPT':
        continue
    model = next((v[:-1].decode('latin1') for t, v in sl if t == b'MODL'), '')
    if 'ghoul' not in model.lower() or 'eye' in model.lower():
        continue
    tn = next((struct.unpack('<I', v)[0] for t, v in sl if t == b'TNAM'), None)
    edid = next((v[:-1].decode('latin1') for t, v in sl if t == b'EDID'), '')
    line = f'  HDPT {owner}:{lid:06X} {edid} [{pn}] MODL={model}'
    if tn is not None:
        mi = tn >> 24
        towner = masters[mi] if mi < len(masters) else pn.lower()
        t = win.get(('TXST', towner, tn & 0xFFFFFF))
        line += f'\n      TNAM {towner}:{tn & 0xFFFFFF:06X} -> ' + (f'[{t[0]}] {fmt(t[1])}' if t else '?')
    print(line)
