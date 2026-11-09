"""List the vanilla deathclaw BGSMs and the strings in each.  python -I dc_bgsm_list.py"""
import pathlib
import re
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402

b = gamedata.Ba2(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Fallout4 - Materials.ba2'))
for n in b.names:
    low = n.lower().replace('\\', '/')
    if '/actors/deathclaw/' in low and low.endswith('.bgsm'):
        d = b.read(n)
        print(n, len(d), [x.decode() for x in re.findall(rb'[ -~]{5,}', d)])
