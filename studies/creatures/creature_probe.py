"""Generic UAP creature genital probe: deployed nif (rel under Data/meshes) -> per shape: count, dominant bones,
bbox; genital shapes: bones with bind origins, tri morphs (bbox per morph); vanilla copy extracted (BA2s) and its
shapes compared (count / positions).  python -I creature_probe.py <rel nif> <genital regex> <out dir>"""
import collections
import pathlib
import re
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import nif  # noqa: E402
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
rel, rx, out = sys.argv[1], re.compile(sys.argv[2], re.I), pathlib.Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
m = nif.Nif(DATA / 'meshes' / rel)
t = re.findall(rb'BODYTRI.{0,8}?([ -~]{5,}\.tri)', m.b, re.S)
tri = {}
if t:
    tp = DATA / 'meshes' / t[0].decode().replace('\\', '/')
    print('BODYTRI', t[0].decode(), 'exists' if tp.exists() else 'MISSING')
    if tp.exists():
        tri = {s: {n: (mu, d) for n, mu, d in ms} for s, ms in tri_sync.read(tp)}
for s in m.shapes():
    P = np.array(s.positions())
    names, xf = m.skin(s)
    dom = collections.Counter(names[max(s.skin_weights(i), key=lambda x: x[1])[0]] for i in range(s.count)) \
        if names else {}
    print(f'{s.name}: {s.count}v {m.types[s.index]} bbox {P.min(0).round(1)} {P.max(0).round(1)} '
          f'dominant {dict(collections.Counter(dom).most_common(5))}')
    if rx.search(s.name):
        for n, (rot, tr, sc) in zip(names, xf):
            o = -np.array(rot).reshape(3, 3).T @ np.array(tr) / sc
            print(f'    bone {n:20s} {o.round(2)}')
        for name, (mu, d) in tri.get(s.name, {}).items():
            Q = P.copy()
            for i, v in d.items():
                Q[i] += np.array(v, float) * mu
            print(f'    morph {name:14s} bbox {Q.min(0).round(1)} {Q.max(0).round(1)}')
for a in sorted(DATA.glob('*.ba2')):
    if 'texture' in a.name.lower():
        continue
    try:
        b = gamedata.Ba2(a)
    except Exception:                                                               # noqa: BLE001
        continue
    if 'meshes/' + rel in b:
        vp = out / pathlib.Path(rel).name
        vp.write_bytes(b.read('meshes/' + rel))
        v = nif.Nif(vp)
        vs = {x.name: x for x in v.shapes()}
        print('vanilla from', a.name, [(x.name, x.count) for x in v.shapes()])
        for s in m.shapes():
            if s.name in vs and s.count == vs[s.name].count:
                dp = np.abs(np.array(s.positions()) - np.array(vs[s.name].positions())).max()
                print(f'    {s.name}: same count, dpos vs vanilla {dp:.4f}')
        break
