"""python -I dc_extract.py <out dir> <rel in Fallout4 - Meshes.ba2>..."""
import pathlib
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402

b = gamedata.Ba2(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Fallout4 - Meshes.ba2'))
out = pathlib.Path(sys.argv[1])
for n in sys.argv[2:]:
    (out / pathlib.PureWindowsPath(n).name).write_bytes(b.read(n))
    print(n)
