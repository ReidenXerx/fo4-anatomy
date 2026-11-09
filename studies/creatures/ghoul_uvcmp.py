"""Are the ghoul skin meshes we paint (CBBE body, BodyTalk-era male body, hands) on the VANILLA UV layout? For each,
the vanilla mesh of the same name from Fallout4 - Meshes.ba2; nearest-position vertex pairs -> UV distance stats.
    python -I ghoul_uvcmp.py"""
import pathlib
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import nif  # noqa: E402

MESH = pathlib.Path(r'D:\F4Output\ghoulskin\mesh')
TMP = pathlib.Path(r'D:\F4Output\ghoulskin\uvcmp')
TMP.mkdir(exist_ok=True)
b = gamedata.Ba2(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Fallout4 - Meshes.ba2'))
VAN = {'femalebody.nif': 'meshes\\actors\\character\\characterassets\\femalebody.nif',
       'malebody.nif': 'meshes\\actors\\character\\characterassets\\malebody.nif',
       'femalehands.nif': 'meshes\\actors\\character\\characterassets\\femalehands.nif',
       'malehands.nif': 'meshes\\actors\\character\\characterassets\\malehands.nif'}
for name, rel in VAN.items():
    (TMP / name).write_bytes(b.read(rel))
    ours, van = nif.Nif(MESH / name), nif.Nif(TMP / name)
    for so in ours.shapes():
        if so.count < 500:
            continue
        sv = max(van.shapes(), key=lambda s: s.count)
        P, Q = np.array(so.positions()), np.array(sv.positions())
        Uo = np.array([so.uv(i) for i in range(so.count)])
        Uv = np.array([sv.uv(i) for i in range(sv.count)])
        d, j = cKDTree(Q).query(P)
        close = d < 0.5
        du = np.linalg.norm(Uo[close] - Uv[j[close]], axis=1)
        print(f'{name} {so.name} ({so.count}v) vs vanilla {sv.name} ({sv.count}v): {close.mean():.0%} within 0.5 units;'
              f' uv dist median {np.median(du):.4f}, <0.01 for {np.mean(du < 0.01):.0%}')
