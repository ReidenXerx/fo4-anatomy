"""The foreign deathclaw skins Ivy runs (depo.esp, MutantMenagerie.esm, OldTimeReligion.esp): winning ARMO (all
subrecords), its ARMAs, each ARMA's model: body shape vertex count/bbox vs the vanilla deathclaw body, the body's
material, and the MO2S swap pairs -> the material the body really wears.
    python -I dc_ivy_survey.py"""
import pathlib
import re
import struct
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import ghoul_redirect as gr  # noqa: E402
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
OWNERS = {'depo.esp', 'mutantmenagerie.esm', 'oldtimereligion.esp'}
game = gamedata.Game(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data'))
win = gr.winning(game, ('NPC_', 'ARMO', 'ARMA', 'MSWP'))
VAN = np.array(nif.Nif(r'D:\F4Output\creatures\dc\vanilla\deathclaw.nif').shape('DeathclawFX:0').positions())
work = pathlib.Path(r'D:\F4Output\creatures\dc\ivy_survey')
work.mkdir(exist_ok=True)


def glob(plugin, masters, v):
    fid = struct.unpack('<I', v)[0]
    src = [m.lower() for m in masters] + [plugin.lower()]
    return (src[min(fid >> 24, len(src) - 1)], fid & 0xFFFFFF)


skins = set()
for key, (plugin, masters, t, flags, subs) in win.items():
    if t != 'NPC_':
        continue
    f = dict(subs)
    if 'RNAM' in f and glob(plugin, masters, f['RNAM']) == ('fallout4.esm', 0x01DB4A) and 'WNAM' in f:
        sk = glob(plugin, masters, f['WNAM'])
        if sk[0] in OWNERS:
            skins.add(sk)
for sk in sorted(skins):
    plugin, masters, t, flags, subs = win[sk]
    f = dict(subs)
    print(f'ARMO {sk[0]}:{sk[1]:06X} {f.get("EDID", b"")[:-1].decode()} [winner {plugin}] subs {[a for a, _ in subs]}')
    for a, v in subs:
        if a != 'MODL':
            continue
        ak = glob(plugin, masters, v)
        ap, am, _, _, asubs = win[ak]
        af = dict(asubs)
        model = af.get('MOD2', b'')[:-1].decode('latin1')
        line = f'   ARMA {ak[0]}:{ak[1]:06X} {af.get("EDID", b"")[:-1].decode()} [winner {ap}] MOD2={model}'
        rel = 'meshes/' + model.replace('\\', '/')
        if game.find(rel) is None:
            print(line, 'MODEL NOT FOUND')
            continue
        p = work / pathlib.Path(rel).name
        p.write_bytes(game.read(rel))
        m = nif.Nif(p)
        body = max(m.shapes(), key=lambda s: s.count)
        P = np.array(body.positions())
        same = len(P) == len(VAN) and np.abs(P - VAN).max() < 0.05
        mats = [s for s in m.strings if s.lower().endswith(('.bgsm', '.bgem'))]
        line += f'\n      body {body.name} {len(P)}v {"== vanilla" if same else "DIFFERS"}' + \
            ('' if same else f' (max move {np.abs(P - VAN).max() if len(P) == len(VAN) else "n/a":})') + \
            f'; materials {mats[:4]}'
        if 'MO2S' in af:
            sw = glob(ap, am, af['MO2S'])
            ws = win.get(sw)
            if ws:
                pairs = [(ws[4][i][1][:-1].decode('latin1'), ws[4][i + 1][1][:-1].decode('latin1'))
                         for i in range(len(ws[4]) - 1) if ws[4][i][0] == 'BNAM' and ws[4][i + 1][0] == 'SNAM']
                line += f'\n      MO2S {sw[0]}:{sw[1]:06X} {pairs}'
        print(line)
