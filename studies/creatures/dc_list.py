import pathlib, sys
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
for a in sorted(DATA.glob('Fallout4 - Meshes*.ba2')):
    b = gamedata.Ba2(a)
    for n in b.names:
        if 'deathclaw' in n.lower() and n.lower().endswith('.nif') and 'fx' not in n.lower():
            print(a.name, n)
