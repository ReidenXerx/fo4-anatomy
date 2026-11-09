"""Per UAP canine mesh: shape transforms of the genital shapes, and whether every other shape equals the vanilla mesh
(positions, UVs, weights by bone name) - i.e. whether UAP touched the body.
    python -I canine_check.py"""
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
VAN = pathlib.Path(r'D:\F4Output\creatures\canine\vanilla')
RELS = ['actors/dogmeat/characterassets/dogmeat.nif', 'actors/dogmeat/characterassets/raiderdog.nif',
        'actors/viciousdog/viciousdog.nif', 'actors/viciousdog/viciousdogpackleader.nif',
        'actors/dlc03/mutatedwolf/wolfalpha.nif', 'actors/dlc03/mutatedwolf/wolffuzzy.nif',
        'actors/fevhound/characterassets/fevhound.nif',
        'actors/dogmeat/characterassets/dogmeat_nude.nif', 'actors/dogmeat/characterassets/raiderdog_nude.nif']
arcs = [gamedata.Ba2(p) for p in [DATA / 'Fallout4 - Meshes.ba2', DATA / 'DLCCoast - Main.ba2']]
VAN.mkdir(parents=True, exist_ok=True)
for rel in RELS:
    m = nif.Nif(DATA / 'meshes' / rel)
    print('==', rel)
    for s in m.shapes():
        t = struct.unpack_from('<3f9ff', m.b, xf_offset(m, s))
        print(f'   {s.name}: t {np.round(t[:3], 2)} scale {t[12]:.3f}')
    base = rel.replace('_nude', '')
    src = next((a for a in arcs if 'meshes/' + base in a), None)
    if src is None:
        print('   vanilla: not found in BA2s')
        continue
    vp = VAN / pathlib.Path(base).name
    vp.write_bytes(src.read('meshes/' + base))
    v = nif.Nif(vp)
    vs = {s.name: s for s in v.shapes()}
    for s in m.shapes():
        if s.name not in vs:
            continue
        w = vs[s.name]
        if s.count != w.count:
            print(f'   {s.name}: COUNT {w.count}->{s.count}')
            continue
        dp = np.abs(np.array(s.positions()) - np.array(w.positions())).max()
        sb, wb = m.skin(s)[0], v.skin(w)[0]
        dw = 0.0
        for i in range(s.count):
            a = {sb[k]: x for k, x in s.skin_weights(i) if x > 1e-4}
            b = {wb[k]: x for k, x in w.skin_weights(i) if x > 1e-4}
            dw = max(dw, max([abs(a.get(n, 0) - b.get(n, 0)) for n in set(a) | set(b)] or [0]))
        print(f'   vs vanilla {s.name}: dpos {dp:.4f} dweight {dw:.4f}')
    print('   only in UAP:', [s.name for s in m.shapes() if s.name not in vs], 'only vanilla:',
          [n for n in vs if n not in {s.name for s in m.shapes()}])
