"""Every deathclaw skin in the owner's load order: NPC_ records whose RNAM is DeathclawRace (0001DB4A) or whose WNAM is
an ARMO naming a deathclaw, their WNAM (skin), and the ARMOs + their ARMAs (models, MO2S). Winning versions.
    python -I dc_skins.py [npc form ids hex...]"""
import os
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import plugin_merge as pm  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
txt = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Fallout4' / 'plugins.txt'
order = ['Fallout4.esm', 'DLCRobot.esm', 'DLCworkshop01.esm', 'DLCCoast.esm', 'DLCworkshop02.esm',
         'DLCworkshop03.esm', 'DLCNukaWorld.esm']
order += [l[1:].strip() for l in txt.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('*')]
win = {}
for name in order:
    if not (DATA / name).exists():
        continue
    try:
        p = pm.Plugin(DATA / name, {'NPC_', 'ARMO', 'ARMA'})
    except Exception:                                                               # noqa: BLE001
        continue
    for key, (t, fl, subs) in p.records.items():
        win[key] = (name, p, t, subs)


def g(p, v):
    return p.glob(struct.unpack('<I', v)[0])


skins = {}
for key, (pn, p, t, subs) in win.items():
    if t != 'NPC_':
        continue
    f = dict(subs)
    if 'RNAM' in f and g(p, f['RNAM']) == ('fallout4.esm', 0x01DB4A) and 'WNAM' in f:
        edid = f.get('EDID', b'')[:-1].decode('latin1')
        skins.setdefault(g(p, f['WNAM']), []).append(f'{key[0]}:{key[1]:06X} {edid}')
for sk, npcs in sorted(skins.items()):
    pn, p, t, subs = win.get(sk, ('?', None, None, []))
    edid = dict(subs).get('EDID', b'?')[:-1].decode('latin1') if subs else '?'
    print(f'ARMO {sk[0]}:{sk[1]:06X} {edid} [{pn}] worn by {len(npcs)} NPCs, e.g. {npcs[:3]}')
    for a, v in subs:
        if a == 'MODL':
            ak = g(p, v)
            apn, ap, _, asubs = win.get(ak, ('?', None, None, []))
            af = dict(asubs)
            print(f'     ARMA {ak[0]}:{ak[1]:06X} {af.get("EDID", b"?")[:-1].decode("latin1")} [{apn}] '
                  f'MOD2={af.get("MOD2", b"")[:-1].decode("latin1")} MO2S={"yes" if "MO2S" in af else "-"}')
