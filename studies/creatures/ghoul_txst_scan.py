"""Which records pick the ghoul skin textures: TXSTs naming a ghoul texture (in the masters + the loose plugins the
owner's AE loads), and every ARMA/HDPT/RACE/NPC_ record that references one of them (by form id in a 4-byte field).
    python -I ghoul_txst_scan.py"""
import os
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
txt = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Fallout4' / 'plugins.txt'
order = ['Fallout4.esm', 'DLCRobot.esm', 'DLCCoast.esm', 'DLCNukaWorld.esm']
order += [l[1:].strip() for l in txt.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('*')]


def subs(d):
    o = 0
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        yield t, d[o + 6:o + 6 + n]
        o += 6 + n


txst = {}           # (owner plugin lower, local id) -> (plugin, edid, textures)
refs = []
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
        if r[0] != 'R' or r[2] not in ('TXST', 'ARMA', 'HDPT', 'RACE'):
            continue
        try:
            body = pl.body(r)
        except Exception:                                                           # noqa: BLE001
            continue
        mi = r[3] >> 24
        owner = masters[mi] if mi < len(masters) else name.lower()
        key = (owner, r[3] & 0xFFFFFF)
        if r[2] == 'TXST':
            tex = [v[:-1].decode('latin1') for t, v in subs(body) if t.startswith(b'TX')]
            if any('ghoul' in t.lower() for t in tex):
                edid = next((v[:-1].decode('latin1') for t, v in subs(body) if t == b'EDID'), '')
                txst[key] = (name, edid, tex)
        else:
            refs.append((name, r[2], r[3], masters, body))
print('GHOUL TXSTs (winning plugin last):')
for k, (pn, edid, tex) in sorted(txst.items()):
    print(f'  {k[0]}:{k[1]:06X} {edid} [{pn}] {tex[:3]}')
ids = set(txst)
print('REFERENCES:')
for pn, typ, fid, masters, body in refs:
    for t, v in subs(body):
        if len(v) == 4:
            x = struct.unpack('<I', v)[0]
            mi = x >> 24
            owner = masters[mi] if mi < len(masters) else pn.lower()
            if (owner, x & 0xFFFFFF) in ids:
                edid = next((vv[:-1].decode('latin1') for tt, vv in subs(body) if tt == b'EDID'), '')
                print(f'  {typ} {fid:08X} {edid} [{pn}] {t.decode()} -> {txst[(owner, x & 0xFFFFFF)][1]}')
