"""Vicious dog: our mesh shapes, the vanilla BA2 paths, and the ARMA model paths in Fallout4.esm.
    python -I vdog_check.py"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import nif  # noqa: E402

OUT = pathlib.Path(r'D:\F4Output\creatures\canine\out9\Data\meshes')
for f in sorted(OUT.rglob('*.nif')):
    if 'vicious' not in f.name.lower():
        continue
    m = nif.Nif(f)
    print(f.relative_to(OUT))
    for s in m.shapes():
        P = np.array(s.positions())
        print('   ', s.name, s.count, P.min(0).round(1).tolist(), P.max(0).round(1).tolist())
b = gamedata.Ba2(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Fallout4 - Meshes.ba2'))
print([n for n in b.names if 'viciousdog' in n.lower() and n.lower().endswith('.nif')][:20])
esm = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Fallout4.esm').read_bytes()
import re  # noqa: E402
print(sorted(set(m.group(0).decode() for m in re.finditer(rb'(?i)actors\\viciousdog\\[ -~]*?\.nif', esm))))
