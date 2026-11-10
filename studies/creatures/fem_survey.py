"""Female mammals survey (Dudu 11-10): for dogs/wolves/FEV hounds, yao guai, radstags, mole rats: every NPC_ of those
races (winning version) -> sex flag, WNAM skin, template; skins -> ARMAs -> MOD2/MOD3; which leveled lists hold them.
    python -I fem_survey.py"""
import collections
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import ghoul_redirect as gr  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
game = gamedata.Game(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data'))
win = gr.winning(game, ('RACE', 'NPC_', 'ARMO', 'ARMA', 'LVLN'))
WANT = ('dog', 'wolf', 'fevhound', 'yaoguai', 'radstag', 'molerat')


def glob(plugin, masters, v):
    fid = struct.unpack('<I', v)[0]
    src = [m.lower() for m in masters] + [plugin.lower()]
    return (src[min(fid >> 24, len(src) - 1)], fid & 0xFFFFFF)


def edid(k):
    r = win.get(k)
    return dict(r[4]).get('EDID', b'?')[:-1].decode('latin1') if r else '?'


races = {k for k, r in win.items() if r[2] == 'RACE' and any(w in edid(k).lower() for w in WANT)
         and 'child' not in edid(k).lower()}
print('RACES', sorted((f'{k[0]}:{k[1]:06X}', edid(k)) for k in races))
by_race = collections.defaultdict(list)
skins = collections.defaultdict(set)
for k, (pl, ms, t, fl, subs) in win.items():
    if t != 'NPC_':
        continue
    f = dict(subs)
    if 'RNAM' not in f:
        continue
    rk = glob(pl, ms, f['RNAM'])
    if rk not in races:
        continue
    acbs = f.get('ACBS', b'')
    female = bool(struct.unpack_from('<I', acbs, 0)[0] & 1) if len(acbs) >= 4 else None
    sk = glob(pl, ms, f['WNAM']) if 'WNAM' in f else None
    by_race[edid(rk)].append((f'{k[0]}:{k[1]:06X}', edid(k), female, sk and edid(sk)))
    if sk:
        skins[sk].add(edid(rk))
for race, npcs in sorted(by_race.items()):
    fem = sum(1 for n in npcs if n[2])
    print(f'{race}: {len(npcs)} NPCs, {fem} female; skins {sorted({n[3] for n in npcs if n[3]})}')
for sk in sorted(skins):
    pl, ms, t, fl, subs = win[sk]
    print(f'ARMO {sk[0]}:{sk[1]:06X} {edid(sk)} [{pl}] races {sorted(skins[sk])}')
    for a, v in subs:
        if a == 'MODL':
            ak = glob(pl, ms, v)
            ar = win.get(ak)
            if not ar:
                continue
            af = dict(ar[4])
            print(f'    ARMA {ak[0]}:{ak[1]:06X} {edid(ak)} [{ar[0]}] MOD2={af.get("MOD2", b"")[:-1].decode("latin1")} '
                  f'MOD3={af.get("MOD3", b"")[:-1].decode("latin1") or "-"}')
