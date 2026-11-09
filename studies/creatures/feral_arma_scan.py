"""Every ARMA in the ENABLED plugins (plugins.txt order) whose male model is one of our 12 feral body meshes, and every
override of the 12 vanilla feral body ARMAs: which female model each ends up with, so no female feral draws the male
mesh. Light plugins included.  python -I feral_arma_scan.py"""
import os
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
BODIES = {'feralghoulbase', 'feralghoulbasebubble1a', 'feralghoulbasebubble1b', 'feralghoulbasebubble1c',
          'feralghoulbasebubble2a', 'feralghoulbasebubble2b', 'feralghoulbasewithered', 'feralghoulbaseshadow',
          'glowingone', 'putridglowingonebody', 'putridglowingonebodyb', 'putridglowingonebloatedbody'}
VAN = {0x06B4ED, 0x0B03B1, 0x0B03B0, 0x0B0393, 0x0B0392, 0x0B039B, 0x0A073E, 0x0A0749, 0x020BCB, 0x0A96B9, 0x0A96B8,
       0x0A96B7}
txt = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Fallout4' / 'plugins.txt'
order = ['Fallout4.esm', 'DLCRobot.esm', 'DLCworkshop01.esm', 'DLCCoast.esm', 'DLCworkshop02.esm',
         'DLCworkshop03.esm', 'DLCNukaWorld.esm']
order += [l[1:].strip() for l in txt.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('*')]


def subs(d):
    o = 0
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        yield t.decode('latin1'), d[o + 6:o + 6 + n]
        o += 6 + n


final = {}
for name in order:
    p = DATA / name
    if not p.exists():
        continue
    try:
        pl = esl.Plugin(p)
    except Exception:                                                               # noqa: BLE001
        continue
    masters = [x.lower() for x in pl.masters]
    for r in pl.records:
        if r[0] != 'R' or r[2] != 'ARMA':
            continue
        fid = r[3]
        mi = fid >> 24
        owner = masters[mi] if mi < len(masters) else name.lower()
        key = (owner, fid & 0xFFFFFF)
        try:
            d = dict((t, v) for t, v in subs(pl.body(r)))
        except Exception:                                                           # noqa: BLE001
            continue
        mod2 = d.get('MOD2', b'').rstrip(b'\0').decode('latin1')
        mod3 = d.get('MOD3', b'').rstrip(b'\0').decode('latin1')
        stem = pathlib.PureWindowsPath(mod2).stem.lower()
        if stem in BODIES or (owner == 'fallout4.esm' and key[1] in VAN):
            edid = d.get('EDID', b'').rstrip(b'\0').decode('latin1')
            final[key] = (name, edid, mod2, mod3)
for (owner, fid), (winner, edid, mod2, mod3) in sorted(final.items()):
    ok = mod3.lower().endswith('_f.nif')
    print(f'{"OK " if ok else "MISSING"} {owner}:{fid:06X} {edid:40s} winner {winner:45s} MOD2 {pathlib.PureWindowsPath(mod2).name:34s} MOD3 {pathlib.PureWindowsPath(mod3).name if mod3 else "-"}')
