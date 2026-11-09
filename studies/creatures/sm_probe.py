"""Super mutant / behemoth genitals in UAP's deployed meshes: per shape its transform, bones, dominant-bone vertex
counts and the bind origins of the genital bones; the vanilla body nif for comparison (nodes present).
    python -I sm_probe.py"""
import collections
import pathlib
import struct
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gamedata  # noqa: E402
import nif  # noqa: E402
from feral_all import xf_offset  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
OUT = pathlib.Path(r'D:\F4Output\creatures\sm\vanilla')
OUT.mkdir(parents=True, exist_ok=True)
ba2 = gamedata.Ba2(DATA / 'Fallout4 - Meshes.ba2')
for rel, gen in (('actors/supermutant/characterassets/supermutantbody.nif', 'SM Penis'),
                 ('actors/supermutantbehemoth/characterassets/supermutantbehemoth.nif', 'Behemoth_Penis1')):
    m = nif.Nif(DATA / 'meshes' / rel)
    print('==', rel)
    for s in m.shapes():
        t = struct.unpack_from('<3f', m.b, xf_offset(m, s))
        bones = m.skin(s)[0]
        dom = collections.Counter(bones[max(s.skin_weights(i), key=lambda x: x[1])[0]] for i in range(s.count))
        print(f'   {s.name}: t {np.round(t, 2)} bones {len(bones)} dominant {dict(dom.most_common(6))}')
        if s.name == gen:
            names, xf = m.skin(s)
            for n, (rot, tr, sc) in zip(names, xf):
                o = -np.array(rot).reshape(3, 3).T @ np.array(tr) / sc
                print(f'      bone {n:14s} origin (skin space) {o.round(2)}')
    vp = OUT / pathlib.Path(rel).name
    vp.write_bytes(ba2.read('meshes/' + rel))
    v = nif.Nif(vp)
    print('   vanilla shapes', [(s.name, s.count) for s in v.shapes()],
          'genital nodes in vanilla', [n['name'] for n in v.nodes.values() if n['name'] and
                                       any(k in n['name'] for k in ('Penis', 'Balls'))])
