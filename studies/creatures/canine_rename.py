"""PyNifly drops a trailing '.001' from shape names (Blender's duplicate suffix). Put UAP's exact name back in the nif
(header string) and in its .tri (shape key).  python -I canine_rename.py <nif> <exported name> <wanted name>"""
import pathlib
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

path, got, want = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
m = nif.Nif(path)
if got not in m.strings:
    raise SystemExit(f'{got} not in {path.name}')
tmp = path.with_suffix('.renamed.nif')
m.save_renamed(tmp, {got: want})
tmp.replace(path)
tri = path.with_suffix('.tri')
if tri.exists():
    shapes = tri_sync.read(tri)
    tri_sync.write(tri, [(want if s == got else s, ms) for s, ms in shapes])
print('renamed', got, '->', want, [s.name for s in nif.Nif(path).shapes()],
      [s for s, _ in tri_sync.read(tri)] if tri.exists() else '')
