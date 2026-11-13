"""Immersive Aliens (Dudu 11-13: "yes we can make it for all aliens") - survey of the game's aliens: the races
alien/zetan NPCs use, their skins (ARMO -> ARMA MOD2/MOD3 body models), every NPC of those races (+ which leveled
lists hold them), base game + DLCs + any Creation (cc*) plugins in Data that mention aliens.
    python -I al_survey.py > D:/F4Output/creatures/alien/survey.txt"""
import collections
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\studies\creatures')
from fem_plugin import Load, get, u32  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
BASE = ['Fallout4.esm', 'DLCRobot.esm', 'DLCworkshop01.esm', 'DLCCoast.esm', 'DLCworkshop02.esm',
        'DLCworkshop03.esm', 'DLCNukaWorld.esm']
cc = [p.name for p in sorted(DATA.glob('cc*.esl')) + sorted(DATA.glob('cc*.esm'))
      if b'lien' in p.read_bytes() or b'Zeta' in p.read_bytes()]
print('Creation plugins mentioning aliens:', cc)
L = Load(BASE + cc)


def ed(fid):
    r = L.rec.get(fid)
    return get(r[2], b'EDID').rstrip(b'\0').decode('latin1') if r and get(r[2], b'EDID') else f'{fid:08X}'


def s(sl, t):
    v = get(sl, t)
    return v.rstrip(b'\0').decode('latin1') if v else ''


npcs = {f: r for f, r in L.rec.items() if r[0] == 'NPC_'}
al_npc = {f: r for f, r in npcs.items() if any(k in ed(f).lower() for k in ('alien', 'zeta'))}
races = collections.Counter(u32(get(r[2], b'RNAM')) for r in al_npc.values() if get(r[2], b'RNAM'))
print('races used by *alien*/*zeta* NPCs:', [(f'{k:08X}', n) for k, n in races.most_common()])
for RACE, _ in races.most_common():
    mine = {f: r for f, r in npcs.items() if get(r[2], b'RNAM') and u32(get(r[2], b'RNAM')) == RACE}
    skins = collections.Counter(u32(get(r[2], b'WNAM')) for r in mine.values() if get(r[2], b'WNAM'))
    print(f'\n== race {RACE:08X}: {len(mine)} NPC_, skins {[(ed(k), n) for k, n in skins.most_common()]}')
    for f, r in sorted(mine.items()):
        acbs = get(r[2], b'ACBS')
        female = bool(struct.unpack_from('<I', acbs, 0)[0] & 1) if acbs else None
        print(f'  {f:08X} {ed(f):40s} female={female} skin={ed(u32(get(r[2], b"WNAM"))) if get(r[2], b"WNAM") else "-"}')
    for f, (t, fl, sl) in sorted(L.rec.items()):
        if t == 'ARMA':
            rs = [u32(v) for k, v in sl if k in (b'RNAM', b'MODL') and len(v) == 4]
            if RACE in rs:
                print(f'  ARMA {f:08X} {ed(f):40s} MOD2={s(sl, b"MOD2")}  MOD3={s(sl, b"MOD3") or "-"}')
