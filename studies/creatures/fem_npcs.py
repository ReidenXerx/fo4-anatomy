"""Survey for the female creature plugins: per race, the NPC_ records, which take their traits (= sex) from a
template, and the leveled actor lists (LVLN) holding the leaf actors (those that carry their own traits).
    python -I fem_npcs.py"""
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402

DATA = r'D:\SteamFreeGames\Fallout 4 AE\Data'
RACES = {0x187AF9: 'RaiderDog', 0x03578A: 'ViciousDog', 0x090C33: 'FEVHound', 0x0A0F2F: 'YaoGuai',
         0x07ED1D: 'RadStag', 0x01D810: 'Molerat', 0x01D698: 'Dogmeat'}


def subs(d):
    o, res = 0, []
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        res.append((t, d[o + 6:o + 6 + n]))
        o += 6 + n
    return res


def scan(path):
    p = esl.Plugin(path)
    npc, lvln = {}, {}
    for r in p.records:
        if r[0] != 'R' or r[2] not in ('NPC_', 'LVLN'):
            continue
        sl = subs(p.body(r))
        d = {}
        for t, v in sl:
            d.setdefault(t, []).append(v)
        edid = d.get(b'EDID', [b'?'])[0].rstrip(b'\0').decode('latin1')
        if r[2] == 'NPC_':
            acbs = d[b'ACBS'][0]
            flags, tflags = struct.unpack_from('<I', acbs, 0)[0], struct.unpack_from('<H', acbs, 14)[0]
            race = struct.unpack('<I', d[b'RNAM'][0])[0] if b'RNAM' in d else 0
            tplt = struct.unpack('<I', d[b'TPLT'][0])[0] if b'TPLT' in d else 0
            tpta = list(struct.unpack(f'<{len(d[b"TPTA"][0]) // 4}I', d[b'TPTA'][0])) if b'TPTA' in d else []
            npc[r[3]] = dict(edid=edid, female=bool(flags & 1), traits=bool(tflags & 1), race=race, tplt=tplt,
                             tpta=tpta, unique=bool(flags & 0x20))
        else:
            ents = [struct.unpack_from('<HHIHBB', v, 0) for v in d.get(b'LVLO', [])]
            lvln[r[3]] = dict(edid=edid, ents=[(lv, fid, cnt) for lv, _, fid, cnt, _, _ in ents])
    return p, npc, lvln


if __name__ == '__main__':
    p, npc, lvln = scan(DATA + r'\Fallout4.esm')
    holders = {}
    for lid, L in lvln.items():
        for lv, fid, cnt in L['ents']:
            holders.setdefault(fid, []).append((lid, lv))
    for race, name in RACES.items():
        mine = {k: v for k, v in npc.items() if v['race'] == race}
        leaf = {k: v for k, v in mine.items() if not v['traits']}
        print(f'== {name}: {len(mine)} NPC_, {len(leaf)} carry own traits, female {sum(v["female"] for v in mine.values())}')
        for k, v in sorted(leaf.items()):
            hl = holders.get(k, [])
            print(f'  {k:06X} {v["edid"]:40s} F={int(v["female"])} U={int(v["unique"])} in {len(hl)} LVLN',
                  [lvln[l]['edid'] for l, _ in hl][:4])
        tr = [v for v in mine.values() if v['traits']]
        print('  traits-templated:', len(tr), 'e.g.', [(v['edid'], f'{v["tplt"]:06X}') for v in tr[:3]])
