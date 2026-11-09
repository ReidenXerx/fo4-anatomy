"""Every model path under actors\\<folder>\\ named in the masters.  python -I model_paths.py <folder name>"""
import pathlib
import re
import sys

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
pat = re.compile(rb'(?i)actors[\\/]' + re.escape(sys.argv[1].encode()) + rb'[\\/][ -~]*?\.nif')
for p in ('Fallout4.esm', 'DLCRobot.esm', 'DLCCoast.esm', 'DLCNukaWorld.esm', 'DLCworkshop01.esm'):
    f = DATA / p
    if f.exists():
        print(p, sorted(set(m.group(0).decode() for m in pat.finditer(f.read_bytes()))))
