"""PNGs for feral_tex_render.py: every texture tex.json names, from our out/Data first, else loose game Data, else the
vanilla texture BA2s; normals -> full XYZ with OpenGL green for Blender.
    python -I feral_tex_prep.py <tex.json> <png dir> <our Data>"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import ghoul_common as gc  # noqa: E402

TEX, PNG, OURS = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
PNG.mkdir(parents=True, exist_ok=True)
names = set()
for f in json.loads(TEX.read_text()).values():
    for o in f.values():
        for k in 'dns':
            if o.get(k):
                names.add(o[k])
arcs = [gamedata.Ba2(p) for p in sorted(DATA.glob('Fallout4 - Textures*.ba2')) + sorted(DATA.glob('DLC*Textures*.ba2'))]
for n in sorted(names):
    rel = n.lower().replace('\\', '/').removeprefix('textures/')
    key = rel.replace('/', '__').removesuffix('.dds')
    src = None
    for base in (OURS / 'textures', DATA / 'textures'):
        if (base / rel).exists():
            src = base / rel
            break
    work = gc.ROOT.parent / 'creatures' / 'feral' / 'dec'
    if src is None:
        for a in arcs:
            if 'textures/' + rel in a:
                work.mkdir(parents=True, exist_ok=True)
                src = work / (key + '.dds')
                src.write_bytes(a.read('textures/' + rel))
                break
    if src is None:
        print('missing', n)
        continue
    rgba = gc.dds_to_array(src, work / 'tga').astype(np.float32) / 255
    if key.endswith('_n'):
        x, y = rgba[..., 0] * 2 - 1, rgba[..., 1] * 2 - 1
        z = np.sqrt(np.clip(1 - x * x - y * y, 0, 1))
        img = np.stack([x, -y, z], -1) * 0.5 + 0.5
    else:
        img = rgba[..., :3]
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(PNG / (key + '.png'))
    print('png', key)
