"""Does a plugin put head-only items into vanilla CLOTHING leveled lists (4estGimp's "nude NPC" fix for EAC 1.5)?
An NPC whose outfit list rolls a hat alone spawns naked. For each vanilla LVLI the plugin overrides: its entries that
are this plugin's armours, and their biped slots (BOD2): head-only (no body slot 33) vs clothing.

    python studies/eac_nude_check.py <plugin.esp>
"""
import struct
import sys

import plugin_compare as pc

HEAD = {0: '30 hair top', 1: '31 hair long', 16: '46 headband', 17: '47 eyes', 18: '48 beard', 19: '49 mouth', 20: '50 neck'}
BODY = 1 << 3                                   # slot 33


def main(path):
    name = path.replace('\\', '/').split('/')[-1]
    masters, flags, recs = pc.read(path)
    own = lambda f: pc.owner(f, masters, name) == name
    armo = {}
    for t, f, e, c, d in recs:
        if t == 'ARMO' and own(f):
            bod = next((sd for st, sd in pc.subrecords(d) if st == b'BOD2'), None)
            armo[f & 0xFFFFFF] = (e, struct.unpack_from('<I', bod, 0)[0] if bod else 0)
    bad = 0
    for t, f, e, c, d in recs:
        if t != 'LVLI' or own(f):
            continue
        heads, cloth = [], 0
        for st, sd in pc.subrecords(d):
            if st != b'LVLO' or len(sd) < 8:
                continue
            ref = struct.unpack_from('<I', sd, 4)[0]
            if pc.owner(ref, masters, name) != name:
                continue
            item = armo.get(ref & 0xFFFFFF)
            if not item:
                continue
            ename, slots = item
            if slots & BODY:
                cloth += 1
            elif any(slots & (1 << b) for b in HEAD):
                heads.append(ename)
        if heads and ('Cloth' in e or 'Outfit' in e or 'Underwear' in e or 'Underarmor' in e or 'Resident' in e):
            bad += 1
            print(f'  {e}: {len(heads)} head-only item(s) beside {cloth} clothing: {heads}')
    print(f'{bad} vanilla clothing list(s) with head-only items from {name}')


if __name__ == '__main__':
    main(sys.argv[1])
