"""PyNifly's .tri ends right after the last morph; BodySlide's (and UAP's) ends with an empty UV-morph section
(uint16 0). Rewrite each given .tri in BodySlide's layout, optionally renaming a shape.
    python -I tri_normalize.py <tri> [...] [--rename old=new]"""
import pathlib
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import tri_sync  # noqa: E402

args = sys.argv[1:]
ren = {}
if '--rename' in args:
    i = args.index('--rename')
    old, new = args[i + 1].split('=', 1)
    ren[old] = new
    args = args[:i] + args[i + 2:]
for a in args:
    p = pathlib.Path(a)
    b = p.read_bytes()
    try:
        shapes = tri_sync.read(p)
    except ValueError:
        p.write_bytes(b + b'\x00\x00')
        shapes = tri_sync.read(p)
    tri_sync.write(p, [(ren.get(s, s), ms) for s, ms in shapes])
    back = tri_sync.read(p)
    print(p.name, [(s, len(ms)) for s, ms in back], len(b), '->', p.stat().st_size)
