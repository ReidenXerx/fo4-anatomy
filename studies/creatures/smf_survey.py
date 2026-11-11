"""Female super mutants (Dudu 11-11, option A) - survey of the vanilla game (Fallout4.esm + DLCs):
the SM race(s), their skins (ARMO -> ARMA MOD2/MOD3), every ARMA wearable by the race (the armour to refit: its
MOD2 models, grouped), and the NPC template structure (leaf actors in leveled lists).
    python -I smf_survey.py > D:/F4Output/creatures/smf/survey.txt"""
import collections
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\studies\creatures')
from fem_plugin import Load, get, u32  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
L = Load(['Fallout4.esm', 'DLCRobot.esm', 'DLCworkshop01.esm', 'DLCCoast.esm', 'DLCworkshop02.esm',
          'DLCworkshop03.esm', 'DLCNukaWorld.esm'])


def ed(fid):
    r = L.rec.get(fid)
    return get(r[2], b'EDID').rstrip(b'\0').decode('latin1') if r and get(r[2], b'EDID') else f'{fid:08X}'


def s(sl, t):
    v = get(sl, t)
    return v.rstrip(b'\0').decode('latin1') if v else ''


# races: by the RACE records is not loaded by Load (NPC_/LVLN/ARMA/ARMO only) -> take the races the SM NPCs use
npcs = {f: r for f, r in L.rec.items() if r[0] == 'NPC_'}
race_count = collections.Counter(u32(get(r[2], b'RNAM')) for r in npcs.values() if get(r[2], b'RNAM'))
sm_npc = {f: r for f, r in npcs.items() if 'supermutant' in ed(f).lower() or 'mutant' in ed(f).lower()}
sm_races = collections.Counter(u32(get(r[2], b'RNAM')) for r in sm_npc.values() if get(r[2], b'RNAM'))
print('races used by *mutant* NPCs:', [(f'{k:08X}', n) for k, n in sm_races.most_common(8)])
RACE = sm_races.most_common(1)[0][0]
print('SM race', f'{RACE:08X}')
# skins
for f, r in sorted(npcs.items()):
    if get(r[2], b'RNAM') and u32(get(r[2], b'RNAM')) == RACE and get(r[2], b'WNAM'):
        pass
skins = collections.Counter(u32(get(r[2], b'WNAM')) for r in npcs.values()
                            if get(r[2], b'RNAM') and u32(get(r[2], b'RNAM')) == RACE and get(r[2], b'WNAM'))
print('skins (WNAM) on SM-race NPCs:', [(ed(k), n) for k, n in skins.most_common()])
# every ARMA whose race (RNAM) or additional races (MODL) include the SM race
arma = []
for f, (t, fl, sl) in L.rec.items():
    if t != 'ARMA':
        continue
    races = [u32(v) for k, v in sl if k in (b'RNAM', b'MODL') and len(v) == 4]
    if RACE in races:
        arma.append((f, s(sl, b'MOD2'), s(sl, b'MOD3'), ed(f)))
print(f'\nARMAs wearable by the SM race: {len(arma)}')
models = collections.Counter(m2.lower() for _, m2, _, _ in arma)
print('distinct MOD2 models:', len(models))
for f, m2, m3, e in sorted(arma, key=lambda a: a[1].lower()):
    print(f'  {f:08X} {e:45s} MOD2={m2}  MOD3={m3 or "-"}')
# NPC structure
lists = {f: r for f, r in L.rec.items() if r[0] == 'LVLN'}
held = collections.defaultdict(list)
for lf, (_, _, sl) in lists.items():
    for k, v in sl:
        if k == b'LVLO':
            held[struct.unpack_from('<I', v, 4)[0]].append(ed(lf))
mine = {f: r for f, r in npcs.items() if get(r[2], b'RNAM') and u32(get(r[2], b'RNAM')) == RACE}
leaf = [f for f, r in mine.items() if not struct.unpack_from('<H', get(r[2], b'ACBS'), 14)[0] & 1]
fem = [f for f, r in mine.items() if struct.unpack_from('<I', get(r[2], b'ACBS'), 0)[0] & 1]
print(f'\nSM-race NPC_: {len(mine)}, own traits {len(leaf)}, female {len(fem)}, in any list {sum(1 for f in mine if held[f])}')
for f in sorted(leaf)[:40]:
    print(f'  {f:08X} {ed(f):40s} lists {held[f][:3]}')
