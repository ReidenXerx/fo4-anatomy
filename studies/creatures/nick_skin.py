"""Which ARMO lists a given ARMA (MODL), which RACE/NPC_ uses those ARMOs as skin (WNAM), and every ARMA the skin
holds with its models + race.  python -I nick_skin.py <plugin> <arma hex> [...]"""
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pl = esl.Plugin(sys.argv[1])
want = {int(x, 16) for x in sys.argv[2:]}


def subs(d):
    o = 0
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        yield t.decode('latin1'), d[o + 6:o + 6 + n]
        o += 6 + n


rec = {}
for r in pl.records:
    if r[0] == 'R' and r[2] in ('ARMO', 'ARMA', 'RACE', 'NPC_'):
        rec[r[3]] = (r[2], r)


def edid(r):
    for t, v in subs(pl.body(r)):
        if t == 'EDID':
            return v.rstrip(b'\0').decode('latin1')
    return '?'


armos = []
for fid, (typ, r) in rec.items():
    if typ == 'ARMO':
        mods = [struct.unpack('<I', v[:4])[0] for t, v in subs(pl.body(r)) if t == 'MODL' and len(v) >= 4]
        if want & set(mods):
            armos.append(fid)
            print(f'ARMO {fid:08X} {edid(r)}')
            for a in mods:
                if a in rec:
                    t2, r2 = rec[a]
                    models = [f'{t}={v.rstrip(chr(0).encode()).decode("latin1")}' for t, v in subs(pl.body(r2))
                              if t in ('MOD2', 'MOD3')]
                    races = [f'{struct.unpack("<I", v[:4])[0]:08X}' for t, v in subs(pl.body(r2)) if t in ('RNAM', 'MODL')]
                    print(f'   ARMA {a:08X} {edid(r2)} {models} races {races}')
for fid, (typ, r) in rec.items():
    if typ in ('RACE', 'NPC_'):
        for t, v in subs(pl.body(r)):
            if t == 'WNAM' and struct.unpack('<I', v[:4])[0] in armos:
                print(f'{typ} {fid:08X} {edid(r)} WNAM -> {struct.unpack("<I", v[:4])[0]:08X}')
