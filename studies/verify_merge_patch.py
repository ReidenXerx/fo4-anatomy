"""Proof of a merge patch (tools/plugin_merge.py): light flag; every LVLO/INAM form id names a record that exists in its
master; LLCT equals the number of LVLO; each list's flags carry every bit a merged plugin set; each list holds every
entry each merged plugin added (vs vanilla) and none it removed.

    python studies/verify_merge_patch.py <patch.esp> <plugin paths that were merged ...>
"""
import collections
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import plugin_merge as pm

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')


def main(patch, merged):
    b = pathlib.Path(patch).read_bytes()
    flags = struct.unpack_from('<I', b, 8)[0]
    pp = pm.Plugin(patch, {'LVLI', 'OTFT'})
    print(f'light flag: {bool(flags & 0x200)}; masters {pp.masters}')
    # every master's form ids (all types: an entry may name an ARMO, a LVLI, ...)
    exists = {}
    paths = {pathlib.Path(m).name.lower(): pathlib.Path(m) if pathlib.Path(m).is_absolute() else DATA / m
             for m in merged}
    for m in pp.masters:
        path = paths.get(m.lower(), DATA / m)
        raw = path.read_bytes()
        hsize = struct.unpack_from('<I', raw, 4)[0]
        ms = [d[:-1].decode('latin1').lower() for t, d in pm.subrecords(raw[24:24 + hsize]) if t == 'MAST']
        own, ids, pos = len(ms), set(), 24 + hsize
        while pos + 24 <= len(raw):
            t = raw[pos:pos + 4]
            size = struct.unpack_from('<I', raw, pos + 4)[0]
            if t == b'GRUP':
                pos += 24
                continue
            fid = struct.unpack_from('<I', raw, pos + 12)[0]
            if fid >> 24 == own:
                ids.add(fid & 0xFFFFFF)
            pos += 24 + size
        exists[m.lower()] = ids
    bad = []
    vanilla = pm.Plugin(DATA / 'Fallout4.esm', {'LVLI', 'OTFT'})
    plugins = [pm.Plugin(pathlib.Path(m) if pathlib.Path(m).is_absolute() else DATA / m, {'LVLI', 'OTFT'}) for m in merged]
    for g, (t, f, subs) in pp.records.items():
        e = next((d[:-1].decode('latin1') for st, d in subs if st == 'EDID'), '')
        refs = []
        if t == 'LVLI':
            n = sum(1 for st, d in subs if st == 'LVLO')
            llct = next((d[0] for st, d in subs if st == 'LLCT'), None)
            if llct != n:
                bad.append(f'{e}: LLCT {llct} vs {n} LVLO')
            refs = [r[1] for r in pm.entries(pp, subs)]
            mine = collections.Counter(pm.entries(pp, subs))
            van = collections.Counter(pm.entries(vanilla, vanilla.records[g][2]))
            vfl = int.from_bytes(dict(vanilla.records[g][2]).get('LVLF', b'\0'), 'little')
            pfl = int.from_bytes(dict(subs).get('LVLF', b'\0'), 'little')
            for p in plugins:
                if g not in p.records:
                    continue
                theirs = collections.Counter(pm.entries(p, p.records[g][2]))
                lost = (theirs - van) - mine
                back = (van - theirs) & mine
                if lost:
                    bad.append(f'{e}: {sum(lost.values())} entries {p.name} added are missing')
                if back:
                    bad.append(f'{e}: {sum(back.values())} entries {p.name} removed came back')
                mf = int.from_bytes(dict(p.records[g][2]).get('LVLF', b'\0'), 'little')
                if (mf & ~vfl) & ~pfl:
                    bad.append(f'{e}: flag bits {(mf & ~vfl):#x} {p.name} set are not set')
            print(f'  {t} {e}: {n} entries, flags {pfl:#x} (vanilla {vfl:#x})')
        else:
            refs = pm.items(pp, subs)
            print(f'  {t} {e}: {len(refs)} items')
        for owner, local in refs:
            if local not in exists.get(owner, set()):
                bad.append(f'{e}: {owner} {local:06X} is not a record of {owner}')
    print('PROBLEMS:' if bad else 'all checks pass')
    for x in bad:
        print('  ' + x)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2:]))
